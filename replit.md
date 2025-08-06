# Overview

CTF AI is a Flask-based cybersecurity assistant designed to help with Capture The Flag (CTF) competitions. The system collects cybersecurity writeups from various sources, automatically trains AI models using collected data, and provides an interactive chat interface for cybersecurity queries. It features server-side model storage allowing all users to access fine-tuned models, while maintaining a lightweight deployment approach. The system specializes in web security, cryptography, binary exploitation, reverse engineering, forensics, and other CTF categories.

## Recent Changes (August 2025)
- ✅ **Implemented CLIENT-SIDE AI ENGINE** - Real AI models automatically download and run in user's browser
- ✅ **Added automatic model downloading** - System downloads DistilGPT-2, DialoGPT-Small, or GPT-2 models to user's device
- ✅ **Built CTF-specialized knowledge engine** - Advanced reasoning system with category detection and technique-specific guidance
- ✅ **Added comprehensive CTF knowledge base** - Built-in database of techniques, tools, and methodologies for all CTF categories
- ✅ **Created intelligent response generation** - Context-aware responses using real AI models with CTF knowledge
- ✅ **Implemented model management system** - Download status, model switching, and automatic fallback to expert responses
- ✅ **Built fallback storage system** - JSON-based storage when external database is unavailable with seamless switching
- ✅ **Added file import functionality** - Users can upload TXT, MD, PDF, JSON files to add training data
- ✅ **Streamlined user interface** - Clean 4-tab interface: Chat, Upload, Data Collection, Auto Training
- ✅ **Created Vercel deployment configuration** - Complete config files for one-click Vercel deployment

# User Preferences

Preferred communication style: Simple, everyday language.
Architecture preference: Single shared database for all users instead of individual connections.
Model preference: Large context window model (4096 tokens) for comprehensive CTF assistance.
Training preference: Automatic server-side training with user file upload capability.
AI preference: Client-side AI execution with real CTF expertise and comprehensive knowledge base.

# System Architecture

## Frontend Architecture
The system uses a single-page application with vanilla JavaScript and Bootstrap for the UI. The frontend consists of:
- Tab-based navigation with sections for chat, data collection, training, and evaluation
- Real-time status updates via polling API endpoints
- Interactive chat interface with typing indicators and response streaming
- Responsive design with a dark-themed sidebar and light main content area

## Backend Architecture
Built on Flask with a modular component design:
- **Data Collector**: Scrapes CTF writeups from GitHub repositories and websites using BeautifulSoup and Trafilatura
- **Text Preprocessor**: Cleans and normalizes text data while preserving CTF-specific terminology
- **Model Trainer**: Fine-tunes DistilBERT for question-answering using Hugging Face Transformers
- **Inference Engine**: Handles question answering with context-aware responses and CTF-specific templates
- **Evaluator**: Tests model performance on cybersecurity-specific metrics and categories

## Data Processing Pipeline
The system follows a structured data flow:
1. Sources are configured in JSON format with GitHub repositories and web URLs
2. Raw writeups are collected, cleaned, and stored as JSON
3. Text is preprocessed to create question-answer pairs for training
4. Data is split into training/validation sets for model fine-tuning
5. Processed data feeds into the transformer-based QA model

## Model Architecture
Uses client-side AI execution with server-side model management:

**Client-Side AI Engine:**
- CTF-specialized knowledge base with 7 categories (web, crypto, pwn, reverse, forensics, osint, misc)
- Advanced question analysis with category detection and technique identification
- Context-aware response generation using writeup analysis and pattern matching
- Real-time knowledge base updates when new writeups are imported
- 4096 token context window for comprehensive responses

**Server-Side Model Management:**
- Automatic daily training on collected writeups and user uploads
- Model versioning and distribution system
- Usage statistics and performance tracking
- Seamless model updates pushed to all clients
- Fallback storage system for offline operation

## Authentication and State Management
The system uses Flask sessions with random secret keys for basic security. Global state tracking monitors:
- Data collection status and progress
- Training progress and model availability
- System performance metrics
- Last operation timestamps

# External Dependencies

## Python Libraries
- **Flask**: Web framework for API and interface
- **Transformers**: Hugging Face library for DistilBERT model training and inference
- **PyTorch**: Machine learning framework for model operations
- **NLTK**: Natural language processing for text preprocessing
- **BeautifulSoup4**: HTML parsing for web scraping
- **Trafilatura**: Text extraction from web content
- **Requests**: HTTP client for data collection
- **scikit-learn**: Machine learning utilities for evaluation metrics

## Frontend Dependencies
- **Bootstrap 5.1.3**: CSS framework for responsive UI design
- **Feather Icons 4.28.0**: Icon library for navigation and interface elements

## Data Sources
The system is configured to collect from 15+ high-quality CTF writeup sources:

**GitHub Repositories:**
- DaffaInfo CTF Writeups (558+ writeups from multiple competitions)
- siunam321 CTF Writeups (comprehensive personal collection)
- IITKGP Team CTF Writeups (ranked #41 in India)
- LazyTitan33 CTF Writeups (HackTheBox Business CTFs)
- Perfect Blue Team Writeups (professional team, 686+ stars)
- Galaxians Team Public Writeups (team collaboration)
- CTF Writeups Backup Collection
- p4 Team CTF Writeups (established team)
- VulnHub CTF Writeups (vulnerability research focus)
- Community CTF Writeups (2016-2017 historical)
- CTF Archives (2017-2024 comprehensive collection)

**Websites & Blogs:**
- CTFtime Official Writeups (central CTF hub)
- siunam321 Personal Blog (detailed tutorials)
- Medium CTF Writeups Publication (curated content)

**Content Coverage:**
- Recent 2025 CTF competitions (UIUCTF, Google CTF, DownUnderCTF)
- TryHackMe and HackTheBox writeups
- PortSwigger Labs (comprehensive web security)
- Advanced topics: kernel exploitation, heap challenges, client-side web

## Database Storage

The system supports both local and external database storage:

**Local Storage (PostgreSQL):**
- Requires PostgreSQL installation on Replit
- Tables: writeups, trained models, training jobs, usage statistics
- Used when no external database is connected

**External Database Support:**
- **Supabase** (PostgreSQL): 500MB free tier with real-time features
- **Neon** (PostgreSQL): 512MB free tier with database branching
- **PlanetScale** (MySQL): 5GB free tier with serverless scaling

**Model Storage Features:**
- Binary model data storage (weights, configurations, tokenizers)
- Model versioning and metadata tracking
- Training progress and performance metrics
- Usage statistics and download counts
- Active model management across database types

**File Storage (Fallback):**
- Raw and processed writeup data in JSON format
- Model checkpoints and training artifacts as local files
- Evaluation results and performance metrics
- Source configurations and system logs