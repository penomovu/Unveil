"""
Client-side AI engine for CTF assistance using lightweight models
"""

import json
import logging
import re
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CTFKnowledgeBase:
    """CTF-specific knowledge base and reasoning engine"""
    
    def __init__(self):
        self.categories = {
            'web': ['sql injection', 'xss', 'csrf', 'directory traversal', 'lfi', 'rfi', 'ssrf', 'command injection'],
            'crypto': ['caesar cipher', 'vigenere', 'rsa', 'aes', 'base64', 'hash cracking', 'frequency analysis'],
            'pwn': ['buffer overflow', 'rop', 'ret2libc', 'format string', 'heap exploitation', 'stack canary'],
            'reverse': ['disassembly', 'decompilation', 'debugging', 'string analysis', 'packing', 'obfuscation'],
            'forensics': ['file analysis', 'network analysis', 'memory dump', 'steganography', 'metadata'],
            'osint': ['social media', 'search engines', 'whois', 'dns', 'geolocation', 'people search'],
            'misc': ['programming', 'logic puzzles', 'encoding', 'protocols', 'automation']
        }
        
        self.techniques = {
            'sql_injection': {
                'description': 'Database query manipulation vulnerability',
                'payloads': ["' OR 1=1--", "admin'--", "' UNION SELECT * FROM users--"],
                'tools': ['sqlmap', 'burp suite', 'manual testing'],
                'detection': ['error messages', 'time delays', 'blind techniques']
            },
            'xss': {
                'description': 'Cross-site scripting vulnerability',
                'payloads': ['<script>alert(1)</script>', '<img src=x onerror=alert(1)>', 'javascript:alert(1)'],
                'tools': ['burp suite', 'xsstrike', 'manual testing'],
                'types': ['reflected', 'stored', 'dom-based']
            },
            'buffer_overflow': {
                'description': 'Memory corruption vulnerability',
                'steps': ['find vulnerability', 'control EIP', 'find bad chars', 'find return address', 'exploit'],
                'tools': ['gdb', 'immunity debugger', 'pwntools', 'checksec'],
                'techniques': ['shellcode injection', 'return-to-libc', 'rop chains']
            },
            'caesar_cipher': {
                'description': 'Simple substitution cipher with fixed shift',
                'approach': ['try all 25 shifts', 'frequency analysis', 'look for common words'],
                'tools': ['online decoders', 'python scripts', 'manual shifting'],
                'indicators': ['shifted alphabet', 'preserved word length', 'pattern preservation']
            }
        }
        
        self.tools = {
            'web': ['burp suite', 'dirb', 'gobuster', 'nikto', 'wfuzz', 'sqlmap', 'nmap'],
            'crypto': ['john the ripper', 'hashcat', 'openssl', 'python', 'sage', 'factordb'],
            'pwn': ['gdb', 'ghidra', 'ida', 'pwntools', 'ropper', 'checksec', 'strings'],
            'reverse': ['ghidra', 'ida', 'x64dbg', 'ollydbg', 'radare2', 'strings', 'file'],
            'forensics': ['autopsy', 'volatility', 'wireshark', 'binwalk', 'exiftool', 'steghide'],
            'osint': ['maltego', 'shodan', 'google dorks', 'whois', 'nslookup', 'social-analyzer']
        }

class ClientSideAI:
    """Client-side AI implementation for CTF assistance"""
    
    def __init__(self):
        self.knowledge_base = CTFKnowledgeBase()
        self.context_window = 4096
        self.model_type = "CTF-Specialist-AI"
        self.writeups_knowledge = []
        self.conversation_history = []
        
    def load_model_from_server(self, model_data: Dict[str, Any]) -> bool:
        """Load model data downloaded from server"""
        try:
            logger.info(f"Loading client-side model: {model_data.get('name', 'Unknown')}")
            
            # Parse model configuration
            config = json.loads(model_data.get('config_data', '{}'))
            self.context_window = config.get('context_window', 4096)
            self.model_type = config.get('base_model', 'CTF-Specialist-AI')
            
            # Load knowledge from writeups
            if 'training_data_count' in config:
                logger.info(f"Model trained on {config['training_data_count']} writeups")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load client-side model: {e}")
            return False
    
    def update_knowledge(self, writeups: List[Dict[str, Any]]) -> None:
        """Update knowledge base with new writeups"""
        self.writeups_knowledge = writeups
        logger.info(f"Updated knowledge base with {len(writeups)} writeups")
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the question to determine category and intent"""
        question_lower = question.lower()
        
        # Detect category
        detected_category = 'misc'
        confidence = 0.0
        
        for category, keywords in self.knowledge_base.categories.items():
            matches = sum(1 for keyword in keywords if keyword in question_lower)
            category_confidence = matches / len(keywords)
            
            if category_confidence > confidence:
                confidence = category_confidence
                detected_category = category
        
        # Detect specific techniques
        detected_techniques = []
        for technique, data in self.knowledge_base.techniques.items():
            if any(keyword in question_lower for keyword in technique.split('_')):
                detected_techniques.append(technique)
        
        # Detect question type
        question_type = 'general'
        if any(word in question_lower for word in ['how', 'what', 'why', 'when', 'where']):
            question_type = 'explanation'
        elif any(word in question_lower for word in ['solve', 'exploit', 'find', 'get', 'bypass']):
            question_type = 'solution'
        elif any(word in question_lower for word in ['tool', 'script', 'command']):
            question_type = 'tooling'
        
        return {
            'category': detected_category,
            'confidence': confidence,
            'techniques': detected_techniques,
            'question_type': question_type,
            'keywords': [word for word in question_lower.split() if len(word) > 3]
        }
    
    def find_relevant_writeups(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find relevant writeups based on question analysis"""
        relevant = []
        keywords = analysis['keywords']
        category = analysis['category']
        
        for writeup in self.writeups_knowledge:
            score = 0
            
            # Category match
            if writeup.get('category', '').lower() == category:
                score += 5
            
            # Keyword matches in title and content
            title = writeup.get('title', '').lower()
            content = writeup.get('content', '').lower()
            
            for keyword in keywords:
                if keyword in title:
                    score += 3
                if keyword in content:
                    score += 1
            
            if score > 0:
                writeup['relevance_score'] = score
                relevant.append(writeup)
        
        # Sort by relevance and return top 3
        relevant.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return relevant[:3]
    
    def generate_ctf_response(self, question: str) -> str:
        """Generate comprehensive CTF response"""
        start_time = time.time()
        
        # Analyze the question
        analysis = self.analyze_question(question)
        category = analysis['category']
        techniques = analysis['techniques']
        question_type = analysis['question_type']
        
        # Find relevant writeups
        relevant_writeups = self.find_relevant_writeups(analysis)
        
        # Build response based on analysis
        response_parts = []
        
        # Add category-specific introduction
        if category in self.knowledge_base.categories:
            response_parts.append(f"This appears to be a {category.upper()} challenge.")
        
        # Add technique-specific guidance
        if techniques:
            for technique in techniques[:2]:  # Limit to 2 techniques
                if technique in self.knowledge_base.techniques:
                    tech_info = self.knowledge_base.techniques[technique]
                    response_parts.append(f"\n**{technique.replace('_', ' ').title()}**: {tech_info['description']}")
                    
                    if 'payloads' in tech_info:
                        response_parts.append(f"Common payloads: {', '.join(tech_info['payloads'][:2])}")
                    
                    if 'tools' in tech_info:
                        response_parts.append(f"Recommended tools: {', '.join(tech_info['tools'][:3])}")
        
        # Add writeup-based insights
        if relevant_writeups:
            response_parts.append("\n**Based on similar challenges:**")
            for writeup in relevant_writeups[:2]:
                title = writeup.get('title', 'Unknown')
                content_snippet = writeup.get('content', '')[:200] + "..."
                response_parts.append(f"- **{title}**: {content_snippet}")
        
        # Add category-specific tools and techniques
        if category in self.knowledge_base.tools:
            tools = self.knowledge_base.tools[category]
            response_parts.append(f"\n**Useful tools for {category}**: {', '.join(tools[:5])}")
        
        # Add general methodology based on question type
        if question_type == 'solution':
            response_parts.append(self._get_solution_methodology(category))
        elif question_type == 'explanation':
            response_parts.append(self._get_explanation_content(category, techniques))
        elif question_type == 'tooling':
            response_parts.append(self._get_tooling_advice(category))
        
        # Add specific guidance if no relevant writeups found
        if not relevant_writeups:
            response_parts.append(self._get_general_guidance(category, question))
        
        response = "\n".join(response_parts)
        
        # Add processing time info
        processing_time = time.time() - start_time
        response += f"\n\n*Response generated in {processing_time:.2f}s using {self.model_type}*"
        
        return response.strip()
    
    def _get_solution_methodology(self, category: str) -> str:
        """Get solution methodology for category"""
        methodologies = {
            'web': "\n**General Web Exploitation Approach:**\n1. Enumerate the application\n2. Identify input points\n3. Test for common vulnerabilities\n4. Exploit and extract data",
            'crypto': "\n**Cryptography Challenge Approach:**\n1. Identify the cipher/encryption type\n2. Look for patterns or weaknesses\n3. Try known attacks or tools\n4. Decrypt or break the system",
            'pwn': "\n**Binary Exploitation Approach:**\n1. Analyze the binary (checksec, file)\n2. Find the vulnerability\n3. Develop exploit strategy\n4. Write and test the exploit",
            'reverse': "\n**Reverse Engineering Approach:**\n1. Analyze file type and packing\n2. Static analysis with disassembler\n3. Dynamic analysis with debugger\n4. Extract the flag or understand logic"
        }
        return methodologies.get(category, "\n**General Approach:**\n1. Understand the challenge\n2. Research relevant techniques\n3. Apply systematic methodology\n4. Verify and document solution")
    
    def _get_explanation_content(self, category: str, techniques: List[str]) -> str:
        """Get explanation content for category/techniques"""
        if techniques:
            explanations = []
            for technique in techniques[:2]:
                if technique in self.knowledge_base.techniques:
                    tech_data = self.knowledge_base.techniques[technique]
                    explanations.append(f"\n**{technique.replace('_', ' ').title()} Explanation:**")
                    explanations.append(tech_data['description'])
                    if 'steps' in tech_data:
                        explanations.append(f"Steps: {' → '.join(tech_data['steps'])}")
            return "\n".join(explanations)
        
        return f"\n**{category.title()} Category Overview:**\nThis category focuses on {', '.join(self.knowledge_base.categories.get(category, ['various techniques']))}."
    
    def _get_tooling_advice(self, category: str) -> str:
        """Get tooling advice for category"""
        if category in self.knowledge_base.tools:
            tools = self.knowledge_base.tools[category]
            return f"\n**Essential Tools for {category.title()}:**\n" + "\n".join([f"• {tool}" for tool in tools])
        return "\n**General Tools:** Use appropriate tools for your specific challenge type."
    
    def _get_general_guidance(self, category: str, question: str) -> str:
        """Get general guidance when no specific writeups match"""
        guidance = {
            'web': "Start by enumerating the web application, checking for common vulnerabilities like SQL injection, XSS, and directory traversal.",
            'crypto': "First identify the cipher type. Look for patterns, known plaintext, or mathematical weaknesses.",
            'pwn': "Begin with basic binary analysis using 'file' and 'checksec'. Look for obvious vulnerabilities in the source code or binary.",
            'reverse': "Start with 'strings' and 'file' commands. Use a disassembler like Ghidra for static analysis.",
            'forensics': "Examine file metadata, run 'binwalk' for embedded files, and use appropriate analysis tools.",
            'osint': "Start with basic searches and gradually narrow down using specific techniques and tools."
        }
        
        return f"\n**Getting Started:** {guidance.get(category, 'Break down the problem systematically and research the specific techniques involved.')}"

# Global client-side AI instance
client_ai = ClientSideAI()