#!/bin/bash
# Setup and run Testcontainers environment
# Author: Claude Code + JuanCS-Dev
# Date: 2025-10-20

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MAXIMUS Test Environment Setup ===${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  docker-compose not found, using 'docker compose' instead${NC}"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${GREEN}📁 Working directory: $PROJECT_ROOT${NC}"

# Parse arguments
COMMAND=${1:-up}

case $COMMAND in
    up)
        echo -e "${GREEN}🚀 Starting test containers...${NC}"
        $COMPOSE_CMD -f docker-compose.test.yml up -d

        echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
        sleep 5

        # Check health
        echo -e "${GREEN}🔍 Checking service health...${NC}"
        $COMPOSE_CMD -f docker-compose.test.yml ps

        echo -e "${GREEN}✅ Test environment ready!${NC}"
        echo ""
        echo "📊 Service Endpoints:"
        echo "   Kafka:      localhost:29092"
        echo "   Zookeeper:  localhost:2181"
        echo "   Redis:      localhost:6379"
        echo "   PostgreSQL: localhost:5432"
        echo "   MinIO:      localhost:9000 (console: 9001)"
        echo "   Prometheus: localhost:9090"
        echo ""
        echo "🧪 Run tests with:"
        echo "   pytest tests/ -v"
        echo "   pytest tests/ -v --cov"
        echo ""
        ;;

    down)
        echo -e "${YELLOW}🛑 Stopping test containers...${NC}"
        $COMPOSE_CMD -f docker-compose.test.yml down
        echo -e "${GREEN}✅ Containers stopped${NC}"
        ;;

    clean)
        echo -e "${YELLOW}🧹 Cleaning test environment (including volumes)...${NC}"
        $COMPOSE_CMD -f docker-compose.test.yml down -v
        echo -e "${GREEN}✅ Environment cleaned${NC}"
        ;;

    restart)
        echo -e "${YELLOW}🔄 Restarting test containers...${NC}"
        $COMPOSE_CMD -f docker-compose.test.yml restart
        echo -e "${GREEN}✅ Containers restarted${NC}"
        ;;

    logs)
        SERVICE=${2:-}
        if [ -z "$SERVICE" ]; then
            $COMPOSE_CMD -f docker-compose.test.yml logs --tail=100 -f
        else
            $COMPOSE_CMD -f docker-compose.test.yml logs --tail=100 -f "$SERVICE"
        fi
        ;;

    ps)
        $COMPOSE_CMD -f docker-compose.test.yml ps
        ;;

    exec)
        SERVICE=${2:-kafka}
        EXEC_CMD=${3:-/bin/bash}
        echo -e "${GREEN}🔧 Executing in $SERVICE: $EXEC_CMD${NC}"
        $COMPOSE_CMD -f docker-compose.test.yml exec "$SERVICE" $EXEC_CMD
        ;;

    test)
        echo -e "${GREEN}🧪 Running full test suite with Testcontainers...${NC}"

        # Ensure containers are up
        $0 up

        # Run tests
        echo -e "${YELLOW}⏳ Running pytest...${NC}"
        pytest tests/ -v --cov --cov-report=html:htmlcov --cov-report=term-missing

        # Generate coverage report
        echo -e "${GREEN}📊 Generating coverage report...${NC}"
        python scripts/coverage_report.py --current htmlcov --modules --badge coverage-badge.md

        echo -e "${GREEN}✅ Tests complete!${NC}"
        ;;

    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  up        Start test containers (default)"
        echo "  down      Stop test containers"
        echo "  clean     Stop and remove containers + volumes"
        echo "  restart   Restart containers"
        echo "  logs      View logs (optionally specify service)"
        echo "  ps        Show container status"
        echo "  exec      Execute command in container (default: kafka bash)"
        echo "  test      Run full test suite with coverage"
        echo ""
        echo "Examples:"
        echo "  $0 up"
        echo "  $0 logs kafka"
        echo "  $0 exec redis redis-cli"
        echo "  $0 test"
        exit 1
        ;;
esac
