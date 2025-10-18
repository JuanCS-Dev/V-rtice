"""Standalone OSINT API Server - Testing Mode.

Simple FastAPI server to test OSINT endpoints without full MAXIMUS initialization.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import OSINT router
from osint_router import router as osint_router

app = FastAPI(title="OSINT API Server - Testing", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register OSINT router
app.include_router(osint_router)
print("✅ OSINT API routes registered at /api/osint/*")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "operational", "service": "OSINT API Testing Server"}


if __name__ == "__main__":
    print("🚀 Starting OSINT API Testing Server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
