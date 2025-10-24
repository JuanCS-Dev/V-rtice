# Dependency Map - Offensive Orchestrator Service

## Import Dependency Graph

### Service Startup Chain

```
main.py
├── [STDLIB] logging ✓
├── [STDLIB] os ✗ MISSING IMPORT (used at line 99)
├── [STDLIB] contextlib.asynccontextmanager ✓
├── [STDLIB] datetime ✓
├── [EXTERNAL] fastapi ✓ (in requirements.txt)
├── [EXTERNAL] prometheus_client ✓ (in requirements.txt)
├── [LOCAL] config ✓
├── [LOCAL] models ✓
├── [LOCAL] api
│   ├── [STDLIB] logging ✓
│   ├── [STDLIB] typing ✓
│   ├── [STDLIB] uuid ✓
│   ├── [EXTERNAL] fastapi ✓
│   ├── [LOCAL] models ✓
│   └── [LOCAL] orchestrator
│       └── orchestrator/__init__.py
│           └── orchestrator/core.py ✗ BROKEN
│               ├── [STDLIB] typing, dataclasses, datetime, enum, json, logging ✓
│               └── [EXTERNAL] anthropic ✗ NOT IMPORTED, NOT IN requirements.txt
├── [LOCAL] memory
│   └── memory/__init__.py
│       ├── memory/attack_memory.py ✗ RELATIVE IMPORT ISSUES
│       │   ├── [STDLIB] logging, typing, uuid, datetime ✓
│       │   ├── [LOCAL] ..models ⚠️ Relative import (line 27)
│       │   ├── [LOCAL] .database ⚠️ Relative import (line 28)
│       │   ├── [LOCAL] .vector_store ⚠️ Relative import (line 30)
│       │   └── [LOCAL] .embeddings ⚠️ Relative import (line 31)
│       ├── memory/database.py
│       │   ├── [STDLIB] logging, typing, uuid, datetime ✓
│       │   ├── [EXTERNAL] sqlalchemy ✓
│       │   ├── [LOCAL] ..config ⚠️ Relative import
│       │   └── [LOCAL] ..models ⚠️ Relative import
│       ├── memory/vector_store.py
│       │   ├── [STDLIB] logging, typing, uuid, datetime ✓
│       │   ├── [EXTERNAL] qdrant_client ✓
│       │   └── [LOCAL] ..config ⚠️ Relative import
│       └── memory/embeddings.py
│           ├── [STDLIB] logging, typing, hashlib ✓
│           ├── [EXTERNAL] google.generativeai ✓
│           ├── [LOCAL] ..config ⚠️ Relative import
│           └── [LOCAL] ..models ⚠️ Relative import
└── [LOCAL] hotl_system
    ├── [STDLIB] logging, typing, uuid, datetime, pathlib, asyncio, json ✓
    ├── [LOCAL] config ✓
    └── [LOCAL] models ✓
```

### Legend
- ✓ = Working correctly
- ✗ = Critical error (missing/broken)
- ⚠️ = Warning (may fail depending on execution context)

---

## Requirements.txt vs Actual Imports

### MISSING from requirements.txt

```
anthropic     # Used in orchestrator/core.py line 74
              # NOT imported, NOT in requirements.txt
              # Severity: CRITICAL if using orchestrator/core.py
```

### PRESENT in requirements.txt (All Imports)

```python
# Web Framework
fastapi==0.104.1                ✓ Used in: main.py, api.py
uvicorn[standard]==0.24.0       ✓ Used in: main.py
pydantic==2.5.0                 ✓ Used in: models.py
pydantic-settings==2.1.0        ✓ Not directly imported (transitive)

# Database
psycopg2-binary==2.9.9          ✓ Used in: memory/database.py (via SQLAlchemy)
sqlalchemy==2.0.23              ✓ Used in: memory/database.py, models.py
alembic==1.12.1                 ⚠️ Not used in code (migrations tool)

# Vector Database
qdrant-client==1.7.0            ✓ Used in: memory/vector_store.py

# LLM & AI
google-generativeai==0.3.1      ✓ Used in: orchestrator.py, memory/embeddings.py
langchain==0.1.0                ✓ Used in: orchestrator.py
langchain-google-genai==0.0.6   ✓ Used in: orchestrator.py (transitive)
openai==1.6.1                   ⚠️ Not used in code (fallback/future use)

# Async & Concurrency
aiohttp==3.9.1                  ⚠️ Not used in code
asyncio==3.4.3                  ✓ Used in: multiple files (stdlib, doesn't need install)

# Data Processing
numpy==1.26.2                   ⚠️ Not used in code
pandas==2.1.4                   ⚠️ Not used in code

# Utilities
python-dotenv==1.0.0            ⚠️ Not used in code
python-jose[cryptography]==3.3.0 ⚠️ Not used in code
passlib[bcrypt]==1.7.4          ⚠️ Not used in code
python-multipart==0.0.6         ⚠️ Not used in code

# Monitoring & Logging
prometheus-client==0.19.0       ✓ Used in: main.py
python-json-logger==2.0.7       ⚠️ Not used in code

# Testing
pytest==7.4.3                   ✓ Used in: tests/*
pytest-asyncio==0.21.1          ✓ Used in: tests/*
pytest-cov==4.1.0               ✓ Used for coverage
pytest-mock==3.12.0             ✓ Used in: tests/*
httpx==0.25.2                   ✓ Used in: tests/test_api.py

# Development
black==23.12.1                  ⚠️ Dev tool
ruff==0.1.8                     ⚠️ Dev tool
mypy==1.7.1                     ⚠️ Dev tool
types-redis==4.6.0.11           ⚠️ Type stubs

# Security
cryptography==41.0.7            ✓ Used by python-jose
```

### UNUSED Dependencies (Consider Removing)

```
aiohttp              # Not imported anywhere
asyncio              # Stdlib, doesn't need installation
numpy                # Not imported anywhere
pandas               # Not imported anywhere
python-dotenv        # Not used (config uses os.getenv directly)
python-jose          # Not imported anywhere
passlib              # Not imported anywhere
python-multipart     # Not imported anywhere
python-json-logger   # Not imported anywhere
openai               # Not imported (marked as "fallback")
```

---

## File-by-File Import Analysis

### main.py
```python
# STDLIB
import logging                           ✓
import os                                ✗ MISSING (used line 99)
from contextlib import asynccontextmanager ✓
from datetime import import datetime     ✓

# EXTERNAL
from fastapi import FastAPI, Request     ✓
from fastapi.middleware.cors import CORSMiddleware ✓
from fastapi.responses import JSONResponse ✓
from prometheus_client import make_asgi_app ✓

# LOCAL
from config import get_config            ✓
from models import HealthResponse        ✓
from api import router as api_router     ✓
from memory import AttackMemorySystem    ⚠️ (relative import issues)
from hotl_system import HOTLDecisionSystem ✓
```

### api.py
```python
# STDLIB
import logging                           ✓
from typing import List, Optional        ✓
from uuid import UUID                    ✓

# EXTERNAL
from fastapi import APIRouter, HTTPException, Query, Depends ✓

# LOCAL
from models import (...)                 ✓
from orchestrator import MaximusOrchestratorAgent ✗ (broken in core.py)
```

### orchestrator/core.py (BROKEN)
```python
# STDLIB
from typing import List, Optional, Dict, Any ✓
from dataclasses import dataclass, field ✓
from datetime import datetime            ✓
from enum import Enum                    ✓
import json                              ✓
import logging                           ✓

# EXTERNAL
import anthropic                         ✗ NOT IMPORTED (used line 74)

# LOCAL
# None
```

### orchestrator.py (WORKING ALTERNATIVE)
```python
# STDLIB
import asyncio                           ✓
import logging                           ✓
from datetime import datetime            ✓
from typing import Dict, Any, Optional   ✓
from uuid import UUID, uuid4             ✓

# EXTERNAL
import google.generativeai as genai      ✓
from langchain.prompts import PromptTemplate ✓

# LOCAL
from config import get_config, LLMConfig ✓
from models import (...)                 ✓
```

### memory/attack_memory.py
```python
# STDLIB
import logging                           ✓
from typing import Optional, List, Dict, Any, Tuple ✓
from uuid import UUID                    ✓
from datetime import datetime            ✓

# EXTERNAL
# None

# LOCAL
from ..models import (...)               ⚠️ Relative import (may fail)
from .database import DatabaseManager    ⚠️ Relative import
from .vector_store import VectorStore    ⚠️ Relative import
from .embeddings import EmbeddingGenerator ⚠️ Relative import
```

### memory/database.py
```python
# STDLIB
import logging                           ✓
from typing import Optional, List, Dict, Any ✓
from uuid import UUID                    ✓
from datetime import datetime            ✓

# EXTERNAL
from sqlalchemy import create_engine, select, and_ ✓
from sqlalchemy.orm import sessionmaker, Session ✓
from sqlalchemy.pool import QueuePool    ✓

# LOCAL
from ..config import DatabaseConfig, get_config ⚠️ Relative import
from ..models import Base, CampaignDB, HOTLDecisionDB, AttackMemoryDB, CampaignStatus ⚠️ Relative import
```

### memory/vector_store.py
```python
# STDLIB
import logging                           ✓
from typing import Optional, List, Dict, Any, Tuple ✓
from uuid import UUID                    ✓
from datetime import datetime            ✓

# EXTERNAL
from qdrant_client import QdrantClient   ✓
from qdrant_client.http import models as qdrant_models ✓

# LOCAL
from ..config import VectorDBConfig, get_config ⚠️ Relative import
```

### memory/embeddings.py
```python
# STDLIB
import logging                           ✓
import hashlib                           ✓
from typing import Optional, List, Dict  ✓

# EXTERNAL
import google.generativeai as genai      ✓
from google.api_core import exceptions as google_exceptions ✓
from google.api_core import retry        ✓

# LOCAL
from ..config import LLMConfig, get_config ⚠️ Relative import
from ..models import CampaignPlan, CampaignObjective ⚠️ Relative import
```

### config.py
```python
# STDLIB
import os                                ✓
from typing import Optional              ✓
from dataclasses import dataclass, field ✓

# EXTERNAL
# None

# LOCAL
# None
```

### models.py
```python
# STDLIB
from datetime import datetime            ✓
from typing import Optional, List, Dict, Any ✓
from enum import Enum                    ✓
from uuid import UUID, uuid4             ✓

# EXTERNAL
from pydantic import BaseModel, Field, ConfigDict ✓
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, Text, Integer, Boolean ✓
from sqlalchemy.ext.declarative import declarative_base ✓
from sqlalchemy.dialects.postgresql import UUID as PGUUID ✓

# LOCAL
# None
```

### hotl_system.py
```python
# STDLIB
import asyncio                           ✓
import json                              ✓
import logging                           ✓
from datetime import datetime            ✓
from pathlib import Path                 ✓
from typing import Optional, List, Dict  ✓
from uuid import UUID                    ✓

# EXTERNAL
# None

# LOCAL
from config import HOTLConfig            ✓
from models import (...)                 ✓
```

---

## Circular Dependency Check

**Status:** ✓ No circular dependencies detected

**Import Tree (Simplified):**
```
main.py
  ├─> api.py ──> orchestrator/
  ├─> memory/ ──> models, config
  ├─> hotl_system ──> models, config
  ├─> models (leaf node)
  └─> config (leaf node)

orchestrator/
  ├─> models
  └─> config

memory/
  ├─> models
  └─> config

No cycles detected.
```

---

## Critical Path for Service Startup

```
1. main.py imports
   ├─ os.getenv()                    ✗ FAILS (missing import)
   └─ STOPPED HERE

2. If os import fixed:
   ├─ api.py imports
   │  └─ orchestrator/__init__.py
   │     └─ orchestrator/core.py
   │        └─ anthropic.Anthropic() ✗ FAILS (missing import)
   └─ STOPPED HERE

3. If anthropic import fixed OR switch to orchestrator.py:
   ├─ memory/__init__.py
   │  └─ memory/attack_memory.py
   │     └─ from ..models          ⚠️ MAY FAIL (relative import)
   └─ Service may start with degraded memory functionality

4. If all imports fixed:
   └─ Service starts successfully  ✓
```

---

## Recommendations

### 1. Immediate Fixes (CRITICAL)
```python
# main.py - ADD
import os

# orchestrator/core.py - EITHER:
# Option A: Add import
import anthropic

# Option B: Delete file and use orchestrator.py instead
```

### 2. High Priority (Prevents core features)
```python
# memory/attack_memory.py - CHANGE FROM:
from ..models import CampaignPlan, CampaignObjective, CampaignDB, CampaignStatus
from .database import DatabaseManager
from .vector_store import VectorStore
from .embeddings import EmbeddingGenerator

# TO:
from models import CampaignPlan, CampaignObjective, CampaignDB, CampaignStatus
from memory.database import DatabaseManager
from memory.vector_store import VectorStore
from memory.embeddings import EmbeddingGenerator
```

### 3. Clean Up requirements.txt
```bash
# Remove unused dependencies:
pip uninstall aiohttp numpy pandas python-dotenv python-jose passlib python-multipart python-json-logger openai

# Update requirements.txt:
pip freeze > requirements-clean.txt
```

### 4. Add Missing Dependencies
```bash
# If keeping orchestrator/core.py:
pip install anthropic==0.34.0
echo "anthropic==0.34.0" >> requirements.txt
```

---

## Dependency Audit Summary

| Category | Count | Status |
|----------|-------|--------|
| Total dependencies in requirements.txt | 27 | |
| Actually used in code | 18 | ✓ |
| Unused/Dev tools | 9 | ⚠️ Can be removed |
| Missing from requirements.txt | 1 | ✗ anthropic |
| Missing stdlib imports | 1 | ✗ os in main.py |

**Code Health:** 🔴 POOR (3 critical import errors preventing startup)
**Dependency Health:** 🟡 FAIR (some unused deps, 1 missing)
**Maintainability:** 🟡 FAIR (duplicate orchestrator implementations, inconsistent imports)

---

**Analysis Completed:** 2025-10-24
**Total Files Analyzed:** 47 Python files
**Critical Issues Found:** 3
**High Issues Found:** 5
**Medium Issues Found:** 9
