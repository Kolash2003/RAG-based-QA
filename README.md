# Production-Grade RAG Question Answering System

A robust, scalable Retrieval-Augmented Generation (RAG) system built with FastAPI, ChromaDB, and modern LLMs (OpenAI/Anthropic).

## Features

- 📄 **Multiple Document Formats**: PDF, TXT, DOCX, PPTX, XLSX, CSV
- 🔍 **Semantic Search**: Vector embeddings with ChromaDB
- 🤖 **LLM Integration**: Support for OpenAI and Anthropic Claude
- 🚀 **Production Ready**: Logging, error handling, health checks
- 🐳 **Docker Support**: Easy deployment with Docker Compose
- 📊 **API Documentation**: Auto-generated with FastAPI
- ✅ **Testing**: Comprehensive test suite

## Project Structure

```
rag-project/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Configuration management
│   ├── api/
│   │   └── routes.py                # API endpoints
│   ├── models/
│   │   └── schemas.py               # Pydantic models
│   ├── services/
│   │   ├── document_processor.py   # Document parsing
│   │   ├── vector_store.py         # Vector database
│   │   └── llm_service.py          # LLM interactions
│   └── utils/
│       └── logger.py                # Structured logging
├── tests/
│   └── test_api.py                  # API tests
├── data/
│   ├── uploads/                     # Uploaded files
│   └── chroma/                      # Vector database
├── logs/                            # Application logs
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Installation

### Prerequisites

- Python 3.11+
- OpenAI API key or Anthropic API key

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd rag-project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. **Run the application**
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f
```

3. **Stop the application**
```bash
docker-compose down
```

## Configuration

Edit the `.env` file to configure the application:

```bash
# Required: Add your API key
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Choose your LLM provider
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-3.5-turbo  # or claude-3-sonnet-20240229

# Adjust retrieval settings
TOP_K_RESULTS=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## API Usage

### 1. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

Response:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "document.pdf",
  "num_chunks": 15,
  "message": "Document uploaded and processed successfully",
  "uploaded_at": "2025-01-15T10:30:00"
}
```

### 2. Ask Questions

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main topics covered?",
    "top_k": 5
  }'
```

Response:
```json
{
  "question": "What are the main topics covered?",
  "answer": "Based on the documents, the main topics include...",
  "sources": [
    {
      "text": "Relevant chunk of text...",
      "metadata": {
        "filename": "document.pdf",
        "document_id": "123e4567..."
      },
      "relevance_score": 0.92
    }
  ],
  "num_sources": 5
}
```

### 3. Delete a Document

```bash
curl -X DELETE "http://localhost:8000/api/v1/document/{document_id}"
```

### 4. Health Check

```bash
curl "http://localhost:8000/api/v1/health"
```

### 5. Get Statistics

```bash
curl "http://localhost:8000/api/v1/stats"
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Supported File Formats

- **PDF** (.pdf)
- **Text** (.txt)
- **Word** (.docx)
- **PowerPoint** (.pptx)
- **Excel** (.xlsx)
- **CSV** (.csv)

