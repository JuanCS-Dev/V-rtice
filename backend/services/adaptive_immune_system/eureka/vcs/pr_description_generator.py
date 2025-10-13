"""
PR Description Generator - Generates comprehensive PR descriptions.

Creates rich markdown descriptions with:
- Vulnerability summary
- CVE details and links
- Patch explanation
- Testing instructions
- Security context
- Reviewer checklist
"""

import logging
from typing import Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PRDescriptionContext(BaseModel):
    """Context for PR description generation."""

    # APV information
    apv_id: str
    apv_code: str
    cve_id: str
    cvss_score: Optional[float] = None
    severity: str
    cwe_ids: List[str]

    # Vulnerability details
    vulnerability_description: str
    affected_files: List[str]

    # Patch information
    patch_strategy: str
    patch_description: str
    dependency_name: Optional[str] = None
    version_before: Optional[str] = None
    version_after: Optional[str] = None

    # Confirmation details
    static_confidence: float
    dynamic_confidence: float
    false_positive_probability: float

    # Validation results
    tests_passed: bool
    validation_warnings: List[str]


class PRDescriptionGenerator:
    """
    Generates comprehensive PR descriptions for security fixes.

    Templates:
    - Version bump PRs
    - Code rewrite PRs
    - Config change PRs
    - Workaround PRs
    """

    def __init__(self):
        """Initialize PR description generator."""
        logger.info("PRDescriptionGenerator initialized")

    def generate_description(
        self, context: PRDescriptionContext
    ) -> str:
        """
        Generate PR description.

        Args:
            context: PRDescriptionContext

        Returns:
            Markdown-formatted PR description
        """
        logger.info(f"Generating PR description for {context.apv_code}")

        # Build description sections
        sections = [
            self._generate_header(context),
            self._generate_vulnerability_summary(context),
            self._generate_patch_details(context),
            self._generate_confidence_scores(context),
            self._generate_testing_instructions(context),
            self._generate_reviewer_checklist(context),
            self._generate_references(context),
            self._generate_footer(),
        ]

        description = "\n\n".join(sections)

        logger.info(f"Generated {len(description)} char PR description")

        return description

    def _generate_header(self, context: PRDescriptionContext) -> str:
        """Generate PR header with severity badge."""
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }

        emoji = severity_emoji.get(context.severity.lower(), "⚪")

        return f"""# {emoji} Security Fix: {context.cve_id}

> **APV Code**: `{context.apv_code}`
> **Severity**: **{context.severity.upper()}** {f"(CVSS {context.cvss_score})" if context.cvss_score else ""}
> **Strategy**: {context.patch_strategy}"""

    def _generate_vulnerability_summary(self, context: PRDescriptionContext) -> str:
        """Generate vulnerability summary section."""
        cwe_list = ", ".join(f"[{cwe}](https://cwe.mitre.org/data/definitions/{cwe.replace('CWE-', '')}.html)" for cwe in context.cwe_ids[:3])

        return f"""## 🐛 Vulnerability Summary

{context.vulnerability_description}

**CWE Classification**: {cwe_list if cwe_list else "N/A"}

**Affected Files**:
{self._format_file_list(context.affected_files)}"""

    def _generate_patch_details(self, context: PRDescriptionContext) -> str:
        """Generate patch details section."""
        if context.patch_strategy == "version_bump":
            return f"""## 🔧 Patch Details

**Strategy**: Version Bump

This PR updates `{context.dependency_name}` from version `{context.version_before}` to `{context.version_after}`, which includes the security patch for {context.cve_id}.

**Change Summary**:
- ✅ Update dependency to patched version
- ✅ No code changes required
- ✅ Low risk, high confidence fix

{context.patch_description}"""

        elif context.patch_strategy == "code_rewrite":
            return f"""## 🔧 Patch Details

**Strategy**: Code Rewrite (LLM-Generated)

This PR rewrites vulnerable code to eliminate the security vulnerability. The fix was generated using AI-powered code analysis and has been validated.

**Change Summary**:
{context.patch_description}

⚠️ **Important**: This is an LLM-generated fix. Please review carefully before merging."""

        elif context.patch_strategy == "config_change":
            return f"""## 🔧 Patch Details

**Strategy**: Configuration Change

This PR modifies configuration to mitigate the vulnerability without requiring code changes.

**Change Summary**:
{context.patch_description}"""

        else:  # workaround
            return f"""## 🔧 Patch Details

**Strategy**: Temporary Workaround

This PR implements a temporary mitigation until an official patch is available.

⚠️ **Warning**: This is a workaround, not a permanent fix. Monitor for official patches.

**Change Summary**:
{context.patch_description}"""

    def _generate_confidence_scores(self, context: PRDescriptionContext) -> str:
        """Generate confidence scores section."""
        fp_status = "✅ Low" if context.false_positive_probability < 0.3 else "⚠️ Medium" if context.false_positive_probability < 0.6 else "🔴 High"

        return f"""## 📊 Confirmation Scores

| Metric | Score | Status |
|--------|-------|--------|
| Static Analysis Confidence | {context.static_confidence:.1%} | {self._get_confidence_emoji(context.static_confidence)} |
| Dynamic Analysis Confidence | {context.dynamic_confidence:.1%} | {self._get_confidence_emoji(context.dynamic_confidence)} |
| False Positive Probability | {context.false_positive_probability:.1%} | {fp_status} |

**Analysis Method**: Hybrid (Static + Dynamic)"""

    def _generate_testing_instructions(self, context: PRDescriptionContext) -> str:
        """Generate testing instructions."""
        test_status = "✅ PASSED" if context.tests_passed else "❌ FAILED"

        warnings_section = ""
        if context.validation_warnings:
            warnings_list = "\n".join(f"- ⚠️ {w}" for w in context.validation_warnings)
            warnings_section = f"\n\n**Validation Warnings**:\n{warnings_list}"

        return f"""## 🧪 Testing

**Automated Tests**: {test_status}{warnings_section}

### Manual Testing Steps

1. **Pull this branch**:
   ```bash
   git fetch origin
   git checkout {self._generate_branch_name(context)}
   ```

2. **Install dependencies**:
   ```bash
   # For Python
   pip install -r requirements.txt

   # For JavaScript
   npm install
   ```

3. **Run tests**:
   ```bash
   # Run full test suite
   pytest  # or npm test

   # Run specific security tests
   pytest tests/security/
   ```

4. **Verify the fix**:
   - Confirm vulnerable code pattern is removed
   - Ensure no new vulnerabilities introduced
   - Check for breaking changes

### Security Verification

Try to reproduce the vulnerability with the patched code:
```bash
# Add specific reproduction steps based on CVE
```

Expected result: Vulnerability should be mitigated."""

    def _generate_reviewer_checklist(self, context: PRDescriptionContext) -> str:
        """Generate reviewer checklist."""
        return """## ✅ Reviewer Checklist

Please verify the following before approving:

### Security Review
- [ ] CVE information verified against official sources
- [ ] Patch correctly addresses the vulnerability
- [ ] No new security issues introduced
- [ ] Sensitive data not exposed in code or commit history

### Code Quality
- [ ] Code follows project style guidelines
- [ ] No breaking changes to public APIs
- [ ] Error handling is appropriate
- [ ] Comments/documentation updated if needed

### Testing
- [ ] All existing tests pass
- [ ] New tests added for security fix (if applicable)
- [ ] Manual testing performed
- [ ] No regression in functionality

### Dependency Management
- [ ] Version constraints are appropriate
- [ ] No conflicting dependencies
- [ ] Lock files updated (if version bump)

### Documentation
- [ ] CHANGELOG updated
- [ ] Security advisory created (if applicable)
- [ ] Deployment notes added (if needed)"""

    def _generate_references(self, context: PRDescriptionContext) -> str:
        """Generate references section."""
        cve_url = f"https://nvd.nist.gov/vuln/detail/{context.cve_id}"
        cwe_links = "\n".join(
            f"- [{cwe}](https://cwe.mitre.org/data/definitions/{cwe.replace('CWE-', '')}.html)"
            for cwe in context.cwe_ids[:5]
        )

        return f"""## 📚 References

### Vulnerability Information
- **NVD**: [{context.cve_id}]({cve_url})
- **CWE**:
{cwe_links if cwe_links else "  - N/A"}

### Additional Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

### Internal Tracking
- **APV Code**: `{context.apv_code}`"""

    def _generate_footer(self) -> str:
        """Generate PR footer."""
        return """---

🤖 **Generated by**: Adaptive Immune System (Eureka - Vulnerability Surgeon)
🔒 **Security Priority**: This PR addresses a confirmed security vulnerability
⏰ **Created**: Automatically generated security fix

**Questions?** Contact the security team or review the [Security Policy](../SECURITY.md)."""

    def _format_file_list(self, files: List[str]) -> str:
        """Format list of files."""
        if not files:
            return "- N/A"

        return "\n".join(f"- `{f}`" for f in files[:10])

    def _get_confidence_emoji(self, confidence: float) -> str:
        """Get emoji for confidence level."""
        if confidence >= 0.8:
            return "✅ High"
        elif confidence >= 0.6:
            return "🟡 Medium"
        else:
            return "⚠️ Low"

    def _generate_branch_name(self, context: PRDescriptionContext) -> str:
        """Generate branch name."""
        return f"security-fix/{context.cve_id.lower()}"

    def generate_commit_message(self, context: PRDescriptionContext) -> str:
        """
        Generate commit message for security fix.

        Args:
            context: PRDescriptionContext

        Returns:
            Commit message
        """
        if context.patch_strategy == "version_bump":
            message = f"""fix(security): {context.cve_id} - Update {context.dependency_name}

Update {context.dependency_name} from {context.version_before} to {context.version_after}
to patch {context.cve_id} ({context.severity} severity).

APV: {context.apv_code}
CVSS: {context.cvss_score or 'N/A'}
CWE: {', '.join(context.cwe_ids)}

This is an automated security fix generated by the Adaptive Immune System."""

        else:
            message = f"""fix(security): {context.cve_id} - {context.patch_strategy}

{context.patch_description[:200]}

APV: {context.apv_code}
Severity: {context.severity}
Strategy: {context.patch_strategy}

This is an automated security fix generated by the Adaptive Immune System."""

        return message
