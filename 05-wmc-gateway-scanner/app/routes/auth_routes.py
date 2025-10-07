"""
Authentication API Routes
Version: 1.0.1
Updated: 2025-08-20 17:35:00 UTC

WMC authentication management endpoints with proper dependency injection
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

auth_router = APIRouter()

# This will be properly injected from main.py
wmc_service_instance = None

def set_wmc_service(service):
    """Set the WMC service instance for dependency injection"""
    global wmc_service_instance
    wmc_service_instance = service

async def get_wmc_service():
    """Dependency to get WMC service"""
    if wmc_service_instance is None:
        raise HTTPException(status_code=503, detail="WMC service not available")
    return wmc_service_instance

@auth_router.post("/auth/test-connection")
async def test_wmc_connection(wmc = Depends(get_wmc_service)) -> Dict[str, Any]:
    """Test WMC API connectivity"""
    try:
        connected = await wmc.test_connection()
        
        return {
            "connected": connected,
            "base_url": wmc.config.base_url,
            "message": "✅ WMC API accessible" if connected else "❌ WMC API not accessible"
        }
        
    except Exception as e:
        logger.error(f"❌ Connection test error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Connection test failed: {str(e)}"
        )

@auth_router.post("/auth/login")
async def login_to_wmc(wmc = Depends(get_wmc_service)) -> Dict[str, Any]:
    """Force re-authentication with WMC API"""
    try:
        success = await wmc.authenticate()
        
        if success:
            return {
                "authenticated": True,
                "message": "✅ WMC authentication successful",
                "expires_at": wmc.auth_token.expires_at.isoformat() if wmc.auth_token else None
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="❌ WMC authentication failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )

@auth_router.get("/auth/status")
async def get_auth_status(wmc = Depends(get_wmc_service)) -> Dict[str, Any]:
    """Get current authentication status"""
    try:
        status = await wmc.get_connection_status()
        
        return {
            "wmc_connection": status,
            "token_valid": wmc.auth_token is not None and not wmc.auth_token.is_expired if wmc.auth_token else False,
            "credentials_configured": bool(wmc.config.username and wmc.config.password)
        }
        
    except Exception as e:
        logger.error(f"❌ Auth status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get auth status: {str(e)}"
        )
