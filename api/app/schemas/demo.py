"""Response model for the demo quota endpoint."""

from pydantic import BaseModel, Field


class QuotaResponse(BaseModel):
    remaining: int = Field(description="Generations left for this visitor today.")
    limit: int
    resets_at: str = Field(description="ISO timestamp of the next reset, UTC midnight.")
    enforced: bool = Field(
        description="False when no rate limiter is configured, so the numbers are indicative."
    )
