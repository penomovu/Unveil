# Overview

CTF AI is a Flask-based cybersecurity assistant designed to help with Capture The Flag (CTF) competitions. The system collects cybersecurity writeups from various sources, trains a question-answering model using transformer architecture, and provides an interactive chat interface for cybersecurity queries. It specializes in web security, cryptography, binary exploitation, reverse engineering, forensics, and other CTF categories.

# User Preferences

Preferred communication style: Simple, everyday language.

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
Uses a lightweight approach optimized for CPU training:
- Base model: DistilBERT (distilbert-base-uncased-distilled-squad)
- Task: Question-answering with extractive approach
- Training: Custom dataset class with tokenization and answer span detection
- Inference: Pipeline-based QA with confidence scoring and response templates

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

## File Storage
All data is stored locally in JSON format:
- Raw and processed writeup data
- Model checkpoints and training artifacts
- Evaluation results and performance metrics
- Source configurations and system logs