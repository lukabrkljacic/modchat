# Backend Service

The backend is a FastAPI application that exposes the core API for the Modchat stack. It receives chat and file-upload requests from the frontend, communicates with language model providers, and stores conversation state in Postgres.

## How it fits in
- **Frontend** – The web client calls the `/chat`, `/upload`, and `/models` endpoints to interact with models and manage files.
- **Database** – Conversation history and feedback are persisted via the `DATABASE_URL` connection string.  A Postgres and pgAdmin instance are provided by the database service.
- **MOD Agent** – When the `decompose` flag is set, the backend sends model output to the MOD Agent at `MOD_AGENT_URL` for structured component generation.
- **Reverse Proxy** – Requests routed to `/api/*` by the Caddy reverse proxy are forwarded to this service.

## Key Endpoints
| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Health check for the service. |
| `/models` | GET | List available models. |
| `/upload` | POST | Accepts files for later use in a chat request. |
| `/chat` | POST | Sends a prompt to the selected model and returns the response. |

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
