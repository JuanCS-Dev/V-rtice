"""
Few-Shot Database - Vulnerability Fix Examples for LLM Learning.

SQLite database containing curated examples of vulnerability fixes for
few-shot learning in Code Patch LLM Strategy.

Theoretical Foundation:
    Few-shot learning dramatically improves LLM patch generation accuracy.
    Brown et al. (2020) showed GPT-3 achieves near-SOTA with 10-100 examples.
    
    Our database provides:
    - Vulnerable code patterns (pre-fix)
    - Fixed code patterns (post-fix)
    - Explanation (why vulnerable, how fixed)
    - CWE mapping (for retrieval)
    - Language tags (Python, JS, etc)
    - Difficulty levels (easy, medium, hard)
    
    Query strategy:
    1. Match by CWE (exact match preferred)
    2. Match by language
    3. Sort by difficulty (prefer similar complexity)
    4. Return top-k examples (typically 3-5)
    
Performance Targets:
    - Query latency: <100ms
    - Database size: ~5MB (50K examples)
    - Initial seed: 50+ examples (CWE Top 25)
    - Coverage: Python (primary), JS/Go (secondary)

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Teacher of patterns
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class DifficultyLevel(str, Enum):
    """Fix difficulty levels"""
    EASY = "easy"      # Single line change, obvious fix
    MEDIUM = "medium"  # Multi-line, requires understanding
    HARD = "hard"      # Complex logic, subtle issues


@dataclass
class VulnerabilityFix:
    """Represents a single vulnerability fix example"""
    
    id: Optional[int]
    cwe_id: str
    cve_id: Optional[str]
    language: str
    vulnerable_code: str
    fixed_code: str
    explanation: str
    difficulty: DifficultyLevel
    created_at: Optional[datetime] = None
    
    def to_few_shot_prompt(self) -> str:
        """Format as few-shot example for LLM"""
        return f"""
## Example Fix ({self.cwe_id})

**Vulnerability**: {self.explanation}

**Vulnerable Code**:
```{self.language}
{self.vulnerable_code}
```

**Fixed Code**:
```{self.language}
{self.fixed_code}
```
""".strip()


class FewShotDatabase:
    """
    SQLite database manager for vulnerability fix examples.
    
    Schema:
        - vulnerability_fixes: Main table with fix examples
        - Indexes: cwe_id, language, difficulty
    
    Usage:
        >>> db = FewShotDatabase("data/few_shot_examples.db")
        >>> db.initialize()
        >>> examples = db.get_examples_by_cwe("CWE-89", language="python", limit=5)
        >>> for ex in examples:
        ...     print(ex.to_few_shot_prompt())
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS vulnerability_fixes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cwe_id TEXT NOT NULL,
        cve_id TEXT,
        language TEXT NOT NULL,
        vulnerable_code TEXT NOT NULL,
        fixed_code TEXT NOT NULL,
        explanation TEXT NOT NULL,
        difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard')) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_cwe ON vulnerability_fixes(cwe_id);
    CREATE INDEX IF NOT EXISTS idx_language ON vulnerability_fixes(language);
    CREATE INDEX IF NOT EXISTS idx_difficulty ON vulnerability_fixes(difficulty);
    CREATE INDEX IF NOT EXISTS idx_cwe_lang ON vulnerability_fixes(cwe_id, language);
    """
    
    def __init__(self, db_path: Path | str = "data/few_shot_examples.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized FewShotDatabase at {self.db_path}")
    
    def initialize(self) -> None:
        """Create database schema if not exists"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
        
        logger.info("Database schema initialized")
    
    def add_example(self, example: VulnerabilityFix) -> int:
        """
        Add vulnerability fix example to database.
        
        Args:
            example: VulnerabilityFix instance
        
        Returns:
            Inserted row ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO vulnerability_fixes 
                (cwe_id, cve_id, language, vulnerable_code, fixed_code, explanation, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    example.cwe_id,
                    example.cve_id,
                    example.language,
                    example.vulnerable_code,
                    example.fixed_code,
                    example.explanation,
                    example.difficulty.value,
                )
            )
            conn.commit()
            row_id = cursor.lastrowid
        
        logger.debug(f"Added example {row_id} for {example.cwe_id}")
        return row_id
    
    def add_examples_bulk(self, examples: List[VulnerabilityFix]) -> int:
        """
        Bulk insert examples (faster than individual inserts).
        
        Args:
            examples: List of VulnerabilityFix instances
        
        Returns:
            Number of inserted rows
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.executemany(
                """
                INSERT INTO vulnerability_fixes 
                (cwe_id, cve_id, language, vulnerable_code, fixed_code, explanation, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (ex.cwe_id, ex.cve_id, ex.language, ex.vulnerable_code,
                     ex.fixed_code, ex.explanation, ex.difficulty.value)
                    for ex in examples
                ]
            )
            conn.commit()
            count = cursor.rowcount
        
        logger.info(f"Bulk inserted {count} examples")
        return count
    
    def get_examples_by_cwe(
        self,
        cwe_id: str,
        language: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
        limit: int = 5
    ) -> List[VulnerabilityFix]:
        """
        Retrieve examples matching CWE (and optionally language/difficulty).
        
        Args:
            cwe_id: CWE identifier (e.g., "CWE-89")
            language: Optional language filter (e.g., "python")
            difficulty: Optional difficulty filter
            limit: Maximum examples to return
        
        Returns:
            List of VulnerabilityFix examples
        """
        query = "SELECT * FROM vulnerability_fixes WHERE cwe_id = ?"
        params = [cwe_id]
        
        if language:
            query += " AND language = ?"
            params.append(language)
        
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty.value)
        
        query += " ORDER BY difficulty ASC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        examples = [self._row_to_example(row) for row in rows]
        logger.debug(f"Retrieved {len(examples)} examples for {cwe_id}")
        return examples
    
    def get_random_examples(
        self,
        language: Optional[str] = None,
        limit: int = 5
    ) -> List[VulnerabilityFix]:
        """
        Get random examples (useful for diversity in few-shot).
        
        Args:
            language: Optional language filter
            limit: Number of examples
        
        Returns:
            List of random VulnerabilityFix examples
        """
        query = "SELECT * FROM vulnerability_fixes"
        params = []
        
        if language:
            query += " WHERE language = ?"
            params.append(language)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        return [self._row_to_example(row) for row in rows]
    
    def count_examples(
        self,
        cwe_id: Optional[str] = None,
        language: Optional[str] = None
    ) -> int:
        """
        Count examples in database.
        
        Args:
            cwe_id: Optional CWE filter
            language: Optional language filter
        
        Returns:
            Count of matching examples
        """
        query = "SELECT COUNT(*) FROM vulnerability_fixes"
        params = []
        conditions = []
        
        if cwe_id:
            conditions.append("cwe_id = ?")
            params.append(cwe_id)
        
        if language:
            conditions.append("language = ?")
            params.append(language)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            count = cursor.fetchone()[0]
        
        return count
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts by CWE, language, difficulty
        """
        with sqlite3.connect(self.db_path) as conn:
            stats = {
                "total": conn.execute("SELECT COUNT(*) FROM vulnerability_fixes").fetchone()[0],
                "by_cwe": {},
                "by_language": {},
                "by_difficulty": {}
            }
            
            # By CWE
            cursor = conn.execute(
                "SELECT cwe_id, COUNT(*) FROM vulnerability_fixes GROUP BY cwe_id"
            )
            stats["by_cwe"] = dict(cursor.fetchall())
            
            # By language
            cursor = conn.execute(
                "SELECT language, COUNT(*) FROM vulnerability_fixes GROUP BY language"
            )
            stats["by_language"] = dict(cursor.fetchall())
            
            # By difficulty
            cursor = conn.execute(
                "SELECT difficulty, COUNT(*) FROM vulnerability_fixes GROUP BY difficulty"
            )
            stats["by_difficulty"] = dict(cursor.fetchall())
        
        return stats
    
    def _row_to_example(self, row: sqlite3.Row) -> VulnerabilityFix:
        """Convert SQLite row to VulnerabilityFix"""
        return VulnerabilityFix(
            id=row["id"],
            cwe_id=row["cwe_id"],
            cve_id=row["cve_id"],
            language=row["language"],
            vulnerable_code=row["vulnerable_code"],
            fixed_code=row["fixed_code"],
            explanation=row["explanation"],
            difficulty=DifficultyLevel(row["difficulty"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )


# Convenience function
def get_few_shot_examples(
    cwe_id: str,
    language: str = "python",
    limit: int = 3,
    db_path: str = "data/few_shot_examples.db"
) -> List[VulnerabilityFix]:
    """
    Quick function to get few-shot examples.
    
    Args:
        cwe_id: CWE identifier
        language: Programming language
        limit: Number of examples
        db_path: Database path
    
    Returns:
        List of VulnerabilityFix examples
    
    Example:
        >>> examples = get_few_shot_examples("CWE-89", language="python", limit=3)
        >>> for ex in examples:
        ...     print(ex.to_few_shot_prompt())
    """
    db = FewShotDatabase(db_path)
    return db.get_examples_by_cwe(cwe_id, language=language, limit=limit)
