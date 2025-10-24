#!/bin/bash
# Fix terminal after neuroshell crash/exit
# Usage: source fix_terminal.sh  OR  . fix_terminal.sh

echo "🔧 Fixing terminal state..."

# Disable mouse tracking
printf '\033[?1000l'  # Disable X10 mouse tracking
printf '\033[?1002l'  # Disable cell motion mouse tracking
printf '\033[?1003l'  # Disable all motion mouse tracking
printf '\033[?1006l'  # Disable SGR mouse mode

# Reset terminal to sane state
stty sane
reset

# Clear screen
clear

echo "✅ Terminal fixed! You can type normally now."
