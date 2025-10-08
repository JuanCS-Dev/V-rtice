package shell

import (
	"strings"

	prompt "github.com/c-bata/go-prompt"
	"github.com/spf13/cobra"
	"github.com/spf13/pflag"
)

// Completer handles auto-completion for the shell
type Completer struct {
	rootCmd     *cobra.Command
	suggestions []prompt.Suggest
}

// NewCompleter creates a new completer
func NewCompleter(rootCmd *cobra.Command) *Completer {
	c := &Completer{
		rootCmd:     rootCmd,
		suggestions: make([]prompt.Suggest, 0),
	}

	c.buildSuggestions()
	return c
}

// Complete returns completion suggestions (go-prompt interface)
func (c *Completer) Complete(d prompt.Document) []prompt.Suggest {
	text := d.TextBeforeCursor()
	return c.CompleteText(text)
}

// CompleteText is the internal completion logic that works on plain text
// This is exported to make testing easier (go-prompt.Document has unexported fields)
func (c *Completer) CompleteText(text string) []prompt.Suggest {
	// Always show slash commands when user types "/"
	if text == "/" {
		return c.getSlashCommands()
	}

	// If empty, show common commands as hint
	if text == "" {
		return c.getCommonCommands()
	}

	// CRITICAL CHECK: If input ends with space, user finished typing word
	// Return empty to prevent sticky autocomplete bug
	if len(text) > 0 && (text[len(text)-1] == ' ' || text[len(text)-1] == '\t') {
		return []prompt.Suggest{}
	}

	// Split into words
	args := strings.Fields(text)
	if len(args) == 0 {
		return c.getCommonCommands()
	}

	// Get last word being typed
	lastWord := args[len(args)-1]

	// If last word is empty, return empty
	if lastWord == "" {
		return []prompt.Suggest{}
	}

	// Context-aware suggestions based on command structure
	if len(args) == 1 {
		// First word - suggest main commands
		results := c.filterSuggestions(lastWord, c.suggestions)
		return c.limitSuggestions(results, 15) // Limit to prevent rendering bugs
	}

	if len(args) >= 2 {
		// Multi-word command - suggest based on context
		firstWord := args[0]

		// K8s resource-specific suggestions
		if firstWord == "k8s" && len(args) == 2 {
			results := c.getK8sSubcommands(lastWord)
			return c.limitSuggestions(results, 15)
		}

		// Orchestrate workflow suggestions
		if firstWord == "orchestrate" && len(args) == 2 {
			results := c.getOrchestrateCategories(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Flag suggestions
		if strings.HasPrefix(lastWord, "-") {
			results := c.getFlagSuggestions(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// General filtering
		results := c.filterSuggestions(lastWord, c.suggestions)
		return c.limitSuggestions(results, 15)
	}

	results := c.filterSuggestions(lastWord, c.suggestions)
	return c.limitSuggestions(results, 15)
}

// getSlashCommands returns only slash commands
func (c *Completer) getSlashCommands() []prompt.Suggest {
	var slashCmds []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "/") {
			slashCmds = append(slashCmds, s)
		}
	}
	return slashCmds
}

// getCommonCommands returns frequently used commands (NO slash commands here)
func (c *Completer) getCommonCommands() []prompt.Suggest {
	return []prompt.Suggest{
		{Text: "k8s get pods", Description: "List pods"},
		{Text: "k8s get deployments", Description: "List deployments"},
		{Text: "orchestrate offensive apt-simulation", Description: "APT simulation"},
		{Text: "investigate", Description: "Launch investigation workspace"},
		{Text: "tui", Description: "Launch TUI"},
	}
}

// getK8sSubcommands returns k8s-specific suggestions
func (c *Completer) getK8sSubcommands(prefix string) []prompt.Suggest {
	var k8sSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "k8s ") {
			k8sSuggestions = append(k8sSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, k8sSuggestions)
}

// getOrchestrateCategories returns orchestrate workflow suggestions
func (c *Completer) getOrchestrateCategories(prefix string) []prompt.Suggest {
	var orchestrateSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "orchestrate ") {
			orchestrateSuggestions = append(orchestrateSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, orchestrateSuggestions)
}

// getFlagSuggestions returns flag suggestions
func (c *Completer) getFlagSuggestions(prefix string) []prompt.Suggest {
	var flagSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "-") {
			flagSuggestions = append(flagSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, flagSuggestions)
}

// filterSuggestions performs fuzzy filtering on suggestions
func (c *Completer) filterSuggestions(prefix string, suggestions []prompt.Suggest) []prompt.Suggest {
	if prefix == "" {
		return suggestions
	}

	// First try exact prefix match (fast path)
	prefixMatches := prompt.FilterHasPrefix(suggestions, prefix, true)
	if len(prefixMatches) > 0 {
		return prefixMatches
	}

	// Fallback to fuzzy matching
	var fuzzyMatches []prompt.Suggest
	lowerPrefix := strings.ToLower(prefix)

	for _, s := range suggestions {
		lowerText := strings.ToLower(s.Text)

		// Contains match
		if strings.Contains(lowerText, lowerPrefix) {
			fuzzyMatches = append(fuzzyMatches, s)
			continue
		}

		// Fuzzy match - check if all characters in prefix appear in order
		if c.fuzzyMatch(lowerPrefix, lowerText) {
			fuzzyMatches = append(fuzzyMatches, s)
		}
	}

	return fuzzyMatches
}

// fuzzyMatch checks if all characters in pattern appear in text in order
func (c *Completer) fuzzyMatch(pattern, text string) bool {
	patternIdx := 0
	for i := 0; i < len(text) && patternIdx < len(pattern); i++ {
		if text[i] == pattern[patternIdx] {
			patternIdx++
		}
	}
	return patternIdx == len(pattern)
}

// limitSuggestions limits the number of suggestions to prevent rendering bugs
func (c *Completer) limitSuggestions(suggestions []prompt.Suggest, max int) []prompt.Suggest {
	if len(suggestions) <= max {
		return suggestions
	}
	return suggestions[:max]
}

// buildSuggestions builds the suggestion list from Cobra commands
func (c *Completer) buildSuggestions() {
	// Add slash commands
	c.suggestions = append(c.suggestions, []prompt.Suggest{
		{Text: "/help", Description: "Show shell help"},
		{Text: "/exit", Description: "Exit the shell"},
		{Text: "/quit", Description: "Exit the shell"},
		{Text: "/clear", Description: "Clear the screen"},
		{Text: "/history", Description: "Show command history"},
		{Text: "/palette", Description: "Open command palette"},
	}...)

	// Add workflow aliases (wf1-wf4)
	c.suggestions = append(c.suggestions, []prompt.Suggest{
		{Text: "wf1", Description: "Threat Hunt workflow"},
		{Text: "wf2", Description: "Incident Response workflow"},
		{Text: "wf3", Description: "Security Audit workflow"},
		{Text: "wf4", Description: "Compliance Check workflow"},
	}...)

	// Add main commands
	c.suggestions = append(c.suggestions, []prompt.Suggest{
		// Orchestration workflows
		{Text: "orchestrate offensive apt-simulation", Description: "APT attack simulation workflow"},
		{Text: "orchestrate offensive target-assessment", Description: "Target assessment workflow"},
		{Text: "orchestrate defensive threat-hunting", Description: "Threat hunting workflow"},
		{Text: "orchestrate defensive threat-response", Description: "Threat response workflow"},
		{Text: "orchestrate osint deep-investigation", Description: "Deep OSINT investigation workflow"},
		{Text: "orchestrate osint actor-profiling", Description: "Actor profiling workflow"},
		{Text: "orchestrate monitoring security-posture", Description: "Security posture monitoring"},
		{Text: "orchestrate monitoring anomaly-response", Description: "Anomaly response workflow"},

		// Core commands
		{Text: "data query", Description: "Query Seriema graph database"},
		{Text: "data ingest", Description: "Ingest data into graph"},
		{Text: "ethical audit", Description: "Run ethical AI audit"},
		{Text: "immune status", Description: "Check immune system status"},
		{Text: "immunis scan", Description: "Run immunis security scan"},
		{Text: "maximus ask", Description: "Ask MAXIMUS AI"},
		{Text: "threat analyze", Description: "Analyze threat intelligence"},
		{Text: "investigate", Description: "Launch investigation workspace"},
		{Text: "metrics", Description: "Show system metrics"},
		{Text: "sync", Description: "Sync services"},
		{Text: "stream", Description: "Stream events"},
		{Text: "gateway", Description: "API gateway operations"},
		{Text: "hcl", Description: "Homeostatic Control Loop operations"},
		{Text: "configure", Description: "Configure vcli"},
		{Text: "tui", Description: "Launch TUI workspaces"},
		{Text: "shell", Description: "Launch interactive shell"},
		{Text: "version", Description: "Show version information"},

		// MAXIMUS Consciousness commands
		{Text: "maximus consciousness state", Description: "Get consciousness state"},
		{Text: "maximus consciousness esgt events", Description: "Get ESGT ignition events"},
		{Text: "maximus consciousness esgt trigger", Description: "Trigger ESGT ignition"},
		{Text: "maximus consciousness arousal", Description: "Get arousal state"},
		{Text: "maximus consciousness arousal adjust", Description: "Adjust arousal level"},
		{Text: "maximus consciousness metrics", Description: "Get consciousness metrics"},
	}...)

	// Add Kubernetes commands explicitly
	c.suggestions = append(c.suggestions, []prompt.Suggest{
		// Resource Management
		{Text: "k8s get pods", Description: "List pods"},
		{Text: "k8s get deployments", Description: "List deployments"},
		{Text: "k8s get services", Description: "List services"},
		{Text: "k8s get nodes", Description: "List nodes"},
		{Text: "k8s get namespaces", Description: "List namespaces"},
		{Text: "k8s get all", Description: "List all resources"},
		{Text: "k8s apply -f", Description: "Apply configuration from file"},
		{Text: "k8s delete pod", Description: "Delete a pod"},
		{Text: "k8s delete deployment", Description: "Delete a deployment"},
		{Text: "k8s scale deployment", Description: "Scale deployment replicas"},
		{Text: "k8s patch", Description: "Patch resource"},

		// Observability
		{Text: "k8s logs", Description: "View pod logs"},
		{Text: "k8s exec", Description: "Execute command in pod"},
		{Text: "k8s describe pod", Description: "Describe pod details"},
		{Text: "k8s describe deployment", Description: "Describe deployment details"},
		{Text: "k8s port-forward", Description: "Forward port to pod"},
		{Text: "k8s watch pods", Description: "Watch pods in real-time"},

		// Metrics
		{Text: "k8s top nodes", Description: "Show node metrics"},
		{Text: "k8s top pods", Description: "Show pod metrics"},
		{Text: "k8s top pod", Description: "Show specific pod metrics"},

		// ConfigMaps & Secrets
		{Text: "k8s create configmap", Description: "Create ConfigMap"},
		{Text: "k8s create secret", Description: "Create Secret"},
		{Text: "k8s get configmaps", Description: "List ConfigMaps"},
		{Text: "k8s get secrets", Description: "List Secrets"},

		// Rollout
		{Text: "k8s rollout status", Description: "Check rollout status"},
		{Text: "k8s rollout history", Description: "View rollout history"},
		{Text: "k8s rollout undo", Description: "Undo rollout"},
		{Text: "k8s rollout restart", Description: "Restart rollout"},
		{Text: "k8s rollout pause", Description: "Pause rollout"},
		{Text: "k8s rollout resume", Description: "Resume rollout"},

		// Metadata
		{Text: "k8s label", Description: "Add/remove labels"},
		{Text: "k8s annotate", Description: "Add/remove annotations"},

		// Auth
		{Text: "k8s auth can-i", Description: "Check permissions"},
		{Text: "k8s auth whoami", Description: "Show current user"},

		// Wait
		{Text: "k8s wait", Description: "Wait for condition"},

		// Common flags
		{Text: "--all-namespaces", Description: "List resources from all namespaces"},
		{Text: "-n", Description: "Specify namespace"},
		{Text: "--namespace", Description: "Specify namespace"},
		{Text: "-f", Description: "Specify file"},
		{Text: "--follow", Description: "Follow log output"},
		{Text: "--replicas", Description: "Number of replicas"},
		{Text: "-o json", Description: "Output format: JSON"},
		{Text: "-o yaml", Description: "Output format: YAML"},
		{Text: "--containers", Description: "Show container-level metrics"},
	}...)

	// Add Cobra commands
	c.addCobraCommands(c.rootCmd, "")
}

// addCobraCommands recursively adds Cobra commands to suggestions
func (c *Completer) addCobraCommands(cmd *cobra.Command, prefix string) {
	for _, subCmd := range cmd.Commands() {
		// Skip hidden commands
		if subCmd.Hidden {
			continue
		}

		// Build command path
		cmdPath := subCmd.Use
		if prefix != "" {
			cmdPath = prefix + " " + subCmd.Use
		}

		fullPath := cmdPath

		// Add to suggestions
		c.suggestions = append(c.suggestions, prompt.Suggest{
			Text:        fullPath,
			Description: subCmd.Short,
		})

		// Add subcommands recursively
		if subCmd.HasSubCommands() {
			c.addCobraCommands(subCmd, fullPath)
		}

		// Add flags
		subCmd.Flags().VisitAll(func(f *pflag.Flag) {
			// Long flag
			if f.Name != "" {
				c.suggestions = append(c.suggestions, prompt.Suggest{
					Text:        "--" + f.Name,
					Description: f.Usage,
				})
			}

			// Short flag
			if f.Shorthand != "" {
				c.suggestions = append(c.suggestions, prompt.Suggest{
					Text:        "-" + f.Shorthand,
					Description: f.Usage,
				})
			}
		})
	}
}

// GetSuggestions returns all available suggestions
func (c *Completer) GetSuggestions() []prompt.Suggest {
	return c.suggestions
}

// AddCustomSuggestion adds a custom suggestion
func (c *Completer) AddCustomSuggestion(text, description string) {
	c.suggestions = append(c.suggestions, prompt.Suggest{
		Text:        text,
		Description: description,
	})
}
