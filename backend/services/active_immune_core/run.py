"""
Run script for Active Immune Core Service.
This file uses absolute imports to avoid relative import issues in Docker.
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8200, workers=4)
