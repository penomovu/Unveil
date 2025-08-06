"""
Vercel Serverless Function for CTF AI
"""

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
        "content": "SQL injection occurs when user input is not properly sanitized before being used in SQL queries. Common payloads include ' OR '1'='1, UNION SELECT statements, and time-based blind injection techniques.",
        "solution": "Use parameterized queries, input validation, and web application firewalls."
    },
    {
        "title": "Buffer Overflow Exploitation", 
        "category": "pwn",
        "content": "Buffer overflows happen when a program writes more data to a buffer than it can hold, potentially overwriting adjacent memory. This can lead to code execution by overwriting return addresses.",
        "solution": "Find the offset to overwrite the return address, control EIP/RIP, and inject shellcode or use ROP chains."
    },
    {
        "title": "XSS Attack Vectors",
        "category": "web", 
        "content": "Cross-site scripting allows attackers to inject malicious scripts into web pages. Types include reflected, stored, and DOM-based XSS.",
        "solution": "Sanitize user input, use Content Security Policy headers, and escape output properly."
    },
    {
        "title": "RSA Cryptography Attacks",
        "category": "crypto",
        "content": "Common RSA attacks include small exponent attacks, common modulus attacks, Wiener's attack for small private exponents, and timing attacks.",
        "solution": "Use proper padding schemes like OAEP, check for weak keys, and implement constant-time operations."
    },
    {
        "title": "Format String Vulnerabilities",
        "category": "pwn",
        "content": "Format string bugs occur when user input is used directly as a format string in printf-family functions. Attackers can read/write arbitrary memory.",
        "solution": "Use %n to write to memory addresses, leak stack values with %x/%p, and control format string parameters."
    },
    {
        "title": "Directory Traversal",
        "category": "web",
        "content": "Path traversal vulnerabilities allow attackers to read files outside the intended directory by using ../../../ sequences.",
        "solution": "Input validation, canonicalize paths, use chroot jails, and whitelist allowed files."
    }
]

def generate_ctf_response(question):
    """Generate intelligent CTF AI response"""
    question_lower = question.lower()
    
    # Enhanced keyword matching
    best_match = None
    best_score = 0
    
    for item in CTF_KNOWLEDGE:
        score = 0
        keywords = [item['title'].lower(), item['category'].lower()] + item['content'].lower().split()[:20]
        
        # Calculate relevance score
        for keyword in keywords:
            if keyword in question_lower:
                score += 1
                if keyword in item['category'].lower():
                    score += 2  # Category match bonus
                if keyword in item['title'].lower():
                    score += 3  # Title match bonus
                    
        if score > best_score:
            best_score = score
            best_match = item
    
    if best_match and best_score > 0:
        return {
            "answer": f"**{best_match['title']} - {best_match['category'].upper()} Category**\n\n{best_match['content']}\n\n**Exploitation Steps:**\n{best_match['solution']}\n\n*Need more specific guidance? Describe your exact challenge scenario.*",
            "confidence": min(0.95, 0.6 + (best_score * 0.1)),
            "category": best_match['category'],
            "source": best_match['title']
        }
    
    # Intelligent fallback based on question type
    if any(word in question_lower for word in ['web', 'http', 'cookie', 'session', 'xss', 'sql', 'injection']):
        category = "web"
        answer = "For web exploitation challenges, start by examining the application for common vulnerabilities like SQL injection, XSS, CSRF, or authentication bypasses. Use tools like Burp Suite, check HTTP headers, analyze JavaScript, and test input validation."
    elif any(word in question_lower for word in ['binary', 'exploit', 'buffer', 'overflow', 'pwn', 'shellcode']):
        category = "pwn"
        answer = "For binary exploitation, analyze the binary with tools like gdb, checksec, and objdump. Look for buffer overflows, format string bugs, or ROP gadgets. Consider ASLR, NX, and stack canaries when planning your exploit."
    elif any(word in question_lower for word in ['crypto', 'cipher', 'rsa', 'hash', 'encryption']):
        category = "crypto"
        answer = "For cryptography challenges, identify the encryption scheme, look for implementation weaknesses, check for small exponents, weak keys, or padding oracle attacks. Tools like sage, openssl, and online factorization services can help."
    elif any(word in question_lower for word in ['forensics', 'file', 'image', 'metadata', 'steganography']):
        category = "forensics"
        answer = "For forensics challenges, examine file headers, metadata, and hidden data. Use tools like binwalk, strings, exiftool, and steghide. Check for hidden partitions, alternate data streams, or embedded files."
    else:
        category = "general"
        answer = "I specialize in CTF challenges across web exploitation, binary exploitation (pwn), cryptography, forensics, and reverse engineering. Please provide more details about your specific challenge for targeted assistance."
    
    return {
        "answer": answer,
        "confidence": random.uniform(0.7, 0.85),
        "category": category,
        "source": "ctf_ai_analysis"
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
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
            
            # Simulate AI processing time
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
                "timestamp": datetime.now().isoformat(),
                "model": "CTF-AI-Enhanced"
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
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()