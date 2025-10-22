package help

// HITLExamples provides examples for Human-in-the-Loop commands
var HITLExamples = ExampleGroup{
	Title: "Human-in-the-Loop Console",
	Examples: []Example{
		{
			Description: "Login to HITL console",
			Command:     "vcli hitl login --username admin --password secret",
		},
		{
			Description: "Check HITL status",
			Command:     "vcli hitl status",
		},
		{
			Description: "Get decision queue",
			Command:     "vcli hitl decisions",
		},
		{
			Description: "Approve a decision",
			Command:     "vcli hitl approve --id decision-123",
		},
		{
			Description: "Reject a decision",
			Command:     "vcli hitl reject --id decision-456 --reason \"Insufficient data\"",
		},
	},
}

// HITLAuthExamples provides examples for HITL authentication
var HITLAuthExamples = ExampleGroup{
	Title: "HITL Authentication",
	Examples: []Example{
		{
			Description: "Login with credentials",
			Command:     "vcli hitl login --username admin --password secret",
		},
		{
			Description: "Login with token",
			Command:     "vcli hitl login --token eyJhbGciOiJIUzI1NiIs...",
		},
		{
			Description: "Check authentication status",
			Command:     "vcli hitl status",
		},
		{
			Description: "Logout",
			Command:     "vcli hitl logout",
		},
	},
}

// HITLDecisionExamples provides examples for decision management
var HITLDecisionExamples = ExampleGroup{
	Title: "Decision Management",
	Examples: []Example{
		{
			Description: "List pending decisions",
			Command:     "vcli hitl decisions --status pending",
		},
		{
			Description: "Get decision details",
			Command:     "vcli hitl decision get --id decision-123",
		},
		{
			Description: "Approve with comment",
			Command:     "vcli hitl approve --id decision-123 --comment \"Looks good\"",
		},
		{
			Description: "Defer decision",
			Command:     "vcli hitl defer --id decision-456 --reason \"Need more information\"",
		},
		{
			Description: "View decision history",
			Command:     "vcli hitl history --id decision-123",
		},
	},
}

// HITLConnectionExamples provides examples for HITL connection
var HITLConnectionExamples = ExampleGroup{
	Title: "Connection Configuration",
	Examples: []Example{
		{
			Description: "Use custom HITL endpoint",
			Command:     "vcli hitl status --endpoint https://hitl.example.com/api",
		},
		{
			Description: "Set endpoint via environment",
			Command:     "export VCLI_HITL_ENDPOINT=https://hitl-staging.example.com && vcli hitl status",
		},
		{
			Description: "Configure via config file",
			Command:     "vcli configure set endpoints.hitl https://hitl-prod.example.com && vcli hitl status",
		},
	},
}

// AllHITLExamples returns all HITL example groups
func AllHITLExamples() []ExampleGroup {
	return []ExampleGroup{
		HITLExamples,
		HITLAuthExamples,
		HITLDecisionExamples,
		HITLConnectionExamples,
	}
}
