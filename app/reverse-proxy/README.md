# Reverse Proxy

This service uses [Caddy](https://caddyserver.com/) to provide a single entry point for all components of the Modchat stack.


## Project Structure
```
app/reverse-proxy/
├── Caddyfile  # Proxy rules for routing requests
└── README.md  # Service documentation
```

## How it works
1. Caddy loads `Caddyfile` at startup.
2. Incoming requests are matched against route rules and forwarded to the frontend, backend, MOD Agent, or pgAdmin services.
3. This service provides a single entry point so the application is accessible at `http://modchat.localhost`.

## How it fits in
- Requests to `http://modchat.localhost` are routed based on path:
  - `/api/*` → backend service
  - `/agent/*` → MOD Agent service
  - all other paths → frontend service
- `http://database.modchat.localhost` proxies to the pgAdmin interface for the database.

## Configuration
Routing rules are defined in `Caddyfile` and use environment variables from the root `.env` file (`BACKEND_URL`, `MOD_AGENT_URL`, `FRONTEND_URL`, `PGADMIN_URL`).

## Usage
The reverse proxy container is started automatically by `docker compose up` and listens on port 80 of the host, making the application available at `http://modchat.localhost`.
