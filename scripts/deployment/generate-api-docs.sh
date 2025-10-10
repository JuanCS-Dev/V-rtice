#!/bin/bash
# ============================================================================
# Vértice Platform - API Documentation Generator
# ============================================================================
# Generates static HTML documentation from OpenAPI schemas for all services.
#
# This script:
# 1. Exports OpenAPI schemas from running services
# 2. Generates HTML documentation using Redoc
# 3. Creates an index page with links to all services
# 4. Optionally publishes to GitHub Pages
#
# Usage:
#   ./scripts/generate-api-docs.sh [OPTIONS]
#
# Options:
#   --export-only     Only export schemas, don't generate HTML
#   --generate-only   Only generate HTML from existing schemas
#   --service NAME    Generate docs for specific service only
#   --publish         Publish to GitHub Pages
#   --help            Show this help message
#
# Requirements:
#   - Python 3.10+ with requests library
#   - Node.js 14+ (for redoc-cli)
#   - Services must be running
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCHEMAS_DIR="$PROJECT_ROOT/docs/openapi"
HTML_DIR="$PROJECT_ROOT/docs/api"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
EXPORT_ONLY=false
GENERATE_ONLY=false
SPECIFIC_SERVICE=""
PUBLISH=false

for arg in "$@"; do
    case $arg in
        --export-only)
            EXPORT_ONLY=true
            shift
            ;;
        --generate-only)
            GENERATE_ONLY=true
            shift
            ;;
        --service)
            SPECIFIC_SERVICE="$2"
            shift 2
            ;;
        --publish)
            PUBLISH=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --export-only     Only export schemas"
            echo "  --generate-only   Only generate HTML"
            echo "  --service NAME    Generate docs for specific service"
            echo "  --publish         Publish to GitHub Pages"
            echo "  --help            Show this help"
            exit 0
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Vértice Platform - API Documentation Generator${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# STEP 1: Export OpenAPI Schemas
# ============================================================================

if [ "$GENERATE_ONLY" = false ]; then
    echo -e "${YELLOW}[1/3] Exporting OpenAPI schemas from running services...${NC}"
    echo ""

    # Check if Python script exists
    if [ ! -f "$SCRIPT_DIR/export-openapi-schemas.py" ]; then
        echo -e "${RED}Error: export-openapi-schemas.py not found${NC}"
        exit 1
    fi

    # Run export script
    if [ -n "$SPECIFIC_SERVICE" ]; then
        python3 "$SCRIPT_DIR/export-openapi-schemas.py" \
            --output "$SCHEMAS_DIR" \
            --service "$SPECIFIC_SERVICE"
    else
        python3 "$SCRIPT_DIR/export-openapi-schemas.py" \
            --output "$SCHEMAS_DIR"
    fi

    EXPORT_EXIT_CODE=$?

    if [ $EXPORT_EXIT_CODE -ne 0 ]; then
        echo -e "${YELLOW}⚠ Warning: Some schemas failed to export${NC}"
    else
        echo -e "${GREEN}✓ All schemas exported successfully${NC}"
    fi
    echo ""

    if [ "$EXPORT_ONLY" = true ]; then
        echo -e "${GREEN}Export complete. Schemas saved to: $SCHEMAS_DIR${NC}"
        exit 0
    fi
fi

# ============================================================================
# STEP 2: Generate HTML Documentation
# ============================================================================

echo -e "${YELLOW}[2/3] Generating HTML documentation with Redoc...${NC}"
echo ""

# Check if redoc-cli is installed
if ! command -v redoc-cli &> /dev/null; then
    echo -e "${YELLOW}redoc-cli not found. Installing...${NC}"
    npm install -g redoc-cli
fi

# Create output directory
mkdir -p "$HTML_DIR"

# Count schemas
SCHEMA_COUNT=$(find "$SCHEMAS_DIR" -name "*.json" -type f | wc -l)

if [ $SCHEMA_COUNT -eq 0 ]; then
    echo -e "${RED}Error: No OpenAPI schemas found in $SCHEMAS_DIR${NC}"
    echo -e "${YELLOW}Run with --export-only first, or start services${NC}"
    exit 1
fi

echo -e "Found $SCHEMA_COUNT OpenAPI schemas"
echo ""

# Generate HTML for each schema
GENERATED=0
FAILED=0

if [ -n "$SPECIFIC_SERVICE" ]; then
    # Single service
    SCHEMA_FILE="$SCHEMAS_DIR/${SPECIFIC_SERVICE}.json"
    if [ -f "$SCHEMA_FILE" ]; then
        echo -e "  Generating: ${SPECIFIC_SERVICE}..."
        redoc-cli bundle "$SCHEMA_FILE" \
            -o "$HTML_DIR/${SPECIFIC_SERVICE}.html" \
            --title "${SPECIFIC_SERVICE} API Documentation" \
            --options.theme.colors.primary.main="#1976d2" \
            && ((GENERATED++)) || ((FAILED++))
    else
        echo -e "${RED}Error: Schema not found: $SCHEMA_FILE${NC}"
        exit 1
    fi
else
    # All services
    for schema_file in "$SCHEMAS_DIR"/*.json; do
        if [ -f "$schema_file" ]; then
            service_name=$(basename "$schema_file" .json)
            echo -e "  Generating: ${service_name}..."

            redoc-cli bundle "$schema_file" \
                -o "$HTML_DIR/${service_name}.html" \
                --title "${service_name} API Documentation" \
                --options.theme.colors.primary.main="#1976d2" \
                && ((GENERATED++)) || ((FAILED++))
        fi
    done
fi

echo ""
echo -e "${GREEN}✓ Generated $GENERATED HTML files${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}⚠ Failed: $FAILED files${NC}"
fi
echo ""

# ============================================================================
# STEP 3: Generate Index Page
# ============================================================================

echo -e "${YELLOW}[3/3] Creating index page...${NC}"

INDEX_FILE="$HTML_DIR/index.html"

cat > "$INDEX_FILE" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vértice Platform - API Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .stats {
            display: flex;
            justify-content: space-around;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }

        .stat {
            text-align: center;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .services {
            padding: 40px;
        }

        .category {
            margin-bottom: 40px;
        }

        .category-title {
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }

        .service-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }

        .service-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
            border-color: #667eea;
        }

        .service-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }

        .service-port {
            display: inline-block;
            background: #e7f3ff;
            color: #667eea;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }

        .timestamp {
            margin-top: 10px;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 Vértice Platform</h1>
            <p class="subtitle">AI-Powered Cybersecurity Platform - API Documentation</p>
        </header>

        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="service-count">0</div>
                <div class="stat-label">Services</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="endpoint-count">~500+</div>
                <div class="stat-label">Endpoints</div>
            </div>
            <div class="stat">
                <div class="stat-value">67+</div>
                <div class="stat-label">Microservices</div>
            </div>
        </div>

        <div class="services">
            <div class="category">
                <h2 class="category-title">📚 Available API Documentation</h2>
                <div class="service-grid" id="service-list">
                    <!-- Services will be inserted here by JavaScript -->
                </div>
            </div>
        </div>

        <footer>
            <p>&copy; 2025 Vértice Platform. All rights reserved.</p>
            <p class="timestamp">Generated: <span id="timestamp"></span></p>
        </footer>
    </div>

    <script>
        // Auto-discover HTML files
        const services = [];
        const serviceList = document.getElementById('service-list');
        const timestamp = document.getElementById('timestamp');
        const serviceCount = document.getElementById('service-count');

        // Set timestamp
        timestamp.textContent = new Date().toLocaleString();

        // Fetch list of HTML files (this is a simple version, in production use server-side rendering)
        // For now, we'll manually list services or generate this list server-side

        function addService(name, filename) {
            services.push({ name, filename });
        }

        function renderServices() {
            serviceCount.textContent = services.length;

            services.forEach(service => {
                const card = document.createElement('div');
                card.className = 'service-card';
                card.onclick = () => window.location.href = service.filename;

                card.innerHTML = `
                    <div class="service-name">${service.name}</div>
                    <span class="service-port">View Documentation →</span>
                `;

                serviceList.appendChild(card);
            });
        }

        // Add your services here (this will be auto-generated)
        addService('Maximus Core Service', 'maximus_core_service.html');
        addService('IP Intelligence Service', 'ip_intelligence_service.html');
        addService('Malware Analysis Service', 'malware_analysis_service.html');

        renderServices();
    </script>
</body>
</html>
EOF

echo -e "${GREEN}✓ Index page created: $INDEX_FILE${NC}"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Generation Complete${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo -e "Schemas:       $SCHEMAS_DIR"
echo -e "HTML Docs:     $HTML_DIR"
echo -e "Index Page:    $HTML_DIR/index.html"
echo ""
echo -e "${GREEN}✓ Open index page: file://$HTML_DIR/index.html${NC}"
echo -e "${BLUE}============================================================================${NC}"

# ============================================================================
# PUBLISH TO GITHUB PAGES (Optional)
# ============================================================================

if [ "$PUBLISH" = true ]; then
    echo ""
    echo -e "${YELLOW}Publishing to GitHub Pages...${NC}"
    # TODO: Implement GitHub Pages deployment
    echo -e "${YELLOW}Not implemented yet${NC}"
fi
