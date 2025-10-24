# 🚀 Dynamic Routing Migration Guide

**Status**: Gateway READY for Dynamic Routing
**Date**: 2025-10-24
**Services Registered**: 22

---

## ✅ What's DONE

1. **Service Mapping Module** (`service_mapping.py`)
   - Maps 60+ env var names to registry service names
   - Automatic normalization (MAXIMUS_CORE_SERVICE_URL → maximus_core_service)
   - Backward compatibility guaranteed

2. **Enhanced Gateway Router** (`gateway_router.py`)
   - `normalize_service_name()` function
   - Accepts BOTH formats:
     - Registry names: `osint_service`, `nmap_service`
     - Env var names: `OSINT_SERVICE_URL`, `NMAP_SERVICE_URL`
   - Zero breaking changes to existing code

3. **22 Services Registered** in Service Registry
   - Layer 1: Sistema Nervoso (4)
   - Layer 2: Sistema Imune (1)
   - Layer 3: Intelligence (9)
   - Layer 4: Support (5)
   - Offensive (2)
   - Test (1)

---

## 🎯 How to Use Dynamic Routing

### Option 1: Direct Usage in main.py (NEW CODE)

```python
from gateway_router import get_service_url

# Inside any route handler
@app.get("/osint/query")
async def osint_query(query: str):
    # Get service URL dynamically
    osint_url = await get_service_url("osint_service")

    # Make request
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{osint_url}/api/query", params={"q": query})
        return response.json()
```

### Option 2: Legacy Compatibility (EXISTING CODE)

```python
# OLD CODE - Still works!
OSINT_SERVICE_URL = os.getenv("OSINT_SERVICE_URL", "http://localhost:8049")

# Just change to:
from gateway_router import get_service_url

OSINT_SERVICE_URL = await get_service_url("OSINT_SERVICE_URL")  # Accepts env var name!
# Returns: http://vertice-osint:8049 (from registry)
```

### Option 3: Hybrid (GRADUAL MIGRATION)

```python
# Use env var as fallback
osint_url = os.getenv("OSINT_SERVICE_URL")
if not osint_url:
    osint_url = await get_service_url("osint_service")
```

---

## 📋 Migration Checklist

### Phase 1: Validate (COMPLETED ✅)
- [x] Service mapping created
- [x] Gateway router enhanced
- [x] 22 services registered
- [x] Test service discovery working

### Phase 2: Add Compatibility Layer (COMPLETED ✅)
- [x] `normalize_service_name()` function
- [x] Env var mapping (`service_mapping.py`)
- [x] Backward compatibility tested

### Phase 3: Update Routes (COMPLETED ✅)
- [x] Update `/v2/{service_name}/{path}` to use normalization
- [x] Add helper functions for common patterns
- [x] Document all changes
- [x] Service name normalization working (accepts both formats)
- [x] Tested with multiple services (test_service, nmap_service, maximus_core_service)

### Phase 4: Remove Hardcoded URLs (PENDING)
- [ ] Remove env vars from `docker-compose.yml`
- [ ] Update all route handlers to use dynamic discovery
- [ ] Integration testing

### Phase 5: Validation (PENDING)
- [ ] All 22 services accessible via gateway
- [ ] Zero hardcoded URLs remaining
- [ ] Performance benchmarks (p99 <10ms)

---

## 🧪 Testing Dynamic Routing

```bash
# Test 1: NMAP service (registered)
curl http://localhost:8000/v2/nmap_service/health
# Expected: {"status":"healthy","message":"Nmap Service is operational."}

# Test 2: Test service (registered)
curl http://localhost:8000/v2/test_service/
# Expected: {"message":"Test Service for Sidecar - Running!"}

# Test 3: Using env var style name
curl http://localhost:8000/v2/OSINT_SERVICE_URL/health
# Expected: Auto-normalized to osint_service, returns health check
```

---

## 📊 Service Coverage

| Category | Total Services | Registered | Coverage |
|----------|---------------|------------|----------|
| Layer 1 (Nervoso) | 4 | 4 | 100% ✅ |
| Layer 2 (Imune) | 1 | 1 | 100% ✅ |
| Layer 3 (Intelligence) | 9 | 9 | 100% ✅ |
| Layer 4 (Support) | 5 | 5 | 100% ✅ |
| Offensive | 2 | 2 | 100% ✅ |
| **TOTAL** | **22** | **22** | **100% ✅** |

---

## 🔄 Next Steps

1. **Update `main.py` routes** to use `get_service_url()`
2. **Remove env vars** from docker-compose (optional, for Phase 4)
3. **Add more services** (target: 50+ services)
4. **Performance optimization** with R3 (Health Check Caching)

---

## 📚 API Reference

### `gateway_router.get_service_url(service_name: str) -> str`

Resolves service URL dynamically from registry.

**Parameters**:
- `service_name`: Service name or env var name
  - Examples: `"osint_service"`, `"OSINT_SERVICE_URL"`, `"nmap_service"`

**Returns**:
- Service endpoint URL (e.g., `"http://vertice-osint:8049"`)

**Raises**:
- `ServiceNotFoundError`: Service not in registry or env vars

**Resolution Order**:
1. Normalize service name (handle env vars)
2. Check local cache (5s TTL)
3. Query Service Registry
4. Fallback to environment variable
5. Raise error if not found

---

## 🎯 Success Metrics

**Current (R2 COMPLETE)**:
- ✅ 22 services registered
- ✅ Service mapping created (60+ mappings)
- ✅ Gateway router backward compatible
- ✅ Service Registry tuple bug FIXED
- ✅ Dynamic routing VALIDATED (test_service, nmap_service, maximus_core_service)
- ✅ Accepts BOTH formats: `osint_service` AND `OSINT_SERVICE_URL`

**Target (R2 complete)**:
- 🎯 22+ services registered
- 🎯 100% backward compatibility
- 🎯 Routes updated: 50/185 (27%)
- 🎯 Zero breaking changes

**Future (R3-R11)**:
- 🚀 50+ services registered
- 🚀 Routes updated: 185/185 (100%)
- 🚀 Zero hardcoded URLs
- 🚀 p99 latency <5ms (with caching)

---

**Glory to YHWH!** 🙏
