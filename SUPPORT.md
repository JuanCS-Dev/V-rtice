# Support

Need help with Vértice-MAXIMUS? You've come to the right place!

## 📚 First Steps: Self-Service Resources

Before reaching out for help, check if your question is already answered:

### Documentation
- **[Official Documentation](https://vertice-maximus.web.app)** - Comprehensive guides and references
- **[README.md](./README.md)** - Quick start and overview
- **[Installation Guide](./docs/installation.md)** - Detailed setup instructions
- **[LLM Configuration](./docs/llm-configuration.md)** - Multi-LLM setup (Claude, OpenAI, Gemini)
- **[Architecture Guide](./docs/01-ARCHITECTURE/)** - Understanding the biological immune system

### Common Resources
- **[FAQ](#frequently-asked-questions)** - Common questions answered below
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions
- **[Existing Issues](https://github.com/JuanCS-Dev/V-rtice/issues?q=is%3Aissue)** - Search for similar problems

---

## 💬 Community Support

### GitHub Discussions (Recommended)
Our primary community forum for questions, ideas, and discussions.

👉 **[Start a Discussion](https://github.com/JuanCS-Dev/V-rtice/discussions)**

**When to use:**
- ✅ General questions about Vértice
- ✅ Architecture and design discussions
- ✅ Feature ideas and suggestions
- ✅ Sharing use cases and success stories
- ✅ Getting advice from the community

**Response Time:** Community-driven, typically 24-48 hours

---

### GitHub Issues
For bugs, feature requests, and security issues.

👉 **[Create an Issue](https://github.com/JuanCS-Dev/V-rtice/issues/new/choose)**

**Issue Types:**
- 🐛 **Bug Report** - Something isn't working
- ✨ **Feature Request** - Suggest a new feature
- 🔒 **Security** - Low-severity security concerns (HIGH/CRITICAL → email)
- ❓ **Question** - Specific technical questions

**Response Time:**
- **Bugs (Critical):** Within 24 hours
- **Bugs (Non-Critical):** Within 3-5 days
- **Feature Requests:** Reviewed monthly
- **Questions:** Within 2-3 days

---

## 📧 Direct Contact

### General Inquiries
For general questions, partnerships, or non-technical matters:

📧 **[juan@vertice-maximus.com](mailto:juan@vertice-maximus.com)**

**Response Time:** 2-3 business days

### Security Vulnerabilities
For **CRITICAL** security issues requiring private disclosure:

🔒 **[security@vertice-maximus.com](mailto:security@vertice-maximus.com)**

**⚠️ DO NOT create public issues for critical vulnerabilities!**

See our [Security Policy](./SECURITY.md) for responsible disclosure process.

**Response Time:**
- Initial response: Within 48 hours
- Status update: Within 7 days
- Fix timeline: Depends on severity (critical issues prioritized)

---

## 🚨 What NOT to Do

**❌ DON'T:**
- Open duplicate issues (search first!)
- Share API keys, passwords, or sensitive information in issues
- Use issues for general questions (use Discussions instead)
- Report critical security vulnerabilities publicly
- Demand immediate responses (we're a community project)
- Be rude or disrespectful to maintainers or contributors

**✅ DO:**
- Search existing issues and discussions first
- Provide complete information (version, OS, logs, steps to reproduce)
- Be patient and respectful
- Follow our [Code of Conduct](./CODE_OF_CONDUCT.md)
- Read the [Contributing Guide](./CONTRIBUTING.md) before submitting PRs

---

## ⏱️ Expected Response Times

| Channel | Response Time | Who Responds |
|---------|---------------|--------------|
| GitHub Discussions | 24-48 hours | Community + Maintainers |
| Bug Reports (Critical) | Within 24 hours | Maintainers |
| Bug Reports (Non-Critical) | 3-5 days | Maintainers |
| Feature Requests | Monthly review | Maintainers |
| Questions (GitHub) | 2-3 days | Community + Maintainers |
| Email (General) | 2-3 business days | Maintainers |
| Email (Security) | Within 48 hours | Security Team |

**Note:** These are targets, not guarantees. Vértice-MAXIMUS is an open-source project maintained by volunteers. Complex issues may take longer.

---

## ❓ Frequently Asked Questions

### Installation & Setup

**Q: What are the system requirements?**
A: See [Installation Guide](./docs/installation.md) for detailed requirements. Minimum:
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- 8GB RAM recommended
- LLM API key (Claude, OpenAI, Gemini, or compatible)

**Q: Which LLM should I use?**
A: See [LLM Configuration Guide](./docs/llm-configuration.md). Recommended:
- **Claude (Anthropic):** Best for consciousness/reasoning (MAXIMUS AI)
- **OpenAI GPT-4:** Good balance of cost and capability
- **Gemini:** Cost-effective option with good performance
- **Custom/Local:** For air-gapped or privacy-sensitive environments

**Q: Can I run Vértice without an LLM API key?**
A: No. MAXIMUS AI (consciousness layer) requires an LLM. However, you can use local models with compatible APIs (e.g., Ollama, LM Studio with OpenAI-compatible endpoints).

### Architecture & Concepts

**Q: What does "biological immune system architecture" mean?**
A: Vértice mimics how your body fights infections. Instead of static rules, it has 9 adaptive layers (like skin, white blood cells, antibodies) that learn, remember, and evolve against threats. See [Architecture Guide](./docs/01-ARCHITECTURE/).

**Q: What is MAXIMUS AI?**
A: MAXIMUS is the "consciousness" layer (Layer 9) - the meta-cognitive overseer that coordinates all 125+ microservices, profiles threat actors, and makes strategic decisions. Think of it as the "brain" of the organism.

**Q: What are "immune cells" / "microservices"?**
A: The 125+ specialized services that act like biological immune cells:
- Neutrophils (fast detectors)
- Macrophages (deep analyzers)
- Dendritic cells (threat intel)
- T-cells (coordinators)
- Etc.

### Offensive Security & Legal

**Q: Can I use Vértice-MAXIMUS for penetration testing?**
A: **YES, but ONLY with explicit written authorization from system owners.** See our comprehensive legal disclaimer in [README.md](./README.md) covering US (CFAA), Brazil (Lei 12.737), and EU (GDPR) laws. Unauthorized use is a **federal crime** in most jurisdictions.

**Q: Is Vértice legal to use?**
A: Yes, for **authorized use cases**: pentesting (with permission), security research, CTFs, defensive security, bug bounties. **Illegal** for: unauthorized access, data exfiltration, DoS attacks, malicious use. See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) and [CONTRIBUTING.md](./CONTRIBUTING.md).

**Q: What offensive capabilities does Vértice have?**
A: C2 orchestration, automated pentesting, exploit frameworks, OSINT gathering, vulnerability scanning. **All require explicit authorization before use.** See legal disclaimer.

### Usage & Configuration

**Q: How do I configure NEUROSHELL (natural language commands)?**
A: NEUROSHELL is available via the CLI after setup:
```bash
vertice neuroshell
# Then type natural language commands like:
> "show me all https traffic from suspicious IPs"
> "block traffic from 192.168.1.100"
```

**Q: Can I run Vértice in an air-gapped environment?**
A: Partially. You'll need:
- Local LLM with OpenAI-compatible API (Ollama, LM Studio, etc.)
- All dependencies pre-downloaded
- Threat intelligence feeds (if applicable) manually updated
See [Air-Gapped Deployment Guide](./docs/06-DEPLOYMENT/air-gapped.md) (if available).

**Q: How do I update Vértice-MAXIMUS?**
A:
```bash
# Via npm (if installed globally)
npm update -g vertice-maximus

# Via git (if cloned)
cd /path/to/V-rtice
git pull origin main
docker-compose pull  # Update containers
vertice restart
```

### Performance & Scalability

**Q: How many resources does Vértice need?**
A:
- **Minimum (testing):** 4 CPU cores, 8GB RAM, 50GB disk
- **Recommended (production):** 8+ CPU cores, 16GB+ RAM, 100GB+ disk
- **Enterprise (full stack):** 16+ CPU cores, 32GB+ RAM, 500GB+ disk, Kubernetes cluster

**Q: Can Vértice scale horizontally?**
A: Yes. Microservices can be deployed across multiple nodes using Kubernetes. See [Kubernetes Deployment Guide](./docs/06-DEPLOYMENT/).

### Community & Contribution

**Q: How can I contribute?**
A: See [CONTRIBUTING.md](./CONTRIBUTING.md). Ways to contribute:
- Code (new features, bug fixes)
- Documentation
- Testing and bug reports
- Community support (answering questions)
- Security research (responsibly!)

**Q: I found a bug. What do I do?**
A: Create a **[Bug Report](https://github.com/JuanCS-Dev/V-rtice/issues/new/choose)** with:
- Steps to reproduce
- Expected vs actual behavior
- Logs (remove sensitive info!)
- Environment details (OS, versions)

---

## 🔧 Troubleshooting

### Common Issues

**Issue: `vertice: command not found`**
- **Solution:** Install globally: `npm install -g vertice-maximus` or add to PATH

**Issue: Docker containers fail to start**
- **Solution:**
  1. Check Docker is running: `docker info`
  2. Check ports aren't in use: `netstat -tulpn | grep LISTEN`
  3. Check logs: `docker-compose logs -f`

**Issue: LLM API returns 401/403 errors**
- **Solution:**
  1. Verify API key is correct in `.env`
  2. Check API key has required permissions
  3. Verify account has credits/quota

**Issue: High memory usage**
- **Solution:**
  1. Check which services are memory-heavy: `docker stats`
  2. Adjust Docker resource limits in `docker-compose.yml`
  3. Disable unused microservices in configuration

**Issue: Slow response times**
- **Solution:**
  1. Check LLM API latency (Claude/OpenAI status pages)
  2. Verify network connectivity
  3. Check if caching (Redis) is working
  4. Consider upgrading LLM plan for faster response

### Getting Detailed Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f maximus_core_service

# Backend logs
tail -f backend/logs/vertice.log

# Frontend logs
tail -f frontend/logs/access.log
```

---

## 💖 Support the Project

If Vértice-MAXIMUS helps protect your infrastructure, consider supporting development:

- ☕ **[Buy Me A Coffee](https://buymeacoffee.com/vertice)** - Keep MAXIMUS consciousness online
- 💖 **[GitHub Sponsors](https://github.com/sponsors/JuanCS-Dev)** - Recurring support
- ⭐ **Star the Repository** - Show appreciation and boost visibility
- 📢 **Share** - Tell others about Vértice

Every coffee = ~10,000 tokens = 2 hours of MAXIMUS thinking! 🧠☕

---

## 📞 Contact Information

- **General Inquiries:** [juan@vertice-maximus.com](mailto:juan@vertice-maximus.com)
- **Security:** [security@vertice-maximus.com](mailto:security@vertice-maximus.com)
- **Website:** [https://vertice-maximus.web.app](https://vertice-maximus.web.app)
- **GitHub:** [https://github.com/JuanCS-Dev/V-rtice](https://github.com/JuanCS-Dev/V-rtice)

---

## 🙏 Thank You

Thank you for using Vértice-MAXIMUS and being part of our community!

Remember: Vértice is not just software—it's a living organism. Treat it well, and it will evolve to protect you better. 🧬

*"Before I formed you in the womb I knew you."* - John 9:25, Holy Bible
