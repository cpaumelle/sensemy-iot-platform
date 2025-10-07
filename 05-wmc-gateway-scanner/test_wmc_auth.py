#!/usr/bin/env python3
"""
WMC Authentication Unit Test
Version: 1.0.0
Created: 2025-08-20 16:10:00 UTC

Standalone script to test and debug WMC API authentication methods
Based on official WMC API documentation findings
"""

import httpx
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Load credentials from environment
WMC_BASE_URL = os.getenv("WMC_BASE_URL", "https://wmc.wanesy.com")
WMC_USERNAME = os.getenv("WMC_USERNAME", "cpaumelle@microshare.io")
WMC_PASSWORD = os.getenv("WMC_PASSWORD", "Eh9Mr@KpsXxVHN")

print(f"🔍 WMC Authentication Unit Test")
print(f"📡 Testing with: {WMC_BASE_URL}")
print(f"👤 Username: {WMC_USERNAME}")
print(f"🔒 Password: {'*' * len(WMC_PASSWORD)}")
print("=" * 60)

async def test_connectivity():
    """Test basic WMC API connectivity"""
    print("🌐 Testing WMC API connectivity...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Test the documentation endpoint (should work without auth)
            response = await client.get(f"{WMC_BASE_URL}/gms/application/doc")
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("   ✅ WMC API is accessible")
                return True
            else:
                print(f"   ❌ WMC API returned {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False

async def test_authentication_method_1():
    """Test Method 1: Standard JSON POST to /gms/application/login"""
    print("\n🔑 Method 1: Standard JSON POST authentication...")
    
    login_data = {
        "login": WMC_USERNAME,
        "password": WMC_PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "WMC-Gateway-Scanner/1.0.0"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{WMC_BASE_URL}/gms/application/login",
                json=login_data,
                headers=headers
            )
            
            print(f"   Request URL: {response.request.url}")
            print(f"   Request Headers: {dict(response.request.headers)}")
            print(f"   Request Body: {response.request.content.decode()}")
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Response Body: {json.dumps(data, indent=2)}")
                
                if "token" in data:
                    print("   ✅ Authentication successful!")
                    return data["token"]
                else:
                    print("   ⚠️ Response missing token field")
                    return None
            else:
                print(f"   Response Body: {response.text}")
                print(f"   ❌ Authentication failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            return None

async def test_authentication_method_2():
    """Test Method 2: Form data POST"""
    print("\n🔑 Method 2: Form data POST authentication...")
    
    form_data = {
        "login": WMC_USERNAME,
        "password": WMC_PASSWORD
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; WMC-Scanner/1.0)"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{WMC_BASE_URL}/gms/application/login",
                data=form_data,
                headers=headers
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    print(f"   Response Body: {json.dumps(data, indent=2)}")
                    
                    if "token" in data:
                        print("   ✅ Form data authentication successful!")
                        return data["token"]
                    else:
                        print("   ⚠️ Response missing token field")
                        return None
                except:
                    print(f"   Response Body (text): {response.text}")
                    return None
            else:
                print(f"   Response Body: {response.text}")
                print(f"   ❌ Form data authentication failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Form data authentication error: {e}")
            return None

async def test_authentication_method_3():
    """Test Method 3: Different field names (username/password)"""
    print("\n🔑 Method 3: Different field names authentication...")
    
    login_data = {
        "username": WMC_USERNAME,
        "password": WMC_PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "WMC-Gateway-Scanner/1.0.0"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{WMC_BASE_URL}/gms/application/login",
                json=login_data,
                headers=headers
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Response Body: {json.dumps(data, indent=2)}")
                
                if "token" in data:
                    print("   ✅ Username/password authentication successful!")
                    return data["token"]
                else:
                    print("   ⚠️ Response missing token field")
                    return None
            else:
                print(f"   Response Body: {response.text}")
                print(f"   ❌ Username/password authentication failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Username/password authentication error: {e}")
            return None

async def test_token_usage(token: str):
    """Test using the JWT token for authenticated requests"""
    print(f"\n🎟️ Testing token usage...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "WMC-Gateway-Scanner/1.0.0"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Test getting the application entry point
            response = await client.get(
                f"{WMC_BASE_URL}/gms/application",
                headers=headers
            )
            
            print(f"   Request URL: {response.request.url}")
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Token is valid and working!")
                print(f"   Available endpoints: {list(data.get('links', {}).keys()) if 'links' in data else 'No links found'}")
                return True
            else:
                print(f"   Response Body: {response.text}")
                print(f"   ❌ Token validation failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Token usage error: {e}")
            return False

async def test_gateways_endpoint(token: str):
    """Test accessing gateways endpoint with token"""
    print(f"\n🚪 Testing gateways endpoint...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "WMC-Gateway-Scanner/1.0.0"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                f"{WMC_BASE_URL}/gms/application/gateways",
                headers=headers
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Gateways endpoint accessible!")
                print(f"   Number of gateways: {len(data) if isinstance(data, list) else 'Unknown'}")
                
                if isinstance(data, list) and len(data) > 0:
                    sample_gateway = data[0]
                    print(f"   Sample gateway fields: {list(sample_gateway.keys())}")
                
                return True
            else:
                print(f"   Response Body: {response.text}")
                print(f"   ❌ Gateways endpoint failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Gateways endpoint error: {e}")
            return False

async def main():
    """Run all authentication tests"""
    print(f"🚀 Starting WMC Authentication Unit Tests")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    connected = await test_connectivity()
    if not connected:
        print("\n❌ Cannot proceed - WMC API is not accessible")
        return
    
    # Test authentication methods
    token = None
    
    # Method 1: Standard JSON
    token = await test_authentication_method_1()
    
    # If Method 1 failed, try Method 2
    if not token:
        token = await test_authentication_method_2()
    
    # If Method 2 failed, try Method 3
    if not token:
        token = await test_authentication_method_3()
    
    if token:
        print(f"\n🎉 Authentication successful!")
        print(f"🎟️ Token (first 20 chars): {token[:20]}...")
        
        # Test token usage
        token_valid = await test_token_usage(token)
        
        if token_valid:
            # Test gateways endpoint
            await test_gateways_endpoint(token)
    else:
        print(f"\n❌ All authentication methods failed!")
        print(f"💡 Check credentials and CloudFront configuration")
    
    print("\n" + "=" * 60)
    print(f"⏰ Completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())
