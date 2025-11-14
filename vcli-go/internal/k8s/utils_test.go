package k8s

import (
	"encoding/json"
	"strings"
	"testing"

	"gopkg.in/yaml.v3"
)

// TestParseLabels tests the ParseLabels function
func TestParseLabels(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		want      map[string]string
		wantErr   bool
		errSubstr string
	}{
		{
			name:  "empty string",
			input: "",
			want:  map[string]string{},
		},
		{
			name:  "single label",
			input: "app=nginx",
			want:  map[string]string{"app": "nginx"},
		},
		{
			name:  "multiple labels",
			input: "app=nginx,env=prod,version=1.0",
			want: map[string]string{
				"app":     "nginx",
				"env":     "prod",
				"version": "1.0",
			},
		},
		{
			name:  "labels with spaces",
			input: " app = nginx , env = prod ",
			want: map[string]string{
				"app": "nginx",
				"env": "prod",
			},
		},
		{
			name:  "empty value",
			input: "app=nginx,env=",
			want: map[string]string{
				"app": "nginx",
				"env": "",
			},
		},
		{
			name:  "trailing comma",
			input: "app=nginx,env=prod,",
			want: map[string]string{
				"app": "nginx",
				"env": "prod",
			},
		},
		{
			name:  "multiple commas",
			input: "app=nginx,,env=prod",
			want: map[string]string{
				"app": "nginx",
				"env": "prod",
			},
		},
		{
			name:      "missing equals sign",
			input:     "app=nginx,invalidlabel",
			wantErr:   true,
			errSubstr: "invalid label format",
		},
		{
			name:      "empty key",
			input:     "app=nginx,=value",
			wantErr:   true,
			errSubstr: "empty label key",
		},
		{
			name:      "no value after equals",
			input:     "app=nginx,key",
			wantErr:   true,
			errSubstr: "invalid label format",
		},
		{
			name:  "special characters in value",
			input: "app=my-app,version=v1.2.3",
			want: map[string]string{
				"app":     "my-app",
				"version": "v1.2.3",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParseLabels(tt.input)

			if tt.wantErr {
				if err == nil {
					t.Errorf("ParseLabels() expected error, got nil")
					return
				}
				if tt.errSubstr != "" && !strings.Contains(err.Error(), tt.errSubstr) {
					t.Errorf("ParseLabels() error = %v, want substring %q", err, tt.errSubstr)
				}
				return
			}

			if err != nil {
				t.Errorf("ParseLabels() unexpected error: %v", err)
				return
			}

			if len(got) != len(tt.want) {
				t.Errorf("ParseLabels() got %d labels, want %d", len(got), len(tt.want))
			}

			for key, wantValue := range tt.want {
				gotValue, ok := got[key]
				if !ok {
					t.Errorf("ParseLabels() missing key %q", key)
					continue
				}
				if gotValue != wantValue {
					t.Errorf("ParseLabels() key %q = %q, want %q", key, gotValue, wantValue)
				}
			}
		})
	}
}

// TestParseLiteral tests the ParseLiteral function
func TestParseLiteral(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		wantKey   string
		wantValue string
		wantErr   bool
		errSubstr string
	}{
		{
			name:      "valid key-value",
			input:     "key=value",
			wantKey:   "key",
			wantValue: "value",
		},
		{
			name:      "with spaces",
			input:     " key = value ",
			wantKey:   "key",
			wantValue: "value",
		},
		{
			name:      "empty value",
			input:     "key=",
			wantKey:   "key",
			wantValue: "",
		},
		{
			name:      "value with equals sign",
			input:     "key=value=with=equals",
			wantKey:   "key",
			wantValue: "value=with=equals",
		},
		{
			name:      "special characters",
			input:     "my-key=my-value",
			wantKey:   "my-key",
			wantValue: "my-value",
		},
		{
			name:      "numeric value",
			input:     "port=8080",
			wantKey:   "port",
			wantValue: "8080",
		},
		{
			name:      "missing equals sign",
			input:     "keyvalue",
			wantErr:   true,
			errSubstr: "invalid format",
		},
		{
			name:      "empty key",
			input:     "=value",
			wantErr:   true,
			errSubstr: "empty key",
		},
		{
			name:      "only spaces as key",
			input:     "  =value",
			wantErr:   true,
			errSubstr: "empty key",
		},
		{
			name:      "empty string",
			input:     "",
			wantErr:   true,
			errSubstr: "invalid format",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotKey, gotValue, err := ParseLiteral(tt.input)

			if tt.wantErr {
				if err == nil {
					t.Errorf("ParseLiteral() expected error, got nil")
					return
				}
				if tt.errSubstr != "" && !strings.Contains(err.Error(), tt.errSubstr) {
					t.Errorf("ParseLiteral() error = %v, want substring %q", err, tt.errSubstr)
				}
				return
			}

			if err != nil {
				t.Errorf("ParseLiteral() unexpected error: %v", err)
				return
			}

			if gotKey != tt.wantKey {
				t.Errorf("ParseLiteral() key = %q, want %q", gotKey, tt.wantKey)
			}

			if gotValue != tt.wantValue {
				t.Errorf("ParseLiteral() value = %q, want %q", gotValue, tt.wantValue)
			}
		})
	}
}

// TestFormatOutput tests the FormatOutput function
func TestFormatOutput(t *testing.T) {
	testObj := map[string]interface{}{
		"name":    "test",
		"version": "1.0",
		"nested": map[string]string{
			"key": "value",
		},
	}

	tests := []struct {
		name      string
		obj       interface{}
		format    string
		wantErr   bool
		errSubstr string
		validate  func(t *testing.T, output string)
	}{
		{
			name:   "json format",
			obj:    testObj,
			format: "json",
			validate: func(t *testing.T, output string) {
				var result map[string]interface{}
				err := json.Unmarshal([]byte(output), &result)
				if err != nil {
					t.Errorf("Output is not valid JSON: %v", err)
				}
				if result["name"] != "test" {
					t.Errorf("JSON name = %v, want 'test'", result["name"])
				}
			},
		},
		{
			name:   "yaml format",
			obj:    testObj,
			format: "yaml",
			validate: func(t *testing.T, output string) {
				var result map[string]interface{}
				err := yaml.Unmarshal([]byte(output), &result)
				if err != nil {
					t.Errorf("Output is not valid YAML: %v", err)
				}
				if result["name"] != "test" {
					t.Errorf("YAML name = %v, want 'test'", result["name"])
				}
			},
		},
		{
			name:   "wide format (default to JSON)",
			obj:    testObj,
			format: "wide",
			validate: func(t *testing.T, output string) {
				var result map[string]interface{}
				err := json.Unmarshal([]byte(output), &result)
				if err != nil {
					t.Errorf("Wide format output is not valid JSON: %v", err)
				}
			},
		},
		{
			name:   "empty format (default to JSON)",
			obj:    testObj,
			format: "",
			validate: func(t *testing.T, output string) {
				var result map[string]interface{}
				err := json.Unmarshal([]byte(output), &result)
				if err != nil {
					t.Errorf("Empty format output is not valid JSON: %v", err)
				}
			},
		},
		{
			name:      "unsupported format",
			obj:       testObj,
			format:    "xml",
			wantErr:   true,
			errSubstr: "unsupported output format",
		},
		{
			name:   "nil object to JSON",
			obj:    nil,
			format: "json",
			validate: func(t *testing.T, output string) {
				if output != "null" {
					t.Errorf("nil object to JSON = %q, want 'null'", output)
				}
			},
		},
		{
			name:   "empty map to JSON",
			obj:    map[string]string{},
			format: "json",
			validate: func(t *testing.T, output string) {
				if !strings.Contains(output, "{}") {
					t.Errorf("empty map to JSON should contain '{}', got %q", output)
				}
			},
		},
		{
			name:   "array to JSON",
			obj:    []string{"a", "b", "c"},
			format: "json",
			validate: func(t *testing.T, output string) {
				var result []string
				err := json.Unmarshal([]byte(output), &result)
				if err != nil {
					t.Errorf("Array to JSON failed: %v", err)
				}
				if len(result) != 3 {
					t.Errorf("Array length = %d, want 3", len(result))
				}
			},
		},
		{
			name:   "array to YAML",
			obj:    []string{"a", "b", "c"},
			format: "yaml",
			validate: func(t *testing.T, output string) {
				var result []string
				err := yaml.Unmarshal([]byte(output), &result)
				if err != nil {
					t.Errorf("Array to YAML failed: %v", err)
				}
				if len(result) != 3 {
					t.Errorf("Array length = %d, want 3", len(result))
				}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := FormatOutput(tt.obj, tt.format)

			if tt.wantErr {
				if err == nil {
					t.Errorf("FormatOutput() expected error, got nil")
					return
				}
				if tt.errSubstr != "" && !strings.Contains(err.Error(), tt.errSubstr) {
					t.Errorf("FormatOutput() error = %v, want substring %q", err, tt.errSubstr)
				}
				return
			}

			if err != nil {
				t.Errorf("FormatOutput() unexpected error: %v", err)
				return
			}

			if tt.validate != nil {
				tt.validate(t, got)
			}
		})
	}
}

// TestFormatOutput_JSONIndentation tests JSON output is properly indented
func TestFormatOutput_JSONIndentation(t *testing.T) {
	obj := map[string]string{
		"key1": "value1",
		"key2": "value2",
	}

	output, err := FormatOutput(obj, "json")
	if err != nil {
		t.Fatalf("FormatOutput() error: %v", err)
	}

	// Check for indentation (should have newlines and spaces)
	if !strings.Contains(output, "\n") {
		t.Error("JSON output should contain newlines for indentation")
	}
	if !strings.Contains(output, "  ") {
		t.Error("JSON output should contain spaces for indentation")
	}
}

// TestFormatOutput_ComplexNesting tests complex nested structures
func TestFormatOutput_ComplexNesting(t *testing.T) {
	obj := map[string]interface{}{
		"level1": map[string]interface{}{
			"level2": map[string]interface{}{
				"level3": "deep value",
				"array":  []int{1, 2, 3},
			},
		},
	}

	t.Run("complex to JSON", func(t *testing.T) {
		output, err := FormatOutput(obj, "json")
		if err != nil {
			t.Fatalf("FormatOutput() error: %v", err)
		}

		var result map[string]interface{}
		err = json.Unmarshal([]byte(output), &result)
		if err != nil {
			t.Errorf("Complex JSON unmarshal failed: %v", err)
		}
	})

	t.Run("complex to YAML", func(t *testing.T) {
		output, err := FormatOutput(obj, "yaml")
		if err != nil {
			t.Fatalf("FormatOutput() error: %v", err)
		}

		var result map[string]interface{}
		err = yaml.Unmarshal([]byte(output), &result)
		if err != nil {
			t.Errorf("Complex YAML unmarshal failed: %v", err)
		}
	})
}
