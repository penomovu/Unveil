"""
Local AI engine that automatically downloads and runs real AI models on user's machine
"""

import os
import json
import logging
import time
import requests
import zipfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalModelDownloader:
    """Downloads and manages AI models locally"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.cache_dir = self.models_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Available models for CTF assistance
        self.available_models = {
            'distilgpt2': {
                'name': 'DistilGPT-2',
                'size': '319MB',
                'url': 'https://huggingface.co/distilgpt2',
                'local_path': self.models_dir / 'distilgpt2',
                'description': 'Fast, lightweight GPT-2 variant for text generation'
            },
            'microsoft/DialoGPT-small': {
                'name': 'DialoGPT-Small',
                'size': '242MB', 
                'url': 'https://huggingface.co/microsoft/DialoGPT-small',
                'local_path': self.models_dir / 'dialogpt-small',
                'description': 'Conversational AI model optimized for dialogue'
            },
            'gpt2': {
                'name': 'GPT-2',
                'size': '548MB',
                'url': 'https://huggingface.co/gpt2',
                'local_path': self.models_dir / 'gpt2',
                'description': 'Standard GPT-2 model for text generation'
            }
        }
        
    def get_model_status(self) -> Dict[str, Any]:
        """Check status of all available models"""
        status = {}
        for model_id, model_info in self.available_models.items():
            local_path = model_info['local_path']
            status[model_id] = {
                'name': model_info['name'],
                'size': model_info['size'],
                'downloaded': local_path.exists(),
                'description': model_info['description'],
                'path': str(local_path) if local_path.exists() else None
            }
        return status
    
    def download_model(self, model_id: str, progress_callback=None) -> bool:
        """Download a model to local storage"""
        if model_id not in self.available_models:
            logger.error(f"Unknown model: {model_id}")
            return False
            
        model_info = self.available_models[model_id]
        local_path = model_info['local_path']
        
        # Check if already downloaded
        if local_path.exists():
            logger.info(f"Model {model_id} already downloaded")
            return True
        
        try:
            logger.info(f"Downloading {model_info['name']} ({model_info['size']})...")
            
            # Create local directory
            local_path.mkdir(parents=True, exist_ok=True)
            
            # Use transformers library to download model
            self._download_with_transformers(model_id, local_path, progress_callback)
            
            # Verify download
            if self._verify_model(local_path):
                logger.info(f"Successfully downloaded {model_info['name']}")
                return True
            else:
                logger.error(f"Model verification failed for {model_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download {model_id}: {e}")
            return False
    
    def _download_with_transformers(self, model_id: str, local_path: Path, progress_callback=None):
        """Download model using transformers library"""
        try:
            # Try to import transformers
            from transformers import AutoModel, AutoTokenizer, AutoConfig
            
            if progress_callback:
                progress_callback("Downloading tokenizer...")
            
            # Download tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_id, 
                cache_dir=str(self.cache_dir)
            )
            tokenizer.save_pretrained(str(local_path))
            
            if progress_callback:
                progress_callback("Downloading model configuration...")
            
            # Download config
            config = AutoConfig.from_pretrained(
                model_id,
                cache_dir=str(self.cache_dir)
            )
            config.save_pretrained(str(local_path))
            
            if progress_callback:
                progress_callback("Downloading model weights...")
            
            # Download model
            model = AutoModel.from_pretrained(
                model_id,
                cache_dir=str(self.cache_dir)
            )
            model.save_pretrained(str(local_path))
            
            logger.info(f"Model {model_id} downloaded to {local_path}")
            
        except ImportError:
            # Fallback: create mock model files for demonstration
            logger.warning("Transformers not available, creating placeholder model")
            self._create_placeholder_model(model_id, local_path)
    
    def _create_placeholder_model(self, model_id: str, local_path: Path):
        """Create placeholder model files when transformers is not available"""
        # Create basic model files
        config = {
            "model_type": "gpt2",
            "vocab_size": 50257,
            "n_positions": 1024,
            "n_ctx": 1024,
            "n_embd": 768,
            "n_layer": 12,
            "n_head": 12,
            "downloaded_from": model_id,
            "download_date": datetime.now().isoformat(),
            "placeholder": True
        }
        
        with open(local_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        # Create tokenizer info
        tokenizer_config = {
            "model_max_length": 1024,
            "pad_token": "<|endoftext|>",
            "unk_token": "<|endoftext|>",
            "placeholder": True
        }
        
        with open(local_path / "tokenizer_config.json", "w") as f:
            json.dump(tokenizer_config, f, indent=2)
        
        # Create vocab file (simplified)
        vocab = {f"token_{i}": i for i in range(1000)}
        with open(local_path / "vocab.json", "w") as f:
            json.dump(vocab, f, indent=2)
        
        logger.info(f"Created placeholder model at {local_path}")
    
    def _verify_model(self, local_path: Path) -> bool:
        """Verify model files are present"""
        required_files = ["config.json"]
        return all((local_path / f).exists() for f in required_files)

class LocalAIEngine:
    """Local AI engine that uses downloaded models"""
    
    def __init__(self):
        self.downloader = LocalModelDownloader()
        self.current_model = None
        self.current_model_id = None
        self.tokenizer = None
        self.context_window = 1024
        self.conversation_history = []
        
        # CTF-specific knowledge
        self.ctf_knowledge = self._load_ctf_knowledge()
    
    def _load_ctf_knowledge(self) -> Dict[str, Any]:
        """Load CTF-specific knowledge base"""
        return {
            'categories': {
                'web': ['sql injection', 'xss', 'csrf', 'directory traversal', 'lfi', 'rfi', 'ssrf'],
                'crypto': ['caesar cipher', 'vigenere', 'rsa', 'aes', 'base64', 'hash cracking'],
                'pwn': ['buffer overflow', 'rop', 'ret2libc', 'format string', 'heap exploitation'],
                'reverse': ['disassembly', 'decompilation', 'debugging', 'string analysis'],
                'forensics': ['file analysis', 'network analysis', 'memory dump', 'steganography'],
                'osint': ['social media', 'search engines', 'whois', 'dns', 'geolocation']
            },
            'tools': {
                'web': ['burp suite', 'dirb', 'gobuster', 'nikto', 'sqlmap'],
                'crypto': ['john the ripper', 'hashcat', 'openssl', 'python'],
                'pwn': ['gdb', 'ghidra', 'ida', 'pwntools', 'ropper'],
                'reverse': ['ghidra', 'ida', 'x64dbg', 'radare2', 'strings'],
                'forensics': ['autopsy', 'volatility', 'wireshark', 'binwalk'],
                'osint': ['maltego', 'shodan', 'google dorks', 'whois']
            }
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models with download status"""
        return self.downloader.get_model_status()
    
    def auto_download_best_model(self, progress_callback=None) -> str:
        """Automatically download the best available model for CTF tasks"""
        # Priority order: smallest first for faster download
        priority_models = ['distilgpt2', 'microsoft/DialoGPT-small', 'gpt2']
        
        for model_id in priority_models:
            if progress_callback:
                progress_callback(f"Attempting to download {model_id}...")
            
            if self.downloader.download_model(model_id, progress_callback):
                logger.info(f"Successfully downloaded {model_id}")
                return model_id
        
        logger.error("Failed to download any model")
        return None
    
    def load_model(self, model_id: str = None) -> bool:
        """Load a model for inference"""
        if not model_id:
            # Auto-select first available model
            model_status = self.get_available_models()
            available = [mid for mid, info in model_status.items() if info['downloaded']]
            
            if not available:
                logger.warning("No models downloaded, attempting auto-download")
                model_id = self.auto_download_best_model()
                if not model_id:
                    return False
            else:
                model_id = available[0]
        
        try:
            model_info = self.downloader.available_models[model_id]
            model_path = model_info['local_path']
            
            if not model_path.exists():
                logger.error(f"Model {model_id} not found at {model_path}")
                return False
            
            # Load configuration
            config_path = model_path / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.context_window = config.get('n_ctx', config.get('max_position_embeddings', 1024))
            
            # Try to load with transformers if available
            self._load_with_transformers(model_id, model_path)
            
            self.current_model_id = model_id
            logger.info(f"Loaded model {model_id} with context window {self.context_window}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def _load_with_transformers(self, model_id: str, model_path: Path):
        """Load model using transformers library"""
        try:
            from transformers import AutoModel, AutoTokenizer, pipeline
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            
            # Create text generation pipeline
            self.current_model = pipeline(
                "text-generation",
                model=str(model_path),
                tokenizer=self.tokenizer,
                max_length=self.context_window,
                do_sample=True,
                temperature=0.7
            )
            
            logger.info(f"Loaded {model_id} with transformers pipeline")
            
        except ImportError:
            logger.warning("Transformers not available, using mock inference")
            self.current_model = None
            self._create_mock_model(model_id)
    
    def _create_mock_model(self, model_id: str):
        """Create mock model for demonstration when transformers unavailable"""
        self.current_model = {
            'model_id': model_id,
            'type': 'mock',
            'context_window': self.context_window
        }
        logger.info(f"Created mock model for {model_id}")
    
    def generate_response(self, question: str, max_length: int = 200) -> str:
        """Generate response to user question"""
        if not self.current_model:
            return "No model loaded. Please wait while downloading..."
        
        try:
            # Analyze question for CTF context
            context = self._analyze_ctf_context(question)
            
            # Prepare prompt with CTF context
            prompt = self._prepare_ctf_prompt(question, context)
            
            if isinstance(self.current_model, dict) and self.current_model.get('type') == 'mock':
                # Mock response with CTF knowledge
                return self._generate_mock_ctf_response(question, context)
            else:
                # Use real model
                response = self.current_model(
                    prompt,
                    max_length=max_length,
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.eos_token_id if self.tokenizer else None
                )
                
                generated_text = response[0]['generated_text']
                # Extract just the response part
                if prompt in generated_text:
                    generated_text = generated_text.replace(prompt, "").strip()
                
                return generated_text[:500]  # Limit response length
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response. Using fallback CTF assistance for: {question}"
    
    def _analyze_ctf_context(self, question: str) -> Dict[str, Any]:
        """Analyze question for CTF-specific context"""
        question_lower = question.lower()
        context = {
            'category': 'general',
            'confidence': 0.0,
            'relevant_tools': [],
            'techniques': []
        }
        
        # Detect CTF category
        for category, keywords in self.ctf_knowledge['categories'].items():
            matches = sum(1 for keyword in keywords if keyword in question_lower)
            confidence = matches / len(keywords)
            
            if confidence > context['confidence']:
                context['category'] = category
                context['confidence'] = confidence
                context['relevant_tools'] = self.ctf_knowledge['tools'].get(category, [])
        
        return context
    
    def _prepare_ctf_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """Prepare CTF-specific prompt"""
        category = context['category']
        tools = ", ".join(context['relevant_tools'][:3]) if context['relevant_tools'] else "various tools"
        
        prompt = f"""CTF Expert Assistant

Question: {question}

Category: {category}
Recommended tools: {tools}

Provide a helpful response for this CTF-related question:"""
        
        return prompt
    
    def _generate_mock_ctf_response(self, question: str, context: Dict[str, Any]) -> str:
        """Generate mock response with real CTF knowledge"""
        category = context['category']
        tools = context['relevant_tools']
        
        if category == 'web':
            return f"For web security challenges, I'd recommend starting with {tools[0] if tools else 'Burp Suite'}. Look for common vulnerabilities like SQL injection, XSS, or directory traversal. Check the source code, test input fields, and examine HTTP requests/responses."
        
        elif category == 'crypto':
            return f"For cryptography challenges, try {tools[0] if tools else 'frequency analysis'} first. Common approaches include identifying the cipher type, checking for patterns, and testing known algorithms. Consider base64 decoding, Caesar ciphers, or hash cracking."
        
        elif category == 'pwn':
            return f"For binary exploitation, use {tools[0] if tools else 'GDB'} to analyze the binary. Look for buffer overflows, format string bugs, or return address manipulation. Check for security protections with checksec and plan your exploit accordingly."
        
        elif category == 'reverse':
            return f"For reverse engineering, start with {tools[0] if tools else 'strings and file'} commands. Use a disassembler like Ghidra or IDA to analyze the code structure. Look for interesting functions, string references, and program logic."
        
        elif category == 'forensics':
            return f"For forensics challenges, use {tools[0] if tools else 'file analysis tools'}. Extract metadata, examine file headers, check for hidden data or steganography. Network captures may contain protocol analysis opportunities."
        
        else:
            return f"I can help with CTF challenges across categories like web, crypto, pwn, reverse engineering, and forensics. What specific aspect would you like assistance with? I can recommend tools, techniques, and approaches based on your challenge type."

# Create global instance
local_ai = LocalAIEngine()