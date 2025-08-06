"""
Data collection module for CTF writeups from various sources.
Supports GitHub repositories, blogs, and other public sources.
"""

import requests
import json
import os
import time
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import trafilatura
from typing import List, Dict, Any
import re

from config import Config

logger = logging.getLogger(__name__)

class CTFDataCollector:
    def __init__(self):
        self.sources_file = Config.SOURCES_FILE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CTF-AI-Collector/1.0 (Educational Purpose)'
        })
        
    def get_sources(self) -> List[Dict]:
        """Load data sources from configuration file."""
        try:
            if os.path.exists(self.sources_file):
                with open(self.sources_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Failed to load sources: {str(e)}")
            return []
    
    def add_source(self, url: str, source_type: str, name: str = ""):
        """Add a new data source."""
        sources = self.get_sources()
        
        new_source = {
            'url': url,
            'type': source_type,
            'name': name or urlparse(url).netloc,
            'added_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        sources.append(new_source)
        
        os.makedirs(os.path.dirname(self.sources_file), exist_ok=True)
        with open(self.sources_file, 'w') as f:
            json.dump(sources, f, indent=2)
    
    def collect_from_github_repo(self, repo_url: str) -> List[Dict]:
        """Collect writeups from a GitHub repository."""
        writeups = []
        
        try:
            # Convert GitHub repo URL to API URL
            if 'github.com' in repo_url:
                parts = repo_url.split('/')
                if len(parts) >= 5:
                    owner = parts[3]
                    repo = parts[4]
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
                    
                    writeups.extend(self._collect_github_contents(api_url, repo_url))
            
        except Exception as e:
            logger.error(f"Failed to collect from GitHub repo {repo_url}: {str(e)}")
        
        return writeups
    
    def _collect_github_contents(self, api_url: str, base_url: str, path: str = "") -> List[Dict]:
        """Recursively collect contents from GitHub repository."""
        writeups = []
        
        try:
            response = self.session.get(api_url)
            if response.status_code == 200:
                contents = response.json()
                
                for item in contents:
                    if item['type'] == 'file':
                        # Check if file is likely a writeup
                        if self._is_writeup_file(item['name']):
                            writeup_content = self._get_github_file_content(item['download_url'])
                            if writeup_content:
                                writeups.append({
                                    'title': item['name'],
                                    'content': writeup_content,
                                    'source': 'github',
                                    'url': item['html_url'],
                                    'path': item['path'],
                                    'collected_date': time.strftime('%Y-%m-%d %H:%M:%S')
                                })
                    
                    elif item['type'] == 'dir':
                        # Recursively collect from subdirectories
                        sub_writeups = self._collect_github_contents(item['url'], base_url, item['path'])
                        writeups.extend(sub_writeups)
            
            # Add delay to respect rate limits
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error collecting GitHub contents from {api_url}: {str(e)}")
        
        return writeups
    
    def _get_github_file_content(self, download_url: str) -> str:
        """Download and extract content from GitHub file."""
        try:
            response = self.session.get(download_url)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.error(f"Failed to download file from {download_url}: {str(e)}")
        
        return ""
    
    def _is_writeup_file(self, filename: str) -> bool:
        """Check if a file is likely a CTF writeup."""
        writeup_extensions = ['.md', '.txt', '.rst', '.html']
        writeup_keywords = ['writeup', 'solution', 'ctf', 'challenge', 'exploit', 'readme']
        
        # Check file extension
        if any(filename.lower().endswith(ext) for ext in writeup_extensions):
            return True
        
        # Check filename for keywords
        filename_lower = filename.lower()
        if any(keyword in filename_lower for keyword in writeup_keywords):
            return True
        
        return False
    
    def collect_from_website(self, url: str) -> List[Dict]:
        """Collect writeups from a website/blog."""
        writeups = []
        
        try:
            # Get main page content
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text_content = trafilatura.extract(downloaded)
                
                if text_content and len(text_content) > 500:  # Minimum length filter
                    writeups.append({
                        'title': self._extract_title_from_url(url),
                        'content': text_content,
                        'source': 'website',
                        'url': url,
                        'collected_date': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Try to find additional writeup links
                soup = BeautifulSoup(downloaded, 'html.parser')
                links = self._extract_writeup_links(soup, url)
                
                for link in links[:10]:  # Limit to first 10 links
                    sub_content = self._get_website_content(link)
                    if sub_content:
                        writeups.append({
                            'title': self._extract_title_from_url(link),
                            'content': sub_content,
                            'source': 'website',
                            'url': link,
                            'collected_date': time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    
                    time.sleep(1)  # Respectful crawling
        
        except Exception as e:
            logger.error(f"Failed to collect from website {url}: {str(e)}")
        
        return writeups
    
    def _get_website_content(self, url: str) -> str:
        """Extract text content from a website using trafilatura."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                return trafilatura.extract(downloaded) or ""
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {str(e)}")
        
        return ""
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a reasonable title from URL."""
        try:
            path = urlparse(url).path
            title = path.split('/')[-1] or path.split('/')[-2] or urlparse(url).netloc
            return title.replace('-', ' ').replace('_', ' ').title()
        except:
            return url
    
    def _extract_writeup_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links that likely point to writeups."""
        links = []
        writeup_keywords = ['writeup', 'solution', 'ctf', 'challenge', 'exploit', 'walkthrough']
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().lower()
            
            # Check if link text contains writeup keywords
            if any(keyword in text for keyword in writeup_keywords):
                full_url = urljoin(base_url, href)
                if self._is_valid_writeup_url(full_url):
                    links.append(full_url)
            
            # Check if href contains writeup keywords
            elif any(keyword in href.lower() for keyword in writeup_keywords):
                full_url = urljoin(base_url, href)
                if self._is_valid_writeup_url(full_url):
                    links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _is_valid_writeup_url(self, url: str) -> bool:
        """Check if URL is likely to contain a writeup."""
        try:
            parsed = urlparse(url)
            
            # Skip certain file types
            skip_extensions = ['.pdf', '.zip', '.tar', '.gz', '.jpg', '.png', '.gif']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            # Skip external domains for now (to avoid infinite crawling)
            # This could be made configurable
            return True
            
        except:
            return False
    
    def collect_all_sources(self) -> List[Dict]:
        """Collect writeups from all configured sources."""
        all_writeups = []
        sources = self.get_sources()
        
        logger.info(f"Starting collection from {len(sources)} sources...")
        
        for source in sources:
            logger.info(f"Collecting from {source['name']} ({source['url']})...")
            
            try:
                if source['type'] == 'github':
                    writeups = self.collect_from_github_repo(source['url'])
                elif source['type'] == 'website':
                    writeups = self.collect_from_website(source['url'])
                else:
                    logger.warning(f"Unknown source type: {source['type']}")
                    continue
                
                logger.info(f"Collected {len(writeups)} writeups from {source['name']}")
                all_writeups.extend(writeups)
                
            except Exception as e:
                logger.error(f"Failed to collect from {source['name']}: {str(e)}")
            
            # Add delay between sources
            time.sleep(2)
        
        logger.info(f"Total collected: {len(all_writeups)} writeups")
        return all_writeups
    
    def save_raw_data(self, writeups: List[Dict], filepath: str):
        """Save raw collected data to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(writeups, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(writeups)} writeups to {filepath}")
