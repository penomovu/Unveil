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
    """Generate CTF AI response with better context understanding"""
    question_lower = question.lower()
    
    # Check for greetings first
    if any(greeting in question_lower for greeting in ['hi', 'hey', 'hello', 'sup', 'yo']):
        return {
            "answer": "Hey there! I'm ready to help you tackle some CTF challenges. What type of security challenge are you working on? I can assist with web vulnerabilities, binary exploitation, cryptography, forensics, or reverse engineering.",
            "confidence": 0.95,
            "category": "greeting",
            "source": "greeting_response"
        }
    
    # Check for general category questions
    category_questions = {
        'web': {
            'keywords': ['web', 'website', 'http', 'browser', 'server'],
            'response': "Web exploitation is a major CTF category focusing on vulnerabilities in web applications. Common attack vectors include:\n\n• **SQL Injection** - Exploiting database queries through unsanitized input\n• **Cross-Site Scripting (XSS)** - Injecting malicious scripts into web pages\n• **Directory Traversal** - Accessing files outside web root\n• **Authentication Bypass** - Circumventing login mechanisms\n• **Command Injection** - Executing system commands through web input\n\nWhat specific web vulnerability are you investigating?"
        },
        'pwn': {
            'keywords': ['pwn', 'binary', 'exploitation', 'buffer', 'overflow', 'shellcode'],
            'response': "Binary exploitation (pwn) involves finding and exploiting vulnerabilities in compiled programs. Key techniques include:\n\n• **Buffer Overflows** - Overwriting memory to control program flow\n• **Return-to-libc** - Calling library functions instead of injecting shellcode\n• **ROP Chains** - Chaining gadgets to bypass DEP/NX protections\n• **Format String Bugs** - Exploiting printf-style functions\n• **Heap Exploitation** - Attacking dynamic memory allocation\n\nAre you working on a specific binary challenge?"
        },
        'crypto': {
            'keywords': ['crypto', 'cryptography', 'cipher', 'hash', 'rsa', 'encryption'],
            'response': "Cryptography challenges involve breaking or bypassing encryption and hashing schemes. Common attack vectors include:\n\n• **RSA Attacks** - Factoring weak keys, small exponents, common modulus\n• **Classical Ciphers** - Caesar, Vigenère, substitution ciphers\n• **Hash Attacks** - Rainbow tables, collision attacks, length extensions\n• **Block Cipher Attacks** - ECB mode weaknesses, padding oracles\n• **Randomness Flaws** - Predictable PRNGs, weak entropy\n\nWhat type of cryptographic challenge are you facing?"
        },
        'forensics': {
            'keywords': ['forensics', 'file', 'image', 'network', 'pcap', 'steganography'],
            'response': "Digital forensics challenges involve analyzing data to find hidden information. Common techniques include:\n\n• **File Analysis** - Examining file headers, metadata, hidden data\n• **Network Forensics** - Analyzing packet captures (PCAP files)\n• **Steganography** - Finding hidden messages in images, audio, text\n• **Memory Forensics** - Analyzing RAM dumps for artifacts\n• **Timeline Analysis** - Reconstructing events from logs\n\nWhat type of evidence are you analyzing?"
        }
    }
    
    # Check for category-specific questions
    for category, info in category_questions.items():
        if any(keyword in question_lower for keyword in info['keywords']):
            return {
                "answer": info['response'],
                "confidence": random.uniform(0.85, 0.95),
                "category": category,
                "source": f"{category}_overview"
            }
    
    # Check for specific technique questions
    for item in CTF_KNOWLEDGE:
        # More precise matching - look for exact technique names or very specific keywords
        specific_keywords = [item['title'].lower().replace(' ', ''), item['category']]
        title_words = item['title'].lower().split()
        
        if (any(keyword in question_lower.replace(' ', '') for keyword in specific_keywords) or
            all(word in question_lower for word in title_words if len(word) > 3)):
            return {
                "answer": f"**{item['title']}**\n\n{item['content']}\n\n**Solution Approach:** {item['solution']}\n\nNeed help with a specific {item['category']} challenge? Share more details and I can provide targeted guidance.",
                "confidence": random.uniform(0.80, 0.95),
                "category": item['category'],
                "source": item['title']
            }
    
    # Enhanced fallback responses based on question content
    if any(word in question_lower for word in ['challenge', 'ctf', 'flag', 'exploit']):
        return {
            "answer": "I'd be happy to help with your CTF challenge! To provide the most relevant guidance, could you share:\n\n• What category is it (web, pwn, crypto, forensics, reversing)?\n• Any error messages or clues you've found?\n• What you've already tried?\n\nThe more context you provide, the better I can assist you.",
            "confidence": 0.75,
            "category": "help",
            "source": "contextual_help"
        }
    
    # General fallback
    return {
        "answer": "I specialize in CTF (Capture The Flag) cybersecurity challenges. I can help you with web exploitation, binary exploitation, cryptography, digital forensics, and reverse engineering.\n\nWhat specific challenge or topic would you like assistance with?",
        "confidence": 0.65,
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