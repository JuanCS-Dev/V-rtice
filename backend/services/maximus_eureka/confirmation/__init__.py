"""
Vulnerability Confirmation Module - MAXIMUS Eureka.

Confirms presence of vulnerabilities in codebase using AST analysis.
Reduces false positives before initiating remediation strategies.

Philosophical Foundation:
    Confirmation phase embodies epistemic rigor - we do not presume vulnerability
    from metadata alone. Like scientific method demands replication, we demand
    code-level evidence before committing remediation resources.

    ast-grep provides syntactic pattern matching that confirms vulnerable code
    patterns exist in specified locations, bridging CVE abstract descriptions
    to concrete code instances.
"""

from confirmation.ast_grep_engine import ASTGrepEngine, ASTGrepMatch
from confirmation.vulnerability_confirmer import (
    VulnerabilityConfirmer,
    ConfirmationConfig,
)

__all__ = [
    "ASTGrepEngine",
    "ASTGrepMatch",
    "VulnerabilityConfirmer",
    "ConfirmationConfig",
]
