# Scripting Guide

## Bash Integration

```bash
#!/bin/bash
# bulk_ip_analysis.sh

# Lê IPs de um arquivo
while read ip; do
  echo "Analyzing $ip..."

  # Analisa e salva JSON
  vertice ip analyze "$ip" --json > "results/${ip}.json"

  # Se threat score > 70, alerta
  score=$(jq '.reputation.score' "results/${ip}.json")
  if [ "$score" -gt 70 ]; then
    echo "⚠️  ALERT: $ip has threat score $score"

    # Adiciona ao ADR
    vertice adr analyze network --ip "$ip"
  fi
done < ips.txt
```

## Python Integration

```python
import subprocess
import json

result = subprocess.run(
    ['vertice', 'ip', 'analyze', '8.8.8.8', '--json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(data)
```

---

See WORKFLOWS.md for common use cases.