<div align="center">

# Protune

**Colle une offre d'emploi. Récupère ton CV adapté et ta lettre de motivation.**

Analyse d'offre, réécriture de CV et rédaction de lettre par IA — sans inscription.

`Next.js` · `FastAPI` · `Gemini` · `Supabase`

🚧 **En construction** — voir la [roadmap](#roadmap). Démo publique au jalon 6.

</div>

---

## Le problème

Adapter son CV à chaque offre, c'est ce qui fait la différence sur un ATS — et c'est exactement ce que personne ne fait, parce que ça prend 40 minutes par candidature.

Protune ramène ça à 30 secondes : une offre en entrée, un CV reciblé et une lettre personnalisée en sortie.

## Comment ça marche

```
Offre (URL ou texte)          CV (PDF)
        │                        │
        └────────┬───────────────┘
                 ▼
        ┌────────────────────┐
        │  Analyse de l'offre │  poste, entreprise, compétences clés, mots-clés ATS
        └────────┬───────────┘
                 ▼
        ┌────────────────────┐
        │  Lettre de motiv.  │  rédigée dans ton style, ancrée sur l'entreprise
        └────────┬───────────┘
                 ▼
        ┌────────────────────┐
        │  CV adapté         │  titre, accroche et projets reciblés
        └────────┬───────────┘
                 ▼
              Export PDF
```

## Architecture

Le produit sépare deux chemins, volontairement :

| | |
|---|---|
| **Chemin produit** — l'utilisateur attend le résultat à l'écran | Next.js + FastAPI |
| **Chemin ops** — déclenché par le temps ou un webhook, personne n'attend | n8n |

Les digests d'offres, les relances de candidature et les notifications restent dans n8n. Le chemin critique est du code : testable, versionnable, multi-utilisateurs.

> **Ce projet a d'abord été prototypé entièrement dans n8n.** Le pipeline (scraping → analyse → lettre → CV) y a été validé en quelques jours, prompts compris. Cette version en est le portage : les prompts sont repris tels quels, mais le profil du candidat — codé en dur dans le prototype — devient une entrée, ce qui rend le produit multi-utilisateurs.

## Stack

| Couche | Choix |
|---|---|
| Front | Next.js 15 (App Router, TypeScript, Tailwind) — Vercel |
| API | FastAPI, Python 3.12 — Fly.io (Docker) |
| LLM | Google Gemini (`gemini-flash-lite-latest`) |
| Données | Supabase (Postgres + Storage) |
| Quotas | Upstash Redis |

Détail des choix et des arbitrages : [`docs/PLAN.md`](docs/PLAN.md).

## Développement local

**Prérequis :** Node 20+, Python 3.12, une clé [Google AI Studio](https://aistudio.google.com/apikey) (gratuite).

```bash
git clone https://github.com/Djamel-Edn/Protune.git
cd Protune
cp .env.example .env   # puis remplir GEMINI_API_KEY
```

```bash
# API
cd api && py -3.12 -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
# Web
cd web && npm install && npm run dev
```

L'app tourne sur `http://localhost:3000`, l'API sur `http://localhost:8000` (docs auto : `/docs`).

## Roadmap

- [ ] **1** — Squelette + `/health` + déploiement de bout en bout
- [ ] **2** — Parsing de CV (PDF → JSON structuré)
- [ ] **3** — Pipeline Gemini : analyse → lettre → CV
- [ ] **4** — Streaming SSE + parcours front complet
- [ ] **5** — Export PDF
- [ ] **6** — Landing + démo publique rate-limitée
- [ ] **7** — Polish, README final, capture vidéo
- [ ] *Plus tard* — comptes, tracker de candidatures, recherche d'offres avec scoring

## Vie privée

En mode démo, **le contenu des CV n'est pas conservé** : seules les métadonnées de génération (durée, modèle, horodatage) sont enregistrées. Les adresses IP ne sont jamais stockées en clair, uniquement hachées, pour appliquer les quotas.

## Licence

MIT — voir [LICENSE](LICENSE).
