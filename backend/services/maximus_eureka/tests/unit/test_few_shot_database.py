"""
Unit tests for Few-Shot Database.

Tests SQLite database manager for vulnerability fix examples.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from data.few_shot_database import (
    FewShotDatabase,
    VulnerabilityFix,
    DifficultyLevel,
    get_few_shot_examples,
)


# Fixtures

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_fix():
    """Sample vulnerability fix"""
    return VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id="CVE-2024-TEST",
        language="python",
        vulnerable_code='cursor.execute(f"SELECT * FROM users WHERE id={user_id}")',
        fixed_code='cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))',
        explanation="SQL injection via f-string. Use parameterized queries.",
        difficulty=DifficultyLevel.EASY
    )


# Tests: Initialization

def test_database_initialization(temp_db):
    """Test database can be initialized"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Check tables exist
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vulnerability_fixes'"
        )
        assert cursor.fetchone() is not None


def test_database_schema_indexes(temp_db):
    """Test indexes are created"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
    
    assert "idx_cwe" in indexes
    assert "idx_language" in indexes
    assert "idx_difficulty" in indexes
    assert "idx_cwe_lang" in indexes


# Tests: add_example

def test_add_example(temp_db, sample_fix):
    """Test adding single example"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    row_id = db.add_example(sample_fix)
    
    assert row_id > 0
    assert db.count_examples() == 1


def test_add_example_without_cve(temp_db):
    """Test adding example without CVE ID"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    fix = VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,  # No CVE
        language="python",
        vulnerable_code="bad",
        fixed_code="good",
        explanation="XSS fix",
        difficulty=DifficultyLevel.EASY
    )
    
    row_id = db.add_example(fix)
    assert row_id > 0


# Tests: add_examples_bulk

def test_add_examples_bulk(temp_db):
    """Test bulk insert"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    examples = [
        VulnerabilityFix(
            id=None,
            cwe_id="CWE-89",
            cve_id=None,
            language="python",
            vulnerable_code=f"code{i}",
            fixed_code=f"fixed{i}",
            explanation=f"Fix {i}",
            difficulty=DifficultyLevel.EASY
        )
        for i in range(10)
    ]
    
    count = db.add_examples_bulk(examples)
    
    assert count == 10
    assert db.count_examples() == 10


# Tests: get_examples_by_cwe

def test_get_examples_by_cwe(temp_db, sample_fix):
    """Test retrieving examples by CWE"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    db.add_example(sample_fix)
    
    examples = db.get_examples_by_cwe("CWE-89")
    
    assert len(examples) == 1
    assert examples[0].cwe_id == "CWE-89"
    assert examples[0].vulnerable_code == sample_fix.vulnerable_code


def test_get_examples_by_cwe_with_language_filter(temp_db):
    """Test CWE query with language filter"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add Python example
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code="py_bad",
        fixed_code="py_good",
        explanation="Python SQL fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    # Add JavaScript example
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="javascript",
        vulnerable_code="js_bad",
        fixed_code="js_good",
        explanation="JS SQL fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    # Query Python only
    python_examples = db.get_examples_by_cwe("CWE-89", language="python")
    
    assert len(python_examples) == 1
    assert python_examples[0].language == "python"


def test_get_examples_by_cwe_with_difficulty_filter(temp_db):
    """Test CWE query with difficulty filter"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add easy example
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="python",
        vulnerable_code="easy",
        fixed_code="fixed",
        explanation="Easy fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    # Add hard example
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="python",
        vulnerable_code="hard",
        fixed_code="fixed",
        explanation="Hard fix",
        difficulty=DifficultyLevel.HARD
    ))
    
    # Query easy only
    easy_examples = db.get_examples_by_cwe("CWE-79", difficulty=DifficultyLevel.EASY)
    
    assert len(easy_examples) == 1
    assert easy_examples[0].difficulty == DifficultyLevel.EASY


def test_get_examples_by_cwe_limit(temp_db):
    """Test limit parameter"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add 10 examples
    for i in range(10):
        db.add_example(VulnerabilityFix(
            id=None,
            cwe_id="CWE-89",
            cve_id=None,
            language="python",
            vulnerable_code=f"code{i}",
            fixed_code=f"fixed{i}",
            explanation="Fix",
            difficulty=DifficultyLevel.EASY
        ))
    
    # Query with limit=3
    examples = db.get_examples_by_cwe("CWE-89", limit=3)
    
    assert len(examples) == 3


def test_get_examples_by_cwe_nonexistent(temp_db):
    """Test querying non-existent CWE"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    examples = db.get_examples_by_cwe("CWE-9999")
    
    assert len(examples) == 0


# Tests: get_random_examples

def test_get_random_examples(temp_db):
    """Test getting random examples"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add examples
    for i in range(10):
        db.add_example(VulnerabilityFix(
            id=None,
            cwe_id=f"CWE-{i}",
            cve_id=None,
            language="python",
            vulnerable_code=f"code{i}",
            fixed_code=f"fixed{i}",
            explanation="Fix",
            difficulty=DifficultyLevel.EASY
        ))
    
    # Get random 3
    examples = db.get_random_examples(limit=3)
    
    assert len(examples) == 3


def test_get_random_examples_with_language_filter(temp_db):
    """Test random examples with language filter"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add Python examples
    for i in range(5):
        db.add_example(VulnerabilityFix(
            id=None,
            cwe_id=f"CWE-{i}",
            cve_id=None,
            language="python",
            vulnerable_code=f"py{i}",
            fixed_code=f"fixed{i}",
            explanation="Fix",
            difficulty=DifficultyLevel.EASY
        ))
    
    # Add JS examples
    for i in range(5):
        db.add_example(VulnerabilityFix(
            id=None,
            cwe_id=f"CWE-{i}",
            cve_id=None,
            language="javascript",
            vulnerable_code=f"js{i}",
            fixed_code=f"fixed{i}",
            explanation="Fix",
            difficulty=DifficultyLevel.EASY
        ))
    
    # Get random Python
    examples = db.get_random_examples(language="python", limit=3)
    
    assert len(examples) == 3
    assert all(ex.language == "python" for ex in examples)


# Tests: count_examples

def test_count_examples_total(temp_db, sample_fix):
    """Test counting all examples"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    assert db.count_examples() == 0
    
    db.add_example(sample_fix)
    assert db.count_examples() == 1


def test_count_examples_by_cwe(temp_db):
    """Test counting by CWE"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add CWE-89
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code="code",
        fixed_code="fixed",
        explanation="Fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    # Add CWE-79
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="python",
        vulnerable_code="code",
        fixed_code="fixed",
        explanation="Fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    assert db.count_examples(cwe_id="CWE-89") == 1
    assert db.count_examples(cwe_id="CWE-79") == 1


def test_count_examples_by_language(temp_db):
    """Test counting by language"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add Python
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code="code",
        fixed_code="fixed",
        explanation="Fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    # Add JS
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="javascript",
        vulnerable_code="code",
        fixed_code="fixed",
        explanation="Fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    assert db.count_examples(language="python") == 1
    assert db.count_examples(language="javascript") == 1


# Tests: get_statistics

def test_get_statistics_empty(temp_db):
    """Test statistics on empty database"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    stats = db.get_statistics()
    
    assert stats["total"] == 0
    assert stats["by_cwe"] == {}
    assert stats["by_language"] == {}
    assert stats["by_difficulty"] == {}


def test_get_statistics_with_data(temp_db):
    """Test statistics with data"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Add diverse examples
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="python",
        vulnerable_code="code",
        fixed_code="fixed",
        explanation="Fix",
        difficulty=DifficultyLevel.EASY
    ))
    
    db.add_example(VulnerabilityFix(
        id=None,
        cwe_id="CWE-89",
        cve_id=None,
        language="javascript",
        vulnerable_code="code",
        fixed_code="fixed",
        explanation="Fix",
        difficulty=DifficultyLevel.HARD
    ))
    
    stats = db.get_statistics()
    
    assert stats["total"] == 2
    assert stats["by_cwe"]["CWE-89"] == 2
    assert stats["by_language"]["python"] == 1
    assert stats["by_language"]["javascript"] == 1
    assert stats["by_difficulty"]["easy"] == 1
    assert stats["by_difficulty"]["hard"] == 1


# Tests: VulnerabilityFix model

def test_vulnerability_fix_to_few_shot_prompt(sample_fix):
    """Test few-shot prompt generation"""
    prompt = sample_fix.to_few_shot_prompt()
    
    assert "CWE-89" in prompt
    assert sample_fix.vulnerable_code in prompt
    assert sample_fix.fixed_code in prompt
    assert sample_fix.explanation in prompt
    assert "```python" in prompt


# Tests: Convenience function

def test_get_few_shot_examples_convenience(temp_db, sample_fix):
    """Test convenience function"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    db.add_example(sample_fix)
    
    examples = get_few_shot_examples("CWE-89", language="python", limit=5, db_path=temp_db)
    
    assert len(examples) == 1
    assert examples[0].cwe_id == "CWE-89"


# Tests: DifficultyLevel enum

def test_difficulty_level_enum():
    """Test DifficultyLevel enum values"""
    assert DifficultyLevel.EASY.value == "easy"
    assert DifficultyLevel.MEDIUM.value == "medium"
    assert DifficultyLevel.HARD.value == "hard"


# Tests: Edge cases

def test_example_with_unicode(temp_db):
    """Test example with unicode characters"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    fix = VulnerabilityFix(
        id=None,
        cwe_id="CWE-79",
        cve_id=None,
        language="python",
        vulnerable_code="# Comment with émojis 🚀",
        fixed_code="# Fixed 中文",
        explanation="Unicode test",
        difficulty=DifficultyLevel.EASY
    )
    
    row_id = db.add_example(fix)
    assert row_id > 0
    
    # Retrieve
    examples = db.get_examples_by_cwe("CWE-79")
    assert "🚀" in examples[0].vulnerable_code
    assert "中文" in examples[0].fixed_code


def test_example_with_multiline_code(temp_db):
    """Test example with multiline code"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    fix = VulnerabilityFix(
        id=None,
        cwe_id="CWE-20",
        cve_id=None,
        language="python",
        vulnerable_code="""def validate(data):
    # No validation
    return True""",
        fixed_code="""def validate(data):
    if not isinstance(data, str):
        raise ValueError("Invalid type")
    return True""",
        explanation="Add type check",
        difficulty=DifficultyLevel.MEDIUM
    )
    
    row_id = db.add_example(fix)
    assert row_id > 0
    
    examples = db.get_examples_by_cwe("CWE-20")
    assert "# No validation" in examples[0].vulnerable_code


def test_empty_query_results(temp_db):
    """Test queries with no results"""
    db = FewShotDatabase(temp_db)
    db.initialize()
    
    # Empty database
    assert db.get_examples_by_cwe("CWE-999") == []
    assert db.get_random_examples(limit=5) == []
    assert db.count_examples() == 0
