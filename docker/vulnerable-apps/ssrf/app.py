"""
Vulnerable Flask API - Server-Side Request Forgery (SSRF)
Purpose: Test target for MAXIMUS Adaptive Immunity Wargaming
CVE Simulated: CVE-2022-TEST-SSRF
Status: INTENTIONALLY VULNERABLE - FOR TESTING ONLY
"""

from flask import Flask, request, jsonify
import requests
import urllib.parse

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "ssrf-test"}), 200

@app.route('/api/fetch', methods=['POST'])
def fetch_url():
    """
    VULNERABLE ENDPOINT: SSRF
    
    Accepts 'url' parameter and fetches it without validation.
    
    CVE: CVE-2022-TEST-SSRF
    CWE: CWE-918 (Server-Side Request Forgery)
    """
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({"status": "error", "message": "URL parameter required"}), 400
    
    # VULNERABILITY: No URL validation or filtering
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        
        return jsonify({
            "status": "success",
            "url": url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:1000]  # First 1KB
        }), 200
        
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/proxy', methods=['GET'])
def proxy():
    """
    VULNERABLE ENDPOINT: SSRF via query params
    
    CVE: CVE-2022-TEST-SSRF-2
    """
    target = request.args.get('target', '')
    
    if not target:
        return jsonify({"status": "error", "message": "Target parameter required"}), 400
    
    # VULNERABILITY: Can access internal resources
    try:
        # Construct URL
        full_url = f"http://{target}"
        response = requests.get(full_url, timeout=5)
        
        return jsonify({
            "status": "success",
            "target": target,
            "response": response.text[:500]
        }), 200
        
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """
    VULNERABLE ENDPOINT: SSRF via webhook callback
    
    CVE: CVE-2022-TEST-SSRF-3
    """
    data = request.get_json()
    callback_url = data.get('callback_url', '')
    
    if not callback_url:
        return jsonify({"status": "error", "message": "callback_url required"}), 400
    
    # VULNERABILITY: Allows internal network access
    try:
        # Send notification to callback
        payload = {
            "event": "webhook_received",
            "timestamp": "2025-10-11T00:00:00Z",
            "data": data.get('payload', {})
        }
        
        response = requests.post(callback_url, json=payload, timeout=5)
        
        return jsonify({
            "status": "success",
            "callback_status": response.status_code,
            "message": "Webhook delivered"
        }), 200
        
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/metadata', methods=['GET'])
def metadata():
    """
    Info endpoint - documents SSRF attack vectors for testing
    """
    return jsonify({
        "service": "ssrf-test",
        "internal_endpoints": [
            "http://localhost:5000/health",
            "http://127.0.0.1:5000/api/metadata"
        ],
        "cloud_metadata_urls": [
            "http://169.254.169.254/latest/meta-data/",  # AWS
            "http://metadata.google.internal/",  # GCP
            "http://169.254.169.254/metadata/instance"  # Azure
        ]
    }), 200

@app.route('/api/info', methods=['GET'])
def info():
    """Info about this vulnerable service."""
    return jsonify({
        "service": "ssrf-test",
        "vulnerabilities": [
            {
                "cve": "CVE-2022-TEST-SSRF",
                "type": "Server-Side Request Forgery",
                "cwe": "CWE-918",
                "endpoint": "/api/fetch",
                "severity": "HIGH",
                "cvss": 8.6,
                "exploit": 'POST /api/fetch {"url": "http://localhost:5000/health"}'
            },
            {
                "cve": "CVE-2022-TEST-SSRF-2",
                "type": "Server-Side Request Forgery",
                "cwe": "CWE-918",
                "endpoint": "/api/proxy",
                "severity": "HIGH",
                "cvss": 8.6,
                "exploit": "GET /api/proxy?target=localhost:5000/health"
            },
            {
                "cve": "CVE-2022-TEST-SSRF-3",
                "type": "Server-Side Request Forgery",
                "cwe": "CWE-918",
                "endpoint": "/api/webhook",
                "severity": "HIGH",
                "cvss": 8.6,
                "exploit": 'POST /api/webhook {"callback_url": "http://169.254.169.254/latest/meta-data/"}'
            }
        ],
        "test_targets": [
            "http://localhost:5000/health",
            "http://127.0.0.1:5000/api/info",
            "http://169.254.169.254/latest/meta-data/"
        ],
        "warning": "INTENTIONALLY VULNERABLE - FOR TESTING ONLY"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
