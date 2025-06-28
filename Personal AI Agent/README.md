# Personal AI Agent

A fully private AI assistant for your documents. Upload documents, ask questions, and get context-aware answers using a retrieval-augmented generation pipeline.

## Features

- 🔒 **Fully Private**: All processing happens locally on your machine
- 📄 **Document Processing**: Upload and process various document types
- 🔍 **Semantic Search**: Find relevant information using vector similarity search
- 🤖 **AI-Powered Answers**: Get context-aware answers to your questions
- 🔐 **User Authentication**: Secure access with JWT authentication
- 📊 **Query History**: Keep track of your questions and answers
- 📝 **Logging**: Comprehensive logging of all system activities

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL/SQLite
- **Vector Store**: FAISS
- **LLM**: Phi-2 (local)
- **Embeddings**: BGE-Small
- **Authentication**: JWT
- **Frontend**: HTML/CSS/JavaScript

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite works out of the box)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/personal-ai-agent.git
cd personal-ai-agent
```

2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
   pip install -r requirements.txt
   ```

4. Download the model
```bash
python download_model.py
```

5. Create an admin user
```bash
python create_admin.py
```

6. Start the server
```bash
   python main.py
   ```

7. Access the UI at http://localhost:8001

## Usage

1. Log in with your admin credentials
2. Upload documents
3. Ask questions about your documents
4. View your query history

## Logging

The system includes comprehensive logging for monitoring and debugging:

- All logs are stored in the `logs` directory
- Log files are automatically rotated (10MB max size, 5 backups)
- Logs include:
  - Server startup/shutdown events
  - Authentication attempts (success/failure)
  - Document uploads and processing
  - Query requests and responses
  - Errors and exceptions

To view logs:
```bash
cat logs/app.log
```

## Project Structure

```
personal-ai-agent/
├── app/                  # Main application code
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality
│   ├── db/               # Database models and connection
│   ├── schemas/          # Pydantic schemas
│   └── utils/            # Utility functions
├── data/                 # Data storage
│   └── vector_db/        # FAISS vector database files
├── logs/                 # Log files
├── models/               # LLM model files
├── static/               # Static files
│   ├── css/              # CSS files
│   ├── js/               # JavaScript files
│   └── uploads/          # Uploaded documents
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Phi-2](https://huggingface.co/microsoft/phi-2)
- [BGE Embeddings](https://huggingface.co/BAAI/bge-small-en-v1.5)

## Recent Changes

### Syntax and Import Fixes
- Fixed syntax errors that were preventing the server from starting.
- Corrected import statements to ensure all modules are correctly loaded.

### Model Loading
- Ensured the correct model (Mistral) is loaded for the AI agent.

### Vector Search Parameters
- Increased vector search parameters to allow the system to find the correct data, specifically for March 2023 expenses.

### Code Refactoring
- Refactored code to prevent hard-coded responses, particularly for general AI-related questions.
- Implemented a configuration file to centralize AI behavior settings.
- Updated the LLM module to use the new configuration.

### Query and Response Improvements
- Improved query classification and response validation.
- Enhanced system prompts to better guide the AI's responses.

### Testing and Debugging
- Successfully started the server and tested the admin login.
- Identified and fixed an error in document searching that was preventing successful query responses. 