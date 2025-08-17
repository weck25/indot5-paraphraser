# IndoT5 Paraphraser - Coolify Deployment Guide

## 🚀 Deployment di Coolify

### 1. **Repository Setup**
- Upload semua file ke repository Git (GitHub/GitLab)
- Pastikan struktur folder seperti ini:
```
indot5-paraphraser/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── scripts/
```

### 2. **Coolify Configuration**

#### **Build Configuration:**
```yaml
# Build Command (kosongkan jika menggunakan Dockerfile)
Build Command: 

# Start Command (kosongkan jika menggunakan Dockerfile)
Start Command: 

# Dockerfile Path
Dockerfile Path: Dockerfile

# Port
Port: 5005
```

#### **Environment Variables:**
```bash
# Port configuration
PORT=5005
HOST=0.0.0.0
PYTHONUNBUFFERED=1

# Optional: HuggingFace token (jika model private)
HF_TOKEN=your_huggingface_token_here
```

#### **Resource Limits:**
```yaml
# Memory (Recommended untuk model Wikidepia/IndoT5-base-paraphrase)
Memory Limit: 4GB
Memory Reservation: 2GB

# CPU
CPU Limit: 2 cores
CPU Reservation: 1 core
```

### 3. **Model Information**

Service ini menggunakan model [Wikidepia/IndoT5-base-paraphrase](https://huggingface.co/Wikidepia/IndoT5-base-paraphrase):
- **Model Size**: ~850MB
- **Training**: Dilatih pada dataset PAWS yang diterjemahkan ke bahasa Indonesia
- **Input Format**: `"paraphrase: " + text + " </s>"`
- **Capabilities**: Generate paraphrase yang natural dan kontekstual

### 4. **Dockerfile Optimization untuk Coolify**

Jika ada masalah dengan Dockerfile, gunakan versi ini:

```dockerfile
# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 5005

# Health check (increased start period for model loading)
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:5005/health || exit 1

# Run the application
CMD ["python", "app.py"]
```

### 5. **Troubleshooting**

#### **Masalah Model Loading:**
Jika model gagal load, cek logs di Coolify dashboard. Kemungkinan penyebab:
- Koneksi internet lambat
- Model tidak ditemukan
- Memory tidak cukup

#### **Solusi:**
1. **Increase memory limit** ke 6GB
2. **Increase startup timeout** ke 300 detik
3. **Check network connectivity**
4. **Verify model name**: `Wikidepia/IndoT5-base-paraphrase`

#### **Health Check Configuration:**
```yaml
# Health Check Path
Health Check Path: /health

# Health Check Interval
Health Check Interval: 30s

# Health Check Timeout
Health Check Timeout: 30s

# Health Check Retries
Health Check Retries: 3

# Health Check Start Period (increased for model loading)
Health Check Start Period: 180s
```

### 6. **Monitoring**

#### **Logs yang Perlu Diperhatikan:**
```bash
# Model loading success
"Loading model: Wikidepia/IndoT5-base-paraphrase"
"IndoT5 model loaded successfully!"

# Model loading failed
"Failed to load model: ..."

# Service ready
"IndoT5 Paraphraser API started successfully!"
```

#### **Health Check Response:**
```json
{
  "status": "healthy",
  "is_model_loaded": true,
  "device": "cpu",
  "uptime": 1234.56
}
```

### 7. **Update Backend Configuration**

Setelah deploy berhasil, update environment variable di backend:

```bash
# Di file .env backend
INDOT5_API_URL=http://your-coolify-domain:5005/paraphrase
```

### 8. **Testing**

#### **Test Health Endpoint:**
```bash
curl http://your-coolify-domain:5005/health
```

#### **Test Paraphrase:**
```bash
curl -X POST http://your-coolify-domain:5005/paraphrase \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Anak anak melakukan piket kelas agar kebersihan kelas terjaga",
    "max_length": 512,
    "num_return_sequences": 1
  }'
```

#### **Expected Response:**
```json
{
  "result": "Para siswa melaksanakan tugas piket untuk menjaga kebersihan ruangan",
  "original_text": "Anak anak melakukan piket kelas agar kebersihan kelas terjaga",
  "style": "default",
  "processing_time": 1.25,
  "model_details": {
    "model": "Wikidepia/IndoT5-base-paraphrase",
    "device": "cpu",
    "max_length": 512,
    "num_return_sequences": 1
  }
}
```

### 9. **Performance Tips**

1. **Enable model caching** dengan volume mount
2. **Use GPU** jika tersedia di server
3. **Monitor memory usage** secara berkala
4. **Set proper resource limits**
5. **Model loading time**: ~2-3 menit pada startup

### 10. **Security**

1. **Use HTTPS** di production
2. **Configure CORS** dengan domain yang spesifik
3. **Set rate limiting** di reverse proxy
4. **Monitor logs** untuk suspicious activity

### 11. **Model Limitations**

Berdasarkan dokumentasi model:
- Kadang paraphrase mengandung tanggal yang tidak ada di teks asli
- Model tidak mendukung style variations (friendly, formal, dll)
- Input harus dalam format yang tepat: `"paraphrase: " + text + " </s>"`

## 🔧 Support

Jika ada masalah dengan deployment:
1. Check logs di Coolify dashboard
2. Verify environment variables
3. Test health endpoint
4. Check resource usage
5. Verify model loading in logs

## 📚 References

- [Model Documentation](https://huggingface.co/Wikidepia/IndoT5-base-paraphrase)
- [Training Dataset](https://huggingface.co/datasets/paws)
- [IndoT5 Base Model](https://huggingface.co/indonesian-nlp/indot5-base)
