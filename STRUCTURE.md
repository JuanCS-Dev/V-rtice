# 📂 Vértice Repository Structure

## Root Directory (Production-Ready)

```
vertice-dev/
├── 📁 backend/              # Core microservices
├── 📁 consciousness/        # MAXIMUS cognitive layer
├── 📁 deployment/           # Infrastructure as Code
│   ├── compose/            # Docker Compose files
│   ├── scripts/            # Control scripts
│   ├── validation/         # System validation
│   └── configs/            # Configuration files
├── 📁 docs/                # Complete documentation
│   ├── 00-VISAO-GERAL/    # Overview & posters
│   ├── 01-ARCHITECTURE/   # Architecture docs
│   ├── 02-BACKEND/        # Backend documentation
│   ├── 03-FRONTEND/       # Frontend documentation
│   ├── 04-VCLI/           # CLI documentation
│   ├── 05-MAXIMUS-AI/     # AI system docs
│   ├── 06-DEPLOYMENT/     # Deployment guides
│   ├── 07-RELATORIOS/     # Development reports
│   ├── 08-REPORTS/        # Status reports
│   ├── 09-ROADMAPS/       # Product roadmaps
│   └── 99-ARTIFACTS/      # Generated artifacts
├── 📁 frontend/            # Cockpit UI & dashboards
├── 📁 honeypots/           # Security honeypots
├── 📁 k8s/                 # Kubernetes manifests
├── 📁 models/              # AI/ML models
├── 📁 monitoring/          # Observability stack
├── 📁 scripts/             # Utility scripts
├── 📁 tests/               # Test suites
├── 📁 tools/               # Development tools
├── 📁 vcli-go/             # Go-based CLI
├── 📁 vertice_cli/         # Python CLI
├── 📁 vertice-terminal/    # Terminal UI
├── 📄 docker-compose.yml   # Main compose file
├── 📄 pyproject.toml       # Python project config
├── 📄 requirements.txt     # Python dependencies
├── 📄 README.md            # Project overview
├── 📄 LICENSE              # License file
└── �� .gitignore           # Git ignore rules
```

## Hidden/Archive Directories (Not Versioned)

```
.archive/
├── backups/               # Old compose backups
├── logs/                  # Runtime logs
└── runtime-logs/          # System logs

data/                      # Docker volumes
├── postgres/
├── redis/
└── vault/
```

## Key Files

- **docker-compose.yml**: Main orchestration
- **pyproject.toml**: Python project configuration
- **requirements.txt**: Production dependencies
- **requirements-dev.txt**: Development dependencies
- **.gitignore**: Comprehensive ignore rules
- **LICENSE**: Project license

## Documentation Structure

All documentation is organized in `/docs/` with numbered prefixes for easy navigation:

- **00-VISAO-GERAL**: High-level overview and architecture posters
- **01-ARCHITECTURE**: Detailed architecture documentation
- **02-06**: Service-specific documentation
- **07-08**: Reports and status tracking
- **09**: Roadmaps and planning
- **99**: Archives and generated artifacts

## Deployment Structure

All deployment-related files are in `/deployment/`:

- **compose/**: All docker-compose variants (sidecars, services, infrastructure)
- **scripts/**: Control scripts (maximus_control.sh, vault scripts)
- **validation/**: System validation and testing scripts
- **configs/**: Standalone config files (prometheus, redis, vault)

---

**Last updated**: 2025-10-25
**Version**: 2.0 (Public-ready)
