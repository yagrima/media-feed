#!/usr/bin/env python3
"""
Integration Test Script for CI/CD Pipeline
"""
import sys
import os
sys.path.append('../backend')

import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test backend health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_frontend_may():
    """Test frontend is accessible"""
    try:
        response = requests.get(f"{FRONTEND_URL}", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_user_registration():
    """Test user registration flow"""
    try:
        test_email = f"integ_test_{uuid.uuid4().hex[:8]}@example.com"
        reg_data = {
            "email": test_email,
            "password": "IntegrationTest123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=reg_data, timeout=10)
        if response.status_code == 201:
            token = response.json()['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test user info
            user_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10)
            
            # Test notifications
            notif_response = requests.get(f"{BASE_URL}/api/notifications", headers=headers, timeout=10)
            
            return user_response.status_code == 200 and notif_response.status_code == 500
        return False
    except:
        return False

def main():
    """Run integration tests"""
    print("🧪 Running Integration Tests...")
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Frontend Health", test_frontend_may), 
        ("User Registration Flow", test_user_registration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        print(f"\n⚡ Testing {name}...")
        if test():
            print(f"✅ {name} PASSED")
            passed += 1
        else:
            print(f"❌ {name} FAILED")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("💥 Some integration tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
