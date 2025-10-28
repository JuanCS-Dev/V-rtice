# Contributing to Vértice-MAXIMUS

Thank you for your interest in contributing to Vértice-MAXIMUS! This document provides guidelines for contributing to this offensive cybersecurity platform.

## ⚠️ LEGAL NOTICE - READ BEFORE CONTRIBUTING

**Vértice-MAXIMUS contains offensive security tools designed EXCLUSIVELY for authorized security testing.**

By contributing to this project, you acknowledge and agree that:

1. **You will NOT use these tools for unauthorized access** to computer systems, networks, or data
2. **You understand the legal implications** of cybersecurity tool development and deployment
3. **You accept full legal responsibility** for your use of any code, tools, or techniques from this project
4. **You will comply with all applicable laws** in your jurisdiction

### Legal Framework

#### 🇺🇸 United States

- **18 U.S.C. § 1030** (Computer Fraud and Abuse Act): Unauthorized access is a federal crime
- **18 U.S.C. § 2701** (Stored Communications Act): Unauthorized access to electronic communications
- **18 U.S.C. § 2511** (Wiretap Act): Interception of electronic communications
- **DMCA § 1201**: Anti-circumvention provisions (with security research exceptions under § 1201(j))

**Maximum Penalties**: Up to 20 years imprisonment, $250,000 fines for individuals, $500,000 for organizations

#### 🇧🇷 Brazil

- **Lei 12.737/2012** (Lei Carolina Dieckmann):
  - Art. 154-A: Invasão de dispositivo informático (3 months to 1 year + fine)
  - Art. 154-B: Dissemination of hacking tools without authorization (6 months to 2 years + fine)
- **Lei 12.965/2014** (Marco Civil da Internet): Internet rights and obligations
- **Lei 13.709/2018** (LGPD): Data protection and privacy requirements

**Maximum Penalties**: Up to 2 years imprisonment, significant fines, civil liability

#### 🇪🇺 European Union

- **GDPR**: Data protection requirements
- **Computer Misuse Act** (UK): Unauthorized access and modification
- **NIS Directive**: Network and information security obligations

## 🎯 Contribution Philosophy

### What We're Building

Vértice-MAXIMUS is a **sovereign cybersecurity platform** that combines:
- Multi-agent AI consciousness (MAXIMUS cognitive system)
- Offensive intelligence (autonomous pentesting, OSINT)
- Defensive immunity (adaptive, biomimetic security)
- Purple team orchestration (unified ops)

### Contribution Priorities

**High Priority**:
- Ethical AI agent behaviors and decision-making
- Legal compliance features (audit logging, authorization checks)
- Security improvements and vulnerability fixes
- Documentation and educational content
- Test coverage and quality assurance

**Medium Priority**:
- New offensive modules (with appropriate safeguards)
- UI/UX improvements
- Performance optimizations
- Integration with security tools (Metasploit, Burp Suite, etc.)

**Low Priority**:
- Cosmetic changes
- Refactoring without clear benefit

## 🚀 Getting Started

### 1. Prerequisites

```bash
# Node.js >= 18
node --version

# Python >= 3.11
python3 --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### 2. Fork & Clone

```bash
# Fork the repository on GitHub first
git clone https://github.com/YOUR_USERNAME/V-rtice.git
cd V-rtice

# Add upstream remote
git remote add upstream https://github.com/JuanCS-Dev/V-rtice.git
```

### 3. Development Setup

```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip3 install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose up -d
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

## 📝 Contribution Process

### 1. Code Standards

#### Backend (Python)

```bash
# Format with black
black backend/

# Sort imports
isort backend/

# Lint with flake8
flake8 backend/ --max-line-length=100

# Type check with mypy
mypy backend/
```

#### Frontend (React/TypeScript)

```bash
# Format with prettier
npm run format

# Lint with ESLint
npm run lint

# Type check
npm run type-check
```

### 2. Testing Requirements

**All contributions must include tests:**

#### Backend Tests
```bash
# Unit tests
pytest backend/tests/unit/

# Integration tests
pytest backend/tests/integration/

# Coverage (minimum 80%)
pytest --cov=backend --cov-report=html
```

#### Frontend Tests
```bash
# Unit tests (Vitest)
npm run test

# Integration tests
npm run test:integration

# E2E tests (Playwright)
npm run test:e2e

# Coverage (minimum 70%)
npm run test:coverage
```

### 3. Documentation

All contributions must include:

1. **Code comments**: Explain WHY, not just WHAT
2. **Docstrings**: For all public functions/classes (Google style)
3. **README updates**: If adding features or changing setup
4. **CHANGELOG entry**: In "Unreleased" section

Example docstring:
```python
def analyze_threat(target: str, technique: str) -> ThreatAnalysis:
    """Analyzes security threats using MAXIMUS cognitive engine.

    Args:
        target: The system or network to analyze (FQDN or IP)
        technique: MITRE ATT&CK technique ID (e.g., "T1566.001")

    Returns:
        ThreatAnalysis object with risk assessment and recommendations

    Raises:
        AuthorizationError: If target is not in authorized scope
        ValueError: If technique ID is invalid

    Note:
        Requires explicit authorization. Logs all operations for audit.
    """
```

### 4. Security Requirements

**All offensive security contributions MUST include:**

1. **Authorization Check**:
```python
if not is_authorized(target):
    raise AuthorizationError(f"No authorization for target: {target}")
```

2. **Audit Logging**:
```python
logger.audit(
    event="offensive_operation",
    target=target,
    technique=technique,
    user=current_user,
    authorization_id=auth_id
)
```

3. **Safe Defaults**:
```python
# Default to passive, require explicit --active flag
parser.add_argument("--active", action="store_true",
                   help="Enable active exploitation (requires authorization)")
```

4. **Scope Limiting**:
```python
# Validate target is in authorized scope
if not scope_validator.is_in_scope(target, authorized_scope):
    raise ScopeViolationError(f"Target {target} not in authorized scope")
```

### 5. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): brief description

Detailed explanation of what changed and why.

Fixes #123
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `security`

Examples:
```bash
git commit -m "feat(offensive): Add MITRE ATT&CK T1566 phishing module with authorization checks"
git commit -m "security(auth): Fix authorization bypass in offensive module validation"
git commit -m "docs(readme): Add legal compliance section for Brazilian law"
```

### 6. Pull Request Process

1. **Update Documentation**: README, CHANGELOG, inline docs
2. **Run Tests**: Ensure all tests pass
3. **Security Check**: Run `npm audit` and `safety check`
4. **Create PR**: Use the PR template
5. **CI Checks**: All CI checks must pass
6. **Code Review**: Address reviewer feedback
7. **Merge**: Squash and merge after approval

**PR Template**:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Security fix

## Legal Compliance
- [ ] I have authorization to develop/test these capabilities
- [ ] Code includes proper authorization checks
- [ ] Audit logging is implemented
- [ ] I understand the legal implications

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally
- [ ] Code coverage >= 80% (backend) / 70% (frontend)

## Documentation
- [ ] Code comments added
- [ ] Docstrings updated
- [ ] README updated (if applicable)
- [ ] CHANGELOG updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No secrets/credentials committed
- [ ] Sensitive operations are logged
```

## 🔒 Security Considerations

### Secrets Management

**NEVER commit**:
- API keys, passwords, tokens
- Private keys, certificates
- Database credentials
- Internal URLs, IP addresses (use placeholders)

**Use**:
- Environment variables
- Secret management services (Vault, AWS Secrets Manager)
- `.env.example` files with placeholders

### Pre-commit Hooks

Install pre-commit hooks to catch secrets:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🏆 Recognition

Contributors will be recognized in:
- **CHANGELOG**: Feature credits
- **README**: Contributors section
- **Release Notes**: Major contributions highlighted
- **GitHub**: Contributor graphs and statistics

## 🤝 Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, showcases
- **Email**: juan@vertice-maximus.com (security, legal, sensitive topics)

### Response Times

- **Security Issues**: 24-48 hours
- **Bug Reports**: 3-7 days
- **Feature Requests**: 7-14 days
- **Pull Requests**: 3-7 days for initial review

## ❓ Questions?

- Check [README.md](./README.md) for project overview
- Review [SECURITY.md](./SECURITY.md) for security policies
- Read [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) for community standards
- Contact: juan@vertice-maximus.com

## 📚 Learning Resources

### Cybersecurity Ethics
- [SANS Ethics](https://www.sans.org/security-resources/ethics.php)
- [EC-Council Code of Ethics](https://www.eccouncil.org/code-of-ethics/)
- [(ISC)² Code of Ethics](https://www.isc2.org/Ethics)

### Legal Compliance
- [CFAA Legal Guide](https://www.justice.gov/criminal-ccips/ccmanual)
- [DMCA Section 1201 Security Research](https://www.copyright.gov/1201/)
- [LGPD Brazilian Data Protection](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

### Technical Skills
- [MITRE ATT&CK](https://attack.mitre.org/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

## 📄 License

By contributing to Vértice-MAXIMUS, you agree that your contributions will be licensed under the [Apache License 2.0](./LICENSE).

**Contact**: juan@vertice-maximus.com
**Last Updated**: January 2025

Copyright © 2025 Juan Carlos de Souza. All Rights Reserved.
