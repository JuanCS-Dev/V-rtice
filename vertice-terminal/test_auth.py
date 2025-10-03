#!/usr/bin/env python3
"""Script de teste para autenticação do Vertice CLI."""

import sys
sys.path.insert(0, '/home/juan/vertice-dev/vertice-terminal')

from vertice.utils.auth import auth_manager

# Simula login direto
user_info = {
    "email": "juan.brainfarma@gmail.com",
    "name": "Juan",
    "picture": "",
    "verified_email": True
}

access_token = "ya29.mock_token_for_juan.brainfarma@gmail.com"

print("🔐 Testando sistema de autenticação...")
print()

# Salva autenticação
auth_manager.save_auth_data(user_info, access_token, expires_in=3600)

print()
print("✅ Autenticação salva com sucesso!")
print()

# Verifica autenticação
if auth_manager.is_authenticated():
    print("✅ Usuário está autenticado")
    user = auth_manager.get_current_user()
    role = auth_manager.get_user_role()

    print(f"   Email: {user.get('email')}")
    print(f"   Role: {role}")
    print(f"   Name: {user.get('name')}")

    # Verifica permissões
    if role == "super_admin":
        print()
        print("👑 SUPER ADMIN DETECTED!")
        print("   ✓ Todas as permissões habilitadas")
else:
    print("❌ Falha na autenticação")
