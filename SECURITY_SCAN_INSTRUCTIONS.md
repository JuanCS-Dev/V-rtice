# Security Scan Instructions

Before making the repository public, run a comprehensive security scan to ensure no secrets or sensitive information are present.

---

## Quick Start

```bash
cd /home/maximus/Documentos/V-rtice

# Make script executable (if not already)
chmod +x scripts/final_security_scan.sh

# Run the scan
./scripts/final_security_scan.sh
```

---

## What the Script Checks

The security scan performs **9 comprehensive checks**:

### 1. **Git History Secret Scan (git-secrets)**
- Scans entire git history for AWS keys, API tokens, etc.
- Detects secrets that may have been committed and later removed

### 2. **Secret Patterns (detect-secrets)**
- Uses Yelp's detect-secrets to find common secret patterns
- Checks against baseline (`.secrets.baseline`)
- Detects: API keys, passwords, tokens, private keys

### 3. **Secret Leaks (gitleaks)**
- Industry-standard secret scanner
- Checks for leaked credentials in code
- Scans current files and git history

### 4. **Pattern Matching (grep)**
- Manual grep for common secret patterns:
  - AWS Access Keys (`AKIA...`)
  - Google API Keys (`AIza...`)
  - OpenAI Keys (`sk-...`)
  - Claude Keys (`sk-ant-...`)
  - GitHub Tokens (`ghp_...`, `gho_...`)
  - Hardcoded passwords, api_keys, tokens

### 5. **File Permissions**
- Checks for world-writable files
- Ensures sensitive files have proper permissions

### 6. **Environment File Safety**
- Verifies `.env` is in `.gitignore`
- Confirms `.env` is not tracked by git
- Checks `.env.example` has placeholder values only

### 7. **Dependency Security**
- npm audit for JavaScript dependencies
- pip-audit for Python dependencies
- Identifies known vulnerabilities

### 8. **Docker Security**
- Checks `docker-compose.yml` for hardcoded passwords
- Verifies development-only credentials are documented

### 9. **Large Files**
- Identifies files >50MB that may bloat repository
- Suggests Git LFS for large assets

---

## Prerequisites

### Required (for basic scan):
- **Git** - Version control
- **Bash** - Shell script execution

### Recommended (for full scan):
Install these tools for comprehensive scanning:

```bash
# git-secrets (AWS/GitHub)
# macOS:
brew install git-secrets

# Ubuntu/Debian:
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
sudo make install

# detect-secrets (Yelp)
pip install detect-secrets

# gitleaks (industry standard)
# macOS:
brew install gitleaks

# Ubuntu/Debian:
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
tar -xzf gitleaks_8.18.0_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/

# pip-audit (Python dependencies)
pip install pip-audit

# npm (JavaScript dependencies) - usually pre-installed
# Verify: npm --version
```

**Note**: The script will skip checks for missing tools and warn you, but won't fail.

---

## Expected Output

### ✅ Clean Repository (No Issues)
```
═══════════════════════════════════════════════════════════════════════════
  FINAL SECURITY SCAN REPORT
═══════════════════════════════════════════════════════════════════════════

Summary:
  Total Checks: 9
  Passed: 9
  Failed: 0
  Warnings: 0

✅ ALL CRITICAL CHECKS PASSED ✅

Repository appears SAFE for public release.

Detailed log saved to: security_scan_20251029_143052.log

Next steps:
1. Review this report carefully
2. Address any warnings if applicable
3. If all looks good, proceed with publication plan
4. After making public, enable GitHub secret scanning
```

### ⚠️ Warnings (Non-Critical)
```
Summary:
  Total Checks: 9
  Passed: 7
  Failed: 0
  Warnings: 2

✅ ALL CRITICAL CHECKS PASSED ✅

However, there are 2 warnings to review.
Review the warnings above and address if necessary.
```

**Common warnings** (usually safe):
- `detect-secrets` finding test files with mock keys
- `docker-compose.yml` with development passwords (document as dev-only)
- Large files (consider Git LFS)
- Missing optional tools (git-secrets, gitleaks)

### ❌ Critical Issues Found
```
Summary:
  Total Checks: 9
  Passed: 6
  Failed: 3
  Warnings: 0

❌ CRITICAL ISSUES FOUND! 🚨

DO NOT make repository public until these issues are resolved:
1. Review all failed checks above
2. Remove any secrets/credentials found
3. Re-run this script
```

**If this happens:**
1. Review the detailed output above the summary
2. Identify which checks failed
3. Remove any secrets found
4. If secrets are in git history, see "Removing Secrets from History" below
5. Re-run the scan

---

## Interpreting Results

### Critical Failures (Must Fix):
- ❌ `.env` file tracked by git → **Remove immediately**: `git rm --cached .env`
- ❌ Real API keys found in code → **Remove and rotate keys**
- ❌ Secrets in git history → **Rewrite history** (see below)
- ❌ `.env` not in `.gitignore` → **Add immediately**: `echo ".env" >> .gitignore`

### Warnings (Review & Decide):
- ⚠️ `detect-secrets` finding test fixtures → **Verify they're fake, not real**
- ⚠️ Docker dev passwords → **Document as dev-only**
- ⚠️ Large files → **Consider Git LFS** (optional)
- ⚠️ World-writable files → **Fix permissions** (usually scripts)
- ⚠️ npm/pip vulnerabilities → **Update dependencies**

### Info (Acknowledged):
- ℹ️ Tool not installed → **Install for full scan** (optional)
- ℹ️ Uncommitted changes → **Commit or stash** (optional)

---

## Removing Secrets from Git History

### ⚠️ WARNING: This rewrites git history!

If secrets are found in git history, you MUST remove them before going public.

### Option 1: git-filter-repo (Recommended)
```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove specific file from history
git filter-repo --invert-paths --path path/to/secret-file.txt

# Remove specific string/pattern from all files
git filter-repo --replace-text <(echo "SECRET_KEY_HERE==>REDACTED")

# Force push (DESTRUCTIVE - only if haven't gone public yet!)
git push origin --force --all
```

### Option 2: BFG Repo-Cleaner
```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Remove file
java -jar bfg-1.14.0.jar --delete-files secret-file.txt

# Remove passwords/keys
java -jar bfg-1.14.0.jar --replace-text passwords.txt  # file with patterns to replace

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

### Option 3: Start Fresh (Nuclear Option)
If history is heavily contaminated:
```bash
# Create new repo with current state only
mkdir ../V-rtice-clean
cp -r . ../V-rtice-clean/
cd ../V-rtice-clean
rm -rf .git

# Initialize fresh
git init
git add .
git commit -m "Initial commit - clean history"

# Push to new repository
git remote add origin https://github.com/JuanCS-Dev/V-rtice-clean.git
git push -u origin main
```

### After Removing Secrets:
1. **Rotate all exposed secrets** (API keys, tokens, passwords)
2. **Notify affected services** (AWS, OpenAI, GitHub, etc.)
3. **Re-run security scan** to verify clean
4. **Update `.gitignore`** to prevent re-occurrence

---

## False Positives

Some detections are **false positives** (not real secrets):

### Common False Positives:
- Test fixtures: `tests/fixtures/mock_api_key.json` (fake keys for testing)
- Documentation: `docs/examples/api-example.md` (example placeholders)
- `.env.example`: Placeholder values like `YOUR_API_KEY_HERE`
- Honeypot code: Intentional fake credentials for security research
- Base64 encoded data: Not a secret, just encoding

### How to Handle:
1. **Review manually** - Verify it's truly fake
2. **Document in baseline**: `detect-secrets audit .secrets.baseline`
3. **Mark as false positive** - Add to `.secrets.baseline`
4. **Continue** - Not a blocker for publication

---

## Post-Scan Checklist

After scan passes:

- [ ] Review full log file (`security_scan_YYYYMMDD_HHMMSS.log`)
- [ ] Address any warnings (or document why they're acceptable)
- [ ] Verify `.env` is not tracked: `git ls-files | grep .env` (should be empty)
- [ ] Verify `.env` is gitignored: `grep .env .gitignore` (should show `.env`)
- [ ] Rotate any secrets that were exposed (even if removed from git)
- [ ] Update `SECURITY.md` with scan date and results
- [ ] Commit any fixes: `git add . && git commit -m "security: Address scan findings"`
- [ ] Re-run scan to confirm: `./scripts/final_security_scan.sh`

---

## Troubleshooting

### "command not found" errors
**Solution**: Install missing tools (see Prerequisites section)
**Workaround**: Script will skip checks for missing tools and continue

### "Not in repository root" error
**Solution**: Run from repository root: `cd /home/maximus/Documentos/V-rtice`

### "Permission denied" when running script
**Solution**: Make executable: `chmod +x scripts/final_security_scan.sh`

### Scan takes a long time
**Normal**: Full history scan can take 5-10 minutes for large repos
**Speed up**: Skip history scan by commenting out git-secrets/gitleaks sections

### Too many false positives
**Solution**:
1. Audit findings: `detect-secrets audit .secrets.baseline`
2. Mark false positives
3. Re-run scan

---

## Integration with CI/CD

To run automatically on every commit:

### GitHub Actions
Already configured in `.github/workflows/security-scan.yml`

### Pre-commit Hook
Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: security-scan
      name: Security Scan
      entry: ./scripts/final_security_scan.sh
      language: system
      pass_filenames: false
```

---

## Summary

**Before going public:**
```bash
# 1. Run scan
./scripts/final_security_scan.sh

# 2. Review output
cat security_scan_*.log

# 3. Fix any critical issues
# (Remove secrets, rotate keys, etc.)

# 4. Re-run to confirm
./scripts/final_security_scan.sh

# 5. If all checks pass, proceed to publication!
```

**Remember**: Better safe than sorry. A few extra minutes scanning can prevent major security incidents.

---

**Questions?** See [SECURITY.md](./SECURITY.md) or email security@vertice-maximus.com
