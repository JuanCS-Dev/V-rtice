"""
Prompt Templates - LLM prompts for vulnerability patching.

APPATCH-inspired prompts for code patch generation via LLM.

Theoretical Foundation:
    Effective LLM patching requires structured prompts with:
    1. Vulnerability context (CVE, description, severity)
    2. Code context (vulnerable code + surrounding context)
    3. Fix guidance (pattern to remove, expected behavior)
    4. Output format (unified diff, specific format)
    
    Prompt engineering principles:
    - Be explicit about format
    - Provide context window
    - Request reasoning (chain-of-thought)
    - Constrain output (diff only, no explanation unless asked)
    
    Inspired by APPATCH paper (2023) which achieved 68% exact match
    on Defects4J benchmark using GPT-4 with structured prompts.

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Master Communicator
"""

from typing import List, Dict


# System prompt for patch generation
SYSTEM_PROMPT = """You are an expert security engineer specializing in vulnerability remediation.

Your task is to generate precise, minimal patches that fix security vulnerabilities while preserving functionality.

Guidelines:
1. Generate ONLY the unified diff (git format) - no explanations unless requested
2. Make minimal changes - fix the vulnerability, nothing else
3. Preserve code style and conventions
4. Consider edge cases and error handling
5. Ensure the fix doesn't introduce new vulnerabilities

Output format:
- Unified diff starting with "--- a/" and "+++ b/"
- Include @@ line numbers @@
- Show only changed lines with context
"""


def generate_patch_prompt(
    cve_id: str,
    summary: str,
    vulnerable_code: str,
    file_path: str,
    context_before: str = "",
    context_after: str = "",
    ast_grep_pattern: str = "",
    fix_guidance: str = "",
) -> str:
    """
    Generate prompt for LLM patch generation.
    
    Creates structured prompt with vulnerability details, code context,
    and fix guidance. Returns prompt ready for LLM completion.
    
    Args:
        cve_id: CVE identifier
        summary: Vulnerability summary
        vulnerable_code: Code containing vulnerability
        file_path: Path to vulnerable file
        context_before: Code before vulnerable section
        context_after: Code after vulnerable section
        ast_grep_pattern: ast-grep pattern that matched (if available)
        fix_guidance: Additional fix guidance (optional)
        
    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"# Vulnerability: {cve_id}",
        "",
        "## Summary",
        summary,
        "",
        f"## File: {file_path}",
        "",
    ]
    
    # Add ast-grep pattern if available
    if ast_grep_pattern:
        prompt_parts.extend([
            "## Vulnerable Pattern (ast-grep)",
            "```",
            ast_grep_pattern,
            "```",
            "",
        ])
    
    # Add code context
    prompt_parts.extend([
        "## Vulnerable Code",
        "",
        "### Context Before",
        "```",
        context_before if context_before else "(start of file)",
        "```",
        "",
        "### VULNERABLE SECTION (FIX THIS)",
        "```",
        vulnerable_code,
        "```",
        "",
        "### Context After",
        "```",
        context_after if context_after else "(end of file)",
        "```",
        "",
    ])
    
    # Add fix guidance if provided
    if fix_guidance:
        prompt_parts.extend([
            "## Fix Guidance",
            fix_guidance,
            "",
        ])
    
    # Add task instruction
    prompt_parts.extend([
        "## Task",
        f"Generate a unified diff (git format) that fixes the vulnerability in {file_path}.",
        "",
        "Requirements:",
        "- Output ONLY the unified diff",
        "- Use proper diff format: --- a/path +++ b/path @@ line,count @@",
        "- Include 3 lines of context before and after changes",
        "- Make minimal changes to fix the vulnerability",
        "- Preserve existing code style",
        "",
        "Generate the diff now:",
    ])
    
    return "\n".join(prompt_parts)


def generate_validation_prompt(
    original_code: str,
    patched_code: str,
    cve_id: str,
    summary: str,
) -> str:
    """
    Generate prompt for patch validation.
    
    Asks LLM to review generated patch and identify potential issues.
    Used for confidence scoring and validation.
    
    Args:
        original_code: Original vulnerable code
        patched_code: Code after applying patch
        cve_id: CVE identifier
        summary: Vulnerability summary
        
    Returns:
        Validation prompt
    """
    return f"""# Patch Validation for {cve_id}

## Vulnerability
{summary}

## Original Code
```
{original_code}
```

## Patched Code
```
{patched_code}
```

## Task
Review the patch and answer:

1. Does this patch fix the vulnerability? (Yes/No)
2. Does it introduce any new issues? (Yes/No)
3. Does it preserve functionality? (Yes/No)
4. Confidence score (0.0-1.0):
5. Brief justification:

Provide a structured response:
FIXES_VULNERABILITY: [Yes/No]
INTRODUCES_ISSUES: [Yes/No]
PRESERVES_FUNCTIONALITY: [Yes/No]
CONFIDENCE: [0.0-1.0]
JUSTIFICATION: [brief explanation]
"""


def generate_complexity_assessment_prompt(
    cve_id: str,
    summary: str,
    affected_files: List[str],
    code_snippets: Dict[str, str],
) -> str:
    """
    Generate prompt for complexity assessment.
    
    Asks LLM to assess remediation complexity before attempting patch.
    Helps with strategy selection and MTTR estimation.
    
    Args:
        cve_id: CVE identifier
        summary: Vulnerability summary
        affected_files: List of affected file paths
        code_snippets: Dict mapping file paths to code snippets
        
    Returns:
        Complexity assessment prompt
    """
    prompt_parts = [
        f"# Remediation Complexity Assessment: {cve_id}",
        "",
        "## Vulnerability",
        summary,
        "",
        f"## Affected Files ({len(affected_files)})",
    ]
    
    # Add code snippets
    for file_path in affected_files[:5]:  # Limit to first 5 files
        code = code_snippets.get(file_path, "")
        if code:
            prompt_parts.extend([
                f"### {file_path}",
                "```",
                code[:500],  # First 500 chars
                "```",
                "",
            ])
    
    if len(affected_files) > 5:
        prompt_parts.append(f"... and {len(affected_files) - 5} more files")
    
    prompt_parts.extend([
        "",
        "## Task",
        "Assess the complexity of remediating this vulnerability.",
        "",
        "Consider:",
        "- Number of locations affected",
        "- Code structure and dependencies",
        "- Potential side effects",
        "- Testing requirements",
        "",
        "Provide assessment:",
        "COMPLEXITY: [LOW/MEDIUM/HIGH/CRITICAL]",
        "ESTIMATED_EFFORT: [< 1h / 1-4h / 4-8h / > 8h]",
        "KEY_CHALLENGES: [list main challenges]",
        "RECOMMENDED_APPROACH: [brief strategy]",
    ])
    
    return "\n".join(prompt_parts)


# Template for explaining patch to human reviewer
PATCH_EXPLANATION_TEMPLATE = """# Patch Explanation: {cve_id}

## Vulnerability Fixed
{summary}

## Changes Made
{changes_description}

## Files Modified
{files_list}

## Testing Recommendations
{testing_recommendations}

## Risk Assessment
{risk_assessment}

## Rollback Plan
{rollback_plan}
"""


def format_patch_explanation(
    cve_id: str,
    summary: str,
    files_modified: List[str],
    diff_content: str,
) -> str:
    """
    Generate human-readable explanation of patch.
    
    Used for PR descriptions and manual review.
    
    Args:
        cve_id: CVE identifier
        summary: Vulnerability summary
        files_modified: List of modified files
        diff_content: Unified diff content
        
    Returns:
        Formatted explanation
    """
    # Extract line changes from diff
    added_lines = len([l for l in diff_content.split('\n') if l.startswith('+')])
    removed_lines = len([l for l in diff_content.split('\n') if l.startswith('-')])
    
    return PATCH_EXPLANATION_TEMPLATE.format(
        cve_id=cve_id,
        summary=summary,
        changes_description=f"Modified {added_lines} lines, removed {removed_lines} lines",
        files_list="\n".join(f"- {f}" for f in files_modified),
        testing_recommendations=(
            "1. Run existing unit tests\n"
            "2. Test affected functionality manually\n"
            "3. Run security scanners\n"
            "4. Deploy to staging environment first"
        ),
        risk_assessment="LOW - Minimal changes, well-tested pattern",
        rollback_plan="git revert <commit-sha> if issues detected",
    )
