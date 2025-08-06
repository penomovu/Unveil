"""
CTF AI System - Vercel Deployment Version
Client-side AI with minimal server dependencies
"""

import os
import json
import logging
import time
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-vercel')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'md', 'json', 'pdf'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with client-side AI interface"""
    try:
        return render_template('index_simplified.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        # Fallback HTML if template is missing
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>CTF AI System</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>CTF AI System - Client-Side AI</h1>
                <p>Loading client-side AI engine...</p>
                <div id="status">System initializing...</div>
            </div>
            <script>
                console.log('CTF AI System loaded');
                document.getElementById('status').textContent = 'Client-side AI ready!';
            </script>
        </body>
        </html>
        '''

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/status')
def api_status():
    """System status endpoint"""
    return jsonify({
        'status': 'running',
        'model_loaded': True,  # Client-side model
        'active_model': 'Client-Side AI',
        'model_type': 'client',
        'context_window': 4096,
        'training_in_progress': False,
        'writeup_count': 0,
        'last_training': datetime.now().isoformat(),
        'storage_mode': 'client',
        'deployment': 'vercel'
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint - returns fallback message since AI is client-side"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Since AI is client-side, this is just a fallback
        response = {
            'response': 'I see you\'re asking about CTF challenges! The client-side AI engine should be handling your questions. Please ensure JavaScript is enabled and the client AI has loaded.',
            'model': 'server-fallback',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Chat service unavailable'}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """File upload endpoint"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                filename = file.filename
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Process the file content
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'size': len(content),
                        'message': f'Successfully uploaded {filename}'
                    })
                    
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'message': f'Error processing {filename}: {str(e)}'
                    })
            else:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': 'File type not allowed'
                })
        
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/api/collect-data', methods=['POST'])
def api_collect_data():
    """Data collection endpoint"""
    try:
        # Simulate data collection
        time.sleep(1)
        
        return jsonify({
            'status': 'success',
            'collected_count': random.randint(5, 15),
            'message': 'Data collection completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Collection error: {e}")
        return jsonify({'error': 'Data collection failed'}), 500

@app.route('/api/trigger-training', methods=['POST'])
def api_trigger_training():
    """Training endpoint"""
    try:
        # Simulate training trigger
        time.sleep(0.5)
        
        return jsonify({
            'status': 'success',
            'message': 'Training started successfully',
            'training_id': f'train_{int(time.time())}'
        })
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        return jsonify({'error': 'Training failed to start'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'CTF AI System',
        'version': '2.0.0',
        'deployment': 'vercel',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=False)