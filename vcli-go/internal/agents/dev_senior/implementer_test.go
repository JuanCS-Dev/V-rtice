package dev_senior

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// TestNewDevSeniorAgent tests agent initialization
func TestNewDevSeniorAgent(t *testing.T) {
	tests := []struct {
		name   string
		config agents.AgentConfig
	}{
		{
			name: "with_minimal_config",
			config: agents.AgentConfig{
				Type:                   agents.AgentTypeDevSenior,
				WorkspacePath:          "/tmp/test",
				MaximusOraculoEndpoint: "http://localhost:8080",
			},
		},
		{
			name: "with_full_config",
			config: agents.AgentConfig{
				Type:                   agents.AgentTypeDevSenior,
				WorkspacePath:          "/tmp/test",
				MaximusOraculoEndpoint: "http://localhost:8080",
				AuthToken:              "test-token",
				RetryConfig: agents.RetryConfig{
					Enabled:            true,
					MaxRetries:         3,
					BackoffStrategy:    "exponential",
					InitialBackoff:     time.Second,
					EnableReflection:   true,
					MaxReflectionDepth: 2,
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDevSeniorAgent(tt.config)

			if agent == nil {
				t.Fatal("NewDevSeniorAgent returned nil")
			}

			if agent.config.Type != tt.config.Type {
				t.Errorf("config.Type = %v, want %v", agent.config.Type, tt.config.Type)
			}

			if agent.status != agents.StatusIdle {
				t.Errorf("status = %v, want %v", agent.status, agents.StatusIdle)
			}

			if agent.logger == nil {
				t.Error("logger is nil")
			}

			if agent.oraculoClient == nil {
				t.Error("oraculoClient is nil")
			}

			if agent.planningEngine == nil {
				t.Error("planningEngine is nil")
			}

			if agent.selfHealing == nil {
				t.Error("selfHealing is nil")
			}

			if agent.reflectionEngine == nil {
				t.Error("reflectionEngine is nil")
			}
		})
	}
}

// TestType tests the Type method
func TestType(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	if got := agent.Type(); got != agents.AgentTypeDevSenior {
		t.Errorf("Type() = %v, want %v", got, agents.AgentTypeDevSenior)
	}
}

// TestName tests the Name method
func TestName(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	name := agent.Name()
	if name == "" {
		t.Error("Name() returned empty string")
	}

	if !strings.Contains(name, "DEV SENIOR") {
		t.Errorf("Name() = %q, want to contain 'DEV SENIOR'", name)
	}
}

// TestGetCapabilities tests the GetCapabilities method
func TestGetCapabilities(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	caps := agent.GetCapabilities()
	if len(caps) == 0 {
		t.Error("GetCapabilities() returned empty slice")
	}

	expectedCaps := []string{
		"Autonomous code generation",
		"File operations",
		"Git operations",
		"Code formatting",
		"Compilation validation",
		"Basic test execution",
	}

	for _, expected := range expectedCaps {
		found := false
		for _, cap := range caps {
			if strings.Contains(cap, expected) {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("GetCapabilities() missing capability containing %q", expected)
		}
	}
}

// TestGetStatus tests the GetStatus method
func TestGetStatus(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	if got := agent.GetStatus(); got != agents.StatusIdle {
		t.Errorf("GetStatus() = %v, want %v", got, agents.StatusIdle)
	}

	// Simulate status change
	agent.status = agents.StatusRunning
	if got := agent.GetStatus(); got != agents.StatusRunning {
		t.Errorf("GetStatus() = %v, want %v", got, agents.StatusRunning)
	}
}

// TestValidate tests the Validate method
func TestValidate(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name    string
		input   agents.AgentInput
		wantErr bool
	}{
		{
			name: "valid_input",
			input: agents.AgentInput{
				Task:    "Implement feature X",
				Targets: []string{"./pkg/feature"},
				Context: make(map[string]interface{}),
			},
			wantErr: false,
		},
		{
			name: "empty_task",
			input: agents.AgentInput{
				Task:    "",
				Targets: []string{"./pkg/feature"},
				Context: make(map[string]interface{}),
			},
			wantErr: true,
		},
		{
			name: "minimal_input",
			input: agents.AgentInput{
				Task: "Simple task",
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := agent.Validate(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("Validate() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// TestBuildContextData tests the buildContextData method
func TestBuildContextData(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name     string
		input    agents.AgentInput
		archPlan *agents.ArchitecturePlan
		wantKeys []string
	}{
		{
			name: "with_architecture_plan",
			input: agents.AgentInput{
				Task:    "Test task",
				Targets: []string{"./test"},
				Context: map[string]interface{}{
					"existing_code": "package main",
					"dependencies":  []string{"dep1", "dep2"},
				},
			},
			archPlan: &agents.ArchitecturePlan{
				PlanID: "test-plan",
				Steps: []agents.ImplementationStep{
					{StepNumber: 1, Description: "Step 1"},
				},
			},
			wantKeys: []string{"architecture_plan", "implementation_steps", "existing_code", "dependencies", "targets"},
		},
		{
			name: "without_architecture_plan",
			input: agents.AgentInput{
				Task:    "Test task",
				Targets: []string{"./test"},
				Context: map[string]interface{}{
					"framework": "cobra",
				},
			},
			archPlan: nil,
			wantKeys: []string{"framework", "targets"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := agent.buildContextData(tt.input, tt.archPlan)

			if result == nil {
				t.Fatal("buildContextData returned nil")
			}

			for _, key := range tt.wantKeys {
				if _, ok := result[key]; !ok {
					t.Errorf("buildContextData() missing key %q", key)
				}
			}
		})
	}
}

// TestExtractArchitecturePlan tests the extractArchitecturePlan method
func TestExtractArchitecturePlan(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name    string
		context map[string]interface{}
		want    bool // true if plan should be found
	}{
		{
			name: "with_valid_plan",
			context: map[string]interface{}{
				"arquiteto_output": &agents.AgentOutput{
					Result: &agents.ArchitecturePlan{
						PlanID: "test-plan-123",
						Title:  "Test Architecture",
					},
				},
			},
			want: true,
		},
		{
			name: "without_plan",
			context: map[string]interface{}{
				"other_data": "value",
			},
			want: false,
		},
		{
			name: "with_invalid_plan_type",
			context: map[string]interface{}{
				"arquiteto_output": &agents.AgentOutput{
					Result: "not a plan",
				},
			},
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			plan := agent.extractArchitecturePlan(tt.context)

			if tt.want && plan == nil {
				t.Error("extractArchitecturePlan() = nil, want plan")
			}

			if !tt.want && plan != nil {
				t.Error("extractArchitecturePlan() = plan, want nil")
			}
		})
	}
}

// TestConvertToCodeChanges tests the convertToCodeChanges method
func TestConvertToCodeChanges(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name            string
		strategyChanges []agents.CodeChange
		wantCreated     int
		wantModified    int
		wantDeleted     int
	}{
		{
			name: "mixed_operations",
			strategyChanges: []agents.CodeChange{
				{FilePath: "file1.go", Operation: "create", After: "package main"},
				{FilePath: "file2.go", Operation: "modify", Before: "old", After: "new"},
				{FilePath: "file3.go", Operation: "delete", Before: "content"},
				{FilePath: "file4.go", Operation: "create", After: "package test"},
			},
			wantCreated:  2,
			wantModified: 1,
			wantDeleted:  1,
		},
		{
			name:            "empty_changes",
			strategyChanges: []agents.CodeChange{},
			wantCreated:     0,
			wantModified:    0,
			wantDeleted:     0,
		},
		{
			name: "only_creates",
			strategyChanges: []agents.CodeChange{
				{FilePath: "new1.go", Operation: "create", After: "content1"},
				{FilePath: "new2.go", Operation: "create", After: "content2"},
			},
			wantCreated:  2,
			wantModified: 0,
			wantDeleted:  0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := agent.convertToCodeChanges(tt.strategyChanges)

			if result == nil {
				t.Fatal("convertToCodeChanges returned nil")
			}

			if len(result.FilesCreated) != tt.wantCreated {
				t.Errorf("FilesCreated count = %d, want %d", len(result.FilesCreated), tt.wantCreated)
			}

			if len(result.FilesModified) != tt.wantModified {
				t.Errorf("FilesModified count = %d, want %d", len(result.FilesModified), tt.wantModified)
			}

			if len(result.FilesDeleted) != tt.wantDeleted {
				t.Errorf("FilesDeleted count = %d, want %d", len(result.FilesDeleted), tt.wantDeleted)
			}
		})
	}
}

// TestCreateFile tests the createFile method
func TestCreateFile(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	// Create temporary directory for tests
	tmpDir := t.TempDir()

	tests := []struct {
		name     string
		filepath string
		content  string
		wantErr  bool
	}{
		{
			name:     "simple_file",
			filepath: filepath.Join(tmpDir, "test1.txt"),
			content:  "Hello, World!",
			wantErr:  false,
		},
		{
			name:     "file_in_subdirectory",
			filepath: filepath.Join(tmpDir, "subdir", "test2.txt"),
			content:  "Content in subdirectory",
			wantErr:  false,
		},
		{
			name:     "nested_subdirectory",
			filepath: filepath.Join(tmpDir, "a", "b", "c", "test3.txt"),
			content:  "Deeply nested content",
			wantErr:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := agent.createFile(tt.filepath, tt.content)
			if (err != nil) != tt.wantErr {
				t.Errorf("createFile() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				// Verify file was created
				if _, err := os.Stat(tt.filepath); os.IsNotExist(err) {
					t.Errorf("createFile() did not create file at %s", tt.filepath)
				}

				// Verify content
				content, err := os.ReadFile(tt.filepath)
				if err != nil {
					t.Fatalf("failed to read created file: %v", err)
				}

				if string(content) != tt.content {
					t.Errorf("file content = %q, want %q", string(content), tt.content)
				}
			}
		})
	}
}

// TestModifyFile tests the modifyFile method
func TestModifyFile(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tmpDir := t.TempDir()

	tests := []struct {
		name        string
		setupFile   bool
		initialContent string
		filepath    string
		newContent  string
		wantErr     bool
	}{
		{
			name:           "modify_existing_file",
			setupFile:      true,
			initialContent: "old content",
			filepath:       filepath.Join(tmpDir, "modify1.txt"),
			newContent:     "new content",
			wantErr:        false,
		},
		{
			name:       "modify_nonexistent_file",
			setupFile:  false,
			filepath:   filepath.Join(tmpDir, "nonexistent.txt"),
			newContent: "content",
			wantErr:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup: create file if needed
			if tt.setupFile {
				if err := os.WriteFile(tt.filepath, []byte(tt.initialContent), 0644); err != nil {
					t.Fatalf("failed to setup test file: %v", err)
				}
			}

			err := agent.modifyFile(tt.filepath, tt.newContent)
			if (err != nil) != tt.wantErr {
				t.Errorf("modifyFile() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				// Verify content was updated
				content, err := os.ReadFile(tt.filepath)
				if err != nil {
					t.Fatalf("failed to read modified file: %v", err)
				}

				if string(content) != tt.newContent {
					t.Errorf("file content = %q, want %q", string(content), tt.newContent)
				}
			}
		})
	}
}

// TestDeleteFile tests the deleteFile method
func TestDeleteFile(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tmpDir := t.TempDir()

	tests := []struct {
		name      string
		setupFile bool
		filepath  string
		wantErr   bool
	}{
		{
			name:      "delete_existing_file",
			setupFile: true,
			filepath:  filepath.Join(tmpDir, "delete1.txt"),
			wantErr:   false,
		},
		{
			name:      "delete_nonexistent_file",
			setupFile: false,
			filepath:  filepath.Join(tmpDir, "nonexistent.txt"),
			wantErr:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup: create file if needed
			if tt.setupFile {
				if err := os.WriteFile(tt.filepath, []byte("content"), 0644); err != nil {
					t.Fatalf("failed to setup test file: %v", err)
				}
			}

			err := agent.deleteFile(tt.filepath)
			if (err != nil) != tt.wantErr {
				t.Errorf("deleteFile() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				// Verify file was deleted
				if _, err := os.Stat(tt.filepath); !os.IsNotExist(err) {
					t.Errorf("deleteFile() did not delete file at %s", tt.filepath)
				}
			}
		})
	}
}

// TestApplyCodeChanges tests the applyCodeChanges method
func TestApplyCodeChanges(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tmpDir := t.TempDir()

	// Create a file to be modified/deleted
	existingFile := filepath.Join(tmpDir, "existing.txt")
	if err := os.WriteFile(existingFile, []byte("original"), 0644); err != nil {
		t.Fatalf("failed to setup test file: %v", err)
	}

	changes := &CodeChanges{
		FilesCreated:  []string{filepath.Join(tmpDir, "new.txt")},
		FilesModified: []string{existingFile},
		FilesDeleted:  []string{},
		Changes: map[string]string{
			filepath.Join(tmpDir, "new.txt"): "new content",
			existingFile:                      "modified content",
		},
	}

	modified, err := agent.applyCodeChanges(changes)
	if err != nil {
		t.Fatalf("applyCodeChanges() error = %v", err)
	}

	if len(modified) != 2 {
		t.Errorf("applyCodeChanges() modified %d files, want 2", len(modified))
	}

	// Verify new file was created
	newContent, err := os.ReadFile(filepath.Join(tmpDir, "new.txt"))
	if err != nil {
		t.Errorf("new file was not created: %v", err)
	} else if string(newContent) != "new content" {
		t.Errorf("new file content = %q, want %q", string(newContent), "new content")
	}

	// Verify existing file was modified
	modContent, err := os.ReadFile(existingFile)
	if err != nil {
		t.Errorf("modified file not found: %v", err)
	} else if string(modContent) != "modified content" {
		t.Errorf("modified file content = %q, want %q", string(modContent), "modified content")
	}
}

// TestCalculateCodeQuality tests the calculateCodeQuality method
func TestCalculateCodeQuality(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name          string
		compilation   *CompilationResult
		test          *TestResult
		wantScore     float64
		scoreRange    [2]float64 // min, max acceptable range
	}{
		{
			name: "perfect_quality",
			compilation: &CompilationResult{
				Success: true,
				Errors:  []string{},
			},
			test: &TestResult{
				TotalTests:  10,
				PassedTests: 10,
				FailedTests: 0,
			},
			wantScore:  100.0,
			scoreRange: [2]float64{100.0, 100.0},
		},
		{
			name: "compilation_success_no_tests",
			compilation: &CompilationResult{
				Success: true,
				Errors:  []string{},
			},
			test: &TestResult{
				TotalTests:  0,
				PassedTests: 0,
				FailedTests: 0,
			},
			wantScore:  60.0,
			scoreRange: [2]float64{60.0, 60.0},
		},
		{
			name: "compilation_success_half_tests_pass",
			compilation: &CompilationResult{
				Success: true,
				Errors:  []string{},
			},
			test: &TestResult{
				TotalTests:  10,
				PassedTests: 5,
				FailedTests: 5,
			},
			wantScore:  80.0,
			scoreRange: [2]float64{80.0, 80.0},
		},
		{
			name: "compilation_failure",
			compilation: &CompilationResult{
				Success: false,
				Errors:  []string{"error 1", "error 2"},
			},
			test: &TestResult{
				TotalTests:  10,
				PassedTests: 10,
				FailedTests: 0,
			},
			wantScore:  40.0,
			scoreRange: [2]float64{40.0, 40.0},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			score := agent.calculateCodeQuality(tt.compilation, tt.test)

			if score < tt.scoreRange[0] || score > tt.scoreRange[1] {
				t.Errorf("calculateCodeQuality() = %.1f, want in range [%.1f, %.1f]",
					score, tt.scoreRange[0], tt.scoreRange[1])
			}
		})
	}
}

// TestGenerateRecommendations tests the generateRecommendations method
func TestGenerateRecommendations(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name        string
		compilation *CompilationResult
		test        *TestResult
		changes     *CodeChanges
		wantContain []string
		minRecs     int
	}{
		{
			name: "compilation_errors",
			compilation: &CompilationResult{
				Success: false,
				Errors:  []string{"syntax error", "type error"},
			},
			test: &TestResult{
				TotalTests:  0,
				PassedTests: 0,
				FailedTests: 0,
			},
			changes:     &CodeChanges{},
			wantContain: []string{"compilation errors"},
			minRecs:     2,
		},
		{
			name: "test_failures",
			compilation: &CompilationResult{
				Success: true,
			},
			test: &TestResult{
				TotalTests:  10,
				PassedTests: 5,
				FailedTests: 5,
			},
			changes:     &CodeChanges{},
			wantContain: []string{"failing tests"},
			minRecs:     1,
		},
		{
			name: "no_tests",
			compilation: &CompilationResult{
				Success: true,
			},
			test: &TestResult{
				TotalTests:  0,
				PassedTests: 0,
				FailedTests: 0,
			},
			changes:     &CodeChanges{},
			wantContain: []string{"unit tests"},
			minRecs:     1,
		},
		{
			name: "all_good",
			compilation: &CompilationResult{
				Success: true,
			},
			test: &TestResult{
				TotalTests:  10,
				PassedTests: 10,
				FailedTests: 0,
			},
			changes:     &CodeChanges{},
			wantContain: []string{"ready"},
			minRecs:     1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			recs := agent.generateRecommendations(tt.compilation, tt.test, tt.changes)

			if len(recs) < tt.minRecs {
				t.Errorf("generateRecommendations() returned %d recommendations, want at least %d",
					len(recs), tt.minRecs)
			}

			for _, want := range tt.wantContain {
				found := false
				for _, rec := range recs {
					if strings.Contains(strings.ToLower(rec), strings.ToLower(want)) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("recommendations don't contain %q, got %v", want, recs)
				}
			}
		})
	}
}

// TestFormatCode tests the formatCode method
func TestFormatCode(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tmpDir := t.TempDir()

	// Create a test Go file with unformatted code
	goFile := filepath.Join(tmpDir, "test.go")
	unformattedCode := `package main

import "fmt"

func main(){
fmt.Println("hello")
}`

	if err := os.WriteFile(goFile, []byte(unformattedCode), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	// Create a non-Go file (should be skipped)
	txtFile := filepath.Join(tmpDir, "test.txt")
	if err := os.WriteFile(txtFile, []byte("text content"), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	files := []string{goFile, txtFile}

	// formatCode should not error even if goimports is not available
	if err := agent.formatCode(files); err != nil {
		t.Errorf("formatCode() error = %v, want nil", err)
	}

	// Note: We can't verify the actual formatting without gofmt/goimports installed
	// This test mainly verifies the method doesn't crash
}

// TestCompileCode tests the compileCode method
func TestCompileCode(t *testing.T) {
	// This test requires being in a valid Go module
	// We'll test the basic structure of the result

	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	result, _ := agent.compileCode()

	// Result should never be nil, even on error
	if result == nil {
		t.Fatal("compileCode() returned nil result")
	}

	// Check result structure
	if result.Output == "" && result.Success {
		// If success is true, output might be empty (successful compilation)
		// This is valid
	}

	// Errors slice should be initialized
	if result.Errors == nil {
		t.Error("compileCode() result.Errors is nil, should be initialized")
	}
}

// TestRunTests tests the runTests method
func TestRunTests(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name    string
		targets []string
	}{
		{
			name:    "default_targets",
			targets: []string{},
		},
		{
			name:    "specific_targets",
			targets: []string{"./internal/agents/dev_senior"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := agent.runTests(tt.targets)

			// Result should never be nil
			if result == nil {
				t.Fatal("runTests() returned nil result")
			}

			// Check result structure
			if result.Output == "" && err == nil {
				// Empty output is valid if no tests were run
			}

			// Verify result fields are initialized
			if result.TotalTests < 0 {
				t.Error("runTests() result.TotalTests is negative")
			}
		})
	}
}

// TestCreateGitBranch tests the createGitBranch method
func TestCreateGitBranch(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	tests := []struct {
		name     string
		task     string
		wantLen  int // expected max length of branch name
	}{
		{
			name:    "simple_task",
			task:    "Add feature X",
			wantLen: 50,
		},
		{
			name:    "long_task",
			task:    "This is a very long task description that should be truncated to fit the maximum branch name length",
			wantLen: 50,
		},
		{
			name:    "task_with_special_chars",
			task:    "Fix: bug in module/package",
			wantLen: 50,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Note: This will fail if not in a git repository
			// We're mainly testing the branch name generation logic
			branchName, _ := agent.createGitBranch(tt.task)

			// If branchName is empty, git operation failed (expected in test env)
			// But we can't test the actual git operation without a repo
			if branchName != "" {
				if len(branchName) > tt.wantLen {
					t.Errorf("createGitBranch() branch name length = %d, want <= %d",
						len(branchName), tt.wantLen)
				}

				// Branch name should not contain invalid characters
				if strings.Contains(branchName, ":") || strings.Contains(branchName, " ") {
					t.Errorf("createGitBranch() branch name %q contains invalid characters", branchName)
				}
			}
		})
	}
}

// TestDisplayPlan tests the displayPlan method
func TestDisplayPlan(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	plan := &agents.ImplementationPlan{
		PlanID:   "test-plan-123",
		Approach: "Use TDD approach with comprehensive tests",
		FilesToCreate: []string{
			"pkg/feature/feature.go",
			"pkg/feature/feature_test.go",
		},
		FilesToModify: []string{
			"cmd/main.go",
		},
		FilesToDelete: []string{
			"deprecated/old.go",
		},
		TestsNeeded: []string{
			"TestFeatureBasic",
			"TestFeatureEdgeCases",
		},
		Risks: []string{
			"Breaking change to API",
		},
		Dependencies: []string{
			"github.com/example/lib",
		},
		Complexity: 7,
	}

	// displayPlan should not panic or error
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("displayPlan() panicked: %v", r)
		}
	}()

	agent.displayPlan(plan)
}

// TestExecute_BasicFlow tests the Execute method with a basic flow
func TestExecute_BasicFlow(t *testing.T) {
	t.Skip("Skipping integration test - requires full setup")

	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type:                   agents.AgentTypeDevSenior,
		MaximusOraculoEndpoint: "http://localhost:8080",
		RetryConfig: agents.RetryConfig{
			Enabled: false, // Disable retry for simpler test
		},
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task:    "Create a simple hello function",
		Targets: []string{"."},
		Context: make(map[string]interface{}),
		Config: map[string]interface{}{
			"skip_planning": true, // Skip planning for faster test
		},
		HITLEnabled: false,
	}

	output, err := agent.Execute(ctx, input)

	// Basic validation
	if err != nil {
		t.Logf("Execute() error (expected in test environment): %v", err)
	}

	if output != nil {
		if output.AgentType != agents.AgentTypeDevSenior {
			t.Errorf("output.AgentType = %v, want %v", output.AgentType, agents.AgentTypeDevSenior)
		}

		if output.StartedAt.IsZero() {
			t.Error("output.StartedAt is zero")
		}

		if output.Metrics == nil {
			t.Error("output.Metrics is nil")
		}
	}
}

// TestExecute_WithLanguageDetection tests Execute with language detection
func TestExecute_WithLanguageDetection(t *testing.T) {
	t.Skip("Skipping integration test - requires full setup")

	// Create a temporary Go project
	tmpDir := t.TempDir()
	goMod := filepath.Join(tmpDir, "go.mod")
	if err := os.WriteFile(goMod, []byte("module test\n\ngo 1.21\n"), 0644); err != nil {
		t.Fatalf("failed to create go.mod: %v", err)
	}

	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type:                   agents.AgentTypeDevSenior,
		WorkspacePath:          tmpDir,
		MaximusOraculoEndpoint: "http://localhost:8080",
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task:    "Add a utility function",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
		Config: map[string]interface{}{
			"skip_planning": true,
		},
	}

	// Should detect Go language
	detector := language.NewDetector()
	result, err := detector.Detect(input.Targets)
	if err != nil {
		t.Fatalf("language detection failed: %v", err)
	}

	if result.Primary != language.LanguageGo {
		t.Errorf("detected language = %v, want %v", result.Primary, language.LanguageGo)
	}

	// Now run Execute (may fail due to missing dependencies, but that's OK)
	if _, err := agent.Execute(ctx, input); err != nil {
		t.Logf("Execute failed (expected in test environment): %v", err)
	}
}

// TestExecute_ValidationError tests Execute with invalid input
func TestExecute_ValidationError(t *testing.T) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	input := agents.AgentInput{
		Task:    "", // Invalid: empty task
		Targets: []string{},
	}

	// Validate should fail before Execute
	err := agent.Validate(input)
	if err == nil {
		t.Error("Validate() with empty task should return error")
	}
}

// Benchmark tests

func BenchmarkNewDevSeniorAgent(b *testing.B) {
	config := agents.AgentConfig{
		Type:                   agents.AgentTypeDevSenior,
		MaximusOraculoEndpoint: "http://localhost:8080",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = NewDevSeniorAgent(config)
	}
}

func BenchmarkBuildContextData(b *testing.B) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	input := agents.AgentInput{
		Task:    "Test task",
		Targets: []string{"./test"},
		Context: map[string]interface{}{
			"existing_code": "package main",
			"dependencies":  []string{"dep1", "dep2"},
		},
	}

	archPlan := &agents.ArchitecturePlan{
		PlanID: "test-plan",
		Steps: []agents.ImplementationStep{
			{StepNumber: 1, Description: "Step 1"},
		},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = agent.buildContextData(input, archPlan)
	}
}

func BenchmarkCalculateCodeQuality(b *testing.B) {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	compilation := &CompilationResult{
		Success: true,
		Errors:  []string{},
	}

	test := &TestResult{
		TotalTests:  100,
		PassedTests: 95,
		FailedTests: 5,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = agent.calculateCodeQuality(compilation, test)
	}
}

// Example tests

func ExampleDevSeniorAgent_GetCapabilities() {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	capabilities := agent.GetCapabilities()
	fmt.Printf("Agent has %d capabilities\n", len(capabilities))
	// Output is non-deterministic due to implementation details
}

func ExampleDevSeniorAgent_Validate() {
	agent := NewDevSeniorAgent(agents.AgentConfig{
		Type: agents.AgentTypeDevSenior,
	})

	// Valid input
	validInput := agents.AgentInput{
		Task:    "Implement feature X",
		Targets: []string{"./pkg/feature"},
	}

	if err := agent.Validate(validInput); err != nil {
		fmt.Println("Validation failed:", err)
	} else {
		fmt.Println("Valid input")
	}

	// Invalid input
	invalidInput := agents.AgentInput{
		Task: "", // Empty task
	}

	if err := agent.Validate(invalidInput); err != nil {
		fmt.Println("Validation failed: empty task")
	}

	// Output:
	// Valid input
	// Validation failed: empty task
}
