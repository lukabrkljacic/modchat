# Production
FROM python:3.11 AS prod

RUN apt-get update -y && \
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin/:$PATH"

COPY src ./src/
WORKDIR /src

RUN uv pip install --no-cache-dir -r requirements.txt --system

ENV FLASK_APP=/src/app.py

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]

