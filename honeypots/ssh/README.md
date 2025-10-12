# Honeypot SSH (Cowrie)
## Sprint 0: Placeholder

**Status**: Sprint 2 Implementation

This directory will contain Cowrie configuration for SSH honeypot.

**Cowrie**: Medium-interaction SSH/Telnet honeypot
- GitHub: https://github.com/cowrie/cowrie
- Docker: cowrie/cowrie:latest

**Sprint 2 Tasks**:
- [ ] Configure cowrie.cfg
- [ ] Setup fake file system
- [ ] Configure fake users/passwords (root:123456, admin:admin)
- [ ] Setup JSON output to /forensics/
- [ ] Test with Hydra brute force
- [ ] Validate capture in analysis service

**Configuration Preview**:
```ini
[honeypot]
hostname = ubuntu-server-01
fake_addr = 192.168.1.100
backend = shell

[output_jsonlog]
enabled = true
logfile = /forensics/cowrie-%(sensorname)s-%(date)s.json
```

**References**:
- Cowrie Docs: https://cowrie.readthedocs.io
- MAXIMUS Integration: See `reactive-fabric-integration-analysis.md`
