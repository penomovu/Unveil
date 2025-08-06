#!/usr/bin/env python3
"""
Startup script that sets environment variables and runs the CTF AI system
"""

import os
import subprocess
import sys

def setup_environment():
    """Set up all required environment variables"""
    print("🚀 Starting CTF AI System...")
    
    # Basic Flask Configuration
    os.environ['SECRET_KEY'] = 'ctf-ai-production-key-2025-secure-random-string'
    
    # Database Configuration - Use Replit's PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        os.environ['SHARED_DATABASE_URL'] = database_url
        print("✅ Database connected")
    else:
        print("⚠️ Using fallback mode (no database)")
    
    # Model Configuration
    os.environ['MODEL_NAME'] = 'CTF-AI-MockLarge'
    os.environ['MODEL_VERSION'] = 'v1.0'
    
    # System Configuration  
    os.environ['DEBUG'] = 'True'
    os.environ['HOST'] = '0.0.0.0'
    os.environ['PORT'] = '5000'
    
    print("✅ Environment configured")

if __name__ == "__main__":
    setup_environment()
    
    # Import and run the application
    try:
        from app_minimal import app
        print("✅ Loading CTF AI application...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        sys.exit(1)