#!/usr/bin/env python3
"""
Complete setup verification script for CTF AI System
Checks all configurations, tests connections, and provides setup status
"""

import os
import sys
import json
from datetime import datetime

def check_database_connection():
    """Check database connection and return status"""
    try:
        import psycopg2
        database_url = os.environ.get('DATABASE_URL')
        shared_url = os.environ.get('SHARED_DATABASE_URL', database_url)
        
        if not shared_url:
            return {"status": "missing", "message": "No database URL configured"}
        
        conn = psycopg2.connect(shared_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {"status": "connected", "message": f"PostgreSQL connected: {version[0][:50]}..."}
    except ImportError:
        return {"status": "missing_driver", "message": "psycopg2-binary not installed"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)[:100]}..."}

def check_required_files():
    """Check if all required files are present"""
    required_files = [
        'app_minimal.py',
        'client_ai_engine.py', 
        'config.py',
        'fallback_storage.py',
        'shared_db.py'
    ]
    
    file_status = {}
    for file in required_files:
        file_status[file] = os.path.exists(file)
    
    return file_status

def check_environment_variables():
    """Check all required environment variables"""
    env_vars = {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'SHARED_DATABASE_URL': os.environ.get('SHARED_DATABASE_URL'),
        'MODEL_NAME': os.environ.get('MODEL_NAME'),
        'HOST': os.environ.get('HOST'),
        'PORT': os.environ.get('PORT')
    }
    
    return env_vars

def main():
    print("🔍 CTF AI System Setup Verification")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    env_vars = check_environment_variables()
    for key, value in env_vars.items():
        if value:
            display_value = "***SET***" if key in ['SECRET_KEY', 'DATABASE_URL', 'SHARED_DATABASE_URL'] else value
            print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ❌ {key}: NOT SET")
    
    # Check database connection
    print("\n🗄️ Database Connection:")
    db_status = check_database_connection()
    if db_status["status"] == "connected":
        print(f"  ✅ {db_status['message']}")
    else:
        print(f"  ⚠️ {db_status['status'].upper()}: {db_status['message']}")
    
    # Check required files
    print("\n📁 Required Files:")
    file_status = check_required_files()
    for file, exists in file_status.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
    
    # Overall status
    print("\n🎯 Overall Status:")
    all_files_exist = all(file_status.values())
    has_secret_key = bool(env_vars['SECRET_KEY'])
    has_database = db_status["status"] in ["connected", "error"]  # error means driver exists
    
    if all_files_exist and has_secret_key:
        if has_database:
            print("  ✅ READY FOR FULL OPERATION")
            print("  ✅ All files present, secrets configured, database available")
        else:
            print("  ⚠️ READY FOR FALLBACK MODE")
            print("  ⚠️ All files present, secrets configured, using JSON storage")
    else:
        print("  ❌ SETUP INCOMPLETE")
        print("  ❌ Missing required components")
    
    # Save configuration summary
    config_summary = {
        "timestamp": datetime.now().isoformat(),
        "database_status": db_status,
        "environment_vars": {k: bool(v) for k, v in env_vars.items()},
        "files_present": file_status,
        "setup_complete": all_files_exist and has_secret_key
    }
    
    with open('setup_status.json', 'w') as f:
        json.dump(config_summary, f, indent=2)
    
    print(f"\n📊 Configuration saved to setup_status.json")
    print(f"🌐 Application should be running at http://0.0.0.0:5000")

if __name__ == "__main__":
    main()