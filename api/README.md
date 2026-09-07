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

Fly.io, from the `Dockerfile`. See `fly.toml`.

```bash
fly launch --no-deploy --copy-config    # first time only
fly secrets set GEMINI_API_KEY=...
fly deploy
```
