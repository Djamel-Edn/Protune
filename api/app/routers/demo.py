"""What the public demo will allow this visitor today."""

from fastapi import APIRouter, Request

from app.config import SettingsDep
from app.schemas.demo import QuotaResponse
from app.services.rate_limit import client_ip, peek

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/quota", response_model=QuotaResponse)
async def quota(request: Request, settings: SettingsDep) -> QuotaResponse:
    result = await peek(client_ip(dict(request.headers)), settings)
    return QuotaResponse(**result.__dict__)
