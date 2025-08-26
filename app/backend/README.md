# Backend Service

The backend is a FastAPI application that exposes the core API for the Modchat stack. It receives chat and file-upload requests from the frontend, communicates with language model providers, and stores conversation state in Postgres.


## Project Structure
```
app/backend/
├── src/
│   └── mod/
│       ├── app.py                   # FastAPI endpoints and application wiring
│       ├── conversation_manager.py  # Session and conversation persistence
│       ├── file_handlers.py         # File upload handling
│       ├── errors/                  # Custom exceptions and handlers
│       ├── enums/                   # Enumerations for model vendors
│       └── models/
│           ├── model_factory.py     # Creates client for selected model vendor
│           └── model_registry.py    # Registry of available models
├── uploads/                         # Temporary file storage
├── requirements.txt                 # Python dependencies
├── env.sample                       # Example environment configuration
└── Dockerfile                       # Container build instructions
```

## How it works
1. `app.py` initializes the FastAPI app and defines endpoints like `/chat` and `/upload`.
2. Incoming chat requests use `conversation_manager.py` to track sessions and conversations.
3. `model_factory.py` selects and initializes the correct vendor client before the request is sent to the language model.
4. Optional files are processed by `file_handlers.py` and included in the prompt.
5. Results can be sent to the MOD Agent for decomposition before being returned to the frontend.

## How it fits in
- **Frontend** – The web client calls the `/chat`, `/upload`, and `/models` endpoints to interact with models and manage files.
- **Database** – Conversation history and feedback are persisted via the `DATABASE_URL` connection string.  A Postgres and pgAdmin instance are provided by the database service.
- **MOD Agent** – When the `decompose` flag is set, the backend sends model output to the MOD Agent at `MOD_AGENT_URL` for structured component generation.
- **Reverse Proxy** – Requests routed to `/api/*` by the Caddy reverse proxy are forwarded to this service.

## Key Endpoints
| Endpoint | Method | Description |
| --- | --- | --- |
| `/upload` | POST | Accepts files for later use in a chat request. |
| `/chat` | POST | Sends a prompt to the selected model and returns the response. |
| `/models` | GET | List available models. |
| `/health` | GET | Health check for the service. |

All POST endpoints expect `application/json` content type unless otherwise specified.

---

### 1. File Upload

**Upload a file for processing**

```http
POST /upload
```

**Headers:**
```
Content-Type: multipart/form-data
```

**Body:**
- `file` (file): The file to upload

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "file_path": "/uploads/document.pdf",
  "supported": true
}
```

**Error Response:**
```json
{
  "error": "No file part"
}
```

**Status Codes:**
- `200` - Success
- `400` - No file part or empty filename
- `500` - File upload failed

---

### 2. Chat

**Send a message to the AI and receive a response**

```http
POST /chat
```

**Body:**
```json
{
  "message": "Hello, how are you?",
  "model": "gpt-4.1-mini",
  "vendor": "openai",
  "settings": {
    "systemPrompt": "You are a helpful assistant",
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "files": [
    {
      "filename": "document.pdf",
      "content": "extracted text content"
    }
  ],
  "decompose": true,
  "session_id": "session-123",
  "conversation_id": "conv-456"
}
```

**Required Fields:**
- `message` (string): The user's message
- `model` (string): The model ID to use
- `vendor` (string): The vendor name (openai, anthropic)

**Optional Fields:**
- `settings` (object): Model configuration settings
- `files` (array): Uploaded files for context
- `decompose` (boolean): Whether to decompose the response into components
- `session_id` (string): Session identifier
- `conversation_id` (string): Conversation identifier (auto-generated if not provided)

**Response:**
```json
{
  "text": "Hello! I'm doing well, thank you for asking.",
  "model": "gpt-4.1-mini",
  "vendor": "openai",
  "conversation_id": "conv-456",
  "components": [
    {
      "type": "greeting",
      "content": "Hello! I'm doing well, thank you for asking.",
      "title": "Greeting"
    }
  ]
}
```

**Error Response:**
```json
{
  "error": "Empty message"
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing required fields or validation error
- `500` - Internal processing error

---

### 3. Available Models

**Get list of available AI models and vendors**

```http
GET /models
```

**Response:**
```json
{
  "vendors": [
    {
      "id": "openai",
      "name": "OpenAI",
      "models": [
        {
          "id": "gpt-4.1-mini",
          "name": "GPT-4.1 Mini"
        },
        {
          "id": "gpt-4.1-nano",
          "name": "GPT-4.1 Nano"
        },
        {
          "id": "gpt-4.1",
          "name": "GPT-4.1"
        }
      ]
    },
    {
      "id": "anthropic",
      "name": "Anthropic",
      "models": [
        {
          "id": "claude-3-opus-latest",
          "name": "Claude 3 Opus"
        },
        {
          "id": "claude-3-7-sonnet-latest",
          "name": "Claude 3.7 Sonnet"
        },
        {
          "id": "claude-3-5-haiku-latest",
          "name": "Claude 3.5 Haiku"
        }
      ]
    }
  ]
}
```

**Status Codes:**
- `200` - Success

---

### 4. Health Check

**Check API health and configuration status**

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "api_keys": {
    "openai": true,
    "anthropic": true
  },
  "file_types": ["txt", "pdf", "docx", "csv"],
  "vendors": ["openai", "anthropic"]
}
```

**Status Codes:**
- `200` - Success

## Error Handling

### Global Error Responses

**404 Not Found:**
```json
{
  "error": "Not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

### Custom Error Types

The API includes custom error handling for:

- **ModelInitializationError** - Issues with AI model setup
- **FileProcessingError** - Problems processing uploaded files
- **ConversationError** - Conversation management issues

## Settings Configuration

The following settings can be passed in the `settings` object of the `/chat` endpoint:

### Common Settings
- `systemPrompt` (string): Custom system prompt for the AI
- `temperature` (float): Randomness in responses (0.0-1.0)
- `max_tokens` (integer): Maximum response length

### OpenAI Specific
- `top_p` (float): Nucleus sampling parameter
- `frequency_penalty` (float): Penalty for repeated tokens
- `presence_penalty` (float): Penalty for new topic introduction

### Anthropic Specific
- `top_k` (integer): Top-k sampling parameter
- `max_tokens_to_sample` (integer): Maximum tokens in response

## File Upload Support

The API supports the following file types for upload and processing:

- **Text Files**: `.txt`
- **PDF Documents**: `.pdf`
- **Word Documents**: `.docx`
- **Excel Files**: `.xlsx`, `.csv`
- **Other formats** as supported by the file handlers

Uploaded files are processed and their content can be included in chat requests for context-aware responses.

## Rate Limiting and Quotas

Rate limiting is handled by the underlying AI service providers (OpenAI, Anthropic). The API will return appropriate error messages when rate limits are exceeded.

## Environment variables
Create an `.env` file based on `env.sample` and provide API keys and optional overrides. Important variables include:
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` – provider credentials
- `DATABASE_URL` – Postgres connection string
- `MOD_AGENT_URL` – base URL for decomposition requests
- `UPLOAD_FOLDER` – location for temporary file storage

## Running locally
```bash
uv pip install -r requirements.txt --system
python src/mod/app.py
```
The service listens on port `5000` by default. When using Docker compose it is available internally as `http://modchat.backend.com:5000` and externally through the reverse proxy at `http://modchat.localhost/api/`.

## Example Usage

### Basic Chat Request
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "model": "gpt-4.1-mini",
    "vendor": "openai",
    "settings": {
      "temperature": 0.7
    }
  }'
```

### File Upload
```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@document.pdf"
```

### Health Check
```bash
curl http://localhost:5000/health
```

## Notes

- All conversation history is automatically managed by the conversation manager
- File uploads are temporarily stored and processed for content extraction
- The API supports both stateless and stateful conversation modes
- Component decomposition is powered by an integrated task decomposition tool
- CORS is enabled for frontend integration