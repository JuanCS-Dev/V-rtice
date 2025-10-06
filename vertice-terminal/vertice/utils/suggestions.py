"""
Suggestion engine for vCLI - "Did you mean?" functionality.

Provides intelligent command suggestions when users make typos.
"""

from difflib import get_close_matches
from typing import List, Optional


# All vCLI commands (updated from cli.py)
VCLI_COMMANDS = [
    "auth", "context", "ip", "threat", "adr", "malware", "maximus",
    "scan", "monitor", "hunt", "ask", "policy", "detect", "analytics",
    "incident", "compliance", "threat_intel", "dlp", "siem", "investigate",
    "osint", "cognitive", "offensive", "immunis", "distributed", "hcl",
    "memory", "menu", "project", "plugin", "script", "tui", "shell", "help"
]


def suggest_command(typo: str, commands: List[str] = None, max_suggestions: int = 3) -> List[str]:
    """
    Suggest similar commands based on a typo.

    Args:
        typo: The mistyped command
        commands: List of valid commands (defaults to VCLI_COMMANDS)
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of suggested commands, ordered by similarity
    """
    if commands is None:
        commands = VCLI_COMMANDS

    # Use difflib to find close matches
    # cutoff=0.6 means 60% similarity required
    suggestions = get_close_matches(
        typo.lower(),
        commands,
        n=max_suggestions,
        cutoff=0.6
    )

    return suggestions


def format_suggestion_message(typo: str, suggestions: List[str]) -> str:
    """
    Format a friendly suggestion message.

    Args:
        typo: The command that was not found
        suggestions: List of suggested commands

    Returns:
        Formatted message string
    """
    if not suggestions:
        return f"Command '{typo}' not found. Try: vcli --help"

    if len(suggestions) == 1:
        return f"Command '{typo}' not found.\n\n💡 Did you mean: {suggestions[0]}?"

    suggestions_list = "\n".join(f"  • {cmd}" for cmd in suggestions)
    return f"Command '{typo}' not found.\n\n💡 Did you mean one of these?\n{suggestions_list}"


def get_command_suggestion(typo: str) -> Optional[str]:
    """
    Get formatted suggestion message for a typo.

    Args:
        typo: The mistyped command

    Returns:
        Formatted suggestion message or None if no suggestions
    """
    suggestions = suggest_command(typo)

    if not suggestions:
        return None

    return format_suggestion_message(typo, suggestions)


# Common typo mappings (manually curated for frequent mistakes)
COMMON_TYPOS = {
    "mallware": "malware",
    "mallicious": "malware",
    "analize": "analytics",
    "analitics": "analytics",
    "maximu": "maximus",
    "maximous": "maximus",
    "invesigate": "investigate",
    "investigat": "investigate",
    "ofensive": "offensive",
    "offencive": "offensive",
    "trheat": "threat",
    "thret": "threat",
    "scann": "scan",
    "hunts": "hunt",
    "monitr": "monitor",
    "memmory": "memory",
    "proyect": "project",
    "projct": "project",
}


def get_direct_correction(typo: str) -> Optional[str]:
    """
    Check if typo has a known direct correction.

    Args:
        typo: The mistyped command

    Returns:
        Direct correction if available, None otherwise
    """
    return COMMON_TYPOS.get(typo.lower())


def suggest_with_correction(typo: str) -> str:
    """
    Get suggestion with direct correction if available, otherwise use fuzzy matching.

    Args:
        typo: The mistyped command

    Returns:
        Formatted suggestion message
    """
    # Try direct correction first
    direct = get_direct_correction(typo)
    if direct:
        return f"Command '{typo}' not found.\n\n💡 Did you mean: {direct}? (common typo)"

    # Fall back to fuzzy matching
    suggestion_msg = get_command_suggestion(typo)
    if suggestion_msg:
        return suggestion_msg

    # No suggestions found
    return f"Command '{typo}' not found.\n\nTry: vcli --help to see all available commands."
