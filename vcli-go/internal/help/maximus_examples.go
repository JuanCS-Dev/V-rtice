package help

// MaximusExamples provides examples for MAXIMUS orchestrator commands
var MaximusExamples = ExampleGroup{
	Title: "MAXIMUS Orchestrator",
	Examples: []Example{
		{
			Description: "List all decisions",
			Command:     "vcli maximus list",
		},
		{
			Description: "List decisions with status filter",
			Command:     "vcli maximus list --status pending",
		},
		{
			Description: "List decisions by type",
			Command:     "vcli maximus list --type security",
		},
		{
			Description: "Get decision details",
			Command:     "vcli maximus get --id decision-123",
		},
		{
			Description: "Submit new decision",
			Command:     "vcli maximus submit --title \"Deploy to Production\" --type deployment",
		},
	},
}

// MaximusSubmitExamples provides examples for submitting decisions
var MaximusSubmitExamples = ExampleGroup{
	Title: "Submit Decisions",
	Examples: []Example{
		{
			Description: "Submit basic decision",
			Command:     "vcli maximus submit --title \"Enable Feature X\" --type feature",
		},
		{
			Description: "Submit with description",
			Command:     "vcli maximus submit --title \"Deploy v2.0\" --description \"Major version upgrade\" --type deployment",
		},
		{
			Description: "Submit with priority",
			Command:     "vcli maximus submit --title \"Security Patch\" --priority high --type security",
		},
		{
			Description: "Submit with context",
			Command:     "vcli maximus submit --title \"Database Migration\" --context production --type infrastructure",
		},
		{
			Description: "Submit with tags",
			Command:     "vcli maximus submit --title \"API Update\" --tags api,backend,v2 --type deployment",
		},
	},
}

// MaximusUpdateExamples provides examples for updating decisions
var MaximusUpdateExamples = ExampleGroup{
	Title: "Update Decisions",
	Examples: []Example{
		{
			Description: "Approve a decision",
			Command:     "vcli maximus update --id decision-123 --status approved",
		},
		{
			Description: "Reject with reason",
			Command:     "vcli maximus update --id decision-456 --status rejected --reason \"Failed security review\"",
		},
		{
			Description: "Update decision status",
			Command:     "vcli maximus update --id decision-789 --status in-progress --updated-by ops-team",
		},
	},
}

// MaximusWatchExamples provides examples for watching decisions
var MaximusWatchExamples = ExampleGroup{
	Title: "Watch Decisions",
	Examples: []Example{
		{
			Description: "Watch all decisions in real-time",
			Command:     "vcli maximus list --watch",
		},
		{
			Description: "Watch pending decisions only",
			Command:     "vcli maximus list --status pending --watch",
		},
		{
			Description: "Watch decisions with JSON output",
			Command:     "vcli maximus list --watch --output json",
		},
	},
}

// MaximusAIExamples provides examples for AI service commands
var MaximusAIExamples = ExampleGroup{
	Title: "AI Services (Eureka, Oraculo, Predict)",
	Examples: []Example{
		{
			Description: "Analyze data with Eureka",
			Command:     "vcli maximus eureka analyze --data-file metrics.json --type timeseries",
		},
		{
			Description: "Get prediction from Oraculo",
			Command:     "vcli maximus oraculo predict --type resource-usage --time-horizon 24h",
		},
		{
			Description: "Analyze code with Predict",
			Command:     "vcli maximus predict analyze --code-file app.py --language python",
		},
		{
			Description: "Find patterns with Eureka",
			Command:     "vcli maximus eureka patterns --data-file logs.json --pattern-file patterns.yaml",
		},
	},
}

// MaximusConnectionExamples provides examples for connection configuration
var MaximusConnectionExamples = ExampleGroup{
	Title: "Connection Configuration",
	Examples: []Example{
		{
			Description: "Use custom MAXIMUS endpoint",
			Command:     "vcli maximus list --server production.example.com:50051",
		},
		{
			Description: "Set endpoint via environment variable",
			Command:     "export VCLI_MAXIMUS_ENDPOINT=staging:50051 && vcli maximus list",
		},
		{
			Description: "Use configuration file",
			Command:     "vcli configure set endpoints.maximus production:50051 && vcli maximus list",
		},
		{
			Description: "Enable debug logging",
			Command:     "export VCLI_DEBUG=true && vcli maximus list",
		},
	},
}

// AllMaximusExamples returns all MAXIMUS example groups
func AllMaximusExamples() []ExampleGroup {
	return []ExampleGroup{
		MaximusExamples,
		MaximusSubmitExamples,
		MaximusUpdateExamples,
		MaximusWatchExamples,
		MaximusAIExamples,
		MaximusConnectionExamples,
	}
}
