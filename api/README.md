# Protune — API

FastAPI backend (Python 3.12).

```bash
py -3.12 -m venv .venv
.venv/Scripts/activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. Interactive docs at `/docs`.

| Path | Purpose |
|---|---|
| `app/main.py` | Application entrypoint and middleware |
| `app/config.py` | Settings, loaded from the environment |
| `app/routers/` | HTTP routes, mounted under `/api/v1` |
| `app/services/` | Business logic — scraping, CV parsing, Gemini calls |
| `app/prompts/` | Prompt templates, ported from the n8n prototype |

## Checks

```bash
ruff check . && ruff format --check . && pytest -q
```

## Deployment

Deployed to **Vercel** as its own project, with **Root Directory** set to `api`.
Vercel detects FastAPI from `requirements.txt` and loads the handler declared by
`tool.vercel.entrypoint` in `pyproject.toml` (`app.main:app`).

Environment variables to set in the Vercel dashboard:

| Variable | Value |
|---|---|
| `GEMINI_API_KEY` | from Google AI Studio |
| `CORS_ORIGINS` | the deployed web URL, e.g. `https://protune-eight.vercel.app` |

Constraints inherited from the platform:

- request bodies are capped at **4.5 MB**, so CV uploads are limited to 4 MB
- functions may run for up to **300 s** on the free plan — ample for a 20–30 s pipeline

### Container alternative

`Dockerfile` and `fly.toml` are kept so the API can run on any container host without
changes. Fly.io itself requires a credit card, so it is not the default target.

```bash
docker build -t protune-api . && docker run -p 8000:8000 protune-api
```
