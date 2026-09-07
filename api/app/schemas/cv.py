"""Response models for CV handling."""

from pydantic import BaseModel, Field


class CvParseResponse(BaseModel):
    raw_text: str = Field(description="Text extracted from the PDF, whitespace-normalised.")
    page_count: int = Field(description="Number of pages in the source document.")
    character_count: int = Field(description="Length of raw_text after any truncation.")
    truncated: bool = Field(description="True when the CV exceeded the extraction cap.")
