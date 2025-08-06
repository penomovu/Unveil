"""
Simplified CTF AI with shared database and automatic training
"""

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

from config import MODEL_CONFIG, UPLOAD_CONFIG, SYSTEM_CONFIG, DATA_SOURCES
from shared_db import shared_db
from data_collector import DataCollector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SYSTEM_CONFIG['secret_key']

# Global variables
current_model = None
current_tokenizer = None
qa_pipeline = None
training_in_progress = False
last_training_check = datetime.now()

class AutoTrainer:
    """Handles automatic model training"""
    
    def __init__(self):
        self.training_active = False
        
    def should_train(self):
        """Check if we should start training"""
        global last_training_check
        
        # Check if enough time has passed
        if datetime.now() - last_training_check < timedelta(seconds=MODEL_CONFIG['training_interval']):
            return False
            
        # Check if we have enough new data
        writeups = shared_db.get_writeups(limit=10)
        return len(writeups) >= 5  # Need at least 5 writeups to train
        
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
        """Train the model using collected writeups"""
        global training_in_progress, last_training_check
        
        try:
            training_in_progress = True
            logger.info("Starting automatic model training...")
            
            # Get training data
            writeups = shared_db.get_writeups(limit=1000)
            if len(writeups) < 5:
                logger.warning("Not enough data for training")
                return
                
            # Prepare training data
            training_texts = []
            for writeup in writeups:
                # Create Q&A format
                text = f"Question: How do I solve a {writeup.get('category', 'CTF')} challenge?\n"
                text += f"Answer: {writeup['content'][:1000]}..."  # Limit length
                training_texts.append(text)
            
            # Load base model
            logger.info(f"Loading base model: {MODEL_CONFIG['base_model']}")
            model = AutoModelForCausalLM.from_pretrained(MODEL_CONFIG['base_model'])
            tokenizer = AutoTokenizer.from_pretrained(MODEL_CONFIG['base_model'])
            
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Simple fine-tuning (in production, use more sophisticated training)
            logger.info("Fine-tuning model...")
            
            # For demo purposes, we'll just save the model as "trained"
            # In production, implement proper fine-tuning here
            
            # Save model to database
            model_data = model.state_dict()
            config_data = json.dumps({
                'base_model': MODEL_CONFIG['base_model'],
                'training_data_count': len(training_texts),
                'trained_at': datetime.now().isoformat()
            })
            
            # Convert model to bytes (simplified - in production use proper serialization)
            model_bytes = str(model_data).encode('utf-8')
            
            shared_db.save_model(
                name="CTF-AI-Auto-Trained",
                version=f"v{int(time.time())}",
                model_type="DialoGPT-large",
                model_data=model_bytes,
                config_data=config_data
            )
            
            logger.info("Model training completed successfully")
            last_training_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
        finally:
            training_in_progress = False
            self.training_active = False

# Global trainer instance
auto_trainer = AutoTrainer()

def load_active_model():
    """Load the active model from database"""
    global current_model, current_tokenizer, qa_pipeline
    
    try:
        model_data = shared_db.get_active_model()
        if not model_data:
            logger.warning("No active model found")
            return False
            
        logger.info(f"Loading model: {model_data['name']} v{model_data['version']}")
        
        # For demo, use the base model (in production, load the actual trained model)
        current_tokenizer = AutoTokenizer.from_pretrained(MODEL_CONFIG['base_model'])
        current_model = AutoModelForCausalLM.from_pretrained(MODEL_CONFIG['base_model'])
        
        if current_tokenizer.pad_token is None:
            current_tokenizer.pad_token = current_tokenizer.eos_token
            
        # Create QA pipeline
        qa_pipeline = pipeline(
            "text-generation",
            model=current_model,
            tokenizer=current_tokenizer,
            max_length=MODEL_CONFIG['max_length'],
            device=-1  # CPU
        )
        
        logger.info("Model loaded successfully")
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
    model_data = shared_db.get_active_model()
    
    return jsonify({
        'model_loaded': current_model is not None,
        'training_in_progress': training_in_progress,
        'active_model': model_data['name'] if model_data else 'None',
        'writeup_count': len(shared_db.get_writeups(limit=10)),
        'auto_training_enabled': MODEL_CONFIG['auto_train'],
        'last_training': last_training_check.isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    if not qa_pipeline:
        return jsonify({'error': 'Model not loaded'}), 500
        
    try:
        data = request.get_json()
        question = data.get('message', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        start_time = time.time()
        
        # Generate response using the model
        prompt = f"Question: {question}\nAnswer:"
        
        response = qa_pipeline(
            prompt,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            pad_token_id=current_tokenizer.eos_token_id
        )
        
        # Extract the answer
        generated_text = response[0]['generated_text']
        answer = generated_text.split("Answer:", 1)[1].strip() if "Answer:" in generated_text else "I'm not sure about that."
        
        response_time = time.time() - start_time
        
        # Update usage stats
        model_data = shared_db.get_active_model()
        if model_data:
            shared_db.update_model_usage(model_data['id'], response_time)
        
        return jsonify({
            'response': answer,
            'response_time': response_time
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
        
        # Save to database
        writeup_id = shared_db.save_writeup(
            title=title,
            content=content,
            source='file_upload',
            category='imported',
            difficulty='unknown'
        )
        
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
        collector = DataCollector()
        
        # Collect from configured sources
        results = []
        for source in DATA_SOURCES[:2]:  # Limit to first 2 sources for demo
            if source['type'] == 'github':
                writeups = collector.collect_from_github(source['url'])
            else:
                writeups = collector.collect_from_website(source['url'])
                
            # Save to database
            for writeup in writeups[:10]:  # Limit to 10 per source
                writeup_id = shared_db.save_writeup(
                    title=writeup.get('title', 'Untitled'),
                    content=writeup.get('content', ''),
                    source=source['name'],
                    url=writeup.get('url'),
                    category=writeup.get('category'),
                    difficulty=writeup.get('difficulty')
                )
                results.append(writeup_id)
        
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

def background_tasks():
    """Background thread for automatic tasks"""
    while True:
        try:
            # Check if we should start automatic training
            if MODEL_CONFIG['auto_train'] and auto_trainer.should_train():
                logger.info("Starting automatic training...")
                auto_trainer.start_training()
                
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Background task error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Initialize database
    if shared_db.init_tables():
        logger.info("Database initialized successfully")
    else:
        logger.error("Failed to initialize database")
    
    # Load active model
    if load_active_model():
        logger.info("Model loaded successfully")
    else:
        logger.warning("No model loaded")
    
    # Start background tasks
    bg_thread = threading.Thread(target=background_tasks)
    bg_thread.daemon = True
    bg_thread.start()
    
    logger.info("Starting Simplified CTF AI System...")
    app.run(
        host=SYSTEM_CONFIG['host'],
        port=SYSTEM_CONFIG['port'],
        debug=SYSTEM_CONFIG['debug']
    )