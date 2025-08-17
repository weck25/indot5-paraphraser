from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
import logging
import time
import os
from typing import Optional, List
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IndoT5 Paraphraser API",
    description="Indonesian text paraphrasing service using IndoT5 model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer
model = None
tokenizer = None
device = None

class ParaphraseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Text to paraphrase")
    style: str = Field(default="friendly", description="Paraphrasing style: friendly, formal, casual, default")
    max_length: int = Field(default=128, ge=10, le=512, description="Maximum output length")

class ParaphraseResponse(BaseModel):
    result: str
    original_text: str
    style: str
    processing_time: float
    model_info: dict

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    uptime: float

# Model loading function
def load_model():
    """Load IndoT5 model and tokenizer"""
    global model, tokenizer, device
    
    try:
        logger.info("Loading IndoT5 model...")
        
        # Check if CUDA is available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        # Load tokenizer and model
        model_name = "cahya/indot5-base-paraphrase"
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        
        # Move model to device
        model.to(device)
        model.eval()
        
        logger.info("IndoT5 model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False

# Style mapping for different paraphrasing styles
STYLE_PROMPTS = {
    "friendly": "Parafrase dengan gaya ramah dan santai: ",
    "formal": "Parafrase dengan gaya formal dan sopan: ",
    "casual": "Parafrase dengan gaya santai dan informal: ",
    "default": "Parafrase: "
}

def generate_paraphrase(text: str, style: str = "friendly", max_length: int = 128) -> str:
    """Generate paraphrase using IndoT5 model"""
    try:
        # Get style prompt
        style_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["default"])
        
        # Prepare input text
        input_text = style_prompt + text
        
        # Tokenize input
        inputs = tokenizer.encode(
            input_text, 
            return_tensors="pt", 
            max_length=512, 
            truncation=True
        ).to(device)
        
        # Generate paraphrase
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=max_length,
                num_beams=4,
                length_penalty=0.6,
                early_stopping=True,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2
            )
        
        # Decode output
        paraphrase = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return paraphrase.strip()
        
    except Exception as e:
        logger.error(f"Error generating paraphrase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Paraphrase generation failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("Starting IndoT5 Paraphraser API...")
    
    # Load model
    success = load_model()
    if not success:
        logger.error("Failed to load model during startup")
        # Don't exit, let the health check handle it
    
    logger.info("IndoT5 Paraphraser API started successfully!")

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "IndoT5 Paraphraser API",
        "version": "1.0.0",
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
        model_loaded=model is not None,
        device=str(device) if device else "unknown",
        uptime=time.time() - app.startup_time if hasattr(app, 'startup_time') else 0
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
            max_length=request.max_length
        )
        
        processing_time = time.time() - start_time
        
        return ParaphraseResponse(
            result=result,
            original_text=request.text,
            style=request.style,
            processing_time=processing_time,
            model_info={
                "model": "cahya/indot5-base-paraphrase",
                "device": str(device),
                "max_length": request.max_length
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
                max_length=request.max_length
            )
            
            processing_time = time.time() - start_time
            
            results.append(ParaphraseResponse(
                result=result,
                original_text=request.text,
                style=request.style,
                processing_time=processing_time,
                model_info={
                    "model": "cahya/indot5-base-paraphrase",
                    "device": str(device),
                    "max_length": request.max_length
                }
            ))
        
        return {"results": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Batch paraphrase error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
