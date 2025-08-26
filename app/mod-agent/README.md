# MOD Agent Service

The MOD Agent provides response decomposition for Modchat. It implements the Agent-to-Agent (A2A) protocol and accepts model output from the backend, returning structured components that the frontend can render and edit.

## How it fits in
- **Backend** – The backend calls the `/decompose` endpoint on this service whenever a chat request sets `decompose: true`.
- **Frontend** – Users enable decomposition through the UI; returned components are displayed in the Component Breakdown column.
- **Reverse Proxy** – The Caddy reverse proxy exposes this service at `http://modchat.localhost/agent/`.

## Running locally
1. Create a `.env` file from `env.sample` and supply any provider keys required by your decomposition model.
2. Build and run the container:
   ```bash
   docker build . -t mod-agent
   docker run -p 9999:9999 --env-file .env mod-agent
   ```
3. Verify the service:
   ```bash
   curl http://modchat.localhost/agent/info
   ```

The service listens on port `9999` and returns a list of components for each decomposition request.
