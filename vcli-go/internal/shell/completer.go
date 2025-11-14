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

		// Neuro cortex suggestions
		if firstWord == "neuro" && len(args) == 2 {
			results := c.getNeuroSubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Behavioral analysis suggestions
		if firstWord == "behavior" && len(args) == 2 {
			results := c.getBehaviorSubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Intelligence operations suggestions
		if firstWord == "intops" && len(args) == 2 {
			results := c.getIntopsSubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Offensive security suggestions
		if firstWord == "offensive" && len(args) == 2 {
			results := c.getOffensiveSubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Immunity suggestions
		if firstWord == "immunity" && len(args) == 2 {
			results := c.getImmunitySubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Hunting suggestions
		if firstWord == "hunting" && len(args) == 2 {
			results := c.getHuntingSubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Streams suggestions
		if firstWord == "streams" && len(args) == 2 {
			results := c.getStreamsSubcommands(lastWord)
			return c.limitSuggestions(results, 10)
		}

		// Specialized suggestions
		if firstWord == "specialized" && len(args) == 2 {
			results := c.getSpecializedSubcommands(lastWord)
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

// getNeuroSubcommands returns neuro cortex suggestions
func (c *Completer) getNeuroSubcommands(prefix string) []prompt.Suggest {
	var neuroSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "neuro ") {
			neuroSuggestions = append(neuroSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, neuroSuggestions)
}

// getBehaviorSubcommands returns behavioral analysis suggestions
func (c *Completer) getBehaviorSubcommands(prefix string) []prompt.Suggest {
	var behaviorSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "behavior ") {
			behaviorSuggestions = append(behaviorSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, behaviorSuggestions)
}

// getIntopsSubcommands returns intelligence operations suggestions
func (c *Completer) getIntopsSubcommands(prefix string) []prompt.Suggest {
	var intopsSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "intops ") {
			intopsSuggestions = append(intopsSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, intopsSuggestions)
}

// getOffensiveSubcommands returns offensive security suggestions
func (c *Completer) getOffensiveSubcommands(prefix string) []prompt.Suggest {
	var offensiveSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "offensive ") {
			offensiveSuggestions = append(offensiveSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, offensiveSuggestions)
}

// getImmunitySubcommands returns immunity suggestions
func (c *Completer) getImmunitySubcommands(prefix string) []prompt.Suggest {
	var immunitySuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "immunity ") {
			immunitySuggestions = append(immunitySuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, immunitySuggestions)
}

// getHuntingSubcommands returns hunting suggestions
func (c *Completer) getHuntingSubcommands(prefix string) []prompt.Suggest {
	var huntingSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "hunting ") {
			huntingSuggestions = append(huntingSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, huntingSuggestions)
}

// getStreamsSubcommands returns streams suggestions
func (c *Completer) getStreamsSubcommands(prefix string) []prompt.Suggest {
	var streamsSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "streams ") {
			streamsSuggestions = append(streamsSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, streamsSuggestions)
}

// getSpecializedSubcommands returns specialized suggestions
func (c *Completer) getSpecializedSubcommands(prefix string) []prompt.Suggest {
	var specializedSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "specialized ") {
			specializedSuggestions = append(specializedSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, specializedSuggestions)
}

// SHELL-9 command helpers
func (c *Completer) getMabaSubcommands(prefix string) []prompt.Suggest {
	var mabaSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "maba ") {
			mabaSuggestions = append(mabaSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, mabaSuggestions)
}

func (c *Completer) getNisSubcommands(prefix string) []prompt.Suggest {
	var nisSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "nis ") {
			nisSuggestions = append(nisSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, nisSuggestions)
}

func (c *Completer) getRteSubcommands(prefix string) []prompt.Suggest {
	var rteSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "rte ") {
			rteSuggestions = append(rteSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, rteSuggestions)
}

func (c *Completer) getArchitectSubcommands(prefix string) []prompt.Suggest {
	var architectSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "architect ") {
			architectSuggestions = append(architectSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, architectSuggestions)
}

func (c *Completer) getPipelineSubcommands(prefix string) []prompt.Suggest {
	var pipelineSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "pipeline ") {
			pipelineSuggestions = append(pipelineSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, pipelineSuggestions)
}

func (c *Completer) getRegistrySubcommands(prefix string) []prompt.Suggest {
	var registrySuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "registry ") {
			registrySuggestions = append(registrySuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, registrySuggestions)
}

func (c *Completer) getEdgeSubcommands(prefix string) []prompt.Suggest {
	var edgeSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "edge ") {
			edgeSuggestions = append(edgeSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, edgeSuggestions)
}

func (c *Completer) getIntegrationSubcommands(prefix string) []prompt.Suggest {
	var integrationSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "integration ") {
			integrationSuggestions = append(integrationSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, integrationSuggestions)
}

func (c *Completer) getHomeostasisSubcommands(prefix string) []prompt.Suggest {
	var homeostasisSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "homeostasis ") {
			homeostasisSuggestions = append(homeostasisSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, homeostasisSuggestions)
}

func (c *Completer) getPurpleSubcommands(prefix string) []prompt.Suggest {
	var purpleSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "purple ") {
			purpleSuggestions = append(purpleSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, purpleSuggestions)
}

func (c *Completer) getVulnscanSubcommands(prefix string) []prompt.Suggest {
	var vulnscanSuggestions []prompt.Suggest
	for _, s := range c.suggestions {
		if strings.HasPrefix(s.Text, "vulnscan ") {
			vulnscanSuggestions = append(vulnscanSuggestions, s)
		}
	}
	return c.filterSuggestions(prefix, vulnscanSuggestions)
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
		{Text: "maximus consciousness watch", Description: "Watch events real-time (WebSocket)"},

		// Narrative Manipulation Filter
		{Text: "narrative analyze", Description: "Analyze text for manipulation"},
		{Text: "narrative health", Description: "Check service health"},
		{Text: "narrative info", Description: "Get service info"},
		{Text: "narrative stats cache", Description: "Cache statistics"},
		{Text: "narrative stats database", Description: "Database statistics"},

		// Neuro-Inspired System Commands
		{Text: "neuro auditory listen", Description: "Listen to auditory cortex events"},
		{Text: "neuro thalamus route", Description: "Route sensory input via thalamus"},
		{Text: "neuro memory consolidate", Description: "Consolidate threat patterns in memory"},
		{Text: "neuro cortex plan", Description: "Generate strategic response plan"},
		{Text: "neuro visual analyze", Description: "Analyze visual feed for threats"},
		{Text: "neuro somatosensory status", Description: "Check somatosensory sensor status"},
		{Text: "neuro tegumentar shield", Description: "Activate protective shield for zone"},
		{Text: "neuro vestibular balance", Description: "Balance system workload"},
		{Text: "neuro chemical sense", Description: "Sense chemical/bio threats"},

		// Offensive Security Commands
		{Text: "offensive tools list", Description: "List available offensive tools"},
		{Text: "offensive c2 deploy", Description: "Deploy C2 infrastructure"},
		{Text: "offensive social-eng phishing", Description: "Launch phishing campaign"},
		{Text: "offensive malware develop", Description: "Develop custom malware"},
		{Text: "offensive wargame start", Description: "Start offensive wargame"},
		{Text: "offensive gateway status", Description: "Check offensive gateway status"},
		{Text: "offensive orchestrator plan", Description: "Plan multi-stage attack"},

		// Behavioral Analysis Commands
		{Text: "behavior analyze --user", Description: "Analyze user behavior patterns"},
		{Text: "behavior bas detect-anomaly", Description: "Detect behavioral anomalies"},
		{Text: "behavior mav scan", Description: "Scan for malicious activity vectors"},
		{Text: "behavior traffic analyze", Description: "Analyze network traffic patterns"},
		{Text: "behavior fabric status", Description: "Check reactive fabric status"},

		// Intelligence Operations Commands
		{Text: "intops google search", Description: "Perform Google OSINT search"},
		{Text: "intops google dork", Description: "Execute Google dork query"},
		{Text: "intops ip lookup", Description: "Lookup IP intelligence"},
		{Text: "intops ip geo", Description: "Get IP geolocation"},
		{Text: "intops sinesp plate", Description: "Lookup vehicle plate (Brazil)"},
		{Text: "intops sinesp document", Description: "Lookup document (Brazil)"},
		{Text: "intops ssl check", Description: "Check SSL certificate"},
		{Text: "intops ssl monitor", Description: "Monitor SSL certificates"},
		{Text: "intops narrative analyze", Description: "Analyze narrative manipulation"},
		{Text: "intops narrative detect", Description: "Detect narrative manipulation"},

		// Adaptive Immunity Commands
		{Text: "immunity core status", Description: "Get immune system status"},
		{Text: "immunity core activate", Description: "Activate immune response"},
		{Text: "immunity scan --target", Description: "Run Immunis security scan"},
		{Text: "immunity vaccine deploy", Description: "Deploy vaccine/patch"},
		{Text: "immunity vaccine list", Description: "List available vaccines"},
		{Text: "immunity antibody generate", Description: "Generate antibody response"},
		{Text: "immunity antibody list", Description: "List active antibodies"},

		// Threat Hunting & Prediction Commands
		{Text: "hunting apt predict", Description: "Predict APT threats"},
		{Text: "hunting apt profile", Description: "Profile APT actor"},
		{Text: "hunting hunt start", Description: "Start threat hunt"},
		{Text: "hunting hunt results", Description: "Get hunt results"},
		{Text: "hunting predict --target", Description: "Predict anomalies"},
		{Text: "hunting surface analyze", Description: "Analyze attack surface"},
		{Text: "hunting surface map", Description: "Map attack surface"},

		// Kafka Streams Commands
		{Text: "streams topic list", Description: "List Kafka topics"},
		{Text: "streams topic create", Description: "Create Kafka topic"},
		{Text: "streams topic describe", Description: "Describe Kafka topic"},
		{Text: "streams produce --topic", Description: "Produce message to topic"},
		{Text: "streams consume --topic", Description: "Consume messages from topic"},
		{Text: "streams consumer list", Description: "List consumer groups"},
		{Text: "streams consumer lag", Description: "Check consumer lag"},

		// Specialized Services Commands
		{Text: "specialized aether --query", Description: "Query distributed consciousness"},
		{Text: "specialized babel --text", Description: "Multi-language translation"},
		{Text: "specialized cerberus --tenant", Description: "Multi-head authentication"},
		{Text: "specialized chimera --query", Description: "Hybrid threat detection"},
		{Text: "specialized chronos --metric", Description: "Time-series analysis"},
		{Text: "specialized echo --event", Description: "Event replay / time-travel"},
		{Text: "specialized hydra --tenant", Description: "Multi-tenancy status"},
		{Text: "specialized iris --image", Description: "Visual recognition"},
		{Text: "specialized janus --query", Description: "Bidirectional sync"},
		{Text: "specialized phoenix status", Description: "Self-healing status"},

		// SHELL-9: MABA Commands
		{Text: "maba browser navigate", Description: "Navigate to URL autonomously"},
		{Text: "maba browser extract", Description: "Extract data from webpage"},
		{Text: "maba browser sessions", Description: "List active browser sessions"},
		{Text: "maba map query", Description: "Query cognitive map"},
		{Text: "maba map stats", Description: "Cognitive map statistics"},
		{Text: "maba tools", Description: "List registered MAXIMUS tools"},
		{Text: "maba status", Description: "MABA service status"},

		// SHELL-9: NIS Commands
		{Text: "nis narrative generate", Description: "Generate AI narrative from metrics"},
		{Text: "nis narrative list", Description: "List recent narratives"},
		{Text: "nis anomaly detect", Description: "Detect statistical anomalies"},
		{Text: "nis anomaly baseline", Description: "Show baseline statistics"},
		{Text: "nis cost status", Description: "Cost tracking status"},
		{Text: "nis cost history", Description: "Cost history"},
		{Text: "nis ratelimit", Description: "Rate limit status"},
		{Text: "nis status", Description: "NIS service status"},

		// SHELL-9: RTE Commands
		{Text: "rte triage", Description: "Real-time alert triage"},
		{Text: "rte fusion correlate", Description: "Correlate event data"},
		{Text: "rte predict", Description: "Fast ML prediction"},
		{Text: "rte match", Description: "Hyperscan pattern matching"},
		{Text: "rte playbooks", Description: "List available playbooks"},
		{Text: "rte status", Description: "RTE service status"},

		// SHELL-9: Architect Commands
		{Text: "architect analyze", Description: "Analyze platform architecture"},
		{Text: "architect blueprint", Description: "Generate service blueprint"},
		{Text: "architect status", Description: "System Architect status"},

		// SHELL-9: Pipeline Commands
		{Text: "pipeline tataca ingest", Description: "Ingest data from source"},
		{Text: "pipeline seriema query", Description: "Execute Cypher query"},
		{Text: "pipeline seriema visualize", Description: "Visualize entity relationships"},
		{Text: "pipeline bus publish", Description: "Publish command to bus"},
		{Text: "pipeline bus list", Description: "List command topics"},
		{Text: "pipeline status", Description: "Pipeline service status"},

		// SHELL-9: Registry Commands
		{Text: "registry list", Description: "List registered services"},
		{Text: "registry health", Description: "Check service health"},
		{Text: "registry status", Description: "Registry service status"},

		// SHELL-9: Edge Commands
		{Text: "edge deploy", Description: "Deploy edge agent"},
		{Text: "edge list", Description: "List edge agents"},
		{Text: "edge status", Description: "Edge service status"},

		// SHELL-9: Integration Commands
		{Text: "integration list", Description: "List all integrations"},
		{Text: "integration test", Description: "Test integration"},
		{Text: "integration status", Description: "Integration service status"},

		// SHELL-9: Homeostasis Commands
		{Text: "homeostasis status", Description: "Homeostatic status"},
		{Text: "homeostasis adjust", Description: "Adjust homeostatic parameter"},

		// SHELL-9: Purple Team Commands
		{Text: "purple exercise", Description: "Run purple team exercise"},
		{Text: "purple report", Description: "Get exercise report"},
		{Text: "purple status", Description: "Purple team service status"},

		// SHELL-9: VulnScan Commands
		{Text: "vulnscan scan", Description: "Scan target for vulnerabilities"},
		{Text: "vulnscan report", Description: "Get scan report"},
		{Text: "vulnscan status", Description: "Vulnerability scanner status"},
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
