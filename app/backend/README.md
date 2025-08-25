# LLM Chat Interface - API Documentation

This document provides comprehensive documentation for the REST API endpoints available in the LLM Chat Interface backend service located at `servers/backend/src/mod/app.py`.

## Base URL
```
http://localhost:5000
```

## Authentication
The API requires API keys for LLM providers to be set as environment variables:
- `OPENAI_API_KEY` - Required for OpenAI models
- `ANTHROPIC_API_KEY` - Required for Anthropic models

## Content Type
All POST endpoints expect `application/json` content type unless otherwise specified.

---

## Endpoints

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

### 3. Analytics/Event Logging

**Log user interaction events for analytics**

```http
POST /analytics
```

**Body:**
```json
{
  "event_type": "component_edited",
  "conversation_id": "conv-456",
  "session_id": "session-123",
  "data": {
    "component_id": "comp-1",
    "original_content": "Original text",
    "edited_content": "Modified text"
  }
}
```

**Required Fields:**
- `event_type` (string): Type of event being logged

**Optional Fields:**
- `conversation_id` (string): Associated conversation ID (defaults to "global")
- `session_id` (string): Session identifier
- `data` (object): Additional event data

**Response:**
```json
{
  "success": true
}
```

**Error Response:**
```json
{
  "error": "Missing event_type"
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing event_type
- `500` - Failed to log event

---

### 4. Available Models

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

### 5. Health Check

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

---

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

---

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

---

## File Upload Support

The API supports the following file types for upload and processing:

- **Text Files**: `.txt`
- **PDF Documents**: `.pdf`
- **Word Documents**: `.docx`
- **Excel Files**: `.xlsx`, `.csv`
- **Other formats** as supported by the file handlers

Uploaded files are processed and their content can be included in chat requests for context-aware responses.

---

## Response Decomposition

When `decompose: true` is set in the chat request, the API will attempt to break down the AI response into logical components such as:

- **Email Components**: Subject, greeting, body, closing
- **Report Components**: Title, executive summary, findings, recommendations
- **General Components**: Based on content structure

This enables the frontend to provide component-based editing capabilities.

---

## Rate Limiting and Quotas

Rate limiting is handled by the underlying AI service providers (OpenAI, Anthropic). The API will return appropriate error messages when rate limits are exceeded.

---

## Environment Variables

The following environment variables configure the API:

| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_FOLDER` | Directory for file uploads | `uploads` |
| `MAX_UPLOAD_SIZE` | Maximum file size in bytes | `16777216` (16MB) |
| `CONVERSATION_STORAGE_DIR` | Conversation persistence directory | `conversations` |
| `MAX_CONVERSATIONS_IN_MEMORY` | Memory limit for conversations | `100` |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI models |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required for Anthropic models |

---

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

---

## Notes

- All conversation history is automatically managed by the conversation manager
- File uploads are temporarily stored and processed for content extraction
- The API supports both stateless and stateful conversation modes
- Component decomposition is powered by an integrated task decomposition tool
- CORS is enabled for frontend integration