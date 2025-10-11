"""
Mock Command Injection Vulnerable App
Intentionally vulnerable for Wargaming validation - DO NOT USE IN PRODUCTION
"""
from fastapi import FastAPI, Query
import subprocess
import os

app = FastAPI(title="Mock Command Injection App")

@app.get("/")
def root():
    return {"app": "command_injection_vulnerable", "status": "vulnerable"}

@app.get("/api/ping")
def ping(host: str = Query("localhost")):
    """INTENTIONALLY VULNERABLE - No command sanitization"""
    try:
        # VULNERABILITY: Direct command execution with user input
        command = f"ping -c 1 {host}"
        result = subprocess.run(
            command,
            shell=True,  # DANGEROUS!
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "success": True,
            "command": command,
            "output": result.stdout,
            "error": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/execute")
def execute(cmd: str = Query("echo 'test'")):
    """INTENTIONALLY VULNERABLE - Arbitrary command execution"""
    try:
        # VULNERABILITY: Execute ANY command
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "success": True,
            "command": cmd,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9083)
