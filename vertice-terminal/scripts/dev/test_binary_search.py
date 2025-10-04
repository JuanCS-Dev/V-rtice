#!/usr/bin/env python3
"""Binary search to find problematic command module"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import typer
import importlib

ALL_MODULES = [
    "auth", "context", "ip", "threat", "adr", "malware", "maximus",
    "scan", "monitor", "hunt", "ask", "policy", "detect", "analytics",
    "incident", "compliance", "threat_intel", "dlp", "siem", "menu",
]

def test_modules(modules):
    """Test if a set of modules loads without error"""
    app = typer.Typer(name="vcli", help="Test CLI")

    for module_name in modules:
        module = importlib.import_module(f"vertice.commands.{module_name}")
        app.add_typer(module.app, name=module_name)

    # Try to get the command - this is where the error happens
    from typer.main import get_command
    try:
        cmd = get_command(app)
        return True
    except TypeError as e:
        if "Secondary flag" in str(e):
            return False
        raise

def binary_search():
    """Binary search to find the problematic module"""

    # First test: all modules
    print("Testing all modules...")
    if test_modules(ALL_MODULES):
        print("✅ All modules work - no problem found!")
        return

    print("❌ Problem found in full set. Starting binary search...\n")

    # Test each half
    mid = len(ALL_MODULES) // 2
    first_half = ALL_MODULES[:mid]
    second_half = ALL_MODULES[mid:]

    print(f"Testing first half: {first_half}")
    if not test_modules(first_half):
        print("❌ Problem in first half\n")
        # Continue searching in first half
        for i, mod in enumerate(first_half):
            print(f"Testing {mod}...")
            if not test_modules([mod]):
                print(f"🎯 FOUND PROBLEM MODULE: {mod}")
                return

    print("✅ First half OK\n")

    print(f"Testing second half: {second_half}")
    if not test_modules(second_half):
        print("❌ Problem in second half\n")
        # Continue searching in second half
        for i, mod in enumerate(second_half):
            print(f"Testing {mod}...")
            if not test_modules([mod]):
                print(f"🎯 FOUND PROBLEM MODULE: {mod}")
                return

    print("✅ Second half OK")
    print("\n⚠️  Problem only appears when modules are combined")

if __name__ == "__main__":
    binary_search()
