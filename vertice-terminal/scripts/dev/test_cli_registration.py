#!/usr/bin/env python3
"""Test CLI registration to find the problematic module"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import typer
import importlib

COMMAND_MODULES = [
    "auth", "context", "ip", "threat", "adr", "malware", "maximus",
    "scan", "monitor", "hunt", "ask", "policy", "detect", "analytics",
    "incident", "compliance", "threat_intel", "dlp", "siem", "menu",
]

app = typer.Typer(name="vcli", help="Test CLI")

for module_name in COMMAND_MODULES:
    try:
        print(f"Registering {module_name}...", end=" ")
        module = importlib.import_module(f"vertice.commands.{module_name}")
        app.add_typer(module.app, name=module_name)
        print("✅")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        break

print("\nTrying to call app()...")
try:
    app()
except Exception as e:
    print(f"❌ ERROR calling app(): {e}")
    import traceback
    traceback.print_exc()
