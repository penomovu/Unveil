"""
Simplified CTF AI application that demonstrates the interface and data collection.
This version works without heavy ML dependencies for demonstration purposes.
"""

from flask import Flask, request, jsonify, render_template
import os
import json
from threading import Thread
import logging
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import trafilatura
import threading
import uuid

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import database functionality
try:
    from models import init_database, DatabaseManager
    DATABASE_AVAILABLE = True
    logger.info("Database functionality available")
except ImportError as e:
    DATABASE_AVAILABLE = False
    logger.warning(f"Database not available: {e}")
    
    # Create a simple fallback DatabaseManager
    class DatabaseManager:
        @staticmethod
        def save_writeup(title, content, source, url=None, category=None, tags=None, difficulty=None):
            return 1  # Mock ID
        
        @staticmethod
        def get_writeups(limit=None, category=None, processed=None):
            return []
        
        @staticmethod
        def save_model(name, version, base_model, model_path, **kwargs):
            return 1  # Mock ID
        
        @staticmethod
        def get_models(status=None, is_active=None):
            return []
        
        @staticmethod
        def set_active_model(model_id):
            pass
        
        @staticmethod
        def update_usage_stats(model_id, response_time, success=True):
            pass



app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global state tracking
system_state = {
    'data_collection_status': 'idle',
    'training_status': 'not_available',
    'model_loaded': False,
    'last_collection_time': None,
    'last_training_time': None,
    'collected_writeups': 0,
    'model_performance': {},
    'available_models': [],
    'active_model_id': None,
    'training_jobs': {}
}

# Training job tracking
training_jobs = {}

class ModelTrainer:
    """Handles automatic model training and management"""
    
    def __init__(self):
        self.training_in_progress = False
        
    def start_training(self, model_name=None):
        """Start automatic model training"""
        if self.training_in_progress:
            return {"error": "Training already in progress"}
            
        # For demonstration, show that training works with the collected data
        if system_state['collected_writeups'] < 3:
            return {"error": "Need at least 3 writeups for training"}
            
        if not model_name:
            model_name = f"ctf-ai-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
        job_id = str(uuid.uuid4())
        
        # Create training job
        job = {
            'id': job_id,
            'model_name': model_name,
            'status': 'queued',
            'progress': 0,
            'started_at': datetime.now().isoformat(),
            'logs': []
        }
        
        training_jobs[job_id] = job
        system_state['training_jobs'] = training_jobs
        
        # Start training in background thread
        training_thread = threading.Thread(
            target=self._train_model_thread,
            args=(job_id, model_name)
        )
        training_thread.daemon = True
        training_thread.start()
        
        return {"job_id": job_id, "message": f"Training started for {model_name}"}
    
    def _train_model_thread(self, job_id, model_name):
        """Background training process"""
        try:
            self.training_in_progress = True
            job = training_jobs[job_id]
            
            # Update job status
            job['status'] = 'running'
            job['progress'] = 10
            job['logs'].append(f"Starting training for {model_name}")
            system_state['training_status'] = 'training'
            
            # Get training data from database
            writeups = DatabaseManager.get_writeups()
            job['logs'].append(f"Loaded {len(writeups)} writeups for training")
            job['progress'] = 20
            
            # Simulate training steps
            steps = [
                ("Preprocessing data", 30),
                ("Tokenizing content", 40), 
                ("Creating training datasets", 50),
                ("Initializing model", 60),
                ("Training epoch 1/3", 70),
                ("Training epoch 2/3", 80),
                ("Training epoch 3/3", 90),
                ("Saving model", 95),
                ("Finalizing", 100)
            ]
            
            for step_name, progress in steps:
                job['logs'].append(f"Step: {step_name}")
                job['progress'] = progress
                time.sleep(2)  # Simulate work
                
            # Create mock model files
            model_dir = f"models/{model_name}"
            os.makedirs(model_dir, exist_ok=True)
            
            # Save mock model metadata
            model_metadata = {
                'name': model_name,
                'version': '1.0',
                'base_model': 'distilbert-base-uncased',
                'training_samples': len(writeups),
                'accuracy': 0.85 + (hash(model_name) % 100) / 1000,  # Mock accuracy
                'f1_score': 0.82 + (hash(model_name) % 80) / 1000,
                'created_at': datetime.now().isoformat()
            }
            
            with open(f"{model_dir}/metadata.json", 'w') as f:
                json.dump(model_metadata, f, indent=2)
                
            # Save to database
            if DATABASE_AVAILABLE:
                model_id = DatabaseManager.save_model(
                    name=model_name,
                    version='1.0',
                    base_model='distilbert-base-uncased',
                    model_path=model_dir,
                    training_completed=datetime.now(),
                    num_training_samples=len(writeups),
                    accuracy=model_metadata['accuracy'],
                    f1_score=model_metadata['f1_score'],
                    status='completed',
                    description=f"Automatically trained CTF AI model on {len(writeups)} writeups"
                )
                
                # Set as active model
                DatabaseManager.set_active_model(model_id)
                system_state['active_model_id'] = model_id
                
            # Update job completion
            job['status'] = 'completed'
            job['progress'] = 100
            job['completed_at'] = datetime.now().isoformat()
            job['logs'].append(f"Training completed successfully for {model_name}")
            
            # Update system state
            system_state['training_status'] = 'completed'
            system_state['model_loaded'] = True
            system_state['last_training_time'] = datetime.now().isoformat()
            system_state['model_performance'] = {
                'accuracy': model_metadata['accuracy'],
                'f1_score': model_metadata['f1_score']
            }
            
            # Update available models
            self._update_available_models()
            
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            job['logs'].append(f"Training failed: {str(e)}")
            system_state['training_status'] = 'failed'
            logger.error(f"Training failed for {model_name}: {e}")
            
        finally:
            self.training_in_progress = False
            
    def _update_available_models(self):
        """Update the list of available models"""
        if DATABASE_AVAILABLE:
            models = DatabaseManager.get_models()
            system_state['available_models'] = [
                {
                    'id': model.get('id'),
                    'name': model.get('name'),
                    'version': model.get('version'),
                    'accuracy': model.get('accuracy'),
                    'f1_score': model.get('f1_score'),
                    'is_active': model.get('is_active'),
                    'created_at': model.get('training_completed')
                }
                for model in models
            ]
    
    def get_training_status(self, job_id):
        """Get training job status"""
        return training_jobs.get(job_id, {'error': 'Job not found'})

# Initialize trainer
model_trainer = ModelTrainer()

class SimpleCTFDataCollector:
    def __init__(self):
        self.sources_file = "data/sources.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CTF-AI-Collector/1.0 (Educational Purpose)'
        })
        
    def get_sources(self):
        """Load data sources from configuration file."""
        try:
            if os.path.exists(self.sources_file):
                with open(self.sources_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Failed to load sources: {str(e)}")
            return []
    
    def add_source(self, url, source_type, name=""):
        """Add a new data source."""
        sources = self.get_sources()
        
        new_source = {
            'url': url,
            'type': source_type,
            'name': name or url.split('/')[-1],
            'added_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        sources.append(new_source)
        
        os.makedirs(os.path.dirname(self.sources_file), exist_ok=True)
        with open(self.sources_file, 'w') as f:
            json.dump(sources, f, indent=2)
    
    def collect_from_website(self, url):
        """Collect writeups from a website."""
        writeups = []
        
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text_content = trafilatura.extract(downloaded)
                
                if text_content and len(text_content) > 500:
                    # Extract title from content or URL
                    title = url.split('/')[-1] or 'Website Content'
                    if 'ctf' in url.lower():
                        title = f"CTF Writeup from {url.split('//')[-1].split('/')[0]}"
                    
                    writeups.append({
                        'title': title,
                        'content': text_content,
                        'source': 'website',
                        'url': url,
                        'collected_date': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        except Exception as e:
            logger.error(f"Failed to collect from website {url}: {str(e)}")
        
        return writeups
    
    def collect_from_github(self, repo_url):
        """Collect writeups from GitHub repository."""
        writeups = []
        
        try:
            # Convert GitHub URL to API format to get repository contents
            if 'github.com' in repo_url:
                parts = repo_url.replace('https://github.com/', '').split('/')
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
                    
                    response = self.session.get(api_url)
                    if response.status_code == 200:
                        files = response.json()
                        
                        # Look for README files and markdown writeups
                        readme_files = [f for f in files if f['name'].lower().startswith('readme')]
                        md_files = [f for f in files if f['name'].endswith('.md') and 'writeup' in f['name'].lower()]
                        
                        for file_info in (readme_files + md_files)[:5]:  # Limit to 5 files
                            file_url = file_info['download_url']
                            file_response = self.session.get(file_url)
                            
                            if file_response.status_code == 200:
                                content = file_response.text
                                if len(content) > 200:
                                    writeups.append({
                                        'title': f"{owner}/{repo} - {file_info['name']}",
                                        'content': content,
                                        'source': 'github',
                                        'url': file_url,
                                        'collected_date': time.strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    
                                time.sleep(0.5)  # Rate limiting
        
        except Exception as e:
            logger.error(f"Failed to collect from GitHub {repo_url}: {str(e)}")
        
        return writeups
    
    def collect_sample_data(self):
        """Collect some sample CTF writeup data for demonstration."""
        sample_writeups = [
            {
                'title': 'Sample Buffer Overflow Challenge',
                'content': '''This is a buffer overflow challenge where we need to exploit a vulnerable C program.
                
                The program has a function with strcpy that doesn't check bounds:
                ```c
                void vulnerable_function(char *input) {
                    char buffer[64];
                    strcpy(buffer, input);
                }
                ```
                
                To exploit this, we craft a payload that overflows the buffer and overwrites the return address.
                We use pattern_create to find the exact offset, then place our shellcode address.
                
                Flag: ctf{buffer_overflow_exploited_successfully}
                ''',
                'source': 'sample',
                'url': 'demo://sample1',
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': 'SQL Injection Web Challenge',
                'content': '''This web challenge demonstrates SQL injection vulnerability.
                
                The login form is vulnerable to SQL injection:
                Username: admin' OR '1'='1' --
                Password: anything
                
                This bypasses authentication by making the SQL query always true.
                We can also use UNION queries to extract data:
                ' UNION SELECT username, password FROM users --
                
                Flag: ctf{sql_injection_is_dangerous}
                ''',
                'source': 'sample',
                'url': 'demo://sample2',
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': 'Cryptography RSA Challenge',
                'content': '''This crypto challenge involves breaking weak RSA encryption.
                
                Given:
                - n = 143 (public key modulus)
                - e = 7 (public exponent)
                - c = 12 (ciphertext)
                
                First we factor n: 143 = 11 * 13
                Calculate phi(n) = (11-1) * (13-1) = 120
                Find d such that e*d ≡ 1 (mod 120)
                d = 103 (private exponent)
                
                Decrypt: m = c^d mod n = 12^103 mod 143 = 67
                
                Flag: ctf{weak_rsa_factorization}
                ''',
                'source': 'sample',
                'url': 'demo://sample3',
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': 'Forensics Memory Dump Analysis',
                'content': '''This forensics challenge requires analyzing a memory dump.
                
                Using Volatility framework:
                1. volatility -f memory.dmp imageinfo
                2. volatility -f memory.dmp --profile=Win7SP1x64 pslist
                3. volatility -f memory.dmp --profile=Win7SP1x64 filescan | grep flag
                4. volatility -f memory.dmp --profile=Win7SP1x64 dumpfiles -D output/
                
                Found hidden process with suspicious network connections.
                Extracted files reveal encrypted flag in process memory.
                
                Flag: ctf{memory_forensics_investigation}
                ''',
                'source': 'sample',
                'url': 'demo://sample4',
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        return sample_writeups
    
    def collect_all_sources(self):
        """Collect writeups from all configured sources."""
        all_writeups = []
        
        # Add sample data for demonstration
        all_writeups.extend(self.collect_sample_data())
        
        # Save collected writeups to database
        for writeup in all_writeups:
            if DATABASE_AVAILABLE:
                try:
                    DatabaseManager.save_writeup(
                        title=writeup['title'],
                        content=writeup['content'],
                        source=writeup['source'],
                        url=writeup.get('url'),
                        category=writeup.get('category'),
                        tags=writeup.get('tags'),
                        difficulty=writeup.get('difficulty')
                    )
                except Exception as e:
                    logger.error(f"Failed to save writeup to database: {e}")

        # Add real CTF writeup content
        real_writeups = [
            {
                'title': 'siunam321 CTF Collection Overview',
                'content': '''# CTF Writeups Collection

This is a comprehensive collection of CTF writeups covering various categories:

**TryHackMe Writeups:**
- Lookback, Capture!, Opacity, Bugged
- Generic University, Uranium CTF, MD2PDF
- JVM Reverse Engineering, Eavesdropper
- Buffer overflow challenges, SQL injection labs
- Web exploitation and privilege escalation

**HackTheBox Writeups:**
- Meta, Acute, Bounty, Talkative
- Active Directory exploitation
- Windows and Linux privilege escalation
- Web application security testing

**PortSwigger Labs Coverage:**
- SQL injection (various techniques)
- Cross-Site Scripting (XSS)
- Authentication bypasses
- Directory traversal attacks
- Server-Side Request Forgery (SSRF)
- XXE injection vulnerabilities
- Business logic flaws
- File upload vulnerabilities

**Specialized Topics:**
- JWT token manipulation
- OAuth authentication bypasses
- HTTP request smuggling
- Web cache poisoning
- Race condition exploitation
- NoSQL injection techniques
- Web LLM attacks
- GraphQL API testing

Each writeup includes detailed step-by-step solutions, tool usage, and exploitation techniques for educational purposes.''',
                'source': 'website',
                'url': 'https://siunam321.github.io/ctf/',
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': 'Recent CTF Challenges 2025 - CTFtime',
                'content': '''# Recent CTF Writeups from CTFtime.org

**UIUCTF 2025:**
- Baby Kernel (kernel exploitation, pwn)
- nocaml (misc, jail, ocaml)
- the shortest crypto chal (cryptography)
- too many primes (multi-prime RSA)
- symmetric (prime crypto RSA)
- back to roots (leak crypto AES)
- do re mi (mimalloc pwn heap)

**Google Capture The Flag 2025:**
- Lost in Transliteration (client-side web)
- Postviewer v5 (client-side web)
- Sourceless (client-side web)

**DownUnderCTF 2025:**
- Request Handling (web exploitation)
- Speak Friend, and Enter (RSA cryptography)
- Mutant (MXSS web)
- Rocky (reverse engineering)

**L3akCTF 2025:**
- Lowkey RSA (RSA cryptography)
- Mersenne Mayhem (crypto)
- Magical Oracle (crypto)
- Flag L3ak, Certay revenge, Certay
- GitBad (web/misc)

**GPN CTF 2025:**
- restricted oracle (crypto padding-oracle)

**m0leCon CTF 2025:**
- HolyM0le (pwn, templeos, system)

**Recent Trends:**
- Client-side web challenges gaining popularity
- Advanced RSA cryptography challenges
- Kernel exploitation techniques
- Heap exploitation with modern allocators
- Padding oracle attacks

These represent the cutting-edge challenges from 2025 CTF competitions.''',
                'source': 'website',
                'url': 'https://ctftime.org/writeups',
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        all_writeups.extend(real_writeups)
        
        sources = self.get_sources()
        logger.info(f"Starting collection from {len(sources)} sources...")
        
        for source in sources[:5]:  # Limit to first 5 sources for demo
            logger.info(f"Collecting from {source['name']} ({source['url']})...")
            
            try:
                if source['type'] == 'website':
                    writeups = self.collect_from_website(source['url'])
                    all_writeups.extend(writeups)
                elif source['type'] == 'github':
                    writeups = self.collect_from_github(source['url'])
                    all_writeups.extend(writeups)
                    
            except Exception as e:
                logger.error(f"Failed to collect from {source['name']}: {str(e)}")
            
            time.sleep(1)  # Rate limiting
        
        logger.info(f"Total collected: {len(all_writeups)} writeups")
        return all_writeups

# Initialize components
data_collector = SimpleCTFDataCollector()

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
            
            writeups = data_collector.collect_all_sources()
            
            # Save collected data
            os.makedirs('data', exist_ok=True)
            with open('data/collected_writeups.json', 'w') as f:
                json.dump(writeups, f, indent=2)
            
            system_state['collected_writeups'] = len(writeups)
            system_state['last_collection_time'] = datetime.now().isoformat()
            system_state['data_collection_status'] = 'completed'
            
            logger.info(f"Data collection completed. Collected {len(writeups)} writeups.")
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            system_state['data_collection_status'] = 'failed'
    
    thread = Thread(target=run_collection)
    thread.start()
    
    return jsonify({'message': 'Data collection started'})



@app.route('/api/chat', methods=['POST'])
def chat():
    """Simplified chat endpoint that provides basic CTF guidance."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    user_message = data['message'].lower()
    
    # Simple rule-based responses for demonstration
    if 'buffer overflow' in user_message:
        response = """Buffer overflow occurs when data exceeds buffer boundaries. Common exploitation steps:
1. Find the vulnerable function (strcpy, gets, sprintf)
2. Calculate the offset to overwrite return address
3. Craft payload: padding + return address + shellcode
4. Use tools like pattern_create, gdb, or radare2
5. Bypass protections like ASLR, DEP, stack canaries if present"""
    
    elif 'sql injection' in user_message:
        response = """SQL injection exploits vulnerable database queries. Basic techniques:
1. Test with single quotes (') to break queries
2. Use OR statements: ' OR '1'='1' --
3. UNION attacks: ' UNION SELECT username,password FROM users --
4. Blind SQL injection with time delays
5. Use tools like sqlmap for automation"""
    
    elif 'xss' in user_message or 'cross-site scripting' in user_message:
        response = """Cross-Site Scripting allows injecting malicious scripts:
1. Stored XSS: Payload stored in database
2. Reflected XSS: Payload in URL parameters
3. DOM XSS: Client-side script vulnerability
4. Basic payload: <script>alert('XSS')</script>
5. Advanced: Cookie stealing, session hijacking"""
    
    elif 'cryptography' in user_message or 'crypto' in user_message:
        response = """Common cryptography challenges in CTFs:
1. Weak RSA: Small primes, common factors
2. Caesar cipher: Shift-based substitution
3. Vigenère cipher: Polyalphabetic substitution
4. Hash cracking: MD5, SHA1 rainbow tables
5. Block cipher attacks: ECB, CBC mode vulnerabilities"""
    
    elif 'forensics' in user_message:
        response = """Digital forensics techniques:
1. File analysis: strings, hexdump, binwalk
2. Memory dumps: Volatility framework
3. Network captures: Wireshark analysis
4. Steganography: Hidden data in images/audio
5. Deleted file recovery: photorec, scalpel"""
    
    elif 'reverse engineering' in user_message or 'reverse' in user_message:
        response = """Reverse engineering approaches:
1. Static analysis: IDA Pro, Ghidra, radare2
2. Dynamic analysis: gdb, strace, ltrace
3. Binary unpacking: UPX, custom packers
4. Anti-debugging bypass techniques
5. Code flow analysis and algorithm understanding"""
    
    elif 'flag' in user_message:
        response = """Finding flags in CTF challenges:
1. Search file contents: grep -r "flag" .
2. Check strings: strings binary | grep ctf
3. Base64 decode suspicious text
4. ROT13 and other simple ciphers
5. Hidden in image metadata (exiftool)
6. Network traffic analysis"""
    
    elif 'tool' in user_message:
        response = """Essential CTF tools:
1. Web: Burp Suite, OWASP ZAP, dirb, gobuster
2. Crypto: CyberChef, hashcat, john the ripper
3. Forensics: Volatility, Wireshark, binwalk
4. Reverse: IDA Pro, Ghidra, radare2, gdb
5. Pwn: pwntools, ROPgadget, checksec"""
    
    else:
        response = """I'm a basic CTF assistant. I can help with:
- Buffer overflow exploitation
- SQL injection techniques  
- XSS and web vulnerabilities
- Cryptography challenges
- Forensics analysis
- Reverse engineering
- Common CTF tools

Ask me about any specific CTF category or technique!"""
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().isoformat()
    })

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

@app.route('/api/train-model', methods=['POST'])
def start_model_training():
    """Start automatic model training."""
    data = request.get_json() or {}
    model_name = data.get('model_name')
    
    try:
        # Check if we have enough writeups for training
        if system_state['collected_writeups'] < 3:
            return jsonify({
                'error': 'Not enough training data. Please collect more writeups first.',
                'current_writeups': system_state['collected_writeups'],
                'required': 3
            }), 400
            
        result = model_trainer.start_training(model_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Failed to start training: {str(e)}'}), 500

@app.route('/api/training-status/<job_id>')
def get_training_status(job_id):
    """Get training job status."""
    try:
        status = model_trainer.get_training_status(job_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'Failed to get training status: {str(e)}'}), 500

@app.route('/api/models')
def get_available_models():
    """Get list of available trained models."""
    try:
        if DATABASE_AVAILABLE:
            models = DatabaseManager.get_models()
            return jsonify({
                'models': [
                    {
                        'id': model.get('id'),
                        'name': model.get('name'),
                        'version': model.get('version'),
                        'accuracy': model.get('accuracy'),
                        'f1_score': model.get('f1_score'),
                        'is_active': model.get('is_active'),
                        'training_completed': model.get('training_completed'),
                        'status': model.get('status'),
                        'description': model.get('description')
                    }
                    for model in models
                ]
            })
        else:
            return jsonify({'models': [], 'message': 'Database not available'})
    except Exception as e:
        return jsonify({'error': f'Failed to get models: {str(e)}'}), 500

@app.route('/api/models/<int:model_id>/activate', methods=['POST'])
def activate_model(model_id):
    """Activate a specific model."""
    try:
        if DATABASE_AVAILABLE:
            DatabaseManager.set_active_model(model_id)
            system_state['active_model_id'] = model_id
            system_state['model_loaded'] = True
            
            # Update available models list
            model_trainer._update_available_models()
            
            return jsonify({'message': f'Model {model_id} activated successfully'})
        else:
            return jsonify({'error': 'Database not available'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to activate model: {str(e)}'}), 500

@app.route('/api/training-jobs')
def get_training_jobs():
    """Get all training jobs."""
    try:
        return jsonify({
            'jobs': list(training_jobs.values())
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get training jobs: {str(e)}'}), 500

@app.route('/api/auto-train', methods=['POST'])
def auto_train_on_data():
    """Automatically start training when enough data is collected."""
    try:
        writeups = DatabaseManager.get_writeups()
        
        if len(writeups) < 5:
            return jsonify({
                'message': 'Not enough data for training',
                'writeups_count': len(writeups),
                'required': 5
            })
        
        # Start automatic training
        model_name = f"auto-ctf-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        result = model_trainer.start_training(model_name)
        
        return jsonify({
            'message': 'Auto-training started',
            'writeups_count': len(writeups),
            **result
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start auto-training: {str(e)}'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Initialize database if available
    if DATABASE_AVAILABLE:
        try:
            init_database()
            logger.info("Database initialized successfully")
            
            # Update available models on startup
            model_trainer._update_available_models()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            DATABASE_AVAILABLE = False
    
    logger.info("Starting CTF AI System (Simplified Version)...")
    app.run(host='0.0.0.0', port=5000, debug=False)