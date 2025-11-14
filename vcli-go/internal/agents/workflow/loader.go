package workflow

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/verticedev/vcli-go/internal/agents"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"gopkg.in/yaml.v3"
)

// WorkflowYAML represents the YAML structure for workflow definition
type WorkflowYAML struct {
	Name        string         `yaml:"name"`
	Description string         `yaml:"description"`
	Steps       []WorkflowStepYAML `yaml:"steps"`
}

// WorkflowStepYAML represents a single step in YAML
type WorkflowStepYAML struct {
	Agent           string                 `yaml:"agent"`
	Description     string                 `yaml:"description"`
	Task            string                 `yaml:"task"`
	Targets         []string               `yaml:"targets"`
	Config          map[string]interface{} `yaml:"config"`
	HITLRequired    bool                   `yaml:"hitl_required"`
	ContinueOnError bool                   `yaml:"continue_on_error"`
}

// LoadWorkflow loads a workflow from YAML file
func LoadWorkflow(workflowName string) (*agents.Workflow, error) {
	// Check if workflowName is a file path or workflow name
	var workflowPath string

	if filepath.Ext(workflowName) == ".yaml" || filepath.Ext(workflowName) == ".yml" {
		// Direct file path provided
		workflowPath = workflowName
	} else {
		// Workflow name - check standard locations using fs helper
		workflowDir, err := vcliFs.GetVCLIWorkflowsDir()
		if err != nil {
			return nil, fmt.Errorf("failed to get workflows directory: %w", err)
		}

		// Try ~/.vcli/workflows/<name>.yaml
		workflowPath = filepath.Join(workflowDir, workflowName+".yaml")

		// Check if file exists
		if _, err := os.Stat(workflowPath); os.IsNotExist(err) {
			// Try current directory
			workflowPath = filepath.Join(".", "workflows", workflowName+".yaml")

			if _, err := os.Stat(workflowPath); os.IsNotExist(err) {
				return nil, fmt.Errorf("workflow '%s' not found in ~/.vcli/workflows/ or ./workflows/", workflowName)
			}
		}
	}

	// Read YAML file
	data, err := os.ReadFile(workflowPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read workflow file: %w", err)
	}

	// Parse YAML
	var workflowYAML WorkflowYAML
	if err := yaml.Unmarshal(data, &workflowYAML); err != nil {
		return nil, fmt.Errorf("failed to parse workflow YAML: %w", err)
	}

	// Validate workflow
	if err := validateWorkflow(&workflowYAML); err != nil {
		return nil, fmt.Errorf("workflow validation failed: %w", err)
	}

	// Convert to internal Workflow struct
	workflow := &agents.Workflow{
		Name:        workflowYAML.Name,
		Description: workflowYAML.Description,
		Steps:       make([]agents.WorkflowStep, 0, len(workflowYAML.Steps)),
	}

	// Convert steps
	for i, stepYAML := range workflowYAML.Steps {
		// Parse agent type
		agentType, err := parseAgentType(stepYAML.Agent)
		if err != nil {
			return nil, fmt.Errorf("step %d: %w", i+1, err)
		}

		// Create workflow step
		step := agents.WorkflowStep{
			AgentType:       agentType,
			Task:            stepYAML.Task,
			Description:     stepYAML.Description,
			Targets:         stepYAML.Targets,
			Context:         make(map[string]interface{}),
			Config:          stepYAML.Config,
			HITLRequired:    stepYAML.HITLRequired,
			ContinueOnError: stepYAML.ContinueOnError,
		}

		// Initialize config if nil
		if step.Config == nil {
			step.Config = make(map[string]interface{})
		}

		workflow.Steps = append(workflow.Steps, step)
	}

	return workflow, nil
}

// validateWorkflow validates workflow structure
func validateWorkflow(workflow *WorkflowYAML) error {
	if workflow.Name == "" {
		return fmt.Errorf("workflow name is required")
	}

	if len(workflow.Steps) == 0 {
		return fmt.Errorf("workflow must have at least one step")
	}

	// Validate each step
	for i, step := range workflow.Steps {
		if step.Agent == "" {
			return fmt.Errorf("step %d: agent type is required", i+1)
		}

		if step.Task == "" {
			return fmt.Errorf("step %d: task description is required", i+1)
		}

		// Validate agent type
		if _, err := parseAgentType(step.Agent); err != nil {
			return fmt.Errorf("step %d: %w", i+1, err)
		}
	}

	return nil
}

// parseAgentType converts string to AgentType
func parseAgentType(agentStr string) (agents.AgentType, error) {
	switch agentStr {
	case "diagnosticador":
		return agents.AgentTypeDiagnosticador, nil
	case "arquiteto":
		return agents.AgentTypeArquiteto, nil
	case "dev_senior":
		return agents.AgentTypeDevSenior, nil
	case "tester":
		return agents.AgentTypeTester, nil
	default:
		return "", fmt.Errorf("invalid agent type '%s' (must be: diagnosticador, arquiteto, dev_senior, tester)", agentStr)
	}
}

// ListWorkflows lists available workflows from standard locations
func ListWorkflows() ([]WorkflowInfo, error) {
	workflows := make([]WorkflowInfo, 0)

	// Check ~/.vcli/workflows/ using fs helper
	workflowDir, err := vcliFs.GetVCLIWorkflowsDir()
	if err == nil {
		if entries, err := os.ReadDir(workflowDir); err == nil {
			for _, entry := range entries {
				if !entry.IsDir() && (filepath.Ext(entry.Name()) == ".yaml" || filepath.Ext(entry.Name()) == ".yml") {
					// Load workflow to get metadata
					workflowPath := filepath.Join(workflowDir, entry.Name())
					if workflow, err := loadWorkflowMetadata(workflowPath); err == nil {
						workflows = append(workflows, workflow)
					}
				}
			}
		}
	}

	// Check ./workflows/
	if entries, err := os.ReadDir("./workflows"); err == nil {
		for _, entry := range entries {
			if !entry.IsDir() && (filepath.Ext(entry.Name()) == ".yaml" || filepath.Ext(entry.Name()) == ".yml") {
				workflowPath := filepath.Join("./workflows", entry.Name())
				if workflow, err := loadWorkflowMetadata(workflowPath); err == nil {
					workflows = append(workflows, workflow)
				}
			}
		}
	}

	return workflows, nil
}

// WorkflowInfo contains metadata about a workflow
type WorkflowInfo struct {
	Name        string
	Description string
	StepCount   int
	FilePath    string
}

// loadWorkflowMetadata loads just the metadata from a workflow file
func loadWorkflowMetadata(filePath string) (WorkflowInfo, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return WorkflowInfo{}, err
	}

	var workflowYAML WorkflowYAML
	if err := yaml.Unmarshal(data, &workflowYAML); err != nil {
		return WorkflowInfo{}, err
	}

	return WorkflowInfo{
		Name:        workflowYAML.Name,
		Description: workflowYAML.Description,
		StepCount:   len(workflowYAML.Steps),
		FilePath:    filePath,
	}, nil
}
