# Common Workflows

## Incident Response

```bash
# 1. Analisa IP
vertice ip analyze 185.220.101.23

# 2. Verifica threat intel
vertice threat check 185.220.101.23

# 3. Se malicioso, adiciona ao ADR para monitoramento
vertice adr analyze network --ip 185.220.101.23

# 4. Pergunta para Maximus
vertice maximus ask "What is the reputation of 185.220.101.23?"
```

## Malware Analysis

```bash
# 1. Análise estática
vertice malware analyze /tmp/suspicious.exe

# 2. Se suspeito, análise dinâmica (sandbox)
# vertice malware dynamic /tmp/suspicious.exe # Not implemented yet

# 3. YARA scan
vertice malware yara /tmp/suspicious.exe

# 4. Consulta Maximus para contexto
vertice maximus investigate malware --file /tmp/suspicious.exe # Not implemented yet
```

## Threat Hunting

```bash
# 1. Busca por IOC
vertice hunt search "185.220.101.23"

# 2. Timeline de atividade
vertice hunt timeline --ioc "185.220.101.23" --last 24h

# 3. Pivot para IPs relacionados
vertice hunt pivot "185.220.101.23"

# 4. Correlação com outros IOCs
# vertice hunt correlate "185.220.101.23" "malware_hash_123" # Not implemented yet
```

---

See COMMANDS.md for all available commands.