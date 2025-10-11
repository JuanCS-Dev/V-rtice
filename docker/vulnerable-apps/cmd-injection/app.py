"""
Vulnerable Flask API - Command Injection
Purpose: Test target for MAXIMUS Adaptive Immunity Wargaming
CVE Simulated: CVE-2022-TEST-CMD
Status: INTENTIONALLY VULNERABLE - FOR TESTING ONLY
"""

from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "cmd-injection-test"}), 200

@app.route('/api/ping', methods=['POST'])
def ping():
    """
    VULNERABLE ENDPOINT: Command Injection
    
    Accepts 'host' parameter and executes ping without sanitization.
    
    CVE: CVE-2022-TEST-CMD
    CWE: CWE-78 (OS Command Injection)
    """
    data = request.get_json()
    host = data.get('host', 'localhost')
    
    # VULNERABILITY: No input sanitization
    try:
        # Directly concatenating user input into shell command
        result = subprocess.check_output(
            f"ping -c 1 {host}",
            shell=True,  # VULNERABLE: shell=True with user input
            stderr=subprocess.STDOUT,
            timeout=5
        )
        
        return jsonify({
            "status": "success",
            "output": result.decode('utf-8')
        }), 200
        
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "Timeout"}), 408
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "output": e.output.decode('utf-8')
        }), 500

@app.route('/api/logs', methods=['GET'])
def logs():
    """
    VULNERABLE ENDPOINT: Command Injection via query params
    
    CVE: CVE-2022-TEST-CMD-2
    """
    file_type = request.args.get('type', 'access')
    
    # VULNERABILITY: Unsanitized query parameter
    try:
        result = subprocess.check_output(
            f"ls -la /var/log/{file_type}.log",
            shell=True,
            stderr=subprocess.STDOUT
        )
        
        return jsonify({
            "status": "success",
            "output": result.decode('utf-8')
        }), 200
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "output": e.output.decode('utf-8')
        }), 500

@app.route('/api/info', methods=['GET'])
def info():
    """Info about this vulnerable service."""
    return jsonify({
        "service": "cmd-injection-test",
        "vulnerabilities": [
            {
                "cve": "CVE-2022-TEST-CMD",
                "type": "Command Injection",
                "cwe": "CWE-78",
                "endpoint": "/api/ping",
                "severity": "CRITICAL",
                "cvss": 9.8,
                "exploit": "POST /api/ping with host=127.0.0.1; whoami"
            },
            {
                "cve": "CVE-2022-TEST-CMD-2",
                "type": "Command Injection",
                "cwe": "CWE-78",
                "endpoint": "/api/logs",
                "severity": "HIGH",
                "cvss": 8.6,
                "exploit": "GET /api/logs?type=../../../etc/passwd%23"
            }
        ],
        "warning": "INTENTIONALLY VULNERABLE - FOR TESTING ONLY"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
