# NK Cell Coverage Gaps Analysis
**Module**: agents/nk_cell.py
**Current**: 52% (58 tests exist)
**Target**: 90%
**Missing Lines**: 89 lines

---

## Gap Analysis

### Gap #1: Lines 110-117 (Missing MHC-I Detection Path)
**Code**:
```python
for host in hosts_sem_mhc:
    logger.warning(...)
    self.mhc_violations += 1
    await self.neutralizar(host, metodo="isolate")
```

**Coverage Issue**: Tests don't trigger the patrol() flow that finds missing MHC-I hosts and calls neutralization.

**Fix**: Add integration test that mocks RTE response with audit_enabled=False hosts.

---

### Gap #2: Lines 123-130 (Behavioral Anomaly Detection Path)
**Code**:
```python
for host, anomaly_score in hosts_anomalos:
    logger.warning(...)
    self.anomalias_detectadas += 1
    await self.investigar(host)
```

**Coverage Issue**: Tests don't trigger anomaly detection that leads to investigation.

**Fix**: Add test with high anomaly metrics triggering investigation path.

---

### Gap #3: Lines 156-170 (MHC Success Path)
**Code**:
```python
data = await response.json()
hosts_suspeitos = [host for host in data.get("hosts", [])
                   if not host.get("audit_enabled", True)]
logger.debug(...)
return hosts_suspeitos
```

**Coverage Issue**: Success path (status 200) not fully covered.

**Fix**: Mock aiohttp.get() to return hosts with mixed audit_enabled status.

---

### Gap #4: Lines 177-190 (Error Handling Paths)
**Code**:
```python
elif response.status == 404: return []  # Line 177-178
except aiohttp.ClientConnectorError: return []  # Line 180-182
except asyncio.TimeoutError: return []  # Line 184-186
except Exception as e: return []  # Line 188-190
```

**Coverage Issue**: Error paths not tested.

**Fix**: Mock different error scenarios (404, connection error, timeout, generic exception).

---

## Implementation Strategy

Since 58 tests already exist, we need **focused integration tests** that exercise patrol() flow:

1. **test_patrol_with_missing_mhc** - Triggers lines 110-117
2. **test_patrol_with_anomaly** - Triggers lines 123-130
3. **test_detect_mhc_success_with_violations** - Triggers lines 156-170
4. **test_detect_mhc_404_error** - Triggers lines 177-178
5. **test_detect_mhc_connection_error** - Triggers lines 180-182
6. **test_detect_mhc_timeout** - Triggers lines 184-186
7. **test_detect_mhc_generic_exception** - Triggers lines 188-190

**Similar patterns** for other missing line blocks.

**Estimated**: 12-15 new focused tests to reach 90%+.

---

## Next Steps

1. Create focused integration tests for patrol() flow
2. Mock aiohttp responses for happy/error paths
3. Verify coverage increase with each test batch
4. Target: 90%+ coverage (38% increase needed)
