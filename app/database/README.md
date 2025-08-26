# Database Service

This directory configures the Postgres database used by the Modchat backend. A companion pgAdmin container is provided for inspecting data through the browser.

## How it fits in
- **Backend** – Uses the `DATABASE_URL` defined in `.env` to store conversation memory and feedback.
- **Reverse Proxy** – Exposes pgAdmin at `http://database.modchat.localhost` for administration.

## Configuration
The `.env` file defines default credentials and ports:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=pgpass
POSTGRES_DB=modchat
POSTGRES_PORT=5432
POSTGRES_HOSTNAME=postgres
PGADMIN_DEFAULT_EMAIL=admin@99Plabs.com
PGADMIN_DEFAULT_PASSWORD=password
PGADMIN_LISTEN_PORT=8080
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOSTNAME:$POSTGRES_PORT/$POSTGRES_DB
```
Adjust these values as needed before starting the stack.

## Usage
The database service is started automatically with `docker compose up`. pgAdmin can be reached via the reverse proxy for debugging or management tasks.
