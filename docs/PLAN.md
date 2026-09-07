# Protune — Product & Technical Plan

> Reference document. Architecture decisions are made here before any code is written.
> **Status:** v1 in progress · **Last updated:** 7 September 2026

---

## 1. The product

**Protune adapts your CV and writes your cover letter from a job posting.**

You paste a posting (URL or text), supply your CV once, and get back:
- a **posting analysis**: role, company, key skills, ATS keywords
- an **adapted CV**: headline, summary and projects rewritten to match the posting
- a **personalised cover letter**, in your own voice
- both **exportable as PDF**

### v1 scope (what ships)
| | |
|---|---|
| ✅ | CV upload (PDF) → parsed into structured data |
| ✅ | Posting by URL (scraped) **or** pasted text |
| ✅ | Analysis + letter + adapted CV via Gemini, streamed |
| ✅ | PDF export for CV and letter |
| ✅ | Public demo, no sign-up |

### Out of scope for v1 (visible on the README roadmap)
| | |
|---|---|
| ⏭️ | Job search + AI scoring (the n8n `F1` workflow) — depends on Adzuna at 1000 req/month, which would not survive a public demo |
| ⏭️ | Application tracker + dashboard (the n8n `F3` workflow) — needs multi-user auth first |
| ⏭️ | Accounts, paid plans, Stripe |

### Default assumptions
1. **Public demo, no sign-up**, IP rate-limited to 3 generations/day. A recruiter will not create an account to try a tool.
2. **v1 is the CV + cover letter generator.** Tracker and job search come later.
3. **Product name `Protune`**, taken from the repository. Centralised in `web/lib/brand.ts` so renaming is a one-line change.
4. **English-only interface.** No i18n routing, no `/en` prefix — this keeps routes flat and the copy in one place.

---

## 2. Architecture

```
                        ┌──────────────────────────────┐
   Browser ───────────► │   Next.js (Vercel)           │
                        │   landing · app · PDF export │
                        └───────────────┬──────────────┘
                                        │ HTTPS / SSE
                                        ▼
                        ┌──────────────────────────────┐
                        │   FastAPI (Fly.io, Docker)   │
                        │   parse CV · scrape · Gemini │
                        └───┬──────────┬───────────┬───┘
                            │          │           │
                  ┌─────────▼──┐  ┌────▼──────┐  ┌─▼───────────┐
                  │  Gemini    │  │ Supabase  │  │  Upstash    │
                  │  API       │  │ PG+Storage│  │  (quotas)   │
                  └────────────┘  └───────────┘  └─────────────┘

  ─────────────────── product path (code) ─────────────────────
  ─────────────────── ops path (n8n, offline) ─────────────────

                        ┌──────────────────────────────┐
                        │   n8n (self-hosted)          │
                        │   daily digest · follow-ups  │
                        │   notifications · reporting  │
                        └──────────────────────────────┘
```

**The rule:** anything a user waits for on screen is code. Anything triggered by a schedule or a webhook, with nobody waiting, lives in n8n.

---

## 3. Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | **Next.js 16** (App Router, TypeScript, Tailwind 4) | Free, instant Vercel deploys; no cold start on the page a recruiter lands on |
| Backend | **FastAPI** (Python 3.12) | The standard way to serve AI in Python; matches the AI & Big Data profile |
| LLM | **Gemini** `gemini-flash-lite-latest` | Free tier at 15 RPM / 1000 RPD; prompts already validated in the n8n prototype |
| Posting scraper | **r.jina.ai** | Free, no API key, handles JS-rendered pages; already proven in n8n |
| PDF parsing | **pypdf** (with a `pdfplumber` fallback) | Sufficient for text-based CVs |
| Database | **Supabase** (Postgres + Storage) | Already provisioned for the n8n project; Auth ready for phase 2 |
| Demo quotas | **Upstash Redis** | Per-IP counters over a REST API — no persistent connection to keep alive |
| PDF export | **@react-pdf/renderer** (client-side, imported on click) | No headless browser to host; deterministic output. Its ~1 MB is dynamically imported so a visitor who never downloads never pays for it |
| Hosting | **Vercel** for both web and API | Free Hobby plan, no credit card, no cold start. See §9 |

> ⚠️ **Python 3.12, not 3.14.** The machine defaults to 3.14, but parts of the PDF/AI ecosystem still lag behind it. The virtualenv is created explicitly with `py -3.12`.

---

## 4. User flow

### Screen 1 — Landing `/`
Hero plus **a pre-generated example rendered immediately** (real posting → CV + letter). Zero cost, zero latency: even if the Gemini quota is exhausted, a visitor still sees the output. CTA: *Try it with my CV*.

### Screen 2 — App `/app`
Three steps on one page:
1. **Your CV** — upload a PDF, or click *use a sample CV* to try the tool without handing over personal data
2. **The posting** — URL or pasted text
3. **Generate** — streamed progress:
   `Reading the posting… → Analysing… → Writing the letter… → Adapting the CV…`

Streaming is not decoration: generation takes 20–30 s, and a dead progress bar for 30 s closes tabs.

### Screen 3 — Result
**Letter** / **Adapted CV** tabs, with a **before/after diff** on the CV — the single most convincing demonstration of what the product does. PDF export on each.

---

## 5. API contract

Base path: `/api/v1`

| Method | Route | Input | Output |
|---|---|---|---|
| `GET` | `/health` | — | `{status, version}` |
| `GET` | `/demo/quota` | — | `{remaining, limit, resets_at}` |

> `/generate` is a POST, so browsers cannot read it with `EventSource`, which is GET-only.
> The frontend reads the response body stream directly. A failure after the first byte
> cannot change the status code, so it travels as an `error` event — everything already
> streamed stays on screen.
| `POST` | `/cv/parse` | `multipart` (PDF ≤ 4 MB) | `{raw_text, page_count, character_count, truncated}` |
| `POST` | `/generate` | `{cv, offer_url?, offer_text?}` | **SSE** |

### SSE events emitted by `/generate`
```
event: step     data: {"step":"scrape","status":"done"}
event: analysis data: {"role":"…","company":"…","key_skills":[…],"ats_keywords":[…]}
event: letter   data: {"paragraphs":["…","…"]}
event: cv       data: {"headline":"…","summary":"…","projects":[…]}
event: done     data: {"duration_ms":24310,"model":"…"}
event: error    data: {"code":"RATE_LIMITED","message":"…"}
```

Error codes: `RATE_LIMITED`, `QUOTA_EXCEEDED` (Gemini), `SCRAPE_FAILED`, `PARSE_FAILED`,
`INVALID_PDF`, `FILE_TOO_LARGE`. Every error response is `{code, message}`; the frontend
branches on `code` and never on the message.

> **Why `/cv/parse` returns text rather than a structured CV.** Extraction is deterministic
> and exhaustively testable; structuring a CV is a language-model job. Keeping them apart
> makes uploads instant, spends no Gemini quota on a file the user may not even submit, and
> lets the parser be tested without an API key. The structured CV is produced inside
> `/generate`, where it is actually needed.

---

## 6. Database schema

```sql
-- v1 is anonymous: store only what serves analytics and abuse prevention
create table generations (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users on delete cascade,  -- null in demo mode
  ip_hash       text not null,          -- sha256(ip + IP_HASH_SALT), never the raw IP
  offer_url     text,
  offer_source  text not null check (offer_source in ('url','text')),
  analysis      jsonb,
  letter        jsonb,
  cv_adapted    jsonb,
  model         text not null,
  duration_ms   integer,
  status        text not null default 'ok',
  created_at    timestamptz not null default now()
);
create index on generations (ip_hash, created_at desc);

-- phase 2 (auth)
create table profiles (
  id         uuid primary key references auth.users on delete cascade,
  full_name  text,
  plan       text not null default 'free',
  created_at timestamptz not null default now()
);

create table cvs (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users on delete cascade,
  label      text,
  raw_text   text not null,
  parsed     jsonb not null,
  file_path  text,                      -- Supabase Storage
  created_at timestamptz not null default now()
);
```

**RLS is enabled on every table.** The backend holds the service key; in v1 the browser never talks to Supabase directly.

⚠️ CV contents are personal data. In demo mode, **the CV text is not persisted** — only generation metadata. The landing page states this explicitly.

---

## 7. Keeping the public demo alive

The Gemini free tier allows 1000 requests/day, and one generation costs 3.
→ **theoretical ceiling ≈ 330 generations/day**, shared across every visitor.

Safeguards, from lightest to strictest:
1. **Hard-coded pre-generated example** on the landing page → zero API calls for a curious visitor
2. **3 generations / IP / day** (Upstash key `demo:{ip_hash}:{YYYY-MM-DD}`)
3. **Global daily ceiling** (`demo:global:{date}`) → past it, the app falls back to the example with an honest message: *demo quota reached, try again tomorrow*
4. **Bounded inputs**: PDF ≤ 4 MB (Vercel caps request bodies at 4.5 MB), posting truncated to 4000 characters (as in the n8n prototype)
5. No automatic client-side retry on `QUOTA_EXCEEDED`

---

## 8. What carries over from n8n

The value of the n8n prototype is **the prompts and the pipeline design**, not the nodes.

| n8n (`F2-Core`) | Protune |
|---|---|
| `HTTP Request` → r.jina.ai | `services/scraper.py` |
| `Extract from File` (PDF) | `services/cv_parser.py` |
| `Offer analyser` (Gemini) | `services/gemini.py::analyse_offer()` |
| `rédaction LM` (Gemini) | `services/gemini.py::write_letter()` |
| `CV writer` (Gemini) | `services/gemini.py::adapt_cv()` |
| `Code parse *` (stripping ```` ```json ````) | no longer needed — see below |
| `Code html` | React rendering on the web side |

**The structural change:** in n8n, the candidate's profile and CV are **hard-coded inside the prompts**. Here they are **inputs**. Each prompt becomes a template in `api/app/prompts/` with variables.

Two improvements on the prototype:

**JSON is now guaranteed, not salvaged.** The prototype asked for JSON in prose and stripped
```` ```json ```` fences off the answer, which broke whenever the model phrased itself
differently. Requests now pin `responseMimeType: application/json` and a `responseSchema`,
so the response parses by construction. The fence-stripping survives only as a fallback,
and a test pins it.

**The output language is decided once.** Both downstream prompts originally said "write in
the language of the posting". Against a French posting that produced a French letter next
to an English CV summary. The analysis now returns a `language` field which is interpolated
into the letter and CV prompts, so the decision is made once instead of re-inferred twice.

Known pitfalls, already paid for once:
- 15 RPM rate limit → exponential backoff over 3 attempts, with 429/500/503 retried and
  everything else failing immediately
- the three calls are sequential (the analysis feeds both the letter and the CV) → this is
  what accounts for the 16–25 s measured end to end

---

## 9. Deployment

Both applications deploy to **Vercel**, as two separate projects pointing at the same
repository. The free Hobby plan requires no credit card.

| Project | Root Directory | Notes |
|---|---|---|
| `protune` (web) | `web` | Next.js preset, detected automatically |
| `protune-api` | `api` | FastAPI and dependencies both read from `pyproject.toml`; entrypoint declared as `tool.vercel.entrypoint` |

> ⚠️ **Root Directory is not optional here.** This is a monorepo: left at the repository
> root, Vercel finds no application, builds nothing, and every request returns
> `404 NOT_FOUND`. Set it per project in *Settings → General → Root Directory*.

Environment variables to set in the dashboard:

| Project | Variable | Value |
|---|---|---|
| web | `NEXT_PUBLIC_API_URL` | the deployed API URL |
| api | `GEMINI_API_KEY` | from Google AI Studio |
| api | `CORS_ORIGINS` | the deployed web URL |

### Deployment gotchas

Three platform behaviours cost time on the first deploy. All three are configuration,
not code.

**1. Root Directory (monorepo).** Left at the repository root, Vercel finds no
application, builds nothing, and every route returns `404 NOT_FOUND`. Set it per project:
`web` for the frontend, `api` for the backend.

**2. Vercel Authentication blocks public access.** New projects ship with Deployment
Protection on. Its *Standard Protection* mode is described as protecting everything
"except production **Custom Domains**" — a `.vercel.app` address is not a custom domain,
so it stays behind a Vercel login wall. A visitor without an account is redirected to
`vercel.com/sso-api`.

On the free plan the only options are to turn *Require Log In* off entirely, or to attach
a real custom domain. For a public portfolio demo, the toggle must be **off**.

Diagnose it without a browser:

```bash
curl -sD - -o /dev/null https://<app>.vercel.app/ | head -3
# 302 + Location: vercel.com/sso-api  -> protected
# 404 + X-Vercel-Error: NOT_FOUND     -> no deployment attached to that domain
# 200                                 -> live
```

**3. Framework Preset must be set explicitly.** With the preset left on *Other*, Vercel
still runs `npm run build`, reports the deployment *Ready*, and then publishes only the
static `public/` directory — the Next.js adapter never runs, so every route returns
`404 NOT_FOUND` while `/window.svg` and the other files in `public/` return `200`. That
asymmetry is the diagnostic: if assets serve but routes do not, the preset is wrong.

**4. An environment variable saved with a blank value is not the same as an unset one.**
A missing variable falls back to its default; a variable present with an empty string
overrides that default and is then parsed against the declared type. A blank
`DEMO_DAILY_LIMIT` therefore failed int parsing at import time and returned 500 on every
route. `Settings` now drops blank values before validation, and `tests/test_config.py`
pins that behaviour.

**5. Vercel installs Python dependencies from `pyproject.toml`, not `requirements.txt`.**
When a `pyproject.toml` with a `[project]` table is present, it becomes the dependency
source. A `[project]` table without a `dependencies` list therefore installs nothing, and
the function crashes at import with `FUNCTION_INVOCATION_FAILED`. Dependencies live in
`pyproject.toml` for that reason — Docker and CI install from the same file, so the lists
cannot drift.

**3. A successful build is not a production deployment.** A production domain that returns
`404 NOT_FOUND` while builds succeed means no deployment was ever promoted to production.
Check *Settings → Git → Production Branch* is `main`, or promote a deployment manually from
the Deployments tab.

### Why Vercel rather than a container host

| Option | Verdict |
|---|---|
| **Vercel Python Functions** | ✅ Chosen. Hobby allows 300 s max duration and 2 GB memory, streaming is enabled by default, and Python 3.12 is the default runtime. Our pipeline needs 20–30 s, so there is ample headroom. |
| Fly.io | ❌ Requires a credit card before any deploy, including for a 256 MB machine. |
| Hugging Face Spaces | ❌ Docker Spaces now require a paid PRO plan; only Static Spaces remain free. |
| Render | 🟡 Free without a card, but free services sleep after 15 minutes and take ~1 minute to wake — unacceptable on a portfolio demo. Kept as a fallback. |

The `Dockerfile` and `fly.toml` stay in the repository. They work locally, they demonstrate
containerisation, and they mean the API can move to any container host without a rewrite.

CI: GitHub Actions — `ruff` + `pytest` for `api/`, `tsc` + `eslint` + `next build` for `web/`.

---

## 10. Milestones

| # | Deliverable | Visible outcome |
|---|---|---|
| ~~1~~ | ~~Skeleton + `/health` + end-to-end deployment~~ ✅ | [protune-eight.vercel.app](https://protune-eight.vercel.app) · [protuneapi.vercel.app](https://protuneapi.vercel.app/docs) |
| ~~2~~ | ~~`cv/parse` — PDF text extraction~~ ✅ | 20 tests, including scans, corrupt files and oversized uploads |
| ~~3~~ | ~~the three Gemini calls ported from n8n~~ ✅ | Full pipeline verified against the live API in 16.4 s |
| ~~4~~ | ~~SSE + full frontend flow~~ ✅ | Driven end to end in a browser: 19.3 s, four stages streamed |
| ~~5~~ | ~~PDF export~~ ✅ | Verified by inflating a generated PDF: accents intact, 1902 characters |
| 6 | Landing + pre-generated example + rate limiting | **The public demo is presentable** |
| 7 | README, demo video, polish | Portfolio-ready |

Milestone 1 deploys **before** any feature exists. That is what prevents discovering infrastructure problems on the last day.

---

## 11. Open decisions

- [ ] Final product name — `Protune` is inherited from the repository, still to be confirmed
- [x] ~~Interface language~~ → **English only**, decided
- [ ] Custom domain, or `protune.vercel.app`?
- [ ] Landing page example: a real public posting, or a fictional one?
