# Changelog

All notable changes to Vértice-MAXIMUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Sponsors and Buy Me A Coffee funding integration ([#funding](https://github.com/JuanCS-Dev/V-rtice))
  - GitHub Sponsors badge in README
  - Buy Me A Coffee interactive button section in landing page
  - Support section with transparent API cost breakdown (~$300/month)
  - Coffee-to-tokens conversion explanation (10k tokens per coffee)
- Landing page with biological metaphor positioning ([#landing](https://github.com/JuanCS-Dev/V-rtice))
  - Vertical 3D perspective carousel for dashboard showcase
  - NEUROSHELL natural language command interface section
  - Easter eggs for family (Penélope's cockroach 🪳, Yakult 🥛)
  - Privacy Policy and Terms of Service pages
  - SEO optimization with structured data (JSON-LD)
  - Sitemap.xml and robots.txt for search engines
- npm package configuration (vertice-maximus) ([#npm](https://github.com/JuanCS-Dev/V-rtice))
  - Interactive CLI with `vertice init` setup wizard
  - Multi-LLM support (Claude, OpenAI, Gemini, custom)
  - Commands: init, start, scan, status, stop, config
  - Beautiful ASCII art and colored terminal output
- Comprehensive legal framework for offensive security tools ([#legal](https://github.com/JuanCS-Dev/V-rtice))
  - SECURITY.md with vulnerability reporting process
  - CODE_OF_CONDUCT.md with cybersecurity ethics
  - CONTRIBUTING.md with authorization requirements
  - Legal compliance for US (CFAA, DMCA), Brazil (Lei 12.737, LGPD), EU (GDPR)
  - Offensive security disclaimer in README
- Security audit infrastructure ([#security](https://github.com/JuanCS-Dev/V-rtice))
  - Pre-commit hooks with 15+ security checks (bandit, safety, pip-audit, detect-secrets, gitleaks, etc.)
  - `.secrets.baseline` for secret detection
  - Custom secret scanner script (`scripts/scan_secrets.sh`)
  - Security audit report (SECURITY_AUDIT_COMPLETE.md)
- Documentation consolidation ([#docs](https://github.com/JuanCS-Dev/V-rtice))
  - Installation guide (docs/installation.md)
  - LLM configuration guide (docs/llm-configuration.md)
  - Deployment guide (DEPLOYMENT.md with Vercel/Netlify/Cloudflare)
  - Consolidated 67+ docs into organized structure (9 categories)
- Dashboard visualization assets ([#assets](https://github.com/JuanCS-Dev/V-rtice))
  - 4 dashboard screenshots (Consciousness, Offensive, Defensive, Neural Architecture)
  - Logo and favicons (16x16, 32x32, 180x180, 1024x1024)
  - Open Graph image (1200x630) for social media sharing

### Changed
- **BREAKING:** Updated LICENSE from proprietary to Apache 2.0 ([#license](https://github.com/JuanCS-Dev/V-rtice))
  - Enables GitHub Sponsors eligibility
  - Allows commercial use with attribution
  - Includes patent protection
- README completely rewritten with biological organism metaphor ([#readme](https://github.com/JuanCS-Dev/V-rtice))
  - Position as "living organism" vs traditional software
  - Immune system comparison table (body vs Vértice)
  - 9-layer biological defense cascade documentation
  - Comprehensive offensive security legal disclaimers
- Attribution and contact information updated across all files ([#attribution](https://github.com/JuanCS-Dev/V-rtice))
  - Author: Juan Carlos de Souza
  - Contact: juan@vertice-maximus.com
  - GitHub: JuanCS-Dev/V-rtice
- Repository organization and cleanup ([#cleanup](https://github.com/JuanCS-Dev/V-rtice))
  - Moved 10+ scripts from root to organized directories (testing/, validation/, maintenance/, utilities/)
  - Removed 5 backup files (*.sh.backup, *.sh.old)
  - Removed production logs from git tracking
  - Updated .gitignore to prevent future log commits
- Landing page styling improvements ([#style](https://github.com/JuanCS-Dev/V-rtice))
  - Buy Me A Coffee button colors to red theme (#FF5F5F) for better visibility
  - Social media icons now render correctly in footer
  - Removed carousel captions for cleaner visual

### Fixed
- Social media icons not showing in footer (changed from `<span set:html>` to direct `set:html` on `<a>` tag)
- Python version in pre-commit config (fixed to Python 3.11)
- DNS resolution in air-gapped environments (fix_dns_air_gap.sh script)

### Security
- **[AUDIT COMPLETE]** Full security audit for public release ([#audit](https://github.com/JuanCS-Dev/V-rtice))
  - Scanned 37,866+ files across entire codebase
  - **0 real API keys found** (Claude, OpenAI, Google, AWS all clean)
  - **0 real private keys found** (9 false positives - honeypot/test code)
  - **0 production secrets found** (30 false positives - dev/test defaults)
  - **Repository is CLEAN and SAFE for public release**
- Pre-commit hooks active with 15+ security checks
- Secret scanning baseline established (`.secrets.baseline`)
- Git history verified clean (no secrets in history)

### Removed
- Scattered documentation from root/frontend/landing (consolidated into docs/)
- AI assistant private files from git tracking (.claude/DOUTRINA, .gemini/*)
- Coverage files from all services (remain locally, not in repository)
- Backup and old script files (*.sh.backup, *.sh.old, maximus_v2_old.sh)
- Production logs (log_producao_*.txt, 5 files deleted)
- SVG placeholder code (replaced with real dashboard screenshot)

---

## [1.0.0] - YYYY-MM-DD (To be released)

### Summary
First public release of Vértice-MAXIMUS - the world's first autonomous cybersecurity platform with biological immune system architecture.

**Key Features:**
- 125+ specialized microservices (immune cells)
- 9-layer biological defense cascade
- 99.73% test coverage on core modules
- 574+ unit tests
- Multi-agent AI consciousness (MAXIMUS)
- Purple team orchestration (offensive + defensive)
- Multi-LLM support (Claude, OpenAI, Gemini)
- Apache 2.0 license (enterprise-friendly)
- Comprehensive legal compliance (US, Brazil, EU)
- NEUROSHELL natural language command interface
- Docker/Kubernetes deployment
- Professional documentation and community standards

**Target Audience:**
- SOC analysts and security engineers
- DevSecOps teams
- Cybersecurity researchers
- Penetration testers (authorized)
- CISO and security leaders
- AI/ML security specialists

**Success Metrics:**
- 99.73% test coverage (tegumentar module)
- 574+ tests with 97.7% pass rate
- 95 operational backend services
- 125+ microservices in ecosystem
- 37,866 AI cognitive files (MAXIMUS core)
- 67+ documentation files organized

### Attribution
- **Architecture & Vision**: Juan Carlos de Souza
- **Biblical Inspiration**: John 9:25, Holy Bible
- **Execution & Documentation**: Built with [Claude Code](https://claude.com/claude-code) by Anthropic

---

## Version History

- **v1.0.0** - First public release (upcoming)
- **Pre-1.0** - Private development (September 2025 - October 2025)

---

## Links

- [Repository](https://github.com/JuanCS-Dev/V-rtice)
- [Documentation](https://vertice-maximus.web.app)
- [npm Package](https://www.npmjs.com/package/vertice-maximus)
- [GitHub Sponsors](https://github.com/sponsors/JuanCS-Dev)
- [Buy Me A Coffee](https://buymeacoffee.com/vertice)
- [Contact](mailto:juan@vertice-maximus.com)

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to contribute to Vértice-MAXIMUS.

## Security

See [SECURITY.md](./SECURITY.md) for vulnerability reporting process and security policy.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](./LICENSE) file for details.
