import platform
"""
OAuth2 Web Flow Routes - Enhanced with Invisible Login
Version: 2.0.0
Updated: 2025-08-20 18:40:00 UTC

Changelog:
- Added invisible OAuth2 login endpoint
- Added mobile device detection
- Added QR code support for mobile users
- Enhanced error handling and user feedback
- Added token status and management endpoints

Web-based OAuth2 authentication flow for WMC Gateway Scanner
Handles login redirect, callback, and token management
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
from typing import Dict, Any, Optional
import json
import asyncio

logger = logging.getLogger(__name__)

oauth2_router = APIRouter()

# This will be set from main.py
wmc_service_instance = None
templates = None

def set_dependencies(service, template_instance):
    """Set service and template dependencies"""
    global wmc_service_instance, templates
    wmc_service_instance = service
    templates = template_instance

class InvisibleLoginRequest(BaseModel):
    """Request model for invisible login"""
    auto_browser: bool = True
    show_qr: bool = True
    timeout: int = 300
    mobile_mode: bool = False

@oauth2_router.post("/auth/invisible-login")
async def invisible_login(request: InvisibleLoginRequest):
    """
    Completely invisible OAuth2 login flow
    
    This endpoint initiates an invisible OAuth2 flow that:
    - Auto-opens browser on desktop
    - Shows QR code on mobile
    - Handles token exchange automatically
    - Returns authentication status
    """
    try:
        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        logger.info("🚀 Starting invisible OAuth2 login...")

        # Check if we already have a valid token
        if hasattr(wmc_service_instance, 'oauth2_service'):
            oauth2_service = wmc_service_instance.oauth2_service
        else:
            # Import and initialize OAuth2 service if not available
            from app.services.wmc_oauth2_service import WMCOAuth2Service
            oauth2_service = WMCOAuth2Service()
            wmc_service_instance.oauth2_service = oauth2_service

        # Check existing token
        auth_status = oauth2_service.get_auth_status()
        if auth_status["authenticated"] and auth_status["token_valid"]:
            logger.info("✅ Already authenticated with valid token")
            return {
                "success": True,
                "message": "Already authenticated",
                "auth_status": auth_status,
                "skipped_login": True
            }

        # Perform invisible login
        token = await oauth2_service.invisible_login(
            auto_browser=request.auto_browser and not request.mobile_mode,
            show_qr=request.show_qr,
            timeout=request.timeout
        )

        # Update main service token reference
        wmc_service_instance.auth_token = token
        wmc_service_instance.token = token

        # Get updated auth status
        auth_status = oauth2_service.get_auth_status()
        
        # Get user info to confirm authentication
        try:
            user_info = await oauth2_service.get_user_info()
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch user info: {e}")
            user_info = None

        logger.info("✅ Invisible OAuth2 login completed successfully")

        return {
            "success": True,
            "message": "✅ Authentication successful",
            "auth_status": auth_status,
            "user_info": user_info,
            "token_expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "has_refresh_token": token.refresh_token is not None
        }

    except asyncio.TimeoutError:
        logger.error("❌ Authentication timeout")
        raise HTTPException(
            status_code=408,
            detail="Authentication timeout - user did not complete login within the specified time"
        )
    except Exception as e:
        logger.error(f"❌ Invisible login error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Invisible login failed: {str(e)}"
        )

@oauth2_router.get("/auth/qr-code")
async def get_qr_code(format: str = "ascii"):
    """
    Generate QR code for mobile OAuth2 login
    
    Args:
        format: "ascii" for terminal display or "base64" for image data
    """
    try:
        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        # Get OAuth2 service
        if hasattr(wmc_service_instance, 'oauth2_service'):
            oauth2_service = wmc_service_instance.oauth2_service
        else:
            from app.services.wmc_oauth2_service import WMCOAuth2Service
            oauth2_service = WMCOAuth2Service()
            wmc_service_instance.oauth2_service = oauth2_service

        # Generate authorization URL
        auth_url, state, code_verifier = oauth2_service.get_authorization_url()
        
        # Generate QR code
        qr_code = oauth2_service.generate_qr_code(auth_url, format)

        return {
            "success": True,
            "qr_code": qr_code,
            "format": format,
            "auth_url": auth_url,
            "state": state,
            "message": "QR code generated successfully"
        }

    except Exception as e:
        logger.error(f"❌ QR code generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"QR code generation failed: {str(e)}"
        )

@oauth2_router.get("/auth/login")
async def oauth2_login():
    """Initiate OAuth2 login flow (legacy endpoint)"""
    try:
        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        # Get OAuth2 service
        if hasattr(wmc_service_instance, 'oauth2_service'):
            oauth2_service = wmc_service_instance.oauth2_service
        else:
            from app.services.wmc_oauth2_service import WMCOAuth2Service
            oauth2_service = WMCOAuth2Service()
            wmc_service_instance.oauth2_service = oauth2_service

        # Generate OAuth2 authorization URL
        auth_url, state, code_verifier = oauth2_service.get_authorization_url()

        logger.info(f"🔗 Generated OAuth2 login URL")

        # Store code_verifier and state in a simple way (in production, use secure session)
        # For now, return them to the client to handle
        return {
            "authorization_url": auth_url,
            "state": state,
            "code_verifier": code_verifier,
            "message": "Redirect to authorization_url to complete login",
            "suggestion": "Use /auth/invisible-login for automatic authentication"
        }

    except Exception as e:
        logger.error(f"❌ OAuth2 login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login initiation failed: {str(e)}")

@oauth2_router.get("/auth/callback")
async def oauth2_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None
):
    """Handle OAuth2 callback from WMC"""
    if error:
        logger.error(f"❌ OAuth2 callback error: {error}")
        return HTMLResponse(content=f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
        <h1 style="color: red;">❌ Authentication Error</h1>
        <p>Error: {error}</p>
        <p>You can close this window and try again.</p>
        <script>
            setTimeout(function() {{
                window.close();
            }}, 5000);
        </script>
        </body></html>
        """, status_code=400)

    if not code:
        logger.error("❌ No authorization code in callback")
        return HTMLResponse(content="""
        <html><body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
        <h1 style="color: red;">❌ Authentication Error</h1>
        <p>No authorization code received</p>
        <p>You can close this window and try again.</p>
        <script>
            setTimeout(function() {
                window.close();
            }, 5000);
        </script>
        </body></html>
        """, status_code=400)

    try:
        # Note: In a real implementation, we'd retrieve code_verifier from secure session
        # For this demo, we'll need to handle this differently

        return HTMLResponse(content=f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
        <h1 style="color: green;">🔄 Processing Authentication...</h1>
        <p>Authorization code received successfully!</p>
        <p><small>Code: {code[:20]}...</small></p>
        <p><small>State: {state}</small></p>

        <div style="margin: 20px 0;">
            <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>

        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>

        <script>
        // Pass the code back to the main application
        if (window.opener) {{
            window.opener.postMessage({{
                type: 'oauth2_callback',
                code: '{code}',
                state: '{state}'
            }}, '*');
            setTimeout(function() {{
                window.close();
            }}, 2000);
        }} else {{
            // Fallback: redirect to main app with code
            setTimeout(function() {{
                window.location.href = '/?code={code}&state={state}';
            }}, 3000);
        }}
        </script>

        <p>Window will close automatically...</p>
        <p>If not, <a href="/?code={code}&state={state}">click here</a></p>
        </body></html>
        """)

    except Exception as e:
        logger.error(f"❌ OAuth2 callback processing error: {e}")
        return HTMLResponse(content=f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
        <h1 style="color: red;">❌ Authentication Processing Error</h1>
        <p>Error: {str(e)}</p>
        <p>You can close this window and try again.</p>
        <script>
            setTimeout(function() {{
                window.close();
            }}, 5000);
        </script>
        </body></html>
        """, status_code=500)

@oauth2_router.post("/auth/exchange-token")
async def exchange_token(request: Request):
    """Exchange authorization code for access token"""
    try:
        body = await request.json()
        authorization_code = body.get("code")
        code_verifier = body.get("code_verifier")

        if not authorization_code or not code_verifier:
            raise HTTPException(status_code=400, detail="Missing code or code_verifier")

        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        # Get OAuth2 service
        if hasattr(wmc_service_instance, 'oauth2_service'):
            oauth2_service = wmc_service_instance.oauth2_service
        else:
            from app.services.wmc_oauth2_service import WMCOAuth2Service
            oauth2_service = WMCOAuth2Service()
            wmc_service_instance.oauth2_service = oauth2_service

        # Exchange code for token
        token = await oauth2_service.exchange_code_for_token(
            authorization_code,
            code_verifier
        )

        # Update main service token reference
        wmc_service_instance.auth_token = token
        wmc_service_instance.token = token

        logger.info("✅ OAuth2 token exchange successful")

        return {
            "success": True,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "has_refresh_token": token.refresh_token is not None,
            "scope": token.scope,
            "message": "Authentication successful"
        }

    except Exception as e:
        logger.error(f"❌ Token exchange error: {e}")
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

@oauth2_router.get("/auth/status")
async def get_auth_status():
    """Get current authentication status"""
    try:
        if not wmc_service_instance:
            return {"authenticated": False, "service_ready": False}

        # Get OAuth2 service
        if hasattr(wmc_service_instance, 'oauth2_service'):
            oauth2_service = wmc_service_instance.oauth2_service
            oauth2_status = oauth2_service.get_auth_status()
        else:
            oauth2_status = {
                "authenticated": False,
                "token_valid": False,
                "oauth2_service_available": False
            }

        # Get connection status from main service
        try:
            connection_status = await wmc_service_instance.get_connection_status()
        except Exception:
            connection_status = {"connected": False}

        return {
            "service_ready": True,
            "oauth2_available": hasattr(wmc_service_instance, 'oauth2_service'),
            "authenticated": oauth2_status.get("authenticated", False),
            "token_valid": oauth2_status.get("token_valid", False),
            "connection_ok": connection_status.get("connected", False),
            "expires_at": oauth2_status.get("expires_at"),
            "has_refresh_token": oauth2_status.get("has_refresh_token", False),
            "has_stored_token": oauth2_status.get("has_stored_token", False),
            "auth_method": oauth2_status.get("auth_method", "oauth2"),
            "full_oauth2_status": oauth2_status,
            "full_connection_status": connection_status
        }

    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return {
            "service_ready": True,
            "authenticated": False,
            "error": str(e)
        }

@oauth2_router.get("/auth/status-detailed")
async def get_detailed_auth_status():
    """Get detailed authentication status (legacy endpoint)"""
    return await get_auth_status()

@oauth2_router.post("/auth/logout")
async def oauth2_logout():
    """Logout and clear tokens"""
    try:
        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        # Clear tokens from OAuth2 service
        if hasattr(wmc_service_instance, 'oauth2_service'):
            await wmc_service_instance.oauth2_service.logout()

        # Clear tokens from main service
        wmc_service_instance.auth_token = None
        if hasattr(wmc_service_instance, 'token'):
            wmc_service_instance.token = None

        logger.info("✅ OAuth2 logout successful")

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@oauth2_router.get("/auth/refresh")
async def refresh_token():
    """Refresh access token using refresh token"""
    try:
        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        # Get OAuth2 service
        if not hasattr(wmc_service_instance, 'oauth2_service'):
            raise HTTPException(status_code=400, detail="OAuth2 service not available")

        oauth2_service = wmc_service_instance.oauth2_service
        token = await oauth2_service.refresh_access_token()

        # Update main service token reference
        wmc_service_instance.auth_token = token
        wmc_service_instance.token = token

        logger.info("✅ Token refresh successful")

        return {
            "success": True,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "message": "Token refreshed successfully"
        }

    except Exception as e:
        logger.error(f"❌ Token refresh error: {e}")
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

# Additional utility endpoints for invisible OAuth2

@oauth2_router.get("/auth/device-info")
async def get_device_info():
    """Get device type information for optimal authentication flow"""
    try:
        if not wmc_service_instance:
            raise HTTPException(status_code=503, detail="Service not available")

        # Get OAuth2 service for device detection
        if hasattr(wmc_service_instance, 'oauth2_service'):
            oauth2_service = wmc_service_instance.oauth2_service
            is_mobile = oauth2_service.is_mobile_device()
        else:
            # Simple mobile detection based on user agent
            import platform
            is_mobile = platform.system().lower() in ['android', 'ios']

        return {
            "is_mobile": is_mobile,
            "platform": platform.system(),
            "recommended_flow": "qr_code" if is_mobile else "auto_browser",
            "supports_auto_browser": not is_mobile,
            "supports_qr_code": True
        }

    except Exception as e:
        logger.error(f"❌ Device info error: {e}")
        raise HTTPException(status_code=500, detail=f"Device info failed: {str(e)}")
