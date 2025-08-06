#!/usr/bin/env python3
"""
Environment setup script for CTF AI System
Sets up all required environment variables and secrets
"""

import os
import sys

def setup_environment():
    """Set up all required environment variables"""
    print("Setting up CTF AI System environment...")
    
    # Basic Flask Configuration
    os.environ['SECRET_KEY'] = 'ctf-ai-production-key-2025-secure-random-string'
    print("✓ SECRET_KEY configured")
    
    # Database Configuration - Use Replit's PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        os.environ['SHARED_DATABASE_URL'] = database_url
        print("✓ SHARED_DATABASE_URL configured using Replit PostgreSQL")
    else:
        print("⚠ DATABASE_URL not found - database features may not work")
    
    # Model Configuration
    os.environ['MODEL_NAME'] = 'CTF-AI-MockLarge'
    os.environ['MODEL_VERSION'] = 'v1.0'
    print("✓ Model configuration set")
    
    # System Configuration  
    os.environ['DEBUG'] = 'True'
    os.environ['HOST'] = '0.0.0.0'
    os.environ['PORT'] = '5000'
    print("✓ System configuration set")
    
    print("\n🎯 Environment setup complete!")
    print("Current configuration:")
    print(f"  - Database: {'✓ Connected' if database_url else '✗ Not available'}")
    print(f"  - Secret Key: {'✓ Set' if os.environ.get('SECRET_KEY') else '✗ Missing'}")
    print(f"  - Model: {os.environ.get('MODEL_NAME', 'Not set')}")
    print(f"  - Port: {os.environ.get('PORT', 'Not set')}")
    
    return True

if __name__ == "__main__":
    setup_environment()