package strategies

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents/language"
)

// TestNewPythonCodeGenStrategy tests constructor
func TestNewPythonCodeGenStrategy(t *testing.T) {
	tests := []struct {
		name             string
		oraculoEndpoint  string
		authToken        string
		expectOraculoUse bool
	}{
		{
			name:             "with oraculo endpoint",
			oraculoEndpoint:  "http://localhost:8080",
			authToken:        "test-token",
			expectOraculoUse: true,
		},
		{
			name:             "without oraculo endpoint",
			oraculoEndpoint:  "",
			authToken:        "",
			expectOraculoUse: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			strategy := NewPythonCodeGenStrategy(tt.oraculoEndpoint, tt.authToken)

			if strategy == nil {
				t.Fatal("NewPythonCodeGenStrategy() returned nil")
			}

			if strategy.useOraculo != tt.expectOraculoUse {
				t.Errorf("useOraculo = %v, want %v", strategy.useOraculo, tt.expectOraculoUse)
			}
		})
	}
}

// TestPythonCodeGenStrategy_Language tests language identification
func TestPythonCodeGenStrategy_Language(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	lang := strategy.Language()

	if lang != language.LanguagePython {
		t.Errorf("Language() = %v, want %v", lang, language.LanguagePython)
	}
}

// TestPythonCodeGenStrategy_GetCapabilities tests capability reporting
func TestPythonCodeGenStrategy_GetCapabilities(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	capabilities := strategy.GetCapabilities()

	if len(capabilities) == 0 {
		t.Error("GetCapabilities() returned no capabilities")
	}

	// Check for essential capabilities
	expectedCaps := []string{"formatting", "generation", "syntax"}
	for _, expected := range expectedCaps {
		found := false
		for _, cap := range capabilities {
			if strings.Contains(strings.ToLower(cap), expected) {
				found = true
				break
			}
		}
		if !found {
			t.Logf("GetCapabilities() might be missing %s capability", expected)
		}
	}
}

// TestPythonCodeGenStrategy_FormatCode tests code formatting
func TestPythonCodeGenStrategy_FormatCode(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	tests := []struct {
		name        string
		code        string
		shouldPass  bool
		description string
	}{
		{
			name: "simple valid code",
			code: `def hello():
    print("Hello, World!")
`,
			shouldPass:  true,
			description: "Should format simple valid code",
		},
		{
			name: "code with formatting issues",
			code: `def hello(  ):
  print(  "Hello"  )
`,
			shouldPass:  true,
			description: "Should fix spacing issues",
		},
		{
			name: "empty code",
			code: "",
			shouldPass:  true,
			description: "Should handle empty code gracefully",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			formatted, err := strategy.FormatCode(tt.code)

			// After fix: should NOT fail if formatters are unavailable
			// Should return original code with informational error
			if err != nil {
				t.Logf("FormatCode() error (acceptable if formatters unavailable): %v", err)
			}

			if formatted == "" && tt.code != "" {
				t.Error("FormatCode() returned empty string for non-empty input")
			}

			// Should return SOME output (formatted or original)
			if len(formatted) == 0 && len(tt.code) > 0 {
				t.Error("FormatCode() lost the code entirely")
			}
		})
	}
}

// TestPythonCodeGenStrategy_FormatCode_GracefulDegradation tests graceful degradation
func TestPythonCodeGenStrategy_FormatCode_GracefulDegradation(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	originalCode := `def test():
    x = 1
    return x
`

	formatted, err := strategy.FormatCode(originalCode)

	// KEY TEST: Even if black/autopep8 are missing, should return original code
	if formatted == "" {
		t.Fatal("FormatCode() should return original code if formatters unavailable")
	}

	// Should contain the original logic
	if !strings.Contains(formatted, "def test") {
		t.Error("FormatCode() lost function definition")
	}

	if !strings.Contains(formatted, "return x") {
		t.Error("FormatCode() lost return statement")
	}

	// Error is acceptable if formatters not available
	if err != nil {
		t.Logf("FormatCode() error (expected if formatters unavailable): %v", err)

		// Error message should be helpful
		if !strings.Contains(err.Error(), "format") {
			t.Errorf("Error message should mention formatting: %v", err)
		}
	}
}

// TestPythonCodeGenStrategy_ValidateSyntax tests syntax validation
func TestPythonCodeGenStrategy_ValidateSyntax(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	tests := []struct {
		name      string
		code      string
		wantError bool
	}{
		{
			name: "valid syntax",
			code: `def hello():
    return "Hello"
`,
			wantError: false,
		},
		{
			name: "invalid syntax",
			code: `def hello(
    return "Hello"
`,
			wantError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := strategy.ValidateSyntax(tt.code)

			if tt.wantError && err == nil {
				t.Error("ValidateSyntax() expected error for invalid syntax")
			}

			if !tt.wantError && err != nil {
				t.Errorf("ValidateSyntax() unexpected error for valid syntax: %v", err)
			}
		})
	}
}

// TestPythonCodeGenStrategy_GenerateCode tests code generation
func TestPythonCodeGenStrategy_GenerateCode(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	task := "Create a simple calculator function"
	contextData := map[string]interface{}{
		"framework": "standard",
	}

	changes, err := strategy.GenerateCode(ctx, task, contextData)

	if err != nil {
		t.Fatalf("GenerateCode() error: %v", err)
	}

	if len(changes) == 0 {
		t.Error("GenerateCode() returned no code changes")
	}

	// Check first change
	if len(changes) > 0 {
		change := changes[0]

		if change.Language != "python" {
			t.Errorf("Language = %q, want %q", change.Language, "python")
		}

		if change.Operation != "create" {
			t.Errorf("Operation = %q, want %q", change.Operation, "create")
		}

		if change.After == "" {
			t.Error("Generated code (After) is empty")
		}

		// Should contain Python code
		if !strings.Contains(change.After, "def") {
			t.Error("Generated code should contain function definition")
		}
	}
}

// TestPythonCodeGenStrategy_DetectFramework tests framework detection
func TestPythonCodeGenStrategy_DetectFramework(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	tests := []struct {
		name        string
		contextData map[string]interface{}
		want        string
	}{
		{
			name: "explicit framework",
			contextData: map[string]interface{}{
				"framework": "fastapi",
			},
			want: "fastapi",
		},
		{
			name: "detect from dependencies",
			contextData: map[string]interface{}{
				"dependencies": []string{"flask==2.0.0", "requests"},
			},
			want: "flask",
		},
		{
			name: "detect django",
			contextData: map[string]interface{}{
				"dependencies": []string{"django==4.0.0"},
			},
			want: "django",
		},
		{
			name:        "default to standard",
			contextData: map[string]interface{}{},
			want:        "standard",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := strategy.detectFramework(tt.contextData)

			if got != tt.want {
				t.Errorf("detectFramework() = %q, want %q", got, tt.want)
			}
		})
	}
}

// TestPythonCodeGenStrategy_GenerateTemplateCode tests template generation
func TestPythonCodeGenStrategy_GenerateTemplateCode(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	tests := []struct {
		name      string
		task      string
		framework string
	}{
		{"fastapi task", "Create REST API", "fastapi"},
		{"flask task", "Create web app", "flask"},
		{"standard task", "Create utility", "standard"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			code := strategy.generateTemplateCode(tt.task, tt.framework)

			if code == "" {
				t.Error("generateTemplateCode() returned empty code")
			}

			// Should contain task description
			if !strings.Contains(code, tt.task) {
				t.Error("Generated code should mention the task")
			}

			// Should contain framework
			if !strings.Contains(code, tt.framework) {
				t.Error("Generated code should mention the framework")
			}

			// Should be valid Python structure
			if !strings.Contains(code, "def main") {
				t.Error("Generated code should have main function")
			}
		})
	}
}

// TestPythonCodeGenStrategy_GetOutputFilePath tests file path generation
func TestPythonCodeGenStrategy_GetOutputFilePath(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	tests := []struct {
		name        string
		task        string
		contextData map[string]interface{}
		wantSuffix  string
	}{
		{
			name:        "simple task",
			task:        "Create Calculator",
			contextData: map[string]interface{}{},
			wantSuffix:  ".py",
		},
		{
			name:        "task with spaces",
			task:        "user authentication module",
			contextData: map[string]interface{}{},
			wantSuffix:  ".py",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			filePath := strategy.getOutputFilePath(tt.task, tt.contextData)

			if !strings.HasSuffix(filePath, tt.wantSuffix) {
				t.Errorf("getOutputFilePath() = %q, want suffix %q", filePath, tt.wantSuffix)
			}

			// Should not have spaces
			if strings.Contains(filePath, " ") {
				t.Errorf("getOutputFilePath() should not contain spaces: %q", filePath)
			}
		})
	}
}

// TestPythonCodeGenStrategy_DetermineOperation tests operation detection
func TestPythonCodeGenStrategy_DetermineOperation(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	tests := []struct {
		name        string
		filePath    string
		contextData map[string]interface{}
		want        string
	}{
		{
			name:     "new file",
			filePath: "new_module.py",
			contextData: map[string]interface{}{
				"existing_files": []string{"old_module.py"},
			},
			want: "create",
		},
		{
			name:     "existing file",
			filePath: "existing.py",
			contextData: map[string]interface{}{
				"existing_files": []string{"existing.py", "other.py"},
			},
			want: "modify",
		},
		{
			name:        "no context",
			filePath:    "some_file.py",
			contextData: map[string]interface{}{},
			want:        "create",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := strategy.determineOperation(tt.filePath, tt.contextData)

			if got != tt.want {
				t.Errorf("determineOperation() = %q, want %q", got, tt.want)
			}
		})
	}
}

// TestPythonCodeGenStrategy_BuildPrompt tests prompt building
func TestPythonCodeGenStrategy_BuildPrompt(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	task := "Create user authentication"
	contextData := map[string]interface{}{
		"architecture_plan": "Microservices architecture",
		"dependencies":      []string{"fastapi", "pydantic"},
	}

	prompt := strategy.buildPrompt(task, contextData)

	if prompt == "" {
		t.Error("buildPrompt() returned empty prompt")
	}

	// Should contain task
	if !strings.Contains(prompt, task) {
		t.Error("Prompt should contain task description")
	}

	// Should contain architecture
	if !strings.Contains(prompt, "Microservices") {
		t.Error("Prompt should contain architecture plan")
	}

	// Should contain Python best practices
	if !strings.Contains(prompt, "PEP 8") {
		t.Error("Prompt should mention PEP 8")
	}
}

// TestPythonCodeGenStrategy_Integration tests realistic workflow
func TestPythonCodeGenStrategy_Integration(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Full workflow: Generate -> Format -> Validate
	task := "Create a simple greeting function"
	contextData := map[string]interface{}{
		"framework": "standard",
	}

	// Step 1: Generate
	changes, err := strategy.GenerateCode(ctx, task, contextData)
	if err != nil {
		t.Fatalf("GenerateCode() error: %v", err)
	}

	if len(changes) == 0 {
		t.Fatal("No code changes generated")
	}

	generatedCode := changes[0].After

	// Step 2: Format (should not fail even if formatters unavailable)
	formatted, err := strategy.FormatCode(generatedCode)
	if err != nil {
		t.Logf("FormatCode() error (acceptable): %v", err)
	}

	if formatted == "" {
		t.Error("Formatting resulted in empty code")
	}

	// Step 3: Validate syntax
	if err := strategy.ValidateSyntax(formatted); err != nil {
		t.Errorf("Generated and formatted code has syntax errors: %v", err)
	}

	t.Logf("Integration test successful - Generated %d lines", len(strings.Split(formatted, "\n")))
}

// TestPythonCodeGenStrategy_EmptyTask tests edge case handling
func TestPythonCodeGenStrategy_EmptyTask(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	ctx := context.Background()

	// Empty task
	changes, err := strategy.GenerateCode(ctx, "", map[string]interface{}{})

	// Should not crash
	if err != nil {
		t.Logf("GenerateCode() with empty task error: %v", err)
	}

	// Should still return something (even if minimal)
	if changes == nil {
		t.Error("GenerateCode() should return non-nil changes even for empty task")
	}
}

// TestPythonCodeGenStrategy_ContextCancellation tests context handling
func TestPythonCodeGenStrategy_ContextCancellation(t *testing.T) {
	strategy := NewPythonCodeGenStrategy("", "")

	// Create already-cancelled context
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err := strategy.GenerateCode(ctx, "test task", map[string]interface{}{})

	// Context cancellation is acceptable
	if err != nil {
		t.Logf("GenerateCode() with cancelled context: %v", err)
	}
}
