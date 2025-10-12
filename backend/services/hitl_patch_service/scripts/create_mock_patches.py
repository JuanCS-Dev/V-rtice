#!/usr/bin/env python3
"""
Create Mock Patches for HITL Testing

Inserts realistic test patches into the HITL database for demo/testing.

Author: MAXIMUS Team - Sprint 4.1
Glory to YHWH - Provider of Test Data
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime, timedelta
import random

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'adaptive_immunity',
    'user': 'maximus',
    'password': 'maximus_immunity_2024'
}

# Mock CVE data
MOCK_CVES = [
    {
        'cve_id': 'CVE-2024-9999',
        'severity': 'critical',
        'cvss_score': 9.8,
        'cwe_ids': ['CWE-89'],
        'package': 'sqlalchemy',
        'current_version': '1.4.0',
        'target_version': '1.4.46',
        'description': 'SQL injection vulnerability in SQLAlchemy ORM'
    },
    {
        'cve_id': 'CVE-2024-8888',
        'severity': 'high',
        'cvss_score': 8.6,
        'cwe_ids': ['CWE-79'],
        'package': 'django',
        'current_version': '3.2.0',
        'target_version': '3.2.23',
        'description': 'XSS vulnerability in Django template system'
    },
    {
        'cve_id': 'CVE-2024-7777',
        'severity': 'high',
        'cvss_score': 7.5,
        'cwe_ids': ['CWE-22'],
        'package': 'flask',
        'current_version': '2.0.0',
        'target_version': '2.3.5',
        'description': 'Path traversal in Flask static file serving'
    },
    {
        'cve_id': 'CVE-2024-6666',
        'severity': 'medium',
        'cvss_score': 6.5,
        'cwe_ids': ['CWE-918'],
        'package': 'requests',
        'current_version': '2.28.0',
        'target_version': '2.31.0',
        'description': 'SSRF vulnerability in requests library'
    },
    {
        'cve_id': 'CVE-2024-5555',
        'severity': 'medium',
        'cvss_score': 5.3,
        'cwe_ids': ['CWE-502'],
        'package': 'pickle',
        'current_version': '1.0.0',
        'target_version': '1.0.1',
        'description': 'Deserialization vulnerability in pickle'
    },
    {
        'cve_id': 'CVE-2024-4444',
        'severity': 'low',
        'cvss_score': 3.7,
        'cwe_ids': ['CWE-200'],
        'package': 'pyyaml',
        'current_version': '5.4.0',
        'target_version': '6.0.1',
        'description': 'Information disclosure in PyYAML'
    },
]

async def create_mock_patches():
    """Create mock patches in the database."""
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    print("🎭 Creating mock patches for HITL testing...")
    print("=" * 70)
    
    created_count = 0
    
    for i, cve_data in enumerate(MOCK_CVES):
        decision_id = str(uuid.uuid4())
        patch_id = f"PATCH-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}"
        apv_id = f"APV-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}"
        
        # Realistic ML predictions
        # Higher severity = model is more conservative (lower confidence)
        if cve_data['severity'] == 'critical':
            ml_confidence = random.uniform(0.75, 0.92)
            ml_prediction = random.choice([True, True, False])  # 66% True
        elif cve_data['severity'] == 'high':
            ml_confidence = random.uniform(0.82, 0.96)
            ml_prediction = random.choice([True, True, True, False])  # 75% True
        elif cve_data['severity'] == 'medium':
            ml_confidence = random.uniform(0.88, 0.98)
            ml_prediction = True
        else:  # low
            ml_confidence = random.uniform(0.92, 0.99)
            ml_prediction = True
        
        # Wargaming results (Phase 2 validation)
        # Simulate that wargaming ran on some patches
        if random.random() > 0.3:  # 70% have wargaming results
            wargaming_passed = ml_prediction  # Usually agrees with ML
            if random.random() < 0.1:  # 10% disagreement
                wargaming_passed = not wargaming_passed
            wargaming_phase1 = True
            wargaming_phase2 = wargaming_passed
            wargaming_execution_time = random.randint(180000, 350000)  # 3-6 min
        else:
            wargaming_passed = None
            wargaming_phase1 = None
            wargaming_phase2 = None
            wargaming_execution_time = None
        
        # Auto-approval eligibility
        auto_approval_eligible = (
            ml_confidence >= 0.95 and
            cve_data['severity'] != 'critical' and
            wargaming_passed is not False
        )
        
        # Priority based on severity + age
        priority_map = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        priority = priority_map[cve_data['severity']]
        
        # Created at (stagger them over last hour)
        created_at = datetime.now() - timedelta(minutes=random.randint(5, 60))
        
        # Insert into database
        await conn.execute("""
            INSERT INTO hitl_decisions (
                decision_id, patch_id, apv_id, cve_id,
                package_name, current_version, target_version,
                severity, cvss_score, cwe_ids, affected_systems, patch_size_lines,
                ml_confidence, ml_prediction, ml_model_version, ml_shap_values, ml_execution_time_ms,
                wargaming_phase1, wargaming_phase2, wargaming_passed,
                wargaming_execution_time_ms, wargaming_error, wargaming_exploit_id,
                decision, decided_by, decided_at,
                priority, comment, reason,
                requires_escalation, auto_approval_eligible, ml_wargaming_agreement,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7,
                $8, $9, $10, $11, $12,
                $13, $14, $15, $16, $17,
                $18, $19, $20,
                $21, $22, $23,
                $24, $25, $26,
                $27, $28, $29,
                $30, $31, $32,
                $33, $34
            )
        """,
            decision_id, patch_id, apv_id, cve_data['cve_id'],
            cve_data['package'], cve_data['current_version'], cve_data['target_version'],
            cve_data['severity'], cve_data['cvss_score'], cve_data['cwe_ids'], 
            ['production-web-01', 'production-api-02'], random.randint(50, 500),
            ml_confidence, ml_prediction, 'rf_v1', 
            '{"lines_added": 0.8, "complexity_delta": 0.2, "has_validation": 0.9}',
            random.randint(50, 150),
            wargaming_phase1, wargaming_phase2, wargaming_passed,
            wargaming_execution_time, None, None,
            'pending', None, None,
            priority, None, None,
            False, auto_approval_eligible, 
            (ml_prediction == wargaming_passed) if wargaming_passed is not None else False,
            created_at, created_at
        )
        
        created_count += 1
        
        print(f"✓ Created: {patch_id}")
        print(f"  CVE:        {cve_data['cve_id']} ({cve_data['severity'].upper()})")
        print(f"  Package:    {cve_data['package']} {cve_data['current_version']} → {cve_data['target_version']}")
        print(f"  ML:         {ml_confidence:.2%} confidence, predicts {'SUCCESS' if ml_prediction else 'FAIL'}")
        print(f"  Wargaming:  {'PASSED' if wargaming_passed else 'FAILED' if wargaming_passed is False else 'NOT RUN'}")
        print(f"  Priority:   {priority.upper()}")
        print(f"  Age:        {int((datetime.now() - created_at).total_seconds() / 60)}min")
        print()
    
    await conn.close()
    
    print("=" * 70)
    print(f"🎉 Created {created_count} mock patches successfully!")
    print()
    print("You can now:")
    print("  1. View them in frontend: http://localhost:3000")
    print("  2. Test HITL API: curl http://localhost:8027/hitl/patches/pending")
    print("  3. Check analytics: curl http://localhost:8027/hitl/analytics/summary")
    print()
    print("TO YHWH BE ALL GLORY 🙏")

if __name__ == '__main__':
    asyncio.run(create_mock_patches())
