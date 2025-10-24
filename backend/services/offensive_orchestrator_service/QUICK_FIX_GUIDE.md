# Quick Fix Guide - Offensive Orchestrator Service

**Service Status:** BROKEN - Cannot Start
**Root Cause:** 3 Critical Import Errors
**Time to Fix:** 15-30 minutes

---

## The 3 Critical Errors

### ❌ ERROR 1: Missing `os` import in main.py (Line 99)
```
NameError: name 'os' is not defined
```

### ❌ ERROR 2: Missing `anthropic` import in orchestrator/core.py (Line 74)
```
NameError: name 'anthropic' is not defined
```

### ❌ ERROR 3: Relative import issues in memory/attack_memory.py (Line 27)
```
ImportError: attempted relative import beyond top-level package
```

---

## Quick Fix (15 minutes)

### Step 1: Fix main.py (1 minute)

**File:** `/home/juan/vertice-dev/backend/services/offensive_orchestrator_service/main.py`

**Location:** Add at line 12 (after `import logging`)

```python
# main.py - Line ~12
import logging
import os  # <-- ADD THIS LINE
from contextlib import asynccontextmanager
```

**Verification:**
```bash
python -c "import main" && echo "✓ main.py fixed" || echo "✗ Still broken"
```

---

### Step 2: Fix Orchestrator (Choose ONE option)

#### Option A: Switch to Working Orchestrator (RECOMMENDED - 5 minutes)

**Why:** The service has TWO orchestrator implementations:
- `orchestrator/core.py` - BROKEN (uses Anthropic, incomplete)
- `orchestrator.py` - WORKING (uses Gemini, complete)

**Action 1:** Update `orchestrator/__init__.py`

**File:** `/home/juan/vertice-dev/backend/services/offensive_orchestrator_service/orchestrator/__init__.py`

```python
# BEFORE:
"""Orchestrator module."""
from orchestrator.core import MaximusOrchestratorAgent

__all__ = ["MaximusOrchestratorAgent"]

# AFTER:
"""Orchestrator module."""
# Use the working Gemini-based orchestrator from parent directory
import sys
from pathlib import Path

# Add parent directory to path to import from orchestrator.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import MaximusOrchestratorAgent

__all__ = ["MaximusOrchestratorAgent"]
```

**Action 2:** Optionally rename broken file to mark as deprecated

```bash
cd /home/juan/vertice-dev/backend/services/offensive_orchestrator_service
mv orchestrator/core.py orchestrator/core.py.BROKEN
```

**Verification:**
```bash
python -c "from orchestrator import MaximusOrchestratorAgent; print('✓ Orchestrator fixed')"
```

---

#### Option B: Fix Broken Orchestrator (Alternative - 10 minutes)

**Only use this if you MUST use Anthropic Claude instead of Gemini**

**Action 1:** Add import to orchestrator/core.py

**File:** `/home/juan/vertice-dev/backend/services/offensive_orchestrator_service/orchestrator/core.py`

```python
# Line ~7 (add after other imports)
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import anthropic  # <-- ADD THIS LINE

logger = logging.getLogger(__name__)
```

**Action 2:** Add anthropic to requirements.txt

```bash
cd /home/juan/vertice-dev/backend/services/offensive_orchestrator_service
echo "anthropic==0.34.0" >> requirements.txt
pip install anthropic==0.34.0
```

**Verification:**
```bash
python -c "from orchestrator import MaximusOrchestratorAgent; print('✓ Orchestrator fixed')"
```

---

### Step 3: Fix Memory Module (10 minutes)

**File:** `/home/juan/vertice-dev/backend/services/offensive_orchestrator_service/memory/attack_memory.py`

**Change relative imports to absolute imports:**

```python
# BEFORE (Lines 27-31):
from ..models import CampaignPlan, CampaignObjective, CampaignDB, CampaignStatus
from .database import DatabaseManager
from .vector_store import VectorStore
from .embeddings import EmbeddingGenerator

# AFTER:
from models import CampaignPlan, CampaignObjective, CampaignDB, CampaignStatus
from memory.database import DatabaseManager
from memory.vector_store import VectorStore
from memory.embeddings import EmbeddingGenerator
```

**Apply same fix to other memory files:**

**File:** `memory/database.py`
```python
# BEFORE:
from ..config import DatabaseConfig, get_config
from ..models import Base, CampaignDB, HOTLDecisionDB, AttackMemoryDB, CampaignStatus

# AFTER:
from config import DatabaseConfig, get_config
from models import Base, CampaignDB, HOTLDecisionDB, AttackMemoryDB, CampaignStatus
```

**File:** `memory/embeddings.py`
```python
# BEFORE:
from ..config import LLMConfig, get_config
from ..models import CampaignPlan, CampaignObjective

# AFTER:
from config import LLMConfig, get_config
from models import CampaignPlan, CampaignObjective
```

**File:** `memory/vector_store.py`
```python
# BEFORE:
from ..config import VectorDBConfig, get_config

# AFTER:
from config import VectorDBConfig, get_config
```

**Verification:**
```bash
python -c "from memory import AttackMemorySystem; print('✓ Memory module fixed')"
```

---

## Complete Verification Checklist

After applying all fixes:

```bash
cd /home/juan/vertice-dev/backend/services/offensive_orchestrator_service

# 1. Test all imports resolve
echo "Testing imports..."
python -c "import os; print('✓ os')"
python -c "from orchestrator import MaximusOrchestratorAgent; print('✓ orchestrator')"
python -c "from memory import AttackMemorySystem; print('✓ memory')"
python -c "from api import router; print('✓ api')"
python -c "from models import CampaignPlan; print('✓ models')"
python -c "from config import get_config; print('✓ config')"
python -c "from hotl_system import HOTLDecisionSystem; print('✓ hotl')"

# 2. Test service starts
echo "Starting service..."
timeout 10 python main.py &
PID=$!
sleep 3

# 3. Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8090/health | grep -q "healthy" && echo "✓ Health endpoint working" || echo "✗ Health endpoint failed"

# 4. Kill test server
kill $PID 2>/dev/null

echo "All checks complete!"
```

---

## Expected Output After Fixes

### Before Fixes:
```bash
$ python main.py
Traceback (most recent call last):
  File "main.py", line 99, in <module>
    ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "...").split(",")
NameError: name 'os' is not defined
```

### After Fixes:
```bash
$ python main.py
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
2025-10-24 14:30:00 - __main__ - INFO - 🚀 Offensive Orchestrator Service starting...
2025-10-24 14:30:00 - __main__ - INFO - Configuration loaded: service_port=8090, llm_model=gemini-1.5-pro
2025-10-24 14:30:01 - __main__ - INFO - ✅ Attack Memory System initialized
2025-10-24 14:30:01 - __main__ - INFO - ✅ HOTL Decision System initialized
2025-10-24 14:30:01 - __main__ - INFO - ✅ Offensive Orchestrator Service ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8090 (Press CTRL+C to quit)
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'models'"

**Cause:** Python can't find the modules because service directory not in PYTHONPATH

**Fix:**
```bash
# Option 1: Run from service directory
cd /home/juan/vertice-dev/backend/services/offensive_orchestrator_service
python main.py

# Option 2: Add to PYTHONPATH
export PYTHONPATH=/home/juan/vertice-dev/backend/services/offensive_orchestrator_service:$PYTHONPATH
python main.py

# Option 3: Run as module (if installed)
python -m offensive_orchestrator_service.main
```

### Issue: "ModuleNotFoundError: No module named 'anthropic'"

**Cause:** You chose Option B (fix broken orchestrator) but didn't install anthropic

**Fix:**
```bash
pip install anthropic==0.34.0
```

**Alternative:** Switch to Option A (use working Gemini orchestrator)

### Issue: Service starts but memory system fails

**Check logs for:**
```
Failed to initialize Attack Memory System: ...
```

**Common causes:**
- PostgreSQL not running
- Qdrant not running
- Wrong database credentials in environment variables

**Fix:**
```bash
# Check environment variables
echo $POSTGRES_HOST
echo $POSTGRES_PORT
echo $POSTGRES_DB
echo $POSTGRES_USER

# Set if missing
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=offensive_campaigns
export POSTGRES_USER=maximus
export POSTGRES_PASSWORD=your_password_here
```

---

## Recommended Fix Order

1. ✅ **Fix main.py** (1 line) - MUST DO FIRST
2. ✅ **Fix orchestrator** (Option A recommended) - MUST DO SECOND
3. ✅ **Fix memory imports** (4 files) - SHOULD DO THIRD
4. ⚠️ **Test service** - Verify everything works
5. ⚠️ **Run test suite** - Ensure no regressions

**Total Time:** 15-30 minutes

---

## Quick Copy-Paste Commands

```bash
# Navigate to service
cd /home/juan/vertice-dev/backend/services/offensive_orchestrator_service

# Backup files before editing
cp main.py main.py.backup
cp orchestrator/__init__.py orchestrator/__init__.py.backup
cp memory/attack_memory.py memory/attack_memory.py.backup
cp memory/database.py memory/database.py.backup
cp memory/embeddings.py memory/embeddings.py.backup
cp memory/vector_store.py memory/vector_store.py.backup

# Now apply fixes using your text editor
# See detailed steps above for exact changes

# After fixes, test
python -c "import main" && echo "✓ main.py OK"
python -c "from orchestrator import MaximusOrchestratorAgent" && echo "✓ orchestrator OK"
python -c "from memory import AttackMemorySystem" && echo "✓ memory OK"

# Start service
python main.py
```

---

## Success Criteria

✅ Service starts without import errors
✅ Health endpoint responds: `curl http://localhost:8090/health`
✅ API docs load: `http://localhost:8090/docs`
✅ All tests pass: `pytest tests/`

---

## Get Help

If fixes don't work:
1. Check detailed diagnostic report: `DIAGNOSTIC_REPORT.md`
2. Check dependency map: `DEPENDENCY_MAP.md`
3. Review error logs carefully
4. Verify Python version: `python --version` (should be 3.11+)
5. Verify virtual environment activated: `which python`

**Last Updated:** 2025-10-24
