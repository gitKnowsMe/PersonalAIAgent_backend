# Personal AI Agent - Complete Database Schema & Workflow Diagram

## Database Schema Overview

This document provides a comprehensive view of the Personal AI Agent database structure, including all tables, relationships, data flow, and processing workflows.

## Entity Relationship Diagram

```mermaid
erDiagram
    %% Core User Management
    users {
        int id PK
        string email UK "max 254 chars"
        string username UK "3-50 chars"
        string hashed_password "bcrypt hash"
        boolean is_active "default true"
        boolean is_admin "default false"
        datetime created_at "auto timestamp"
    }

    %% Document Management
    documents {
        int id PK
        string title "max 200 chars"
        text description "optional"
        string file_path "max 500 chars"
        string file_type "pdf, txt, docx"
        string document_type "financial, long_form, generic"
        int file_size "bytes"
        datetime created_at "auto timestamp"
        string vector_namespace "unique, for vector storage"
        int owner_id FK "references users.id"
    }

    %% Query History
    queries {
        int id PK
        text question "max 5000 chars"
        text answer "optional, can be NULL"
        datetime created_at "auto timestamp"
        int user_id FK "references users.id"
        int document_id FK "references documents.id, optional"
    }

    %% Email Account Management
    email_accounts {
        int id PK
        int user_id FK "references users.id"
        string email_address "max 254 chars"
        string provider "gmail, outlook"
        text access_token "encrypted OAuth token"
        text refresh_token "encrypted refresh token"
        datetime token_expires_at "optional"
        boolean is_active "default true"
        boolean sync_enabled "default true"
        datetime last_sync_at "optional"
        datetime created_at "auto timestamp"
    }

    %% Email Storage
    emails {
        int id PK
        int email_account_id FK "references email_accounts.id"
        int user_id FK "references users.id"
        string message_id "Gmail message ID, unique"
        string thread_id "Gmail thread ID, optional"
        string subject "max 500 chars"
        string sender_email "max 254 chars"
        string sender_name "max 200 chars"
        text recipient_emails "JSON array"
        text cc_emails "JSON array"
        text bcc_emails "JSON array"
        text body_text "plain text body"
        text body_html "HTML body"
        string email_type "business, personal, promotional, transactional, support, generic"
        boolean is_read "default false"
        boolean is_important "default false"
        boolean has_attachments "default false"
        text gmail_labels "JSON array"
        datetime sent_at "email timestamp"
        datetime created_at "auto timestamp"
        string vector_namespace "for vector storage, optional"
    }

    %% Email Attachments
    email_attachments {
        int id PK
        int email_id FK "references emails.id"
        int user_id FK "references users.id"
        string filename "max 255 chars"
        string file_path "local path, optional"
        int file_size "bytes"
        string mime_type "max 100 chars"
        string attachment_id "Gmail attachment ID"
        boolean is_downloaded "default false"
        datetime created_at "auto timestamp"
    }

    %% OAuth Session Management
    oauth_sessions {
        int id PK
        string session_id "unique, min 10 chars"
        int user_id FK "references users.id"
        string provider "gmail, outlook"
        string oauth_state "OAuth state parameter"
        string redirect_uri "max 500 chars"
        datetime expires_at "session expiration"
        datetime created_at "auto timestamp"
    }

    %% Relationships
    users ||--o{ documents : "owns"
    users ||--o{ queries : "makes"
    users ||--o{ email_accounts : "has"
    users ||--o{ emails : "receives"
    users ||--o{ email_attachments : "owns"
    users ||--o{ oauth_sessions : "creates"
    
    documents ||--o{ queries : "queried_in"
    email_accounts ||--o{ emails : "contains"
    emails ||--o{ email_attachments : "has"
```

## Data Flow & Processing Workflow

```mermaid
flowchart TD
    %% User Authentication Flow
    A[User Login] --> B{Valid Credentials?}
    B -->|Yes| C[Create Session]
    B -->|No| D[Return Error]
    C --> E[Access Granted]
    
    %% Document Upload & Processing Flow
    F[Document Upload] --> G[File Validation]
    G --> H{File Type Supported?}
    H -->|Yes| I[Store File]
    H -->|No| J[Return Error]
    I --> K[Create Document Record]
    K --> L[Document Classification]
    L --> M[Content Extraction]
    M --> N[Chunking Strategy]
    N --> O[Vector Embedding]
    O --> P[Store in Vector DB]
    P --> Q[Update Document Status]
    
    %% Email Integration Flow
    R[Gmail OAuth] --> S[Store Email Account]
    S --> T[Email Sync Process]
    T --> U[Fetch Emails from Gmail]
    U --> V[Email Classification]
    V --> W[Content Processing]
    W --> X[Chunking by Email Type]
    X --> Y[Vector Embedding]
    Y --> Z[Store in Vector DB]
    Z --> AA[Update Email Status]
    
    %% Query Processing Flow
    BB[User Query] --> CC[Query Analysis]
    CC --> DD[Source Selection]
    DD --> EE[Vector Search]
    EE --> FF[Retrieve Relevant Chunks]
    FF --> GG[Context Assembly]
    GG --> HH[LLM Processing]
    HH --> II[Response Generation]
    II --> JJ[Store Query & Response]
    JJ --> KK[Return Answer to User]
    
    %% Vector Storage Organization
    LL[Vector Storage] --> MM[Financial Documents]
    LL --> NN[Long Form Documents]
    LL --> OO[Generic Documents]
    LL --> PP[Email Vectors]
    
    MM --> QQ[Business Emails]
    MM --> RR[Personal Emails]
    MM --> SS[Promotional Emails]
    MM --> TT[Transactional Emails]
    MM --> UU[Support Emails]
```

## Database Indexes & Performance

```mermaid
graph LR
    %% Primary Indexes
    A[Primary Keys] --> A1[users.id]
    A --> A2[documents.id]
    A --> A3[queries.id]
    A --> A4[email_accounts.id]
    A --> A5[emails.id]
    A --> A6[email_attachments.id]
    A --> A7[oauth_sessions.id]
    
    %% Foreign Key Indexes
    B[Foreign Key Indexes] --> B1[idx_documents_owner_id]
    B --> B2[idx_queries_user_id]
    B --> B3[idx_queries_document_id]
    B --> B4[idx_email_accounts_user_id]
    B --> B5[idx_emails_user_id]
    B --> B6[idx_emails_email_account_id]
    B --> B7[idx_email_attachments_email_id]
    B --> B8[idx_email_attachments_user_id]
    B --> B9[idx_oauth_sessions_user_id]
    
    %% Performance Indexes
    C[Performance Indexes] --> C1[idx_documents_document_type]
    C --> C2[idx_documents_created_at]
    C --> C3[idx_queries_created_at]
    C --> C4[idx_email_accounts_is_active]
    C --> C5[idx_email_accounts_sync_enabled]
    C --> C6[idx_email_accounts_last_sync_at]
    C --> C7[idx_emails_email_type]
    C --> C8[idx_emails_is_read]
    C --> C9[idx_emails_has_attachments]
    C --> C10[idx_emails_is_important]
    C --> C11[idx_emails_sent_at]
    C --> C12[idx_email_attachments_is_downloaded]
    C --> C13[idx_email_attachments_mime_type]
    C --> C14[idx_oauth_sessions_expires_at]
    C --> C15[idx_oauth_sessions_provider]
    
    %% Composite Indexes
    D[Composite Indexes] --> D1[idx_emails_user_account_composite]
    D --> D2[idx_emails_user_type_composite]
    D --> D3[idx_emails_user_sent_at_composite]
    D --> D4[idx_emails_account_sent_at_composite]
    D --> D5[idx_emails_user_read_composite]
    
    %% Unique Indexes
    E[Unique Indexes] --> E1[users.email]
    E --> E2[users.username]
    E --> E3[documents.vector_namespace]
    E --> E4[emails.message_id]
    E --> E5[oauth_sessions.session_id]
```

## Email Processing Workflow

```mermaid
flowchart TD
    %% Email Sync Process
    A[Gmail API Call] --> B[Fetch Email List]
    B --> C[Filter New Emails]
    C --> D[Process Each Email]
    
    %% Email Classification
    D --> E[Extract Email Data]
    E --> F[Classify Email Type]
    F --> G{Email Type}
    G -->|Business| H[Business Processing]
    G -->|Personal| I[Personal Processing]
    G -->|Promotional| J[Promotional Processing]
    G -->|Transactional| K[Transactional Processing]
    G -->|Support| L[Support Processing]
    G -->|Generic| M[Generic Processing]
    
    %% Chunking Strategies
    H --> N[Thread-Aware Chunking<br/>800 chars, 100 overlap]
    I --> O[Conversation Chunking<br/>600 chars, 75 overlap]
    J --> P[Content-Focused Chunking<br/>500 chars, 50 overlap]
    K --> Q[Data Extraction Chunking<br/>400 chars, 40 overlap]
    L --> R[Issue-Focused Chunking<br/>700 chars, 100 overlap]
    M --> S[Balanced Chunking<br/>400 chars, 50 overlap]
    
    %% Vector Storage
    N --> T[Create Embeddings]
    O --> T
    P --> T
    Q --> T
    R --> T
    S --> T
    
    T --> U[Store in Vector DB]
    U --> V[Update Email Record]
    V --> W[Mark as Processed]
```

## Document Processing Workflow

```mermaid
flowchart TD
    %% Document Upload
    A[File Upload] --> B[File Validation]
    B --> C{File Type}
    C -->|PDF| D[PDF Processor]
    C -->|TXT| E[Text Processor]
    C -->|CSV| E
    C -->|MD| E
    C -->|Unsupported| F[Return Error]
    
    %% Content Extraction
    D --> G[Extract Text Content]
    E --> G
    G --> H[Document Classification]
    
    %% Classification
    H --> I{Document Type}
    I -->|Financial| J[Financial Processing]
    I -->|Long Form| K[Long Form Processing]
    I -->|Generic| L[Generic Processing]
    
    %% Chunking Strategies
    J --> M[Token-Based Chunking<br/>500 tokens, 50 overlap]
    K --> M
    L --> N[Section-Based Chunking<br/>Adaptive size]
    
    %% Vector Processing
    M --> O[Create Embeddings]
    N --> O
    O --> P[Store in Vector DB]
    P --> Q[Update Document Status]
```

## Vector Storage Architecture

```mermaid
graph TB
    %% Vector Storage Organization
    A[Vector Database] --> B[Financial Category]
    A --> C[Long Form Category]
    A --> D[Generic Category]
    A --> E[Email Vectors]
    
    %% Financial Documents
    B --> F[Bank Statements]
    B --> G[Invoices]
    B --> H[Receipts]
    B --> I[Financial Reports]
    
    %% Long Form Documents
    C --> J[Reports]
    C --> K[Manuals]
    C --> L[Books]
    C --> M[Research Papers]
    
    %% Generic Documents
    D --> N[Resumes]
    D --> O[Letters]
    D --> P[Notes]
    D --> Q[Miscellaneous]
    
    %% Email Categories
    E --> R[Business Emails]
    E --> S[Personal Emails]
    E --> T[Promotional Emails]
    E --> U[Transactional Emails]
    E --> V[Support Emails]
    
    %% Storage Structure
    subgraph "File System Organization"
        W[data/vector_db/]
        W --> X[financial/]
        W --> Y[long_form/]
        W --> Z[generic/]
        W --> AA[emails/]
        
        X --> BB[*.index files]
        X --> CC[*.pkl files]
        Y --> DD[*.index files]
        Y --> EE[*.pkl files]
        Z --> FF[*.index files]
        Z --> GG[*.pkl files]
        AA --> HH[*.index files]
        AA --> II[*.pkl files]
    end
```

## Security & Constraints

```mermaid
graph LR
    %% Data Validation Constraints
    A[Input Validation] --> A1[Email Format Check]
    A --> A2[Username Length 3-50]
    A --> A3[Password Min 8 chars]
    A --> A4[File Size Limits]
    A --> A5[File Type Validation]
    
    %% Security Measures
    B[Security] --> B1[Password Hashing<br/>bcrypt]
    B --> B2[Token Encryption<br/>AES-256]
    B --> B3[OAuth Token Storage<br/>Encrypted]
    B --> B4[Session Management<br/>Secure]
    B --> B5[Input Sanitization]
    
    %% Database Constraints
    C[Database Constraints] --> C1[Foreign Key Constraints]
    C --> C2[Unique Constraints]
    C --> C3[Check Constraints]
    C --> C4[NOT NULL Constraints]
    C --> C5[Length Constraints]
    
    %% Access Control
    D[Access Control] --> D1[User Authentication]
    D --> D2[Admin Role Check]
    D --> D3[Resource Ownership]
    D --> D4[Session Validation]
    D --> D5[API Rate Limiting]
```

## Key Features & Capabilities

### 1. Multi-User Support
- Isolated user data with proper foreign key relationships
- Admin user management capabilities
- Secure session management

### 2. Document Processing
- Support for PDF, TXT, CSV, MD files
- Automatic document classification (financial, long_form, generic)
- Adaptive chunking strategies based on document type
- Vector storage with FAISS for similarity search

### 3. Email Integration
- Gmail OAuth integration
- Email classification (business, personal, promotional, transactional, support)
- Type-specific chunking strategies
- Attachment handling
- Thread-aware processing

### 4. Vector Search & RAG
- FAISS-based vector similarity search
- Category-organized vector storage
- Multi-source query processing
- Context-aware response generation

### 5. Performance Optimization
- Comprehensive indexing strategy
- Composite indexes for common query patterns
- Efficient vector storage organization
- Connection pooling and timeout handling

### 6. Security & Data Integrity
- Encrypted token storage
- Input validation and sanitization
- Database constraints and checks
- Secure authentication flow

This database schema supports a comprehensive personal AI assistant that can process documents, integrate with email systems, and provide intelligent responses through vector-based retrieval and LLM processing. 