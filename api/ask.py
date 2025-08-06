from http.server import BaseHTTPRequestHandler
import json
import time
import random
from datetime import datetime

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

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for asking questions"""
        try:
            # Get request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            question = data.get('question', '').strip()
            if not question:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
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
            self.send_header('Access-Control-Allow-Origin', '*')
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
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": f"Processing failed: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()