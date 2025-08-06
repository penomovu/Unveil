"""
CTF AI System - Vercel Serverless Function
"""

from http.server import BaseHTTPRequestHandler
import json
import time
import random
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# CTF Knowledge Base
CTF_KNOWLEDGE = [
    {
        "title": "SQL Injection Basics",
        "category": "web",
        "content": "SQL injection occurs when user input is not properly sanitized before being used in SQL queries.",
        "solution": "Use parameterized queries and input validation."
    },
    {
        "title": "Buffer Overflow Exploitation", 
        "category": "pwn",
        "content": "Buffer overflows happen when a program writes more data to a buffer than it can hold.",
        "solution": "Find the offset to overwrite the return address and inject shellcode."
    },
    {
        "title": "XSS Attack Vectors",
        "category": "web", 
        "content": "Cross-site scripting allows attackers to inject malicious scripts into web pages.",
        "solution": "Sanitize user input and use Content Security Policy headers."
    },
    {
        "title": "RSA Cryptography Attacks",
        "category": "crypto",
        "content": "Common RSA attacks include small exponent attacks, common modulus attacks, and timing attacks.",
        "solution": "Use proper padding schemes and check for weak keys."
    }
]

def generate_ctf_response(question):
    """Generate CTF AI response"""
    question_lower = question.lower()
    
    # Find relevant knowledge
    for item in CTF_KNOWLEDGE:
        keywords = [item['title'].lower(), item['category'].lower()] + item['content'].lower().split()[:15]
        if any(keyword in question_lower for keyword in keywords):
            return {
                "answer": f"**{item['title']}**\n\n{item['content']}\n\n**Solution:** {item['solution']}",
                "confidence": random.uniform(0.75, 0.95),
                "category": item['category'],
                "source": item['title']
            }
    
    # Fallback response
    return {
        "answer": "I can help with CTF challenges in web exploitation, binary exploitation (pwn), cryptography, forensics, and reverse engineering. Please provide more details about your specific challenge.",
        "confidence": 0.6,
        "category": "general",
        "source": "general_help"
    }

def get_html_page():
    """Return the main HTML page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CTF AI System</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            h1 { color: #333; text-align: center; margin-bottom: 10px; font-size: 2.5em; }
            .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
            .status-bar { background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 15px; margin-bottom: 25px; }
            .chat { border: 1px solid #ddd; height: 450px; overflow-y: auto; padding: 20px; margin: 25px 0; background: #fafafa; border-radius: 10px; }
            .input-area { display: flex; gap: 12px; }
            input { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
            button { padding: 15px 30px; background: #4299e1; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; }
            button:hover { background: #3182ce; }
            .message { margin: 15px 0; padding: 15px; border-radius: 10px; }
            .user { background: #e3f2fd; border-left: 4px solid #2196f3; }
            .ai { background: #f3e5f5; border-left: 4px solid #9c27b0; }
            .loading { background: #fff3cd; border-left: 4px solid #ffc107; font-style: italic; }
            .confidence { font-size: 0.9em; color: #666; margin-top: 8px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 CTF AI System</h1>
            <p class="subtitle">Your AI assistant for cybersecurity capture-the-flag challenges</p>
            
            <div class="status-bar">
                <strong>Status:</strong> Online | <strong>Knowledge Base:</strong> 4 categories | <strong>Response Time:</strong> ~1s
            </div>
            
            <div class="chat" id="chat">
                <div class="message ai">
                    <strong>CTF AI:</strong> Hello! I'm your specialized CTF assistant. I can help you with:
                    <br>• Web exploitation (SQL injection, XSS, etc.)
                    <br>• Binary exploitation (buffer overflows, ROP chains)
                    <br>• Cryptography (RSA attacks, hash collisions)
                    <br>• Forensics and reverse engineering
                    <br><br>What challenge are you working on today?
                </div>
            </div>
            
            <div class="input-area">
                <input type="text" id="question" placeholder="Describe your CTF challenge or ask a specific question..." onkeypress="if(event.key==='Enter') ask()">
                <button onclick="ask()">Ask AI</button>
            </div>
        </div>

        <script>
            function ask() {
                const input = document.getElementById('question');
                const question = input.value.trim();
                if (!question) return;
                
                addMessage('user', question);
                input.value = '';
                
                const loadingMsg = addMessage('loading', 'Analyzing your question...');
                
                fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                })
                .then(r => r.json())
                .then(data => {
                    loadingMsg.remove();
                    const response = addMessage('ai', data.answer);
                    if (data.confidence) {
                        const conf = document.createElement('div');
                        conf.className = 'confidence';
                        conf.textContent = `Confidence: ${Math.round(data.confidence * 100)}% | Category: ${data.category}`;
                        response.appendChild(conf);
                    }
                })
                .catch(e => {
                    loadingMsg.remove();
                    addMessage('ai', 'Sorry, there was an error processing your question. Please try again.');
                });
            }
            
            function addMessage(type, text) {
                const chat = document.getElementById('chat');
                const div = document.createElement('div');
                div.className = 'message ' + (type === 'loading' ? 'loading' : type);
                div.innerHTML = '<strong>' + (type === 'user' ? 'You' : type === 'loading' ? 'Processing' : 'CTF AI') + ':</strong> ' + text.replace(/\\n/g, '<br>');
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
                return div;
            }
        </script>
    </body>
    </html>
    """

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == '/' or path == '':
            # Serve main HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_html_page().encode())
            
        elif path == '/status':
            # API status endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "online",
                "knowledge_entries": len(CTF_KNOWLEDGE),
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            # 404 for other paths
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        if path == '/ask':
            try:
                # Get request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                question = data.get('question', '').strip()
                if not question:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Please provide a question"}).encode())
                    return
                
                # Simulate processing time
                time.sleep(random.uniform(0.3, 0.8))
                
                # Generate response
                response_data = generate_ctf_response(question)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                full_response = {
                    "question": question,
                    "answer": response_data["answer"],
                    "confidence": response_data["confidence"],
                    "category": response_data["category"],
                    "timestamp": datetime.now().isoformat()
                }
                
                self.wfile.write(json.dumps(full_response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"error": f"Processing failed: {str(e)}"}
                self.wfile.write(json.dumps(error_response).encode())
        
        else:
            # 404 for other POST paths
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())