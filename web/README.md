# Protune — Web

Next.js 16 frontend (App Router, TypeScript, Tailwind 4).

```bash
npm install
npm run dev
```

Runs on `http://localhost:3000`. Set `NEXT_PUBLIC_API_URL` in `.env.local` to point at
the API (defaults to `http://localhost:8000`).

| Path | Purpose |
|---|---|
| `src/lib/brand.ts` | Product naming and copy — the only place to change to rename the product |
| `src/lib/api.ts` | Typed client for the Protune API |
| `src/components/` | Shared UI components |

## Deployment

Deployed to Vercel with **Root Directory** set to `web`. Required environment variable:
`NEXT_PUBLIC_API_URL` pointing at the deployed API.
