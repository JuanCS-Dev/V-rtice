#!/bin/bash
echo "=== TRACK 1 VALIDATION ==="
echo ""

# Validar vertice_core
echo "📦 VERTICE_CORE"
cd vertice_core
echo "  Modules:"
ls -1 src/vertice_core/*.py | grep -v __init__ | grep -v __pycache__ | sed 's/^/    - /'
echo "  TODOs/FIXMEs:"
grep -r "TODO\|FIXME\|XXX" src/ 2>/dev/null | wc -l | xargs -I {} echo "    Found: {}"
cd ..
echo ""

# Validar vertice_api  
echo "📦 VERTICE_API"
cd vertice_api
echo "  Modules:"
ls -1 src/vertice_api/*.py | grep -v __init__ | grep -v __pycache__ | sed 's/^/    - /'
echo "  Missing (per plan):"
for mod in dependencies.py versioning.py; do
  if [ ! -f "src/vertice_api/$mod" ]; then
    echo "    ❌ $mod"
  fi
done
echo "  TODOs/FIXMEs:"
grep -r "TODO\|FIXME\|XXX" src/ 2>/dev/null | wc -l | xargs -I {} echo "    Found: {}"
cd ..
echo ""

# Validar vertice_db
echo "📦 VERTICE_DB"
cd vertice_db
echo "  Modules:"
ls -1 src/vertice_db/*.py | grep -v __init__ | grep -v __pycache__ | sed 's/^/    - /'
echo "  Missing (per plan):"
for mod in session.py base.py; do
  if [ ! -f "src/vertice_db/$mod" ]; then
    echo "    ❌ $mod"
  fi
done
echo "  TODOs/FIXMEs:"
grep -r "TODO\|FIXME\|XXX" src/ 2>/dev/null | wc -l | xargs -I {} echo "    Found: {}"
cd ..

