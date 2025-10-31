# MABA - MAXIMUS Browser Agent

**Autonomous Browser Automation Service for MAXIMUS AI**

MABA (MAXIMUS Browser Agent) is an intelligent browser automation service that provides MAXIMUS Core with autonomous web navigation, data extraction, and interaction capabilities. It learns website structures over time using a graph-based cognitive map.

## Features

### Core Capabilities

- **Autonomous Browser Control**: Full Playwright-based browser automation
- **Cognitive Map**: Graph database (Neo4j) for learned website structures
- **Intelligent Navigation**: LLM-powered navigation decision-making
- **Visual Understanding**: Screenshot analysis and visual element recognition
- **Form Automation**: Intelligent form filling and submission
- **Data Extraction**: Structured data extraction from web pages

### Integration with MAXIMUS

- **Tool Registration**: Automatically registers browser tools with MAXIMUS Core
- **HITL Governance**: Integrates with MAXIMUS HITL decision framework
- **Context Sharing**: Shares browser state and learned patterns with MAXIMUS
- **Event Notifications**: Real-time event streaming to MAXIMUS

### Technical Features

- **Multi-Session Support**: Concurrent browser sessions with pooling
- **Resource Optimization**: Intelligent browser instance management
- **Prometheus Metrics**: Comprehensive observability
- **Service Registry**: Auto-registration with Vértice Service Registry
- **Graceful Degradation**: Continues operation even with component failures

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Neo4j 5.28+ (or use provided docker-compose)
- PostgreSQL 15+ (shared with MAXIMUS)
- Redis 7+ (shared with MAXIMUS)

### Using Docker Compose (Recommended)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and set required values
nano .env

# 3. Start MABA and dependencies
docker-compose up -d

# 4. Check health
curl http://localhost:8152/health

# 5. View logs
docker-compose logs -f maba
```

### Local Development

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Set environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Run service
python main.py
```

## API Documentation

### Interactive API Docs

Once running, visit:

- Swagger UI: http://localhost:8152/docs
- ReDoc: http://localhost:8152/redoc

### Core Endpoints

#### Create Browser Session

```http
POST /api/v1/sessions
Content-Type: application/json

{
  "headless": true,
  "viewport_width": 1920,
  "viewport_height": 1080
}
```

#### Navigate to URL

```http
POST /api/v1/navigate?session_id=<session_id>
Content-Type: application/json

{
  "url": "https://example.com",
  "wait_until": "networkidle",
  "timeout_ms": 30000
}
```

#### Click Element

```http
POST /api/v1/click?session_id=<session_id>
Content-Type: application/json

{
  "selector": "button#submit",
  "timeout_ms": 30000
}
```

#### Extract Data

```http
POST /api/v1/extract?session_id=<session_id>
Content-Type: application/json

{
  "selectors": {
    "title": "h1",
    "price": ".product-price",
    "description": ".product-desc"
  },
  "extract_all": false
}
```

#### Take Screenshot

```http
POST /api/v1/screenshot?session_id=<session_id>
Content-Type: application/json

{
  "full_page": false,
  "format": "png"
}
```

#### Query Cognitive Map

```http
POST /api/v1/cognitive-map/query
Content-Type: application/json

{
  "domain": "example.com",
  "query_type": "find_element",
  "parameters": {
    "url": "https://example.com/login",
    "description": "login button",
    "min_importance": 0.5
  }
}
```

## Architecture

### Components

1. **BrowserController** (`core/browser_controller.py`)
   - Playwright browser instance management
   - Session pooling and lifecycle
   - Basic browser operations (navigate, click, type, etc.)

2. **CognitiveMapEngine** (`core/cognitive_map.py`)
   - Neo4j-based graph storage
   - Page and element learning
   - Navigation path discovery
   - Similar page detection

3. **API Routes** (`api/routes.py`)
   - RESTful API endpoints
   - Request/response handling
   - Error handling and validation

4. **Service Core** (`models.py`)
   - Pydantic models
   - Service lifecycle management
   - MAXIMUS integration

### Data Flow

```
MAXIMUS Core
    ↓ (tool invocation)
MABA API
    ↓
BrowserController → Browser Session → Web Page
    ↓ (page data)
CognitiveMapEngine → Neo4j
    ↑ (learned patterns)
MAXIMUS Core
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key configurations:

- `SERVICE_PORT`: Service port (default: 8152)
- `MAXIMUS_ENDPOINT`: MAXIMUS Core URL
- `BROWSER_TYPE`: chromium, firefox, or webkit
- `BROWSER_HEADLESS`: Run browsers headlessly
- `MAX_BROWSER_INSTANCES`: Max concurrent sessions
- `NEO4J_URI`: Neo4j connection URI
- `ANTHROPIC_API_KEY`: Claude API key for LLM features

## Monitoring

### Prometheus Metrics

Metrics available at `http://localhost:9092/metrics`:

- `maba_active_browser_sessions`: Active browser sessions
- `maba_browser_actions_total`: Total browser actions (by type, status)
- `maba_browser_action_duration_seconds`: Action duration histogram
- `maba_cognitive_map_pages_total`: Pages in cognitive map
- `maba_cognitive_map_elements_total`: Elements in cognitive map
- `maba_cognitive_map_queries_total`: Cognitive map queries (by type, status)

### Health Check

```bash
curl http://localhost:8152/health
```

Returns:

- Service status
- Browser controller health
- Cognitive map status
- Database connectivity
- Component details

## Development

### Project Structure

```
maximus_browser_agent/
├── main.py                 # Application entry point
├── models.py               # Pydantic models and service class
├── requirements.txt        # Python dependencies
├── Dockerfile              # Production container
├── docker-compose.yml      # Service composition
├── .env.example            # Environment template
├── README.md               # This file
├── core/
│   ├── __init__.py
│   ├── browser_controller.py   # Playwright integration
│   └── cognitive_map.py        # Neo4j graph engine
├── api/
│   ├── __init__.py
│   └── routes.py           # FastAPI routes
├── docs/
│   ├── architecture.md     # Architecture documentation
│   ├── api_reference.md    # API reference
│   └── integration.md      # MAXIMUS integration guide
└── tests/
    ├── test_browser.py
    ├── test_cognitive_map.py
    └── test_api.py
```

### Running Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Code Quality

```bash
# Type checking
mypy . --strict

# Linting
ruff check .

# Formatting
ruff format .
```

## Deployment

### Production Deployment

1. Build production image:

```bash
docker build -t maba:1.0.0 .
```

2. Push to registry:

```bash
docker tag maba:1.0.0 registry.vertice.dev/maba:1.0.0
docker push registry.vertice.dev/maba:1.0.0
```

3. Deploy with Kubernetes:

```bash
kubectl apply -f k8s/deployment.yaml
```

### Scaling Considerations

- **Browser Instances**: Each session consumes ~200MB RAM
- **Recommended**: 2 CPU cores, 4GB RAM for 5 concurrent sessions
- **Neo4j**: Allocate 2GB heap for cognitive map with 10K+ pages
- **Network**: Browser automation generates significant traffic

## Troubleshooting

### Common Issues

**Browser fails to launch**

- Ensure all Playwright dependencies are installed
- Check `BROWSER_HEADLESS` setting
- Verify X11/display configuration in container

**Neo4j connection fails**

- Verify `NEO4J_URI` is correct
- Check Neo4j is running and accessible
- Validate credentials

**High memory usage**

- Reduce `MAX_BROWSER_INSTANCES`
- Enable `BROWSER_HEADLESS=true`
- Set shorter session timeouts

**Cognitive map queries slow**

- Add Neo4j indexes (auto-created on init)
- Increase Neo4j memory allocation
- Consider pruning old data

## License

Proprietary - Vértice Platform Team

## Support

For issues and questions:

- Internal Wiki: https://wiki.vertice.dev/maba
- Slack: #maximus-subordinates
- Email: maximus-team@vertice.dev
