"""
Minimal CTF AI with shared database, file imports, and mock large context model
"""

import os
import json
import logging
import time
import threading
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename

from config import UPLOAD_CONFIG, SYSTEM_CONFIG, DATA_SOURCES
from shared_db import shared_db
from simple_data_collector import SimpleDataCollector
from fallback_storage import fallback_storage
from local_ai_engine import local_ai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SYSTEM_CONFIG['secret_key']

# Global variables
model_loaded = False
training_in_progress = False
last_training_check = datetime.now()
use_fallback_storage = False

# Mock Large Context Model (simulates DialoGPT-Large with 4096 token context)
class MockLargeContextModel:
    """Mock implementation of a large context window model"""
    
    def __init__(self):
        self.context_window = 4096
        self.model_name = "MockDialoGPT-Large-4K"
        self.knowledge_base = []
        
    def load_knowledge(self, writeups):
        """Load writeups into the mock knowledge base"""
        self.knowledge_base = writeups[:100]  # Limit for demo
        logger.info(f"Loaded {len(self.knowledge_base)} writeups into knowledge base")
        
    def generate_response(self, question, context=""):
        """Generate a response based on the question and context"""
        # Simulate processing time
        time.sleep(random.uniform(0.5, 1.5))
        
        # Look for relevant content in knowledge base
        relevant_content = self._find_relevant_content(question)
        
        if relevant_content:
            # Generate response based on relevant content
            response = self._generate_ctf_response(question, relevant_content)
        else:
            # Fallback responses
            response = self._generate_fallback_response(question)
            
        return response
    
    def _find_relevant_content(self, question):
        """Find relevant content from knowledge base"""
        question_lower = question.lower()
        keywords = ['ctf', 'exploit', 'vulnerability', 'hack', 'security', 'crypto', 'web', 'pwn', 'reverse', 'forensics']
        
        # Simple keyword matching
        for writeup in self.knowledge_base:
            content_lower = writeup.get('content', '').lower()
            title_lower = writeup.get('title', '').lower()
            category_lower = writeup.get('category', '').lower()
            
            # Check if question keywords match content
            if any(keyword in question_lower for keyword in keywords):
                if any(keyword in content_lower or keyword in title_lower or keyword in category_lower 
                       for keyword in question_lower.split()):
                    return writeup
        
        return None
    
    def _generate_ctf_response(self, question, relevant_content):
        """Generate response based on relevant CTF content"""
        category = relevant_content.get('category', 'CTF')
        title = relevant_content.get('title', 'Unknown Challenge')
        content = relevant_content.get('content', '')[:500]  # Limit content length
        
        responses = [
            f"Based on similar {category} challenges like '{title}', here's what I recommend:\n\n{content}",
            f"I found a related {category} writeup that might help. In '{title}', the approach was:\n\n{content}",
            f"Looking at {category} challenges, particularly '{title}', you should consider:\n\n{content}",
            f"From my analysis of {category} challenges including '{title}', here's the solution approach:\n\n{content}"
        ]
        
        return random.choice(responses)
    
    def _generate_fallback_response(self, question):
        """Generate fallback responses for questions without specific matches"""
        fallback_responses = [
            "I'd be happy to help with your CTF challenge! Could you provide more specific details about the challenge type (web, crypto, pwn, etc.) and what you've tried so far?",
            "This looks like an interesting CTF problem. To give you the best guidance, can you share more context about the challenge category and any error messages or clues you have?",
            "CTF challenges can be tricky! Let me know more about the specific vulnerability type or challenge category, and I'll provide more targeted advice.",
            "I have knowledge of various CTF techniques including web exploitation, cryptography, binary analysis, and more. Could you be more specific about what type of challenge you're working on?",
            "Based on my training data from thousands of CTF writeups, I can help with web security, crypto challenges, reverse engineering, and forensics. What specific area would you like assistance with?"
        ]
        
        return random.choice(fallback_responses)

# Global model instance
mock_model = MockLargeContextModel()

class AutoTrainer:
    """Handles automatic model training with mock implementation"""
    
    def __init__(self):
        self.training_active = False
        
    def should_train(self):
        """Check if we should start training"""
        global last_training_check
        
        # Check if enough time has passed (daily training)
        if datetime.now() - last_training_check < timedelta(hours=24):
            return False
            
        # Check if we have enough new data
        writeups = shared_db.get_writeups(limit=10)
        return len(writeups) >= 5
        
    def start_training(self):
        """Start automatic training in background"""
        if self.training_active:
            return False
            
        self.training_active = True
        thread = threading.Thread(target=self._train_model)
        thread.daemon = True
        thread.start()
        return True
        
    def _train_model(self):
        """Mock training process"""
        global training_in_progress, last_training_check, model_loaded
        
        try:
            training_in_progress = True
            logger.info("Starting mock model training...")
            
            # Get training data
            if use_fallback_storage:
                writeups = fallback_storage.get_writeups(limit=1000)
            else:
                writeups = shared_db.get_writeups(limit=1000)
            if len(writeups) < 5:
                logger.warning("Not enough data for training")
                return
                
            logger.info(f"Training on {len(writeups)} writeups")
            
            # Mock training process (simulate 30 seconds of training)
            for i in range(6):
                time.sleep(5)
                logger.info(f"Training progress: {(i+1)*20}%")
            
            # Update local AI knowledge (handled automatically by model loading)
            
            # Save model metadata to database or fallback
            config_data = json.dumps({
                'base_model': 'MockDialoGPT-Large-4K',
                'context_window': 4096,
                'training_data_count': len(writeups),
                'trained_at': datetime.now().isoformat()
            })
            
            model_bytes = json.dumps({'model_type': 'mock', 'writeup_count': len(writeups)}).encode('utf-8')
            
            if use_fallback_storage:
                fallback_storage.save_model(
                    name="CTF-AI-MockLarge",
                    version=f"v{int(time.time())}",
                    model_type="MockDialoGPT-Large-4K",
                    model_data=model_bytes,
                    config_data=config_data
                )
            else:
                shared_db.save_model(
                    name="CTF-AI-MockLarge",
                    version=f"v{int(time.time())}",
                    model_type="MockDialoGPT-Large-4K",
                    model_data=model_bytes,
                    config_data=config_data
                )
            
            logger.info("Mock model training completed successfully")
            last_training_check = datetime.now()
            model_loaded = True
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
        finally:
            training_in_progress = False
            self.training_active = False

# Global trainer instance
auto_trainer = AutoTrainer()

def load_active_model():
    """Load the active model from database"""
    global model_loaded
    
    try:
        if use_fallback_storage:
            model_data = fallback_storage.get_active_model()
            writeups = fallback_storage.get_writeups(limit=100)
        else:
            model_data = shared_db.get_active_model()
            writeups = shared_db.get_writeups(limit=100)
            
        if not model_data:
            logger.warning("No active model found")
            return False
            
        logger.info(f"Loading model: {model_data['name']} v{model_data['version']}")
        
        # Load model into local AI engine  
        success = local_ai.load_model()
        
        if not success:
            logger.warning("Failed to load local AI model, will attempt auto-download")
        
        model_loaded = True
        logger.info("Mock model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {ext.lstrip('.') for ext in UPLOAD_CONFIG['allowed_extensions']}

@app.route('/')
def index():
    """Main page"""
    return render_template('index_simplified.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    if use_fallback_storage:
        model_data = fallback_storage.get_active_model()
        writeup_count = len(fallback_storage.get_writeups(limit=100))
    else:
        model_data = shared_db.get_active_model()
        writeup_count = len(shared_db.get_writeups(limit=100))
    
    return jsonify({
        'model_loaded': model_loaded and (local_ai.current_model_id is not None),
        'training_in_progress': training_in_progress,
        'active_model': local_ai.current_model_id or model_data.get('name', 'No Model') if model_data else 'No Model',
        'writeup_count': writeup_count,
        'auto_training_enabled': True,
        'last_training': last_training_check.isoformat(),
        'context_window': 4096,
        'model_type': 'Local AI Engine',
        'storage_mode': 'fallback' if use_fallback_storage else 'database'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""        
    try:
        data = request.get_json()
        question = data.get('message', '') or data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        start_time = time.time()
        
        # Generate response using local AI
        response = local_ai.generate_response(question)
        
        response_time = time.time() - start_time
        
        # Update usage stats
        if use_fallback_storage:
            model_data = fallback_storage.get_active_model()
            if model_data:
                fallback_storage.update_model_usage(model_data['id'], response_time)
        else:
            model_data = shared_db.get_active_model()
            if model_data:
                shared_db.update_model_usage(model_data['id'], response_time)
        
        return jsonify({
            'response': response,
            'response_time': response_time,
            'model_type': local_ai.current_model_id or 'Local AI Engine',
            'context_window': local_ai.context_window
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
        
    try:
        # Create upload directory
        os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_CONFIG['upload_folder'], filename)
        file.save(filepath)
        
        # Read and process file content
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract title from filename
        title = filename.rsplit('.', 1)[0]
        
        # Save to database or fallback
        if use_fallback_storage:
            writeup_id = fallback_storage.save_writeup(
                title=title,
                content=content,
                source='file_upload',
                category='imported',
                difficulty='unknown'
            )
            # Update local AI knowledge handled automatically
        else:
            writeup_id = shared_db.save_writeup(
                title=title,
                content=content,
                source='file_upload',
                category='imported',
                difficulty='unknown'
            )
            # Update local AI knowledge handled automatically
        
        # Clean up file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'writeup_id': writeup_id,
            'message': 'File uploaded and processed successfully'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Failed to process file'}), 500

@app.route('/api/collect-data', methods=['POST'])
def collect_data():
    """Start data collection"""
    try:
        collector = SimpleDataCollector()
        
        # Collect from configured sources
        results = []
        for source in DATA_SOURCES[:2]:  # Limit to first 2 sources for demo
            if source['type'] == 'github':
                writeups = collector.collect_from_github(source['url'])
            else:
                writeups = collector.collect_from_website(source['url'])
                
            # Save to database or fallback
            for writeup in writeups[:5]:  # Limit to 5 per source
                if use_fallback_storage:
                    writeup_id = fallback_storage.save_writeup(
                        title=writeup.get('title', 'Untitled'),
                        content=writeup.get('content', ''),
                        source=source['name'],
                        url=writeup.get('url'),
                        category=writeup.get('category'),
                        difficulty=writeup.get('difficulty')
                    )
                else:
                    writeup_id = shared_db.save_writeup(
                        title=writeup.get('title', 'Untitled'),
                        content=writeup.get('content', ''),
                        source=source['name'],
                        url=writeup.get('url'),
                        category=writeup.get('category'),
                        difficulty=writeup.get('difficulty')
                    )
                if writeup_id:
                    results.append(writeup_id)
        
        # Local AI knowledge is updated automatically when new data is saved
        
        return jsonify({
            'success': True,
            'collected_count': len(results),
            'message': f'Collected {len(results)} writeups'
        })
        
    except Exception as e:
        logger.error(f"Collection error: {e}")
        return jsonify({'error': 'Failed to collect data'}), 500

@app.route('/api/trigger-training', methods=['POST'])
def trigger_training():
    """Manually trigger model training"""
    if auto_trainer.start_training():
        return jsonify({'success': True, 'message': 'Training started'})
    else:
        return jsonify({'error': 'Training already in progress'}), 400

@app.route('/api/download-model', methods=['GET'])
def download_model():
    """Download the active model for client-side use"""
    try:
        if use_fallback_storage:
            model_data = fallback_storage.get_active_model()
        else:
            model_data = shared_db.get_active_model()
            
        if not model_data:
            return jsonify({'error': 'No active model available'}), 404
        
        # Prepare model data for client-side use
        client_model_data = {
            'id': model_data['id'],
            'name': model_data['name'],
            'version': model_data['version'],
            'model_type': model_data['model_type'],
            'config_data': model_data.get('config_data'),
            'download_count': model_data.get('download_count', 0),
            'created_at': model_data.get('created_at'),
            'context_window': 4096
        }
        
        # Update download count
        if use_fallback_storage:
            fallback_storage.update_model_usage(model_data['id'], 0)
        else:
            shared_db.update_model_usage(model_data['id'], 0)
        
        logger.info(f"Model downloaded: {model_data['name']} v{model_data['version']}")
        
        return jsonify({
            'success': True,
            'model': client_model_data,
            'message': f'Model {model_data["name"]} v{model_data["version"]} downloaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Model download error: {e}")
        return jsonify({'error': 'Failed to download model'}), 500

def background_tasks():
    """Background thread for automatic tasks"""
    while True:
        try:
            # Check if we should start automatic training
            if auto_trainer.should_train():
                logger.info("Starting automatic training...")
                auto_trainer.start_training()
                
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Background task error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Initialize database or use fallback  
    logger.info("Initializing database connection...")
    if shared_db.init_db():
        logger.info("Database connected successfully")
        use_fallback_storage = False
        if not shared_db.init_tables():
            logger.warning("Table initialization failed, switching to fallback")
            use_fallback_storage = True
    else:
        logger.info("Using fallback JSON storage")
        use_fallback_storage = True
        fallback_storage.init_storage()
    
    # Initialize local AI system first
    logger.info("Initializing Local AI Engine...")
    available_models = local_ai.get_available_models()
    downloaded_models = [mid for mid, info in available_models.items() if info['downloaded']]
    
    if downloaded_models:
        logger.info(f"Found downloaded model: {downloaded_models[0]}")
        if local_ai.load_model(downloaded_models[0]):
            model_loaded = True
            logger.info(f"Loaded model {downloaded_models[0]} successfully")
    else:
        logger.info("No models found locally, attempting auto-download...")
        def progress_callback(message):
            logger.info(f"Model download: {message}")
        
        downloaded_model = local_ai.auto_download_best_model(progress_callback)
        if downloaded_model:
            if local_ai.load_model(downloaded_model):
                model_loaded = True
                logger.info(f"Successfully downloaded and loaded {downloaded_model}")
            else:
                logger.warning("Model downloaded but failed to load, using fallback responses")
                model_loaded = True
        else:
            logger.info("Model download failed, using intelligent fallback responses")
            model_loaded = True  # Still allow system to function
    
    # Load additional training data if available
    load_active_model()
    
    # Start background tasks
    bg_thread = threading.Thread(target=background_tasks)
    bg_thread.daemon = True
    bg_thread.start()
    
    logger.info("Starting CTF AI System with Local AI...")
    logger.info(f"Local AI Engine ready with {local_ai.context_window} token context window")
    logger.info(f"Model loaded: {model_loaded}")
    logger.info(f"Current model: {local_ai.current_model_id or 'None'}")
    logger.info(f"Storage mode: {'Fallback JSON' if use_fallback_storage else 'Database'}")
    
    app.run(
        host=SYSTEM_CONFIG['host'],
        port=SYSTEM_CONFIG['port'],
        debug=False  # Disable debug to avoid conflicts
    )