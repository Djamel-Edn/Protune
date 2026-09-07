/**
 * A generation captured ahead of time, rendered on the landing page.
 *
 * It costs nothing and appears instantly, so a visitor sees real output before
 * deciding whether to spend a generation — and still sees it once the shared
 * daily quota is spent.
 *
 * The posting is fictional on purpose: publishing generated text under a real
 * company's name would imply an involvement they never agreed to.
 *
 * Regenerate with: api/.venv/Scripts/python scripts/generate_example.py
 */
import type { AdaptedCv, CoverLetter, OfferAnalysis } from "@/lib/api";

export const EXAMPLE: {
  offerTitle: string;
  offerCompany: string;
  analysis: OfferAnalysis;
  letter: CoverLetter;
  cv: AdaptedCv;
} = {
  "offerTitle": "Data Engineer Apprentice",
  "offerCompany": "Northwind Analytics",
  "analysis": {
    "role": "Data Engineer Apprentice",
    "company": "Northwind Analytics",
    "location": "Lyon",
    "sector": "Data Analytics",
    "contract_type": "Apprenticeship",
    "language": "English",
    "key_skills": [
      "Python",
      "SQL",
      "Airflow",
      "Snowflake",
      "Docker",
      "Spark"
    ],
    "ats_keywords": [
      "Data Engineer Apprentice",
      "Python",
      "Airflow",
      "Snowflake",
      "SQL",
      "Docker",
      "Spark"
    ]
  },
  "letter": {
    "paragraphs": [
      "Northwind Analytics is scaling its data infrastructure right here in Lyon, and as a software and data engineering student at INSA Lyon, I want to contribute to that growth as your next Data Engineer Apprentice starting this September 2026.",
      "Building reliable data pipelines and managing efficient data flows requires a strong foundation in core engineering tools, which I apply daily in my academic and personal projects. Working with Python, SQL, and Docker, I focus on writing clean, reproducible code and managing dependencies effectively across different environments.",
      "Beyond foundational tooling, I bring practical experience in handling complex data challenges. In the Kaggle Titanic Challenge, where I placed in the top 15%, I utilized Python, pandas, and scikit-learn for rigorous feature engineering and gradient boosting to optimize predictive performance.",
      "My engineering background also extends to system reliability and collaboration, demonstrated by deploying a Java constraint solver timetable scheduler for 400 university students and contributing three merged pull requests to an open-source Python HTTP library using Git.",
      "I am eager to bring my technical stack, including Python, SQL, and Docker, to the Data Engineer Apprentice role at Northwind Analytics, helping your team build robust analytics systems over a 12-month apprenticeship."
    ]
  },
  "cv": {
    "headline": "Data Engineer Apprentice",
    "summary": "Engineering student at INSA Lyon specialising in software and data, seeking a 12-month apprenticeship from September 2026. Experienced in building robust data pipelines, feature engineering, and deploying scalable software solutions in Python and Java. Bringing strong skills in database querying, containerisation, and workflow management to Northwind Analytics.",
    "projects": [
      {
        "title": "Kaggle Titanic Challenge",
        "description": "Achieved top 15% by implementing advanced feature engineering and gradient boosting pipelines in Python, demonstrating strong data manipulation and processing capabilities."
      },
      {
        "title": "University timetable scheduler",
        "description": "Developed a constraint solver in Java and deployed the data-driven application for 400 students, focusing on reliable architecture and execution."
      },
      {
        "title": "Open-source contributor",
        "description": "Successfully delivered three merged pull requests to a Python HTTP library, showcasing collaborative software engineering and code quality practices."
      }
    ],
    "skills": [
      "Python",
      "SQL",
      "Docker",
      "Git",
      "Java",
      "pandas",
      "scikit-learn",
      "REST APIs"
    ]
  }
} as const;
