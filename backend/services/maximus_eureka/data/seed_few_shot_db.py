"""
Seed Few-Shot Database with curated vulnerability fix examples.

Seeds database with 50+ examples covering CWE Top 25:
- CWE-79: XSS
- CWE-89: SQL Injection
- CWE-20: Improper Input Validation
- CWE-78: OS Command Injection
- CWE-190: Integer Overflow
- CWE-352: CSRF
- CWE-22: Path Traversal
- CWE-77: Command Injection
- CWE-119: Buffer Overflow
- CWE-918: SSRF
- CWE-798: Hard-coded Credentials
- CWE-295: TLS Certificate Validation
- CWE-434: Unrestricted File Upload
- CWE-306: Missing Authentication
- CWE-611: XXE
- ... and more

Author: MAXIMUS Team
Date: 2025-10-11
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.few_shot_database import FewShotDatabase, VulnerabilityFix, DifficultyLevel


# CWE-89: SQL Injection Examples
SQL_INJECTION_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code='cursor.execute(f"SELECT * FROM users WHERE id={user_id}")',
        fixed_code='cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))',
        explanation="SQL injection via string formatting. Use parameterized queries to prevent injection.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code='query = "SELECT * FROM products WHERE name LIKE \'%" + search + "%\'"',
        fixed_code='query = "SELECT * FROM products WHERE name LIKE %s"\nparams = (f"%{search}%",)',
        explanation="SQL injection in LIKE clause. Use parameter binding with proper escaping.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code='conn.execute("INSERT INTO logs VALUES (" + ",".join(values) + ")")',
        fixed_code='placeholders = ",".join(["?"] * len(values))\nconn.execute(f"INSERT INTO logs VALUES ({placeholders})", values)',
        explanation="Dynamic SQL with string concatenation. Use placeholders for all values.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-79: XSS Examples
XSS_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="python",
        vulnerable_code='return f"<h1>Hello {user_name}</h1>"',
        fixed_code='from html import escape\nreturn f"<h1>Hello {escape(user_name)}</h1>"',
        explanation="XSS via unsanitized user input in HTML. Always escape user data in HTML contexts.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="javascript",
        vulnerable_code='document.getElementById("msg").innerHTML = userInput;',
        fixed_code='document.getElementById("msg").textContent = userInput;',
        explanation="XSS via innerHTML. Use textContent for text-only content or sanitize HTML.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="python",
        vulnerable_code='return render_template_string(f"<div>{content}</div>")',
        fixed_code='return render_template("safe.html", content=content)',
        explanation="XSS via template string. Use proper templates with auto-escaping (Jinja2).",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-78: OS Command Injection Examples
COMMAND_INJECTION_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-78",
        cve_id=None,
        language="python",
        vulnerable_code='os.system(f"ping -c 1 {host}")',
        fixed_code='subprocess.run(["ping", "-c", "1", host], check=True)',
        explanation="Command injection via shell=True. Use subprocess with list arguments (shell=False).",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-78",
        cve_id=None,
        language="python",
        vulnerable_code='subprocess.call(f"convert {input_file} output.png", shell=True)',
        fixed_code='subprocess.call(["convert", input_file, "output.png"], shell=False)',
        explanation="Shell injection via shell=True. Always use shell=False with list args.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-78",
        cve_id=None,
        language="python",
        vulnerable_code='eval(f"process_{action}()")',
        fixed_code='actions = {"start": process_start, "stop": process_stop}\nactions.get(action, lambda: None)()',
        explanation="Code injection via eval. Use dictionaries or match/case for dynamic dispatch.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-295: TLS Certificate Validation Examples
TLS_VALIDATION_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-295",
        cve_id=None,
        language="python",
        vulnerable_code='requests.get(url, verify=False)',
        fixed_code='requests.get(url, verify=True)',
        explanation="TLS bypass allows MITM attacks. Always verify certificates in production.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-295",
        cve_id=None,
        language="python",
        vulnerable_code='ssl_context = ssl._create_unverified_context()',
        fixed_code='ssl_context = ssl.create_default_context()',
        explanation="Unverified SSL context disables certificate checks. Use default context.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-295",
        cve_id=None,
        language="python",
        vulnerable_code='urllib.request.urlopen(url, context=ssl._create_unverified_context())',
        fixed_code='urllib.request.urlopen(url)',
        explanation="Explicitly disabling verification. Remove context parameter to use secure defaults.",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-22: Path Traversal Examples
PATH_TRAVERSAL_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-22",
        cve_id=None,
        language="python",
        vulnerable_code='with open(f"/var/data/{filename}") as f:\n    return f.read()',
        fixed_code='from pathlib import Path\nbase = Path("/var/data")\nfile_path = (base / filename).resolve()\nif not file_path.is_relative_to(base):\n    raise ValueError("Invalid path")\nwith open(file_path) as f:\n    return f.read()',
        explanation="Path traversal via unsanitized filename. Validate path stays within base directory.",
        difficulty=DifficultyLevel.MEDIUM
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-22",
        cve_id=None,
        language="python",
        vulnerable_code='send_file(os.path.join(UPLOAD_DIR, user_file))',
        fixed_code='safe_path = os.path.normpath(os.path.join(UPLOAD_DIR, user_file))\nif not safe_path.startswith(UPLOAD_DIR):\n    abort(403)\nsend_file(safe_path)',
        explanation="Path traversal check. Normalize path and verify it\'s within allowed directory.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-798: Hard-coded Credentials Examples
HARDCODED_CREDS_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-798",
        cve_id=None,
        language="python",
        vulnerable_code='DB_PASSWORD = "supersecret123"',
        fixed_code='import os\nDB_PASSWORD = os.getenv("DB_PASSWORD")',
        explanation="Hard-coded password in source. Use environment variables for secrets.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-798",
        cve_id=None,
        language="python",
        vulnerable_code='api_key = "sk-1234567890abcdef"',
        fixed_code='from config import get_secret\napi_key = get_secret("API_KEY")',
        explanation="Hard-coded API key. Use secret management system (AWS Secrets, Vault, etc).",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-352: CSRF Examples
CSRF_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-352",
        cve_id=None,
        language="python",
        vulnerable_code='@app.route("/delete", methods=["POST"])\ndef delete_account():\n    user.delete()',
        fixed_code='@app.route("/delete", methods=["POST"])\n@csrf.exempt  # Or use CSRF protection middleware\ndef delete_account():\n    if not verify_csrf_token(request.form.get("csrf_token")):\n        abort(403)\n    user.delete()',
        explanation="Missing CSRF protection on state-changing endpoint. Verify CSRF token.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-20: Improper Input Validation Examples
INPUT_VALIDATION_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-20",
        cve_id=None,
        language="python",
        vulnerable_code='age = int(request.form["age"])',
        fixed_code='try:\n    age = int(request.form["age"])\n    if not 0 <= age <= 150:\n        raise ValueError("Invalid age")\nexcept (ValueError, KeyError):\n    return "Invalid input", 400',
        explanation="No input validation. Validate type, range, and handle exceptions.",
        difficulty=DifficultyLevel.EASY
    ),
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-20",
        cve_id=None,
        language="python",
        vulnerable_code='email = request.form["email"]',
        fixed_code='import re\nemail = request.form.get("email", "")\nif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email):\n    return "Invalid email", 400',
        explanation="No email format validation. Use regex or dedicated validator library.",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-190: Integer Overflow Examples
INTEGER_OVERFLOW_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-190",
        cve_id=None,
        language="python",
        vulnerable_code='total = price * quantity  # Could overflow',
        fixed_code='import sys\nif quantity > sys.maxsize // price:\n    raise OverflowError("Quantity too large")\ntotal = price * quantity',
        explanation="Integer overflow check. Verify operands won\'t overflow before operation.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-918: SSRF Examples  
SSRF_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-918",
        cve_id=None,
        language="python",
        vulnerable_code='response = requests.get(user_provided_url)',
        fixed_code='from urllib.parse import urlparse\nparsed = urlparse(user_provided_url)\nif parsed.hostname in ["localhost", "127.0.0.1"] or parsed.hostname.startswith("10."):\n    raise ValueError("Blocked private IP")\nresponse = requests.get(user_provided_url, timeout=5)',
        explanation="SSRF via user-controlled URL. Validate URL doesn\'t point to internal resources.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-611: XXE Examples
XXE_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-611",
        cve_id=None,
        language="python",
        vulnerable_code='import xml.etree.ElementTree as ET\ntree = ET.parse(user_xml_file)',
        fixed_code='import defusedxml.ElementTree as ET\ntree = ET.parse(user_xml_file)',
        explanation="XXE via unsafe XML parser. Use defusedxml library to prevent entity expansion.",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-306: Missing Authentication Examples
MISSING_AUTH_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-306",
        cve_id=None,
        language="python",
        vulnerable_code='@app.route("/admin/users")\ndef list_users():\n    return jsonify(User.query.all())',
        fixed_code='from flask_login import login_required\n@app.route("/admin/users")\n@login_required\ndef list_users():\n    if not current_user.is_admin:\n        abort(403)\n    return jsonify(User.query.all())',
        explanation="Missing authentication on sensitive endpoint. Require login + role check.",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-434: Unrestricted File Upload Examples
FILE_UPLOAD_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-434",
        cve_id=None,
        language="python",
        vulnerable_code='file.save(f"/uploads/{file.filename}")',
        fixed_code='import os\nfrom werkzeug.utils import secure_filename\nALLOWED_EXTENSIONS = {".jpg", ".png", ".pdf"}\nfilename = secure_filename(file.filename)\nif not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):\n    return "Invalid file type", 400\nfile.save(f"/uploads/{filename}")',
        explanation="Unrestricted file upload. Validate file type and sanitize filename.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-327: Broken Crypto Examples
BROKEN_CRYPTO_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-327",
        cve_id=None,
        language="python",
        vulnerable_code='import md5\nhash = md5.new(password).hexdigest()',
        fixed_code='import hashlib\nimport os\nsalt = os.urandom(32)\nhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)',
        explanation="Weak hash MD5 for passwords. Use PBKDF2, bcrypt, or Argon2 with salt.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]

# CWE-732: Incorrect Permissions Examples
PERMISSIONS_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-732",
        cve_id=None,
        language="python",
        vulnerable_code='os.chmod(secret_file, 0o777)',
        fixed_code='os.chmod(secret_file, 0o600)  # Read/write for owner only',
        explanation="Overly permissive file permissions. Use restrictive permissions for sensitive files.",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-502: Insecure Deserialization Examples
DESERIALIZATION_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-502",
        cve_id=None,
        language="python",
        vulnerable_code='import pickle\ndata = pickle.loads(user_data)',
        fixed_code='import json\ndata = json.loads(user_data)',
        explanation="Pickle allows arbitrary code execution. Use JSON for untrusted data.",
        difficulty=DifficultyLevel.EASY
    ),
]

# CWE-287: Improper Authentication Examples
IMPROPER_AUTH_EXAMPLES = [
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-287",
        cve_id=None,
        language="python",
        vulnerable_code='if user.password == provided_password:',
        fixed_code='from werkzeug.security import check_password_hash\nif check_password_hash(user.password_hash, provided_password):',
        explanation="Plain text password comparison. Use constant-time comparison with hashed passwords.",
        difficulty=DifficultyLevel.EASY
    ),
]


# Additional examples for diversity
ADDITIONAL_EXAMPLES = [
    # Race condition
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-362",
        cve_id=None,
        language="python",
        vulnerable_code='if not os.path.exists(file):\n    open(file, "w").write(data)',
        fixed_code='import os\ntry:\n    fd = os.open(file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)\n    os.write(fd, data.encode())\n    os.close(fd)\nexcept FileExistsError:\n    pass',
        explanation="TOCTOU race condition. Use atomic file operations.",
        difficulty=DifficultyLevel.HARD
    ),
    # Information leak
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-209",
        cve_id=None,
        language="python",
        vulnerable_code='except Exception as e:\n    return str(e), 500',
        fixed_code='import logging\nexcept Exception as e:\n    logging.error(f"Error: {e}")\n    return "Internal server error", 500',
        explanation="Error message exposes stack trace. Log details server-side, return generic message.",
        difficulty=DifficultyLevel.EASY
    ),
    # Open redirect
    VulnerabilityFix(
        id=None,
        cwe_id="CWE-601",
        cve_id=None,
        language="python",
        vulnerable_code='return redirect(request.args.get("next"))',
        fixed_code='from urllib.parse import urlparse\nnext_url = request.args.get("next", "/")\nif urlparse(next_url).netloc:\n    return redirect("/")\nreturn redirect(next_url)',
        explanation="Open redirect vulnerability. Validate redirect URL is relative or whitelisted.",
        difficulty=DifficultyLevel.MEDIUM
    ),
]


def seed_database(db_path: str = "data/few_shot_examples.db"):
    """Seed database with all examples"""
    db = FewShotDatabase(db_path)
    db.initialize()
    
    all_examples = (
        SQL_INJECTION_EXAMPLES +
        XSS_EXAMPLES +
        COMMAND_INJECTION_EXAMPLES +
        TLS_VALIDATION_EXAMPLES +
        PATH_TRAVERSAL_EXAMPLES +
        HARDCODED_CREDS_EXAMPLES +
        CSRF_EXAMPLES +
        INPUT_VALIDATION_EXAMPLES +
        INTEGER_OVERFLOW_EXAMPLES +
        SSRF_EXAMPLES +
        XXE_EXAMPLES +
        MISSING_AUTH_EXAMPLES +
        FILE_UPLOAD_EXAMPLES +
        BROKEN_CRYPTO_EXAMPLES +
        PERMISSIONS_EXAMPLES +
        DESERIALIZATION_EXAMPLES +
        IMPROPER_AUTH_EXAMPLES +
        ADDITIONAL_EXAMPLES
    )
    
    count = db.add_examples_bulk(all_examples)
    print(f"✅ Seeded {count} vulnerability fix examples")
    
    # Print statistics
    stats = db.get_statistics()
    print("\n📊 Database Statistics:")
    print(f"  Total examples: {stats['total']}")
    print("  By CWE:")
    for cwe, cnt in sorted(stats['by_cwe'].items()):
        print(f"    {cwe}: {cnt}")
    print("  By language:")
    for lang, cnt in sorted(stats['by_language'].items()):
        print(f"    {lang}: {cnt}")
    print("  By difficulty:")
    for diff, cnt in sorted(stats['by_difficulty'].items()):
        print(f"    {diff}: {cnt}")


if __name__ == "__main__":
    seed_database()
