"""
Simple data collector for CTF writeups
"""

import requests
import json
import logging
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)

class SimpleDataCollector:
    """Simple data collector without complex dependencies"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect_from_github(self, github_url, limit=5):
        """Collect writeups from GitHub repository"""
        try:
            logger.info(f"Collecting from GitHub: {github_url}")
            
            # Mock GitHub data for demo (in production, use GitHub API)
            mock_writeups = [
                {
                    'title': 'Web Challenge: SQL Injection',
                    'content': 'This web challenge involved finding and exploiting a SQL injection vulnerability in the login form. The payload "admin\' OR 1=1-- " bypassed authentication.',
                    'category': 'web',
                    'difficulty': 'medium',
                    'url': f'{github_url}/web-sqli'
                },
                {
                    'title': 'Crypto Challenge: Caesar Cipher',
                    'content': 'A simple Caesar cipher with shift 13 (ROT13). Decoded the flag by shifting each letter 13 positions in the alphabet.',
                    'category': 'crypto',
                    'difficulty': 'easy',
                    'url': f'{github_url}/crypto-caesar'
                },
                {
                    'title': 'Binary Exploitation: Buffer Overflow',
                    'content': 'Classic buffer overflow in a C program. Found the vulnerable strcpy function and crafted a payload to overwrite the return address.',
                    'category': 'pwn',
                    'difficulty': 'hard',
                    'url': f'{github_url}/pwn-bof'
                },
                {
                    'title': 'Reverse Engineering: Basic Analysis',
                    'content': 'Used Ghidra to analyze the binary. Found the flag comparison in the main function by looking for string constants.',
                    'category': 'reverse',
                    'difficulty': 'medium',
                    'url': f'{github_url}/rev-basic'
                },
                {
                    'title': 'Forensics: Network Analysis',
                    'content': 'Analyzed PCAP file with Wireshark. Found HTTP POST request containing base64-encoded flag in the packet data.',
                    'category': 'forensics',
                    'difficulty': 'easy',
                    'url': f'{github_url}/forensics-pcap'
                }
            ]
            
            # Return limited number for demo
            return mock_writeups[:limit]
            
        except Exception as e:
            logger.error(f"GitHub collection error: {e}")
            return []
    
    def collect_from_website(self, website_url, limit=5):
        """Collect writeups from website"""
        try:
            logger.info(f"Collecting from website: {website_url}")
            
            # Mock website data for demo (in production, implement web scraping)
            mock_writeups = [
                {
                    'title': 'OWASP Top 10: XSS Challenge',
                    'content': 'Found reflected XSS vulnerability in search parameter. Payload: <script>alert(document.cookie)</script> executed successfully.',
                    'category': 'web',
                    'difficulty': 'medium',
                    'url': f'{website_url}/xss-writeup'
                },
                {
                    'title': 'Cryptography: RSA Weak Keys',
                    'content': 'RSA challenge with small prime factors. Used factordb.com to find p and q, then calculated private key using extended Euclidean algorithm.',
                    'category': 'crypto',
                    'difficulty': 'hard',
                    'url': f'{website_url}/rsa-weak'
                },
                {
                    'title': 'Web Security: Directory Traversal',
                    'content': 'Directory traversal vulnerability in file parameter. Used ../../../etc/passwd to read system files.',
                    'category': 'web',
                    'difficulty': 'easy',
                    'url': f'{website_url}/dir-traversal'
                }
            ]
            
            # Return limited number for demo  
            return mock_writeups[:limit]
            
        except Exception as e:
            logger.error(f"Website collection error: {e}")
            return []