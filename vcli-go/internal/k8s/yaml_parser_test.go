package k8s

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Test fixtures
const (
	validPodYAML = `apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:latest`

	validDeploymentYAML = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx:latest`

	multiDocumentYAML = `apiVersion: v1
kind: Pod
metadata:
  name: pod1
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:latest
---
apiVersion: v1
kind: Service
metadata:
  name: service1
  namespace: default
spec:
  selector:
    app: test
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deployment1
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx:latest`

	validPodJSON = `{
  "apiVersion": "v1",
  "kind": "Pod",
  "metadata": {
    "name": "test-pod-json",
    "namespace": "default"
  },
  "spec": {
    "containers": [
      {
        "name": "nginx",
        "image": "nginx:latest"
      }
    ]
  }
}`

	jsonArray = `[
  {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
      "name": "pod1",
      "namespace": "default"
    },
    "spec": {
      "containers": [
        {
          "name": "nginx",
          "image": "nginx:latest"
        }
      ]
    }
  },
  {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {
      "name": "service1",
      "namespace": "default"
    },
    "spec": {
      "selector": {
        "app": "test"
      },
      "ports": [
        {
          "port": 80
        }
      ]
    }
  }
]`

	missingAPIVersionYAML = `kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest`

	missingKindYAML = `apiVersion: v1
metadata:
  name: test-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest`

	missingMetadataYAML = `apiVersion: v1
kind: Pod
spec:
  containers:
  - name: nginx
    image: nginx:latest`

	emptyYAML = ``

	invalidYAML = `this is not valid YAML: [[[`
)

// TestNewResourceParser tests parser creation
func TestNewResourceParser(t *testing.T) {
	parser := NewResourceParser()
	assert.NotNil(t, parser)
	assert.Empty(t, parser.AllowedKinds)
	assert.False(t, parser.StrictValidation)
}

// TestParseString_ValidPodYAML tests parsing valid Pod YAML
func TestParseString_ValidPodYAML(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validPodYAML)

	require.NoError(t, err)
	require.Len(t, resources, 1)

	resource := resources[0]
	assert.Equal(t, "v1", resource.Object.GetAPIVersion())
	assert.Equal(t, "Pod", resource.Object.GetKind())
	assert.Equal(t, "test-pod", resource.Object.GetName())
	assert.Equal(t, "default", resource.Object.GetNamespace())
	assert.Equal(t, 0, resource.Index)
}

// TestParseString_ValidDeploymentYAML tests parsing valid Deployment YAML
func TestParseString_ValidDeploymentYAML(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validDeploymentYAML)

	require.NoError(t, err)
	require.Len(t, resources, 1)

	resource := resources[0]
	assert.Equal(t, "apps/v1", resource.Object.GetAPIVersion())
	assert.Equal(t, "Deployment", resource.Object.GetKind())
	assert.Equal(t, "test-deployment", resource.Object.GetName())
}

// TestParseString_MultiDocumentYAML tests parsing multi-document YAML
func TestParseString_MultiDocumentYAML(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(multiDocumentYAML)

	require.NoError(t, err)
	require.Len(t, resources, 3)

	// Verify first document (Pod)
	assert.Equal(t, "Pod", resources[0].Object.GetKind())
	assert.Equal(t, "pod1", resources[0].Object.GetName())
	assert.Equal(t, 0, resources[0].Index)

	// Verify second document (Service)
	assert.Equal(t, "Service", resources[1].Object.GetKind())
	assert.Equal(t, "service1", resources[1].Object.GetName())
	assert.Equal(t, 1, resources[1].Index)

	// Verify third document (Deployment)
	assert.Equal(t, "Deployment", resources[2].Object.GetKind())
	assert.Equal(t, "deployment1", resources[2].Object.GetName())
	assert.Equal(t, 2, resources[2].Index)
}

// TestParseString_ValidJSON tests parsing valid JSON
func TestParseString_ValidJSON(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validPodJSON)

	require.NoError(t, err)
	require.Len(t, resources, 1)

	resource := resources[0]
	assert.Equal(t, "v1", resource.Object.GetAPIVersion())
	assert.Equal(t, "Pod", resource.Object.GetKind())
	assert.Equal(t, "test-pod-json", resource.Object.GetName())
}

// TestParseString_JSONArray tests parsing JSON array
func TestParseString_JSONArray(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseBytes([]byte(jsonArray))

	require.NoError(t, err)
	require.Len(t, resources, 2)

	assert.Equal(t, "Pod", resources[0].Object.GetKind())
	assert.Equal(t, "Service", resources[1].Object.GetKind())
}

// TestParseString_MissingAPIVersion tests error for missing apiVersion
func TestParseString_MissingAPIVersion(t *testing.T) {
	parser := NewResourceParser()
	_, err := parser.ParseString(missingAPIVersionYAML)

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "apiVersion")
}

// TestParseString_MissingKind tests error for missing kind
func TestParseString_MissingKind(t *testing.T) {
	parser := NewResourceParser()
	_, err := parser.ParseString(missingKindYAML)

	assert.Error(t, err)
	// Error can come from K8s decoder or our validation
	assert.True(t, err != nil, "should error on missing kind")
}

// TestParseString_MissingMetadata tests error for missing metadata
func TestParseString_MissingMetadata(t *testing.T) {
	parser := NewResourceParser()
	_, err := parser.ParseString(missingMetadataYAML)

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "metadata")
}

// TestParseString_EmptyYAML tests error for empty YAML
func TestParseString_EmptyYAML(t *testing.T) {
	parser := NewResourceParser()
	_, err := parser.ParseString(emptyYAML)

	assert.Error(t, err)
}

// TestParseString_InvalidYAML tests error for invalid YAML
func TestParseString_InvalidYAML(t *testing.T) {
	parser := NewResourceParser()
	_, err := parser.ParseString(invalidYAML)

	assert.Error(t, err)
}

// TestParseFile_ValidYAML tests parsing from file
func TestParseFile_ValidYAML(t *testing.T) {
	// Create temp file
	tmpFile, err := os.CreateTemp("", "test-*.yaml")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	// Write content
	_, err = tmpFile.WriteString(validPodYAML)
	require.NoError(t, err)
	tmpFile.Close()

	// Parse file
	parser := NewResourceParser()
	resources, err := parser.ParseFile(tmpFile.Name())

	require.NoError(t, err)
	require.Len(t, resources, 1)
	assert.Equal(t, tmpFile.Name(), resources[0].SourceFile)
	assert.Equal(t, "Pod", resources[0].Object.GetKind())
}

// TestParseFile_ValidJSON tests parsing JSON file
func TestParseFile_ValidJSON(t *testing.T) {
	// Create temp file
	tmpFile, err := os.CreateTemp("", "test-*.json")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	// Write content
	_, err = tmpFile.WriteString(validPodJSON)
	require.NoError(t, err)
	tmpFile.Close()

	// Parse file
	parser := NewResourceParser()
	resources, err := parser.ParseFile(tmpFile.Name())

	require.NoError(t, err)
	require.Len(t, resources, 1)
	assert.Equal(t, "Pod", resources[0].Object.GetKind())
}

// TestParseFile_NonExistent tests error for non-existent file
func TestParseFile_NonExistent(t *testing.T) {
	parser := NewResourceParser()
	_, err := parser.ParseFile("/non/existent/file.yaml")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

// TestParseDirectory tests parsing directory
func TestParseDirectory(t *testing.T) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "test-dir-*")
	require.NoError(t, err)
	defer os.RemoveAll(tmpDir)

	// Create test files
	file1 := filepath.Join(tmpDir, "pod.yaml")
	err = os.WriteFile(file1, []byte(validPodYAML), 0644)
	require.NoError(t, err)

	file2 := filepath.Join(tmpDir, "deployment.yaml")
	err = os.WriteFile(file2, []byte(validDeploymentYAML), 0644)
	require.NoError(t, err)

	// Parse directory
	parser := NewResourceParser()
	resources, err := parser.ParseDirectory(tmpDir, false)

	require.NoError(t, err)
	assert.Len(t, resources, 2)

	// Verify both resources parsed
	kinds := make(map[string]bool)
	for _, r := range resources {
		kinds[r.Object.GetKind()] = true
	}
	assert.True(t, kinds["Pod"])
	assert.True(t, kinds["Deployment"])
}

// TestParseDirectory_Recursive tests recursive directory parsing
func TestParseDirectory_Recursive(t *testing.T) {
	// Create temp directory structure
	tmpDir, err := os.MkdirTemp("", "test-dir-*")
	require.NoError(t, err)
	defer os.RemoveAll(tmpDir)

	subDir := filepath.Join(tmpDir, "subdir")
	err = os.Mkdir(subDir, 0755)
	require.NoError(t, err)

	// Create files in both directories
	file1 := filepath.Join(tmpDir, "pod.yaml")
	err = os.WriteFile(file1, []byte(validPodYAML), 0644)
	require.NoError(t, err)

	file2 := filepath.Join(subDir, "deployment.yaml")
	err = os.WriteFile(file2, []byte(validDeploymentYAML), 0644)
	require.NoError(t, err)

	// Parse recursively
	parser := NewResourceParser()
	resources, err := parser.ParseDirectory(tmpDir, true)

	require.NoError(t, err)
	assert.Len(t, resources, 2)
}

// TestParseDirectory_NonRecursive tests non-recursive parsing
func TestParseDirectory_NonRecursive(t *testing.T) {
	// Create temp directory structure
	tmpDir, err := os.MkdirTemp("", "test-dir-*")
	require.NoError(t, err)
	defer os.RemoveAll(tmpDir)

	subDir := filepath.Join(tmpDir, "subdir")
	err = os.Mkdir(subDir, 0755)
	require.NoError(t, err)

	// Create files in both directories
	file1 := filepath.Join(tmpDir, "pod.yaml")
	err = os.WriteFile(file1, []byte(validPodYAML), 0644)
	require.NoError(t, err)

	file2 := filepath.Join(subDir, "deployment.yaml")
	err = os.WriteFile(file2, []byte(validDeploymentYAML), 0644)
	require.NoError(t, err)

	// Parse non-recursively
	parser := NewResourceParser()
	resources, err := parser.ParseDirectory(tmpDir, false)

	require.NoError(t, err)
	// Should only find file in root directory
	assert.Len(t, resources, 1)
	assert.Equal(t, "Pod", resources[0].Object.GetKind())
}

// TestAllowedKinds tests kind filtering
func TestAllowedKinds(t *testing.T) {
	parser := NewResourceParser()
	parser.AllowedKinds = []string{"Pod"}

	resources, err := parser.ParseString(multiDocumentYAML)

	require.NoError(t, err)
	// Should only return Pod (filter out Service and Deployment)
	assert.Len(t, resources, 1)
	assert.Equal(t, "Pod", resources[0].Object.GetKind())
}

// TestStrictValidation tests strict validation mode
func TestStrictValidation(t *testing.T) {
	yamlWithoutName := `apiVersion: v1
kind: Pod
metadata:
  generateName: test-pod-
spec:
  containers:
  - name: nginx
    image: nginx:latest`

	parser := NewResourceParser()
	parser.StrictValidation = true

	_, err := parser.ParseString(yamlWithoutName)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "name is required")
}

// TestSplitYAMLDocuments tests YAML document splitting
func TestSplitYAMLDocuments(t *testing.T) {
	docs := SplitYAMLDocuments(multiDocumentYAML)

	assert.Len(t, docs, 3)
	assert.Contains(t, docs[0], "kind: Pod")
	assert.Contains(t, docs[1], "kind: Service")
	assert.Contains(t, docs[2], "kind: Deployment")
}

// TestToYAML tests converting object to YAML
func TestToYAML(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validPodYAML)
	require.NoError(t, err)

	yamlStr, err := ToYAML(resources[0].Object)
	require.NoError(t, err)

	assert.Contains(t, yamlStr, "kind: Pod")
	assert.Contains(t, yamlStr, "name: test-pod")
}

// TestToJSON tests converting object to JSON
func TestToJSON(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validPodYAML)
	require.NoError(t, err)

	// Test compact JSON
	jsonStr, err := ToJSON(resources[0].Object, false)
	require.NoError(t, err)
	assert.Contains(t, jsonStr, `"kind":"Pod"`)

	// Test pretty JSON
	prettyJSON, err := ToJSON(resources[0].Object, true)
	require.NoError(t, err)
	assert.Contains(t, prettyJSON, `"kind": "Pod"`)
	assert.Contains(t, prettyJSON, "\n")
}

// TestToJSON_NilObject tests error for nil object
func TestToJSON_NilObject(t *testing.T) {
	_, err := ToJSON(nil, false)
	assert.Error(t, err)
}

// TestToYAML_NilObject tests error for nil object
func TestToYAML_NilObject(t *testing.T) {
	_, err := ToYAML(nil)
	assert.Error(t, err)
}

// TestExtractResourceIdentifier tests resource identifier extraction
func TestExtractResourceIdentifier(t *testing.T) {
	tests := []struct {
		name     string
		yaml     string
		expected string
	}{
		{
			name: "with name",
			yaml: validPodYAML,
			expected: "Pod/test-pod",
		},
		{
			name: "with generateName",
			yaml: `apiVersion: v1
kind: Pod
metadata:
  generateName: test-pod-
spec:
  containers:
  - name: nginx
    image: nginx:latest`,
			expected: "Pod/test-pod-*",
		},
	}

	parser := NewResourceParser()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			resources, err := parser.ParseString(tt.yaml)
			require.NoError(t, err)

			identifier := ExtractResourceIdentifier(resources[0].Object)
			assert.Equal(t, tt.expected, identifier)
		})
	}
}

// TestExtractResourceIdentifier_NilObject tests nil object handling
func TestExtractResourceIdentifier_NilObject(t *testing.T) {
	identifier := ExtractResourceIdentifier(nil)
	assert.Equal(t, "<unknown>", identifier)
}

// TestIsNamespaced tests namespace detection
func TestIsNamespaced(t *testing.T) {
	parser := NewResourceParser()

	// Test namespaced resource
	resources, err := parser.ParseString(validPodYAML)
	require.NoError(t, err)
	assert.True(t, IsNamespaced(resources[0].Object))

	// Test cluster-scoped resource (node)
	nodeYAML := `apiVersion: v1
kind: Node
metadata:
  name: worker-1`
	resources, err = parser.ParseString(nodeYAML)
	require.NoError(t, err)
	assert.False(t, IsNamespaced(resources[0].Object))
}

// TestSetNamespace tests setting namespace
func TestSetNamespace(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validPodYAML)
	require.NoError(t, err)

	obj := resources[0].Object
	err = SetNamespace(obj, "new-namespace")
	require.NoError(t, err)

	assert.Equal(t, "new-namespace", obj.GetNamespace())
}

// TestSetNamespace_NilObject tests error for nil object
func TestSetNamespace_NilObject(t *testing.T) {
	err := SetNamespace(nil, "test")
	assert.Error(t, err)
}

// TestValidateResourceForApply tests apply-specific validation
func TestValidateResourceForApply(t *testing.T) {
	parser := NewResourceParser()
	resources, err := parser.ParseString(validPodYAML)
	require.NoError(t, err)

	err = ValidateResourceForApply(resources[0].Object)
	assert.NoError(t, err)
}

// TestValidateResourceForApply_MissingName tests validation without name
func TestValidateResourceForApply_MissingName(t *testing.T) {
	yamlWithoutName := `apiVersion: v1
kind: Pod
metadata: {}
spec:
  containers:
  - name: nginx
    image: nginx:latest`

	parser := NewResourceParser()
	resources, err := parser.ParseString(yamlWithoutName)
	require.NoError(t, err)

	err = ValidateResourceForApply(resources[0].Object)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "name")
}

// TestValidateResourceForApply_NilObject tests nil object
func TestValidateResourceForApply_NilObject(t *testing.T) {
	err := ValidateResourceForApply(nil)
	assert.Error(t, err)
}
