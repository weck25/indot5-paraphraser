from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import time
import os
from typing import Optional, List
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for model and tokenizer
model = None
tokenizer = None
device = None

# Model loading function
def load_model():
    """Load IndoT5 model and tokenizer"""
    global model, tokenizer, device
    
    try:
        logger.info("Loading IndoT5 model...")
        
        # Check if CUDA is available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        # Load tokenizer and model - using Wikidepia model
        model_name = "Wikidepia/IndoT5-base-paraphrase"
        logger.info(f"Loading model: {model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Move model to device
        model.to(device)
        model.eval()
        
        logger.info("IndoT5 model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        # Try alternative model
        try:
            logger.info("Trying alternative model...")
            model_name = "indonesian-nlp/indot5-base"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            model.to(device)
            model.eval()
            logger.info("Alternative model loaded successfully!")
            return True
        except Exception as e2:
            logger.error(f"Failed to load alternative model: {str(e2)}")
            return False

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting IndoT5 Paraphraser API...")
    
    # Load model
    success = load_model()
    if not success:
        logger.error("Failed to load model during startup")
        # Don't exit, let the health check handle it
    
    logger.info("IndoT5 Paraphraser API started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IndoT5 Paraphraser API...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="IndoT5 Paraphraser API",
    description="Indonesian text paraphrasing service using Wikidepia/IndoT5-base-paraphrase model",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware with more permissive settings for Coolify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Coolify
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

class ParaphraseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Text to paraphrase")
    style: str = Field(default="default", description="Paraphrasing style: default (model doesn't support style variations)")
    max_length: int = Field(default=512, ge=10, le=512, description="Maximum output length")
    num_return_sequences: int = Field(default=1, ge=1, le=5, description="Number of paraphrase variations to generate")

class ParaphraseResponse(BaseModel):
    result: str
    original_text: str
    style: str
    processing_time: float
    model_details: dict

class HealthResponse(BaseModel):
    status: str
    is_model_loaded: bool
    device: str
    uptime: float

def generate_paraphrase(text: str, style: str = "default", max_length: int = 512, num_return_sequences: int = 1) -> str:
    """Generate paraphrase using Wikidepia/IndoT5-base-paraphrase model"""
    try:
        # Prepare input text according to model documentation
        # The model expects: "paraphrase: " + sentence + " </s>"
        input_text = "paraphrase: " + text + " </s>"
        
        # Tokenize input exactly as shown in the model documentation
        encoding = tokenizer(input_text, padding='longest', return_tensors="pt")
        
        # Move to device
        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)
        
        # Generate paraphrase exactly as shown in the model documentation
        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids, 
                attention_mask=attention_mask,
                max_length=max_length,
                do_sample=True,
                top_k=200,
                top_p=0.95,
                early_stopping=True,
                num_return_sequences=num_return_sequences
            )
        
        # Decode output - take the first sequence if multiple
        paraphrase = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return paraphrase.strip()
        
    except Exception as e:
        logger.error(f"Error generating paraphrase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Paraphrase generation failed: {str(e)}")

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "IndoT5 Paraphraser API",
        "version": "1.0.0",
        "model": "Wikidepia/IndoT5-base-paraphrase",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "paraphrase": "/paraphrase",
            "batch_paraphrase": "/batch-paraphrase"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        is_model_loaded=model is not None,
        device=str(device) if device else "unknown",
        uptime=time.time() - getattr(app, 'startup_time', time.time())
    )

@app.post("/paraphrase", response_model=ParaphraseResponse)
async def paraphrase_text(request: ParaphraseRequest):
    """Paraphrase a single text"""
    start_time = time.time()
    
    # Check if model is loaded
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Generate paraphrase
        result = generate_paraphrase(
            text=request.text,
            style=request.style,
            max_length=request.max_length,
            num_return_sequences=request.num_return_sequences
        )
        
        processing_time = time.time() - start_time
        
        return ParaphraseResponse(
            result=result,
            original_text=request.text,
            style=request.style,
            processing_time=processing_time,
            model_details={
                "model": "Wikidepia/IndoT5-base-paraphrase",
                "device": str(device),
                "max_length": request.max_length,
                "num_return_sequences": request.num_return_sequences
            }
        )
        
    except Exception as e:
        logger.error(f"Paraphrase error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-paraphrase")
async def batch_paraphrase_texts(requests: List[ParaphraseRequest]):
    """Paraphrase multiple texts"""
    # Check if model is loaded
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        results = []
        for request in requests:
            start_time = time.time()
            
            result = generate_paraphrase(
                text=request.text,
                style=request.style,
                max_length=request.max_length,
                num_return_sequences=request.num_return_sequences
            )
            
            processing_time = time.time() - start_time
            
            results.append(ParaphraseResponse(
                result=result,
                original_text=request.text,
                style=request.style,
                processing_time=processing_time,
                model_details={
                    "model": "Wikidepia/IndoT5-base-paraphrase",
                    "device": str(device),
                    "max_length": request.max_length,
                    "num_return_sequences": request.num_return_sequences
                }
            ))
        
        return {"results": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Batch paraphrase error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add OPTIONS handler for CORS preflight requests
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for CORS"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    # Set startup time
    app.startup_time = time.time()
    
    # Run the application
    port = int(os.getenv("PORT", 5005))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
