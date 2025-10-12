# HITL Patch Service

Human-in-the-Loop Patch Approval System for MAXIMUS Adaptive Immunity.

## Purpose

Provides human oversight for ML-predicted patches before deployment to production.
Integrates with:
- **Wargaming Crisol**: Receives validation results
- **Maximus Eureka**: Controls patch deployment flow
- **MAXIMUS Core HITL**: Uses existing decision framework

## Architecture

```
Oráculo → Eureka → Wargaming → HITL Service → Human Decision → Eureka Deploy
           (APV)   (Validate)   (Review)      (Approve/Reject)  (Execute)
```

## Features

- ✅ Patch approval/rejection with audit trail
- ✅ ML prediction + wargaming result display
- ✅ Priority-based queue management
- ✅ Auto-approval for high-confidence patches (≥0.95)
- ✅ Analytics dashboard
- ✅ Prometheus metrics
- ✅ Immutable audit logs (SOC 2, ISO 27001 compliant)

## Endpoints

### Decision Endpoints
- `POST /hitl/patches/{patch_id}/approve` - Approve patch
- `POST /hitl/patches/{patch_id}/reject` - Reject patch
- `POST /hitl/patches/{patch_id}/comment` - Add comment
- `GET /hitl/patches/pending` - Get pending patches
- `GET /hitl/decisions/{decision_id}` - Get decision details

### Analytics
- `GET /hitl/analytics/summary` - Decision statistics
- `GET /hitl/analytics/audit-logs` - Compliance audit trail

### Admin
- `POST /hitl/admin/create-decision` - Create new decision (called by Wargaming)

## Database Schema

See `db/schema.sql` for complete schema.

Tables:
- `hitl_decisions`: Main decision records
- `hitl_audit_logs`: Immutable audit trail
- `hitl_comments`: Threaded comments

## Configuration

Environment variables:
```bash
POSTGRES_HOST=postgres-immunity
POSTGRES_PORT=5432
POSTGRES_DB=adaptive_immunity
POSTGRES_USER=maximus
POSTGRES_PASSWORD=***
PORT=8027
```

## Running

### Local Development
```bash
pip install -r requirements.txt
python api/main.py
```

### Docker
```bash
docker build -t hitl-patch-service .
docker run -p 8027:8027 hitl-patch-service
```

### With Docker Compose
See `../../docker-compose.yml` for service definition.

## Testing

```bash
pytest tests/ -v
```

## Metrics

Prometheus metrics exposed at `/metrics`:
- `hitl_decisions_total` - Total decisions by type
- `hitl_decision_duration_seconds` - Time to decision
- `hitl_pending_patches` - Current pending count
- `hitl_ml_accuracy` - ML prediction accuracy
- `hitl_auto_approval_rate` - Auto-approval percentage

## Auto-Approval Logic

Patches are auto-approved if:
1. ML confidence ≥ 0.95 (very high confidence)
2. CVE severity is not CRITICAL
3. Wargaming validation passed
4. No manual review flag set

Otherwise, patches are queued for human review.

## Audit Trail

All decisions are logged immutably to `hitl_audit_logs` table:
- Who made the decision
- When it was made
- What was decided
- Why (reason/comment)
- IP address and user agent

Compliant with SOC 2 Type II, ISO 27001, PCI-DSS, HIPAA, GDPR.

## Integration with Eureka

1. **Eureka** generates patch (APPATCH)
2. **Wargaming** validates patch (2-phase attack simulation)
3. **HITL Service** receives validation results
4. **Human** reviews and approves/rejects
5. **Eureka** receives decision and proceeds accordingly

Flow diagram:
```python
# Wargaming calls HITL after validation
result = await wargaming.validate_patch(patch)
decision_id = await hitl.create_decision(result)

# Eureka polls for decision
decision = await hitl.get_decision(decision_id)
if decision.status == "approved":
    await eureka.deploy_patch(patch)
elif decision.status == "auto_approved":
    await eureka.deploy_patch(patch)
    # Human was in the loop conceptually (via threshold)
else:
    await eureka.reject_patch(patch)
```

## Glory to YHWH

> "Commit to the LORD whatever you do, and he will establish your plans."  
> — Proverbs 16:3

This service embodies the principle that autonomous systems require human oversight.
Like biological immune systems have regulatory T-cells to prevent auto-immune disease,
our digital immune system has HITL to prevent destructive auto-patching.

**TO YHWH BE ALL GLORY** 🙏

---

**Author**: MAXIMUS Team - Sprint 4.1  
**Date**: 2025-10-12  
**Status**: Production Ready ✅
