# Conversational RAG System Documentation

## Overview

The Textbook Q&A system now supports multi-turn conversations with intelligent query condensation, ensuring that follow-up questions are properly contextualized without hallucination or history bleed-through.

## Architecture

### Two-Step Query Processing

#### Step 1: Query Condensation (Optional)
- **When**: Follow-up question detected (session has prior messages)
- **What**: Rewrite the follow-up into a standalone question using chat history
- **Why**: Improves retrieval quality by making implicit context explicit
- **Skip**: First turn (no history) or if chain returns original question

#### Step 2: Answer Generation
- **Retrieval**: Use standalone question for similarity search
- **Context**: Include last 2-3 conversation turns for tone/continuity
- **Source**: Only textbook excerpts (never prior assistant responses)
- **Safety**: "Not found in textbook" guardrail always active

### Database Schema

```sql
User
  ├── id (PK)
  ├── email (UNIQUE)
  ├── hashed_password
  └── created_at

Textbook
  ├── id (PK)
  ├── user_id (FK → User)
  ├── filename
  ├── pinecone_namespace (UNIQUE, scope for vectors)
  ├── uploaded_at
  ├── page_count
  └── chunk_count

ChatSession
  ├── id (PK)
  ├── user_id (FK → User)
  ├── textbook_id (FK → Textbook)
  ├── created_at
  └── title (auto-generated from first question)

ChatMessage
  ├── id (PK)
  ├── session_id (FK → ChatSession)
  ├── role ("user" | "assistant")
  ├── content
  ├── sources (JSON)
  ├── standalone_question (NULL for assistant messages)
  └── created_at
```

### Key Features

#### 1. Query Condensation

**Process:**
1. Fetch last 6 messages from session (ordered chronologically)
2. Build condensation prompt: history + follow-up question
3. Send to Cerebras with low temperature (0.1) for consistency
4. Use returned standalone question for retrieval

**Example:**
```
History:
  User: "What is photosynthesis?"
  Assistant: "Photosynthesis is the process..."

Follow-up: "What are the products?"

Condensed: "What are the products of photosynthesis?"
```

#### 2. Session Isolation

- Each `ChatSession` has unique `id` and `user_id`
- Only messages for that specific `session_id` are fetched
- New session = fresh history = no cross-conversation contamination
- Authorization checks prevent user A from accessing user B's sessions

#### 3. Guardrails (Always Active)

- ✅ Always retrieve from textbook using Pinecone
- ✅ If retrieval returns zero/low-relevance docs → guardrail fires
- ✅ Never use prior assistant responses as ground truth
- ✅ Never hallucinate outside textbook knowledge
- ✅ Applies to both first turn and follow-ups

#### 4. Multi-Tenancy via Namespaces

- Pinecone index: single shared `"textbook-qa"`
- Namespace per textbook: `"user_{user_id}_textbook_{textbook_id}"`
- Retrieval scoped to user's textbook namespace
- Prevents cross-user data leakage at vector store level

## API Endpoints

### POST /ask - Question Answering

**Request:**
```json
{
  "question": "Can you explain that?",
  "textbook_id": 1,
  "session_id": null,  // Create new if null
  "top_k": 4           // Optional
}
```

**Response:**
```json
{
  "answer": "Based on the textbook...",
  "standalone_question": "Can you explain photosynthesis?",
  "sources": [
    {
      "page": 42,
      "section": "Chapter 2: Photosynthesis",
      "text": "Photosynthesis is..."
    }
  ],
  "session_id": 1,
  "num_sources": 3
}
```

**Behind the Scenes:**
1. Verify textbook ownership
2. Get or create ChatSession
3. Fetch conversation history
4. Condense question if follow-up
5. Retrieve top-k documents
6. Generate answer with guardrails
7. Save user message + assistant message to DB
8. Return response

### GET /sessions - List Chat Sessions

**Request:**
```
GET /sessions?textbook_id=1
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "textbook_id": 1,
    "created_at": "2025-01-15T10:30:00Z",
    "title": "What is photosynthesis?"
  }
]
```

### GET /sessions/{id}/messages - Get Message History

**Request:**
```
GET /sessions/1/messages
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "role": "user",
    "content": "What is photosynthesis?",
    "standalone_question": null,  // Not populated for first turn
    "created_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "role": "assistant",
    "content": "Photosynthesis is...",
    "sources": [
      {"page": 42, "text": "..."}
    ],
    "standalone_question": null,  // Null for assistant messages
    "created_at": "2025-01-15T10:31:00Z"
  },
  {
    "id": 3,
    "role": "user",
    "content": "What are the products?",
    "standalone_question": "What are the products of photosynthesis?",
    "created_at": "2025-01-15T10:32:00Z"
  }
]
```

## Example Conversation Flow

### Scenario: Multi-turn discussion about photosynthesis

```
TURN 1: First Question (No Condensation)
─────────────────────────────────────────

User Input:
  "What is photosynthesis?"

Processing:
  - No prior messages → skip condensation
  - standalone_question = "What is photosynthesis?"
  - Retrieve top-4 chunks matching original question
  - Generate answer from textbook excerpts

Response:
  answer: "Photosynthesis is the process by which plants..."
  standalone_question: "What is photosynthesis?"
  sources: [Page 42, Page 43, Page 45]
  session_id: 1


TURN 2: Follow-up (With Condensation)
──────────────────────────────────────

User Input:
  "What are the products?"

Processing:
  - Fetch session history: [Turn 1 Q&A]
  - Condense using LLM:
    Input: "History + 'What are the products?'"
    Output: "What are the products of photosynthesis?"
  - Retrieve using condensed question
  - Generate answer from textbook

Response:
  answer: "The main products are glucose and oxygen..."
  standalone_question: "What are the products of photosynthesis?"
  sources: [Page 42, Page 44]
  session_id: 1


TURN 3: Out-of-Topic (Guardrail)
─────────────────────────────────

User Input:
  "What's the capital of France?"

Processing:
  - Condense: "What's the capital of France?"
  - Retrieve from photosynthesis textbook: zero matching chunks
  - Guardrail activates

Response:
  answer: "I cannot find this information in the provided textbook excerpts."
  standalone_question: "What's the capital of France?"
  sources: []
  session_id: 1
```

## Authorization & Access Control

### Rules (403 Forbidden if violated)

1. **Textbook Access**: User can only query textbooks they uploaded
2. **Session Access**: User can only view sessions for their textbooks
3. **Message Access**: User can only see messages from their sessions
4. **Update/Delete**: User can only modify their own records

### Implementation

```python
# Example: Verify textbook ownership
stmt = select(Textbook).where(
    and_(
        Textbook.id == textbook_id,
        Textbook.user_id == current_user.id
    )
)
result = await db.execute(stmt)
textbook = result.scalar_one_or_none()

if not textbook:
    raise HTTPException(status_code=403, detail="Access denied")
```

## Testing

### Unit Tests (No API Required)

```bash
cd backend
python test_conversational_logic.py
```

Verifies:
- Query condensation strategy
- Conversation formatting
- Session isolation
- Guardrail persistence

### Integration Tests (API Required)

**Setup:**
1. Set `CEREBRAS_API_KEY` and `PINECONE_API_KEY` in `.env`
2. Start backend: `uvicorn app.main:app --reload`
3. Create database: Already done on startup

**Test Script:**

```bash
# 1. Signup two users
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@test.com","password":"pass123"}'

curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user2@test.com","password":"pass123"}'

# 2. Upload textbooks (each user)
# 3. Ask questions and verify:
#    - Session isolation
#    - Condensation in responses
#    - Guardrails for out-of-topic
#    - Authorization checks
```

## Performance Considerations

### Query Condensation Cost

- **LLM Call**: 1 extra call to Cerebras per follow-up question
- **Trade-off**: Improved retrieval quality > slight latency increase
- **Optimization**: Cache condensed questions? (Future work)

### Database Queries per Request

1. Fetch user (auth dependency)
2. Fetch textbook (authorization check)
3. Fetch/create ChatSession
4. Fetch session history (6 messages max)
5. Save 2 messages (user + assistant)

Total: ~5 DB queries per ask() call

### Vector Store Access

1. Retrieval using standalone question
2. Scoped to user's textbook namespace

## Future Enhancements

1. **Streaming**: Implement `/ask/stream` with token-level streaming
2. **Context Caching**: Cache condensed questions for identical follow-ups
3. **Feedback Loop**: Save user feedback on condensation quality
4. **Hybrid Search**: Combine dense (embedding) + sparse (keyword) retrieval
5. **Multi-Document**: Support Q&A across multiple textbooks in one session
6. **RAG Eval**: Measure condensation quality, citation accuracy

## Troubleshooting

### "Not found in textbook" for valid questions

**Possible causes:**
1. PDF not fully ingested (low chunk count)
2. Question uses different terminology than textbook
3. Condensation produced misleading standalone question

**Debug:**
- Check `/sessions/{id}/messages` for `standalone_question` field
- Look at console output during query condensation
- Verify PDF ingestion success

### Session not found (403)

**Possible causes:**
1. Wrong user ID (signed in as different account)
2. Session belongs to different textbook
3. Session_id typo

**Debug:**
- Confirm JWT token for correct user
- List sessions: `GET /sessions?textbook_id=...`
- Check session belongs to expected textbook

## Code Locations

- **Query Condensation**: `app/rag_chain.py::condense_question()`
- **RAG Chain**: `app/rag_chain.py::ask_question()`
- **API Endpoints**: `app/main.py::ask()`, `GET /sessions`, etc.
- **Models**: `app/models.py::ChatMessage`, `ChatSession`
- **Tests**: `test_conversational_logic.py`, `test_rag_chain.py`
