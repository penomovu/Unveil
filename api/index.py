"""
Vercel-compatible CTF AI System
Simplified version for serverless deployment without database dependencies
"""

import os
import json
import time
import random
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-demo')

# Mock CTF Knowledge Base (simplified for demo)
MOCK_CTF_KNOWLEDGE = [
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
    }
]

class SimpleCTFAI:
    """Simplified CTF AI for Vercel deployment"""
    
    def __init__(self):
        self.knowledge_base = MOCK_CTF_KNOWLEDGE
        self.model_name = "Simplified CTF AI v1.0"
        
    def generate_response(self, question):
        """Generate a response based on the question"""
        # Simulate processing time
        time.sleep(random.uniform(0.3, 0.8))
        
        question_lower = question.lower()
        
        # Find relevant knowledge
        for item in self.knowledge_base:
            if any(keyword in question_lower for keyword in [
                item['title'].lower(), 
                item['category'].lower(),
                *item['content'].lower().split()[:10]
            ]):
                return {
                    "answer": f"Based on my knowledge about {item['title']}:\n\n{item['content']}\n\nSolution approach: {item['solution']}",
                    "confidence": random.uniform(0.7, 0.95),
                    "category": item['category'],
                    "source": item['title']
                }
        
        # Fallback response
        return {
            "answer": "I can help you with CTF challenges in categories like web exploitation, binary exploitation (pwn), cryptography, forensics, and reverse engineering. Could you provide more specific details about your challenge?",
            "confidence": 0.5,
            "category": "general",
            "source": "fallback"
        }

# Initialize AI
ctf_ai = SimpleCTFAI()

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTF AI System</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        h1 { color: #4a5568; text-align: center; margin-bottom: 30px; font-size: 2.5em; }
        .status { background: #e6fffa; border: 1px solid #38b2ac; border-radius: 5px; padding: 10px; margin-bottom: 20px; color: #2d3748; }
        .chat-container { border: 1px solid #e2e8f0; border-radius: 8px; height: 400px; overflow-y: auto; padding: 20px; margin-bottom: 20px; background: #f7fafc; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user-message { background: #e6fffa; border-left: 4px solid #38b2ac; }
        .ai-message { background: #fff5f5; border-left: 4px solid #f56565; }
        .input-group { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 16px; }
        button { padding: 12px 24px; background: #4299e1; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
        button:hover { background: #3182ce; }
        .loading { color: #718096; font-style: italic; }
        .confidence { font-size: 0.9em; color: #718096; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 CTF AI System</h1>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Ready</span> | 
            <strong>Model:</strong> {{ model_name }} | 
            <strong>Knowledge Base:</strong> {{ knowledge_count }} entries
        </div>
        
        <div class="chat-container" id="chat-container">
            <div class="message ai-message">
                <strong>CTF AI:</strong> Hello! I'm your CTF AI assistant. I can help you with cybersecurity challenges in web exploitation, binary exploitation, cryptography, forensics, and reverse engineering. What challenge are you working on?
            </div>
        </div>
        
        <div class="input-group">
            <input type="text" id="question-input" placeholder="Ask about your CTF challenge..." onkeypress="if(event.key==='Enter') askQuestion()">
            <button onclick="askQuestion()">Ask</button>
        </div>
    </div>

    <script>
        function askQuestion() {
            const input = document.getElementById('question-input');
            const question = input.value.trim();
            
            if (!question) return;
            
            // Add user message
            addMessage('user', question);
            input.value = '';
            
            // Show loading
            const loadingMsg = addMessage('ai', 'Analyzing your question...');
            loadingMsg.classList.add('loading');
            
            // Send question to API
            fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading message
                loadingMsg.remove();
                
                // Add AI response
                const response = addMessage('ai', data.answer);
                if (data.confidence) {
                    const confidenceSpan = document.createElement('div');
                    confidenceSpan.className = 'confidence';
                    confidenceSpan.textContent = `Confidence: ${Math.round(data.confidence * 100)}% | Category: ${data.category}`;
                    response.appendChild(confidenceSpan);
                }
            })
            .catch(error => {
                loadingMsg.remove();
                addMessage('ai', 'Sorry, I encountered an error. Please try again.');
                console.error('Error:', error);
            });
        }
        
        function addMessage(sender, text) {
            const container = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'CTF AI'}:</strong> ${text.replace(/\\n/g, '<br>')}`;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
            return messageDiv;
        }
        
        // Status check
        function checkStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                })
                .catch(() => {
                    document.getElementById('status').textContent = 'Error';
                });
        }
        
        // Check status every 5 seconds
        setInterval(checkStatus, 5000);
        checkStatus();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE, 
                                model_name=ctf_ai.model_name,
                                knowledge_count=len(ctf_ai.knowledge_base))

@app.route('/api/status')
def status():
    """API status endpoint"""
    return jsonify({
        "status": "online",
        "model": ctf_ai.model_name,
        "timestamp": datetime.now().isoformat(),
        "knowledge_entries": len(ctf_ai.knowledge_base)
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    """Ask the CTF AI a question"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question.strip():
            return jsonify({"error": "Please provide a question"}), 400
        
        response = ctf_ai.generate_response(question)
        
        return jsonify({
            "question": question,
            "answer": response["answer"],
            "confidence": response["confidence"],
            "category": response["category"],
            "source": response["source"],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

# WSGI application
application = app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))