# Frontend Service

The frontend is a Flask application that delivers the web interface for Modchat. It presents a four-column chat layout, allows file uploads, and lets users edit decomposed components before generating a final output.

## How it fits in
- **Backend** – All user actions are sent to the backend via the `BACKEND_BASE_URL` or `BACKEND_EXTERNAL_BASE_URL` setting.
- **MOD Agent** – Decomposition is triggered by the backend; results are displayed in the Component Breakdown column when enabled.
- **Reverse Proxy** – The Caddy reverse proxy serves this service at `http://modchat.localhost` and forwards API calls to the backend and MOD Agent.

## Project structure
```
app/frontend/
├── src/
│   ├── app.py          # Flask entry point
│   ├── templates/      # Jinja2 templates
│   └── static/         # CSS and JavaScript assets
├── requirements.txt
└── Dockerfile
```

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
