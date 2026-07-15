# Textbook Q&A RAG - Backend

FastAPI-based backend for the Interactive Textbook Q&A RAG System.

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Run development server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

## API Endpoints

The API provides the following endpoints:

- `GET /` - Health check
- `GET /docs` - Swagger UI documentation
- `POST /api/query` - Submit a question and get an answer
- `POST /api/documents` - Upload textbook documents

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Configuration settings
│   ├── models.py         # Pydantic models
│   └── routes/           # API route handlers
├── pyproject.toml        # Project metadata and dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Dependencies

Core dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` - LLM orchestration
- `langchain-core` - Core abstractions
- `langchain-community` - Community integrations
- `langchain-pinecone` - Pinecone integration
- `pinecone` - Vector database client
- `pydantic` - Data validation
- `python-dotenv` - Environment variable management

## Development

Run linting:
```bash
ruff check .
```

Run type checking:
```bash
mypy app/
```

Run tests:
```bash
pytest
```

Format code:
```bash
black app/
```
