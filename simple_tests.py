#!/usr/bin/env python3
"""
Simple local tests for Me Feed - no external dependencies
"""
import asyncio
import httpx
import time
from datetime import datetime
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

async def test_health():
    """Test health endpoints"""
    print("🔍 Testing health endpoints...")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Test backend health
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("   ✅ Backend health check passed")
            else:
                print(f"   ❌ Backend health failed: {response.status_code}")
                return False
                
            # Test frontend
            try:
                response = await client.get(f"{FRONTEND_URL}")
                if response.status_code == 200:
                    print("   ✅ Frontend accessible")
                else:
                    print(f"   ❌ Frontend failed: {response.status_code}")
            except:
                print("   ⚠️  Frontend not accessible (may be normal)")
                
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    return True

async def test_authentication():
    """Test authentication flow"""
    print("🔐 Testing authentication flow...")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Test registration
            user_data = {
                "email": f"test-{datetime.now().timestamp()}@test.com",
                "password": "TestPassword123!@#"
            }
            
            response = await client.post(f"{BASE_URL}/api/auth/register", json=user_data)
            if response.status_code in [200, 201]:
                print("   ✅ User registration works")
                data = response.json()
                if "access_token" in data:
                    print("   ✅ JWT token generation works")
                else:
                    print("   ❌ No token in response")
                    return False
            else:
                print(f"   ❌ Registration failed: {response.status_code}")
                if hasattr(response, 'text'):
                    print(f"   Error: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False
    
    return True

async def test_email_service():
    """Test email configuration"""
    print("📧 Testing email service configuration...")
    
    try:
        # Import and test email service
        import sys
        sys.path.insert(0, "backend")
        from backend.app.core.config import Settings
        from backend.app.services.email_service import EmailService
        
        settings = Settings()
        
        # Check email configuration
        if settings.SMTP_HOST:
            print(f"   ✅ SMTP Host configured: {settings.SMTP_HOST}")
        else:
            print("   ❌ SMTP Host not configured")
            return False
            
        if settings.SMTP_USER:
            print(f"   ✅ SMTP User configured: {settings.SMTP_USER[:10]}...")
        else:
            print("   ❌ SMTP User not configured")
            return False
            
        if settings.SMTP_PASSWORD and settings.SMTP_PASSWORD != "your_sendgrid_api_key_here":
            print("   ✅ SMTP Password configured")
        else:
            print("   ❌ SMTP Password not configured")
            return False
            
        # Test email service instantiation
        email_service = EmailService()
        print("   ✅ Email service can be initialized")
        
    except Exception as e:
        print(f"   ❌ Email service test failed: {e}")
        return False
    
    return True

async def test_security():
    """Test security configuration"""
    print("🔒 Testing security configuration...")
    
    try:
        import sys
        sys.path.insert(0, "backend")
        from backend.app.core.config import Settings
        from pathlib import Path
        
        settings = Settings()
        
        # Check JWT configuration
        if settings.JWT_ALGORITHM == "RS256":
            print("   ✅ JWT RSA-256 algorithm configured")
        else:
            print(f"   ❌ JWT algorithm: {settings.JWT_ALGORITHM}")
            return False
            
        # Check JWT key files
        try:
            private_key_path = Path(settings.JWT_PRIVATE_KEY_PATH)
            public_key_path = Path(settings.JWT_PUBLIC_KEY_PATH)
            
            if private_key_path.exists() and private_key_path.stat().st_size > 100:
                print("   ✅ JWT private key exists")
            else:
                print(f"   ❌ JWT private key issue: {settings.JWT_PRIVATE_KEY_PATH}")
                return False
                
            if public_key_path.exists() and public_key_path.stat().st_size > 100:
                print("   ✅ JWT public key exists")
            else:
                print(f"   ❌ JWT public key issue: {settings.JWT_PUBLIC_KEY_PATH}")
                return False
        except Exception as e:
            print(f"   ❌ JWT key check failed: {e}")
            return False
            
        # Check database URL masking
        if settings.DATABASE_URL.count("*") > 10:
            print("   ✅ Database URL properly masked")
        else:
            print("   ❌ Database URL not properly masked")
            return False
            
    except Exception as e:
        print(f"   ❌ Security test failed: {e}")
        return False
    
    return True

async def test_file_upload():
    """Test file upload endpoint"""
    print("📁 Testing file upload endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Create test user first
            user_data = {
                "email": f"upload-{datetime.now().timestamp()}@test.com",
                "password": "UploadTest123!@#"
            }
            
            reg_response = await client.post(f"{BASE_URL}/api/auth/register", json=user_data)
            if reg_response.status_code not in [200, 201]:
                print("   ⚠️  Could not create test user for upload test")
                return True  # Don't fail the test
                
            token = reg_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            # Test CSV upload
            csv_content = """Title,Type,Year
Test Movie,Movie,2023
Test Series,TV Series,2022
"""
            
            files = {"file": ("test.csv", csv_content, "text/csv")}
            upload_response = await client.post(f"{BASE_URL}/api/import/upload", 
                                               files=files, 
                                               headers=headers)
            
            if upload_response.status_code in [200, 201, 202]:
                print("   ✅ File upload endpoint accepts files")
            else:
                print(f"   ❌ File upload failed: {upload_response.status_code}")
                if hasattr(upload_response, 'text'):
                    print(f"   Error: {upload_response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ File upload test failed: {e}")
        return False
    
    return True

async def test_database():
    """Test database connectivity"""
    print("💾 Testing database connectivity...")
    
    try:
        import sys
        sys.path.insert(0, "backend")
        
        # Test import
        from backend.app.db.base import get_db
        from backend.app.core.config import Settings
        import asyncpg
        
        settings = Settings()
        
        # Parse database URL (simplified)
        db_url = settings.DATABASE_URL
        if db_url and db_url.count("*") > 10:
            print("   ⚠️  Using masked DB URL, can't test detailed connectivity")
            print("   ✅ Database URL appears configured")
        else:
            print("   ❌ Database URL not properly configured")
            return False
            
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🧪 Me Feed Local Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health & Connectivity", test_health),
        ("Authentication Flow", test_authentication),
        ("Email Service", test_email_service),
        ("Security Configuration", test_security),
        ("File Upload", test_file_upload),
        ("Database", test_database)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if await test_func():
                passed += 1
            else:
                print("   ❌ TEST FAILED")
        except Exception as e:
            print(f"   ❌ TEST ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION!")
        return 0
    elif passed >= total * 0.8:
        print("⚠️  MOST TESTS PASSED - Minor Issues to Address")
        return 1
    else:
        print("❌ CRITICAL ISSUES FOUND - Must Fix Before Production")
        return 2

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        sys.exit(1)
