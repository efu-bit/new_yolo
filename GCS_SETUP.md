# Private GCS Image Proxy Setup Guide

This guide explains how to set up the private Google Cloud Storage (GCS) image proxy system for the Decor Detective application.

## Overview

The system allows serving images from a private GCS bucket through a FastAPI proxy endpoint without exposing direct GCS URLs or using signed URLs. Images are streamed from RAM without being saved to disk.

## Architecture

1. **Database**: Stores only GCS paths (e.g., `gs://bucket/images/cat/123.jpg`)
2. **Proxy Endpoint**: `/images/{filename}` downloads from GCS and streams to frontend
3. **Frontend URLs**: Uses proxy URLs (e.g., `http://localhost:8000/images/images/cat/123.jpg`)
4. **Caching**: Optional RAM cache for improved performance

## Setup Instructions

### 1. GCS Configuration

1. **Create a private GCS bucket** (if not already created)
2. **Create a service account** with Storage Object Viewer permissions
3. **Download the service account JSON key file**

### 2. Environment Configuration

Update your `.env` file with GCS credentials:

```env
# Google Cloud Storage Configuration
GCS_BUCKET_NAME=your-private-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

**Alternative**: Instead of using a service account key file, you can use:
- Application Default Credentials (ADC)
- Workload Identity (for GKE)
- Compute Engine service account (for GCE)

### 3. Install Dependencies

Install the required Google Cloud Storage library:

```bash
pip install google-cloud-storage==2.10.0
```

Or install from requirements.txt:

```bash
pip install -r backend/requirements.txt
```

### 4. Database Schema

Ensure your MongoDB documents have the `original_url` field with GCS paths:

```json
{
  "_id": "...",
  "name": "Modern Chair",
  "price": "$299",
  "original_url": "gs://your-bucket/images/furniture/chair-123.jpg",
  "image_embedding": [0.1, 0.2, ...]
}
```

## Usage

### Frontend Image URLs

The search endpoint now returns proxy URLs instead of direct GCS URLs:

```json
{
  "id": "123",
  "name": "Modern Chair",
  "imageUrl": "http://localhost:8000/images/images/furniture/chair-123.jpg",
  "original_url": "gs://your-bucket/images/furniture/chair-123.jpg"
}
```

### Direct Image Access

You can also access images directly via the proxy endpoint:

```
GET /images/{path-to-image}
```

Example:
```
GET /images/images/furniture/chair-123.jpg
```

## Features

### RAM Caching

- **Cache Size**: 100MB by default (configurable)
- **TTL**: 1 hour (3600 seconds)
- **Cleanup**: Automatic removal of expired and excess items
- **Performance**: Significant improvement for frequently accessed images

### Error Handling

- **404**: Image not found in GCS bucket
- **500**: GCS connection or download errors
- **Graceful Degradation**: System works without GCS if not configured

### HTTP Headers

The proxy endpoint sets appropriate headers:
- `Content-Type`: Based on file extension
- `Cache-Control`: 1-hour public cache
- `Content-Length`: Exact file size

## Testing

### 1. Test GCS Connection

```python
from backend.gcs_service import GCSService

gcs = GCSService()
# Should print: "✅ GCS client initialized for bucket: your-bucket-name"
```

### 2. Test Image Download

```python
image_bytes = gcs.download_image_to_memory("images/test.jpg")
print(f"Downloaded {len(image_bytes)} bytes" if image_bytes else "Failed")
```

### 3. Test Proxy Endpoint

```bash
curl http://localhost:8000/images/images/test.jpg
```

### 4. Test Search Integration

Search results should return proxy URLs in the `imageUrl` field.

## Troubleshooting

### Common Issues

1. **"GCS disabled" message**
   - Check `GCS_BUCKET_NAME` in `.env`
   - Verify service account credentials

2. **"Failed to initialize GCS client"**
   - Check service account JSON file path
   - Verify service account permissions
   - Test network connectivity to GCS

3. **"Image not found in GCS"**
   - Verify the image exists in the bucket
   - Check the path format (no leading slash)
   - Ensure bucket name is correct

4. **404 errors on proxy endpoint**
   - Check if the image path is correct
   - Verify GCS bucket permissions
   - Check service account access

### Performance Optimization

1. **Increase cache size** for frequently accessed images:
   ```python
   gcs = GCSService(cache_size_mb=200)
   ```

2. **Monitor cache hit rate** in logs:
   - Look for "✅ Cache hit" messages
   - High cache hit rate = better performance

3. **Use CDN** in production for additional caching layer

## Security Considerations

1. **Service Account Permissions**: Use minimal required permissions (Storage Object Viewer)
2. **Credential Storage**: Keep service account keys secure and out of version control
3. **Network Security**: Consider VPC/firewall rules for GCS access
4. **Rate Limiting**: Implement rate limiting on the proxy endpoint if needed

## Production Deployment

1. **Environment Variables**: Use secure secret management
2. **Monitoring**: Add metrics for cache hit rate, download times, errors
3. **Scaling**: Consider multiple backend instances with shared cache
4. **CDN Integration**: Add CloudFlare/CloudFront for global distribution
