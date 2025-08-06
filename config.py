"""
Configuration for CTF AI system with shared database
"""

import os

# Shared database configuration (server-side)
# Use a free external database service like Supabase, Neon, or PlanetScale
SHARED_DATABASE_URL = os.environ.get('SHARED_DATABASE_URL', 
    # Default to local PostgreSQL if available
    f'postgresql://{os.environ.get("PGUSER", "postgres")}:{os.environ.get("PGPASSWORD", "password")}@{os.environ.get("PGHOST", "localhost")}:{os.environ.get("PGPORT", "5432")}/{os.environ.get("PGDATABASE", "ctfai")}'
)

# Model configuration with large context window
MODEL_CONFIG = {
    'base_model': 'microsoft/DialoGPT-large',  # Large context window model
    'max_length': 4096,  # Large context window
    'training_enabled': True,
    'auto_train': True,  # Automatic training
    'training_interval': 24 * 60 * 60,  # Train daily (in seconds)
}

# Data collection sources
DATA_SOURCES = [
    {
        'type': 'github',
        'url': 'https://github.com/DaffaInfo/ctf-writeup',
        'name': 'DaffaInfo CTF Writeups'
    },
    {
        'type': 'github', 
        'url': 'https://github.com/siunam321/siunam321.github.io',
        'name': 'siunam321 CTF Writeups'
    },
    {
        'type': 'website',
        'url': 'https://ctftime.org/writeups',
        'name': 'CTFtime Writeups'
    }
]

# File upload configuration
UPLOAD_CONFIG = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': {'.txt', '.md', '.pdf', '.json'},
    'upload_folder': 'uploads'
}

# System settings
SYSTEM_CONFIG = {
    'debug': True,
    'host': '0.0.0.0',
    'port': 5000,
    'secret_key': os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
}