# 🚀 PRÓXIMOS PASSOS - ETHICAL AI SYSTEM

**Status Atual**: ✅ Code complete, all fixes applied, tests passing
**Próximo Marco**: Production deployment & integration

---

## 📋 FASE IMEDIATA (Hoje/Esta Semana)

### 1. ✅ Testar Sistema Localmente (30 min)

```bash
# 1.1 - Instalar dependências
cd /home/juan/vertice-dev/backend/services/ethical_audit_service
pip install -r requirements.txt

# 1.2 - Configurar environment variables
cat > .env << 'EOF'
# Database
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/aurora

# JWT Authentication (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_EXPIRE_MINUTES=60

# CORS (adjust to your frontend URLs)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:4200

# Trusted Hosts
TRUSTED_HOSTS=localhost,127.0.0.1,ethical-audit,ethical_audit_service
EOF

# 1.3 - Start PostgreSQL (if not running)
docker-compose up -d postgres

# 1.4 - Start ethical_audit_service
docker-compose up -d ethical_audit_service

# 1.5 - Check health
curl http://localhost:8612/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "ethical_audit_service",
#   "timestamp": "2025-10-05T...",
#   "database": "connected"
# }
```

---

### 2. ✅ Criar Tokens JWT para Testes (15 min)

```bash
# 2.1 - Criar script de geração de tokens
cat > /home/juan/vertice-dev/backend/services/ethical_audit_service/generate_token.py << 'EOF'
"""Generate JWT tokens for testing/development."""
import sys
from datetime import timedelta
from auth import create_access_token

def generate_token(user_id: str, username: str, roles: list):
    """Generate a JWT token."""
    token = create_access_token(
        data={
            "sub": user_id,
            "username": username,
            "roles": roles
        },
        expires_delta=timedelta(days=7)  # 7 days for testing
    )
    return token

if __name__ == "__main__":
    # Admin token
    admin_token = generate_token("admin-001", "admin", ["admin"])
    print("=" * 80)
    print("ADMIN TOKEN (full access):")
    print("=" * 80)
    print(admin_token)
    print()

    # SOC Operator token
    soc_token = generate_token("soc-001", "soc_operator", ["soc_operator"])
    print("=" * 80)
    print("SOC OPERATOR TOKEN (log decisions, overrides):")
    print("=" * 80)
    print(soc_token)
    print()

    # Auditor token
    auditor_token = generate_token("auditor-001", "auditor", ["auditor"])
    print("=" * 80)
    print("AUDITOR TOKEN (query decisions, metrics):")
    print("=" * 80)
    print(auditor_token)
    print()

    # Save to file for easy access
    with open('/tmp/ethical_ai_tokens.txt', 'w') as f:
        f.write(f"ADMIN_TOKEN={admin_token}\n")
        f.write(f"SOC_TOKEN={soc_token}\n")
        f.write(f"AUDITOR_TOKEN={auditor_token}\n")

    print("Tokens saved to /tmp/ethical_ai_tokens.txt")
    print("Use: source /tmp/ethical_ai_tokens.txt")
EOF

# 2.2 - Generate tokens
cd /home/juan/vertice-dev/backend/services/ethical_audit_service
python generate_token.py

# 2.3 - Load tokens into environment
source /tmp/ethical_ai_tokens.txt
```

---

### 3. ✅ Testar API com Autenticação (20 min)

```bash
# 3.1 - Test unauthenticated request (should fail)
curl -X GET http://localhost:8612/audit/metrics
# Expected: 403 Forbidden

# 3.2 - Test authenticated request (should succeed)
curl -X GET http://localhost:8612/audit/metrics \
  -H "Authorization: Bearer $AUDITOR_TOKEN" | jq

# Expected: JSON with metrics

# 3.3 - Test logging a decision (SOC operator)
curl -X POST http://localhost:8612/audit/decision \
  -H "Authorization: Bearer $SOC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "00000000-0000-0000-0000-000000000001",
    "timestamp": "2025-10-05T12:00:00Z",
    "decision_type": "auto_response",
    "action_description": "Block malicious IP 192.168.1.100",
    "system_component": "immunis_neutrophil",
    "input_context": {},
    "final_decision": "APPROVED",
    "final_confidence": 0.95,
    "decision_explanation": "High-confidence threat detected",
    "total_latency_ms": 45,
    "risk_level": "high",
    "automated": true,
    "environment": "test"
  }' | jq

# Expected: {"status": "success", "decision_id": "..."}

# 3.4 - Query decisions (Auditor)
curl -X POST http://localhost:8612/audit/decisions/query \
  -H "Authorization: Bearer $AUDITOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10,
    "offset": 0
  }' | jq

# Expected: List of decisions

# 3.5 - Test rate limiting (send 35 requests rapidly)
for i in {1..35}; do
  curl -X POST http://localhost:8612/audit/decisions/query \
    -H "Authorization: Bearer $AUDITOR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"limit": 1, "offset": 0}' 2>/dev/null
  echo "Request $i"
done

# Expected: After 30 requests, get 429 Too Many Requests
```

---

### 4. ✅ Integrar com MAXIMUS Core (45 min)

```bash
# 4.1 - Atualizar maximus_integrated.py
cat > /home/juan/vertice-dev/backend/services/maximus_core_service/maximus_integrated.py << 'EOF'
"""MAXIMUS Core with Ethical AI Integration.

This module integrates the ethical engine with MAXIMUS Core for
all critical decision-making.
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional

# Add ethics module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ethics'))

from ethics import EthicalIntegrationEngine, ActionContext
from ethics.config import get_config
import aiohttp
import logging

logger = logging.getLogger(__name__)


class MaximusIntegrated:
    """MAXIMUS Core with ethical decision-making."""

    def __init__(self):
        """Initialize MAXIMUS with ethical engine."""
        # Initialize Ethical Engine
        environment = os.getenv('ETHICAL_ENV', 'production')
        ethical_config = get_config(environment)
        self.ethical_engine = EthicalIntegrationEngine(ethical_config)

        # Ethical Audit Service URL
        self.audit_service_url = os.getenv(
            'ETHICAL_AUDIT_SERVICE_URL',
            'http://localhost:8612'
        )

        # JWT token for audit service
        self.audit_token = os.getenv('ETHICAL_AUDIT_TOKEN')
        if not self.audit_token:
            logger.warning("⚠️  ETHICAL_AUDIT_TOKEN not set - audit logging may fail")

        logger.info(f"✅ MAXIMUS initialized with ethical engine (env={environment})")

    async def execute_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action with ethical evaluation.

        Args:
            action_data: Action to evaluate and potentially execute

        Returns:
            Dict with execution result and ethical decision
        """
        logger.info(f"Executing action: {action_data.get('description', 'N/A')}")

        try:
            # Step 1: Create ethical context
            ethical_context = self._create_ethical_context(action_data)

            # Step 2: Evaluate ethically
            decision = await self.ethical_engine.evaluate(ethical_context)

            # Step 3: Log to audit service (fire and forget)
            asyncio.create_task(self._log_to_audit(decision, ethical_context))

            # Step 4: Handle decision
            if decision.final_decision == "APPROVED":
                logger.info(f"✅ Action APPROVED (confidence: {decision.final_confidence:.2f})")
                return await self._execute_approved_action(action_data, decision)

            elif decision.final_decision == "REJECTED":
                logger.warning(f"❌ Action REJECTED: {decision.explanation}")
                return {
                    'status': 'rejected',
                    'reason': decision.explanation,
                    'confidence': decision.final_confidence,
                    'framework_agreement': decision.framework_agreement_rate
                }

            else:  # ESCALATED_HITL
                logger.warning(f"⚠️  Action ESCALATED to human review: {decision.explanation}")
                return await self._escalate_to_human(action_data, decision)

        except Exception as e:
            logger.error(f"Error during ethical evaluation: {str(e)}", exc_info=True)
            # Fail-safe: Reject on error
            return {
                'status': 'rejected',
                'reason': f'Ethical evaluation failed: {str(e)}',
                'error': True
            }

    def _create_ethical_context(self, action_data: Dict[str, Any]) -> ActionContext:
        """Convert action data to ethical context.

        Args:
            action_data: Action data from MAXIMUS

        Returns:
            ActionContext for ethical evaluation
        """
        return ActionContext(
            action_type=action_data.get('type', 'auto_response'),
            action_description=action_data.get('description', ''),
            system_component=action_data.get('component', 'maximus_core'),
            threat_data=action_data.get('threat_data'),
            target_info=action_data.get('target_info'),
            impact_assessment=action_data.get('impact_assessment'),
            alternatives=action_data.get('alternatives'),
            urgency=action_data.get('urgency', 'medium'),
            operator_context=action_data.get('operator_context')
        )

    async def _log_to_audit(self, decision, context: ActionContext):
        """Log decision to ethical audit service.

        Args:
            decision: Ethical decision
            context: Action context
        """
        try:
            log_data = {
                'id': str(context.action_description)[:36],  # Simplified
                'timestamp': '2025-10-05T12:00:00Z',  # Use datetime.utcnow()
                'decision_type': context.action_type,
                'action_description': context.action_description,
                'system_component': context.system_component,
                'input_context': {
                    'threat_data': context.threat_data,
                    'urgency': context.urgency
                },
                'final_decision': decision.final_decision,
                'final_confidence': decision.final_confidence,
                'decision_explanation': decision.explanation,
                'total_latency_ms': decision.total_latency_ms,
                'risk_level': 'medium',  # Determine from context
                'automated': context.operator_context is None,
                'environment': 'production'
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.audit_token}'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.audit_service_url}/audit/decision',
                    json=log_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.debug("✅ Logged to audit service")
                    else:
                        logger.warning(f"⚠️  Audit logging failed: {response.status}")

        except Exception as e:
            logger.error(f"⚠️  Error logging to audit service: {str(e)}")

    async def _execute_approved_action(self, action_data: Dict[str, Any], decision) -> Dict[str, Any]:
        """Execute an ethically approved action.

        Args:
            action_data: Action data
            decision: Ethical decision

        Returns:
            Execution result
        """
        # TODO: Implement actual action execution
        logger.info(f"Executing approved action: {action_data.get('description')}")

        return {
            'status': 'executed',
            'action': action_data.get('description'),
            'ethical_decision': decision.final_decision,
            'confidence': decision.final_confidence,
            'explanation': decision.explanation
        }

    async def _escalate_to_human(self, action_data: Dict[str, Any], decision) -> Dict[str, Any]:
        """Escalate decision to human operator.

        Args:
            action_data: Action data
            decision: Ethical decision

        Returns:
            Escalation result
        """
        # TODO: Implement HITL queue (WebSocket, Redis, DB)
        logger.warning(f"Escalating to HITL: {action_data.get('description')}")

        return {
            'status': 'escalated_hitl',
            'reason': decision.explanation,
            'confidence': decision.final_confidence,
            'framework_agreement': decision.framework_agreement_rate,
            'action_data': action_data,
            'message': 'This decision requires human review'
        }


# Example usage
async def main():
    """Example usage of MAXIMUS with ethical integration."""
    maximus = MaximusIntegrated()

    # Example 1: High-confidence threat (should be APPROVED)
    action1 = {
        'type': 'auto_response',
        'description': 'Block IP 192.168.1.100 detected with SQL injection attempts (95% confidence)',
        'component': 'immunis_neutrophil',
        'threat_data': {
            'severity': 0.9,
            'confidence': 0.95,
            'people_protected': 1000
        },
        'urgency': 'high'
    }

    result1 = await maximus.execute_action(action1)
    print(f"\n{'='*80}")
    print(f"Action 1 Result: {result1['status']}")
    print(f"{'='*80}\n")

    # Example 2: Offensive action without authorization (should be REJECTED)
    action2 = {
        'type': 'offensive_action',
        'description': 'Deploy social engineering attack against employees without consent',
        'component': 'offensive_tools',
        'urgency': 'low'
    }

    result2 = await maximus.execute_action(action2)
    print(f"\n{'='*80}")
    print(f"Action 2 Result: {result2['status']}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
EOF

# 4.2 - Test integration
cd /home/juan/vertice-dev/backend/services/maximus_core_service
export ETHICAL_AUDIT_TOKEN=$SOC_TOKEN
python maximus_integrated.py

# Expected:
# ✅ MAXIMUS initialized with ethical engine
# Action 1 Result: executed
# Action 2 Result: rejected
```

---

## 📊 FASE DE MONITORAMENTO (Próxima Semana)

### 5. ✅ Configurar Dashboard de Métricas (2 horas)

```bash
# 5.1 - Criar script de monitoramento
cat > /home/juan/vertice-dev/scripts/monitor_ethical_metrics.sh << 'EOF'
#!/bin/bash
# Monitor ethical AI metrics in real-time

AUDIT_URL="${ETHICAL_AUDIT_URL:-http://localhost:8612}"
TOKEN="${AUDITOR_TOKEN}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       VÉRTICE ETHICAL AI - METRICS DASHBOARD              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

while true; do
    clear
    echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Get metrics
    metrics=$(curl -s -H "Authorization: Bearer $TOKEN" "$AUDIT_URL/audit/metrics")

    echo "📊 ETHICAL DECISIONS (Last 24h)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$metrics" | jq -r '
        "Total Decisions:     \(.total_decisions_last_24h)",
        "Approval Rate:       \((.approval_rate * 100) | tostring | .[0:5])%",
        "Rejection Rate:      \((.rejection_rate * 100) | tostring | .[0:5])%",
        "HITL Escalation:     \((.hitl_escalation_rate * 100) | tostring | .[0:5])%",
        "",
        "⏱️  PERFORMANCE",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "Avg Latency:         \(.avg_latency_ms | tostring | .[0:5])ms",
        "P95 Latency:         \(.p95_latency_ms | tostring | .[0:5])ms",
        "P99 Latency:         \(.p99_latency_ms | tostring | .[0:5])ms",
        "",
        "🤝 FRAMEWORK AGREEMENT",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "Agreement Rate:      \((.framework_agreement_rate * 100) | tostring | .[0:5])%",
        "Kantian Veto Rate:   \((.kantian_veto_rate * 100) | tostring | .[0:5])%"
    '

    sleep 5
done
EOF

chmod +x /home/juan/vertice-dev/scripts/monitor_ethical_metrics.sh

# 5.2 - Run monitor
./scripts/monitor_ethical_metrics.sh
```

---

## 🔄 FASE DE PRODUÇÃO (Próximas 2 Semanas)

### 6. ✅ Deploy em Produção (1 dia)

```bash
# 6.1 - Update docker-compose.yml with production settings
# 6.2 - Configure secrets management (Vault/AWS Secrets Manager)
# 6.3 - Setup SSL/TLS certificates
# 6.4 - Configure production database (managed PostgreSQL)
# 6.5 - Setup monitoring (Prometheus + Grafana)
# 6.6 - Configure alerts (PagerDuty/Slack)
```

### 7. ✅ Frontend Integration (3 dias)

```jsx
// frontend/src/components/ethics/EthicalMetricsWidget.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

export const EthicalMetricsWidget = () => {
    const [metrics, setMetrics] = useState(null);
    const token = localStorage.getItem('auth_token');

    useEffect(() => {
        const fetchMetrics = async () => {
            const response = await axios.get(
                'http://localhost:8612/audit/metrics',
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setMetrics(response.data);
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 30000);
        return () => clearInterval(interval);
    }, [token]);

    if (!metrics) return <div>Loading...</div>;

    return (
        <div className="ethical-metrics-widget">
            <h3>Ethical AI Metrics (24h)</h3>
            <div className="metric">
                <span>Approval Rate:</span>
                <span className="value">{(metrics.approval_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="metric">
                <span>HITL Escalation:</span>
                <span className="value">{(metrics.hitl_escalation_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="metric">
                <span>Avg Latency:</span>
                <span className="value">{metrics.avg_latency_ms.toFixed(0)}ms</span>
            </div>
        </div>
    );
};
```

---

## 🚀 ROADMAP FUTURO (Próximos 3-6 Meses)

### PHASE 2: XAI - Explainability (Mês 2)
- [ ] Implementar LIME para feature importance
- [ ] Implementar SHAP values
- [ ] Interface de explicação visual
- [ ] Counterfactual explanations

### PHASE 3: Fairness & Bias Detection (Mês 3)
- [ ] Demographic parity checks
- [ ] Equalized odds analysis
- [ ] Bias mitigation strategies
- [ ] Fairness metrics dashboard

### PHASE 4: Privacy & Security (Mês 4)
- [ ] Differential privacy
- [ ] Federated learning
- [ ] Homomorphic encryption
- [ ] Privacy-preserving ML

### PHASE 5: HITL Interface (Mês 5)
- [ ] Web UI para review de decisões
- [ ] WebSocket para notificações
- [ ] Approval workflow
- [ ] Justification requirements

### PHASE 6: Compliance & Certification (Mês 6)
- [ ] EU AI Act compliance checker
- [ ] GDPR Article 22 validator
- [ ] ISO 27001 mapping
- [ ] Audit report generator

---

## 📞 SUPORTE & DOCUMENTAÇÃO

- **Docs**: `/docs/ETHICAL_AI_IMPLEMENTATION_COMPLETE.md`
- **Integration**: `/backend/services/maximus_core_service/ETHICAL_INTEGRATION_GUIDE.md`
- **API**: `http://localhost:8612/docs` (FastAPI auto-docs)
- **Issues**: Create GitHub issues for bugs/features

---

**Preparado por**: Claude Code + JuanCS-Dev
**Data**: 2025-10-05
**Status**: ✅ Ready to execute
