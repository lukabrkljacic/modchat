# Component-Based LLM Chat Interface

A modular Flask application packaged for containerized deployment that delivers a unified API and web UI for interacting with AI language models across multiple providers. This interface features a unique component-based approach that breaks down AI responses into structured, editable components, enabling a streamlined component-based response workflow.

## Features

- Separate AI responses into logical components
- Edit each component individually
- Generate formatted final outputs from components

### Advanced Configuration
- Customizable system prompts
- JSON-based structured output formats
- Adjustable model parameters (temperature, context length, etc.)
- Chunking and token management

### Document Processing
- Process uploaded files (TXT, CSV, PDF, DOCX, etc.)
- Automatic text chunking for context management
- Content extraction and summarization

### Conversation Management
- Persistent conversation history
- Conversation retrieval and deletion
- Memory-efficient storage with LRU eviction
- Session-based storage groups multiple conversations under a single session ID

### Model Integration
- Supports multiple language model providers:
  - OpenAI (GPT-4, GPT-4.1)
  - Anthropic (Claude 3 models)
- Vendor-agnostic design supports easy addition of new providers

## Prerequisites

- Docker & Docker Compose
- API keys for supported model providers (OpenAI, Anthropic, etc.)

## Quickstart

1. Clone the repo and enter the `app` directory:

```bash
git clone <repository-url>
cd modchat/app
```

2. Set up your API keys

Go the the `backend` folder and create a `.env` file (you can reuse the `env_sample` file for this purpose.) Fill in the API key for your language model service provider. 

Example:

```
# .env

OPENAI_API_KEY=<Your-openai-api-key-goes-here>
```

3. Start the docker container services

```bash
docker compose up -d
```

Once the containers finish building, you can go to the main chat interface at: http://modchat.localhost

=======

## Usage
1. **Select a Model**: Choose an AI model from the dropdown menu
2. **Toggle Advanced Mode**: Enable to access system prompt and advanced settings
3. **Enter Your Message**: Type your query in the input field
4. **View Components**: See how the AI breaks down its response
5. **Edit Components**: Click the edit icon to modify any component
6. **Generate Final Output**: Combine components into a formatted result
7. **Copy Output**: Use the copy button to quickly copy the final output

## Interface Features
- **System Prompt**: Control the AI's behavior and instructions
- **User Prompt**: Your message to the AI
- **Main Response**: The AI's complete response
- **Component Breakdown**: Individual parts of the response
- **Final Output**: Combined components formatted for a specific purpose

## Extending Model Support
1. Update `app/backend/src/model_factory.py` to add a new handler method
2. Add provider-specific error handling in `app/backend/src/error_handlers.py`
3. Update the `AVAILABLE_VENDORS` list in `app/backend/src/app.py`

## Project Structure
```
modchat/
├── app/
│   ├── backend/        # FastAPI backend
│   ├── frontend/       # Frontend interface
│   ├── mod-agent/      # Documentation agent service
│   ├── database/       # Database service configuration
│   ├── reverse-proxy/  # Caddy reverse proxy
│   └── docker-compose.yml
└── README.md
```

## Environment Variables

The environment variables listed below drive the container-level configuration for every service—things like image tags, hostnames, ports, and internal URLs—so the stack is easy to customize while still working out-of-the-box. Sensible defaults are provided, so you don’t need to change anything to get started, but you can override any value as needed. The shared variables live in the `app` root [`.env`](./app/.env) and are referenced by docker-compose.yml; each service also loads its own .env at startup for service-specific settings. This separation keeps configuration clear, predictable, and highly flexible.

| Variable                       | Data Type             | Description                                                       | Default Value                                                   |
| ------------------------------ | --------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------- |
| FRONTEND\_BUILD\_TARGET        | string                | Build target/stage for the frontend image (e.g., prod/dev).       | `prod`                                                          |
| FRONTEND\_CONTAINER\_NAME      | string                | Docker container name for the frontend service.                   | `modchat.frontend.com`                                          |
| FRONTEND\_HOSTNAME             | string                | Hostname used on the Docker network for the frontend.             | `modchat-frontend`                                              |
| FRONTEND\_IMAGE\_TAG\_PREFIX   | string                | Prefix used when tagging/publishing frontend images.              | `modchat-frontend`                                              |
| FRONTEND\_EXTERNAL\_PORT       | integer               | Host (public) port exposed for the frontend.                      | `8888`                                                          |
| FRONTEND\_INTERNAL\_PORT       | integer               | Container port the frontend listens on.                           | `8000`                                                          |
| FRONTEND\_PORT\_MAPPING        | string (port mapping) | Host-to-container port mapping for frontend (`host:container`).   | `${FRONTEND_EXTERNAL_PORT}:${FRONTEND_INTERNAL_PORT}`           |
| FRONTEND\_URL                  | URL                   | Internal/base URL to reach the frontend.                          | `http://${FRONTEND_CONTAINER_NAME}:${FRONTEND_INTERNAL_PORT}`   |
| BACKEND\_BUILD\_TARGET         | string                | Build target/stage for the backend image.                         | `prod`                                                          |
| BACKEND\_CONTAINER\_NAME       | string                | Docker container name for the backend service.                    | `modchat.backend.com`                                           |
| BACKEND\_HOSTNAME              | string                | Hostname used on the Docker network for the backend.              | `modchat-backend`                                               |
| BACKEND\_IMAGE\_TAG\_PREFIX    | string                | Prefix used when tagging/publishing backend images.               | `modchat-backend`                                               |
| BACKEND\_EXTERNAL\_PORT        | integer               | Host (public) port exposed for the backend.                       | `5555`                                                          |
| BACKEND\_INTERNAL\_PORT        | integer               | Container port the backend listens on.                            | `5000`                                                          |
| BACKEND\_PORT\_MAPPING         | string (port mapping) | Host-to-container port mapping for backend (`host:container`).    | `${BACKEND_EXTERNAL_PORT}:${BACKEND_INTERNAL_PORT}`             |
| BACKEND\_URL                   | URL                   | Internal/base URL to reach the backend.                           | `http://${BACKEND_CONTAINER_NAME}:${BACKEND_INTERNAL_PORT}`     |
| MOD\_AGENT\_BUILD\_TARGET      | string                | Build target/stage for the MOD Agent image.                       | `prod`                                                          |
| MOD\_AGENT\_CONTAINER\_NAME    | string                | Docker container name for the MOD Agent.                          | `modchat.agent.com`                                             |
| MOD\_AGENT\_HOSTNAME           | string                | Hostname used on the Docker network for the MOD Agent.            | `modchat-agent`                                                 |
| MOD\_AGENT\_IMAGE\_TAG\_PREFIX | string                | Prefix used when tagging/publishing MOD Agent images.             | `modchat-agent`                                                 |
| MOD\_AGENT\_INTERNAL\_PORT     | integer               | Container port the MOD Agent listens on.                          | `9999`                                                          |
| MOD\_AGENT\_EXTERNAL\_PORT     | integer               | Host (public) port exposed for the MOD Agent.                     | `9999`                                                          |
| MOD\_AGENT\_PORT\_MAPPING      | string (port mapping) | Host-to-container port mapping for MOD Agent (`host:container`).  | `${MOD_AGENT_EXTERNAL_PORT}:${MOD_AGENT_INTERNAL_PORT}`         |
| MOD\_AGENT\_URL                | URL                   | Internal/base URL to reach the MOD Agent.                         | `http://${MOD_AGENT_CONTAINER_NAME}:${MOD_AGENT_INTERNAL_PORT}` |
| POSTGRES\_CONTAINER\_NAME      | string                | Docker container name for PostgreSQL.                             | `postgres`                                                      |
| POSTGRES\_HOSTNAME             | string                | Hostname used on the Docker network for PostgreSQL.               | `postgres`                                                      |
| POSTGRES\_EXTERNAL\_PORT       | integer               | Host (public) port exposed for PostgreSQL.                        | `55432`                                                         |
| POSTGRES\_INTERNAL\_PORT       | integer               | Container port PostgreSQL listens on.                             | `5432`                                                          |
| POSTGRES\_PORT\_MAPPING        | string (port mapping) | Host-to-container port mapping for PostgreSQL (`host:container`). | `${POSTGRES_EXTERNAL_PORT}:${POSTGRES_INTERNAL_PORT}`           |
| PGADMIN\_CONTAINER\_NAME       | string                | Docker container name for pgAdmin.                                | `pgadmin`                                                       |
| PGADMIN\_HOSTNAME              | string                | Hostname used on the Docker network for pgAdmin.                  | `pgadmin`                                                       |
| PGADMIN\_EXTERNAL\_PORT        | integer               | Host (public) port exposed for pgAdmin.                           | `8889`                                                          |
| PGADMIN\_INTERNAL\_PORT        | integer               | Container port pgAdmin listens on.                                | `8080`                                                          |
| PGADMIN\_PORT\_MAPPING         | string (port mapping) | Host-to-container port mapping for pgAdmin (`host:container`).    | `${PGADMIN_EXTERNAL_PORT}:${PGADMIN_INTERNAL_PORT}`             |
| PGADMIN\_URL                   | URL                   | Internal/base URL to reach pgAdmin.                               | `http://${PGADMIN_CONTAINER_NAME}:${PGADMIN_INTERNAL_PORT}`     |


## License
MIT

