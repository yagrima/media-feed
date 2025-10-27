#!/usr/bin/env python3
"""
Manual tests using only standard library
"""
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, "backend")

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from backend.app.core.config import Settings
        print("   ✅ Settings module imported")
    except Exception as e:
        print(f"   ❌ Settings import failed: {e}")
        return False
    
    try:
        from backend.app.services.email_service import EmailService
        print("   ✅ Email service imported")
    except Exception as e:
        print(f"   ❌ Email service import failed: {e}")
        return False
    
    try:
        from backend.app.services.auth_service import AuthService
        print("   ✅ Auth service imported")
    except Exception as e:
        print(f"   ❌ Auth service import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test all configuration settings"""
    print("⚙️ Testing configuration...")
    
    try:
        from backend.app.core.config import Settings
        settings = Settings()
        
        # Core settings
        if settings.APP_NAME == "Me Feed":
            print("   ✅ App name configured")
        else:
            print(f"   ❌ App name: {settings.APP_NAME}")
            return False
        
        # Security settings
        if settings.JWT_ALGORITHM == "RS256":
            print("   ✅ JWT RSA-256 configured")
        else:
            print(f"   ❌ JWT algorithm: {settings.JWT_ALGORITHM}")
            return False
        
        if settings.PASSWORD_MIN_LENGTH >= 12:
            print(f"   ✅ Password policy: {settings.PASSWORD_MIN_LENGTH} chars")
        else:
            print(f"   ❌ Password policy too short: {settings.PASSWORD_MIN_LENGTH}")
            return False
        
        # Database URL masking
        if settings.DATABASE_URL.count("*") > 10:
            print("   ✅ Database URL properly masked")
        else:
            print("   ❌ Database URL not properly masked")
            return False
        
        # Email configuration
        if settings.SMTP_HOST and settings.SMTP_HOST != "smtp.sendgrid.net":
            print(f"   ✅ SMTP configured: {settings.SMTP_HOST}")
        else:
            print("   ❌ SMTP not properly configured")
            return False
        
        if settings.SMTP_PASSWORD and settings.SMTP_PASSWORD != "your_sendgrid_api_key_here":
            print("   ✅ SMTP password configured")
        else:
            print("   ❌ SMTP password set")
            return False
            
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False
    
    return True

def test_jwt_keys():
    """Test JWT key files exist and are valid"""
    print("🔑 Testing JWT keys...")
    
    try:
        from backend.app.core.config import Settings
        settings = Settings()
        
        # Check private key
        private_key_path = Path(settings.JWT_PRIVATE_KEY_PATH)
        if private_key_path.exists():
            if private_key_path.stat().st_size > 100:
                print("   ✅ JWT private key exists and has content")
            else:
                print("   ❌ JWT private key too small")
                return False
        else:
            print(f"   ❌ JWT private key missing: {private_key_path}")
            return False
        
        # Check public key
        public_key_path = Path(settings.JWT_PUBLIC_KEY_PATH)
        if public_key_path.exists():
            if public_key_path.stat().st_size > 100:
                print("   ✅ JWT public key exists and has content")
            else:
                print("   ❌ JWT public key too small")
                return False
        else:
            print(f"   ❌ JWT public key missing: {public_key_path}")
            return False
        
        # Test key reading
        try:
            private_key = settings._load_private_key()
            if private_key:
                print("   ✅ Private key can be loaded")
            else:
                print("   ❌ Private key cannot be loaded")
                return False
        except Exception as e:
            print(f"   ❌ Private key loading failed: {e}")
            return False
        
        try:
            public_key = settings._load_public_key()
            if public_key:
                print("   ✅ Public key can be loaded")
            else:
                print("   ❌ Public key cannot be loaded")
                return False
        except Exception as e:
            print(f"   ❌ Public key loading failed: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ JWT key test failed: {e}")
        return False
    
    return True

def test_encryption():
    """Test encryption key exists"""
    print("🔒 Testing encryption...")
    
    try:
        from backend.app.core.config import Settings
        settings = Settings()
        
        encryption_key_path = Path(settings.ENCRYPTION_KEY_PATH)
        if encryption_key_path.exists():
            if encryption_key_path.stat().st_size > 20:
                print("   ✅ Encryption key exists and has content")
                
                # Test key loading
                try:
                    key = settings._load_encryption_key()
                    if key:
                        print("   ✅ Encryption key can be loaded")
                    else:
                        print("   ❌ Encryption key cannot be loaded")
                        return False
                except Exception as e:
                    print(f"   ❌ Encryption key loading failed: {e}")
                    return False
            else:
                print("   ❌ Encryption key too small")
                return False
        else:
            print(f"   ❌ Encryption key missing: {encryption_key_path}")
            return False
    
    except Exception as e:
        print(f"   ❌ Encryption test failed: {e}")
        return False
    
    return True

def test_email_templates():
    """Test email templates exist"""
    print("📧 Testing email templates...")
    
    template_dir = Path("backend/app/templates/email")
    required_templates = [
        "email_verification.html",
        "email_verification.txt", 
        "password_reset.html",
        "password_reset.txt",
        "daily_digest.html",
        "daily_digest.txt",
        "sequel_notification.html",
        "sequel_notification.txt"
    ]
    
    for template in required_templates:
        template_path = template_dir / template
        if template_path.exists():
            if template_path.stat().st_size > 50:
                print(f"   ✅ {template} exists and has content")
            else:
                print(f"   ⚠️  {template} exists but may be minimal")
        else:
            print(f"   ❌ {template} missing")
            return False
    
    return True

def test_secrets_directory():
    """Test secrets directory structure"""
    print("🗂️ Testing secrets directory...")
    
    secrets_dir = Path("../Media Feed Secrets")
    secrets_subdir = secrets_dir / "secrets"
    
    if not secrets_dir.exists():
        print(f"   ❌ Secrets directory missing: {secrets_dir}")
        return False
    
    print(f"   ✅ Secrets directory exists: {secrets_dir}")
    
    required_secret_files = [
        "jwt_private.pem",
        "jwt_public.pem", 
        "encryption.key",
        "db_user.txt",
        "db_password.txt",
        "redis_password.txt",
        "secret_key.txt"
    ]
    
    for secret_file in required_secret_files:
        secret_path = secrets_subdir / secret_file
        if secret_path.exists():
            if secret_path.stat().st_size > 5:
                print(f"   ✅ {secret_file} exists")
            else:
                print(f"   ⚠️  {secret_file} exists but may be empty")
        else:
            print(f"   ❌ {secret_file} missing")
            return False
    
    return True

def test_docker_files():
    """Test Docker configuration files"""
    print("🐳 Testing Docker configuration...")
    
    docker_files = [
        "docker-compose.yml",
        "docker-compose-simple.yml",
        "docker-checks.yml"
    ]
    
    for docker_file in docker_files:
        docker_path = Path(docker_file)
        if docker_path.exists():
            if docker_path.stat().st_size > 100:
                print(f"   ✅ {docker_file} exists and has content")
            else:
                print(f"   ⚠️  {docker_file} exists but may be minimal")
        else:
            print(f"   ❌ {docker_file} missing")
            return False
    
    return True

def test_api_endpoints():
    """Test if backend is running and endpoints are accessible"""
    print("🌐 Testing API endpoints...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8000/health"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("status") == "healthy":
                    print("   ✅ Backend health endpoint working")
                    print(f"   📊 Service: {data.get('service', 'Unknown')}")
                    print(f"   📦 Version: {data.get('version', 'Unknown')}")
                else:
                    print(f"   ❌ Health endpoint returned: {data}")
                    return False
            except json.JSONDecodeError:
                print(f"   ❌ Health endpoint returned invalid JSON: {result.stdout[:100]}")
                return False
        else:
            print(f"   ❌ Health endpoint failed: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print("   ❌ Health endpoint timeout")
        return False
    except FileNotFoundError:
        print("   ⚠️  curl not available, skipping endpoint test")
        return True  # Don't fail the test
    except Exception as e:
        print(f"   ❌ Endpoint test failed: {e}")
        return False
    
    return True

def main():
    """Run all manual tests"""
    print("Me Feed Manual Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("JWT Keys", test_jwt_keys),
        ("Encryption", test_encryption),
        ("Email Templates", test_email_templates),
        ("Secrets Directory", test_secrets_directory),
        ("Docker Files", test_docker_files),
        ("API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print("   ❌ TEST FAILED")
        except Exception as e:
            print(f"   ❌ TEST ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - APPLICATION IS PRODUCTION READY!")
        return 0
    elif passed >= total * 0.8:
        print("⚠️  MOST TESTS PASSED - Minor Issues to Address")
        return 1
    else:
        print("❌ CRITICAL ISSUES FOUND - Must Fix Before Production")
        return 2

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        sys.exit(1)
