"""
Gateway API Routes
Version: 1.0.1
Updated: 2025-08-20 17:35:00 UTC

REST API endpoints for gateway operations with proper dependency injection
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

gateway_router = APIRouter(prefix="/gateways")

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

@gateway_router.get("/lookup/{gateway_eui}")
async def lookup_gateway(
    gateway_eui: str,
    include_stats: bool = False,
    wmc = Depends(get_wmc_service)
) -> Dict[str, Any]:
    """
    Lookup gateway by EUI from WMC API
    
    Args:
        gateway_eui: Gateway EUI (from QR code)
        include_stats: Include performance statistics
        
    Returns:
        Gateway information and status
    """
    try:
        # Validate EUI format (basic validation)
        if not gateway_eui or len(gateway_eui) < 8:
            raise HTTPException(
                status_code=400, 
                detail="Invalid gateway EUI format"
            )
        
        # Clean up EUI (remove spaces, colons, etc.)
        clean_eui = gateway_eui.replace(":", "").replace("-", "").replace(" ", "").upper()
        
        logger.info(f"🔍 Gateway lookup request: {clean_eui}")
        
        # Get gateway information from WMC
        gateway_info = await wmc.get_gateway_by_eui(clean_eui)
        
        if not gateway_info:
            raise HTTPException(
                status_code=404,
                detail=f"Gateway not found: {clean_eui}"
            )
        
        # Get additional statistics if requested
        if include_stats and gateway_info.get("id"):
            stats = await wmc.get_gateway_statistics(gateway_info["id"])
            if stats:
                gateway_info["statistics"] = stats
        
        # Format response
        response = {
            "gateway": gateway_info,
            "lookup_success": True,
            "source": "wmc_api",
            "requested_eui": gateway_eui,
            "clean_eui": clean_eui
        }
        
        logger.info(f"✅ Gateway lookup successful: {gateway_info.get('name', clean_eui)}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Gateway lookup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error during gateway lookup: {str(e)}"
        )

@gateway_router.get("/validate-eui/{gateway_eui}")
async def validate_gateway_eui(gateway_eui: str) -> Dict[str, Any]:
    """
    Validate gateway EUI format without WMC lookup
    
    Args:
        gateway_eui: Gateway EUI to validate
        
    Returns:
        Validation result and formatted EUI
    """
    try:
        # Clean up EUI
        clean_eui = gateway_eui.replace(":", "").replace("-", "").replace(" ", "").upper()
        
        # Basic validation
        is_valid = (
            len(clean_eui) >= 8 and
            len(clean_eui) <= 16 and
            all(c in "0123456789ABCDEF" for c in clean_eui)
        )
        
        # Format for display
        formatted_eui = ":".join([clean_eui[i:i+2] for i in range(0, len(clean_eui), 2)])
        
        return {
            "original_eui": gateway_eui,
            "clean_eui": clean_eui,
            "formatted_eui": formatted_eui,
            "is_valid": is_valid,
            "length": len(clean_eui)
        }
        
    except Exception as e:
        logger.error(f"❌ EUI validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"EUI validation failed: {str(e)}"
        )

@gateway_router.post("/batch-lookup")
async def batch_gateway_lookup(
    gateway_euis: list[str],
    wmc = Depends(get_wmc_service)
) -> Dict[str, Any]:
    """
    Lookup multiple gateways (useful for bulk operations)
    
    Args:
        gateway_euis: List of gateway EUIs
        
    Returns:
        Results for each gateway lookup
    """
    if len(gateway_euis) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 gateways per batch request"
        )
    
    results = []
    
    for eui in gateway_euis:
        try:
            clean_eui = eui.replace(":", "").replace("-", "").replace(" ", "").upper()
            gateway_info = await wmc.get_gateway_by_eui(clean_eui)
            
            results.append({
                "eui": eui,
                "success": gateway_info is not None,
                "gateway": gateway_info
            })
            
        except Exception as e:
            results.append({
                "eui": eui,
                "success": False,
                "error": str(e)
            })
    
    return {
        "batch_results": results,
        "total_requested": len(gateway_euis),
        "successful_lookups": sum(1 for r in results if r["success"])
    }
