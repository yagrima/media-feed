#!/usr/bin/env python3
"""
Basic manual tests avoiding Unicode issues
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, "backend")

def test_configuration():
    """Test configuration"""
    print("Testing configuration...")
    try:
        from backend.app.core.config import Settings
        settings = Settings()
        
        print(f"   App: {settings.APP_NAME}")
        print(f"   JWT: {settings.JWT_ALGORITHM}")
        print(f"   Password min: {settings.PASSWORD_MIN_LENGTH}")
        print(f"   SMTP host: {settings.SMTP_HOST}")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_jwt_keys():
    """Test JWT keys"""
    print("Testing JWT keys...")
    try:
        from backend.app.core.config import Settings
        settings = Settings()
        
        private_path = Path(settings.JWT_PRIVATE_KEY_PATH)
        public_path = Path(settings.JWT_PUBLIC_KEY_PATH)
        
        print(f"   Private key: {private_path.exists()} ({private_path.stat().st_size} bytes)")
        print(f"   Public key: {public_path.exists()} ({public_path.stat().st_size} bytes)")
        return private_path.exists() and public_path.exists()
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_secrets():
    """Test secrets directory"""
    print("Testing secrets...")
    try:
        secrets_dir = Path("../Media Feed Secrets/secrets")
        print(f"   Secrets dir: {secrets_dir.exists()}")
        
        if secrets_dir.exists():
            required = ["jwt_private.pem", "jwt_public.pem", "encryption.key"]
            for file in required:
                file_path = secrets_dir / file
                print(f"   {file}: {file_path.exists()}")
        return secrets_dir.exists()
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_email_service():
    """Test email service"""
    print("Testing email service...")
    try:
        from backend.app.services.email_service import EmailService
        email_service = EmailService()
        print(f"   SMTP host: {email_service.smtp_host}")
        print(f"   SMTP port: {email_service.smtp_port}")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    """Run tests"""
    print("Me Feed Test Suite")
    print("=" * 30)
    
    tests = [
        ("Configuration", test_configuration),
        ("JWT Keys", test_jwt_keys),
        ("Secrets", test_secrets),
        ("Email Service", test_email_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            if test_func():
                print("   PASS")
                passed += 1
            else:
                print("   FAIL")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print(f"\nResults: {passed}/{total} passed")
    
    if passed == total:
        print("READY FOR PRODUCTION!")
    else:
        print("ISSUES FOUND")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
