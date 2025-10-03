#!/usr/bin/env python3
"""Script de teste para logout do Vertice CLI."""

import sys
sys.path.insert(0, '/home/juan/vertice-dev/vertice-terminal')

from vertice.utils.auth import auth_manager

print("🔐 Testando logout...")
print()

# Faz logout
auth_manager.logout()

# Verifica se realmente fez logout
if not auth_manager.is_authenticated():
    print("✅ Logout realizado com sucesso!")
    print("   Usuário não está mais autenticado")
else:
    print("❌ Falha no logout - usuário ainda autenticado")
