# Database Constraints Documentation

This document outlines the database constraints implemented in the Personal AI Agent application.

## Overview

Database constraints have been added to ensure data integrity, prevent invalid data, and enforce business rules at the database level. These constraints work in conjunction with Pydantic schema validation for comprehensive data validation.

## User Table Constraints

### Column Constraints
- `email`: VARCHAR(254) NOT NULL UNIQUE
- `username`: VARCHAR(50) NOT NULL UNIQUE  
- `hashed_password`: VARCHAR(255) NOT NULL
- `is_active`: BOOLEAN NOT NULL DEFAULT TRUE
- `is_admin`: BOOLEAN NOT NULL DEFAULT FALSE
- `created_at`: DATETIME NOT NULL

### Check Constraints
- `username_min_length`: Username must be at least 3 characters
- `username_max_length`: Username cannot exceed 50 characters
- `email_max_length`: Email cannot exceed 254 characters
- `email_format`: Email must contain '@' symbol
- `password_hash_min_length`: Hashed password must be at least 8 characters

## Document Table Constraints

### Column Constraints
- `title`: VARCHAR(200) NOT NULL
- `description`: TEXT (nullable)
- `file_path`: VARCHAR(500) NOT NULL
- `file_type`: VARCHAR(10) NOT NULL
- `file_size`: INTEGER NOT NULL
- `created_at`: DATETIME NOT NULL
- `vector_namespace`: VARCHAR(200) NOT NULL UNIQUE
- `owner_id`: INTEGER NOT NULL (Foreign Key)

### Check Constraints
- `title_not_empty`: Title must have at least 1 character
- `title_max_length`: Title cannot exceed 200 characters
- `file_size_positive`: File size must be greater than 0
- `file_type_min_length`: File type must be at least 2 characters
- `namespace_min_length`: Vector namespace must be at least 5 characters

## Query Table Constraints

### Column Constraints
- `question`: TEXT NOT NULL
- `answer`: TEXT (nullable)
- `created_at`: DATETIME NOT NULL
- `user_id`: INTEGER NOT NULL (Foreign Key)
- `document_id`: INTEGER (nullable, Foreign Key)

### Check Constraints
- `question_not_empty`: Question must have at least 1 character
- `question_max_length`: Question cannot exceed 5000 characters

## Pydantic Schema Validation

The database constraints are complemented by Pydantic schema validation:

### UserCreate Schema
```python
email: EmailStr = Field(..., max_length=254)
username: str = Field(..., min_length=3, max_length=50)  
password: str = Field(..., min_length=8)
```

### DocumentCreate Schema
```python
title: str = Field(..., min_length=1, max_length=200)
description: Optional[str] = Field(None, max_length=1000)
```

### QueryCreate Schema
```python
question: str = Field(..., min_length=1, max_length=5000)
```

## Migration

The constraints were applied using the `migrate_db_constraints.py` script, which:

1. Validates existing data against new constraints
2. Recreates tables with proper constraints (SQLite limitation)
3. Preserves all existing data
4. Logs the migration process

## Benefits

- **Data Integrity**: Prevents invalid data at the database level
- **Performance**: Database-level validation is faster than application-level
- **Consistency**: Ensures all data meets minimum quality standards
- **Security**: Prevents SQL injection and data corruption
- **Maintenance**: Makes debugging and data analysis easier

## Constants Used

All constraint values are defined in `app/core/constants.py`:

```python
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8
EMAIL_MAX_LENGTH = 254
TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 1000
```

This ensures consistency between database constraints, schema validation, and application logic.