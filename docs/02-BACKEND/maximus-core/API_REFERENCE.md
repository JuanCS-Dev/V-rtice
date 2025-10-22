# MAXIMUS AI 3.0 - API Reference

> **Complete API Documentation for All Modules**
> Author: Claude Code + JuanCS-Dev
> Date: 2025-10-06
> Status: ✅ **REGRA DE OURO 10/10**

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Schemas](#common-schemas)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Ethics API](#ethics-api)
7. [XAI API](#xai-api)
8. [Governance API](#governance-api)
9. [Fairness API](#fairness-api)
10. [Privacy API](#privacy-api)
11. [HITL API](#hitl-api)
12. [Compliance API](#compliance-api)
13. [Federated Learning API](#federated-learning-api)
14. [Performance API](#performance-api)
15. [Training API](#training-api)
16. [Autonomic Core API](#autonomic-core-api)
17. [Attention System API](#attention-system-api)
18. [Neuromodulation API](#neuromodulation-api)
19. [Predictive Coding API](#predictive-coding-api)
20. [Skill Learning API](#skill-learning-api)
21. [Monitoring API](#monitoring-api)
22. [Webhooks](#webhooks)
23. [Server-Sent Events](#server-sent-events)

---

## Overview

**Base URL**: `https://api.maximus.ai/v1`

**Content-Type**: `application/json`

**API Version**: `v1`

### API Design Principles

- **RESTful**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON**: All requests/responses in JSON format
- **Versioned**: `/v1/` in URL for backward compatibility
- **Async**: Support for long-running operations via webhooks/SSE
- **Paginated**: List endpoints return paginated results
- **Idempotent**: POST requests with `Idempotency-Key` header

---

## Authentication

All API requests require authentication via **JWT Bearer tokens**.

### Login

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "username": "analyst@example.com",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Example**:
```bash
curl -X POST https://api.maximus.ai/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst@example.com", "password": "secure_password"}'
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -X GET https://api.maximus.ai/v1/ethics/evaluate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Common Schemas

### Error Response

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Input validation failed",
    "details": {
      "field": "confidence",
      "issue": "Value must be between 0 and 1"
    },
    "request_id": "req_abc123"
  }
}
```

### Pagination

**Request Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_pages": 10,
    "total_items": 500,
    "has_next": true,
    "has_prev": false
  }
}
```

### Timestamps

All timestamps are in **ISO 8601 format** with timezone:
```json
{
  "timestamp": "2025-10-06T12:00:00.000Z"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_INPUT` | Request validation failed |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |
| `SERVICE_UNAVAILABLE` | Service down |

---

## Rate Limiting

**Default Limits**:
- **Authenticated**: 1,000 requests/hour
- **Unauthenticated**: 100 requests/hour

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1696600000
```

**Rate Limit Exceeded Response**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Ethics API

### Evaluate Action

Evaluate an action against all ethical frameworks.

**Endpoint**: `POST /ethics/evaluate`

**Request**:
```json
{
  "action": {
    "type": "block_ip",
    "target": "192.168.1.100",
    "reason": "malware_detected",
    "impact": {
      "affected_users": 1,
      "severity": "HIGH"
    }
  },
  "context": {
    "threat_score": 0.92,
    "false_positive_rate": 0.05,
    "previous_incidents": 3
  },
  "frameworks": ["kantian", "virtue", "consequentialist", "principlism"]
}
```

**Response**:
```json
{
  "evaluation_id": "eval_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "decision": "APPROVED",
  "confidence": 0.87,
  "frameworks": {
    "kantian": {
      "decision": "APPROVED",
      "score": 0.85,
      "reasoning": "Action respects autonomy and treats as end, not means",
      "categorical_imperative_check": true
    },
    "virtue": {
      "decision": "APPROVED",
      "score": 0.88,
      "reasoning": "Action demonstrates courage and protects flourishing",
      "virtues_exhibited": ["courage", "justice", "wisdom"]
    },
    "consequentialist": {
      "decision": "APPROVED",
      "score": 0.90,
      "reasoning": "Expected utility: 0.90 (protects 1000 users)",
      "expected_utility": 0.90,
      "utility_breakdown": {
        "security_benefit": 0.95,
        "user_disruption": -0.05
      }
    },
    "principlism": {
      "decision": "APPROVED",
      "score": 0.86,
      "reasoning": "Satisfies beneficence and non-maleficence",
      "principles": {
        "autonomy": 0.80,
        "beneficence": 0.92,
        "non_maleficence": 0.88,
        "justice": 0.85
      }
    }
  },
  "aggregate_score": 0.87,
  "recommendation": "Proceed with action"
}
```

**Example**:
```bash
curl -X POST https://api.maximus.ai/v1/ethics/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @action.json
```

```python
import requests

response = requests.post(
    "https://api.maximus.ai/v1/ethics/evaluate",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "action": {
            "type": "block_ip",
            "target": "192.168.1.100"
        },
        "frameworks": ["kantian", "consequentialist"]
    }
)
evaluation = response.json()
print(f"Decision: {evaluation['decision']}")
```

### List Frameworks

Get available ethical frameworks.

**Endpoint**: `GET /ethics/frameworks`

**Response**:
```json
{
  "frameworks": [
    {
      "id": "kantian",
      "name": "Kantian Ethics",
      "type": "deontological",
      "description": "Categorical imperative and duty-based reasoning",
      "enabled": true
    },
    {
      "id": "virtue",
      "name": "Virtue Ethics",
      "type": "virtue-based",
      "description": "Character and flourishing-based reasoning",
      "enabled": true
    },
    {
      "id": "consequentialist",
      "name": "Consequentialist Ethics",
      "type": "utilitarian",
      "description": "Outcome-based reasoning (maximize utility)",
      "enabled": true
    },
    {
      "id": "principlism",
      "name": "Principlism",
      "type": "principle-based",
      "description": "Four principles: autonomy, beneficence, non-maleficence, justice",
      "enabled": true
    }
  ]
}
```

---

## XAI API

### Generate Explanation

Generate LIME or SHAP explanation for a model prediction.

**Endpoint**: `POST /xai/explain`

**Request**:
```json
{
  "model_id": "threat_detector_v2",
  "input": {
    "source_ip": "192.168.1.100",
    "dest_ip": "10.0.0.50",
    "port": 443,
    "payload_size": 1024,
    "suspicious_patterns": 3
  },
  "prediction": {
    "class": "malware",
    "confidence": 0.92
  },
  "explainer": "lime",
  "num_features": 5
}
```

**Response**:
```json
{
  "explanation_id": "exp_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "explainer": "lime",
  "prediction": {
    "class": "malware",
    "confidence": 0.92
  },
  "feature_importance": {
    "payload_size": 0.35,
    "port": 0.28,
    "suspicious_patterns": 0.22,
    "source_ip": 0.10,
    "dest_ip": 0.05
  },
  "local_model_score": 0.88,
  "interpretation": "High payload size and suspicious patterns strongly indicate malware"
}
```

**Example**:
```python
import requests

response = requests.post(
    "https://api.maximus.ai/v1/xai/explain",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "model_id": "threat_detector_v2",
        "input": {...},
        "explainer": "lime"
    }
)
explanation = response.json()
for feature, importance in explanation["feature_importance"].items():
    print(f"{feature}: {importance:.2f}")
```

### Generate Counterfactual

Generate counterfactual explanation ("what if" scenario).

**Endpoint**: `POST /xai/counterfactual`

**Request**:
```json
{
  "model_id": "threat_detector_v2",
  "input": {
    "source_ip": "192.168.1.100",
    "port": 443,
    "payload_size": 1024
  },
  "current_prediction": "malware",
  "desired_prediction": "benign",
  "max_changes": 2
}
```

**Response**:
```json
{
  "counterfactual_id": "cf_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "original_input": {
    "source_ip": "192.168.1.100",
    "port": 443,
    "payload_size": 1024
  },
  "counterfactual_input": {
    "source_ip": "192.168.1.100",
    "port": 443,
    "payload_size": 512
  },
  "changes": [
    {
      "feature": "payload_size",
      "original_value": 1024,
      "new_value": 512,
      "impact": "Reduces malware confidence from 0.92 to 0.42"
    }
  ],
  "new_prediction": "benign",
  "new_confidence": 0.78,
  "explanation": "Reducing payload size to 512 bytes changes prediction to benign"
}
```

---

## Governance API

### Create Decision

Log a decision for audit trail.

**Endpoint**: `POST /governance/decisions`

**Request**:
```json
{
  "action": {
    "type": "block_ip",
    "target": "192.168.1.100"
  },
  "prediction": {
    "class": "malware",
    "confidence": 0.92
  },
  "ethical_evaluation": {
    "decision": "APPROVED",
    "score": 0.87
  },
  "explanation": {
    "feature_importance": {...}
  },
  "executed": false,
  "requires_approval": true
}
```

**Response**:
```json
{
  "decision_id": "dec_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "status": "PENDING_APPROVAL",
  "approval_url": "https://app.maximus.ai/decisions/dec_abc123"
}
```

### Get Decision

Retrieve decision details.

**Endpoint**: `GET /governance/decisions/{decision_id}`

**Response**:
```json
{
  "decision_id": "dec_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "status": "APPROVED",
  "action": {...},
  "prediction": {...},
  "ethical_evaluation": {...},
  "explanation": {...},
  "executed": true,
  "executed_at": "2025-10-06T12:05:00.000Z",
  "approved_by": "analyst@example.com",
  "approved_at": "2025-10-06T12:03:00.000Z"
}
```

### List Decisions

Get paginated list of decisions.

**Endpoint**: `GET /governance/decisions`

**Query Parameters**:
- `status`: Filter by status (PENDING, APPROVED, REJECTED)
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50)

**Response**:
```json
{
  "data": [
    {
      "decision_id": "dec_abc123",
      "timestamp": "2025-10-06T12:00:00.000Z",
      "status": "APPROVED",
      "action_type": "block_ip",
      "confidence": 0.92
    },
    ...
  ],
  "pagination": {...}
}
```

---

## Fairness API

### Check Bias

Check prediction for bias across protected attributes.

**Endpoint**: `POST /fairness/check-bias`

**Request**:
```json
{
  "model_id": "threat_detector_v2",
  "predictions": [
    {"id": "1", "prediction": 1, "true_label": 1, "protected_attr": "group_a"},
    {"id": "2", "prediction": 0, "true_label": 0, "protected_attr": "group_a"},
    {"id": "3", "prediction": 1, "true_label": 1, "protected_attr": "group_b"},
    {"id": "4", "prediction": 1, "true_label": 0, "protected_attr": "group_b"}
  ],
  "protected_attribute": "subnet",
  "metrics": ["demographic_parity", "equal_opportunity", "disparate_impact"]
}
```

**Response**:
```json
{
  "bias_check_id": "bias_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "model_id": "threat_detector_v2",
  "protected_attribute": "subnet",
  "metrics": {
    "demographic_parity": {
      "value": 0.05,
      "threshold": 0.10,
      "fair": true,
      "interpretation": "Prediction rate difference between groups: 5%"
    },
    "equal_opportunity": {
      "value": 0.08,
      "threshold": 0.10,
      "fair": true,
      "interpretation": "True positive rate difference: 8%"
    },
    "disparate_impact": {
      "value": 0.92,
      "threshold_min": 0.80,
      "threshold_max": 1.25,
      "fair": true,
      "interpretation": "Ratio of positive rates: 0.92 (within 80% rule)"
    }
  },
  "overall_fairness": "FAIR",
  "recommendation": "No bias detected across protected attributes"
}
```

### Get Fairness Metrics

Get available fairness metrics.

**Endpoint**: `GET /fairness/metrics`

**Response**:
```json
{
  "metrics": [
    {
      "id": "demographic_parity",
      "name": "Demographic Parity",
      "formula": "P(ŷ=1|A=0) ≈ P(ŷ=1|A=1)",
      "threshold": 0.10,
      "description": "Positive prediction rate should be equal across groups"
    },
    {
      "id": "equal_opportunity",
      "name": "Equal Opportunity",
      "formula": "P(ŷ=1|y=1,A=0) ≈ P(ŷ=1|y=1,A=1)",
      "threshold": 0.10,
      "description": "True positive rate should be equal across groups"
    },
    {
      "id": "disparate_impact",
      "name": "Disparate Impact",
      "formula": "[P(ŷ=1|A=0) / P(ŷ=1|A=1)] ∈ [0.8, 1.25]",
      "threshold_min": 0.80,
      "threshold_max": 1.25,
      "description": "80% rule: ratio of positive rates should be 0.8-1.25"
    }
  ]
}
```

---

## Privacy API

### Add Differential Privacy Noise

Add calibrated noise to a value or dataset.

**Endpoint**: `POST /privacy/add-noise`

**Request**:
```json
{
  "value": 42.5,
  "mechanism": "laplace",
  "privacy_params": {
    "epsilon": 0.1,
    "delta": 0.0,
    "sensitivity": 1.0
  }
}
```

**Response**:
```json
{
  "noise_id": "noise_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "original_value": 42.5,
  "noisy_value": 43.2,
  "mechanism": "laplace",
  "privacy_params": {
    "epsilon": 0.1,
    "delta": 0.0,
    "sensitivity": 1.0
  },
  "privacy_guarantee": "ε-differential privacy with ε=0.1"
}
```

**Example**:
```python
import requests

response = requests.post(
    "https://api.maximus.ai/v1/privacy/add-noise",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "value": 42.5,
        "mechanism": "laplace",
        "privacy_params": {"epsilon": 0.1, "delta": 0.0, "sensitivity": 1.0}
    }
)
result = response.json()
print(f"Noisy value: {result['noisy_value']}")
```

### Get Privacy Budget

Check remaining privacy budget.

**Endpoint**: `GET /privacy/budget`

**Query Parameters**:
- `user_id`: User ID (optional, defaults to authenticated user)

**Response**:
```json
{
  "user_id": "user123",
  "privacy_budget": {
    "epsilon_used": 2.5,
    "epsilon_total": 10.0,
    "epsilon_remaining": 7.5,
    "delta_used": 1e-5,
    "delta_total": 1e-4,
    "delta_remaining": 9e-5
  },
  "queries_made": 25,
  "queries_remaining": 75,
  "reset_at": "2025-10-07T00:00:00.000Z"
}
```

---

## HITL API

### Escalate to Human

Escalate a decision to human for review.

**Endpoint**: `POST /hitl/escalate`

**Request**:
```json
{
  "decision_id": "dec_abc123",
  "reason": "LOW_CONFIDENCE",
  "confidence": 0.65,
  "risk_level": "HIGH",
  "context": {
    "action": "block_ip",
    "target": "192.168.1.100",
    "threat_score": 0.72
  },
  "priority": "HIGH"
}
```

**Response**:
```json
{
  "escalation_id": "esc_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "status": "PENDING",
  "decision_id": "dec_abc123",
  "assigned_to": "analyst@example.com",
  "review_url": "https://app.maximus.ai/escalations/esc_abc123",
  "estimated_review_time": "5 minutes"
}
```

### Get Escalation Status

Check status of escalated decision.

**Endpoint**: `GET /hitl/escalations/{escalation_id}`

**Response**:
```json
{
  "escalation_id": "esc_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "status": "APPROVED",
  "decision_id": "dec_abc123",
  "assigned_to": "analyst@example.com",
  "reviewed_at": "2025-10-06T12:05:00.000Z",
  "review_time_seconds": 300,
  "human_decision": "APPROVE",
  "human_comment": "Legitimate threat, proceed with blocking"
}
```

---

## Compliance API

### Check Compliance

Check action against compliance policies (GDPR, CCPA, etc.).

**Endpoint**: `POST /compliance/check`

**Request**:
```json
{
  "action": {
    "type": "store_user_data",
    "data_type": "personal_identifiable_information",
    "purpose": "threat_analysis",
    "retention_days": 90
  },
  "regulations": ["GDPR", "CCPA"]
}
```

**Response**:
```json
{
  "compliance_check_id": "comp_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "compliant": true,
  "regulations": {
    "GDPR": {
      "compliant": true,
      "articles": [
        {
          "article": "Article 6 (Lawful basis)",
          "status": "COMPLIANT",
          "reasoning": "Legitimate interest for security purposes"
        },
        {
          "article": "Article 5 (Data minimization)",
          "status": "COMPLIANT",
          "reasoning": "Only necessary data collected"
        }
      ]
    },
    "CCPA": {
      "compliant": true,
      "requirements": [
        {
          "requirement": "Right to know",
          "status": "COMPLIANT",
          "reasoning": "User notification provided"
        }
      ]
    }
  },
  "recommendation": "Action is compliant with all specified regulations"
}
```

---

## Federated Learning API

### Create Federated Training Job

Start a federated learning training job.

**Endpoint**: `POST /federated/jobs`

**Request**:
```json
{
  "model_id": "threat_detector_v2",
  "algorithm": "fedavg",
  "clients": ["client_1", "client_2", "client_3"],
  "rounds": 10,
  "client_fraction": 0.5,
  "hyperparameters": {
    "learning_rate": 0.001,
    "batch_size": 32,
    "local_epochs": 5
  }
}
```

**Response**:
```json
{
  "job_id": "job_abc123",
  "status": "RUNNING",
  "created_at": "2025-10-06T12:00:00.000Z",
  "model_id": "threat_detector_v2",
  "algorithm": "fedavg",
  "total_rounds": 10,
  "current_round": 0,
  "estimated_completion": "2025-10-06T14:00:00.000Z"
}
```

### Get Job Status

Get status of federated training job.

**Endpoint**: `GET /federated/jobs/{job_id}`

**Response**:
```json
{
  "job_id": "job_abc123",
  "status": "RUNNING",
  "created_at": "2025-10-06T12:00:00.000Z",
  "model_id": "threat_detector_v2",
  "current_round": 5,
  "total_rounds": 10,
  "progress": 0.50,
  "metrics": {
    "train_loss": 0.25,
    "val_accuracy": 0.92,
    "clients_participated": 2
  }
}
```

---

## Performance API

### Quantize Model

Quantize a model for faster inference.

**Endpoint**: `POST /performance/quantize`

**Request**:
```json
{
  "model_id": "threat_detector_v2",
  "quantization_type": "dynamic",
  "dtype": "int8"
}
```

**Response**:
```json
{
  "quantization_id": "quant_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "original_model_id": "threat_detector_v2",
  "quantized_model_id": "threat_detector_v2_int8",
  "quantization_type": "dynamic",
  "dtype": "int8",
  "size_reduction": 0.75,
  "speedup": 2.5,
  "accuracy_loss": 0.005
}
```

### Benchmark Model

Run latency/throughput benchmark.

**Endpoint**: `POST /performance/benchmark`

**Request**:
```json
{
  "model_id": "threat_detector_v2",
  "num_samples": 1000,
  "batch_sizes": [1, 8, 32]
}
```

**Response**:
```json
{
  "benchmark_id": "bench_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "model_id": "threat_detector_v2",
  "results": [
    {
      "batch_size": 1,
      "latency_p50_ms": 8.5,
      "latency_p95_ms": 15.2,
      "latency_p99_ms": 22.1,
      "throughput_samples_per_sec": 117.6
    },
    {
      "batch_size": 8,
      "latency_p50_ms": 45.0,
      "throughput_samples_per_sec": 177.8
    },
    {
      "batch_size": 32,
      "latency_p50_ms": 150.0,
      "throughput_samples_per_sec": 213.3
    }
  ]
}
```

---

## Training API

### Start Training Job

Start a model training job.

**Endpoint**: `POST /training/jobs`

**Request**:
```json
{
  "model_id": "threat_detector_v3",
  "dataset_id": "threat_dataset_2025",
  "hyperparameters": {
    "learning_rate": 0.001,
    "batch_size": 64,
    "epochs": 10,
    "optimizer": "adam"
  },
  "use_gpu": true,
  "distributed": false
}
```

**Response**:
```json
{
  "job_id": "train_abc123",
  "status": "RUNNING",
  "created_at": "2025-10-06T12:00:00.000Z",
  "model_id": "threat_detector_v3",
  "estimated_completion": "2025-10-06T14:00:00.000Z"
}
```

### Get Training Job Status

**Endpoint**: `GET /training/jobs/{job_id}`

**Response**:
```json
{
  "job_id": "train_abc123",
  "status": "RUNNING",
  "created_at": "2025-10-06T12:00:00.000Z",
  "model_id": "threat_detector_v3",
  "current_epoch": 5,
  "total_epochs": 10,
  "progress": 0.50,
  "metrics": {
    "train_loss": 0.25,
    "train_accuracy": 0.92,
    "val_loss": 0.28,
    "val_accuracy": 0.90
  },
  "gpu_utilization": 0.85
}
```

---

## Autonomic Core API

### Get System Metrics

Get current system metrics from MAPE-K Monitor phase.

**Endpoint**: `GET /autonomic/metrics`

**Response**:
```json
{
  "timestamp": "2025-10-06T12:00:00.000Z",
  "system": {
    "cpu_percent": 65.5,
    "memory_percent": 72.3,
    "disk_io_read_mbps": 12.5,
    "disk_io_write_mbps": 8.2,
    "network_rx_mbps": 25.0,
    "network_tx_mbps": 18.5
  },
  "application": {
    "request_rate_per_sec": 1500,
    "avg_latency_ms": 12.5,
    "error_rate": 0.002,
    "active_connections": 250
  }
}
```

### Execute Action

Execute an autonomic action (MAPE-K Execute phase).

**Endpoint**: `POST /autonomic/actions`

**Request**:
```json
{
  "action": {
    "type": "scale_up",
    "target": "api_gateway",
    "replicas": 5
  },
  "reason": "HIGH_CPU",
  "dry_run": false
}
```

**Response**:
```json
{
  "action_id": "act_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "status": "EXECUTED",
  "action": {...},
  "result": {
    "success": true,
    "message": "Scaled api_gateway from 3 to 5 replicas",
    "execution_time_seconds": 15
  }
}
```

### Get Health Status

Check system health.

**Endpoint**: `GET /autonomic/health`

**Response**:
```json
{
  "status": "HEALTHY",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "components": {
    "api_gateway": "UP",
    "database": "UP",
    "redis": "UP",
    "kafka": "UP",
    "ethics_engine": "UP",
    "xai_engine": "UP"
  },
  "mode": "NORMAL"
}
```

---

## Attention System API

### Calculate Salience

Calculate salience scores for inputs.

**Endpoint**: `POST /attention/salience`

**Request**:
```json
{
  "inputs": [
    {"id": "threat_1", "threat_score": 0.92, "priority": "HIGH"},
    {"id": "threat_2", "threat_score": 0.65, "priority": "MEDIUM"},
    {"id": "alert_1", "type": "system", "severity": "LOW"}
  ]
}
```

**Response**:
```json
{
  "salience_id": "sal_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "scores": [
    {"id": "threat_1", "salience": 0.95},
    {"id": "threat_2", "salience": 0.60},
    {"id": "alert_1", "salience": 0.15}
  ],
  "attention_order": ["threat_1", "threat_2", "alert_1"]
}
```

---

## Neuromodulation API

### Update Neuromodulator Levels

Update dopamine, serotonin, norepinephrine, acetylcholine levels.

**Endpoint**: `POST /neuromodulation/update`

**Request**:
```json
{
  "dopamine": 0.8,
  "serotonin": 0.6,
  "norepinephrine": 0.7,
  "acetylcholine": 0.5,
  "event": "success"
}
```

**Response**:
```json
{
  "neuromod_id": "neuro_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "levels": {
    "dopamine": 0.8,
    "serotonin": 0.6,
    "norepinephrine": 0.7,
    "acetylcholine": 0.5
  },
  "effects": {
    "learning_rate": 0.002,
    "exploration_rate": 0.15,
    "attention_focus": 0.85
  }
}
```

---

## Predictive Coding API

### Generate Prediction

Generate prediction using hierarchical predictive coding network.

**Endpoint**: `POST /predictive-coding/predict`

**Request**:
```json
{
  "layer": "layer3_operational",
  "context": {
    "recent_events": [...],
    "system_state": {...}
  }
}
```

**Response**:
```json
{
  "prediction_id": "pred_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "layer": "layer3_operational",
  "prediction": {
    "next_action": "scale_up",
    "confidence": 0.87,
    "prediction_error": 0.12
  }
}
```

---

## Skill Learning API

### Learn Skill

Learn a new skill from experience.

**Endpoint**: `POST /skill-learning/learn`

**Request**:
```json
{
  "skill_name": "auto_scale_api",
  "experiences": [
    {"state": {...}, "action": "scale_up", "reward": 0.8},
    {"state": {...}, "action": "scale_down", "reward": 0.6}
  ]
}
```

**Response**:
```json
{
  "skill_id": "skill_abc123",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "skill_name": "auto_scale_api",
  "learned": true,
  "performance": 0.85
}
```

---

## Monitoring API

### Get Prometheus Metrics

Get Prometheus-formatted metrics.

**Endpoint**: `GET /metrics`

**Response** (Prometheus format):
```
# HELP predictions_total Total predictions made
# TYPE predictions_total counter
predictions_total{model="threat_detector",result="malware"} 1500

# HELP prediction_latency_seconds Prediction latency
# TYPE prediction_latency_seconds histogram
prediction_latency_seconds_bucket{le="0.01"} 100
prediction_latency_seconds_bucket{le="0.1"} 950
prediction_latency_seconds_bucket{le="1.0"} 1000
```

---

## Webhooks

### Register Webhook

Register a webhook for event notifications.

**Endpoint**: `POST /webhooks`

**Request**:
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["decision.created", "escalation.approved", "training.completed"],
  "secret": "webhook_secret_key"
}
```

**Response**:
```json
{
  "webhook_id": "wh_abc123",
  "url": "https://your-app.com/webhook",
  "events": ["decision.created", "escalation.approved", "training.completed"],
  "created_at": "2025-10-06T12:00:00.000Z",
  "active": true
}
```

### Webhook Payload

When an event occurs, MAXIMUS sends a POST request to your webhook URL:

```json
{
  "event": "decision.created",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "data": {
    "decision_id": "dec_abc123",
    "action": {...},
    "confidence": 0.92
  }
}
```

**Signature Verification**:
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

---

## Server-Sent Events

### Stream System Metrics

Stream real-time system metrics via SSE.

**Endpoint**: `GET /stream/metrics`

**Response** (SSE format):
```
event: metrics
data: {"timestamp": "2025-10-06T12:00:00.000Z", "cpu_percent": 65.5}

event: metrics
data: {"timestamp": "2025-10-06T12:00:01.000Z", "cpu_percent": 66.2}
```

**Example** (JavaScript):
```javascript
const eventSource = new EventSource('https://api.maximus.ai/v1/stream/metrics');

eventSource.addEventListener('metrics', (event) => {
  const metrics = JSON.parse(event.data);
  console.log('CPU:', metrics.cpu_percent);
});
```

**Example** (Python):
```python
import sseclient
import requests

response = requests.get(
    'https://api.maximus.ai/v1/stream/metrics',
    headers={'Authorization': f'Bearer {token}'},
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    if event.event == 'metrics':
        metrics = json.loads(event.data)
        print(f"CPU: {metrics['cpu_percent']}")
```

---

## Summary

MAXIMUS AI 3.0 provides **comprehensive REST APIs** across all 16 modules:

✅ **Ethics API**: Multi-framework ethical evaluation
✅ **XAI API**: LIME, SHAP, counterfactual explanations
✅ **Governance API**: Decision logging, audit trails
✅ **Fairness API**: Bias detection, fairness metrics
✅ **Privacy API**: Differential privacy, privacy budget
✅ **HITL API**: Human escalation, review workflows
✅ **Compliance API**: GDPR, CCPA compliance checks
✅ **Federated Learning API**: Distributed training coordination
✅ **Performance API**: Quantization, benchmarking, profiling
✅ **Training API**: Model training jobs
✅ **Autonomic Core API**: MAPE-K control loop, system health
✅ **Attention System API**: Salience scoring
✅ **Neuromodulation API**: Neuromodulator level updates
✅ **Predictive Coding API**: Hierarchical predictions
✅ **Skill Learning API**: Experience-based learning
✅ **Monitoring API**: Prometheus metrics

**Key Features**:
- **RESTful design** with standard HTTP methods
- **JWT authentication** for all endpoints
- **Rate limiting** (1,000 req/hour authenticated)
- **Pagination** for list endpoints
- **Webhooks** for event notifications
- **Server-Sent Events** for real-time streaming
- **Comprehensive error handling** with detailed error codes
- **REGRA DE OURO 10/10**: Production-ready, no placeholders

---

**Next Steps**: See [README_MASTER.md](./README_MASTER.md) for usage examples and [ARCHITECTURE.md](./ARCHITECTURE.md) for system architecture.
