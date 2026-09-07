"""Models for the generation pipeline, and the JSON schemas Gemini must answer with."""

from pydantic import BaseModel, Field


class OfferAnalysis(BaseModel):
    role: str = ""
    company: str = ""
    location: str = ""
    sector: str = ""
    contract_type: str = ""
    # Decided once, then imposed on the letter and the CV: asking each call to
    # re-infer the language produced a French letter next to an English CV.
    language: str = "English"
    key_skills: list[str] = Field(default_factory=list)
    ats_keywords: list[str] = Field(default_factory=list)


class CoverLetter(BaseModel):
    paragraphs: list[str] = Field(default_factory=list)


class CvProject(BaseModel):
    title: str = ""
    description: str = ""


class AdaptedCv(BaseModel):
    headline: str = ""
    summary: str = ""
    projects: list[CvProject] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


# Gemini accepts an OpenAPI subset. Declaring the shape here is what makes the
# response parseable JSON by construction, rather than text to be salvaged.
_STRING = {"type": "string"}
_STRING_LIST = {"type": "array", "items": _STRING}

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "role": _STRING,
        "company": _STRING,
        "location": _STRING,
        "sector": _STRING,
        "contract_type": _STRING,
        "language": _STRING,
        "key_skills": _STRING_LIST,
        "ats_keywords": _STRING_LIST,
    },
    "required": ["role", "company", "language", "key_skills", "ats_keywords"],
}

LETTER_SCHEMA = {
    "type": "object",
    "properties": {"paragraphs": _STRING_LIST},
    "required": ["paragraphs"],
}

ADAPTED_CV_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": _STRING,
        "summary": _STRING,
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"title": _STRING, "description": _STRING},
                "required": ["title", "description"],
            },
        },
        "skills": _STRING_LIST,
    },
    "required": ["headline", "summary", "projects", "skills"],
}
