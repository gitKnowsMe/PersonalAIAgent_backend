# Personal AI Agent - Desktop Installation Package

A privacy-first AI assistant that processes everything locally on your computer.

## 🚀 Quick Start

### 1. Install
```bash
python install.py
```

### 2. Download Models (~4GB)
```bash
python download_models.py
```

### 3. Run Application
```bash
open PersonalAIAgent.app    # macOS
```

### 4. Access Web Interface
Open browser to: http://localhost:8000

## 📋 Features

- 🔒 **Complete Privacy**: All AI processing happens locally
- 📄 **PDF Intelligence**: Upload and query documents with smart categorization
- 📧 **Gmail Integration**: Search and analyze emails (requires OAuth setup)
- 🤖 **Local AI**: Mistral 7B model for intelligent responses
- 🔍 **Semantic Search**: Vector-based search across documents and emails
- ⚡ **Fast Setup**: Single executable with progressive model downloading

## 🔧 System Requirements

- **OS**: macOS 10.14+ (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 15GB free space (10GB models + 5GB data)
- **Python**: 3.8+ (installer only)

## ⚙️ Configuration

Edit `.env` file for customization:
- `PORT=8000` - Change port if needed
- `USE_METAL=true` - Metal acceleration (macOS)
- Gmail OAuth credentials (optional)

## 🔍 Usage

1. **PDF Processing**: Upload PDFs via web interface
2. **Ask Questions**: Query documents with natural language
3. **Gmail Sync**: Connect Gmail for email search (optional)
4. **Local Processing**: All AI happens on your computer

## 🔒 Privacy

- No external API calls for AI processing
- All data stored locally in SQLite
- No telemetry or data collection
- Gmail integration is optional and local-only

## 📞 Support

Check logs at `logs/personal_ai_agent.log` for troubleshooting.

Built with: FastAPI, Mistral 7B, FAISS, SQLAlchemy