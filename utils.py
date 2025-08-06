"""
Utility functions for the CTF AI system.
"""

import os
import json
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
        ]
    )
    
    # Add file handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

def clean_filename(filename: str) -> str:
    """Clean filename for safe filesystem use."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename or "unnamed"

def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except FileNotFoundError:
        return ""

def save_json(data: Any, filepath: str, indent: int = 2):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading JSON from {filepath}: {str(e)}")
        return None

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc
    except:
        return ""

def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize URL, making it absolute if needed."""
    if not url:
        return ""
    
    # If URL is already absolute, return as is
    if url.startswith(('http://', 'https://')):
        return url
    
    # If base_url provided, make URL absolute
    if base_url:
        return urljoin(base_url, url)
    
    return url

def extract_text_summary(text: str, max_words: int = 50) -> str:
    """Extract a summary of text content."""
    if not text:
        return ""
    
    # Clean and split into words
    words = text.strip().split()
    
    if len(words) <= max_words:
        return text
    
    # Take first max_words and add ellipsis
    summary = ' '.join(words[:max_words])
    return f"{summary}..."

def detect_ctf_keywords(text: str) -> List[str]:
    """Detect CTF-related keywords in text."""
    ctf_keywords = [
        # General CTF terms
        'ctf', 'capture the flag', 'writeup', 'solution', 'challenge',
        'flag', 'team', 'competition', 'exploit', 'vulnerability',
        
        # Categories
        'web', 'crypto', 'pwn', 'reverse', 'forensics', 'misc',
        'cryptography', 'steganography', 'binary exploitation',
        'reverse engineering', 'web security',
        
        # Techniques
        'buffer overflow', 'sql injection', 'xss', 'csrf', 'lfi', 'rfi',
        'rop', 'ret2libc', 'format string', 'heap overflow',
        
        # Tools
        'burp', 'metasploit', 'nmap', 'wireshark', 'ida', 'ghidra',
        'volatility', 'john', 'hashcat', 'sqlmap', 'dirb', 'gobuster'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in ctf_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords

def estimate_difficulty(text: str) -> str:
    """Estimate difficulty level based on text content."""
    text_lower = text.lower()
    
    # Difficulty indicators
    easy_indicators = ['easy', 'beginner', 'simple', 'basic', 'tutorial', 'intro']
    medium_indicators = ['medium', 'intermediate', 'moderate']
    hard_indicators = ['hard', 'difficult', 'advanced', 'complex', 'challenging']
    expert_indicators = ['expert', 'insane', 'extreme', 'nightmare', 'hardcore']
    
    # Count indicators
    easy_count = sum(1 for word in easy_indicators if word in text_lower)
    medium_count = sum(1 for word in medium_indicators if word in text_lower)
    hard_count = sum(1 for word in hard_indicators if word in text_lower)
    expert_count = sum(1 for word in expert_indicators if word in text_lower)
    
    # Determine difficulty
    counts = {
        'easy': easy_count,
        'medium': medium_count,
        'hard': hard_count,
        'expert': expert_count
    }
    
    max_count = max(counts.values())
    if max_count == 0:
        return 'unknown'
    
    # Return difficulty with highest count
    for difficulty, count in counts.items():
        if count == max_count:
            return difficulty
    
    return 'unknown'

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_info(filepath: str) -> Dict[str, Any]:
    """Get information about a file."""
    if not os.path.exists(filepath):
        return {}
    
    stat = os.stat(filepath)
    return {
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'hash': calculate_file_hash(filepath)
    }

def create_backup(filepath: str) -> str:
    """Create a backup of a file."""
    if not os.path.exists(filepath):
        return ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(filepath, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return ""

def rate_limit_delay(last_request_time: float, min_delay: float = 1.0) -> None:
    """Implement rate limiting with minimum delay."""
    import time
    current_time = time.time()
    elapsed = current_time - last_request_time
    
    if elapsed < min_delay:
        sleep_time = min_delay - elapsed
        time.sleep(sleep_time)

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input for security."""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized

def check_system_resources() -> Dict[str, Any]:
    """Check system resources availability."""
    import psutil
    
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage_percent': psutil.disk_usage('/').percent,
        'available_memory_gb': psutil.virtual_memory().available / (1024**3)
    }

def validate_model_requirements() -> Dict[str, bool]:
    """Validate system requirements for model training."""
    requirements = {
        'torch_available': False,
        'transformers_available': False,
        'sufficient_memory': False,
        'sufficient_disk': False
    }
    
    try:
        import torch
        requirements['torch_available'] = True
    except ImportError:
        pass
    
    try:
        import transformers
        requirements['transformers_available'] = True
    except ImportError:
        pass
    
    try:
        resources = check_system_resources()
        requirements['sufficient_memory'] = resources['available_memory_gb'] > 2.0
        requirements['sufficient_disk'] = resources['disk_usage_percent'] < 90
    except:
        pass
    
    return requirements

def create_error_response(error_message: str, error_code: str = "UNKNOWN") -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        'success': False,
        'error': {
            'message': error_message,
            'code': error_code,
            'timestamp': datetime.now().isoformat()
        }
    }

def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create standardized success response."""
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return response
