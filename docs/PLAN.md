# Protune — Plan produit & technique

> Document de référence. Toute décision d'architecture se prend ici avant d'écrire du code.
> **Statut :** v1 en cours de construction · **Dernière mise à jour :** 7 septembre 2026

---

## 1. Le produit

**Protune adapte ton CV et rédige ta lettre de motivation à partir d'une offre d'emploi.**

Tu colles une offre (URL ou texte), tu fournis ton CV une fois, et tu récupères :
- une **analyse de l'offre** : poste, entreprise, compétences clés, mots-clés ATS
- un **CV adapté** : titre, accroche et projets réécrits pour matcher l'offre
- une **lettre de motivation** personnalisée, dans ton style
- le tout **exportable en PDF**

### Périmètre v1 (ce qu'on livre)
| | |
|---|---|
| ✅ | Upload CV (PDF) → parsing en données structurées |
| ✅ | Offre par URL (scraping) **ou** texte collé |
| ✅ | Analyse + LM + CV adapté par Gemini, en streaming |
| ✅ | Export PDF du CV et de la lettre |
| ✅ | Démo publique sans inscription |

### Hors périmètre v1 (roadmap visible dans le README)
| | |
|---|---|
| ⏭️ | Recherche d'offres + scoring (le F1 n8n) — dépend d'Adzuna, 1000 req/mois, tient mal une démo publique |
| ⏭️ | Tracker de candidatures + dashboard (le F3 n8n) — nécessite l'auth multi-utilisateurs |
| ⏭️ | Comptes, plans payants, Stripe |

### Hypothèses prises par défaut
1. **Démo publique, sans inscription**, rate-limitée par IP (3 générations/jour). Un recruteur ne crée pas de compte pour tester.
2. **v1 = générateur CV + LM.** Le tracker et la recherche viennent après.
3. **Nom `Protune`** — repris du repo. Centralisé dans `web/lib/brand.ts`, renommable en une ligne.

---

## 2. Architecture

```
                        ┌──────────────────────────────┐
   Navigateur ────────► │   Next.js (Vercel)           │
                        │   landing · app · export PDF │
                        └───────────────┬──────────────┘
                                        │ HTTPS / SSE
                                        ▼
                        ┌──────────────────────────────┐
                        │   FastAPI (Fly.io, Docker)   │
                        │   parse CV · scrape · Gemini │
                        └───┬──────────┬───────────┬───┘
                            │          │           │
                  ┌─────────▼──┐  ┌────▼─────┐  ┌──▼──────────┐
                  │  Gemini    │  │ Supabase │  │  Upstash    │
                  │  API       │  │ PG+Storage│ │  (quotas)   │
                  └────────────┘  └──────────┘  └─────────────┘

  ─────────────────── chemin produit (code) ───────────────────
  ─────────────────── chemin ops (n8n, hors ligne) ────────────

                        ┌──────────────────────────────┐
                        │   n8n (self-hosted)          │
                        │   digest quotidien · relances│
                        │   notifs Discord · reporting │
                        └──────────────────────────────┘
```

**La règle :** ce que l'utilisateur attend à l'écran est du code. Ce qui est déclenché par le temps ou un webhook, sans personne devant l'écran, est dans n8n.

---

## 3. Stack

| Couche | Choix | Pourquoi |
|---|---|---|
| Front | **Next.js 15** (App Router, TypeScript, Tailwind) | Prouve une compétence revendiquée sans preuve ; déploiement Vercel gratuit et instantané |
| Backend | **FastAPI** (Python 3.12) | Standard pour servir de l'IA en Python ; parle au profil IA & Big Data |
| LLM | **Gemini** `gemini-flash-lite-latest` | Free tier 15 RPM / 1000 RPD ; prompts déjà validés en n8n |
| Scraping offre | **r.jina.ai** | Gratuit, sans clé, gère le JS ; déjà éprouvé en n8n |
| Parsing PDF | **pypdf** (+ fallback `pdfplumber`) | Suffisant pour du CV texte |
| Base | **Supabase** (Postgres + Storage) | Déjà en place sur le projet n8n ; Auth prête pour la phase 2 |
| Quotas démo | **Upstash Redis** | Compteur par IP hachée, free tier, API REST (pas de connexion persistante) |
| Export PDF | **@react-pdf/renderer** (client) | Pas de navigateur headless à héberger ; rendu déterministe |
| Hébergement | **Vercel** (web) + **Fly.io** (api, Docker) | Voir §9 |

> ⚠️ **Python 3.12, pas 3.14.** L'écosystème (pypdf, weasyprint, certains wheels) est encore en retard sur 3.14, qui est le Python par défaut de la machine. Le venv sera créé explicitement avec `py -3.12`.

---

## 4. Parcours utilisateur

### Écran 1 — Landing `/`
Hero + **un exemple déjà généré affiché immédiatement** (offre réelle → CV + LM). Coût zéro, aucune latence : même si le quota Gemini est épuisé, le visiteur voit le résultat. CTA « Essayer avec mon CV ».

### Écran 2 — App `/app`
Trois étapes sur une page :
1. **Ton CV** — upload PDF, ou bouton « utiliser un CV d'exemple » (pour tester sans donner ses données)
2. **L'offre** — URL, ou zone de texte
3. **Générer** — progression en streaming :
   `Lecture de l'offre… → Analyse… → Rédaction de la lettre… → Adaptation du CV…`

Le streaming n'est pas cosmétique : la génération prend 20-30 s, et une barre morte pendant 30 s fait fermer l'onglet.

### Écran 3 — Résultat
Onglets **Lettre** / **CV adapté**, avec un **diff avant/après** sur le CV (c'est la démonstration la plus parlante du produit). Bouton export PDF sur chaque.

---

## 5. Contrat d'API

Base : `/api/v1`

| Méthode | Route | Entrée | Sortie |
|---|---|---|---|
| `GET` | `/health` | — | `{status, version}` |
| `GET` | `/demo/quota` | — | `{remaining, limit, resets_at}` |
| `POST` | `/cv/parse` | `multipart` (PDF ≤ 5 Mo) | `{raw_text, parsed: {titre, profil, experiences[], projets[], competences[], formations[]}}` |
| `POST` | `/generate` | `{cv, offer_url?, offer_text?}` | **SSE** |

### Événements SSE de `/generate`
```
event: step     data: {"step":"scrape","status":"done"}
event: analysis data: {"poste":"…","entreprise":"…","competences_cles":[…],"mots_cles_ats":[…]}
event: letter   data: {"paragraphes":["…","…"]}
event: cv       data: {"nouveau_titre":"…","nouveau_profil":"…","projets":[…]}
event: done     data: {"duration_ms":24310,"model":"…"}
event: error    data: {"code":"RATE_LIMITED","message":"…"}
```

Codes d'erreur : `RATE_LIMITED`, `QUOTA_EXCEEDED` (Gemini), `SCRAPE_FAILED`, `PARSE_FAILED`, `INVALID_PDF`.

---

## 6. Schéma de base

```sql
-- v1 : anonyme, on ne stocke que ce qui sert aux stats et à l'anti-abus
create table generations (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users on delete cascade,  -- null en démo
  ip_hash       text not null,          -- sha256(ip + IP_HASH_SALT), jamais l'IP en clair
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

**RLS activée sur toutes les tables.** Le backend utilise la service key ; le navigateur ne parle jamais directement à Supabase en v1.

⚠️ Le contenu des CV est une donnée personnelle. En v1 démo : **on ne persiste pas le texte du CV**, seulement les métadonnées de génération. Une ligne le dit explicitement sur la landing.

---

## 7. Démo publique : tenir sans se faire vider le quota

Le free tier Gemini est de 1000 requêtes/jour, et une génération en consomme 3.
→ **plafond théorique ≈ 330 générations/jour**, partagé entre tous les visiteurs.

Garde-fous, du moins au plus contraignant :
1. **Exemple pré-généré en dur** sur la landing → 0 appel pour le visiteur curieux
2. **3 générations / IP / jour** (Upstash, clé `demo:{ip_hash}:{YYYY-MM-DD}`)
3. **Plafond global journalier** (`demo:global:{date}`) → au-delà, l'app bascule sur l'exemple avec un message honnête : « quota de démo atteint, revenez demain »
4. **Taille d'entrée bornée** : PDF ≤ 5 Mo, offre tronquée à 4000 caractères (déjà le cas en n8n)
5. Pas de retry automatique côté client sur `QUOTA_EXCEEDED`

---

## 8. Ce qu'on porte depuis n8n

La valeur du prototype n8n, ce sont **les prompts et le design du pipeline**, pas les nodes.

| n8n (`F2-Core`) | Protune |
|---|---|
| `HTTP Request` → r.jina.ai | `services/scraper.py` |
| `Extract from File` (PDF) | `services/cv_parser.py` |
| `Offer analyser` (Gemini) | `services/gemini.py::analyse_offer()` |
| `rédaction LM` (Gemini) | `services/gemini.py::write_letter()` |
| `CV writer` (Gemini) | `services/gemini.py::adapt_cv()` |
| `Code parse *` (strip des ```` ```json ````) | `services/gemini.py::_parse_json()` — mutualisé |
| `Code html` | rendu React côté web |

**Changement de fond :** dans n8n, le profil de Djamel et son CV sont **écrits en dur dans les prompts**. Ici, ce sont des **entrées**. Chaque prompt devient un template dans `api/app/prompts/` avec des variables.

Pièges déjà connus (à ne pas redécouvrir) :
- Gemini emballe son JSON dans des ```` ```json ```` → strip systématique avant `json.loads`
- rate limit 15 RPM → backoff exponentiel
- les 3 appels sont séquentiels (l'analyse alimente la LM et le CV) → c'est ce qui fait les 20-30 s

---

## 9. Déploiement

| | Cible | Note |
|---|---|---|
| `web/` | **Vercel** | Build instantané, pas de cold start |
| `api/` | **Fly.io** (Docker, scale-to-zero) | Réveil ~1-3 s, acceptable ; le front affiche l'exemple pendant ce temps |

> Les free tiers (Vercel Hobby, Fly.io, Upstash, Supabase) **changent souvent**. Je vérifierai les limites réelles au moment du déploiement plutôt que de m'appuyer sur ce document — considère ce tableau comme une intention, pas comme une garantie.

Alternative si Fly.io ne convient pas : **Hugging Face Spaces** (Docker, gratuit, et bon signal pour un profil IA), ou **Koyeb**.

CI : GitHub Actions — `ruff` + `pytest` sur `api/`, `tsc` + `eslint` + `next build` sur `web/`.

---

## 10. Jalons

| # | Livrable | Sortie visible |
|---|---|---|
| 1 | Squelette + `/health` + **déploiement de bout en bout** | Deux URLs en ligne, vides mais réelles |
| 2 | `cv/parse` — PDF → JSON structuré | Test unitaire sur un vrai CV |
| 3 | `generate` — les 3 appels Gemini portés depuis n8n | Un JSON complet en ligne de commande |
| 4 | SSE + parcours front complet | Le produit marche en local |
| 5 | Export PDF (CV + lettre) | Le livrable est téléchargeable |
| 6 | Landing + exemple pré-généré + rate limit | **La démo publique est présentable** |
| 7 | README, capture vidéo, polish | Prêt pour le portfolio |

Le jalon 1 déploie **avant** d'avoir des fonctionnalités : c'est ce qui évite de découvrir les problèmes d'infra le dernier jour.

---

## 11. Décisions ouvertes

- [ ] Nom définitif — `Protune` est repris du repo, à valider
- [ ] Domaine personnalisé, ou `protune.vercel.app` ?
- [ ] Langue de l'interface : FR, EN, ou les deux ? (EN élargit l'audience Upwork, FR colle aux recruteurs alternance)
- [ ] L'exemple de la landing : une vraie offre publique, ou une offre fictive ?
