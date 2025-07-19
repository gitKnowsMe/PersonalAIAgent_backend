# Security Guide

Comprehensive security considerations and best practices for Personal AI Agent deployment.

## Security Architecture

Personal AI Agent is designed with privacy and security as core principles:

- **Local Processing**: All document analysis happens locally
- **Data Isolation**: User data is strictly separated
- **Minimal External Calls**: Only Gmail OAuth requires external access
- **Encrypted Communications**: HTTPS for all web communications
- **Secure Authentication**: JWT-based with configurable expiration

## Authentication Security

### JWT Token Security
```env
# Use strong, random secret keys (32+ characters)
SECRET_KEY=your_cryptographically_secure_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15  # Short expiration for security
```

### Password Security
- **Bcrypt Hashing**: Industry-standard password hashing
- **Configurable Rounds**: Adjustable computational cost
- **No Plain Text Storage**: Passwords never stored in plain text

```python
# Password hashing configuration
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### Session Management
- **Stateless JWT**: No server-side session storage
- **Automatic Expiration**: Configurable token lifetime
- **Secure Headers**: HTTP-only, secure cookie attributes

## Data Privacy

### Local Data Processing
- **No External AI APIs**: All LLM processing happens locally
- **Local Vector Storage**: FAISS indices stored locally
- **Local Database**: User data in local SQLite/PostgreSQL

### User Data Isolation
```python
# All database queries include user isolation
user_documents = session.query(Document).filter(
    Document.user_id == current_user.id
).all()

# Vector store namespacing
namespace = f"user_{user_id}_doc_{document_id}"
```

### Data Encryption
- **OAuth Tokens**: Encrypted at rest
- **Database Encryption**: Optional full database encryption
- **File System**: Recommend encrypted storage volumes

## Gmail Integration Security

### OAuth2 Implementation
- **Standard OAuth2 Flow**: Industry-standard authentication
- **Minimal Scopes**: Request only necessary permissions
- **Secure Token Storage**: Encrypted refresh tokens
- **Token Rotation**: Automatic token refresh

```python
# OAuth scopes (read-only)
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly'
]
```

### API Security
- **Rate Limiting**: Respect Gmail API quotas
- **Error Handling**: Secure error messages
- **Token Validation**: Verify token authenticity
- **Secure Callbacks**: HTTPS-only redirect URIs

## Network Security

### HTTPS Configuration
```nginx
# Force HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# SSL configuration
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
}
```

### CORS Security
```python
# Restrict CORS to specific domains
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Input Validation and Sanitization

### File Upload Security
```python
# File type validation
ALLOWED_MIME_TYPES = ['application/pdf']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_upload(file):
    # Check file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Invalid file type")
    
    # Check file size
    if len(file.file.read()) > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    # Reset file pointer
    file.file.seek(0)
```

### Query Input Sanitization
```python
# Sanitize user queries
def sanitize_query(query: str) -> str:
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', query)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()
```

### SQL Injection Prevention
- **Parameterized Queries**: Always use SQLAlchemy ORM
- **Input Validation**: Validate all user inputs
- **Least Privilege**: Database users with minimal permissions

```python
# Safe query example
documents = session.query(Document).filter(
    Document.user_id == user_id,
    Document.filename.like(f"%{search_term}%")
).all()
```

## System Security

### File System Security
```bash
# Secure file permissions
sudo chown -R aiagent:aiagent /opt/personal-ai-agent
sudo chmod -R 750 /opt/personal-ai-agent

# Sensitive files
sudo chmod 600 /opt/personal-ai-agent/.env
sudo chmod 600 /opt/personal-ai-agent/personal_ai_agent.db
```

### Process Security
```bash
# Run as non-root user
sudo useradd -r -s /bin/false aiagent

# Systemd service with restricted permissions
[Service]
User=aiagent
Group=aiagent
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
```

### Log Security
```python
# Secure logging configuration
import logging

# Avoid logging sensitive data
class SecureFormatter(logging.Formatter):
    def format(self, record):
        # Sanitize log messages
        record.msg = self.sanitize_message(record.msg)
        return super().format(record)
    
    def sanitize_message(self, message):
        # Remove tokens, passwords, etc.
        return re.sub(r'token=\w+', 'token=***', str(message))
```

## Vulnerability Management

### Security Headers
```python
# FastAPI security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])

# Custom security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### Dependency Security
```bash
# Regular security updates
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Security scanning
pip install safety
safety check

# Vulnerability scanning
pip install bandit
bandit -r app/
```

### Regular Security Audits
```bash
# Automated security checks
#!/bin/bash
# security-audit.sh

echo "Running security audit..."

# Check for updates
echo "Checking for system updates..."
sudo apt list --upgradable

# Python security check
echo "Checking Python dependencies..."
safety check

# File permission check
echo "Checking file permissions..."
find /opt/personal-ai-agent -type f -perm /o+w

# Log file analysis
echo "Checking logs for suspicious activity..."
grep -i "error\|fail\|attack" /opt/personal-ai-agent/logs/app.log
```

## Backup Security

### Encrypted Backups
```bash
# Encrypted database backup
pg_dump personal_ai_agent | gpg --cipher-algo AES256 --compress-algo 1 \
    --symmetric --output backup_$(date +%Y%m%d).sql.gpg

# Encrypted file backup
tar -czf - /opt/personal-ai-agent/data | gpg --cipher-algo AES256 \
    --symmetric --output data_backup_$(date +%Y%m%d).tar.gz.gpg
```

### Secure Backup Storage
- **Off-site Storage**: Store backups in different location
- **Access Control**: Limit backup access to authorized personnel
- **Encryption**: Always encrypt sensitive backups
- **Rotation**: Regular backup rotation and testing

## Incident Response

### Security Monitoring
```python
# Security event logging
def log_security_event(event_type: str, user_id: int, details: str):
    security_logger.warning(
        f"Security event: {event_type} for user {user_id}: {details}"
    )
```

### Incident Response Plan
1. **Detection**: Monitoring and alerting systems
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Improve security measures

### Security Alerts
```bash
# Failed login monitoring
tail -f /opt/personal-ai-agent/logs/app.log | \
    grep "authentication failed" | \
    while read line; do
        echo "Security Alert: $line" | mail -s "Failed Login" admin@domain.com
    done
```

## Compliance and Privacy

### Data Protection Principles
- **Data Minimization**: Collect only necessary data
- **Purpose Limitation**: Use data only for stated purposes
- **Storage Limitation**: Retain data only as long as necessary
- **Accuracy**: Keep data accurate and up-to-date
- **Security**: Implement appropriate technical measures

### User Rights
- **Access**: Users can view their data
- **Rectification**: Users can correct inaccurate data
- **Erasure**: Users can delete their data
- **Portability**: Users can export their data

```python
# Data deletion implementation
async def delete_user_data(user_id: int):
    # Delete database records
    session.query(Document).filter(Document.user_id == user_id).delete()
    session.query(EmailMessage).filter(EmailMessage.user_id == user_id).delete()
    
    # Delete vector indices
    user_vector_pattern = f"user_{user_id}_*"
    for vector_file in glob.glob(f"data/vector_db/**/{user_vector_pattern}"):
        os.remove(vector_file)
    
    # Delete uploaded files
    user_upload_dir = f"static/uploads/{user_id}"
    if os.path.exists(user_upload_dir):
        shutil.rmtree(user_upload_dir)
```

## Security Testing

### Penetration Testing Checklist
- [ ] Authentication bypass attempts
- [ ] SQL injection testing
- [ ] Cross-site scripting (XSS) tests
- [ ] File upload vulnerabilities
- [ ] API endpoint security
- [ ] Session management testing
- [ ] Input validation testing

### Security Automation
```bash
# Automated security testing
#!/bin/bash
# security-test.sh

# OWASP ZAP automated scan
zap-baseline.py -t http://localhost:8000

# SQLMap testing
sqlmap -u "http://localhost:8000/api/v1/login" --batch

# SSL testing
sslyze --regular localhost:8000
```

This security guide provides comprehensive coverage of security considerations for Personal AI Agent. Regular security reviews and updates are essential for maintaining a secure deployment.