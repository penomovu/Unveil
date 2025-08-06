"""
Database models for the CTF AI system.
Stores writeups, trained models, and metadata server-side.
"""

import os
import psycopg2
from datetime import datetime
import json

# Database connection utility
def get_db_connection():
    """Get a PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.environ.get('PGHOST'),
        database=os.environ.get('PGDATABASE'), 
        user=os.environ.get('PGUSER'),
        password=os.environ.get('PGPASSWORD'),
        port=os.environ.get('PGPORT')
    )

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ctf_writeups (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            source VARCHAR(100) NOT NULL,
            url VARCHAR(1000),
            category VARCHAR(100),
            tags TEXT,
            difficulty VARCHAR(50),
            collected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trained_models (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            version VARCHAR(50) NOT NULL,
            base_model VARCHAR(200) NOT NULL,
            model_path VARCHAR(500) NOT NULL,
            config_path VARCHAR(500),
            tokenizer_path VARCHAR(500),
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
            description TEXT,
            training_config TEXT,
            created_by VARCHAR(100) DEFAULT 'system'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_jobs (
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
            trained_model_id INTEGER REFERENCES trained_models(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_usage_stats (
            id SERIAL PRIMARY KEY,
            model_id INTEGER REFERENCES trained_models(id) NOT NULL,
            query_count INTEGER DEFAULT 0,
            total_response_time FLOAT DEFAULT 0.0,
            successful_queries INTEGER DEFAULT 0,
            failed_queries INTEGER DEFAULT 0,
            average_response_time FLOAT,
            success_rate FLOAT,
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

class DatabaseManager:
    """Manage database operations for CTF writeups and models"""
    
    @staticmethod
    def save_writeup(title, content, source, url=None, category=None, tags=None, difficulty=None):
        """Save a writeup to the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ctf_writeups (title, content, source, url, category, tags, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (title, content, source, url, category, json.dumps(tags) if tags else None, difficulty))
        
        writeup_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return writeup_id
    
    @staticmethod
    def get_writeups(limit=None, category=None, processed=None):
        """Get writeups from the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM ctf_writeups WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
            
        if processed is not None:
            query += " AND processed = %s"
            params.append(processed)
            
        query += " ORDER BY collected_date DESC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        writeups = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        return writeups
    
    @staticmethod
    def save_model(name, version, base_model, model_path, **kwargs):
        """Save a trained model to the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trained_models 
            (name, version, base_model, model_path, config_path, tokenizer_path, 
             training_completed, training_duration, num_training_samples, num_validation_samples,
             accuracy, f1_score, exact_match, validation_loss, status, description, training_config)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            name, version, base_model, model_path,
            kwargs.get('config_path'), kwargs.get('tokenizer_path'),
            kwargs.get('training_completed'), kwargs.get('training_duration'),
            kwargs.get('num_training_samples'), kwargs.get('num_validation_samples'),
            kwargs.get('accuracy'), kwargs.get('f1_score'), kwargs.get('exact_match'),
            kwargs.get('validation_loss'), kwargs.get('status', 'completed'),
            kwargs.get('description'), json.dumps(kwargs.get('training_config', {}))
        ))
        
        model_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return model_id
    
    @staticmethod
    def get_models(status=None, is_active=None):
        """Get trained models from the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM trained_models WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
            
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active)
            
        query += " ORDER BY training_completed DESC NULLS LAST"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        models = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        return models
    
    @staticmethod
    def set_active_model(model_id):
        """Set a model as the active one"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, deactivate all models
        cursor.execute("UPDATE trained_models SET is_active = FALSE")
        
        # Then activate the specified model
        cursor.execute("UPDATE trained_models SET is_active = TRUE WHERE id = %s", (model_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def update_usage_stats(model_id, response_time, success=True):
        """Update usage statistics for a model"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if stats exist for this model
        cursor.execute("SELECT id FROM model_usage_stats WHERE model_id = %s", (model_id,))
        stats_id = cursor.fetchone()
        
        if stats_id:
            # Update existing stats
            cursor.execute('''
                UPDATE model_usage_stats 
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
                UPDATE model_usage_stats 
                SET average_response_time = total_response_time / query_count,
                    success_rate = CAST(successful_queries AS FLOAT) / query_count
                WHERE model_id = %s
            ''', (model_id,))
        else:
            # Create new stats
            cursor.execute('''
                INSERT INTO model_usage_stats 
                (model_id, query_count, total_response_time, successful_queries, failed_queries,
                 average_response_time, success_rate, last_used)
                VALUES (%s, 1, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ''', (model_id, response_time, 1 if success else 0, 0 if success else 1, 
                  response_time, 1.0 if success else 0.0))
        
        conn.commit()
        cursor.close()
        conn.close()

class CTFWriteup(db.Model):
    """Store CTF writeups in the database"""
    __tablename__ = 'ctf_writeups'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100), nullable=False)  # 'github', 'website', etc.
    url = db.Column(db.String(1000))
    category = db.Column(db.String(100))  # 'web', 'crypto', 'pwn', etc.
    tags = db.Column(db.Text)  # JSON string of tags
    difficulty = db.Column(db.String(50))  # 'easy', 'medium', 'hard'
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'url': self.url,
            'category': self.category,
            'tags': json.loads(self.tags) if self.tags else [],
            'difficulty': self.difficulty,
            'collected_date': self.collected_date.isoformat() if self.collected_date else None,
            'processed': self.processed
        }

class TrainedModel(db.Model):
    """Store trained AI models and their metadata"""
    __tablename__ = 'trained_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    base_model = db.Column(db.String(200), nullable=False)  # e.g., 'distilbert-base-uncased'
    model_path = db.Column(db.String(500), nullable=False)  # Path to saved model
    config_path = db.Column(db.String(500))  # Path to model config
    tokenizer_path = db.Column(db.String(500))  # Path to tokenizer
    
    # Training metadata
    training_started = db.Column(db.DateTime, default=datetime.utcnow)
    training_completed = db.Column(db.DateTime)
    training_duration = db.Column(db.Float)  # In seconds
    num_training_samples = db.Column(db.Integer)
    num_validation_samples = db.Column(db.Integer)
    
    # Performance metrics
    accuracy = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    exact_match = db.Column(db.Float)
    validation_loss = db.Column(db.Float)
    
    # Model status
    status = db.Column(db.String(50), default='training')  # 'training', 'completed', 'failed', 'active'
    is_active = db.Column(db.Boolean, default=False)  # Currently loaded model
    download_count = db.Column(db.Integer, default=0)
    
    # Additional metadata
    description = db.Column(db.Text)
    training_config = db.Column(db.Text)  # JSON string of training parameters
    created_by = db.Column(db.String(100), default='system')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'base_model': self.base_model,
            'model_path': self.model_path,
            'training_started': self.training_started.isoformat() if self.training_started else None,
            'training_completed': self.training_completed.isoformat() if self.training_completed else None,
            'training_duration': self.training_duration,
            'num_training_samples': self.num_training_samples,
            'num_validation_samples': self.num_validation_samples,
            'accuracy': self.accuracy,
            'f1_score': self.f1_score,
            'exact_match': self.exact_match,
            'validation_loss': self.validation_loss,
            'status': self.status,
            'is_active': self.is_active,
            'download_count': self.download_count,
            'description': self.description,
            'training_config': json.loads(self.training_config) if self.training_config else {},
            'created_by': self.created_by
        }

class TrainingJob(db.Model):
    """Track training jobs and their progress"""
    __tablename__ = 'training_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False)
    model_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='queued')  # 'queued', 'running', 'completed', 'failed'
    progress = db.Column(db.Float, default=0.0)  # 0-100
    current_step = db.Column(db.String(200))
    total_steps = db.Column(db.Integer)
    
    # Job metadata
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    logs = db.Column(db.Text)  # Training logs
    
    # Results
    trained_model_id = db.Column(db.Integer, db.ForeignKey('trained_models.id'))
    trained_model = db.relationship('TrainedModel', backref='training_job')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'model_name': self.model_name,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'trained_model_id': self.trained_model_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ModelUsageStats(db.Model):
    """Track model usage statistics"""
    __tablename__ = 'model_usage_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('trained_models.id'), nullable=False)
    model = db.relationship('TrainedModel', backref='usage_stats')
    
    # Usage metrics
    query_count = db.Column(db.Integer, default=0)
    total_response_time = db.Column(db.Float, default=0.0)  # Total time in seconds
    successful_queries = db.Column(db.Integer, default=0)
    failed_queries = db.Column(db.Integer, default=0)
    
    # Performance tracking
    average_response_time = db.Column(db.Float)
    success_rate = db.Column(db.Float)
    
    # Time tracking
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_stats(self, response_time, success=True):
        """Update usage statistics"""
        self.query_count += 1
        self.total_response_time += response_time
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
            
        self.average_response_time = self.total_response_time / self.query_count
        self.success_rate = self.successful_queries / self.query_count
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
    def to_dict(self):
        return {
            'id': self.id,
            'model_id': self.model_id,
            'query_count': self.query_count,
            'average_response_time': self.average_response_time,
            'success_rate': self.success_rate,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }