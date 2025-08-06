"""
CTF AI System - Vercel Serverless Function
"""

from flask import Flask, request, jsonify
import json
import time
import random
from datetime import datetime

app = Flask(__name__)

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

@app.route('/')
def home():
    """Main landing page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CTF AI System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .chat { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 15px; margin: 20px 0; background: #fafafa; }
            .input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #e3f2fd; }
            .ai { background: #f3e5f5; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 CTF AI System</h1>
            <p>Ask me about cybersecurity CTF challenges!</p>
            
            <div class="chat" id="chat"></div>
            
            <div class="input-area">
                <input type="text" id="question" placeholder="Ask about your CTF challenge..." onkeypress="if(event.key==='Enter') ask()">
                <button onclick="ask()">Ask</button>
            </div>
        </div>

        <script>
            function ask() {
                const input = document.getElementById('question');
                const question = input.value.trim();
                if (!question) return;
                
                addMessage('user', question);
                input.value = '';
                
                fetch('/api/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                })
                .then(r => r.json())
                .then(data => {
                    addMessage('ai', data.answer + '\\n\\nConfidence: ' + Math.round(data.confidence * 100) + '%');
                })
                .catch(e => addMessage('ai', 'Error occurred. Please try again.'));
            }
            
            function addMessage(type, text) {
                const chat = document.getElementById('chat');
                const div = document.createElement('div');
                div.className = 'message ' + type;
                div.innerHTML = '<strong>' + (type === 'user' ? 'You' : 'CTF AI') + ':</strong> ' + text.replace(/\\n/g, '<br>');
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/', methods=['POST'])
def ask_question():
    """Handle CTF questions"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Please provide a question"}), 400
        
        # Simulate processing time
        time.sleep(random.uniform(0.2, 0.6))
        
        response = generate_ctf_response(question)
        
        return jsonify({
            "question": question,
            "answer": response["answer"],
            "confidence": response["confidence"],
            "category": response["category"],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/status')
def status():
    """API status"""
    return jsonify({
        "status": "online",
        "knowledge_entries": len(CTF_KNOWLEDGE),
        "timestamp": datetime.now().isoformat()
    })

# For Vercel deployment
app.wsgi_app

if __name__ == '__main__':
    app.run(debug=True)