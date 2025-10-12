"""
Abstract base parser for forensic captures.

Defines the interface all parsers must implement.
Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class ForensicParser(ABC):
    """
    Abstract base parser for forensic captures.
    
    All parsers must implement parse() and supports() methods.
    Extracts structured data from honeypot logs, PCAPs, etc.
    
    Returns standardized format:
    {
        "attacker_ip": str,
        "attack_type": str,
        "commands": List[str],
        "credentials": List[tuple],  # [(username, password), ...]
        "file_hashes": List[str],
        "timestamps": List[datetime],
        "sessions": List[dict]
    }
    """
    
    @abstractmethod
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse forensic capture and extract structured data.
        
        Args:
            file_path: Path to forensic capture file
        
        Returns:
            Dict with structured attack data:
            {
                "attacker_ip": str | None,
                "attack_type": str,
                "commands": List[str],
                "credentials": List[tuple],
                "file_hashes": List[str],
                "timestamps": List[datetime],
                "sessions": List[dict],
                "metadata": Dict[str, Any]
            }
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ParserError: If parsing fails
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """
        Check if this parser supports the given file.
        
        Args:
            file_path: Path to check
        
        Returns:
            True if parser can handle this file type
        """
        pass
    
    def _determine_attack_type(self, data: Dict[str, Any]) -> str:
        """
        Determine attack type based on parsed data.
        
        Override in subclasses for specific logic.
        
        Args:
            data: Parsed data dictionary
        
        Returns:
            Attack type string (e.g., "ssh_brute_force", "web_exploit")
        """
        return "unknown"
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract file metadata (size, hash, etc).
        
        Args:
            file_path: Path to file
        
        Returns:
            Dict with metadata
        """
        import hashlib
        
        stat = file_path.stat()
        
        # Calculate SHA256
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return {
            "filename": file_path.name,
            "file_size_bytes": stat.st_size,
            "file_hash": sha256.hexdigest(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime)
        }


class ParserError(Exception):
    """Exception raised when parsing fails."""
    pass
