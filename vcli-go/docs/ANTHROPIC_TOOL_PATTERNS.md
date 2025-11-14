# 🔧 ANTHROPIC TOOL AVAILABILITY PATTERNS - VCLI-GO

**Date**: 2025-11-14
**Project**: vCLI 2.0
**Purpose**: External tool checking and graceful degradation patterns
**Mode**: Boris Cherny - Production Quality Standards

---

## 📋 EXECUTIVE SUMMARY

This document synthesizes:
1. **Pre-flight validation** patterns (Kubernetes, AWS)
2. **Graceful degradation** strategies (2025 best practices)
3. **CLI tool availability** checking patterns
4. **User experience** for missing dependencies

**Key Principle**: "Transform hard dependencies into soft dependencies" - AWS Well-Architected

**Goal**: CLI continues functioning even when optional tools are missing

---

## 🏗️ PRE-FLIGHT VALIDATION PATTERNS

### Pattern 1: Early Validation Chain ✅

**Philosophy**: Validate environment BEFORE attempting operations

```go
// Pre-flight check interface (inspired by Kubernetes kubeadm)
type PreflightChecker interface {
    Name() string
    Check() error
}

type PreflightCheck struct {
    name    string
    checkFn func() error
}

func (c *PreflightCheck) Name() string {
    return c.name
}

func (c *PreflightCheck) Check() error {
    return c.checkFn()
}

// Run all pre-flight checks
func RunPreflightChecks(checks []PreflightChecker) error {
    var failures []string

    for _, check := range checks {
        if err := check.Check(); err != nil {
            failures = append(failures, fmt.Sprintf("%s: %v", check.Name(), err))
        }
    }

    if len(failures) > 0 {
        return fmt.Errorf("pre-flight checks failed:\n  - %s",
            strings.Join(failures, "\n  - "))
    }

    return nil
}
```

**Usage**:
```go
func main() {
    checks := []PreflightChecker{
        &PreflightCheck{
            name: "Go toolchain",
            checkFn: func() error {
                _, err := exec.LookPath("go")
                return err
            },
        },
        &PreflightCheck{
            name: "Home directory",
            checkFn: func() error {
                _, err := os.UserHomeDir()
                return err
            },
        },
    }

    if err := RunPreflightChecks(checks); err != nil {
        fmt.Fprintf(os.Stderr, "❌ %v\n", err)
        os.Exit(1)
    }

    // Proceed with main logic
}
```

---

### Pattern 2: Tool Registry with Lazy Loading ✅

**Philosophy**: Check tools only when needed, cache results

```go
package tools

import (
    "os/exec"
    "sync"
)

type Tool struct {
    Name         string
    Required     bool               // Hard vs. soft dependency
    Severity     errors.Severity
    InstallCmd   string
    CheckCmd     []string           // Custom verification command
}

type Checker struct {
    tools map[string]Tool
    cache map[string]bool
    mu    sync.RWMutex
}

func NewChecker() *Checker {
    return &Checker{
        tools: make(map[string]Tool),
        cache: make(map[string]bool),
    }
}

// Register registers a tool for checking
func (c *Checker) Register(tool Tool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.tools[tool.Name] = tool
}

// Check performs lazy check with caching
func (c *Checker) Check(toolName string) error {
    c.mu.RLock()
    tool, exists := c.tools[toolName]
    c.mu.RUnlock()

    if !exists {
        return fmt.Errorf("tool %s not registered", toolName)
    }

    // Check cache first
    c.mu.RLock()
    if available, cached := c.cache[toolName]; cached {
        c.mu.RUnlock()
        if available {
            return nil
        }
        return c.toolNotFoundError(tool)
    }
    c.mu.RUnlock()

    // Perform actual check
    available := c.checkToolAvailability(tool)

    // Cache result
    c.mu.Lock()
    c.cache[toolName] = available
    c.mu.Unlock()

    if !available {
        return c.toolNotFoundError(tool)
    }

    return nil
}

func (c *Checker) checkToolAvailability(tool Tool) bool {
    // Method 1: exec.LookPath (fastest)
    if _, err := exec.LookPath(tool.Name); err == nil {
        return true
    }

    // Method 2: Custom check command (if specified)
    if len(tool.CheckCmd) > 0 {
        cmd := exec.Command(tool.CheckCmd[0], tool.CheckCmd[1:]...)
        if err := cmd.Run(); err == nil {
            return true
        }
    }

    return false
}

func (c *Checker) toolNotFoundError(tool Tool) error {
    return &errors.ToolError{
        Tool:         tool.Name,
        Err:          errors.ErrToolNotFound,
        Severity:     tool.Severity,
        InstallGuide: tool.InstallCmd,
    }
}
```

**Benefits**:
- ✅ Lazy evaluation (check only when used)
- ✅ Caching prevents redundant checks
- ✅ Thread-safe
- ✅ Custom verification commands
- ✅ Severity-aware

---

## 🎯 GRACEFUL DEGRADATION STRATEGIES

### Strategy 1: Hard vs. Soft Dependencies ✅

**Philosophy**: Distinguish between required and optional tools

```go
// Dependency classification
const (
    DependencyRequired = iota  // Hard: Cannot function without
    DependencyOptional         // Soft: Can degrade gracefully
    DependencyNiceToHave       // Enhancement: Better UX but not needed
)

type Dependency struct {
    Name       string
    Type       int
    Fallback   string  // What happens when missing
}

// Example classification
var dependencies = []Dependency{
    {
        Name:     "go",
        Type:     DependencyRequired,
        Fallback: "Cannot compile code",
    },
    {
        Name:     "kubectl",
        Type:     DependencyOptional,
        Fallback: "K8s commands unavailable",
    },
    {
        Name:     "gosec",
        Type:     DependencyOptional,
        Fallback: "Security scanning skipped",
    },
    {
        Name:     "black",
        Type:     DependencyNiceToHave,
        Fallback: "Python code unformatted",
    },
}
```

---

### Strategy 2: Capability Detection ✅

**Philosophy**: CLI detects terminal capabilities and adjusts

```go
package capabilities

import (
    "os"
    "github.com/mattn/go-isatty"
)

type Capabilities struct {
    Interactive  bool
    ColorSupport bool
    Unicode      bool
    ToolsAvailable map[string]bool
}

func Detect(checker *tools.Checker) *Capabilities {
    caps := &Capabilities{
        ToolsAvailable: make(map[string]bool),
    }

    // Terminal detection
    caps.Interactive = isatty.IsTerminal(os.Stdout.Fd())

    // Color support
    term := os.Getenv("TERM")
    caps.ColorSupport = term != "dumb" && caps.Interactive

    // Unicode support (check LANG)
    lang := os.Getenv("LANG")
    caps.Unicode = strings.Contains(strings.ToLower(lang), "utf")

    // Tool availability
    for _, toolName := range []string{"kubectl", "gosec", "black", "pytest"} {
        caps.ToolsAvailable[toolName] = (checker.Check(toolName) == nil)
    }

    return caps
}

// Adapt output based on capabilities
func (c *Capabilities) Spinner() string {
    if c.Unicode {
        return "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"  // Unicode spinner
    }
    return "|/-\\"  // ASCII spinner
}

func (c *Capabilities) Checkmark() string {
    if c.Unicode {
        return "✓"
    }
    return "[OK]"
}

func (c *Capabilities) ErrorMark() string {
    if c.Unicode {
        return "✗"
    }
    return "[ERR]"
}
```

**Usage**:
```go
func main() {
    checker := tools.DefaultRegistry
    caps := capabilities.Detect(checker)

    if caps.Interactive {
        fmt.Printf("%s Starting operation...\n", caps.Spinner()[0:1])
    } else {
        fmt.Println("Starting operation...")  // Non-interactive
    }

    if !caps.ToolsAvailable["kubectl"] {
        fmt.Printf("%s kubectl unavailable - K8s features disabled\n",
            caps.ErrorMark())
    }
}
```

---

### Strategy 3: Fallback Chains ✅

**Philosophy**: Try primary tool, fall back to alternatives

```go
// Formatter with fallback chain
type Formatter interface {
    Format(code string) (string, error)
    Name() string
}

type PythonFormatter struct {
    checker *tools.Checker
}

func (f *PythonFormatter) Format(code string) (string, error) {
    // Try black (preferred)
    if err := f.checker.Check("black"); err == nil {
        return f.formatWithBlack(code)
    }

    // Try autopep8 (fallback)
    if err := f.checker.Check("autopep8"); err == nil {
        return f.formatWithAutopep8(code)
    }

    // Last resort: return unformatted with warning
    fmt.Fprintf(os.Stderr, "⚠️  No Python formatters available\n")
    fmt.Fprintf(os.Stderr, "   Install: pip install black autopep8\n")

    return code, fmt.Errorf("formatters unavailable, returning unformatted code")
}

func (f *PythonFormatter) formatWithBlack(code string) (string, error) {
    cmd := exec.Command("black", "--quiet", "--code", code)
    output, err := cmd.CombinedOutput()
    if err != nil {
        return "", fmt.Errorf("black failed: %w", err)
    }
    return string(output), nil
}

func (f *PythonFormatter) formatWithAutopep8(code string) (string, error) {
    cmd := exec.Command("autopep8", "--aggressive", "--aggressive", "-")
    cmd.Stdin = strings.NewReader(code)
    output, err := cmd.CombinedOutput()
    if err != nil {
        return "", fmt.Errorf("autopep8 failed: %w", err)
    }
    return string(output), nil
}
```

**Fallback Chain Visualization**:
```
┌──────────┐
│  black   │ ─── Available? ──> Format code ──> Success ✓
└──────────┘          │
                      No
                      ↓
                ┌──────────┐
                │autopep8  │ ─── Available? ──> Format code ──> Success ✓
                └──────────┘          │
                                      No
                                      ↓
                                ┌──────────┐
                                │Unformatted│ ─── Warning ──> Return original
                                └──────────┘
```

---

### Strategy 4: Feature Flags for Degradation ✅

**Philosophy**: Explicitly disable features when tools missing

```go
type Features struct {
    KubernetesOps    bool
    SecurityScanning bool
    PythonFormatting bool
    GoLinting        bool
}

func DetectFeatures(checker *tools.Checker) *Features {
    return &Features{
        KubernetesOps:    checker.Check("kubectl") == nil,
        SecurityScanning: checker.Check("gosec") == nil,
        PythonFormatting: checker.Check("black") == nil || checker.Check("autopep8") == nil,
        GoLinting:        checker.Check("golangci-lint") == nil,
    }
}

// Command availability based on features
func (f *Features) AvailableCommands() []string {
    commands := []string{"version", "help"}  // Always available

    if f.KubernetesOps {
        commands = append(commands, "k8s")
    }

    if f.SecurityScanning {
        commands = append(commands, "scan")
    }

    return commands
}

// Usage in CLI
func registerCommands(rootCmd *cobra.Command, features *Features) {
    if features.KubernetesOps {
        rootCmd.AddCommand(k8sCmd)
    } else {
        // Register stub command with helpful error
        k8sStub := &cobra.Command{
            Use:   "k8s",
            Short: "Kubernetes operations (kubectl required)",
            RunE: func(cmd *cobra.Command, args []string) error {
                return fmt.Errorf("kubectl not found - install: https://kubernetes.io/docs/tasks/tools/")
            },
        }
        rootCmd.AddCommand(k8sStub)
    }
}
```

---

## 📊 USER EXPERIENCE PATTERNS

### Pattern 3: Clear Status Reporting ✅

**Philosophy**: Users must know what's available

```go
// vcli doctor command - health check
func runDoctor(cmd *cobra.Command, args []string) error {
    checker := tools.DefaultRegistry
    styles := visual.NewStyles()

    fmt.Println(styles.Header.Render("🏥 VCLI Health Check"))
    fmt.Println()

    categories := map[string][]string{
        "Core Tools": {"go", "git"},
        "Python Ecosystem": {"python3", "pytest", "black", "autopep8"},
        "Go Ecosystem": {"gosec", "golangci-lint"},
        "Infrastructure": {"kubectl"},
    }

    allOK := true

    for category, toolNames := range categories {
        fmt.Printf("%s\n", styles.Subheader.Render(category))

        for _, toolName := range toolNames {
            err := checker.Check(toolName)

            if err == nil {
                fmt.Printf("  %s %s\n",
                    styles.Success.Render("✓"),
                    toolName)
            } else {
                allOK = false

                var toolErr *errors.ToolError
                if errors.As(err, &toolErr) {
                    icon := "⚠️"
                    if toolErr.Severity == errors.SeverityFatal {
                        icon = "❌"
                    }

                    fmt.Printf("  %s %s\n",
                        icon,
                        styles.Error.Render(toolName+" - not found"))

                    if toolErr.InstallGuide != "" {
                        fmt.Printf("    %s\n",
                            styles.Info.Render("Install: "+toolErr.InstallGuide))
                    }
                }
            }
        }
        fmt.Println()
    }

    // Summary
    if allOK {
        fmt.Println(styles.Success.Render("✅ All tools available"))
        return nil
    }

    fmt.Println(styles.Warning.Render("⚠️  Some tools missing - reduced functionality"))
    fmt.Println()
    fmt.Println("Run 'vcli doctor' anytime to check tool status")

    return nil  // Not an error - informational
}
```

**Output Example**:
```
🏥 VCLI Health Check

Core Tools
  ✓ go
  ✓ git

Python Ecosystem
  ✓ python3
  ✓ pytest
  ✓ black
  ⚠️  autopep8 - not found
    Install: pip install autopep8

Go Ecosystem
  ❌ gosec - not found
    Install: go install github.com/securego/gosec/v2/cmd/gosec@latest
  ⚠️  golangci-lint - not found
    Install: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

Infrastructure
  ✓ kubectl

⚠️  Some tools missing - reduced functionality

Run 'vcli doctor' anytime to check tool status
```

---

### Pattern 4: JSON Output for CI/CD ✅

**Philosophy**: Support both human and machine-readable output

```go
type DoctorReport struct {
    Timestamp    time.Time               `json:"timestamp"`
    OverallStatus string                 `json:"overall_status"`  // "healthy", "degraded", "critical"
    Tools        map[string]ToolStatus   `json:"tools"`
}

type ToolStatus struct {
    Available    bool   `json:"available"`
    Severity     string `json:"severity"`  // "required", "optional", "nice-to-have"
    InstallGuide string `json:"install_guide,omitempty"`
}

func runDoctor(cmd *cobra.Command, args []string) error {
    jsonOutput, _ := cmd.Flags().GetBool("json")

    report := &DoctorReport{
        Timestamp: time.Now(),
        Tools:     make(map[string]ToolStatus),
    }

    // Check all tools
    for _, toolName := range allTools {
        err := checker.Check(toolName)
        status := ToolStatus{
            Available: err == nil,
            Severity:  getSeverity(toolName),
        }

        if err != nil {
            var toolErr *errors.ToolError
            if errors.As(err, &toolErr) {
                status.InstallGuide = toolErr.InstallGuide
            }
        }

        report.Tools[toolName] = status
    }

    // Determine overall status
    report.OverallStatus = computeOverallStatus(report.Tools)

    // Output
    if jsonOutput {
        data, _ := json.MarshalIndent(report, "", "  ")
        fmt.Println(string(data))
    } else {
        printHumanReadable(report)
    }

    return nil
}
```

**Usage**:
```bash
# Human-readable (default)
vcli doctor

# Machine-readable (CI/CD)
vcli doctor --json | jq '.overall_status'

# Fail CI if critical tools missing
if [ "$(vcli doctor --json | jq -r '.overall_status')" = "critical" ]; then
    echo "Critical tools missing"
    exit 1
fi
```

---

## 🔧 INSTALLATION AUTOMATION

### Pattern 5: Self-Healing with User Consent ✅

**Philosophy**: Offer to install missing tools (with permission)

```go
func offerInstallation(toolName string, installCmd string) error {
    fmt.Printf("⚠️  %s not found\n", toolName)
    fmt.Printf("   Install command: %s\n", installCmd)
    fmt.Print("   Install now? [y/N]: ")

    var response string
    fmt.Scanln(&response)

    if strings.ToLower(response) != "y" {
        return fmt.Errorf("installation declined")
    }

    // Execute install command
    fmt.Printf("📦 Installing %s...\n", toolName)

    cmd := exec.Command("sh", "-c", installCmd)
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        return fmt.Errorf("installation failed: %w", err)
    }

    fmt.Printf("✅ %s installed successfully\n", toolName)
    return nil
}

// Usage
func requireTool(toolName string) error {
    if err := checker.Check(toolName); err != nil {
        var toolErr *errors.ToolError
        if errors.As(err, &toolErr) {
            // In interactive mode, offer installation
            if isInteractive() {
                return offerInstallation(toolName, toolErr.InstallGuide)
            }

            // In non-interactive (CI), just error
            return fmt.Errorf("%s required but not found: %s",
                toolName, toolErr.InstallGuide)
        }
        return err
    }
    return nil
}
```

---

### Pattern 6: Setup Wizard ✅

**Philosophy**: First-run experience guides setup

```go
func runSetup(cmd *cobra.Command, args []string) error {
    fmt.Println("🚀 VCLI Setup Wizard")
    fmt.Println()

    // Check all optional tools
    missingTools := []Tool{}

    for _, tool := range optionalTools {
        if err := checker.Check(tool.Name); err != nil {
            missingTools = append(missingTools, tool)
        }
    }

    if len(missingTools) == 0 {
        fmt.Println("✅ All optional tools already installed!")
        return nil
    }

    fmt.Printf("Found %d missing optional tools:\n\n", len(missingTools))

    for _, tool := range missingTools {
        fmt.Printf("  • %s - %s\n", tool.Name, tool.Description)
    }

    fmt.Print("\nInstall all? [y/N]: ")
    var response string
    fmt.Scanln(&response)

    if strings.ToLower(response) != "y" {
        fmt.Println("Skipped. Run 'vcli setup' anytime to install.")
        return nil
    }

    // Install each tool
    for _, tool := range missingTools {
        fmt.Printf("\n📦 Installing %s...\n", tool.Name)
        if err := installTool(tool); err != nil {
            fmt.Printf("   ⚠️  Failed: %v\n", err)
        } else {
            fmt.Printf("   ✅ Installed\n")
        }
    }

    fmt.Println("\n✅ Setup complete! Run 'vcli doctor' to verify.")
    return nil
}
```

---

## 📋 ANTI-PATTERNS TO AVOID

### ❌ Anti-Pattern 1: Silent Failure

```go
// BAD
func runScan() {
    cmd := exec.Command("gosec", "./...")
    output, err := cmd.CombinedOutput()
    if err != nil {
        return  // ❌ User thinks scan ran!
    }
}

// GOOD
func runScan() error {
    if err := checker.Check("gosec"); err != nil {
        fmt.Fprintf(os.Stderr, "⚠️  gosec not available - skipping security scan\n")
        fmt.Fprintf(os.Stderr, "   Install: %s\n", getInstallCmd("gosec"))
        return err  // ✅ Clear communication
    }

    cmd := exec.Command("gosec", "./...")
    return cmd.Run()
}
```

---

### ❌ Anti-Pattern 2: Checking Every Time

```go
// BAD - Checks every call (slow)
func formatCode(code string) (string, error) {
    if _, err := exec.LookPath("black"); err != nil {  // ❌ Repeated check
        return code, err
    }
    // ...
}

// GOOD - Check once, cache result
func formatCode(code string) (string, error) {
    if err := checker.Check("black"); err != nil {  // ✅ Cached
        return code, err
    }
    // ...
}
```

---

### ❌ Anti-Pattern 3: Generic Error Messages

```go
// BAD
return errors.New("tool not found")  // ❌ Which tool?

// GOOD
return &ToolError{
    Tool:         "gosec",
    Err:          ErrToolNotFound,
    Severity:     SeverityWarn,
    InstallGuide: "go install github.com/securego/gosec/v2/cmd/gosec@latest",
}
```

---

## 🎯 IMPLEMENTATION CHECKLIST

### For Each External Tool

- [ ] Register tool in global registry
- [ ] Classify as required/optional/nice-to-have
- [ ] Provide install instructions
- [ ] Add pre-flight check before use
- [ ] Handle missing tool gracefully
- [ ] Show clear error message
- [ ] Document in INSTALL.md
- [ ] Test with tool present
- [ ] Test with tool missing

### For CLI Commands

- [ ] Detect terminal capabilities
- [ ] Support `--json` flag for CI
- [ ] Provide `vcli doctor` health check
- [ ] Offer `vcli setup` wizard (optional)
- [ ] Show available features in help
- [ ] Disable unavailable commands gracefully
- [ ] Log tool checks for debugging

---

## 📊 SUCCESS CRITERIA

### For Air-Gap Implementation

- [ ] Tool registry created (`internal/tools/`)
- [ ] Pre-flight checks for all tools
- [ ] Graceful degradation implemented
- [ ] `vcli doctor` command functional
- [ ] Clear error messages with install guides
- [ ] JSON output for CI/CD
- [ ] Feature flags for optional tools
- [ ] All tool invocations checked first

### For Production

- [ ] Zero silent tool failures
- [ ] Terminal capability detection
- [ ] Setup wizard available
- [ ] INSTALL.md documents all tools
- [ ] CI validates tool availability
- [ ] Metrics track tool usage/failures

---

## 📚 RECOMMENDED READING

### AWS Well-Architected
- Reliability Pillar: Graceful Degradation
- Transform Hard Dependencies to Soft

### Kubernetes
- kubeadm Pre-flight Checks
- Validation Patterns

### CLI Best Practices
- Node.js CLI Apps Best Practices
- Terminal Capability Detection
- User Experience Guidelines

---

**Generated**: 2025-11-14
**Mode**: Boris Cherny - "Degrade gracefully or fail clearly"
**Sources**: AWS, Kubernetes, CLI best practices 2025
**Next**: FASE 0.5.4 - Quality Baseline Configuration
