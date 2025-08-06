"""
Vercel Serverless Function for CTF AI Status
"""

from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for status"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "online",
            "model": "CTF-AI-Enhanced",
            "knowledge_entries": 6,
            "categories": ["web", "pwn", "crypto", "forensics", "reverse", "misc"],
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()