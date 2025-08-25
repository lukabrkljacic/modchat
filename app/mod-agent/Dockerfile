# Production
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS prod

WORKDIR /src

COPY src .
COPY ./src/requirements.txt .

RUN uv pip install --no-cache-dir -r requirements.txt --system

EXPOSE 9999

# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
ENTRYPOINT ["fastapi"]
CMD ["run", "server.py", "--port", "9999"]

# Dev/Debug
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS dev

WORKDIR /src

COPY src .
COPY ./src/requirements.txt .

RUN uv pip install --no-cache-dir -r requirements.txt --system && \
    uv pip install --no-cache-dir jupyterlab --system

ENV JUPYTER_TOKEN=ai

EXPOSE 9999

CMD ["jupyter", "lab", "--ip","0.0.0.0", "--port", "9999", "--notebook-dir", "/src", "--no-browser", "--allow-root"]