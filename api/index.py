# Vercel API endpoint for the CTF AI System
import sys
import os

# Add the root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# This is the entry point for Vercel
def handler(request, context):
    return app(request, context)

# For Vercel's WSGI compatibility
application = app

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)