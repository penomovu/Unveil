"""
Add sample CTF writeup data for testing the client-side AI
"""

import json
import requests
import logging

logger = logging.getLogger(__name__)

def add_sample_data():
    """Add sample CTF writeups to test the AI functionality"""
    
    sample_writeups = [
        {
            'title': 'SQL Injection in Login Form',
            'content': '''This web challenge featured a classic SQL injection vulnerability in the login form. 

The application used PHP with MySQL and didn't properly sanitize user input. By analyzing the source code, I found the vulnerable query:

```sql
SELECT * FROM users WHERE username='$username' AND password='$password'
```

I tested various payloads and found that the following worked:
- Username: admin' OR '1'='1'-- 
- Password: anything

This bypassed the authentication because the injected SQL made the WHERE clause always true for the admin user. The query became:

```sql
SELECT * FROM users WHERE username='admin' OR '1'='1'-- ' AND password='anything'
```

The flag was displayed after successful login: flag{sql_injection_basic_bypass}

Key lessons:
- Always use prepared statements
- Never trust user input
- Implement proper input validation
- Use web application firewalls''',
            'category': 'web',
            'difficulty': 'easy',
            'source': 'sample_data'
        },
        {
            'title': 'XSS Reflected in Search Parameter',
            'content': '''Found a reflected XSS vulnerability in the search functionality of a web application.

The vulnerable endpoint was: /search?q=<user_input>

The application directly reflected the search term in the response without encoding:
```html
<p>Search results for: PAYLOAD_HERE</p>
```

I tested several XSS payloads:
1. <script>alert('XSS')</script> - Blocked by basic filtering
2. <img src=x onerror=alert('XSS')> - Worked!
3. javascript:alert('XSS') - Also worked in href attributes

The successful payload was:
```html
<img src=x onerror=alert(document.cookie)>
```

This executed JavaScript and displayed the session cookies. In a real attack, this could steal user sessions.

Flag: flag{xss_reflected_cookie_theft}

Prevention:
- Always HTML encode output
- Use Content Security Policy (CSP)
- Implement input validation
- Use HTTPOnly cookies''',
            'category': 'web',
            'difficulty': 'medium',
            'source': 'sample_data'
        },
        {
            'title': 'Buffer Overflow in C Program',
            'content': '''This pwn challenge involved a classic stack buffer overflow in a C program.

First, I analyzed the binary:
```bash
file challenge
checksec challenge
```

The binary had no stack canaries and no ASLR, making exploitation easier.

Vulnerable code:
```c
char buffer[64];
gets(buffer);  // Vulnerable function
```

The `gets()` function doesn't check buffer length, allowing overflow.

Exploitation steps:
1. Found offset: 72 bytes to overwrite EIP
2. Located system() function and "/bin/sh" string
3. Crafted ROP chain for ret2libc attack

Final payload:
```python
payload = b'A' * 72          # Buffer + saved EBP
payload += p32(system_addr)  # Return address
payload += b'JUNK'           # Return address for system
payload += p32(binsh_addr)   # Argument to system
```

This spawned a shell and allowed reading the flag file.

Flag: flag{buffer_overflow_ret2libc}

Tools used:
- GDB for debugging
- pwntools for exploitation
- ROPgadget for finding gadgets''',
            'category': 'pwn',
            'difficulty': 'hard',
            'source': 'sample_data'
        },
        {
            'title': 'Caesar Cipher with ROT13',
            'content': '''This crypto challenge presented an encoded message that needed decryption.

Given ciphertext: "synt{pnrfne_pvcure_vf_rnfl}"

I recognized this might be a Caesar cipher due to:
- Preserved word structure
- Common letter patterns
- Format suggesting a flag

I tried all possible shifts (1-25) and found that ROT13 (shift of 13) produced readable text:

Original: synt{pnrfne_pvcure_vf_rnfl}
ROT13:    flag{caesar_cipher_is_easy}

ROT13 is a special case of Caesar cipher where each letter is shifted 13 positions. It's its own inverse - applying ROT13 twice returns the original text.

Python solution:
```python
import codecs
cipher = "synt{pnrfne_pvcure_vf_rnfl}"
flag = codecs.encode(cipher, 'rot_13')
print(flag)  # flag{caesar_cipher_is_easy}
```

This challenge taught the importance of:
- Trying simple ciphers first
- Recognizing patterns in encoded text
- Using automated tools for quick testing''',
            'category': 'crypto',
            'difficulty': 'easy',
            'source': 'sample_data'
        },
        {
            'title': 'RSA with Small Exponent Attack',
            'content': '''This cryptography challenge involved breaking RSA encryption with a small public exponent.

Given:
- n = 133337 (very small for demonstration)
- e = 3 (small exponent)
- c = 8027 (ciphertext)

When the public exponent e is small and the message m is also small, we can sometimes decrypt without the private key.

The attack works when m^e < n, meaning no modular reduction occurred during encryption.

I used the cube root attack:
1. Calculate the eth root of the ciphertext
2. Since e=3, calculate cube root of c
3. If m^3 < n, then c = m^3 (no mod n)

Python solution:
```python
import gmpy2

n = 133337
e = 3
c = 8027

# Calculate cube root
m = gmpy2.iroot(c, e)[0]
print(f"Message: {m}")

# Convert to ASCII if needed
flag = bytes.fromhex(hex(m)[2:]).decode()
print(f"Flag: {flag}")
```

The cube root of 8027 is 20, which converts to ASCII as "flag".

This demonstrates why:
- Use proper padding (OAEP)
- Use larger exponents (65537 is standard)
- Ensure message size relative to modulus''',
            'category': 'crypto',
            'difficulty': 'medium',
            'source': 'sample_data'
        },
        {
            'title': 'ELF Binary Reverse Engineering',
            'content': '''This reverse engineering challenge required analyzing a Linux ELF binary to extract the flag.

Initial analysis:
```bash
file challenge
strings challenge | grep flag
hexdump -C challenge | grep -i flag
```

The `strings` command revealed some interesting text but no clear flag. I used Ghidra for deeper analysis.

In Ghidra, I found the main function contained several checks:
1. Command line argument validation
2. String transformation operations  
3. XOR operations with hardcoded keys

Key function pseudo-code:
```c
void main(int argc, char *argv[]) {
    if (argc != 2) return;
    
    char *input = argv[1];
    if (strlen(input) != 24) return;
    
    // XOR each character with position-based key
    for (int i = 0; i < 24; i++) {
        input[i] ^= (0x42 + i);
    }
    
    if (strcmp(input, "expected_result") == 0) {
        printf("Correct! Flag: flag{%s}\n", decoded_flag);
    }
}
```

I reversed the XOR operation to find the correct input:
```python
expected = "expected_result"  # From Ghidra analysis
flag_chars = []

for i in range(24):
    original = ord(expected[i]) ^ (0x42 + i)
    flag_chars.append(chr(original))

print(''.join(flag_chars))
```

Final flag: flag{reverse_engineering_success}

Tools used:
- Ghidra for static analysis
- GDB for dynamic analysis
- Python for crypto operations''',
            'category': 'reverse',
            'difficulty': 'medium',
            'source': 'sample_data'
        }
    ]
    
    # Send data to the server
    base_url = 'http://localhost:5000'
    
    for writeup in sample_writeups:
        try:
            # Create a temporary file to upload
            filename = f"{writeup['title'].lower().replace(' ', '_')}.txt"
            content = f"Title: {writeup['title']}\nCategory: {writeup['category']}\nDifficulty: {writeup['difficulty']}\n\n{writeup['content']}"
            
            # Simulate file upload
            files = {'file': (filename, content, 'text/plain')}
            response = requests.post(f"{base_url}/api/upload", files=files)
            
            if response.status_code == 200:
                logger.info(f"Added sample writeup: {writeup['title']}")
            else:
                logger.error(f"Failed to add {writeup['title']}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error adding sample data: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    add_sample_data()