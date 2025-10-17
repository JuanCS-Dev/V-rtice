#!/bin/bash

echo "=== VERTICE_API MODULES ==="
echo "client.py exports:"
grep -E "^(class|def|async def) " vertice_api/src/vertice_api/client.py | head -5 | sed 's/^/  /'

echo ""
echo "factory.py exports:"
grep -E "^(class|def|async def) " vertice_api/src/vertice_api/factory.py | head -5 | sed 's/^/  /'

echo ""
echo "=== VERTICE_DB MODULES ==="
echo "connection.py exports:"
grep -E "^(class|def|async def) " vertice_db/src/vertice_db/connection.py | head -5 | sed 's/^/  /'

echo ""
echo "models.py exports:"
grep -E "^(class|def) " vertice_db/src/vertice_db/models.py | head -5 | sed 's/^/  /'

echo ""
echo "repository.py exports:"
grep -E "^(class|def|async def) " vertice_db/src/vertice_db/repository.py | head -5 | sed 's/^/  /'

