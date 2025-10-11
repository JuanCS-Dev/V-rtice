"""
Vulnerable Flask API - Path Traversal
Purpose: Test target for MAXIMUS Adaptive Immunity Wargaming
CVE Simulated: CVE-2022-TEST-PATH
Status: INTENTIONALLY VULNERABLE - FOR TESTING ONLY
"""

from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

# Create some test files
TEST_FILES_DIR = "/app/public_files"
os.makedirs(TEST_FILES_DIR, exist_ok=True)

with open(f"{TEST_FILES_DIR}/welcome.txt", "w") as f:
    f.write("Welcome to the public files directory!")

with open(f"{TEST_FILES_DIR}/readme.txt", "w") as f:
    f.write("README: This is a test file")

# Create sensitive file (should NOT be accessible)
with open("/app/secrets.txt", "w") as f:
    f.write("SECRET_API_KEY=sk_live_12345\nDATABASE_PASSWORD=SuperSecret123")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "path-traversal-test"}), 200

@app.route('/api/file', methods=['GET'])
def get_file():
    """
    VULNERABLE ENDPOINT: Path Traversal
    
    Accepts 'filename' parameter without sanitization.
    
    CVE: CVE-2022-TEST-PATH
    CWE: CWE-22 (Path Traversal)
    """
    filename = request.args.get('filename', 'welcome.txt')
    
    # VULNERABILITY: No path sanitization
    try:
        filepath = os.path.join(TEST_FILES_DIR, filename)
        
        # This allows ../../../etc/passwd style attacks
        with open(filepath, 'r') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "content": content
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            "status": "error",
            "message": f"File not found: {filename}"
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/download', methods=['GET'])
def download_file():
    """
    VULNERABLE ENDPOINT: Path Traversal via download
    
    CVE: CVE-2022-TEST-PATH-2
    """
    filename = request.args.get('file', 'readme.txt')
    
    # VULNERABILITY: Direct path concatenation
    try:
        filepath = f"{TEST_FILES_DIR}/{filename}"
        return send_file(filepath, as_attachment=True)
        
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/list', methods=['GET'])
def list_files():
    """List available files in public directory."""
    files = os.listdir(TEST_FILES_DIR)
    return jsonify({
        "status": "success",
        "files": files,
        "directory": TEST_FILES_DIR
    }), 200

@app.route('/api/info', methods=['GET'])
def info():
    """Info about this vulnerable service."""
    return jsonify({
        "service": "path-traversal-test",
        "vulnerabilities": [
            {
                "cve": "CVE-2022-TEST-PATH",
                "type": "Path Traversal",
                "cwe": "CWE-22",
                "endpoint": "/api/file",
                "severity": "HIGH",
                "cvss": 7.5,
                "exploit": "GET /api/file?filename=../secrets.txt"
            },
            {
                "cve": "CVE-2022-TEST-PATH-2",
                "type": "Path Traversal",
                "cwe": "CWE-22",
                "endpoint": "/api/download",
                "severity": "HIGH",
                "cvss": 7.5,
                "exploit": "GET /api/download?file=../../secrets.txt"
            }
        ],
        "test_targets": [
            "/api/file?filename=../secrets.txt",
            "/api/file?filename=../../etc/passwd",
            "/api/download?file=../secrets.txt"
        ],
        "warning": "INTENTIONALLY VULNERABLE - FOR TESTING ONLY"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
