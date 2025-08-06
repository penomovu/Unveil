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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    'model_performance': {}
}

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
                    writeups.append({
                        'title': url.split('/')[-1] or 'Website Content',
                        'content': text_content,
                        'source': 'website',
                        'url': url,
                        'collected_date': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        except Exception as e:
            logger.error(f"Failed to collect from website {url}: {str(e)}")
        
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
        
        sources = self.get_sources()
        logger.info(f"Starting collection from {len(sources)} sources...")
        
        for source in sources[:3]:  # Limit to first 3 sources for demo
            logger.info(f"Collecting from {source['name']} ({source['url']})...")
            
            try:
                if source['type'] == 'website':
                    writeups = self.collect_from_website(source['url'])
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

@app.route('/api/train-model', methods=['POST'])
def train_model():
    """Simulate model training process."""
    return jsonify({'error': 'Model training requires additional ML dependencies. Please install transformers, torch, and other ML libraries.'}), 400

@app.route('/api/load-model', methods=['POST'])
def load_existing_model():
    """Simulate loading a model."""
    return jsonify({'error': 'No pre-trained model available. Please train a model first.'}), 404

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

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting CTF AI System (Simplified Version)...")
    app.run(host='0.0.0.0', port=5000, debug=False)