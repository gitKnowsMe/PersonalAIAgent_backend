# Database Schema and Management

Detailed information about the database structure, models, and management operations.

## Database Architecture

Personal AI Agent uses a relational database for metadata storage with vector databases for semantic search.

### Supported Database Systems

- **SQLite**: Default for development and single-user deployments
- **PostgreSQL**: Recommended for production and multi-user systems

## Core Database Schema

### Users Table

Stores user account information and authentication data.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Features:**
- Unique username and email constraints
- Bcrypt hashed passwords
- Soft delete capability with is_active flag
- Automatic timestamp tracking

### Documents Table

Tracks uploaded PDF documents and their processing status.

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    chunk_count INTEGER DEFAULT 0,
    metadata TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Document Types:**
- `financial`: Bank statements, invoices, receipts
- `long_form`: Research papers, reports, contracts
- `generic`: Resumes, letters, personal documents

**Processing Status:**
- `pending`: Upload received, processing not started
- `processing`: Active text extraction and analysis
- `completed`: Ready for queries
- `failed`: Processing error occurred

### Document Chunks Table

Stores processed text chunks for vector search and retrieval.

```sql
CREATE TABLE document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    metadata TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
```

### Email Messages Table

Tracks processed Gmail messages and their metadata.

```sql
CREATE TABLE email_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    gmail_id VARCHAR(100) NOT NULL,
    thread_id VARCHAR(100) NOT NULL,
    subject TEXT NOT NULL,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    date TIMESTAMP NOT NULL,
    category VARCHAR(50) NOT NULL,
    labels TEXT NULL,
    has_attachments BOOLEAN DEFAULT FALSE,
    content TEXT NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, gmail_id)
);
```

**Email Categories:**
- `business`: Work-related communications
- `personal`: Family and friends
- `promotional`: Marketing and newsletters
- `transactional`: Receipts and confirmations
- `support`: Customer service interactions

### Queries Table

Logs user queries and system responses for analytics and debugging.

```sql
CREATE TABLE queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    response TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL,
    sources_used TEXT NULL,
    processing_time FLOAT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### OAuth Tokens Table

Securely stores Gmail OAuth2 tokens for authenticated API access.

```sql
CREATE TABLE oauth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    service VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NULL,
    token_expiry TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, service)
);
```

## Database Operations

### Initial Setup

Create the database and tables:

```bash
# Initialize database
python setup_db.py

# Verify setup
python -c "from app.db.database import engine; print('Database ready')"
```

### Migrations

Apply database schema changes:

```bash
# General migrations
python migrate_db.py

# Add constraints and indexes
python migrate_db_constraints.py

# Email-specific migrations
python migrate_email_db.py

# Performance optimizations
python migrate_add_performance_indexes.py
```

### Maintenance Operations

```bash
# List all documents
python list_documents.py

# Check database integrity
python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('PRAGMA integrity_check'))
    print(result.fetchall())
"

# Backup database (SQLite)
cp personal_ai_agent.db personal_ai_agent.db.backup

# Compact database
python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('VACUUM'))
"
```

## Performance Optimization

### Indexing Strategy

Key indexes for optimal performance:

```sql
-- User lookup optimization
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Document queries
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_created ON documents(created_at);

-- Chunk retrieval
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_index ON document_chunks(document_id, chunk_index);

-- Email queries
CREATE INDEX idx_emails_user_id ON email_messages(user_id);
CREATE INDEX idx_emails_category ON email_messages(category);
CREATE INDEX idx_emails_date ON email_messages(date);
CREATE INDEX idx_emails_sender ON email_messages(sender);
CREATE INDEX idx_emails_thread ON email_messages(thread_id);

-- Query analytics
CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_queries_created ON queries(created_at);
CREATE INDEX idx_queries_type ON queries(query_type);
```

### Query Optimization

Common query patterns and optimizations:

```python
# Efficient document retrieval
def get_user_documents(user_id: int, document_type: str = None):
    query = session.query(Document).filter(Document.user_id == user_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    return query.order_by(Document.created_at.desc()).all()

# Optimized email search
def get_user_emails(user_id: int, category: str = None, limit: int = 50):
    query = session.query(EmailMessage).filter(EmailMessage.user_id == user_id)
    if category:
        query = query.filter(EmailMessage.category == category)
    return query.order_by(EmailMessage.date.desc()).limit(limit).all()
```

## Data Management

### User Data Isolation

Each user's data is strictly isolated:

```python
# All queries include user_id filter
user_documents = session.query(Document).filter(
    Document.user_id == current_user.id
).all()

# Vector stores use user-specific namespaces
vector_namespace = f"user_{user_id}_doc_{document_id}"
```

### Data Cleanup

Automated cleanup procedures:

```python
# Remove orphaned chunks
def cleanup_orphaned_chunks():
    session.execute(text("""
        DELETE FROM document_chunks 
        WHERE document_id NOT IN (SELECT id FROM documents)
    """))

# Clean old query logs (optional)
def cleanup_old_queries(days: int = 90):
    cutoff_date = datetime.now() - timedelta(days=days)
    session.query(Query).filter(
        Query.created_at < cutoff_date
    ).delete()
```

### Backup Strategies

**Development (SQLite):**
```bash
# Simple file copy
cp personal_ai_agent.db backup_$(date +%Y%m%d).db

# With compression
tar -czf backup_$(date +%Y%m%d).tar.gz personal_ai_agent.db data/
```

**Production (PostgreSQL):**
```bash
# Full database dump
pg_dump personal_ai_agent > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump personal_ai_agent | gzip > backup_$(date +%Y%m%d).sql.gz

# Schema-only backup
pg_dump --schema-only personal_ai_agent > schema_backup.sql
```

## Security Considerations

### Data Protection

- **Password Hashing**: Bcrypt with configurable rounds
- **Token Encryption**: OAuth tokens encrypted at rest
- **SQL Injection Prevention**: Parameterized queries only
- **Access Control**: User-based data isolation

### Audit Logging

Query logging for security and debugging:

```python
def log_query(user_id: int, query_text: str, response: str):
    query_log = Query(
        user_id=user_id,
        query_text=query_text,
        response=response,
        query_type=determine_query_type(query_text),
        created_at=datetime.utcnow()
    )
    session.add(query_log)
    session.commit()
```

## Development Tools

### Database Inspection

```python
# Check table schema
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_columns('documents'))

# Analyze table sizes
def analyze_table_sizes():
    tables = ['users', 'documents', 'document_chunks', 'email_messages', 'queries']
    for table in tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count} rows")
```

### Migration Testing

```python
# Test migration on copy
def test_migration():
    # Create backup
    shutil.copy('personal_ai_agent.db', 'test_migration.db')
    
    # Apply migration to test database
    test_engine = create_engine('sqlite:///test_migration.db')
    # Run migration logic
    
    # Verify results
    # Cleanup test database
    os.remove('test_migration.db')
```

## Troubleshooting

### Common Issues

**Database Lock Errors:**
```bash
# Check for active connections
lsof personal_ai_agent.db

# Force unlock (SQLite)
python -c "
import sqlite3
conn = sqlite3.connect('personal_ai_agent.db')
conn.execute('BEGIN IMMEDIATE;')
conn.rollback()
"
```

**Migration Failures:**
```bash
# Check current schema version
python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    try:
        result = conn.execute(text('SELECT version FROM schema_version'))
        print(result.fetchone())
    except:
        print('No schema version table')
"

# Reset to clean state
rm personal_ai_agent.db
python setup_db.py
```

**Performance Issues:**
```bash
# Analyze query performance
python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('EXPLAIN QUERY PLAN SELECT * FROM documents'))
"

# Rebuild indexes
python migrate_add_performance_indexes.py
```

This database documentation provides a comprehensive overview of the data architecture and management procedures for Personal AI Agent.