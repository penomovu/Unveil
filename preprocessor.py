"""
Text preprocessing pipeline for CTF writeup data.
Handles cleaning, tokenization, and formatting of collected writeups.
"""

import re
import json
import os
import logging
from typing import List, Dict, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
import html
from collections import Counter

from config import Config

logger = logging.getLogger(__name__)

class TextPreprocessor:
    def __init__(self):
        self.setup_nltk()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # CTF-specific terms that should not be removed
        self.ctf_keywords = {
            'exploit', 'payload', 'shellcode', 'buffer', 'overflow', 'injection',
            'xss', 'csrf', 'sql', 'rce', 'lfi', 'rfi', 'ssrf', 'xxe',
            'crypto', 'cipher', 'hash', 'decode', 'encode', 'base64',
            'reverse', 'forensics', 'steganography', 'binary', 'assembly',
            'pwn', 'rop', 'gadget', 'canary', 'aslr', 'pie', 'nx',
            'flag', 'ctf', 'challenge', 'writeup', 'solution'
        }
        
    def setup_nltk(self):
        """Download required NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove markdown formatting
        text = re.sub(r'```[^`]*```', ' [CODE_BLOCK] ', text)  # Code blocks
        text = re.sub(r'`[^`]*`', ' [INLINE_CODE] ', text)    # Inline code
        text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)  # Links
        text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text) # Images
        text = re.sub(r'#{1,6}\s', '', text)                  # Headers
        text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)       # Bold
        text = re.sub(r'\*([^*]*)\*', r'\1', text)           # Italic
        
        # Clean up common artifacts
        text = re.sub(r'https?://\S+', '[URL]', text)        # URLs
        text = re.sub(r'[a-fA-F0-9]{32,}', '[HASH]', text)   # Long hex strings (hashes)
        text = re.sub(r'[0-9a-fA-F]{8,}', '[HEX]', text)     # Hex values
        text = re.sub(r'[01]{20,}', '[BINARY]', text)        # Binary strings
        
        # Preserve flag formats
        text = re.sub(r'(\w+\{[^}]+\})', r' \1 ', text)      # CTF flags
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)                     # Multiple spaces
        text = re.sub(r'\n+', '\n', text)                    # Multiple newlines
        
        return text.strip()
    
    def extract_metadata(self, writeup: Dict) -> Dict:
        """Extract metadata from writeup content."""
        content = writeup.get('content', '')
        metadata = {
            'word_count': len(content.split()),
            'char_count': len(content),
            'has_code': '[CODE_BLOCK]' in content or '[INLINE_CODE]' in content,
            'has_urls': '[URL]' in content,
            'has_hashes': '[HASH]' in content or '[HEX]' in content,
            'categories': self.extract_categories(content),
            'difficulty_indicators': self.extract_difficulty_indicators(content),
            'tools_mentioned': self.extract_tools(content),
            'techniques': self.extract_techniques(content)
        }
        
        return metadata
    
    def extract_categories(self, text: str) -> List[str]:
        """Extract CTF categories from text."""
        categories = []
        category_keywords = {
            'web': ['web', 'http', 'xss', 'csrf', 'sql injection', 'lfi', 'rfi', 'ssrf'],
            'crypto': ['crypto', 'cipher', 'rsa', 'aes', 'encryption', 'decrypt', 'hash'],
            'pwn': ['pwn', 'buffer overflow', 'rop', 'shellcode', 'binary exploitation'],
            'reverse': ['reverse', 'assembly', 'disassembly', 'ida', 'ghidra', 'decompile'],
            'forensics': ['forensics', 'steganography', 'memory dump', 'pcap', 'wireshark'],
            'misc': ['misc', 'miscellaneous', 'programming', 'scripting']
        }
        
        text_lower = text.lower()
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def extract_difficulty_indicators(self, text: str) -> List[str]:
        """Extract difficulty indicators from text."""
        indicators = []
        text_lower = text.lower()
        
        difficulty_patterns = {
            'easy': ['easy', 'beginner', 'simple', 'basic', 'trivial'],
            'medium': ['medium', 'intermediate', 'moderate'],
            'hard': ['hard', 'difficult', 'advanced', 'complex', 'challenging'],
            'expert': ['expert', 'insane', 'extreme', 'nightmare']
        }
        
        for level, keywords in difficulty_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators.append(level)
        
        return indicators
    
    def extract_tools(self, text: str) -> List[str]:
        """Extract mentioned tools from text."""
        tools = []
        text_lower = text.lower()
        
        common_tools = [
            'burp', 'metasploit', 'nmap', 'wireshark', 'ida', 'ghidra',
            'gdb', 'radare2', 'volatility', 'john', 'hashcat', 'sqlmap',
            'dirb', 'gobuster', 'nikto', 'hydra', 'binwalk', 'strings',
            'ltrace', 'strace', 'objdump', 'readelf', 'hexdump'
        ]
        
        for tool in common_tools:
            if tool in text_lower:
                tools.append(tool)
        
        return tools
    
    def extract_techniques(self, text: str) -> List[str]:
        """Extract mentioned techniques from text."""
        techniques = []
        text_lower = text.lower()
        
        technique_patterns = [
            'buffer overflow', 'sql injection', 'xss', 'csrf', 'lfi', 'rfi',
            'ssrf', 'xxe', 'command injection', 'path traversal', 'rop',
            'ret2libc', 'format string', 'race condition', 'time of check',
            'privilege escalation', 'reverse shell', 'bind shell'
        ]
        
        for technique in technique_patterns:
            if technique in text_lower:
                techniques.append(technique)
        
        return techniques
    
    def create_training_examples(self, writeup: Dict) -> List[Dict]:
        """Create training examples from a writeup."""
        content = writeup['content']
        examples = []
        
        # Split content into sentences
        sentences = sent_tokenize(content)
        
        # Create question-answer pairs
        for i, sentence in enumerate(sentences):
            if len(sentence.split()) < 5:  # Skip very short sentences
                continue
            
            # Create context from surrounding sentences
            start_idx = max(0, i - 2)
            end_idx = min(len(sentences), i + 3)
            context = ' '.join(sentences[start_idx:end_idx])
            
            # Generate questions based on sentence content
            questions = self.generate_questions_for_sentence(sentence, writeup)
            
            for question in questions:
                examples.append({
                    'question': question,
                    'context': context,
                    'answer': sentence,
                    'metadata': writeup.get('metadata', {}),
                    'source': writeup.get('source', ''),
                    'categories': writeup.get('metadata', {}).get('categories', [])
                })
        
        return examples
    
    def generate_questions_for_sentence(self, sentence: str, writeup: Dict) -> List[str]:
        """Generate relevant questions for a sentence."""
        questions = []
        sentence_lower = sentence.lower()
        
        # Tool-based questions
        tools = writeup.get('metadata', {}).get('tools_mentioned', [])
        for tool in tools:
            if tool in sentence_lower:
                questions.append(f"How to use {tool} in CTF challenges?")
                questions.append(f"What is {tool} used for?")
        
        # Technique-based questions
        techniques = writeup.get('metadata', {}).get('techniques', [])
        for technique in techniques:
            if any(word in sentence_lower for word in technique.split()):
                questions.append(f"How does {technique} work?")
                questions.append(f"How to exploit {technique}?")
        
        # Category-based questions
        categories = writeup.get('metadata', {}).get('categories', [])
        for category in categories:
            if category in sentence_lower:
                questions.append(f"What are common {category} vulnerabilities?")
                questions.append(f"How to solve {category} challenges?")
        
        # Generic questions based on content
        if 'flag' in sentence_lower:
            questions.append("How to find the flag?")
            questions.append("Where is the flag located?")
        
        if any(word in sentence_lower for word in ['exploit', 'vulnerability', 'attack']):
            questions.append("How to exploit this vulnerability?")
            questions.append("What is the attack vector?")
        
        if any(word in sentence_lower for word in ['solve', 'solution', 'approach']):
            questions.append("How to solve this challenge?")
            questions.append("What is the solution approach?")
        
        return questions[:3]  # Limit to 3 questions per sentence
    
    def process_writeups(self, writeups: List[Dict]) -> List[Dict]:
        """Process a list of writeups."""
        processed_writeups = []
        
        logger.info(f"Processing {len(writeups)} writeups...")
        
        for i, writeup in enumerate(writeups):
            try:
                # Clean the content
                cleaned_content = self.clean_text(writeup['content'])
                
                # Skip if content is too short
                if len(cleaned_content.split()) < 50:
                    continue
                
                # Extract metadata
                metadata = self.extract_metadata({'content': cleaned_content})
                
                # Create training examples
                training_examples = self.create_training_examples({
                    'content': cleaned_content,
                    'metadata': metadata,
                    'source': writeup.get('source', ''),
                    'url': writeup.get('url', '')
                })
                
                processed_writeup = {
                    'original_title': writeup.get('title', ''),
                    'cleaned_content': cleaned_content,
                    'metadata': metadata,
                    'training_examples': training_examples,
                    'source': writeup.get('source', ''),
                    'url': writeup.get('url', ''),
                    'collected_date': writeup.get('collected_date', ''),
                    'processed_date': Config.get_timestamp()
                }
                
                processed_writeups.append(processed_writeup)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(writeups)} writeups")
                
            except Exception as e:
                logger.error(f"Error processing writeup {i}: {str(e)}")
        
        logger.info(f"Successfully processed {len(processed_writeups)} writeups")
        return processed_writeups
    
    def save_processed_data(self, processed_data: List[Dict], filepath: str):
        """Save processed data to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(processed_data)} processed writeups to {filepath}")
    
    def load_processed_data(self, filepath: str) -> List[Dict]:
        """Load processed data from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_statistics(self, processed_data: List[Dict]) -> Dict:
        """Generate statistics about processed data."""
        stats = {
            'total_writeups': len(processed_data),
            'total_training_examples': sum(len(w['training_examples']) for w in processed_data),
            'categories': Counter(),
            'tools': Counter(),
            'techniques': Counter(),
            'sources': Counter(),
            'avg_length': 0
        }
        
        total_length = 0
        for writeup in processed_data:
            metadata = writeup['metadata']
            stats['categories'].update(metadata.get('categories', []))
            stats['tools'].update(metadata.get('tools_mentioned', []))
            stats['techniques'].update(metadata.get('techniques', []))
            stats['sources'][writeup.get('source', 'unknown')] += 1
            total_length += metadata.get('word_count', 0)
        
        if processed_data:
            stats['avg_length'] = total_length / len(processed_data)
        
        return stats
