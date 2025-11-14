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

## Advanced Features

### Cognitive Map Learning

MABA's cognitive map learns website structures automatically, enabling faster and more reliable automation over time.

#### Learning Process

1. **First Visit**: Browser navigates using Claude AI decision-making
2. **Pattern Extraction**: MABA identifies page elements, forms, and navigation paths
3. **Graph Storage**: Patterns stored as nodes/edges in Neo4j
4. **Pattern Matching**: Subsequent visits use learned patterns (70-90% success rate)
5. **Continuous Learning**: Updates patterns when pages change

#### Example: Login Form Learning

```python
# First visit - AI-powered
session_id = await maba.create_session()
await maba.navigate(session_id, "https://example.com/login")
# Claude AI identifies: username field, password field, submit button
await maba.fill_form(session_id, {
    "username": "user@example.com",
    "password": "secret123"
})
await maba.click(session_id, "submit button")

# Subsequent visits - Pattern-based (10x faster)
session_id = await maba.create_session()
await maba.navigate(session_id, "https://example.com/login")
# Cognitive map knows: input[name='email'], input[type='password'], button#login-submit
await maba.fill_form(session_id, {...})  # Direct element access
```

#### Cognitive Map Query Examples

```bash
# Find all login pages learned
curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "find_pages_by_type",
    "parameters": {"page_type": "login"}
  }'

# Find navigation path between pages
curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "find_path",
    "parameters": {
      "from": "https://example.com/",
      "to": "https://example.com/checkout"
    }
  }'

# Find similar pages across domains
curl -X POST https://maba.vertice.ai/api/v1/cognitive-map/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "find_similar_pages",
    "parameters": {
      "reference_url": "https://site-a.com/product/123",
      "min_similarity": 0.75
    }
  }'
```

### Session Management

MABA manages browser sessions with intelligent pooling and lifecycle management.

#### Session Lifecycle

```
[Create Session] → [Active] → [Idle] → [Cleanup]
                       ↓
                  [Navigate]
                  [Interact]
                  [Extract]
```

#### Session Pooling Benefits

- **Reduced Startup Time**: Reuse existing browsers (3-5s → <100ms)
- **Memory Efficiency**: Pool maintains optimal instance count
- **Cost Optimization**: Fewer browser launches = lower CPU usage

#### Advanced Session Configuration

```python
# Create session with custom configuration
session = await maba.create_session({
    "headless": True,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Custom User Agent",
    "locale": "en-US",
    "timezone": "America/New_York",
    "permissions": ["geolocation", "notifications"],
    "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
    "extra_http_headers": {
        "X-Custom-Header": "value"
    },
    "proxy": {
        "server": "http://proxy.example.com:8080",
        "username": "proxyuser",
        "password": "proxypass"
    }
})
```

### Visual Understanding

MABA can analyze screenshots to understand page layout and identify elements.

#### Screenshot Analysis

```python
# Take screenshot
screenshot = await maba.screenshot(session_id, {
    "full_page": True,
    "format": "png",
    "quality": 85
})

# Analyze with Claude Vision
analysis = await maba.analyze_screenshot(session_id, {
    "task": "identify_interactive_elements",
    "filters": ["buttons", "links", "forms"]
})

# Result:
# {
#   "elements": [
#     {"type": "button", "text": "Sign Up", "location": {"x": 100, "y": 200}},
#     {"type": "link", "text": "Forgot Password", "location": {"x": 150, "y": 250}},
#     {"type": "form", "fields": ["email", "password"], "location": {"x": 50, "y": 150}}
#   ]
# }
```

### Form Automation

MABA intelligently fills forms based on field semantics and learned patterns.

#### Intelligent Form Filling

```python
# MABA identifies field types automatically
await maba.fill_form(session_id, {
    "form_data": {
        "email": "user@example.com",
        "password": "secret123",
        "phone": "+1-555-0123",
        "date_of_birth": "1990-01-15",
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        }
    },
    "submit": True,  # Auto-submit after filling
    "validate": True  # Validate fields before submit
})
```

#### Form Field Recognition

MABA uses multiple strategies to identify form fields:

1. **Label Association**: `<label for="email">Email</label>` → `<input id="email">`
2. **Placeholder Text**: `<input placeholder="Enter your email">`
3. **Name Attribute**: `<input name="email">`
4. **ARIA Labels**: `<input aria-label="Email address">`
5. **Visual Analysis**: Claude Vision identifies field purpose from screenshot
6. **Cognitive Map**: Previously learned field mappings

### Data Extraction

Extract structured data from web pages with flexible selectors.

#### Basic Extraction

```python
# Extract with CSS selectors
data = await maba.extract(session_id, {
    "selectors": {
        "title": "h1.product-title",
        "price": "span.price",
        "description": "div.description",
        "images": "img.product-image",  # Returns array
        "availability": "span.stock-status"
    }
})

# Result:
# {
#   "title": "Premium Laptop",
#   "price": "$1,299.99",
#   "description": "High-performance laptop...",
#   "images": ["img1.jpg", "img2.jpg", "img3.jpg"],
#   "availability": "In Stock"
# }
```

#### Advanced Extraction with XPath

```python
# Extract with XPath
data = await maba.extract(session_id, {
    "selectors": {
        "rating": "//div[@class='rating']//span[@class='stars']",
        "reviews": "//div[@id='reviews']//article",
        "seller_info": "//div[contains(@class, 'seller')]//text()"
    },
    "selector_type": "xpath"
})
```

#### Structured Data Extraction

```python
# Extract table data
table_data = await maba.extract_table(session_id, {
    "table_selector": "table#products",
    "headers": True,  # First row is header
    "extract_links": True  # Extract href from cells
})

# Result:
# {
#   "headers": ["Product", "Price", "Quantity", "Total"],
#   "rows": [
#     {"Product": "Item A", "Price": "$10.00", "Quantity": "2", "Total": "$20.00"},
#     {"Product": "Item B", "Price": "$15.00", "Quantity": "1", "Total": "$15.00"}
#   ]
# }
```

### Security and Safety

MABA includes multiple security layers to protect against malicious sites and prevent abuse.

#### Security Policy Configuration

```bash
# Configure security policy
curl -X PUT https://maba.vertice.ai/api/v1/security-policy \
  -H "Content-Type: application/json" \
  -d '{
    "blocked_domains": [
      "*.malicious-site.com",
      "*.phishing-domain.org"
    ],
    "allowed_protocols": ["https", "http"],
    "max_redirects": 5,
    "max_page_size_mb": 50,
    "javascript_enabled": true,
    "allow_downloads": false,
    "allow_popups": false,
    "content_security_policy": "strict"
  }'
```

#### Safety Features

1. **Domain Blocklist**: Prevent navigation to known malicious sites
2. **Protocol Filtering**: Restrict to HTTPS/HTTP only
3. **Redirect Limits**: Prevent redirect loops
4. **Size Limits**: Block excessively large pages
5. **Download Control**: Disable automatic downloads
6. **Popup Blocking**: Block popup windows
7. **CSP Enforcement**: Content Security Policy compliance

### Performance Optimization

MABA includes several performance optimizations for faster automation.

#### Browser Instance Pooling

```bash
# Configure browser pool
export MABA_MIN_BROWSER_INSTANCES=2
export MABA_MAX_BROWSER_INSTANCES=10
export MABA_BROWSER_POOL_WARMUP=true  # Pre-start browsers
export MABA_BROWSER_RECYCLING_ENABLED=true  # Recycle after N uses
export MABA_BROWSER_RECYCLING_THRESHOLD=50  # Recycle after 50 sessions
```

#### Network Optimization

```bash
# Disable unnecessary resources
export MABA_BLOCK_IMAGES=false  # Keep images (needed for vision)
export MABA_BLOCK_FONTS=true  # Block web fonts (30% faster)
export MABA_BLOCK_MEDIA=true  # Block video/audio (50% bandwidth)
export MABA_BLOCK_ADS=true  # Block ad networks (40% faster)
export MABA_BLOCK_TRACKING=true  # Block analytics (20% faster)
```

#### Caching Strategy

```bash
# Enable aggressive caching
export MABA_CACHE_ENABLED=true
export MABA_CACHE_COGNITIVE_MAP=true  # Cache Neo4j queries
export MABA_CACHE_SCREENSHOTS=false  # Don't cache screenshots (large)
export MABA_CACHE_TTL_SECONDS=300  # 5 minutes
```

### Integration Examples

#### MAXIMUS Core Integration

```python
# MAXIMUS Core calls MABA as a tool
tools = [
    {
        "name": "navigate_web",
        "description": "Navigate to a URL and return page content",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "extract_selectors": {"type": "object"}
            }
        }
    }
]

# User query: "Check the price of premium laptops on example.com"
# MAXIMUS decides to use MABA
result = await maximus.use_tool("navigate_web", {
    "url": "https://example.com/laptops/premium",
    "extract_selectors": {
        "products": "div.product",
        "prices": "span.price"
    }
})
```

#### Python SDK Example

```python
from maba_client import MABAClient

# Initialize client
maba = MABAClient(
    base_url="https://maba.vertice.ai",
    api_key="your-api-key"
)

# Create session
session_id = await maba.create_session(headless=True)

try:
    # Navigate
    await maba.navigate(session_id, "https://example.com/login")

    # Fill form
    await maba.fill_form(session_id, {
        "username": "user@example.com",
        "password": "secret123"
    })

    # Click submit
    await maba.click(session_id, "button[type='submit']")

    # Wait for navigation
    await maba.wait_for_navigation(session_id)

    # Extract data
    data = await maba.extract(session_id, {
        "user_name": "span.user-name",
        "balance": "div.account-balance"
    })

    print(f"Logged in as: {data['user_name']}")
    print(f"Balance: {data['balance']}")

finally:
    # Cleanup
    await maba.close_session(session_id)
```

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
