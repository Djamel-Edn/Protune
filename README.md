<div align="center">

# Protune

**Paste a job posting. Get your CV retargeted and your cover letter written.**

AI-powered job analysis, CV rewriting and cover letter drafting — no sign-up required.

`Next.js` · `FastAPI` · `Gemini` · `Supabase`

**[Live app](https://protune-eight.vercel.app)** · **[API](https://protuneapi.vercel.app/docs)**

🚧 **Under construction** — see the [roadmap](#roadmap). The generator ships at milestone 6.

</div>

---

## The problem

Tailoring your CV to each posting is what gets you past an ATS — and it's exactly what nobody does, because it takes 40 minutes per application.

Protune brings that down to 30 seconds: a job posting in, a retargeted CV and a personalised cover letter out.

## How it works

```
Job posting (URL or text)        CV (PDF)
          │                         │
          └───────────┬─────────────┘
                      ▼
          ┌───────────────────────┐
          │  Posting analysis     │  role, company, key skills, ATS keywords
          └───────────┬───────────┘
                      ▼
          ┌───────────────────────┐
          │  Cover letter         │  written in your voice, grounded in the company
          └───────────┬───────────┘
                      ▼
          ┌───────────────────────┐
          │  Adapted CV           │  headline, summary and projects retargeted
          └───────────┬───────────┘
                      ▼
                  PDF export
```

## Architecture

The system deliberately separates two paths:

| Path | Runs on |
|---|---|
| **Product path** — a user is waiting for the result on screen | Next.js + FastAPI |
| **Ops path** — triggered by a schedule or a webhook, nobody is waiting | n8n |

Job digests, application follow-ups and internal notifications stay in n8n. The critical path is code: testable, reviewable in a diff, and multi-tenant.

> **This project was first prototyped entirely in n8n.** The pipeline — scrape → analyse → letter → CV — was validated there in a few days, prompts included. This repository is the port: the prompts carry over as-is, but the candidate profile, hard-coded in the prototype, becomes an *input*. That single change is what turns a personal automation into a product.

## Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 16 (App Router, TypeScript, Tailwind 4) — Vercel |
| API | FastAPI, Python 3.12 — Vercel (Python runtime) |
| LLM | Google Gemini (`gemini-flash-lite-latest`) |
| Data | Supabase (Postgres + Storage) |
| Quotas | Upstash Redis |

Design decisions and trade-offs are documented in [`docs/PLAN.md`](docs/PLAN.md).

## Local development

**Requirements:** Node 20+, Python 3.12, and a free [Google AI Studio](https://aistudio.google.com/apikey) API key.

```bash
git clone https://github.com/Djamel-Edn/Protune.git
cd Protune
cp .env.example .env   # then fill in GEMINI_API_KEY
```

```bash
# API
cd api && py -3.12 -m venv .venv && .venv/Scripts/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

```bash
# Web
cd web && npm install && npm run dev
```

The app runs on `http://localhost:3000`, the API on `http://localhost:8000` (auto-generated docs at `/docs`).

## Roadmap

- [x] **1** — Skeleton, `/health`, end-to-end deployment
- [x] **2** — CV parsing (PDF text extraction, with actionable errors)
- [x] **3** — Gemini pipeline: analyse → letter → CV
- [x] **4** — SSE streaming and full frontend flow
- [ ] **5** — PDF export
- [ ] **6** — Landing page and rate-limited public demo
- [ ] **7** — Polish, final README, demo video
- [ ] *Later* — accounts, application tracker, job search with AI scoring

## Privacy

In demo mode, **CV contents are not retained** — only generation metadata (duration, model, timestamp) is stored. IP addresses are never stored in clear text, only hashed, and solely to enforce quotas.

## Licence

MIT — see [LICENSE](LICENSE).
