# CTF AI System - Complete Setup Guide

## 🎯 Current Status
- **Application**: ✅ RUNNING on port 5000
- **Database**: ⚠️ Using fallback JSON storage
- **Security**: ✅ Configured with secret keys
- **AI Model**: ✅ CTF-AI-MockLarge v1.0 active
- **Client AI**: ✅ 4096 token context window

## 🚀 Quick Start
The system is already configured and running! Access it at:
- **Local**: http://127.0.0.1:5000
- **Public**: http://172.31.115.2:5000

## 🔧 Configuration Files

### 1. secrets.txt
Contains all environment variables and configuration secrets:
- SECRET_KEY: ✅ Configured
- DATABASE_URL: ✅ Available (Replit PostgreSQL)
- Model settings: ✅ CTF-AI-MockLarge v1.0

### 2. setup_environment.py
Script to configure environment variables manually if needed.

### 3. start_ctf_ai.py
Main startup script that:
- Sets up environment variables
- Configures database connections
- Starts the Flask application

## 📊 System Architecture

### Database Configuration
- **Primary**: Replit PostgreSQL (DATABASE_URL available)
- **Current Mode**: Fallback JSON storage
- **Reason**: Socket connection method preference
- **Data Storage**: Local JSON files in `data/` directory

### AI Model Configuration
- **Model**: CTF-AI-MockLarge v1.0
- **Context Window**: 4096 tokens
- **Execution**: Client-side processing
- **Knowledge Base**: 6 CTF writeups loaded

### Security Configuration
- **Secret Key**: Secure random string (production-ready)
- **Debug Mode**: Enabled for development
- **Host**: 0.0.0.0 (accessible from all interfaces)
- **Port**: 5000 (only open port on Replit)

## 🎮 Features Available

### 1. Chat Interface
Interactive CTF assistant with:
- Category detection (web, crypto, pwn, reverse, forensics, osint, misc)
- Technique-specific guidance
- Context-aware responses

### 2. File Upload
Upload training materials:
- TXT, MD, PDF, JSON files
- Max file size: 10MB
- Automatic knowledge base updates

### 3. Data Collection
Automatic collection from sources:
- GitHub CTF writeup repositories
- CTFtime writeups
- Personal CTF blogs

### 4. Auto Training
Server-side model training:
- Daily automatic training
- Uses collected writeups and uploads
- Model versioning and distribution

## 🔧 Maintenance Commands

### Start System
```bash
python start_ctf_ai.py
```

### Check Status
```bash
python setup_complete.py
```

### Environment Setup
```bash
python setup_environment.py
```

## 🐛 Troubleshooting

### Database Connection Issues
- System automatically falls back to JSON storage
- Data persists in `data/` directory
- No functionality loss in fallback mode

### Port Conflicts
- Only port 5000 is available on Replit
- System automatically handles port management
- Check workflow status if conflicts occur

### Environment Variables
- Variables are set programmatically in start_ctf_ai.py
- No need to manually export in shell
- Configuration persists across restarts

## 📚 Additional Resources

- **Main App**: `app_minimal.py` - Core Flask application
- **AI Engine**: `client_ai_engine.py` - CTF-specialized AI processing
- **Database**: `shared_db.py` - Database abstraction layer
- **Storage**: `fallback_storage.py` - JSON-based fallback storage
- **Config**: `config.py` - System configuration settings

## 🎯 Next Steps

1. **Access Application**: Visit http://127.0.0.1:5000
2. **Test Chat**: Ask CTF-related questions
3. **Upload Files**: Add your own writeups or training data
4. **Monitor Status**: Check system logs for performance

The system is fully operational and ready for CTF assistance!