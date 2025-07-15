# Installation Guide

This guide will help you set up the Personal AI Agent on your local machine.

## Prerequisites

- Python 3.8 or higher
- 4GB+ RAM (for local LLM processing)
- Git

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/personal-ai-agent.git
cd personal-ai-agent
```

## Step 2: Create Virtual Environment

=== "Linux/macOS"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows"

    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

!!! tip "Installation Time"
    The installation may take several minutes as it includes machine learning libraries like transformers and FAISS.

## Step 4: Download AI Models

Download the required language model and embedding model:

```bash
# Download Mistral 7B model (this may take some time)
python download_model.py

# Download embedding model
python download_embedding_model.py
```

!!! warning "Model Size"
    The Mistral 7B model is approximately 4GB. Ensure you have sufficient disk space and a stable internet connection.

## Step 5: Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
   ```env
   # Database Configuration
   DATABASE_URL=sqlite:///./personal_ai_agent.db
   
   # Security Configuration
   SECRET_KEY=your_super_secure_secret_key_here
   
   # Server Configuration
   HOST=localhost
   PORT=8000
   DEBUG=true
   
   # LLM Configuration
   LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
   USE_METAL=true  # Set to false if not on macOS
   ```

## Step 6: Database Setup

Initialize the database:

```bash
python setup_db.py
```

## Step 7: Create Admin User

Create an administrative user:

```bash
python create_admin.py
```

Follow the prompts to set up your admin credentials.

## Step 8: Start the Application

```bash
python main.py
```

The application will be available at `http://localhost:8000`.

## Verification

1. Open your browser and navigate to `http://localhost:8000`
2. You should see the Personal AI Agent interface
3. Check the health endpoint: `http://localhost:8000/api/v1/health-check`

## Next Steps

- [Quick Start Guide](quickstart.md) - Learn basic usage
- [Gmail Integration](../user-guide/gmail-integration.md) - Connect your Gmail account
- [Configuration Guide](configuration.md) - Advanced configuration options

## Troubleshooting

### Common Issues

**Model Loading Fails**
```bash
# Test model loading
python test_model_loading.py
```

**Database Errors**
```bash
# Reset database
rm personal_ai_agent.db
python setup_db.py
```

**Port Already in Use**
```bash
# Change port in .env file
PORT=8001
```

For more troubleshooting help, see our [Troubleshooting Guide](../troubleshooting/common-issues.md).