"""
Configuration settings for the CTF AI system.
"""

import os
from datetime import datetime

class Config:
    # Model configuration
    MODEL_NAME = "distilbert-base-uncased-distilled-squad"  # Lightweight QA model
    MODEL_SAVE_PATH = "models/ctf_ai_model"
    
    # Data paths
    DATA_DIR = "data"
    SOURCES_FILE = "data/sources.json"
    RAW_DATA_PATH = "data/raw_writeups.json"
    PROCESSED_DATA_PATH = "data/processed_writeups.json"
    EVALUATION_RESULTS_PATH = "data/evaluation_results.json"
    
    # Training configuration
    MAX_LENGTH = 512
    BATCH_SIZE = 4
    LEARNING_RATE = 3e-5
    NUM_EPOCHS = 3
    WARMUP_STEPS = 100
    
    # Data collection settings
    MAX_WRITEUPS_PER_SOURCE = 100
    MIN_CONTENT_LENGTH = 100  # Minimum content length in characters
    COLLECTION_DELAY = 1  # Delay between requests in seconds
    
    # Inference settings
    MAX_ANSWER_LENGTH = 200
    CONTEXT_WINDOW = 1000
    CONFIDENCE_THRESHOLD = 0.3
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/ctf_ai.log"
    
    @staticmethod
    def get_timestamp():
        """Get current timestamp string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def ensure_directories():
        """Ensure all necessary directories exist."""
        directories = [
            Config.DATA_DIR,
            "models",
            "logs",
            os.path.dirname(Config.MODEL_SAVE_PATH)
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

# Environment-specific configurations
class DevelopmentConfig(Config):
    DEBUG = True
    MAX_WRITEUPS_PER_SOURCE = 10  # Smaller dataset for development

class ProductionConfig(Config):
    DEBUG = False
    MAX_WRITEUPS_PER_SOURCE = 1000

# Select configuration based on environment
config_name = os.getenv('FLASK_ENV', 'development')
if config_name == 'production':
    config = ProductionConfig
else:
    config = DevelopmentConfig
