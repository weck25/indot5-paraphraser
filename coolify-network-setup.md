# Coolify Network Setup - IndoT5 Paraphraser

## 🚨 **Masalah 405 dan CORS di Coolify**

### **Penyebab Masalah:**
1. **405 Method Not Allowed**: Container tidak bisa akses satu sama lain
2. **CORS Error**: Cross-origin requests diblokir
3. **Network Isolation**: Container terisolasi di Coolify

## 🔧 **Solusi Lengkap**

### **1. Environment Variables untuk Backend**

Update environment variables di backend service:

```bash
# Di Coolify Dashboard > Backend Service > Environment Variables

# IndoT5 API URL - Gunakan service name Coolify
INDOT5_API_URL=http://indot5-paraphraser:5005/paraphrase

# Atau gunakan internal IP jika service name tidak work
# INDOT5_API_URL=http://172.17.0.1:5005/paraphrase

# Tambahan untuk debugging
DEBUG=true
NODE_ENV=production
```

### **2. Coolify Service Configuration**

#### **A. IndoT5 Service Settings:**
```yaml
# Service Name: indot5-paraphraser
# Port: 5005
# Build Command: (kosong)
# Start Command: (kosong)
# Dockerfile Path: Dockerfile

# Environment Variables:
PORT=5005
HOST=0.0.0.0
PYTHONUNBUFFERED=1

# Resource Limits:
Memory: 4GB
CPU: 2 cores

# Health Check:
Path: /health
Interval: 30s
Timeout: 30s
Start Period: 180s
Retries: 3
```

#### **B. Backend Service Settings:**
```yaml
# Service Name: backend
# Port: 3000 (atau port yang Anda gunakan)

# Environment Variables:
INDOT5_API_URL=http://indot5-paraphraser:5005/paraphrase
NODE_ENV=production
```

### **3. Network Configuration**

#### **A. Create Custom Network (jika diperlukan):**
```bash
# SSH ke server Coolify
docker network create coolify-network

# Atau gunakan network default Coolify
docker network ls
```

#### **B. Service Discovery:**
```bash
# Cek service yang running
docker ps

# Cek network
docker network inspect coolify_default

# Test connectivity
docker exec -it backend-container ping indot5-paraphraser
```

### **4. Alternative URL Patterns**

Coba berbagai format URL untuk koneksi:

```bash
# Format 1: Service name
INDOT5_API_URL=http://indot5-paraphraser:5005/paraphrase

# Format 2: Full domain
INDOT5_API_URL=https://indot5-paraphraser.your-domain.com/paraphrase

# Format 3: Internal IP
INDOT5_API_URL=http://172.17.0.1:5005/paraphrase

# Format 4: Localhost dengan port mapping
INDOT5_API_URL=http://localhost:5005/paraphrase
```

### **5. Testing Connectivity**

#### **A. Test dari Backend Container:**
```bash
# Masuk ke backend container
docker exec -it backend-container bash

# Test curl
curl -X GET http://indot5-paraphraser:5005/health
curl -X POST http://indot5-paraphraser:5005/paraphrase \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "max_length": 512}'
```

#### **B. Test dari Host:**
```bash
# Test health endpoint
curl http://your-domain:5005/health

# Test paraphrase endpoint
curl -X POST http://your-domain:5005/paraphrase \
  -H "Content-Type: application/json" \
  -d '{"text": "Anak anak melakukan piket kelas", "max_length": 512}'
```

### **6. Debugging Steps**

#### **A. Check Logs:**
```bash
# IndoT5 service logs
docker logs indot5-paraphraser

# Backend service logs
docker logs backend-container

# Check for CORS errors
grep -i "cors\|405\|method" /var/log/nginx/error.log
```

#### **B. Check Network:**
```bash
# List all containers
docker ps -a

# Check network connectivity
docker network inspect coolify_default

# Test DNS resolution
docker exec -it backend-container nslookup indot5-paraphraser
```

### **7. Coolify-Specific Solutions**

#### **A. Use Coolify Proxy:**
```bash
# Jika Coolify menggunakan reverse proxy
INDOT5_API_URL=http://nginx:80/indot5-paraphraser/paraphrase
```

#### **B. Use External Domain:**
```bash
# Deploy IndoT5 dengan domain terpisah
INDOT5_API_URL=https://indot5-api.your-domain.com/paraphrase
```

#### **C. Use Port Mapping:**
```bash
# Map port di Coolify
INDOT5_API_URL=http://your-server-ip:5005/paraphrase
```

### **8. Updated Backend Configuration**

Update `backend/utils/paraphraser.js` untuk better error handling:

```javascript
// === PROVIDER: IndoT5 FastAPI Local ===
async function paraphraseWithIndoT5(text, { style, lang }) {
  // Hanya gunakan untuk bahasa Indonesia
  if (lang !== 'id') return null;
  try {
    const payload = { 
      text, 
      max_length: 512,
      num_return_sequences: 1
    };
    
    const apiUrl = process.env.INDOT5_API_URL || 'http://localhost:5005/paraphrase';
    console.log(`[Paraphrase] Calling IndoT5 API: ${apiUrl}`);
    
    const res = await axios.post(apiUrl, payload, { 
      timeout: 20000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    if (res.data && res.data.result) {
      console.log(`[Paraphrase] IndoT5 success: ${res.data.result}`);
      return res.data.result;
    }
    return null;
  } catch (e) {
    console.error('[Paraphrase] IndoT5 FastAPI failed:', e.message);
    console.error('[Paraphrase] Error details:', e.response?.data || e.code);
    return null;
  }
}
```

### **9. Health Check Script**

Buat script untuk test koneksi:

```bash
#!/bin/bash
# test-connection.sh

echo "Testing IndoT5 API connection..."

# Test health endpoint
echo "1. Testing health endpoint..."
curl -f http://indot5-paraphraser:5005/health || echo "Health check failed"

# Test paraphrase endpoint
echo "2. Testing paraphrase endpoint..."
curl -X POST http://indot5-paraphraser:5005/paraphrase \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "max_length": 512}' || echo "Paraphrase test failed"

echo "Connection test completed."
```

### **10. Troubleshooting Checklist**

- [ ] IndoT5 service running dan healthy
- [ ] Environment variables set dengan benar
- [ ] Network connectivity antara container
- [ ] CORS headers configured
- [ ] Port mapping correct
- [ ] Service discovery working
- [ ] DNS resolution working
- [ ] Firewall rules allow traffic

## 🚀 **Quick Fix Steps**

1. **Restart kedua service** di Coolify
2. **Update environment variables** dengan service name
3. **Check health endpoint** dari browser
4. **Test dari backend container** menggunakan curl
5. **Check logs** untuk error details

## 📞 **Support**

Jika masih bermasalah:
1. Check Coolify logs di dashboard
2. Verify network configuration
3. Test dengan external domain
4. Contact Coolify support jika diperlukan
