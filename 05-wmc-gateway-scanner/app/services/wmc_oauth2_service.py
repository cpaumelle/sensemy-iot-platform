"""
WMC OAuth2 Service Implementation - Enhanced with Invisible Login
Version: 3.0.0
Created: 2025-08-20 18:30:00 UTC
Authors: SenseMy IoT Development Team

Changelog:
- Added invisible OAuth2 login with local callback server
- Added automatic browser launching for desktop users
- Added QR code generation for mobile users
- Added token persistence with secure storage
- Added seamless authentication flow

Complete OAuth2 implementation for WMC authentication using AWS Cognito
Based on browser network analysis and OAuth2 discovery
"""

import httpx
import asyncio
import os
import logging
import urllib.parse
import secrets
import base64
import hashlib
import json
import webbrowser
import socket
import threading
import qrcode
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from aiohttp import web, ClientSession
import aiohttp
from cryptography.fernet import Fernet
import platform

logger = logging.getLogger(__name__)

@dataclass
class WMCOAuth2Config:
    """WMC OAuth2 configuration"""
    client_id: str = "2lk7uhemurg6jpt8qmvcf1e4dl"
    auth_domain: str = "auth.wmc.wanesy.com"
    redirect_uri: str = "https://wmc.wanesy.com/login/oauth2/code/cognito"
    scope: str = "openid profile email"
    response_type: str = "code"
    local_callback_port: int = 8765

@dataclass
class OAuth2Token:
    """OAuth2 access token"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.expires_at is None and self.expires_in:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        return self.expires_at and datetime.utcnow() >= self.expires_at

class TokenStorage:
    """Secure token storage with encryption"""
    
    def __init__(self, storage_dir: str = ".wmc_tokens"):
        self.storage_dir = storage_dir
        self.token_file = os.path.join(storage_dir, "oauth2_token.enc")
        self.key_file = os.path.join(storage_dir, "key.enc")
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize encryption key
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize or load encryption key"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
        
        self.cipher = Fernet(self.key)
    
    def save_token(self, token: OAuth2Token):
        """Encrypt and save token to disk"""
        try:
            token_data = {
                "access_token": token.access_token,
                "token_type": token.token_type,
                "expires_in": token.expires_in,
                "refresh_token": token.refresh_token,
                "scope": token.scope,
                "id_token": token.id_token,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None
            }
            
            encrypted_data = self.cipher.encrypt(json.dumps(token_data).encode())
            
            with open(self.token_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.token_file, 0o600)
            
            logger.info("✅ Token saved securely")
            
        except Exception as e:
            logger.error(f"❌ Failed to save token: {e}")
    
    def load_token(self) -> Optional[OAuth2Token]:
        """Load and decrypt token from disk"""
        try:
            if not os.path.exists(self.token_file):
                return None
            
            with open(self.token_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            # Parse expires_at
            expires_at = None
            if token_data.get("expires_at"):
                expires_at = datetime.fromisoformat(token_data["expires_at"])
            
            token = OAuth2Token(
                access_token=token_data["access_token"],
                token_type=token_data["token_type"],
                expires_in=token_data["expires_in"],
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
                id_token=token_data.get("id_token"),
                expires_at=expires_at
            )
            
            logger.info("✅ Token loaded from secure storage")
            return token
            
        except Exception as e:
            logger.error(f"❌ Failed to load token: {e}")
            return None
    
    def clear_token(self):
        """Remove stored token"""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                logger.info("✅ Token cleared from storage")
        except Exception as e:
            logger.error(f"❌ Failed to clear token: {e}")

class LocalCallbackServer:
    """Local HTTP server to capture OAuth2 callbacks"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        self.authorization_code = None
        self.state = None
        self.error = None
        self.callback_received = asyncio.Event()
    
    async def start(self) -> str:
        """Start the local callback server"""
        self.app = web.Application()
        self.app.router.add_get('/callback', self.handle_callback)
        self.app.router.add_get('/', self.handle_root)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        # Try to find an available port
        port = self.port
        for attempt in range(10):
            try:
                self.site = web.TCPSite(self.runner, 'localhost', port)
                await self.site.start()
                
                callback_url = f"http://localhost:{port}/callback"
                logger.info(f"🌐 Local callback server started on {callback_url}")
                return callback_url
                
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    port += 1
                    logger.warning(f"⚠️ Port {port-1} in use, trying {port}")
                    continue
                else:
                    raise
        
        raise Exception("Could not find available port for callback server")
    
    async def stop(self):
        """Stop the local callback server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("🛑 Local callback server stopped")
    
    async def handle_callback(self, request):
        """Handle OAuth2 callback"""
        query = request.query
        
        self.authorization_code = query.get('code')
        self.state = query.get('state')
        self.error = query.get('error')
        
        logger.info(f"📥 OAuth2 callback received - Code: {'✅' if self.authorization_code else '❌'}")
        
        # Signal that callback was received
        self.callback_received.set()
        
        if self.error:
            return web.Response(text=f"""
            <html><body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1 style="color: red;">❌ Authentication Error</h1>
                <p>Error: {self.error}</p>
                <p>You can close this window and try again.</p>
            </body></html>
            """, content_type='text/html')
        
        if self.authorization_code:
            return web.Response(text="""
            <html><body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                <h1 style="color: green;">✅ Authentication Successful!</h1>
                <p>Authorization code received successfully.</p>
                <p>You can close this window now.</p>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                </script>
            </body></html>
            """, content_type='text/html')
        
        return web.Response(text="""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>❌ Authentication Error</h1>
            <p>No authorization code received.</p>
            <p>You can close this window and try again.</p>
        </body></html>
        """, content_type='text/html')
    
    async def handle_root(self, request):
        """Handle root path"""
        return web.Response(text="""
        <html><body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <h1>🔐 WMC OAuth2 Authentication</h1>
            <p>Waiting for authentication callback...</p>
            <p>If you haven't been redirected to login, please check your browser.</p>
        </body></html>
        """, content_type='text/html')

class WMCOAuth2Service:
    """Enhanced WMC OAuth2 authentication service with invisible login"""

    def __init__(self, base_url: str = "https://wmc.wanesy.com"):
        self.config = WMCOAuth2Config()
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30)
        self.token: Optional[OAuth2Token] = None
        
        # Enhanced features
        self.token_storage = TokenStorage()
        self.callback_server: Optional[LocalCallbackServer] = None
        
        # Load existing token if available
        self._load_stored_token()

    def _load_stored_token(self):
        """Load stored token on initialization"""
        stored_token = self.token_storage.load_token()
        if stored_token and not stored_token.is_expired:
            self.token = stored_token
            logger.info("✅ Valid token loaded from storage")
        elif stored_token and stored_token.is_expired:
            logger.info("⚠️ Stored token expired, will need to refresh or re-authenticate")
            self.token = stored_token

    async def close(self):
        """Close HTTP client and cleanup"""
        await self.client.aclose()
        if self.callback_server:
            await self.callback_server.stop()

    def generate_pkce_challenge(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge for OAuth2"""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

        # Generate code challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        return code_verifier, code_challenge

    def get_authorization_url(self, state: Optional[str] = None, local_callback: bool = False) -> tuple[str, str, str]:
        """
        Generate OAuth2 authorization URL for user login

        Args:
            state: Optional state parameter
            local_callback: Use local callback server instead of WMC redirect

        Returns:
            tuple: (authorization_url, state, code_verifier)
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        code_verifier, code_challenge = self.generate_pkce_challenge()
        
        # Use local callback if requested
        redirect_uri = self.config.redirect_uri
        if local_callback and self.callback_server:
            redirect_uri = f"http://localhost:{self.callback_server.port}/callback"

        params = {
            "client_id": self.config.client_id,
            "response_type": self.config.response_type,
            "scope": self.config.scope,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        auth_url = f"https://{self.config.auth_domain}/oauth2/authorize?" + urllib.parse.urlencode(params)

        logger.info(f"🔗 Generated OAuth2 authorization URL")
        return auth_url, state, code_verifier

    def generate_qr_code(self, auth_url: str, format: str = "ascii") -> str:
        """
        Generate QR code for mobile users
        
        Args:
            auth_url: OAuth2 authorization URL
            format: "ascii" for terminal display or "base64" for image data
            
        Returns:
            QR code as ASCII art or base64 image data
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(auth_url)
            qr.make(fit=True)
            
            if format == "ascii":
                # Create ASCII QR code for terminal
                qr_ascii = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=1,
                    border=1,
                )
                qr_ascii.add_data(auth_url)
                qr_ascii.make(fit=True)
                
                from io import StringIO
                f = StringIO()
                qr_ascii.print_ascii(out=f)
                return f.getvalue()
            
            elif format == "base64":
                # Create image QR code
                img = qr.make_image(fill_color="black", back_color="white")
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                import base64
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"❌ QR code generation failed: {e}")
            return f"QR Code generation failed: {e}"

    def is_mobile_device(self) -> bool:
        """Detect if running on mobile device"""
        # Simple detection based on platform
        system = platform.system().lower()
        if system in ['android', 'ios']:
            return True
        
        # Check for common mobile indicators in environment
        if any(mobile_env in os.environ.get('USER_AGENT', '').lower() 
               for mobile_env in ['mobile', 'android', 'iphone', 'ipad']):
            return True
            
        return False

    async def invisible_login(self, 
                            auto_browser: bool = True, 
                            show_qr: bool = True,
                            timeout: int = 300) -> OAuth2Token:
        """
        Completely invisible OAuth2 login flow
        
        Args:
            auto_browser: Automatically open browser for desktop users
            show_qr: Show QR code for mobile users
            timeout: Timeout in seconds for user authentication
            
        Returns:
            OAuth2Token: Valid access token
        """
        logger.info("🚀 Starting invisible OAuth2 login flow...")
        
        try:
            # Check if we have a valid token already
            if self.token and not self.token.is_expired:
                logger.info("✅ Valid token already available")
                return self.token
            
            # Try to refresh existing token
            if self.token and self.token.refresh_token:
                try:
                    refreshed_token = await self.refresh_access_token()
                    logger.info("✅ Token refreshed successfully")
                    return refreshed_token
                except Exception as e:
                    logger.warning(f"⚠️ Token refresh failed: {e}")
            
            # Start local callback server
            self.callback_server = LocalCallbackServer(self.config.local_callback_port)
            callback_url = await self.callback_server.start()
            
            # Generate authorization URL with local callback
            auth_url, state, code_verifier = self.get_authorization_url(local_callback=True)
            
            # Detect device type and handle accordingly
            is_mobile = self.is_mobile_device()
            
            if is_mobile or not auto_browser:
                # Mobile device or manual mode - show QR code
                if show_qr:
                    logger.info("📱 Mobile device detected - generating QR code")
                    qr_code = self.generate_qr_code(auth_url, "ascii")
                    print("\n" + "="*50)
                    print("📱 SCAN QR CODE TO LOGIN:")
                    print("="*50)
                    print(qr_code)
                    print("="*50)
                    print(f"Or visit: {auth_url}")
                    print("="*50 + "\n")
                else:
                    print(f"🔗 Please visit: {auth_url}")
            else:
                # Desktop - auto-open browser
                logger.info("🖥️ Desktop detected - opening browser automatically")
                try:
                    webbrowser.open(auth_url)
                    logger.info("✅ Browser opened successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to open browser: {e}")
                    print(f"🔗 Please visit: {auth_url}")
            
            # Wait for callback
            logger.info(f"⏱️ Waiting for authentication (timeout: {timeout}s)...")
            
            try:
                await asyncio.wait_for(
                    self.callback_server.callback_received.wait(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise Exception(f"Authentication timeout after {timeout} seconds")
            
            # Check for errors
            if self.callback_server.error:
                raise Exception(f"OAuth2 error: {self.callback_server.error}")
            
            if not self.callback_server.authorization_code:
                raise Exception("No authorization code received")
            
            # Exchange code for token
            logger.info("🔄 Exchanging authorization code for token...")
            token = await self.exchange_code_for_token(
                self.callback_server.authorization_code,
                code_verifier
            )
            
            # Save token securely
            self.token_storage.save_token(token)
            
            logger.info("✅ Invisible OAuth2 login completed successfully!")
            return token
            
        finally:
            # Cleanup callback server
            if self.callback_server:
                await self.callback_server.stop()
                self.callback_server = None

    async def exchange_code_for_token(self, authorization_code: str, code_verifier: str) -> OAuth2Token:
        """
        Exchange authorization code for access token

        Args:
            authorization_code: Code from OAuth2 callback
            code_verifier: PKCE code verifier

        Returns:
            OAuth2Token: Access token and metadata
        """
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "code": authorization_code,
            "code_verifier": code_verifier
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        logger.info("🔄 Exchanging authorization code for access token...")

        try:
            response = await self.client.post(
                f"https://{self.config.auth_domain}/oauth2/token",
                data=token_data,
                headers=headers
            )

            if response.status_code == 200:
                token_response = response.json()

                self.token = OAuth2Token(
                    access_token=token_response["access_token"],
                    token_type=token_response.get("token_type", "Bearer"),
                    expires_in=token_response.get("expires_in", 3600),
                    refresh_token=token_response.get("refresh_token"),
                    scope=token_response.get("scope"),
                    id_token=token_response.get("id_token")
                )

                logger.info("✅ Successfully obtained access token")
                return self.token
            else:
                error_detail = response.text
                logger.error(f"❌ Token exchange failed: {response.status_code} - {error_detail}")
                raise Exception(f"Token exchange failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Token exchange error: {e}")
            raise

    async def refresh_access_token(self) -> OAuth2Token:
        """Refresh access token using refresh token"""
        if not self.token or not self.token.refresh_token:
            raise Exception("No refresh token available")

        token_data = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "refresh_token": self.token.refresh_token
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        try:
            response = await self.client.post(
                f"https://{self.config.auth_domain}/oauth2/token",
                data=token_data,
                headers=headers
            )

            if response.status_code == 200:
                token_response = response.json()

                # Update existing token
                self.token.access_token = token_response["access_token"]
                self.token.expires_in = token_response.get("expires_in", 3600)
                self.token.expires_at = datetime.utcnow() + timedelta(seconds=self.token.expires_in)

                if "refresh_token" in token_response:
                    self.token.refresh_token = token_response["refresh_token"]

                # Save updated token
                self.token_storage.save_token(self.token)

                logger.info("✅ Access token refreshed successfully")
                return self.token
            else:
                logger.error(f"❌ Token refresh failed: {response.status_code}")
                raise Exception(f"Token refresh failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}")
            raise

    async def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.token:
            return False

        if self.token.is_expired:
            if self.token.refresh_token:
                try:
                    await self.refresh_access_token()
                    return True
                except:
                    return False
            else:
                return False

        return True

    async def get_headers(self) -> Dict[str, str]:
        """Get headers with OAuth2 access token"""
        if not await self.ensure_valid_token():
            raise Exception("No valid access token available")

        return {
            "Authorization": f"{self.token.token_type} {self.token.access_token}",
            "Accept": "application/vnd.kerlink.iot-v1+json",
            "Content-Type": "application/vnd.kerlink.iot-v1+json"
        }

    async def get_gateway_by_eui(self, gateway_eui: str) -> Optional[Dict[str, Any]]:
        """Get gateway information by EUI using OAuth2 token"""
        try:
            headers = await self.get_headers()

            logger.info(f"🔍 Looking up gateway: {gateway_eui}")

            # Get list of gateways
            response = await self.client.get(
                f"{self.base_url}/gms/application/gateways",
                headers=headers
            )

            if response.status_code == 200:
                gateways = response.json()

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
                                gateway_detail["source"] = "wmc_oauth2_api"

                                logger.info(f"✅ Gateway found: {gateway.get('name', gateway_eui)}")
                                return gateway_detail

                logger.warning(f"⚠️ Gateway not found: {gateway_eui}")
                return None

            else:
                logger.error(f"❌ Failed to fetch gateways: {response.status_code}")
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

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            "authenticated": self.token is not None,
            "token_valid": self.token and not self.token.is_expired if self.token else False,
            "expires_at": self.token.expires_at.isoformat() if self.token and self.token.expires_at else None,
            "has_refresh_token": self.token and self.token.refresh_token is not None if self.token else False,
            "scope": self.token.scope if self.token else None,
            "has_stored_token": self.token_storage.load_token() is not None,
            "auth_method": "oauth2_invisible"
        }

    async def logout(self):
        """Logout and clear all tokens"""
        self.token = None
        self.token_storage.clear_token()
        logger.info("✅ Logged out successfully")
