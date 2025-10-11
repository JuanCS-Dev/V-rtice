"""
Mock Path Traversal Vulnerable App
Intentionally vulnerable for Wargaming validation - DO NOT USE IN PRODUCTION
"""
from fastapi import FastAPI, Query
from pathlib import Path
import os

app = FastAPI(title="Mock Path Traversal App")

# Create fake file system
FAKE_FILES = {
    "public/index.html": "<h1>Welcome</h1>",
    "public/about.html": "<h1>About Us</h1>",
    "private/secrets.txt": "SECRET_API_KEY=super_secret_123",
    "private/passwords.txt": "admin:password123\nuser:pass456",
}

@app.get("/")
def root():
    return {"app": "path_traversal_vulnerable", "status": "vulnerable"}

@app.get("/api/file")
def read_file(path: str = Query("public/index.html")):
    """INTENTIONALLY VULNERABLE - No path sanitization"""
    try:
        # VULNERABILITY: No validation, allows ../../../
        file_content = FAKE_FILES.get(path)
        
        if file_content:
            return {
                "success": True,
                "path": path,
                "content": file_content,
                "message": "File read successfully"
            }
        else:
            # Try path traversal simulation
            normalized = path.replace("../", "").replace("..\\", "")
            if normalized in FAKE_FILES:
                return {
                    "success": True,
                    "path": path,
                    "normalized_path": normalized,
                    "content": FAKE_FILES[normalized],
                    "message": "Path traversal successful!"
                }
            
            return {
                "success": False,
                "path": path,
                "error": "File not found"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download")
def download_file(filename: str = Query("index.html")):
    """INTENTIONALLY VULNERABLE - Direct file access"""
    # VULNERABILITY: Allows access to any filename
    for file_path, content in FAKE_FILES.items():
        if filename in file_path:
            return {
                "success": True,
                "filename": filename,
                "full_path": file_path,
                "content": content
            }
    
    return {"success": False, "error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9084)
