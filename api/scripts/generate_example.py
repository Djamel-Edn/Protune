"""Regenerates the example rendered on the landing page.

Run from the api/ directory, with GEMINI_API_KEY set:

    .venv/Scripts/python scripts/generate_example.py

Costs three Gemini calls and overwrites web/src/lib/example.ts.
The posting below is fictional on purpose — see that file's header.
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, ".")
from app.config import get_settings
from app.services.gemini import GeminiClient

CV = """Alex Moreau - Lyon, France
Engineering student, INSA Lyon, specialising in software and data.
Seeking a 12-month apprenticeship from September 2026.

PROJECTS
Kaggle Titanic Challenge - top 15%. Feature engineering and gradient boosting in Python.
University timetable scheduler - constraint solver in Java, deployed for 400 students.
Open-source contributor - three merged pull requests to a Python HTTP library.

SKILLS
Python, Java, SQL, Git, Docker, pandas, scikit-learn, REST APIs.

LANGUAGES
French native. English C1. Spanish B1."""

OFFER = """Data Engineer Apprentice (12 months) - Northwind Analytics, Lyon
Northwind Analytics builds forecasting tools for mid-sized retailers across Europe.
You will join the Data Platform team for a 12-month apprenticeship starting September 2026.
What you will do: build and maintain ingestion pipelines in Python and Airflow, model data
in our Snowflake warehouse, add data-quality checks, and document the flows you own.
What we look for: an engineering student specialising in data or software. Python and SQL
are essential. Familiarity with Docker, Spark or Airflow is a plus. Working English required."""


async def main():
    c = GeminiClient(get_settings())
    analysis = await c.analyse_offer(OFFER)
    letter = await c.write_letter(CV, analysis)
    cv = await c.adapt_cv(CV, analysis)
    payload = {
        "offerTitle": "Data Engineer Apprentice",
        "offerCompany": "Northwind Analytics",
        "analysis": analysis.model_dump(),
        "letter": letter.model_dump(),
        "cv": cv.model_dump(),
    }
    out = pathlib.Path("../web/src/lib/example.ts")
    out.write_text(
        "/**\n"
        " * A generation captured ahead of time, rendered on the landing page.\n"
        " *\n"
        " * It costs nothing and appears instantly, so a visitor sees real output before\n"
        " * deciding whether to spend a generation — and still sees it once the shared\n"
        " * daily quota is spent.\n"
        " *\n"
        " * The posting is fictional on purpose: publishing generated text under a real\n"
        " * company's name would imply an involvement they never agreed to.\n"
        " *\n"
        " * Regenerate with: api/.venv/Scripts/python scripts/generate_example.py\n"
        " */\n"
        'import type { AdaptedCv, CoverLetter, OfferAnalysis } from "@/lib/api";\n\n'
        "export const EXAMPLE: {\n"
        "  offerTitle: string;\n"
        "  offerCompany: string;\n"
        "  analysis: OfferAnalysis;\n"
        "  letter: CoverLetter;\n"
        "  cv: AdaptedCv;\n"
        "} = " + json.dumps(payload, indent=2, ensure_ascii=False) + " as const;\n",
        encoding="utf-8",
    )
    print("ecrit ->", out.resolve())
    print("titre  :", cv.headline)
    print("langue :", analysis.language)
    print("paras  :", len(letter.paragraphs), "| projets:", len(cv.projects))


asyncio.run(main())
