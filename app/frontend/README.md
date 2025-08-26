# Frontend Service

The frontend is a Flask application that delivers the web interface for Modchat. It presents a four-column chat layout, allows file uploads, and lets users edit decomposed components before generating a final output.

## Project Structure
```
app/frontend/
├── src/
│   ├── app.py          # Flask routes and request handling
│   ├── templates/      # Jinja2 templates for the UI
│   └── static/         # CSS, JavaScript, and image assets
├── env.sample          # Example environment variables
├── requirements.txt    # Python dependencies
└── Dockerfile          # Container build instructions
```

## How it works
1. `app.py` starts the Flask server and serves the main chat page.
2. Client-side JavaScript posts messages and file uploads to the backend endpoints defined in the environment.
3. Responses from the backend update the chat interface and, if enabled, display decomposed components for editing.

## How it fits in
- **Backend** – All user actions are sent to the backend via the `BACKEND_BASE_URL` or `BACKEND_EXTERNAL_BASE_URL` setting.
- **MOD Agent** – Decomposition is triggered by the backend; results are displayed in the Component Breakdown column when enabled.
- **Reverse Proxy** – The Caddy reverse proxy serves this service at `http://modchat.localhost` and forwards API calls to the backend and MOD Agent.

## Environment variables
```
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=8080
BACKEND_BASE_URL=http://localhost:5000
BACKEND_EXTERNAL_BASE_URL=http://localhost:5000
MODEL_LISTING_ENDPOINT=models
```
The base URLs should point to the backend service. When using Docker compose these values are supplied automatically from the root `.env` file.

## Running locally
```bash
pip install -r requirements.txt
python src/app.py
```
The application listens on port `8080` in development and is available through the reverse proxy at `http://modchat.localhost`.
