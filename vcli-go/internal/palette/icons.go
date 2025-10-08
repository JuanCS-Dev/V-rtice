package palette

import "strings"

// CommandIcon maps command patterns to emoji icons
var CommandIcon = map[string]string{
	// Workflow aliases
	"wf1": "🔍",
	"wf2": "🚨",
	"wf3": "🔒",
	"wf4": "✅",

	// K8s resources
	"k8s get pods":        "📦",
	"k8s get deployments": "📦",
	"k8s get services":    "🌐",
	"k8s get nodes":       "🖥️",
	"k8s get namespaces":  "📁",
	"k8s logs":            "📄",
	"k8s describe":        "📋",
	"k8s delete":          "🗑️",
	"k8s scale":           "📊",
	"k8s apply":           "✅",
	"k8s exec":            "⚡",
	"k8s top":             "📈",

	// Orchestration
	"orchestrate offensive": "🎯",
	"orchestrate defensive": "🛡️",
	"orchestrate osint":     "🔍",
	"orchestrate monitoring": "👁️",

	// Data
	"data query":  "💾",
	"data ingest": "📥",

	// Investigation
	"investigate": "🔬",

	// Immune system
	"immune status": "🛡️",
	"immune scan":   "🔍",

	// MAXIMUS
	"maximus ask":                       "🧠",
	"maximus analyze":                   "🤖",
	"maximus consciousness":             "🌟",
	"maximus consciousness state":       "🌟",
	"maximus consciousness esgt":        "⚡",
	"maximus consciousness esgt events": "⚡",
	"maximus consciousness esgt trigger": "⚡",
	"maximus consciousness arousal":     "📊",
	"maximus consciousness metrics":     "📈",

	// Metrics
	"metrics": "📊",

	// Narrative Manipulation Filter
	"narrative":          "🛡️",
	"narrative analyze":  "🔍",
	"narrative health":   "💚",
	"narrative info":     "ℹ️",
	"narrative stats":    "📊",
}

// GetIconForCommand returns an icon for a command
func GetIconForCommand(cmd string) string {
	// Direct match
	if icon, ok := CommandIcon[cmd]; ok {
		return icon
	}

	// Prefix match
	for pattern, icon := range CommandIcon {
		if strings.HasPrefix(cmd, pattern) {
			return icon
		}
	}

	// Category-based fallback
	if strings.HasPrefix(cmd, "k8s") {
		return "📦"
	}
	if strings.HasPrefix(cmd, "orchestrate") {
		return "🚀"
	}
	if strings.HasPrefix(cmd, "data") {
		return "💾"
	}
	if strings.HasPrefix(cmd, "investigate") {
		return "🔍"
	}
	if strings.HasPrefix(cmd, "immune") {
		return "🛡️"
	}
	if strings.HasPrefix(cmd, "maximus") {
		return "🧠"
	}
	if strings.HasPrefix(cmd, "metrics") {
		return "📊"
	}

	// Default
	return "▶"
}
