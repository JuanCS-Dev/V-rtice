package config

import "time"

// Config represents the complete VCLI configuration
type Config struct {
	API       APIConfig                `yaml:"api" json:"api"`
	Endpoints map[string]string        `yaml:"endpoints" json:"endpoints"`
	Auth      AuthConfig               `yaml:"auth" json:"auth"`
	Output    OutputConfig             `yaml:"output" json:"output"`
	Profiles  map[string]ProfileConfig `yaml:"profiles,omitempty" json:"profiles,omitempty"`
}

// APIConfig contains global API settings
type APIConfig struct {
	Timeout time.Duration `yaml:"timeout" json:"timeout"`
	Retry   int           `yaml:"retry" json:"retry"`
}

// AuthConfig contains authentication settings
type AuthConfig struct {
	Token  string `yaml:"token" json:"token"`
	Method string `yaml:"method" json:"method"`
}

// OutputConfig contains output formatting settings
type OutputConfig struct {
	Format  string `yaml:"format" json:"format"`
	Color   string `yaml:"color" json:"color"`
	Verbose bool   `yaml:"verbose" json:"verbose"`
}

// ProfileConfig represents a named configuration profile
type ProfileConfig struct {
	Endpoints map[string]string `yaml:"endpoints" json:"endpoints"`
	Auth      AuthConfig        `yaml:"auth" json:"auth"`
}

// Source indicates where a config value came from
type Source int

const (
	SourceDefault Source = iota
	SourceUserConfig
	SourceProjectConfig
	SourceEnv
	SourceFlag
)

func (s Source) String() string {
	switch s {
	case SourceDefault:
		return "default"
	case SourceUserConfig:
		return "~/.vcli/config.yaml"
	case SourceProjectConfig:
		return "VCLI.md"
	case SourceEnv:
		return "environment"
	case SourceFlag:
		return "flag"
	default:
		return "unknown"
	}
}

// DefaultConfig returns the default configuration
func DefaultConfig() *Config {
	return &Config{
		API: APIConfig{
			Timeout: 30 * time.Second,
			Retry:   3,
		},
		Endpoints: map[string]string{
			"maximus":      "http://localhost:8000",
			"immune":       "http://localhost:8001",
			"maba":         "http://localhost:9700",
			"nis":          "http://localhost:9800",
			"rte":          "http://localhost:9900",
			"architect":    "http://localhost:10000",
			"pipeline":     "http://localhost:10100",
			"registry":     "http://localhost:10200",
			"edge":         "http://localhost:10300",
			"integration":  "http://localhost:10400",
			"homeostasis":  "http://localhost:10500",
			"purple":       "http://localhost:10600",
			"vulnscan":     "http://localhost:10700",
			"specialized":  "http://localhost:9600",
			"neuro":        "http://localhost:9500",
			"offensive":    "http://localhost:9400",
			"behavior":     "http://localhost:9300",
			"intops":       "http://localhost:9200",
			"immunity":     "http://localhost:9100",
			"hunting":      "http://localhost:9000",
			"streams":      "http://localhost:9092",
		},
		Auth: AuthConfig{
			Token:  "",
			Method: "bearer",
		},
		Output: OutputConfig{
			Format:  "json",
			Color:   "auto",
			Verbose: false,
		},
		Profiles: make(map[string]ProfileConfig),
	}
}
