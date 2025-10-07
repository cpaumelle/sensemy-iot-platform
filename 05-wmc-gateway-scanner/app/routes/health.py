"""
Health Endpoints
Version: 1.1.0
Last Updated: 2025-08-20 22:40 UTC

Changelog:
- Keep /healthz
- Add /health alias used by the frontend JS
"""

from fastapi import APIRouter
router = APIRouter()

def _payload():
    # Extend here with deeper checks (e.g., WMC reachability)
    return {"status": "ok"}

@router.get("/healthz")
async def healthz():
    return _payload()

@router.get("/health")
async def health():
    return _payload()
