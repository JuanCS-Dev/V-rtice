# 🎯 Vertice CLI Terminal

**AI-Powered Cybersecurity Command Line Interface**

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install CLI
pip install -e .

# Verify installation
vertice --version
```

## Quick Start

```bash
# Display help
vertice --help

# Analyze IP
vertice ip analyze 8.8.8.8

# Threat lookup
vertice threat lookup malicious.com

# Aurora AI query
vertice aurora ask "What are the latest threats?"

# Network scan
vertice scan ports example.com

# Start monitoring
vertice monitor threats
```

## Documentation

See `docs/` directory for detailed documentation:

- `COMMANDS.md` - Complete command reference
- `WORKFLOWS.md` - Common workflows
- `SCRIPTING.md` - Scripting guide

## Configuration

Configuration file: `~/.vertice/config.yaml`

Service endpoints: `vertice/config/services.yaml`

## Architecture

- **Commands**: High-level user commands
- **Connectors**: Backend service integrations
- **Utils**: Shared utilities (output, config, cache)
- **Tests**: Unit and integration tests

## Development

```bash
# Run tests
pytest

# Run with debug
vertice --verbose ip analyze 1.2.3.4

# Clear cache
rm -rf ~/.vertice/cache
```

## License

Proprietary - Vertice Platform