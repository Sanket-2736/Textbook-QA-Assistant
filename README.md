# Interactive Textbook Q&A RAG System

A full-stack Retrieval-Augmented Generation (RAG) system for building interactive Q&A systems from textbook content. The system combines a FastAPI backend with a React + Vite frontend, integrated with LangChain and Pinecone for intelligent document retrieval and LLM-powered responses.

## Project Structure

```
.
├── backend/           # Python FastAPI backend
├── frontend/          # React + Vite + Tailwind frontend
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Backend Setup

The backend is built with:
- **FastAPI** - Modern, fast Python web framework
- **Uvicorn** - ASGI web server
- **LangChain** - Framework for building LLM applications
- **Pinecone** - Vector database for semantic search
- **Pydantic** - Data validation using Python type hints

### Getting Started

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your API keys:
   - `PINECONE_API_KEY` - Your Pinecone API key
   - `OPENAI_API_KEY` - (Optional) OpenAI API key for embeddings

5. Run the development server:
   ```bash
   python -m uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

## Frontend Setup

The frontend is built with:
- **React** - UI library
- **Vite** - Next generation frontend tooling
- **Tailwind CSS** - Utility-first CSS framework

### Getting Started

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:5173`.

## Key Features

- **Semantic Search** - Find relevant textbook content using vector embeddings
- **Intelligent Q&A** - LLM-powered responses based on retrieved context
- **Fast API** - RESTful API with automatic documentation
- **Modern UI** - Responsive React frontend with Tailwind CSS
- **Production Ready** - Scalable architecture with proper error handling

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
pip install -e .
python -m uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

## Deployment

Both backend and frontend can be deployed to various platforms:

- **Backend**: Heroku, Railway, AWS (Lambda with Mangum), Google Cloud Run
- **Frontend**: Vercel, Netlify, GitHub Pages

## License

MIT
