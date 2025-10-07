# 🤝 Contributing to vCLI 2.0

**Welcome!** We're thrilled you're interested in contributing to vCLI 2.0.

This guide will help you get started with contributing code, documentation, or ideas.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contribution Workflow](#contribution-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)
9. [Community](#community)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability
- Ethnicity, gender identity
- Experience level
- Nationality, personal appearance
- Race, religion
- Sexual identity and orientation

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Respecting differing viewpoints
- Accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy

**Unacceptable behaviors:**
- Trolling, insulting comments
- Public or private harassment
- Publishing others' private information
- Conduct inappropriate in a professional setting

### Enforcement

Violations may be reported to conduct@vertice.dev. All complaints will be reviewed and investigated confidentially.

---

## Getting Started

### Ways to Contribute

1. **Code Contributions**
   - Bug fixes
   - New features
   - Performance improvements
   - Refactoring

2. **Documentation**
   - Improve existing docs
   - Write tutorials
   - Create examples
   - Translate documentation

3. **Testing**
   - Write test cases
   - Report bugs
   - Verify fixes

4. **Community**
   - Answer questions
   - Help newcomers
   - Write blog posts
   - Give talks

### Good First Issues

Look for issues labeled:
- `good-first-issue` - Perfect for newcomers
- `help-wanted` - We need community help
- `documentation` - Documentation improvements

---

## Development Setup

### Prerequisites

```bash
# Install Go 1.21+
go version  # Should be 1.21 or higher

# Install development tools
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install github.com/securego/gosec/v2/cmd/gosec@latest
go install github.com/cosmtrek/air@latest  # For live reload
```

### Fork and Clone

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/vcli-go.git
cd vcli-go

# 3. Add upstream remote
git remote add upstream https://github.com/verticedev/vcli-go.git

# 4. Verify remotes
git remote -v
```

### Install Dependencies

```bash
# Download dependencies
go mod download

# Verify build works
make build

# Run tests
make test
```

### Set Up IDE

#### VS Code

Install extensions:
- Go (`golang.go`)
- Go Test Explorer
- Error Lens

**Settings (.vscode/settings.json):**

```json
{
  "go.useLanguageServer": true,
  "go.lintTool": "golangci-lint",
  "go.lintOnSave": "workspace",
  "go.formatTool": "goimports",
  "editor.formatOnSave": true,
  "go.testFlags": ["-v", "-race"]
}
```

#### GoLand / IntelliJ

1. Open project
2. Enable Go Modules integration
3. Configure golangci-lint
4. Set up run configurations

---

## Contribution Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-awesome-feature

# Or for bugfix
git checkout -b fix/bug-description
```

**Branch Naming Convention:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `perf/` - Performance improvements

### 2. Make Changes

```bash
# Edit files
# ...

# Check status
git status

# View changes
git diff
```

### 3. Test Locally

```bash
# Run tests
make test

# Run linter
make lint

# Run security scan
make security

# Full CI pipeline
make ci
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add workspace switching with Ctrl+W

- Implement keyboard shortcut for quick workspace navigation
- Add WorkspaceSwitchMsg to MVU update cycle
- Update documentation with new shortcut
- Add tests for workspace switching logic

Closes #123"
```

**Commit Message Format:**

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `refactor` - Code refactoring
- `test` - Test improvements
- `perf` - Performance improvement
- `chore` - Maintenance tasks
- `ci` - CI/CD changes

**Examples:**

```
feat: add plugin health monitoring

- Implement periodic health checks for loaded plugins
- Add health status to plugin info
- Update UI to show plugin health indicators

Closes #456
```

```
fix: prevent race condition in state management

Use RWMutex for thread-safe access to plugin map.

Fixes #789
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/my-awesome-feature

# Create Pull Request on GitHub
```

---

## Coding Standards

### REGRA DE OURO (Golden Rule)

Our project follows the **REGRA DE OURO**:

1. **NO MOCKS** - Use real implementations or interfaces
2. **NO PLACEHOLDERS** - Complete implementations only
3. **NO TODOs** - Finish work before committing
4. **QUALITY FIRST** - Primoroso code quality

### Go Code Style

#### Formatting

```bash
# Format code (automatic with gofmt)
go fmt ./...

# Organize imports (automatic with goimports)
goimports -w .
```

#### Naming Conventions

```go
// Package names: lowercase, no underscores
package core

// Exported: PascalCase
type PluginManager struct {}
func NewPluginManager() *PluginManager {}

// Unexported: camelCase
func processEvent() {}
var internalState = 0

// Constants: PascalCase or SCREAMING_SNAKE_CASE
const MaxRetries = 3
const DEFAULT_TIMEOUT = 30
```

#### Error Handling

```go
// GOOD: Return errors, don't panic
func LoadPlugin(path string) error {
    if _, err := os.Stat(path); err != nil {
        return fmt.Errorf("plugin file not found: %w", err)
    }
    return nil
}

// BAD: Don't use panic for normal errors
func LoadPlugin(path string) {
    if _, err := os.Stat(path); err != nil {
        panic(err)  // ❌ Don't do this
    }
}

// GOOD: Wrap errors with context
if err := plugin.Initialize(ctx); err != nil {
    return fmt.Errorf("failed to initialize plugin %s: %w", name, err)
}
```

#### Comments and Documentation

```go
// Package-level comment
// Package core provides state management and business logic
// for the vCLI application following the MVU pattern.
package core

// Exported functions: GoDoc comment
// LoadPlugin loads a plugin from the specified path and initializes it.
// Returns an error if the plugin cannot be loaded or initialized.
//
// Example:
//   err := LoadPlugin("/path/to/plugin.so")
//   if err != nil {
//       log.Fatal(err)
//   }
func LoadPlugin(path string) error {
    // Implementation...
}

// Unexported functions: brief comment
// processEvent handles incoming events and updates state
func processEvent(event Event) {}
```

### Code Organization

```go
// Order of declarations in a file:
package core

// 1. Imports (grouped: stdlib, external, internal)
import (
    "context"
    "time"

    "github.com/external/package"

    "github.com/verticedev/vcli-go/pkg/types"
)

// 2. Constants
const (
    DefaultTimeout = 30 * time.Second
    MaxRetries     = 3
)

// 3. Variables
var (
    globalState *State
)

// 4. Types
type State struct {
    // fields...
}

// 5. Constructors
func NewState() *State {
    return &State{}
}

// 6. Methods (receiver order: value receivers, then pointer receivers)
func (s State) GetVersion() string {}
func (s *State) SetVersion(v string) {}

// 7. Functions
func ProcessEvent(event Event) error {}
```

---

## Testing Guidelines

### Test File Structure

```go
package core

import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/suite"
)

// Test suite
type StateSuite struct {
    suite.Suite
    state *State
}

// Setup
func (s *StateSuite) SetupTest() {
    s.state = NewState("1.0.0")
}

// Teardown
func (s *StateSuite) TearDownTest() {
    s.state = nil
}

// Test cases
func (s *StateSuite) TestStateCreation() {
    assert.NotNil(s.T(), s.state)
    assert.Equal(s.T(), "1.0.0", s.state.Version)
}

// Run suite
func TestStateSuite(t *testing.T) {
    suite.Run(t, new(StateSuite))
}
```

### Test Coverage

**Minimum Requirements:**
- Core packages: **80%+ coverage**
- TUI components: **70%+ coverage**
- Plugins: **70%+ coverage**

```bash
# Check coverage
make coverage

# View in browser
go tool cover -html=coverage.out
```

### Benchmarks

```go
func BenchmarkStateUpdate(b *testing.B) {
    state := NewState("1.0.0")
    b.ResetTimer()

    for i := 0; i < b.N; i++ {
        state.SetActiveWorkspace("test")
    }
}
```

### Table-Driven Tests

```go
func TestPluginValidation(t *testing.T) {
    tests := []struct {
        name    string
        plugin  string
        wantErr bool
    }{
        {"valid plugin", "kubernetes", false},
        {"empty name", "", true},
        {"invalid chars", "plugin@123", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidatePluginName(tt.plugin)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

---

## Documentation

### Code Documentation

```go
// Package documentation
// Package core provides state management following MVU pattern.
//
// The core package implements:
//   - Thread-safe state management
//   - Action dispatching
//   - Event handling
//
// Example:
//   state := core.NewState("1.0.0")
//   state.LoadPlugin("kubernetes", "1.0.0")
package core
```

### Markdown Documentation

- Use clear headings
- Include code examples
- Add diagrams where helpful
- Link to related docs

### README Updates

Update README.md when adding:
- New features
- New commands
- Breaking changes
- Configuration options

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Linter passing (`make lint`)
- [ ] Security scan clean (`make security`)
- [ ] No merge conflicts with main

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Changes Made
- List key changes
- Be specific

## Testing
Describe testing performed:
- Unit tests added
- Integration tests updated
- Manual testing steps

## Checklist
- [ ] Code follows project style
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Tests added and passing
- [ ] Dependent changes merged

## Screenshots (if applicable)

## Related Issues
Closes #123
Relates to #456
```

### Review Process

1. **Automated Checks** - CI/CD must pass
2. **Code Review** - At least one approval required
3. **Testing** - Reviewers may test locally
4. **Approval** - Maintainer approval needed
5. **Merge** - Squash and merge to main

### After Merge

- Branch will be automatically deleted
- Release notes may be updated
- Documentation deployed

---

## Community

### Communication Channels

- **GitHub Discussions** - General questions, ideas
- **GitHub Issues** - Bug reports, feature requests
- **Discord** - Real-time chat (link in README)
- **Twitter** - Announcements (@verticedev)

### Getting Help

- Check [Getting Started](getting-started.md)
- Search existing issues
- Ask in Discussions
- Join Discord

### Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor events

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

- **Email:** contribute@vertice.dev
- **Discord:** [Join our server](https://discord.gg/vertice)
- **Discussions:** [GitHub Discussions](https://github.com/verticedev/vcli-go/discussions)

---

**Thank you for contributing to vCLI 2.0!** 🚀

Together, we're building the future of cybersecurity operations.

---

**Version:** 1.0 | **Last Updated:** 2025-01-06
