#!/usr/bin/env python3
"""
Test script to verify the authentication flow works correctly
"""

import requests
import json

# Test the complete authentication flow
def test_auth_flow():
    base_url = "http://localhost:8000/v1"
    
    print("🔍 Testing Authentication Flow...")
    print("=" * 50)
    
    # Test 1: Check if backend is running
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend not responding")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test 2: Test email registration
    print("\n📝 Testing Email Registration...")
    try:
        response = requests.post(
            f"{base_url}/auth/email/register",
            json={
                "email": "testuser@example.com",
                "password": "password123",
                "username": "testuser",
                "name": "Test User"
            }
        )
        if response.status_code == 200:
            print("✅ Email registration works")
            data = response.json()
            print(f"   User created: {data.get('user', {}).get('login', 'Unknown')}")
        else:
            print(f"❌ Email registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Email registration error: {e}")
    
    # Test 3: Test email login
    print("\n🔐 Testing Email Login...")
    try:
        response = requests.post(
            f"{base_url}/auth/email/login",
            json={
                "email": "testuser@example.com",
                "password": "password123"
            }
        )
        if response.status_code == 200:
            print("✅ Email login works")
            data = response.json()
            print(f"   User logged in: {data.get('user', {}).get('login', 'Unknown')}")
        else:
            print(f"❌ Email login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Email login error: {e}")
    
    # Test 4: Test GitHub OAuth
    print("\n🐙 Testing GitHub OAuth...")
    try:
        response = requests.get(f"{base_url}/auth/github/login")
        if response.status_code == 200:
            print("✅ GitHub OAuth login URL generated")
            data = response.json()
            print(f"   Login URL: {data.get('login_url', 'Unknown')[:50]}...")
        else:
            print(f"❌ GitHub OAuth failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ GitHub OAuth error: {e}")
    
    # Test 5: Test /auth/me endpoint
    print("\n👤 Testing /auth/me endpoint...")
    try:
        response = requests.get(f"{base_url}/auth/me")
        if response.status_code == 401:
            print("✅ /auth/me endpoint exists (returns 401 when not authenticated)")
        else:
            print(f"❌ /auth/me endpoint issue: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ /auth/me endpoint error: {e}")
    
    # Test 6: Test team member pages
    print("\n👥 Testing Team Member Pages...")
    try:
        response = requests.get(f"{base_url}/member/5/summary")
        if response.status_code == 200:
            print("✅ Team member pages work")
            data = response.json()
            print(f"   User: {data.get('user', {}).get('username', 'Unknown')}")
        else:
            print(f"❌ Team member pages failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Team member pages error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Authentication Flow Test Complete!")

if __name__ == "__main__":
    test_auth_flow()
