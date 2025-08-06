"""
Vercel Serverless Function for CTF AI
"""

from http.server import BaseHTTPRequestHandler
import json
import time
import random
from datetime import datetime

# CTF Knowledge Base
PENTEST_KNOWLEDGE = [
    {
        "title": "Advanced SQL Injection Techniques",
        "category": "web",
        "content": "Beyond basic SQLi: Error-based extraction using EXTRACTVALUE/UPDATEXML, Boolean blind injection with SUBSTRING, Time-based with SLEEP/WAITFOR DELAY, UNION-based with NULL balancing, Second-order injection, and NoSQL injection for MongoDB/CouchDB.",
        "tools": ["sqlmap", "Burp Suite", "SQLNinja", "NoSQLMap"],
        "payloads": ["' UNION SELECT NULL,@@version,NULL-- -", "1' AND (SELECT SUBSTRING(username,1,1) FROM users WHERE id=1)='a'-- -", "'; WAITFOR DELAY '00:00:05'-- -"],
        "solution": "Parameterized queries, stored procedures, input validation, WAF deployment, principle of least privilege"
    },
    {
        "title": "Modern Binary Exploitation",
        "category": "pwn", 
        "content": "Advanced pwn: Stack/heap overflows with ASLR/PIE bypass, ROP/JOP chain construction, ret2libc/ret2syscall, Format string arbitrary write, Use-after-free exploitation, Kernel exploitation techniques, and ARM/x86-64 shellcoding.",
        "tools": ["gdb + GEF/pwndbg", "ROPgadget", "pwntools", "radare2", "Ghidra", "checksec"],
        "payloads": ["cyclic(200)", "p64(pop_rdi) + p64(binsh) + p64(system)", "b'%{}c%{}$hn'.format(target & 0xffff, offset)"],
        "solution": "Stack canaries, ASLR, DEP/NX bit, FORTIFY_SOURCE, Control Flow Integrity (CFI)"
    },
    {
        "title": "Cross-Site Scripting (XSS) Advanced",
        "category": "web",
        "content": "Advanced XSS: DOM-based via innerHTML/document.write, Mutation XSS (mXSS), CSP bypass techniques, JavaScript prototype pollution, PostMessage exploitation, and Electron application XSS.",
        "tools": ["BeEF", "XSStrike", "DOMPurify", "Burp XSS Validator"],
        "payloads": ["<img src=x onerror=alert(1)>", "javascript:alert(document.domain)", "<svg/onload=alert`1`>", "eval(atob('YWxlcnQoMSk='))"],
        "solution": "Content Security Policy, input sanitization, output encoding, HTTPOnly cookies, SameSite attribute"
    },
    {
        "title": "RSA Cryptanalysis Methods",
        "category": "crypto",
        "content": "RSA attacks: Factorization with pollard-rho/quadratic sieve, Small private exponent (Wiener's attack), Common modulus attack, Coppersmith's attack, Fault injection, and timing/power analysis side channels.",
        "tools": ["SageMath", "factordb.com", "RsaCtfTool", "Yafu", "msieve", "OpenSSL"],
        "payloads": ["sage: factor(n)", "python RsaCtfTool.py -n N -e E --attack wiener", "openssl rsautl -decrypt -in cipher.txt"],
        "solution": "Use strong padding (OAEP), key size ≥2048 bits, secure random generation, constant-time implementations"
    },
    {
        "title": "Network Reconnaissance & Exploitation",
        "category": "network",
        "content": "Advanced techniques: Service enumeration with custom scripts, SMB relay attacks, Kerberos attacks (ASREPRoast/Kerberoasting), LDAP injection, DNS poisoning, IPv6 attacks, and wireless security bypasses.",
        "tools": ["nmap", "masscan", "Responder", "Impacket", "BloodHound", "Empire", "Cobalt Strike"],
        "payloads": ["nmap -sC -sV -O -A target", "python GetNPUsers.py domain/ -usersfile users.txt -format john", "responder -I eth0 -wrf"],
        "solution": "Network segmentation, SMB signing, disable LLMNR/NBT-NS, Kerberos pre-authentication, monitoring"
    },
    {
        "title": "Reverse Engineering Methodologies", 
        "category": "reverse",
        "content": "RE techniques: Static analysis with disassemblers, Dynamic analysis with debuggers, Anti-analysis evasion, Malware unpacking, Firmware extraction, Protocol reverse engineering, and mobile app analysis.",
        "tools": ["IDA Pro", "Ghidra", "x64dbg", "OllyDbg", "Cheat Engine", "Frida", "JADX", "binwalk"],
        "payloads": ["objdump -d binary", "strings -a binary | grep -i password", "ltrace ./binary", "strace -e trace=file ./binary"],
        "solution": "Code obfuscation, anti-debugging techniques, packing, control flow flattening, virtualization"
    },
    {
        "title": "Digital Forensics Analysis",
        "category": "forensics",
        "content": "Forensics methodology: Timeline analysis, file carving from unallocated space, metadata extraction, steganography detection, memory dump analysis, network packet forensics, and mobile device examination.",
        "tools": ["Autopsy", "Volatility", "Wireshark", "binwalk", "foremost", "exiftool", "steghide", "John the Ripper"],
        "payloads": ["volatility -f memory.dmp --profile=Win7SP1x64 pslist", "binwalk -e firmware.bin", "exiftool image.jpg", "steghide extract -sf image.jpg"],
        "solution": "Data encryption, secure deletion, access logging, incident response procedures, chain of custody"
    },
    {
        "title": "Open Source Intelligence (OSINT)",
        "category": "osint", 
        "content": "OSINT techniques: Social media reconnaissance, DNS/WHOIS analysis, Certificate transparency logs, Search engine dorking, Shodan/Censys scanning, Email harvesting, and metadata analysis.",
        "tools": ["theHarvester", "recon-ng", "Maltego", "Shodan", "Censys", "Google Dorks", "SpiderFoot"],
        "payloads": ["site:target.com filetype:pdf", "intitle:\"index of\" password", "theHarvester -d target.com -l 100 -b google"],
        "solution": "Information classification, data loss prevention, social media policies, employee training"
    }
]

def generate_pentestgpt_response(question):
    """Generate PentestGPT-style penetration testing response"""
    question_lower = question.lower()
    
    # Advanced pattern matching with multiple criteria
    best_match = None
    best_score = 0
    
    for item in PENTEST_KNOWLEDGE:
        score = 0
        
        # Multi-factor scoring
        title_words = item['title'].lower().split()
        content_words = item['content'].lower().split()[:30]
        tool_words = [tool.lower() for tool in item.get('tools', [])]
        
        all_keywords = title_words + [item['category']] + content_words + tool_words
        
        # Calculate relevance with weighted scoring
        for keyword in all_keywords:
            if keyword in question_lower:
                if keyword in title_words:
                    score += 5  # Title match highest priority
                elif keyword == item['category']:
                    score += 4  # Category match high priority
                elif keyword in tool_words:
                    score += 3  # Tool match medium priority
                else:
                    score += 1  # Content match basic priority
        
        if score > best_score:
            best_score = score
            best_match = item
    
    if best_match and best_score >= 3:
        # Generate comprehensive PentestGPT-style response
        tools_section = "\n**RECOMMENDED TOOLS:**\n" + "\n".join([f"• {tool}" for tool in best_match.get('tools', [])])
        
        payloads_section = ""
        if best_match.get('payloads'):
            payloads_section = "\n\n**EXAMPLE PAYLOADS/COMMANDS:**\n```\n" + "\n".join(best_match['payloads']) + "\n```"
        
        defense_section = f"\n\n**DEFENSIVE COUNTERMEASURES:**\n{best_match['solution']}"
        
        answer = f"## {best_match['title']} [{best_match['category'].upper()}]\n\n**VULNERABILITY ANALYSIS:**\n{best_match['content']}{tools_section}{payloads_section}{defense_section}\n\n**NEXT STEPS:** Need specific target details? Provide more context about your environment, constraints, or specific objectives."
        
        return {
            "answer": answer,
            "confidence": min(0.95, 0.7 + (best_score * 0.05)),
            "category": best_match['category'],
            "source": f"PentestGPT-{best_match['title']}"
        }
    
    # Intelligent categorization with pentest methodology
    if any(word in question_lower for word in ['web', 'http', 'api', 'cookie', 'session', 'xss', 'sql', 'injection', 'owasp']):
        category = "web"
        answer = """## WEB APPLICATION SECURITY ASSESSMENT

**RECONNAISSANCE PHASE:**
• Spider/crawl application (Burp Suite, OWASP ZAP)
• Technology fingerprinting (Wappalyzer, whatweb)
• Directory/file enumeration (dirb, gobuster, ffuf)

**VULNERABILITY SCANNING:**
• Automated scanning (Nikto, Nuclei templates)
• Manual testing for OWASP Top 10
• Parameter fuzzing and input validation testing

**EXPLOITATION TECHNIQUES:**
• SQL injection (sqlmap, manual testing)
• Cross-site scripting (BeEF, custom payloads)
• Authentication bypass attempts
• Business logic flaws identification"""

    elif any(word in question_lower for word in ['binary', 'exploit', 'buffer', 'overflow', 'pwn', 'rop', 'shellcode', 'assembly']):
        category = "pwn"
        answer = """## BINARY EXPLOITATION METHODOLOGY

**STATIC ANALYSIS:**
• File analysis (file, checksec, strings, objdump)
• Disassembly (Ghidra, radare2, IDA Pro)
• Vulnerability identification (buffer overflows, format strings)

**DYNAMIC ANALYSIS:**
• Debugging (gdb + GEF/pwndbg)
• Crash reproduction and analysis
• Memory layout examination

**EXPLOIT DEVELOPMENT:**
• Offset calculation (pattern_create, pattern_offset)
• ROP chain construction (ROPgadget, ropper)
• Shellcode development (msfvenom, custom assembly)
• Bypass techniques (ASLR, stack canaries, DEP)"""

    elif any(word in question_lower for word in ['crypto', 'cipher', 'rsa', 'hash', 'encryption', 'decrypt', 'key']):
        category = "crypto"
        answer = """## CRYPTOGRAPHIC ANALYSIS APPROACH

**CIPHER IDENTIFICATION:**
• Algorithm detection (cipher-identifier, CyberChef)
• Key/IV analysis and entropy testing
• Implementation weakness assessment

**ATTACK METHODOLOGIES:**
• Classical cipher attacks (frequency analysis, Kasiski examination)
• Modern crypto attacks (padding oracles, timing attacks)
• RSA-specific attacks (factorization, small exponents, Wiener's attack)

**TOOLS & TECHNIQUES:**
• SageMath for mathematical analysis
• RsaCtfTool for automated RSA attacks
• John the Ripper/hashcat for hash cracking
• Custom scripts for protocol analysis"""

    elif any(word in question_lower for word in ['network', 'scan', 'port', 'service', 'nmap', 'enumeration']):
        category = "network"
        answer = """## NETWORK PENETRATION TESTING

**RECONNAISSANCE:**
• Network discovery (nmap, masscan)
• Service enumeration (nmap scripts, manual banners)
• OS fingerprinting and version detection

**VULNERABILITY ASSESSMENT:**
• Automated scanning (Nessus, OpenVAS, Nuclei)
• Manual service testing
• Protocol-specific attacks (SMB, SNMP, DNS)

**EXPLOITATION:**
• Service exploitation (Metasploit, custom exploits)
• Credential attacks (hydra, medusa, patator)
• Post-exploitation (lateral movement, privilege escalation)"""

    elif any(word in question_lower for word in ['forensics', 'file', 'image', 'metadata', 'steganography', 'memory', 'dump']):
        category = "forensics"
        answer = """## DIGITAL FORENSICS INVESTIGATION

**EVIDENCE ACQUISITION:**
• Disk imaging (dd, FTK Imager, Cellebrite)
• Memory capture (DumpIt, Magnet RAM Capture)
• Network traffic capture (Wireshark, tcpdump)

**ANALYSIS METHODOLOGY:**
• Timeline reconstruction (Plaso, Autopsy)
• File system analysis (Sleuth Kit, PhotoRec)
• Memory forensics (Volatility Framework)
• Steganography detection (stegsolve, zsteg, binwalk)

**ARTIFACT RECOVERY:**
• Deleted file carving (foremost, scalpel)
• Metadata extraction (ExifTool, FOCA)
• Registry/log analysis
• Mobile device forensics (MSAB, Oxygen)"""

    else:
        category = "general"
        answer = """## PENETRATION TESTING METHODOLOGY

**INFORMATION GATHERING:**
• OSINT reconnaissance (Google dorking, social media, DNS)
• Network discovery and enumeration
• Technology stack identification

**VULNERABILITY ASSESSMENT:**
• Automated and manual vulnerability scanning
• Configuration review and security assessment
• Threat modeling and attack surface analysis

**EXPLOITATION & POST-EXPLOITATION:**
• Proof-of-concept development
• Privilege escalation techniques
• Persistence and lateral movement
• Evidence collection and documentation

**REPORTING:**
• Executive summary with business impact
• Technical findings with remediation steps
• Risk assessment and prioritization

Provide more specific details about your target environment, objectives, or constraints for tailored guidance."""
    
    return {
        "answer": answer,
        "confidence": random.uniform(0.75, 0.90),
        "category": category,
        "source": "PentestGPT-Methodology"
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Get request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            question = data.get('question', '').strip()
            if not question:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Please provide a question"}).encode())
                return
            
            # Simulate AI processing time
            time.sleep(random.uniform(0.3, 0.8))
            
            # Generate response
            response_data = generate_pentestgpt_response(question)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            full_response = {
                "question": question,
                "answer": response_data["answer"],
                "confidence": response_data["confidence"],
                "category": response_data["category"],
                "timestamp": datetime.now().isoformat(),
                "model": "PentestGPT-Enhanced"
            }
            
            self.wfile.write(json.dumps(full_response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": f"Processing failed: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()