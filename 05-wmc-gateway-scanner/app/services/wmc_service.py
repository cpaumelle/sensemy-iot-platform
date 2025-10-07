"""
WMC Service - Hybrid Authentication (Backend + OAuth2)
Version: 4.0.0
Created: 2025-08-20 18:45:00 UTC
Authors: SenseMy IoT Development Team

Changelog:
- Added OAuth2 invisible login integration
- Maintained backend authentication fallback
- Added hybrid authentication flow
- Enhanced token management
- Added authentication method selection

Purpose: Hybrid authentication supporting both backend credentials and OAuth2 invisible login
Users can choose between automatic backend auth or interactive OAuth2 flow
"""

import os
import logging
import asyncio
import httpx
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BackendToken:
    """Simple backend token for WMC authentication"""
    access_token: str
    expires_at: datetime
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at

class WMCService:
    """Hybrid WMC Service with backend authentication and OAuth2 support"""

    def __init__(self, base_url: str = "https://wmc.wanesy.com", auth_method: str = "auto"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30)
        self.token: Optional[BackendToken] = None
        self.auth_token = None  # For backward compatibility
        
        # Authentication method selection
        self.preferred_auth_method = auth_method  # "backend", "oauth2", "auto"

        # Backend authentication setup
        self.username = os.getenv('WMC_USERNAME', 'cpaumelle@microshare.io')
        self.password = os.getenv('WMC_PASSWORD', 'Eh9Mr@KpsXxVHN')

        # OAuth2 service (lazy initialization)
        self.oauth2_service = None
        self._oauth2_initialized = False

        # Configuration for backward compatibility
        self.config = type('Config', (), {
            'base_url': base_url,
            'username': self.username,
            'password': self.password,
        })()

        logger.info(f"🔧 WMC Service initialized - Auth method: {auth_method}, User: {self.username}")

    def _init_oauth2_service(self):
        """Lazy initialization of OAuth2 service"""
        if not self._oauth2_initialized:
            try:
                from .wmc_oauth2_service import WMCOAuth2Service
                self.oauth2_service = WMCOAuth2Service(self.base_url)
                self._oauth2_initialized = True
                logger.info("✅ OAuth2 service initialized")
            except Exception as e:
                logger.warning(f"⚠️ OAuth2 service not available: {e}")
                self._oauth2_initialized = True  # Don't try again

    async def close(self):
        """Close HTTP client and cleanup"""
        await self.client.aclose()
        if self.oauth2_service:
            await self.oauth2_service.close()

    # =============================================================================
    # Hybrid Authentication Methods
    # =============================================================================

    async def authenticate_smart(self, force_method: Optional[str] = None) -> bool:
        """
        Smart authentication that chooses the best method
        
        Args:
            force_method: Force specific method ("backend", "oauth2") or None for auto
            
        Returns:
            bool: True if authentication successful
        """
        method = force_method or self.preferred_auth_method
        
        logger.info(f"🔄 Starting smart authentication - Method: {method}")
        
        if method == "backend":
            return await self.authenticate_backend()
        elif method == "oauth2":
            return await self.authenticate_oauth2()
        elif method == "auto":
            # Auto mode: Try backend first, then OAuth2 if available
            backend_success = await self.authenticate_backend()
            if backend_success:
                logger.info("✅ Backend authentication successful")
                return True
            
            logger.info("⚠️ Backend authentication failed, trying OAuth2...")
            return await self.authenticate_oauth2()
        else:
            logger.error(f"❌ Unknown authentication method: {method}")
            return False

    async def authenticate_oauth2(self, invisible: bool = True) -> bool:
        """
        Authenticate using OAuth2 (invisible or interactive)
        
        Args:
            invisible: Use invisible login flow if True
            
        Returns:
            bool: True if authentication successful
        """
        try:
            self._init_oauth2_service()
            
            if not self.oauth2_service:
                logger.error("❌ OAuth2 service not available")
                return False
            
            # Check if already authenticated
            auth_status = self.oauth2_service.get_auth_status()
            if auth_status["authenticated"] and auth_status["token_valid"]:
                logger.info("✅ Already authenticated with valid OAuth2 token")
                self._sync_oauth2_token()
                return True
            
            if invisible:
                logger.info("🚀 Starting invisible OAuth2 authentication...")
                token = await self.oauth2_service.invisible_login(
                    auto_browser=True,
                    show_qr=True,
                    timeout=300
                )
            else:
                # Interactive OAuth2 flow (for future use)
                logger.info("🔗 Starting interactive OAuth2 authentication...")
                auth_url, state, code_verifier = self.oauth2_service.get_authorization_url()
                logger.info(f"🔗 Please visit: {auth_url}")
                return False  # Would need callback handling
            
            # Sync OAuth2 token to main service
            self._sync_oauth2_token()
            
            logger.info("✅ OAuth2 authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"❌ OAuth2 authentication error: {e}")
            return False

    def _sync_oauth2_token(self):
        """Sync OAuth2 token to main service token format"""
        if self.oauth2_service and self.oauth2_service.token:
            oauth_token = self.oauth2_service.token
            
            # Convert OAuth2Token to BackendToken for compatibility
            self.token = BackendToken(
                access_token=oauth_token.access_token,
                expires_at=oauth_token.expires_at or (datetime.utcnow() + timedelta(hours=1)),
                token_type=oauth_token.token_type
            )
            self.auth_token = self.token  # Backward compatibility
            
            logger.info("✅ OAuth2 token synced to main service")

    async def authenticate_backend(self) -> bool:
        """Authenticate using backend credentials"""
        try:
            logger.info("🔑 Authenticating with WMC using backend credentials...")

            if not self.username or not self.password:
                logger.error("❌ Missing WMC credentials in environment")
                return False

            # Try different authentication methods
            methods = [
                {"login": self.username, "password": self.password},
                {"username": self.username, "password": self.password}
            ]

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "WMC-Gateway-Scanner/4.0.0"
            }

            for login_data in methods:
                try:
                    response = await self.client.post(
                        f"{self.base_url}/gms/application/login",
                        json=login_data,
                        headers=headers
                    )

                    logger.info(f"🔄 Login attempt with {list(login_data.keys())[0]}: {response.status_code}")

                    if response.status_code in [200, 201]:
                        data = response.json()

                        if "token" in data:
                            # Create backend token with 1-hour expiry
                            self.token = BackendToken(
                                access_token=data["token"],
                                expires_at=datetime.utcnow() + timedelta(hours=1)
                            )
                            self.auth_token = self.token  # Backward compatibility

                            logger.info("✅ Backend authentication successful!")
                            return True
                        else:
                            logger.warning("⚠️ Login response missing token field")
                    else:
                        logger.warning(f"⚠️ Login failed: {response.status_code} - {response.text[:100]}")

                except Exception as e:
                    logger.warning(f"⚠️ Login method failed: {e}")
                    continue

            logger.error("❌ All backend authentication methods failed")
            return False

        except Exception as e:
            logger.error(f"❌ Backend authentication error: {e}")
            return False

    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token (hybrid approach)"""
        # Check current token validity
        if self.token and not self.token.is_expired:
            return True

        # Check OAuth2 token if available
        if self.oauth2_service:
            auth_status = self.oauth2_service.get_auth_status()
            if auth_status["authenticated"] and auth_status["token_valid"]:
                self._sync_oauth2_token()
                return True

        logger.info("🔄 Token expired or missing, re-authenticating...")
        return await self.authenticate_smart()

    # =============================================================================
    # Gateway and API Methods
    # =============================================================================

    async def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if not await self.ensure_authenticated():
            raise Exception("Failed to authenticate with WMC")

        return {
            "Authorization": f"{self.token.token_type} {self.token.access_token}",
            "Accept": "application/vnd.kerlink.iot-v1+json",
            "Content-Type": "application/vnd.kerlink.iot-v1+json",
            "User-Agent": "WMC-Gateway-Scanner/4.0.0"
        }

    async def get_gateway_by_eui(self, gateway_eui: str) -> Optional[Dict[str, Any]]:
        """Get gateway information by EUI using current authentication method"""
        try:
            logger.info(f"🔍 Looking up gateway: {gateway_eui}")

            headers = await self.get_headers()

            # Get list of gateways
            response = await self.client.get(
                f"{self.base_url}/gms/application/gateways",
                headers=headers
            )

            if response.status_code == 200:
                gateways = response.json()
                logger.info(f"📊 Retrieved {len(gateways) if isinstance(gateways, list) else 'unknown'} gateways from WMC")

                # Find gateway by EUI
                for gateway in gateways:
                    if gateway.get("eui", "").upper() == gateway_eui.upper():
                        # Get detailed gateway information
                        gateway_id = gateway.get("id")
                        if gateway_id:
                            detail_response = await self.client.get(
                                f"{self.base_url}/gms/application/gateways/{gateway_id}",
                                headers=headers
                            )

                            if detail_response.status_code == 200:
                                gateway_detail = detail_response.json()
                                gateway_detail["lookup_timestamp"] = datetime.utcnow().isoformat()
                                
                                # Indicate auth method used
                                auth_method = "oauth2" if self.oauth2_service and self.oauth2_service.token else "backend"
                                gateway_detail["source"] = f"wmc_{auth_method}_api"

                                logger.info(f"✅ Gateway found: {gateway.get('name', gateway_eui)}")
                                return gateway_detail

                logger.warning(f"⚠️ Gateway not found: {gateway_eui}")
                return None

            else:
                logger.error(f"❌ Failed to fetch gateways: {response.status_code} - {response.text[:100]}")
                return None

        except Exception as e:
            logger.error(f"❌ Error looking up gateway {gateway_eui}: {e}")
            return None

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        try:
            headers = await self.get_headers()

            response = await self.client.get(
                f"{self.base_url}/gms/application/userInfo",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to get user info: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting user info: {e}")
            return None

    # =============================================================================
    # OAuth2 Integration Methods
    # =============================================================================

    def get_authorization_url(self) -> tuple[str, str, str]:
        """Get OAuth2 authorization URL (for manual flows)"""
        self._init_oauth2_service()
        if not self.oauth2_service:
            raise Exception("OAuth2 service not available")
        
        return self.oauth2_service.get_authorization_url()

    async def exchange_code_for_token(self, authorization_code: str, code_verifier: str):
        """Exchange OAuth2 authorization code for token"""
        self._init_oauth2_service()
        if not self.oauth2_service:
            raise Exception("OAuth2 service not available")
        
        token = await self.oauth2_service.exchange_code_for_token(authorization_code, code_verifier)
        self._sync_oauth2_token()
        return token

    async def invisible_login(self, **kwargs):
        """Shortcut for invisible OAuth2 login"""
        return await self.authenticate_oauth2(invisible=True)

    # =============================================================================
    # Legacy Methods (For Route Compatibility)
    # =============================================================================

    async def test_connection(self) -> bool:
        """Test WMC API connectivity"""
        try:
            response = await self.client.get(f"{self.base_url}/gms/application/doc", timeout=10)
            return response.status_code in [200, 302]  # 302 might redirect to login
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    async def authenticate(self) -> bool:
        """Legacy authenticate method - uses smart authentication"""
        return await self.authenticate_smart()

    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection and authentication status"""
        connected = await self.test_connection()
        authenticated = self.token and not self.token.is_expired if self.token else False
        
        # Determine auth method
        auth_method = "unknown"
        if self.oauth2_service and self.oauth2_service.token:
            auth_method = "oauth2"
        elif self.token:
            auth_method = "backend_credentials"

        return {
            "connected": connected,
            "authenticated": authenticated,
            "token_valid": authenticated,
            "auth_method": auth_method,
            "base_url": self.base_url,
            "username": self.username,
            "expires_at": self.token.expires_at.isoformat() if self.token else None,
            "oauth2_available": self.oauth2_service is not None,
            "preferred_auth_method": self.preferred_auth_method
        }

    def get_oauth2_status(self) -> Dict[str, Any]:
        """Get OAuth2 authentication status"""
        if self.oauth2_service:
            oauth2_status = self.oauth2_service.get_auth_status()
            oauth2_status["service_available"] = True
        else:
            oauth2_status = {
                "authenticated": False,
                "token_valid": False,
                "service_available": False,
                "auth_method": "oauth2_not_available"
            }

        # Add backend auth info for compatibility
        if self.token and not oauth2_status["authenticated"]:
            oauth2_status.update({
                "authenticated": not self.token.is_expired,
                "token_valid": not self.token.is_expired,
                "expires_at": self.token.expires_at.isoformat(),
                "auth_method": "backend_credentials"
            })

        return oauth2_status

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive service health check"""
        connection_status = await self.get_connection_status()

        # Determine available auth methods
        auth_methods = ["backend_credentials"]
        if self.oauth2_service:
            auth_methods.append("oauth2_invisible")

        return {
            "service": "wmc-gateway-scanner",
            "version": "4.0.0",
            "status": "WMC Gateway Scanner healthy ✅",
            "wmc_api_status": "connected" if connection_status["connected"] else "disconnected",
            "authentication": {
                "method": connection_status["auth_method"],
                "authenticated": connection_status["authenticated"],
                "token_valid": connection_status["token_valid"],
                "username": self.username,
                "auto_login": True,
                "available_methods": auth_methods,
                "preferred_method": self.preferred_auth_method
            },
            "features": [
                "qr_code_scanning",
                "wmc_api_integration",
                "mobile_responsive_ui",
                "real_time_gateway_status",
                "hybrid_authentication",
                "backend_authentication",
                "oauth2_invisible_login",
                "automatic_login"
            ],
            "oauth2_status": self.get_oauth2_status(),
            "templates_available": True
        }

    def __del__(self):
        """Cleanup when service is destroyed"""
        try:
            asyncio.create_task(self.close())
        except:
            pass
