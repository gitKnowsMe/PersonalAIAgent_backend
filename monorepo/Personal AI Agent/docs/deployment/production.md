# Production Deployment

Guide for deploying Personal AI Agent in production environments.

## Production Considerations

### Infrastructure Requirements
- **CPU**: 4+ cores recommended
- **Memory**: 16GB+ RAM for optimal performance
- **Storage**: 50GB+ SSD storage
- **Network**: Stable internet for Gmail integration
- **OS**: Ubuntu 20.04 LTS or CentOS 8+ recommended

### Security Requirements
- SSL/TLS certificates for HTTPS
- Firewall configuration
- Regular security updates
- Backup and disaster recovery
- Access control and monitoring

## Deployment Options

### Option 1: Single Server Deployment
Best for small to medium organizations with controlled user base.

**Architecture:**
- Single server running all components
- PostgreSQL database
- Nginx reverse proxy
- SSL termination
- Local file storage

### Option 2: Container Deployment
Recommended for scalable and maintainable deployments.

**Components:**
- Docker containers for application
- Docker Compose or Kubernetes orchestration
- Persistent volumes for data
- Load balancing capabilities

### Option 3: Cloud Deployment
For organizations requiring high availability and scalability.

**Platforms:**
- AWS EC2 with RDS
- Google Cloud Platform
- Azure Virtual Machines
- Digital Ocean Droplets

## Production Configuration

### Environment Variables
```env
# Production Settings
DEBUG=false
ENV=production
HOST=0.0.0.0
PORT=8000

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://user:password@localhost:5432/personal_ai_agent

# Security
SECRET_KEY=your_very_secure_production_key_32_chars_minimum
ACCESS_TOKEN_EXPIRE_MINUTES=15

# CORS (restrict to your domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# File Storage
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/opt/personal-ai-agent/uploads

# Logging
LOG_LEVEL=INFO
```

### Database Setup (PostgreSQL)
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE personal_ai_agent;
CREATE USER aiagent WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE personal_ai_agent TO aiagent;
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/personal-ai-agent/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p data/vector_db static/uploads logs

# Download models (in production, consider using volume mounts)
RUN python download_model.py

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://aiagent:password@db:5432/personal_ai_agent
      - DEBUG=false
    volumes:
      - ./data:/app/data
      - ./static:/app/static
      - ./logs:/app/logs
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=personal_ai_agent
      - POSTGRES_USER=aiagent
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
```

## System Service Setup

### Systemd Service
```ini
# /etc/systemd/system/personal-ai-agent.service
[Unit]
Description=Personal AI Agent
After=network.target

[Service]
Type=simple
User=aiagent
WorkingDirectory=/opt/personal-ai-agent
Environment=PATH=/opt/personal-ai-agent/.venv/bin
ExecStart=/opt/personal-ai-agent/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable personal-ai-agent
sudo systemctl start personal-ai-agent
sudo systemctl status personal-ai-agent
```

## Security Hardening

### Firewall Configuration
```bash
# UFW (Ubuntu Firewall)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Application Security
```bash
# Create dedicated user
sudo useradd -r -s /bin/false aiagent

# Set file permissions
sudo chown -R aiagent:aiagent /opt/personal-ai-agent
sudo chmod -R 750 /opt/personal-ai-agent
```

## Monitoring and Logging

### Log Management
```bash
# Logrotate configuration
# /etc/logrotate.d/personal-ai-agent
/opt/personal-ai-agent/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 aiagent aiagent
}
```

### Health Monitoring
```bash
# Health check script
#!/bin/bash
# /opt/personal-ai-agent/health-check.sh
curl -f http://localhost:8000/api/v1/health-check || exit 1
```

### Application Monitoring
Consider implementing:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **ELK Stack**: Centralized logging
- **Uptime monitoring**: External service monitoring

## Backup and Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
# /opt/personal-ai-agent/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump personal_ai_agent > /backups/db_backup_$DATE.sql
gzip /backups/db_backup_$DATE.sql

# Keep only last 30 days
find /backups -name "db_backup_*.sql.gz" -mtime +30 -delete
```

### File System Backup
```bash
# Backup data and uploads
tar -czf /backups/files_backup_$DATE.tar.gz \
    /opt/personal-ai-agent/data \
    /opt/personal-ai-agent/static/uploads
```

### Recovery Procedures
```bash
# Database recovery
gunzip -c /backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql personal_ai_agent

# File recovery
tar -xzf /backups/files_backup_YYYYMMDD_HHMMSS.tar.gz -C /
```

## Performance Optimization

### Application Performance
- Use Gunicorn with multiple workers
- Implement caching (Redis)
- Optimize database queries
- Monitor resource usage

### Database Optimization
```sql
-- PostgreSQL optimizations
-- Increase shared_buffers
-- Tune work_mem
-- Configure checkpoint settings
-- Add appropriate indexes
```

### Hardware Optimization
- Use SSD storage for database and vector indexes
- Ensure sufficient RAM for model loading
- Consider GPU acceleration where available
- Network optimization for Gmail API calls

## Scaling Considerations

### Horizontal Scaling
- Load balancer configuration
- Shared storage for uploads
- Database clustering
- Session management

### Vertical Scaling
- CPU and memory upgrades
- Storage expansion
- Network bandwidth increase
- GPU addition for AI acceleration

*This production deployment guide provides comprehensive guidance for enterprise-ready deployments of Personal AI Agent.*