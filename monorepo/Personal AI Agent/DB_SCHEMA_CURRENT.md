# Current Database Schema

## **Schema Overview**
This is the current multi-user database schema that's already implemented and production-ready.

## **Entity Relationship Diagram (Text Format)**

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                    CURRENT DATABASE SCHEMA                                                                             │
│                                                        (Multi-User Ready)                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

                                                    ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
                                                    │                                        USERS                                                        │
                                                    │─────────────────────────────────────────────────────────────────────────────────────────────────────────│
                                                    │ PK  id: INTEGER                                                                                        │
                                                    │ UQ  email: VARCHAR(255) [INDEXED]                                                                      │
                                                    │ UQ  username: VARCHAR(50) [INDEXED]                                                                    │
                                                    │     hashed_password: VARCHAR(255)                                                                      │
                                                    │     is_active: BOOLEAN [DEFAULT: true]                                                                 │
                                                    │     is_admin: BOOLEAN [DEFAULT: false]                                                                 │
                                                    │     created_at: TIMESTAMP [DEFAULT: NOW()]                                                             │
                                                    │─────────────────────────────────────────────────────────────────────────────────────────────────────────│
                                                    │ CONSTRAINTS:                                                                                            │
                                                    │ • username: 3-50 chars                                                                                 │
                                                    │ • email: valid format (@)                                                                              │
                                                    │ • password_hash: min 8 chars                                                                           │
                                                    └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                              │
                                                                                              │ (1:N relationships)
                                                                                              │
                    ┌─────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┐
                    │                                                                         │                                                                         │
                    │                                                                         │                                                                         │
                    ▼                                                                         ▼                                                                         ▼
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐                                      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │                                   DOCUMENTS                                             │                                      │                                EMAIL_ACCOUNTS                                          │
      │─────────────────────────────────────────────────────────────────────────────────────────│                                      │─────────────────────────────────────────────────────────────────────────────────────────│
      │ PK  id: INTEGER                                                                         │                                      │ PK  id: INTEGER                                                                         │
      │ FK  owner_id: INTEGER → users.id [INDEXED]                                              │                                      │ FK  user_id: INTEGER → users.id [INDEXED]                                               │
      │     title: VARCHAR(200) [INDEXED]                                                       │                                      │     email_address: VARCHAR(255) [INDEXED]                                               │
      │     description: TEXT [NULLABLE]                                                        │                                      │     provider: VARCHAR(50) [DEFAULT: 'gmail']                                            │
      │     file_path: VARCHAR(500)                                                             │                                      │     access_token: TEXT [NULLABLE, ENCRYPTED]                                            │
      │     file_type: VARCHAR(10)                                                              │                                      │     refresh_token: TEXT [NULLABLE, ENCRYPTED]                                           │
      │     document_type: VARCHAR(20) [DEFAULT: 'generic']                                     │                                      │     token_expires_at: TIMESTAMP [NULLABLE]                                              │
      │     file_size: INTEGER                                                                  │                                      │     is_active: BOOLEAN [DEFAULT: true] [INDEXED]                                        │
      │     created_at: TIMESTAMP [DEFAULT: NOW()] [INDEXED]                                    │                                      │     sync_enabled: BOOLEAN [DEFAULT: true] [INDEXED]                                     │
      │ UQ  vector_namespace: VARCHAR(200)                                                      │                                      │     last_sync_at: TIMESTAMP [NULLABLE] [INDEXED]                                        │
      │─────────────────────────────────────────────────────────────────────────────────────────│                                      │     created_at: TIMESTAMP [DEFAULT: NOW()]                                              │
      │ CONSTRAINTS:                                                                            │                                      │─────────────────────────────────────────────────────────────────────────────────────────│
      │ • title: 1-200 chars                                                                   │                                      │ CONSTRAINTS:                                                                            │
      │ • file_size: > 0                                                                       │                                      │ • email_address: valid format (@)                                                      │
      │ • document_type: 'financial', 'long_form', 'generic'                                   │                                      │ • provider: 'gmail', 'outlook'                                                         │
      │ • file_type: min 2 chars                                                               │                                      └─────────────────────────────────────────────────────────────────────────────────────────┘
      │ • vector_namespace: min 5 chars                                                        │                                                                                  │
      └─────────────────────────────────────────────────────────────────────────────────────────┘                                                                                  │
                                                    │                                                                                                                      │
                                                    │                                                                                                                      │
                                                    │                                                                                                                      │
                                                    ▼                                                                                                                      ▼
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐                                      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │                                    QUERIES                                              │                                      │                                    EMAILS                                               │
      │─────────────────────────────────────────────────────────────────────────────────────────│                                      │─────────────────────────────────────────────────────────────────────────────────────────│
      │ PK  id: INTEGER                                                                         │                                      │ PK  id: INTEGER                                                                         │
      │ FK  user_id: INTEGER → users.id [INDEXED]                                               │                                      │ FK  email_account_id: INTEGER → email_accounts.id [INDEXED]                             │
      │ FK  document_id: INTEGER → documents.id [INDEXED] [NULLABLE]                            │                                      │ FK  user_id: INTEGER → users.id [INDEXED]                                               │
      │     question: TEXT                                                                      │                                      │ UQ  message_id: VARCHAR(255) [INDEXED]                                                  │
      │     answer: TEXT [NULLABLE]                                                             │                                      │     thread_id: VARCHAR(255) [INDEXED] [NULLABLE]                                        │
      │     created_at: TIMESTAMP [DEFAULT: NOW()] [INDEXED]                                    │                                      │     subject: VARCHAR(500) [NULLABLE]                                                    │
      │─────────────────────────────────────────────────────────────────────────────────────────│                                      │     sender_email: VARCHAR(255) [INDEXED]                                                │
      │ CONSTRAINTS:                                                                            │                                      │     sender_name: VARCHAR(200) [NULLABLE]                                                │
      │ • question: 1-5000 chars                                                               │                                      │     recipient_emails: TEXT [NULLABLE] [JSON]                                            │
      └─────────────────────────────────────────────────────────────────────────────────────────┘                                      │     cc_emails: TEXT [NULLABLE] [JSON]                                                   │
                                                                                                                                       │     bcc_emails: TEXT [NULLABLE] [JSON]                                                  │
                                                                                                                                       │     body_text: TEXT [NULLABLE]                                                          │
                                                                                                                                       │     body_html: TEXT [NULLABLE]                                                          │
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐                                      │     email_type: VARCHAR(20) [DEFAULT: 'generic'] [INDEXED]                             │
      │                                OAUTH_SESSIONS                                           │                                      │     is_read: BOOLEAN [DEFAULT: false] [INDEXED]                                         │
      │─────────────────────────────────────────────────────────────────────────────────────────│                                      │     is_important: BOOLEAN [DEFAULT: false] [INDEXED]                                    │
      │ PK  id: INTEGER                                                                         │                                      │     has_attachments: BOOLEAN [DEFAULT: false] [INDEXED]                                 │
      │ FK  user_id: INTEGER → users.id [INDEXED]                                               │                                      │     gmail_labels: TEXT [NULLABLE] [JSON]                                                │
      │ UQ  session_id: VARCHAR(255) [INDEXED]                                                  │                                      │     sent_at: TIMESTAMP [INDEXED]                                                        │
      │     provider: VARCHAR(50) [INDEXED]                                                     │                                      │     created_at: TIMESTAMP [DEFAULT: NOW()]                                              │
      │     oauth_state: VARCHAR(255)                                                           │                                      │     vector_namespace: VARCHAR(200) [NULLABLE]                                           │
      │     redirect_uri: VARCHAR(500)                                                          │                                      │─────────────────────────────────────────────────────────────────────────────────────────│
      │     expires_at: TIMESTAMP [INDEXED]                                                     │                                      │ CONSTRAINTS:                                                                            │
      │     created_at: TIMESTAMP [DEFAULT: NOW()]                                              │                                      │ • sender_email: valid format (@)                                                       │
      │─────────────────────────────────────────────────────────────────────────────────────────│                                      │ • email_type: 'business', 'personal', 'promotional',                                   │
      │ CONSTRAINTS:                                                                            │                                      │               'transactional', 'support', 'generic'                                     │
      │ • provider: 'gmail', 'outlook'                                                         │                                      │ • subject: max 500 chars                                                               │
      │ • session_id: min 10 chars                                                             │                                      └─────────────────────────────────────────────────────────────────────────────────────────┘
      └─────────────────────────────────────────────────────────────────────────────────────────┘                                                                                  │
                                                                                                                                                                                     │
                                                                                                                                                                                     │
                                                                                                                                                                                     ▼
                                                                                                                                       ┌─────────────────────────────────────────────────────────────────────────────────────────┐
                                                                                                                                       │                              EMAIL_ATTACHMENTS                                          │
                                                                                                                                       │─────────────────────────────────────────────────────────────────────────────────────────│
                                                                                                                                       │ PK  id: INTEGER                                                                         │
                                                                                                                                       │ FK  email_id: INTEGER → emails.id [INDEXED]                                             │
                                                                                                                                       │ FK  user_id: INTEGER → users.id [INDEXED]                                               │
                                                                                                                                       │     filename: VARCHAR(255)                                                              │
                                                                                                                                       │     file_path: VARCHAR(500) [NULLABLE]                                                  │
                                                                                                                                       │     file_size: INTEGER                                                                  │
                                                                                                                                       │     mime_type: VARCHAR(100) [INDEXED]                                                   │
                                                                                                                                       │     attachment_id: VARCHAR(255)                                                         │
                                                                                                                                       │     is_downloaded: BOOLEAN [DEFAULT: false] [INDEXED]                                   │
                                                                                                                                       │     created_at: TIMESTAMP [DEFAULT: NOW()]                                              │
                                                                                                                                       │─────────────────────────────────────────────────────────────────────────────────────────│
                                                                                                                                       │ CONSTRAINTS:                                                                            │
                                                                                                                                       │ • file_size: > 0                                                                       │
                                                                                                                                       │ • filename: min 1 char                                                                 │
                                                                                                                                       └─────────────────────────────────────────────────────────────────────────────────────────┘
```

## **Key Features**

### **User Isolation**
- ✅ All user data is properly isolated with foreign key relationships
- ✅ Every data table includes `user_id` for complete separation
- ✅ Proper indexes on all foreign keys for performance

### **Document Management**
- ✅ Category-based document classification (financial, long_form, generic)
- ✅ Unique vector namespaces per document: `user_{user_id}_doc_{filename}`
- ✅ File type validation and size constraints
- ✅ User-specific file storage paths

### **Email Integration**
- ✅ Multi-provider support (Gmail, Outlook)
- ✅ OAuth2 token management with expiration
- ✅ Email classification (business, personal, promotional, transactional, support)
- ✅ Thread-aware email processing
- ✅ Attachment handling with download tracking

### **Performance Optimization**
- ✅ Strategic indexing on all frequently queried fields
- ✅ Composite indexes for common query patterns
- ✅ Foreign key indexes for relationship queries
- ✅ Timestamp indexes for chronological queries

### **Data Integrity**
- ✅ Check constraints for data validation
- ✅ Foreign key constraints for referential integrity
- ✅ Unique constraints on critical fields
- ✅ Length and format validation

### **Security Features**
- ✅ Encrypted token storage for OAuth2
- ✅ bcrypt password hashing
- ✅ Email format validation
- ✅ Session management with expiration

## **Storage Architecture**

### **File System Organization**
```
data/
├── uploads/
│   ├── {user_id}/
│   │   ├── document1.pdf
│   │   └── document2.pdf
│   └── {user_id}/
│       └── document3.pdf
├── emails/
│   ├── attachments/
│   └── content/
└── vector_db/
    ├── financial/
    │   ├── user_{user_id}_doc_{filename}.index
    │   └── user_{user_id}_doc_{filename}.pkl
    ├── long_form/
    │   ├── user_{user_id}_doc_{filename}.index
    │   └── user_{user_id}_doc_{filename}.pkl
    ├── generic/
    │   ├── user_{user_id}_doc_{filename}.index
    │   └── user_{user_id}_doc_{filename}.pkl
    └── emails/
        ├── user_{user_id}_email_{source}_{id}.index
        └── user_{user_id}_email_{source}_{id}.pkl
```

### **Vector Database Namespaces**
- **PDF Documents**: `user_{user_id}_doc_{sanitized_filename}`
- **Email Messages**: `user_{user_id}_email_{email_source}_{email_id}`
- **Category Separation**: Different directories for document types

## **Performance Indexes**

### **High Priority Indexes (Foreign Keys)**
- `idx_documents_owner_id` - Document ownership queries
- `idx_queries_user_id` - User query history
- `idx_emails_user_id` - User email filtering
- `idx_emails_email_account_id` - Email account filtering
- `idx_email_accounts_user_id` - User email accounts

### **Medium Priority Indexes (Filtering)**
- `idx_documents_document_type` - Document category filtering
- `idx_emails_email_type` - Email classification filtering
- `idx_emails_is_read` - Read/unread email filtering
- `idx_emails_has_attachments` - Attachment filtering

### **Composite Indexes (Query Optimization)**
- `idx_emails_user_account_composite` - Multi-field email queries
- `idx_emails_user_type_composite` - User + email type queries
- `idx_emails_user_sent_at_composite` - User + timestamp queries

## **Multi-User Ready Features**

### **✅ Complete User Isolation**
- All data tables include `user_id` foreign keys
- File storage organized by user directories
- Vector namespaces include user identifiers
- API endpoints filter by current user

### **✅ Scalable Architecture**
- Proper indexing for multi-user performance
- Connection pooling support
- Efficient query patterns
- Category-based data organization

### **✅ Security & Privacy**
- Local data storage (no cloud dependencies)
- Encrypted OAuth2 tokens
- Secure password hashing
- User-specific data access only

## **Database Statistics**

### **Tables: 7**
- `users` - User management
- `documents` - PDF document metadata
- `queries` - Query history
- `email_accounts` - OAuth2 email accounts
- `emails` - Email messages
- `email_attachments` - Email attachments
- `oauth_sessions` - OAuth2 sessions

### **Indexes: 25+**
- Foreign key indexes for all relationships
- Performance indexes on frequently queried fields
- Composite indexes for complex queries
- Unique indexes on critical fields

### **Constraints: 20+**
- Check constraints for data validation
- Foreign key constraints for referential integrity
- Unique constraints on critical fields
- Length and format validation rules

## **Current Status**

**✅ Production Ready**: This schema is fully implemented and multi-user ready
**✅ PostgreSQL Compatible**: All types and features work with PostgreSQL
**✅ Performance Optimized**: Comprehensive indexing strategy
**✅ Security Hardened**: Proper validation and constraints
**✅ Scalable Design**: Handles multiple users with proper isolation

The current database schema requires **NO CHANGES** for multi-user PostgreSQL deployment. It's already a sophisticated, enterprise-grade design with proper user isolation, security, and performance optimization.