# IndoT5 Paraphraser API

Indonesian text paraphrasing service menggunakan model [Wikidepia/IndoT5-base-paraphrase](https://huggingface.co/Wikidepia/IndoT5-base-paraphrase) yang dioptimalkan untuk paraphrasing bahasa Indonesia.

## 🚀 Fitur

- **High-quality paraphrasing**: Menggunakan model IndoT5 yang dilatih khusus untuk paraphrasing
- **Batch processing**: Paraphrase multiple texts sekaligus
- **Multiple variations**: Generate hingga 5 variasi paraphrase
- **Health monitoring**: Built-in health checks
- **Docker support**: Easy deployment dengan Docker
- **RESTful API**: FastAPI dengan dokumentasi otomatis
- **Error handling**: Comprehensive error handling dan logging

## 📋 Requirements

- Docker & Docker Compose
- Minimum 2GB RAM (4GB recommended)
- Internet connection untuk download model

## 🐳 Deployment dengan Docker

### Quick Start

```bash
# Clone atau download files
cd indot5-paraphraser

# Build dan run dengan Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:5005/health
```

### Manual Docker Build

```bash
# Build image
docker build -t indot5-paraphraser .

# Run container
docker run -d \
  --name indot5-paraphraser \
  -p 5005:5005 \
  --restart unless-stopped \
  indot5-paraphraser
```

## 🔧 Konfigurasi

### Environment Variables

```bash
# Port (default: 5005)
PORT=5005

# Host (default: 0.0.0.0)
HOST=0.0.0.0

# Python settings
PYTHONUNBUFFERED=1
```

### Docker Compose Override

Buat file `docker-compose.override.yml` untuk custom configuration:

```yaml
version: '3.8'
services:
  indot5-paraphraser:
    environment:
      - PORT=5005
      - HOST=0.0.0.0
    volumes:
      - ./logs:/app/logs
      - model_cache:/root/.cache/huggingface
```

## 📚 API Documentation

### Base URL
```
http://localhost:5005
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "is_model_loaded": true,
  "device": "cpu",
  "uptime": 1234.56
}
```

#### 2. Single Paraphrase
```http
POST /paraphrase
Content-Type: application/json

{
  "text": "Anak anak melakukan piket kelas agar kebersihan kelas terjaga",
  "max_length": 512,
  "num_return_sequences": 1
}
```

Response:
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

#### 3. Batch Paraphrase
```http
POST /batch-paraphrase
Content-Type: application/json

[
  {
    "text": "Anak anak melakukan piket kelas agar kebersihan kelas terjaga",
    "max_length": 512
  },
  {
    "text": "Terima kasih atas bantuannya",
    "max_length": 512
  }
]
```

### Model Information

Model ini menggunakan format input khusus:
- **Input format**: `"paraphrase: " + text + " </s>"`
- **Training**: Dilatih pada dataset PAWS yang diterjemahkan ke bahasa Indonesia
- **Capabilities**: Generate paraphrase yang natural dan kontekstual

### Parameters

- **text**: Teks yang akan diparafrase (required)
- **max_length**: Panjang maksimum output (default: 512, max: 512)
- **num_return_sequences**: Jumlah variasi paraphrase (default: 1, max: 5)
- **style**: Tidak digunakan (model tidak mendukung style variations)

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:5005/health
```

### Logs
```bash
# Docker Compose
docker-compose logs -f indot5-paraphraser

# Docker
docker logs -f indot5-paraphraser
```

### Metrics
- Processing time per request
- Model loading status
- Device utilization (CPU/GPU)
- Uptime

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

### Testing

```bash
# Test health endpoint
curl http://localhost:5005/health

# Test paraphrase endpoint
curl -X POST http://localhost:5005/paraphrase \
  -H "Content-Type: application/json" \
  -d '{"text": "Anak anak melakukan piket kelas agar kebersihan kelas terjaga"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Model loading fails**
   ```bash
   # Check logs
   docker-compose logs indot5-paraphraser
   
   # Restart service
   docker-compose restart indot5-paraphraser
   ```

2. **Out of memory**
   ```bash
   # Increase memory limit in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 6G
   ```

3. **Port already in use**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "5006:5005"  # Use port 5006 instead
   ```

### Performance Optimization

1. **GPU Support** (if available)
   ```yaml
   # Add to docker-compose.yml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

2. **Model Caching**
   ```yaml
   # Mount model cache volume
   volumes:
     - model_cache:/root/.cache/huggingface
   ```

## 📊 Performance

- **Model Size**: ~850MB
- **Memory Usage**: ~2-4GB
- **Response Time**: 1-3 seconds (CPU)
- **Throughput**: ~5-10 requests/second (CPU)

## 🔒 Security

- Non-root user dalam container
- Input validation dan sanitization
- Rate limiting (implementasi di reverse proxy)
- CORS configuration

## 📝 License

MIT License

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 Support

Untuk bantuan dan pertanyaan:
- Create issue di repository
- Email: support@example.com
- Documentation: `/docs` (Swagger UI)

## 🙏 Acknowledgement

Model ini menggunakan [Wikidepia/IndoT5-base-paraphrase](https://huggingface.co/Wikidepia/IndoT5-base-paraphrase) yang dilatih pada dataset PAWS yang diterjemahkan ke bahasa Indonesia. Terima kasih kepada Tensorflow Research Cloud untuk menyediakan TPU v3-8s untuk training.
