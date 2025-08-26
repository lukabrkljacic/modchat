# Modchat Application

This directory contains the Docker compose configuration and service definitions for the Modchat stack. The project provides a component-based chat interface that can optionally decompose model responses into editable parts.

## Components
- **Frontend** – Flask web interface served at `http://modchat.localhost`.
- **Backend** – FastAPI service handling chat requests, file uploads, and conversation management.
- **MOD Agent** – Optional decomposition service implementing the A2A protocol.
- **Database** – Postgres for conversation memory with a pgAdmin interface.
- **Reverse Proxy** – Caddy server that exposes a single hostname and routes requests to the appropriate service.

## Request flow
1. A user visits the frontend and submits a prompt.
2. The frontend posts the request to the backend through the reverse proxy.
3. The backend queries the selected language model provider.
4. If `decompose` is **enabled**, the backend sends the model output to the MOD Agent, which returns structured components.  These components are stored alongside the conversation and returned to the frontend.
5. If `decompose` is **disabled**, the backend returns the raw model response directly.
6. The frontend renders the response and any components for further editing.

## Running the stack
1. Populate `app/.env` with any custom values.
2. Provide API keys in `app/backend/.env` and any model configuration for the MOD Agent.
3. From this directory run:
   ```bash
   docker compose up -d
   ```
4. Open `http://modchat.localhost` in your browser to use the interface. pgAdmin is available at `http://database.modchat.localhost`.
