"""
Main Flask application for the CTF AI system.
Provides web interface and API endpoints for data collection, training, and inference.
"""

from flask import Flask, request, jsonify, render_template
import os
import json
from threading import Thread
import logging
from datetime import datetime

from data_collector import CTFDataCollector
from preprocessor import TextPreprocessor
from model_trainer import ModelTrainer
from inference_engine import InferenceEngine
from evaluator import ModelEvaluator
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize components
data_collector = CTFDataCollector()
preprocessor = TextPreprocessor()
model_trainer = ModelTrainer()
inference_engine = InferenceEngine()
evaluator = ModelEvaluator()

# Global state tracking
system_state = {
    'data_collection_status': 'idle',
    'training_status': 'idle',
    'model_loaded': False,
    'last_collection_time': None,
    'last_training_time': None,
    'collected_writeups': 0,
    'model_performance': {}
}

@app.route('/')
def index():
    """Main interface for the CTF AI system."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current system status."""
    return jsonify(system_state)

@app.route('/api/collect-data', methods=['POST'])
def collect_data():
    """Start data collection process."""
    if system_state['data_collection_status'] == 'running':
        return jsonify({'error': 'Data collection already in progress'}), 400
    
    def run_collection():
        try:
            system_state['data_collection_status'] = 'running'
            logger.info("Starting data collection...")
            
            # Collect writeups from various sources
            writeups = data_collector.collect_all_sources()
            
            # Preprocess collected data
            processed_data = preprocessor.process_writeups(writeups)
            
            # Save processed data
            preprocessor.save_processed_data(processed_data, Config.PROCESSED_DATA_PATH)
            
            system_state['collected_writeups'] = len(processed_data)
            system_state['last_collection_time'] = datetime.now().isoformat()
            system_state['data_collection_status'] = 'completed'
            
            logger.info(f"Data collection completed. Collected {len(processed_data)} writeups.")
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            system_state['data_collection_status'] = 'failed'
    
    thread = Thread(target=run_collection)
    thread.start()
    
    return jsonify({'message': 'Data collection started'})

@app.route('/api/train-model', methods=['POST'])
def train_model():
    """Start model training process."""
    if system_state['training_status'] == 'running':
        return jsonify({'error': 'Training already in progress'}), 400
    
    if not os.path.exists(Config.PROCESSED_DATA_PATH):
        return jsonify({'error': 'No processed data found. Please collect data first.'}), 400
    
    def run_training():
        try:
            system_state['training_status'] = 'running'
            logger.info("Starting model training...")
            
            # Load processed data
            processed_data = preprocessor.load_processed_data(Config.PROCESSED_DATA_PATH)
            
            # Train the model
            training_results = model_trainer.train(processed_data)
            
            # Evaluate the model
            evaluation_results = evaluator.evaluate_model(model_trainer.model, model_trainer.tokenizer)
            
            system_state['model_performance'] = evaluation_results
            system_state['last_training_time'] = datetime.now().isoformat()
            system_state['training_status'] = 'completed'
            system_state['model_loaded'] = True
            
            # Initialize inference engine with trained model
            inference_engine.load_model(model_trainer.model, model_trainer.tokenizer)
            
            logger.info("Model training completed successfully.")
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            system_state['training_status'] = 'failed'
    
    thread = Thread(target=run_training)
    thread.start()
    
    return jsonify({'message': 'Model training started'})

@app.route('/api/load-model', methods=['POST'])
def load_existing_model():
    """Load a previously trained model."""
    try:
        if inference_engine.load_saved_model(Config.MODEL_SAVE_PATH):
            system_state['model_loaded'] = True
            return jsonify({'message': 'Model loaded successfully'})
        else:
            return jsonify({'error': 'No saved model found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to load model: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for querying the AI model."""
    if not system_state['model_loaded']:
        return jsonify({'error': 'No model loaded. Please train or load a model first.'}), 400
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    user_message = data['message']
    
    try:
        # Generate response using the inference engine
        response = inference_engine.generate_response(user_message)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate_model():
    """Evaluate the current model performance."""
    if not system_state['model_loaded']:
        return jsonify({'error': 'No model loaded'}), 400
    
    try:
        evaluation_results = evaluator.evaluate_model(
            inference_engine.model, 
            inference_engine.tokenizer
        )
        system_state['model_performance'] = evaluation_results
        return jsonify(evaluation_results)
    
    except Exception as e:
        return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500

@app.route('/api/data-sources')
def get_data_sources():
    """Get list of configured data sources."""
    return jsonify(data_collector.get_sources())

@app.route('/api/add-source', methods=['POST'])
def add_data_source():
    """Add a new data source."""
    data = request.get_json()
    if not data or 'url' not in data or 'type' not in data:
        return jsonify({'error': 'Missing required fields: url, type'}), 400
    
    try:
        data_collector.add_source(data['url'], data['type'], data.get('name', ''))
        return jsonify({'message': 'Data source added successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to add source: {str(e)}'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Check if model exists and load it
    if os.path.exists(Config.MODEL_SAVE_PATH):
        try:
            if inference_engine.load_saved_model(Config.MODEL_SAVE_PATH):
                system_state['model_loaded'] = True
                logger.info("Loaded existing model on startup")
        except Exception as e:
            logger.warning(f"Failed to load existing model: {str(e)}")
    
    logger.info("Starting CTF AI System...")
    app.run(host='0.0.0.0', port=5000, debug=False)
