"""
External database integration for CTF AI system.
Provides connectivity to free cloud database services for model storage.
"""

import os
import psycopg2
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ExternalDatabaseManager:
    """Manage external cloud database connections and operations"""
    
    def __init__(self):
        self.connection = None
        self.db_type = None
        self.connection_string = None
        
    def connect_supabase(self, connection_string):
        """Connect to Supabase PostgreSQL database"""
        try:
            # Parse the connection string
            parsed = urlparse(connection_string)
            
            self.connection = psycopg2.connect(
                host=parsed.hostname,
                database=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
                port=parsed.port or 5432,
                sslmode='require'  # Supabase requires SSL
            )
            
            self.db_type = 'supabase'
            self.connection_string = connection_string
            logger.info("Successfully connected to Supabase database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
    
    def connect_planetscale(self, connection_string):
        """Connect to PlanetScale MySQL database (alternative option)"""
        try:
            import mysql.connector
            from urllib.parse import parse_qs
            
            # Parse PlanetScale connection string
            parsed = urlparse(connection_string)
            query_params = parse_qs(parsed.query)
            
            self.connection = mysql.connector.connect(
                host=parsed.hostname,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                port=parsed.port or 3306,
                ssl_disabled=False
            )
            
            self.db_type = 'planetscale'
            self.connection_string = connection_string
            logger.info("Successfully connected to PlanetScale database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PlanetScale: {e}")
            return False
    
    def connect_neon(self, connection_string):
        """Connect to Neon PostgreSQL database (another free option)"""
        try:
            self.connection = psycopg2.connect(
                connection_string,
                sslmode='require'
            )
            
            self.db_type = 'neon'
            self.connection_string = connection_string
            logger.info("Successfully connected to Neon database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neon: {e}")
            return False
    
    def init_schema(self):
        """Initialize the database schema for model storage"""
        if not self.connection:
            raise Exception("No database connection established")
        
        cursor = self.connection.cursor()
        
        try:
            # Create models table
            if self.db_type in ['supabase', 'neon']:
                # PostgreSQL syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ctf_models (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        version VARCHAR(50) NOT NULL,
                        base_model VARCHAR(200) NOT NULL,
                        model_url VARCHAR(1000) NOT NULL,
                        config_data TEXT,
                        tokenizer_data TEXT,
                        training_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        training_completed TIMESTAMP,
                        training_duration FLOAT,
                        num_training_samples INTEGER,
                        num_validation_samples INTEGER,
                        accuracy FLOAT,
                        f1_score FLOAT,
                        exact_match FLOAT,
                        validation_loss FLOAT,
                        status VARCHAR(50) DEFAULT 'training',
                        is_active BOOLEAN DEFAULT FALSE,
                        download_count INTEGER DEFAULT 0,
                        file_size_mb FLOAT,
                        description TEXT,
                        training_config TEXT,
                        created_by VARCHAR(100) DEFAULT 'system',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create model files table for storing actual model binaries
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ctf_model_files (
                        id SERIAL PRIMARY KEY,
                        model_id INTEGER REFERENCES ctf_models(id) ON DELETE CASCADE,
                        file_name VARCHAR(500) NOT NULL,
                        file_type VARCHAR(50) NOT NULL,  -- 'model', 'config', 'tokenizer'
                        file_data BYTEA,
                        file_url VARCHAR(1000),  -- For external storage links
                        file_hash VARCHAR(64),  -- SHA256 hash for integrity
                        compressed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create training jobs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ctf_training_jobs (
                        id SERIAL PRIMARY KEY,
                        job_id VARCHAR(100) UNIQUE NOT NULL,
                        model_name VARCHAR(200) NOT NULL,
                        status VARCHAR(50) DEFAULT 'queued',
                        progress FLOAT DEFAULT 0.0,
                        current_step VARCHAR(200),
                        total_steps INTEGER,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        logs TEXT,
                        model_id INTEGER REFERENCES ctf_models(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create usage stats table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ctf_model_usage (
                        id SERIAL PRIMARY KEY,
                        model_id INTEGER REFERENCES ctf_models(id) NOT NULL,
                        query_count INTEGER DEFAULT 0,
                        total_response_time FLOAT DEFAULT 0.0,
                        successful_queries INTEGER DEFAULT 0,
                        failed_queries INTEGER DEFAULT 0,
                        average_response_time FLOAT DEFAULT 0.0,
                        success_rate FLOAT DEFAULT 0.0,
                        last_used TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
            elif self.db_type == 'planetscale':
                # MySQL syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ctf_models (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        version VARCHAR(50) NOT NULL,
                        base_model VARCHAR(200) NOT NULL,
                        model_url VARCHAR(1000) NOT NULL,
                        config_data TEXT,
                        tokenizer_data TEXT,
                        training_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        training_completed TIMESTAMP NULL,
                        training_duration FLOAT,
                        num_training_samples INT,
                        num_validation_samples INT,
                        accuracy FLOAT,
                        f1_score FLOAT,
                        exact_match FLOAT,
                        validation_loss FLOAT,
                        status VARCHAR(50) DEFAULT 'training',
                        is_active BOOLEAN DEFAULT FALSE,
                        download_count INT DEFAULT 0,
                        file_size_mb FLOAT,
                        description TEXT,
                        training_config TEXT,
                        created_by VARCHAR(100) DEFAULT 'system',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                ''')
            
            self.connection.commit()
            logger.info(f"Database schema initialized for {self.db_type}")
            return True
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            return False
        finally:
            cursor.close()
    
    def save_model(self, name, version, base_model, model_files, **kwargs):
        """Save a trained model to external database"""
        if not self.connection:
            raise Exception("No database connection established")
        
        cursor = self.connection.cursor()
        
        try:
            # Insert model metadata
            if self.db_type in ['supabase', 'neon']:
                cursor.execute('''
                    INSERT INTO ctf_models 
                    (name, version, base_model, model_url, config_data, tokenizer_data,
                     training_completed, training_duration, num_training_samples, num_validation_samples,
                     accuracy, f1_score, exact_match, validation_loss, status, description, training_config, file_size_mb)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    name, version, base_model, kwargs.get('model_url', ''),
                    kwargs.get('config_data'), kwargs.get('tokenizer_data'),
                    kwargs.get('training_completed'), kwargs.get('training_duration'),
                    kwargs.get('num_training_samples'), kwargs.get('num_validation_samples'),
                    kwargs.get('accuracy'), kwargs.get('f1_score'), kwargs.get('exact_match'),
                    kwargs.get('validation_loss'), kwargs.get('status', 'completed'),
                    kwargs.get('description'), json.dumps(kwargs.get('training_config', {})),
                    kwargs.get('file_size_mb', 0.0)
                ))
                
                model_id = cursor.fetchone()[0]
            
            # Save model files if provided
            if model_files and isinstance(model_files, dict):
                for file_type, file_data in model_files.items():
                    if isinstance(file_data, bytes):
                        cursor.execute('''
                            INSERT INTO ctf_model_files 
                            (model_id, file_name, file_type, file_data)
                            VALUES (%s, %s, %s, %s)
                        ''', (model_id, f"{name}_{file_type}", file_type, file_data))
            
            self.connection.commit()
            logger.info(f"Model {name} saved to external database with ID {model_id}")
            return model_id
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to save model: {e}")
            raise
        finally:
            cursor.close()
    
    def get_models(self, status=None, is_active=None, limit=50):
        """Get models from external database"""
        if not self.connection:
            raise Exception("No database connection established")
        
        cursor = self.connection.cursor()
        
        try:
            query = "SELECT * FROM ctf_models WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
                
            if is_active is not None:
                query += " AND is_active = %s"
                params.append(is_active)
                
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            models = [dict(zip(columns, row)) for row in rows]
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []
        finally:
            cursor.close()
    
    def get_model_file(self, model_id, file_type='model'):
        """Retrieve model file data from external database"""
        if not self.connection:
            raise Exception("No database connection established")
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute('''
                SELECT file_data, file_name, file_hash 
                FROM ctf_model_files 
                WHERE model_id = %s AND file_type = %s
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (model_id, file_type))
            
            result = cursor.fetchone()
            if result:
                return {
                    'data': result[0],
                    'filename': result[1],
                    'hash': result[2]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get model file: {e}")
            return None
        finally:
            cursor.close()
    
    def set_active_model(self, model_id):
        """Set a model as active"""
        if not self.connection:
            raise Exception("No database connection established")
        
        cursor = self.connection.cursor()
        
        try:
            # Deactivate all models
            cursor.execute("UPDATE ctf_models SET is_active = FALSE")
            
            # Activate specified model
            cursor.execute("UPDATE ctf_models SET is_active = TRUE WHERE id = %s", (model_id,))
            
            self.connection.commit()
            logger.info(f"Model {model_id} set as active")
            return True
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to set active model: {e}")
            return False
        finally:
            cursor.close()
    
    def update_usage_stats(self, model_id, response_time, success=True):
        """Update model usage statistics"""
        if not self.connection:
            return
        
        cursor = self.connection.cursor()
        
        try:
            # Check if stats exist
            cursor.execute("SELECT id FROM ctf_model_usage WHERE model_id = %s", (model_id,))
            stats_id = cursor.fetchone()
            
            if stats_id:
                # Update existing stats
                cursor.execute('''
                    UPDATE ctf_model_usage 
                    SET query_count = query_count + 1,
                        total_response_time = total_response_time + %s,
                        successful_queries = successful_queries + %s,
                        failed_queries = failed_queries + %s,
                        last_used = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE model_id = %s
                ''', (response_time, 1 if success else 0, 0 if success else 1, model_id))
                
                # Update calculated fields
                cursor.execute('''
                    UPDATE ctf_model_usage 
                    SET average_response_time = total_response_time / query_count,
                        success_rate = CAST(successful_queries AS FLOAT) / query_count
                    WHERE model_id = %s
                ''', (model_id,))
            else:
                # Create new stats
                cursor.execute('''
                    INSERT INTO ctf_model_usage 
                    (model_id, query_count, total_response_time, successful_queries, failed_queries,
                     average_response_time, success_rate, last_used)
                    VALUES (%s, 1, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ''', (model_id, response_time, 1 if success else 0, 0 if success else 1, 
                      response_time, 1.0 if success else 0.0))
            
            self.connection.commit()
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to update usage stats: {e}")
        finally:
            cursor.close()
    
    def test_connection(self):
        """Test the database connection"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

# Global external database manager instance
external_db = ExternalDatabaseManager()

def get_external_db():
    """Get the external database manager instance"""
    return external_db