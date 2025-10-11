"""
Mock SSRF Vulnerable App
Intentionally vulnerable for Wargaming validation - DO NOT USE IN PRODUCTION
"""
from fastapi import FastAPI, Query
import httpx

app = FastAPI(title="Mock SSRF App")

# Fake internal services
INTERNAL_SERVICES = {
    "http://internal-api:8080/admin": {"secret": "admin_token_123", "users": ["admin", "root"]},
    "http://metadata-service/latest/meta-data": {"instance_id": "i-1234567890", "public_ip": "1.2.3.4"},
    "http://localhost:6379/info": "# Redis Server Info\nredis_version:6.2.0",
}

@app.get("/")
def root():
    return {"app": "ssrf_vulnerable", "status": "vulnerable"}

@app.get("/api/fetch")
async def fetch_url(url: str = Query("https://example.com")):
    """INTENTIONALLY VULNERABLE - No URL validation"""
    try:
        # VULNERABILITY: Allows fetching ANY URL, including internal services
        
        # Simulate internal service access
        if url in INTERNAL_SERVICES:
            return {
                "success": True,
                "url": url,
                "content": INTERNAL_SERVICES[url],
                "message": "⚠️ SSRF successful - accessed internal service!",
                "is_internal": True
            }
        
        # Actually fetch external URL
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "content": response.text[:500],  # First 500 chars
                "headers": dict(response.headers),
                "is_internal": False
            }
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/webhook")
async def trigger_webhook(callback_url: str = Query("")):
    """INTENTIONALLY VULNERABLE - Webhook with no validation"""
    try:
        # VULNERABILITY: Triggers callback to ANY URL
        if callback_url in INTERNAL_SERVICES:
            return {
                "success": True,
                "callback_url": callback_url,
                "response": INTERNAL_SERVICES[callback_url],
                "message": "⚠️ SSRF via webhook - internal service accessed!"
            }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(callback_url, json={"event": "test"})
            
            return {
                "success": True,
                "callback_url": callback_url,
                "status_code": response.status_code,
                "response": response.text[:200]
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9085)
