#!/bin/bash
# Audit specific consciousness modules (excluding certified ones)

MODULES=(
    "api"
    "autobiographical_narrative"
    "biomimetic_safety_bridge"
    "episodic_memory"
    "integration"
    "lrr"
    "mea"
    "metacognition"
    "neuromodulation"
    "predictive_coding"
    "reactive_fabric"
    "sandboxing"
    "system"
    "temporal_binding"
    "validation"
)

echo "MODULE,STATEMENTS,COVERAGE" > /tmp/consciousness_audit.csv

for mod in "${MODULES[@]}"; do
    echo "=== Auditing consciousness/$mod ==="
    PYTHONPATH=. timeout 60 /home/juan/vertice-dev/.venv/bin/python -m pytest \
        --cov=consciousness.$mod \
        --cov-report=json:/tmp/cov_$mod.json \
        --tb=no -q consciousness/ 2>&1 | grep -E "consciousness\.$mod|===|TOTAL" | head -10
    
    if [ -f /tmp/cov_$mod.json ]; then
        statements=$(jq -r '.totals.num_statements // 0' /tmp/cov_$mod.json)
        coverage=$(jq -r '.totals.percent_covered // 0' /tmp/cov_$mod.json)
        echo "$mod,$statements,$coverage" >> /tmp/consciousness_audit.csv
    fi
done

cat /tmp/consciousness_audit.csv | column -t -s,
