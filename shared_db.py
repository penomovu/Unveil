"""
Shared database manager for CTF AI system
Single database used by all users, server-side training
"""

import os
import psycopg2
import json
import logging
from datetime import datetime
from config import SHARED_DATABASE_URL

logger = logging.getLogger(__name__)

class SharedDatabaseManager:
    """Manages the shared database for all users"""
    
    def __init__(self):
        self.db_url = SHARED_DATABASE_URL
        self.connection_failed = False
        
    def get_connection(self):
        """Get database connection with smart error handling"""
        if not self.db_url or self.connection_failed:
            return None
            
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            if not self.connection_failed:  # Only log the first failure
                logger.warning(f"Database connection failed, switching to fallback mode: {e}")
                self.connection_failed = True
            return None
    
    def init_db(self):
        """Initialize database or mark for fallback mode"""
        if not self.db_url:
            logger.info("No database URL configured, using fallback storage")
            return False
            
        conn = self.get_connection()
        if not conn:
            logger.info("Database connection failed, using fallback storage")
            return False
            
        try:
            # Test the connection and close it
            conn.close()
            return self.init_tables()
        except Exception as e:
            logger.warning(f"Database test failed: {e}")
            return False
    
    def init_tables(self):
        """Initialize all required tables"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # CTF Writeups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS writeups (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    url VARCHAR(1000),
                    category VARCHAR(100),
                    tags TEXT,
                    difficulty VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Shared models table - single model for all users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shared_models (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    version VARCHAR(50) NOT NULL,
                    model_type VARCHAR(100) NOT NULL,
                    model_data BYTEA,
                    config_data TEXT,
                    tokenizer_data BYTEA,
                    is_active BOOLEAN DEFAULT FALSE,
                    training_status VARCHAR(50) DEFAULT 'ready',
                    performance_metrics TEXT,
                    last_trained TIMESTAMP,
                    download_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Training jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_jobs (
                    id SERIAL PRIMARY KEY,
                    job_id VARCHAR(100) UNIQUE NOT NULL,
                    status VARCHAR(50) DEFAULT 'queued',
                    progress FLOAT DEFAULT 0.0,
                    current_step VARCHAR(200),
                    logs TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Usage statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id SERIAL PRIMARY KEY,
                    model_id INTEGER REFERENCES shared_models(id),
                    query_count INTEGER DEFAULT 0,
                    total_response_time FLOAT DEFAULT 0.0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")
            return False
    
    def save_writeup(self, title, content, source, url=None, category=None, tags=None, difficulty=None):
        """Save a writeup to shared database"""
        conn = self.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO writeups (title, content, source, url, category, tags, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (title, content, source, url, category, json.dumps(tags) if tags else None, difficulty))
            
            writeup_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return writeup_id
            
        except Exception as e:
            logger.error(f"Failed to save writeup: {e}")
            return None
    
    def get_writeups(self, limit=100):
        """Get writeups from shared database"""
        conn = self.get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM writeups ORDER BY created_at DESC LIMIT %s', (limit,))
            rows = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            writeups = [dict(zip(columns, row)) for row in rows]
            
            cursor.close()
            conn.close()
            return writeups
            
        except Exception as e:
            logger.error(f"Failed to get writeups: {e}")
            return []
    
    def save_model(self, name, version, model_type, model_data, config_data=None, tokenizer_data=None):
        """Save the shared model"""
        conn = self.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            
            # Deactivate all existing models first
            cursor.execute('UPDATE shared_models SET is_active = FALSE')
            
            # Insert new active model
            cursor.execute('''
                INSERT INTO shared_models 
                (name, version, model_type, model_data, config_data, tokenizer_data, is_active, last_trained)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                RETURNING id
            ''', (name, version, model_type, model_data, config_data, tokenizer_data))
            
            model_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return model_id
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return None
    
    def get_active_model(self):
        """Get the currently active shared model"""
        conn = self.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM shared_models WHERE is_active = TRUE ORDER BY created_at DESC LIMIT 1')
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                model = dict(zip(columns, row))
                cursor.close()
                conn.close()
                return model
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active model: {e}")
            return None
    
    def update_model_usage(self, model_id, response_time):
        """Update usage statistics"""
        conn = self.get_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            
            # Check if stats exist
            cursor.execute('SELECT id FROM usage_stats WHERE model_id = %s', (model_id,))
            if cursor.fetchone():
                cursor.execute('''
                    UPDATE usage_stats 
                    SET query_count = query_count + 1,
                        total_response_time = total_response_time + %s,
                        last_used = CURRENT_TIMESTAMP
                    WHERE model_id = %s
                ''', (response_time, model_id))
            else:
                cursor.execute('''
                    INSERT INTO usage_stats (model_id, query_count, total_response_time, last_used)
                    VALUES (%s, 1, %s, CURRENT_TIMESTAMP)
                ''', (model_id, response_time))
            
            # Update download count
            cursor.execute('UPDATE shared_models SET download_count = download_count + 1 WHERE id = %s', (model_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update usage stats: {e}")

# Global instance
shared_db = SharedDatabaseManager()