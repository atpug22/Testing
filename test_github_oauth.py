#!/usr/bin/env python3
"""
Test script to verify GitHub OAuth configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_github_oauth():
    print("🔍 Testing GitHub OAuth Configuration...")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please create .env file with your GitHub OAuth credentials")
        return False
    
    # Load environment variables
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    print(f"📁 .env file: ✅ Found")
    print(f"🔑 GITHUB_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
    print(f"🔐 GITHUB_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Not set'}")
    
    if not client_id or not client_secret:
        print("\n❌ GitHub OAuth not properly configured!")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://github.com/settings/applications/new")
        print("2. Create OAuth App with:")
        print("   - Name: LogPose")
        print("   - Homepage: http://localhost:3000")
        print("   - Callback: http://localhost:8000/v1/auth/github/callback")
        print("3. Copy Client ID and Client Secret to .env file")
        return False
    
    # Test OAuth URL generation
    try:
        from app.integrations.github_oauth import build_oauth_login_url, generate_state
        state = generate_state()
        login_url = build_oauth_login_url(state)
        print(f"\n🔗 OAuth URL: ✅ Generated successfully")
        print(f"🌐 Login URL: {login_url}")
        return True
    except Exception as e:
        print(f"\n❌ Error generating OAuth URL: {e}")
        return False

if __name__ == "__main__":
    success = test_github_oauth()
    if success:
        print("\n🎉 GitHub OAuth is properly configured!")
        print("🚀 You can now test the login flow at http://localhost:3000")
    else:
        print("\n⚠️  Please fix the configuration issues above")
