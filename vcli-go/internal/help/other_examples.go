package help

// ConsciousnessExamples provides examples for Consciousness API commands
var ConsciousnessExamples = ExampleGroup{
	Title: "Consciousness API",
	Examples: []Example{
		{
			Description: "Query consciousness state",
			Command:     "vcli consciousness query --type state",
		},
		{
			Description: "Stream consciousness events",
			Command:     "vcli consciousness stream",
		},
		{
			Description: "Get consciousness metrics",
			Command:     "vcli consciousness metrics",
		},
		{
			Description: "Custom endpoint",
			Command:     "export VCLI_CONSCIOUSNESS_ENDPOINT=http://localhost:8022 && vcli consciousness query",
		},
	},
}

// ImmuneExamples provides examples for Active Immune Core commands
var ImmuneExamples = ExampleGroup{
	Title: "Active Immune Core",
	Examples: []Example{
		{
			Description: "Check immune system status",
			Command:     "vcli immune status",
		},
		{
			Description: "List active threats",
			Command:     "vcli immune threats",
		},
		{
			Description: "Get threat details",
			Command:     "vcli immune threat get --id threat-123",
		},
		{
			Description: "Trigger immune response",
			Command:     "vcli immune respond --threat-id threat-456",
		},
		{
			Description: "Custom endpoint",
			Command:     "export VCLI_IMMUNE_ENDPOINT=localhost:50052 && vcli immune status",
		},
	},
}

// ConfigureExamples provides examples for configuration management
var ConfigureExamples = ExampleGroup{
	Title: "Configuration Management",
	Examples: []Example{
		{
			Description: "Launch interactive configuration wizard",
			Command:     "vcli configure",
		},
		{
			Description: "Show current configuration",
			Command:     "vcli configure show",
		},
		{
			Description: "Set MAXIMUS endpoint",
			Command:     "vcli configure set endpoints.maximus production:50051",
		},
		{
			Description: "Set consciousness endpoint",
			Command:     "vcli configure set endpoints.consciousness http://localhost:8022",
		},
		{
			Description: "Create new profile",
			Command:     "vcli configure profile create staging",
		},
		{
			Description: "Switch profile",
			Command:     "vcli configure profile use staging",
		},
		{
			Description: "List profiles",
			Command:     "vcli configure profile list",
		},
	},
}

// ShellExamples provides examples for interactive shell
var ShellExamples = ExampleGroup{
	Title: "Interactive Shell",
	Examples: []Example{
		{
			Description: "Launch interactive shell",
			Command:     "vcli shell",
		},
		{
			Description: "Use shell commands",
			Command:     "vcli> k8s get pods",
		},
		{
			Description: "Open command palette",
			Command:     "vcli> /palette",
		},
		{
			Description: "View command history",
			Command:     "vcli> /history",
		},
		{
			Description: "Exit shell",
			Command:     "vcli> /exit",
		},
	},
}

// TUIExamples provides examples for TUI workspaces
var TUIExamples = ExampleGroup{
	Title: "Terminal UI Workspaces",
	Examples: []Example{
		{
			Description: "Launch TUI",
			Command:     "vcli tui",
		},
		{
			Description: "Launch specific workspace",
			Command:     "vcli workspace launch situational",
		},
		{
			Description: "Launch investigation workspace",
			Command:     "vcli workspace launch investigation",
		},
		{
			Description: "Launch governance workspace",
			Command:     "vcli workspace launch governance",
		},
		{
			Description: "List available workspaces",
			Command:     "vcli workspace list",
		},
	},
}

// GeneralExamples provides general vcli examples
var GeneralExamples = ExampleGroup{
	Title: "Getting Started",
	Examples: []Example{
		{
			Description: "Show version",
			Command:     "vcli version",
		},
		{
			Description: "Get help for any command",
			Command:     "vcli help k8s",
		},
		{
			Description: "Launch interactive shell (default)",
			Command:     "vcli",
		},
		{
			Description: "Enable debug logging",
			Command:     "export VCLI_DEBUG=true && vcli maximus list",
		},
		{
			Description: "Show banner",
			Command:     "vcli version",
		},
	},
}

// AllOtherExamples returns all other example groups
func AllOtherExamples() []ExampleGroup {
	return []ExampleGroup{
		GeneralExamples,
		ConfigureExamples,
		ShellExamples,
		TUIExamples,
		ConsciousnessExamples,
		ImmuneExamples,
	}
}
