# PostgreSQL Database Documentation

## Personal AI Agent Multi-User Database System

This document provides comprehensive information about the PostgreSQL database implementation for the Personal AI Agent's multi-user system.

## Database Configuration

### Connection Details
- **Host**: localhost
- **Port**: 5432
- **Database Name**: `personal_ai_agent_dev`
- **Username**: `personal_ai_agent`
- **Password**: `dev_password`
- **Connection URL**: `postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev`
- **Async Connection URL**: `postgresql+asyncpg://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev`

### Connection Pool Configuration
```python
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
DATABASE_HEALTH_CHECK_INTERVAL = 60
```

## Database Evolution History

### Phase 1: Initial Setup
- **Original System**: SQLite-based single-user system
- **Migration Need**: Required multi-user support with data isolation
- **Target**: PostgreSQL with Row-Level Security (RLS)

### Phase 2: Multi-User Database Implementation
**Date**: August 2025  
**Objective**: Implement multi-user database system with Row-Level Security

#### Key Changes:
1. **Database Migration**: SQLite → PostgreSQL
2. **User Management**: Added comprehensive user system
3. **Session Management**: JWT-linked database sessions
4. **Connection Pooling**: AsyncAdaptedQueuePool implementation
5. **Row-Level Security**: User data isolation

### Phase 3: API Integration & Statistics Fix
**Date**: August 2025  
**Objective**: Complete multi-user API integration and fix statistics

#### Key Changes:
1. **JWT Authentication**: Fixed token validation
2. **Statistics System**: Corrected table references
3. **Data Isolation**: Verified RLS functionality
4. **API Updates**: All endpoints updated for multi-user support

## Database Schema

### Complete Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PERSONAL AI AGENT DATABASE SCHEMA                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐
│             USERS                    │
├──────────────────────────────────────┤
│ • id (SERIAL, PK)                   │
│ • uuid (UUID, UNIQUE)               │
│ • username (VARCHAR, UNIQUE)        │
│ • email (VARCHAR, UNIQUE)           │
│ • password_hash (VARCHAR)           │
│ • first_name (VARCHAR)              │
│ • last_name (VARCHAR)               │
│ • is_active (BOOLEAN)               │
│ • is_admin (BOOLEAN)                │
│ • created_at (TIMESTAMPTZ)          │
│ • last_login (TIMESTAMPTZ)          │
│ • storage_used_mb (INTEGER)         │
└──────────────────────────────────────┘
              │
              ├─────────────────────────────────────────┐
              │                                         │
              ▼                                         ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│         USER_SESSIONS                │  │           DOCUMENTS                  │
├──────────────────────────────────────┤  ├──────────────────────────────────────┤
│ • id (UUID, PK)                     │  │ • id (SERIAL, PK)                   │
│ • user_id (INTEGER, FK→users)       │  │ • title (VARCHAR)                   │
│ • session_token (UUID, UNIQUE)      │  │ • description (TEXT)                │
│ • expires_at (TIMESTAMPTZ)          │  │ • file_path (VARCHAR)               │
│ • created_at (TIMESTAMPTZ)          │  │ • file_type (VARCHAR)               │
│ • last_accessed (TIMESTAMPTZ)       │  │ • document_type (VARCHAR)           │
│ • ip_address (INET)                 │  │ • file_size (INTEGER)               │
│ • user_agent (TEXT)                 │  │ • created_at (TIMESTAMPTZ)          │
│ • is_active (BOOLEAN)               │  │ • vector_namespace (VARCHAR)        │
└──────────────────────────────────────┘  │ • owner_id (INTEGER, FK→users)      │
                                          └──────────────────────────────────────┘
              │                                         │
              │                                         │
              ▼                                         ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│            EMAILS                    │  │           QUERIES                    │
├──────────────────────────────────────┤  ├──────────────────────────────────────┤
│ • id (SERIAL, PK)                   │  │ • id (SERIAL, PK)                   │
│ • email_account_id (INTEGER)        │  │ • question (TEXT)                   │
│ • user_id (INTEGER, FK→users)       │  │ • answer (TEXT)                     │
│ • message_id (VARCHAR)              │  │ • created_at (TIMESTAMPTZ)          │
│ • thread_id (VARCHAR)               │  │ • user_id (INTEGER, FK→users)       │
│ • subject (VARCHAR)                 │  │ • document_id (INTEGER, FK→docs)    │
│ • sender_email (VARCHAR)            │  └──────────────────────────────────────┘
│ • sender_name (VARCHAR)             │
│ • recipient_emails (TEXT)           │
│ • cc_emails (TEXT)                  │  ┌──────────────────────────────────────┐
│ • bcc_emails (TEXT)                 │  │        EMAIL_ACCOUNTS                │
│ • body_text (TEXT)                  │  ├──────────────────────────────────────┤
│ • body_html (TEXT)                  │  │ • id (SERIAL, PK)                   │
│ • email_type (VARCHAR)              │  │ • user_id (INTEGER, FK→users)       │
│ • is_read (BOOLEAN)                 │  │ • email_address (VARCHAR)           │
│ • is_important (BOOLEAN)            │  │ • provider (VARCHAR)                │
│ • has_attachments (BOOLEAN)         │  │ • is_active (BOOLEAN)               │
│ • gmail_labels (TEXT)               │  │ • created_at (TIMESTAMPTZ)          │
│ • sent_at (TIMESTAMPTZ)             │  │ • last_sync (TIMESTAMPTZ)           │
│ • created_at (TIMESTAMPTZ)          │  └──────────────────────────────────────┘
│ • vector_namespace (VARCHAR)        │
└──────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│       EMAIL_ATTACHMENTS              │  │       USER_OAUTH_TOKENS              │
├──────────────────────────────────────┤  ├──────────────────────────────────────┤
│ • id (SERIAL, PK)                   │  │ • id (SERIAL, PK)                   │
│ • email_id (INTEGER, FK→emails)     │  │ • user_id (INTEGER, FK→users)       │
│ • filename (VARCHAR)                │  │ • provider (VARCHAR)                │
│ • content_type (VARCHAR)            │  │ • access_token (TEXT)               │
│ • file_size (INTEGER)               │  │ • refresh_token (TEXT)              │
│ • attachment_id (VARCHAR)           │  │ • token_type (VARCHAR)              │
│ • created_at (TIMESTAMPTZ)          │  │ • expires_at (TIMESTAMPTZ)          │
└──────────────────────────────────────┘  │ • scope (TEXT)                      │
                                          │ • created_at (TIMESTAMPTZ)          │
┌──────────────────────────────────────┐  │ • updated_at (TIMESTAMPTZ)          │
│        OAUTH_SESSIONS                │  └──────────────────────────────────────┘
├──────────────────────────────────────┤
│ • id (UUID, PK)                     │  ┌──────────────────────────────────────┐
│ • user_id (INTEGER, FK→users)       │  │        SCHEMA_VERSIONS               │
│ • provider (VARCHAR)                │  ├──────────────────────────────────────┤
│ • state (VARCHAR)                   │  │ • id (SERIAL, PK)                   │
│ • code_verifier (VARCHAR)           │  │ • version (VARCHAR)                 │
│ • redirect_uri (VARCHAR)            │  │ • description (TEXT)                │
│ • expires_at (TIMESTAMPTZ)          │  │ • applied_at (TIMESTAMPTZ)          │
│ • created_at (TIMESTAMPTZ)          │  └──────────────────────────────────────┘
└──────────────────────────────────────┘
                                          ┌──────────────────────────────────────┐
                                          │         SYSTEM_LOGS                  │
                                          ├──────────────────────────────────────┤
                                          │ • id (SERIAL, PK)                   │
                                          │ • user_id (INTEGER, FK→users)       │
                                          │ • level (VARCHAR)                   │
                                          │ • message (TEXT)                    │
                                          │ • metadata (JSONB)                  │
                                          │ • created_at (TIMESTAMPTZ)          │
                                          └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 RELATIONSHIPS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • users.id ←→ user_sessions.user_id (1:N)                                     │
│ • users.id ←→ documents.owner_id (1:N)                                        │
│ • users.id ←→ emails.user_id (1:N)                                            │
│ • users.id ←→ queries.user_id (1:N)                                           │
│ • users.id ←→ email_accounts.user_id (1:N)                                    │
│ • users.id ←→ user_oauth_tokens.user_id (1:N)                                 │
│ • users.id ←→ oauth_sessions.user_id (1:N)                                    │
│ • emails.id ←→ email_attachments.email_id (1:N)                               │
│ • documents.id ←→ queries.document_id (1:N, optional)                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Database Design Principles

**Multi-Tenant Architecture**: Each user's data is completely isolated through Row-Level Security (RLS)

**Data Relationships**: 
- **User-Centric**: All content tables reference `users.id` as foreign key
- **Cascade Deletion**: User deletion automatically removes all associated data
- **Optional References**: Some relationships are optional (queries ↔ documents)

**Security Model**:
- **Row-Level Security (RLS)**: Automatic data filtering by user context
- **Session Management**: JWT tokens tracked in `user_sessions` table
- **OAuth Integration**: Secure token storage for external services

### Core Tables

#### 1. Users Table
**Purpose**: Central user management with authentication
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_admin BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    storage_used_mb INTEGER DEFAULT 0
);
```

**Key Features**:
- UUID for external references
- bcrypt password hashing
- User status tracking
- Admin role support
- Storage tracking

#### 2. User Sessions Table
**Purpose**: JWT token session management
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token UUID NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL
);
```

**Key Features**:
- JWT token tracking
- Automatic expiration
- IP and user agent logging
- Cascade deletion with users

#### 3. Documents Table
**Purpose**: User document management with ownership
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    vector_namespace VARCHAR(255) NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
```

**Key Features**:
- User ownership via `owner_id`
- File metadata tracking
- Vector namespace for embeddings
- Automatic cascade deletion

#### 4. Emails Table
**Purpose**: Multi-user email management
```sql
CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    email_account_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255),
    subject VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    recipient_emails TEXT,
    cc_emails TEXT,
    bcc_emails TEXT,
    body_text TEXT,
    body_html TEXT,
    email_type VARCHAR(50) NOT NULL DEFAULT 'inbox',
    is_read BOOLEAN DEFAULT false NOT NULL,
    is_important BOOLEAN DEFAULT false NOT NULL,
    has_attachments BOOLEAN DEFAULT false NOT NULL,
    gmail_labels TEXT,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    vector_namespace VARCHAR(255)
);
```

**Key Features**:
- User ownership via `user_id`
- Gmail integration support
- Email metadata and content
- Vector namespace for embeddings

#### 5. Queries Table
**Purpose**: User query history and AI responses
```sql
CREATE TABLE queries (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL
);
```

**Key Features**:
- User ownership via `user_id`
- Optional document association
- Question-answer tracking

#### 6. Supporting Tables

**Email Accounts**: Email account management per user
```sql
CREATE TABLE email_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_address VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL DEFAULT 'gmail',
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_sync TIMESTAMP WITH TIME ZONE
);
```

**Email Attachments**: Email attachment metadata
```sql
CREATE TABLE email_attachments (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size INTEGER DEFAULT 0,
    attachment_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

**OAuth Sessions**: OAuth flow management
```sql
CREATE TABLE oauth_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    state VARCHAR(255) NOT NULL,
    code_verifier VARCHAR(255),
    redirect_uri VARCHAR(500),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

**User OAuth Tokens**: OAuth token storage
```sql
CREATE TABLE user_oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE,
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

**Schema Versions**: Database migration tracking
```sql
CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

**System Logs**: Application logging
```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### Database Indexes and Performance

#### Primary Indexes (Automatic)
All tables have primary key indexes created automatically:
```sql
-- Automatically created
CREATE INDEX users_pkey ON users(id);
CREATE INDEX documents_pkey ON documents(id);
CREATE INDEX emails_pkey ON emails(id);
-- ... etc for all primary keys
```

#### Foreign Key Indexes
Essential for join performance and RLS filtering:
```sql
-- User relationship indexes (critical for RLS performance)
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_documents_owner_id ON documents(owner_id);
CREATE INDEX idx_emails_user_id ON emails(user_id);
CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_email_accounts_user_id ON email_accounts(user_id);
CREATE INDEX idx_user_oauth_tokens_user_id ON user_oauth_tokens(user_id);
CREATE INDEX idx_oauth_sessions_user_id ON oauth_sessions(user_id);
CREATE INDEX idx_email_attachments_email_id ON email_attachments(email_id);

-- Optional relationship indexes
CREATE INDEX idx_queries_document_id ON queries(document_id);
```

#### Unique Constraint Indexes
For data integrity and fast lookups:
```sql
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_uuid ON users(uuid);
CREATE UNIQUE INDEX idx_user_sessions_token ON user_sessions(session_token);
```

#### Performance Optimization Indexes
For common query patterns:
```sql
-- Session management (JWT validation)
CREATE INDEX idx_user_sessions_active ON user_sessions(user_id, is_active, expires_at);

-- Email searching and filtering
CREATE INDEX idx_emails_user_type ON emails(user_id, email_type);
CREATE INDEX idx_emails_user_sent_at ON emails(user_id, sent_at DESC);
CREATE INDEX idx_emails_thread_id ON emails(thread_id);

-- Document searching
CREATE INDEX idx_documents_user_type ON documents(owner_id, document_type);
CREATE INDEX idx_documents_user_created ON documents(owner_id, created_at DESC);

-- OAuth token management
CREATE INDEX idx_oauth_tokens_user_provider ON user_oauth_tokens(user_id, provider);
CREATE INDEX idx_oauth_sessions_state ON oauth_sessions(state);

-- System performance
CREATE INDEX idx_system_logs_user_created ON system_logs(user_id, created_at DESC);
CREATE INDEX idx_system_logs_level_created ON system_logs(level, created_at DESC);
```

#### Row-Level Security Indexes
Specialized indexes for RLS performance:
```sql
-- These indexes are crucial for RLS filtering performance
-- They allow PostgreSQL to quickly filter rows by user context

-- Current user context filtering (used by RLS policies)
CREATE INDEX idx_documents_rls ON documents(owner_id) 
WHERE owner_id = current_setting('app.current_user_id', true)::integer;

CREATE INDEX idx_emails_rls ON emails(user_id) 
WHERE user_id = current_setting('app.current_user_id', true)::integer;

CREATE INDEX idx_queries_rls ON queries(user_id) 
WHERE user_id = current_setting('app.current_user_id', true)::integer;
```

### Query Performance Guidelines

#### Fast User Data Retrieval
```sql
-- GOOD: Uses index on owner_id
SELECT * FROM documents WHERE owner_id = 123;

-- GOOD: Uses composite index
SELECT * FROM emails WHERE user_id = 123 AND email_type = 'inbox';

-- GOOD: Uses index with ordering
SELECT * FROM emails WHERE user_id = 123 ORDER BY sent_at DESC LIMIT 10;
```

#### Efficient Session Management
```sql
-- GOOD: Uses unique index on session_token
SELECT u.* FROM users u 
JOIN user_sessions s ON u.id = s.user_id 
WHERE s.session_token = $1 AND s.is_active = true AND s.expires_at > NOW();
```

#### Optimal Statistics Queries
```sql
-- GOOD: Uses indexes for counting
SELECT 
    (SELECT COUNT(*) FROM documents WHERE owner_id = $1) as doc_count,
    (SELECT COUNT(*) FROM emails WHERE user_id = $1) as email_count,
    (SELECT COUNT(*) FROM queries WHERE user_id = $1) as query_count;
```

### Index Maintenance

#### Monitoring Index Usage
```sql
-- Check index usage statistics
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;

-- Find unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0 AND idx_tup_fetch = 0;
```

#### Index Size Monitoring
```sql
-- Monitor index sizes
SELECT schemaname, tablename, indexname, 
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Row-Level Security (RLS)

### Implementation
The database uses Row-Level Security to ensure complete data isolation between users.

### User Context Setting
```sql
SELECT set_config('app.current_user_id', '{user_id}', true);
```

### RLS Policies
Each table with user data has RLS policies that automatically filter data based on the current user context.

**Example Policy Structure**:
- **Documents**: `owner_id = current_setting('app.current_user_id')::integer`
- **Emails**: `user_id = current_setting('app.current_user_id')::integer`
- **Queries**: `user_id = current_setting('app.current_user_id')::integer`

## Connection Management

### AsyncAdaptedQueuePool Configuration
```python
engine = create_async_engine(
    database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=10,              # Base connections
    max_overflow=20,           # Additional connections
    pool_timeout=30,           # Connection timeout
    pool_recycle=3600,         # Connection recycling
    pool_pre_ping=True,        # Connection validation
    pool_reset_on_return='commit',
    echo=False,                # SQL logging in debug
    future=True,
    connect_args={
        "server_settings": {
            "application_name": "PersonalAIAgent_Multi",
            "jit": "off"
        }
    }
)
```

### Health Monitoring
- **Background Task**: Continuous health monitoring
- **Metrics Tracking**: Connection attempts, failures, query times
- **Pool Statistics**: Utilization, overflow usage
- **Recommendations**: Automatic pool optimization suggestions

## Statistics System

### User Statistics Queries
The statistics system tracks:

1. **Document Count**:
   ```sql
   SELECT COUNT(*) FROM documents WHERE owner_id = :user_id
   ```

2. **Email Count**:
   ```sql
   SELECT COUNT(*) FROM emails WHERE user_id = :user_id
   ```

3. **Query Count**:
   ```sql
   SELECT COUNT(*) FROM queries WHERE user_id = :user_id
   ```

4. **Storage Usage**:
   ```sql
   SELECT COALESCE(SUM(file_size), 0) FROM documents WHERE owner_id = :user_id
   ```

### Performance Optimization
- **Indexes**: Optimized indexes on foreign keys
- **Query Optimization**: Efficient user-specific queries
- **Connection Reuse**: Pool-based connection management

## Authentication Flow

### User Registration
1. **Password Hashing**: bcrypt with salt rounds
2. **UUID Generation**: Unique user identifier
3. **Database Insert**: User record creation
4. **Validation**: Username/email uniqueness

### Login Process
1. **Credential Verification**: Username/password validation
2. **JWT Token Generation**: Secure token creation
3. **Session Creation**: Database session record
4. **Response**: Token with user data

### Token Validation
1. **JWT Decode**: Token signature verification
2. **User Lookup**: Database user verification
3. **Context Setting**: RLS user context
4. **Authorization**: Protected endpoint access

## Migration History

### Migration 1: PostgreSQL Setup
- Created initial PostgreSQL database
- Set up user and permissions
- Configured connection parameters

### Migration 2: Multi-User Schema
- Added users table with UUID support
- Implemented user sessions table
- Updated existing tables with user references
- Added Row-Level Security policies

### Migration 3: Statistics Fix
- Corrected table name references
- Updated foreign key relationships
- Optimized query performance
- Added proper indexes

### Migration 4: Authentication Enhancement
- Fixed JWT token validation
- Added session cleanup procedures
- Enhanced security measures
- Improved error handling

## Security Measures

### Password Security
- **Hashing**: bcrypt with proper salt rounds
- **No Plain Text**: Passwords never stored in plain text
- **Validation**: Minimum length requirements

### Token Security
- **JWT**: Signed tokens with expiration
- **Session Tracking**: Database session management
- **Automatic Cleanup**: Expired session removal

### Database Security
- **Row-Level Security**: Complete data isolation
- **Connection Encryption**: Secure database connections
- **User Permissions**: Limited database user permissions
- **Input Validation**: SQL injection prevention

## Performance Metrics

### Connection Pool Statistics
- **Pool Size**: Base 10, Max 30 connections
- **Utilization Tracking**: Real-time usage monitoring
- **Health Checks**: 60-second intervals
- **Performance Logging**: Query time tracking

### Optimization Features
- **Connection Recycling**: Automatic connection refresh
- **Pre-ping Validation**: Connection health verification
- **Query Caching**: Prepared statement caching
- **Async Operations**: Non-blocking database operations

## Monitoring and Maintenance

### Health Monitoring
- **Automated Checks**: Background health monitoring
- **Metric Collection**: Performance and usage statistics
- **Alert System**: High utilization warnings
- **Recommendations**: Automatic optimization suggestions

### Maintenance Tasks
- **Session Cleanup**: Expired session removal
- **Connection Pool Management**: Dynamic sizing
- **Performance Analysis**: Query optimization
- **Security Auditing**: Access logging

## New Engineer Onboarding Guide

### Prerequisites for Database Development

1. **PostgreSQL Installation** (Version 13+)
   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Database Tools** (Recommended)
   - **pgAdmin**: Web-based PostgreSQL administration
   - **DBeaver**: Universal database tool
   - **psql**: Command-line PostgreSQL client (included with PostgreSQL)

### Development Workflow

#### Step 1: Local Development Setup
1. **PostgreSQL Installation**: Local PostgreSQL server (see prerequisites)

2. **Database Creation**: Create development database
   ```bash
   # Connect to PostgreSQL as superuser
   sudo -u postgres psql
   
   # Or on macOS with Homebrew:
   psql postgres
   
   # Create database and user
   CREATE DATABASE personal_ai_agent_dev;
   CREATE USER personal_ai_agent WITH PASSWORD 'dev_password';
   
   # Grant permissions
   GRANT ALL PRIVILEGES ON DATABASE personal_ai_agent_dev TO personal_ai_agent;
   
   # Enable UUID extension (required)
   \c personal_ai_agent_dev
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   
   # Grant usage on schema
   GRANT USAGE, CREATE ON SCHEMA public TO personal_ai_agent;
   ```

3. **Environment Configuration**: Set up your `.env` file
   ```bash
   cd PersonalAIAgent_backend
   cp .env.example .env
   
   # Edit .env with database credentials
   DATABASE_URL=postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev
   ```

4. **Schema Migration**: Run setup scripts
   ```bash
   # Initialize database schema
   python setup_db.py
   
   # Create admin user
   python create_admin.py
   
   # Verify database connection
   python test_backend_connection.py
   ```

#### Step 2: Understanding the Multi-User System

**Key Concepts for New Engineers**:

1. **Row-Level Security (RLS)**: Every table with user data automatically filters by user context
   ```python
   # When you get a user session, RLS is automatically applied
   async with db_manager.get_user_session(user_id) as session:
       # This query only returns documents owned by the current user
       result = await session.execute(text("SELECT * FROM documents"))
   ```

2. **User Context Management**: The system sets PostgreSQL session variables
   ```sql
   -- This is done automatically by the system
   SELECT set_config('app.current_user_id', '123', true);
   
   -- RLS policies use this to filter data
   -- Example policy: WHERE owner_id = current_setting('app.current_user_id')::integer
   ```

3. **Connection Pooling**: AsyncAdaptedQueuePool manages database connections
   ```python
   # Good: Use the database manager
   async with db_manager.get_user_session(user_id) as session:
       # Your database operations here
       pass
   
   # Bad: Don't create raw connections
   # engine.connect() # This bypasses RLS and connection pooling
   ```

#### Step 3: Working with the Database

**Common Development Tasks**:

1. **Adding New User Data Tables**:
   ```sql
   -- 1. Create table with user reference
   CREATE TABLE my_new_table (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
       data TEXT NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   
   -- 2. Add RLS policy
   ALTER TABLE my_new_table ENABLE ROW LEVEL SECURITY;
   CREATE POLICY my_new_table_user_policy ON my_new_table
       FOR ALL TO public
       USING (user_id = current_setting('app.current_user_id', true)::integer);
   
   -- 3. Add performance index
   CREATE INDEX idx_my_new_table_user_id ON my_new_table(user_id);
   ```

2. **Writing User-Safe Queries**:
   ```python
   # Good: Use user session (RLS automatically applied)
   async def get_user_data(user_id: int):
       async with db_manager.get_user_session(user_id) as session:
           result = await session.execute(text("SELECT * FROM documents"))
           return result.fetchall()
   
   # Good: For admin operations
   async def get_all_users():
       async with db_manager.get_admin_session() as session:
           result = await session.execute(text("SELECT * FROM users"))
           return result.fetchall()
   ```

3. **Testing Data Isolation**:
   ```python
   # Test script to verify RLS works correctly
   async def test_data_isolation():
       # Create test users
       user1 = await db_manager.create_user("test1", "test1@example.com", "password")
       user2 = await db_manager.create_user("test2", "test2@example.com", "password")
       
       # Add data for user1
       async with db_manager.get_user_session(user1.id) as session:
           await session.execute(text("INSERT INTO documents (title, owner_id) VALUES ('User1 Doc', :user_id)"), {"user_id": user1.id})
           await session.commit()
       
       # Try to access from user2 session
       async with db_manager.get_user_session(user2.id) as session:
           result = await session.execute(text("SELECT * FROM documents"))
           docs = result.fetchall()
           assert len(docs) == 0, "RLS failed - user2 can see user1's documents!"
   ```

#### Step 4: Database Schema Changes

**Migration Process**:

1. **Create Migration Script**:
   ```python
   # migrations/add_my_feature.py
   async def apply_migration():
       async with db_manager.get_admin_session() as session:
           # Your schema changes
           await session.execute(text("""
               CREATE TABLE my_new_feature (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                   feature_data JSONB NOT NULL,
                   created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
               );
               
               -- Add RLS
               ALTER TABLE my_new_feature ENABLE ROW LEVEL SECURITY;
               CREATE POLICY my_new_feature_user_policy ON my_new_feature
                   FOR ALL TO public
                   USING (user_id = current_setting('app.current_user_id', true)::integer);
               
               -- Add indexes
               CREATE INDEX idx_my_new_feature_user_id ON my_new_feature(user_id);
           """))
           
           # Record migration
           await session.execute(text("""
               INSERT INTO schema_versions (version, description)
               VALUES ('1.4.0', 'Added my_new_feature table')
           """))
           await session.commit()
   ```

2. **Test Migration**:
   ```bash
   # Test on development database
   python your_migration_script.py
   
   # Verify schema
   psql -d personal_ai_agent_dev -c "\d my_new_feature"
   
   # Test RLS
   python test_rls_for_new_table.py
   ```

#### Step 5: Performance Monitoring

**Essential Monitoring Queries**:

```sql
-- 1. Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_tup_read DESC;

-- 2. Find slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 3. Check table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Connection Pool Monitoring**:
```python
# Check pool health in your application
stats = await db_manager.get_detailed_pool_metrics()
print(f"Pool utilization: {stats['utilization_pct']}%")
print(f"Recommendations: {stats['recommendations']}")
```

### Common Pitfalls to Avoid

1. **Bypassing RLS**:
   ```python
   # DON'T: This bypasses RLS and connection pooling
   direct_conn = await asyncpg.connect(database_url)
   
   # DO: Always use the database manager
   async with db_manager.get_user_session(user_id) as session:
       pass
   ```

2. **Not Using Indexes**:
   ```sql
   -- DON'T: This will be slow without index
   SELECT * FROM emails WHERE body_text LIKE '%search term%';
   
   -- DO: Add appropriate index first
   CREATE INDEX idx_emails_body_text ON emails USING gin(to_tsvector('english', body_text));
   SELECT * FROM emails WHERE to_tsvector('english', body_text) @@ plainto_tsquery('search term');
   ```

3. **Forgetting User Context**:
   ```python
   # DON'T: This won't work with RLS
   async def get_document(doc_id: int):
       async with db_manager.get_admin_session() as session:  # Wrong session type
           result = await session.execute(text("SELECT * FROM documents WHERE id = :id"), {"id": doc_id})
           return result.first()
   
   # DO: Use user session and let RLS handle access control
   async def get_document(user_id: int, doc_id: int):
       async with db_manager.get_user_session(user_id) as session:
           result = await session.execute(text("SELECT * FROM documents WHERE id = :id"), {"id": doc_id})
           return result.first()  # Will be None if user doesn't own the document
   ```

### Debugging Database Issues

**Common Debugging Steps**:

1. **Check RLS Policies**:
   ```sql
   SELECT schemaname, tablename, policyname, qual, with_check
   FROM pg_policies 
   WHERE schemaname = 'public';
   ```

2. **Verify User Context**:
   ```sql
   SELECT current_setting('app.current_user_id', true);
   ```

3. **Explain Query Plans**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM documents WHERE owner_id = 123;
   ```

4. **Check Connection Pool**:
   ```python
   # In your application
   stats = await db_manager.get_connection_stats()
   if stats['failure_rate_pct'] > 5:
       print("High connection failure rate!")
   ```

### Quick Reference Commands

```bash
# Connect to development database
psql -d personal_ai_agent_dev -U personal_ai_agent -h localhost

# Check database size
psql -d personal_ai_agent_dev -c "SELECT pg_size_pretty(pg_database_size('personal_ai_agent_dev'));"

# List all tables
psql -d personal_ai_agent_dev -c "\dt"

# Show table structure
psql -d personal_ai_agent_dev -c "\d users"

# Check active connections
psql -d personal_ai_agent_dev -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'personal_ai_agent_dev';"
```

### Testing Procedure
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Multi-user scenario testing
3. **Performance Tests**: Connection pool testing
4. **Security Tests**: RLS and authentication testing

### Deployment Process
1. **Database Provisioning**: Production PostgreSQL setup
2. **Migration Execution**: Schema deployment
3. **Configuration**: Environment-specific settings
4. **Monitoring Setup**: Health check configuration
5. **Performance Tuning**: Production optimization

## Troubleshooting

### Common Issues
1. **Connection Timeouts**: Pool size optimization
2. **Permission Errors**: User privilege verification
3. **RLS Issues**: User context configuration
4. **Performance Problems**: Query optimization

### Debug Procedures
1. **Connection Testing**: Database connectivity verification
2. **Query Analysis**: SQL performance analysis
3. **Log Review**: Application and database logs
4. **Metric Analysis**: Performance metric evaluation

## Future Enhancements

### Planned Improvements
1. **Read Replicas**: Read scaling with replicas
2. **Sharding**: Horizontal scaling implementation
3. **Caching Layer**: Redis integration
4. **Advanced Monitoring**: Enhanced metrics collection
5. **Backup Strategy**: Automated backup system

### Scalability Considerations
- **Connection Pool Scaling**: Dynamic pool sizing
- **Database Partitioning**: Table partitioning strategies
- **Index Optimization**: Advanced indexing strategies
- **Query Optimization**: Continuous performance improvement

---

**Last Updated**: August 12, 2025  
**Version**: 3.0 (Multi-User Implementation Complete)  
**Status**: Production Ready