package k8s

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/util/yaml"
	sigyaml "sigs.k8s.io/yaml"
)

// ResourceParser handles parsing of Kubernetes resources from YAML/JSON files
type ResourceParser struct {
	// AllowedKinds restricts parsing to specific resource kinds (empty = allow all)
	AllowedKinds []string
	// StrictValidation enables strict schema validation
	StrictValidation bool
}

// NewResourceParser creates a new resource parser with default settings
func NewResourceParser() *ResourceParser {
	return &ResourceParser{
		AllowedKinds:     []string{},
		StrictValidation: false,
	}
}

// ParsedResource represents a parsed Kubernetes resource
type ParsedResource struct {
	// Object is the unstructured representation of the resource
	Object *unstructured.Unstructured
	// SourceFile is the file path this resource was parsed from (if applicable)
	SourceFile string
	// Index is the position in multi-document YAML (0-based)
	Index int
}

// ParseFile parses Kubernetes resources from a file
// Supports both YAML and JSON formats
// For YAML, supports multi-document files (separated by ---)
func (p *ResourceParser) ParseFile(filePath string) ([]*ParsedResource, error) {
	// Check file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return nil, fmt.Errorf("file not found: %s", filePath)
	}

	// Open file
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file %s: %w", filePath, err)
	}
	defer file.Close()

	// Read file content
	content, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read file %s: %w", filePath, err)
	}

	// Determine format and parse
	ext := strings.ToLower(filepath.Ext(filePath))
	if ext == ".json" {
		return p.parseJSON(content, filePath)
	}

	// Default to YAML (supports .yaml, .yml, and no extension)
	return p.parseYAML(content, filePath)
}

// ParseDirectory parses all YAML/JSON files in a directory
// If recursive is true, walks subdirectories
func (p *ResourceParser) ParseDirectory(dirPath string, recursive bool) ([]*ParsedResource, error) {
	var allResources []*ParsedResource

	// Check directory exists
	info, err := os.Stat(dirPath)
	if err != nil {
		return nil, fmt.Errorf("directory not found: %s", dirPath)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("path is not a directory: %s", dirPath)
	}

	// Walk function
	walkFn := func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if info.IsDir() {
			// Skip subdirectories if not recursive
			if !recursive && path != dirPath {
				return filepath.SkipDir
			}
			return nil
		}

		// Check if file is YAML or JSON
		ext := strings.ToLower(filepath.Ext(path))
		if ext != ".yaml" && ext != ".yml" && ext != ".json" {
			return nil
		}

		// Parse file
		resources, err := p.ParseFile(path)
		if err != nil {
			// Log warning but continue with other files
			fmt.Fprintf(os.Stderr, "Warning: failed to parse %s: %v\n", path, err)
			return nil
		}

		allResources = append(allResources, resources...)
		return nil
	}

	// Walk directory
	if err := filepath.Walk(dirPath, walkFn); err != nil {
		return nil, fmt.Errorf("failed to walk directory %s: %w", dirPath, err)
	}

	if len(allResources) == 0 {
		return nil, fmt.Errorf("no valid Kubernetes resources found in %s", dirPath)
	}

	return allResources, nil
}

// ParseString parses Kubernetes resources from a string
// Supports both YAML and JSON formats
func (p *ResourceParser) ParseString(content string) ([]*ParsedResource, error) {
	return p.ParseBytes([]byte(content))
}

// ParseBytes parses Kubernetes resources from byte array
// Supports both YAML and JSON formats
func (p *ResourceParser) ParseBytes(content []byte) ([]*ParsedResource, error) {
	// Try to determine if content is JSON
	trimmed := bytes.TrimLeft(content, " \t\r\n")
	if len(trimmed) > 0 && (trimmed[0] == '{' || trimmed[0] == '[') {
		return p.parseJSON(content, "")
	}

	// Default to YAML
	return p.parseYAML(content, "")
}

// parseYAML parses YAML content, supporting multi-document YAML
func (p *ResourceParser) parseYAML(content []byte, sourcePath string) ([]*ParsedResource, error) {
	var resources []*ParsedResource

	// Create YAML decoder that supports multi-document
	decoder := yaml.NewYAMLOrJSONDecoder(bytes.NewReader(content), 4096)

	index := 0
	for {
		// Decode next document
		obj := &unstructured.Unstructured{}
		if err := decoder.Decode(obj); err != nil {
			if err == io.EOF {
				break
			}
			return nil, fmt.Errorf("failed to decode YAML document %d: %w", index, err)
		}

		// Skip empty documents
		if obj.Object == nil || len(obj.Object) == 0 {
			continue
		}

		// Validate basic structure
		if err := p.validateResource(obj); err != nil {
			return nil, fmt.Errorf("invalid resource at document %d: %w", index, err)
		}

		// Check if kind is allowed
		if !p.isKindAllowed(obj.GetKind()) {
			continue
		}

		resources = append(resources, &ParsedResource{
			Object:     obj,
			SourceFile: sourcePath,
			Index:      index,
		})

		index++
	}

	if len(resources) == 0 {
		return nil, fmt.Errorf("no valid Kubernetes resources found")
	}

	return resources, nil
}

// parseJSON parses JSON content
// Supports both single objects and arrays
func (p *ResourceParser) parseJSON(content []byte, sourcePath string) ([]*ParsedResource, error) {
	var resources []*ParsedResource

	// Try to parse as single object first
	obj := &unstructured.Unstructured{}
	if err := json.Unmarshal(content, &obj.Object); err == nil {
		// Successfully parsed as single object
		if err := p.validateResource(obj); err != nil {
			return nil, fmt.Errorf("invalid resource: %w", err)
		}

		if p.isKindAllowed(obj.GetKind()) {
			resources = append(resources, &ParsedResource{
				Object:     obj,
				SourceFile: sourcePath,
				Index:      0,
			})
		}
		return resources, nil
	}

	// Try to parse as array
	var objArray []map[string]interface{}
	if err := json.Unmarshal(content, &objArray); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	// Process each object in array
	for i, objMap := range objArray {
		obj := &unstructured.Unstructured{Object: objMap}

		if err := p.validateResource(obj); err != nil {
			return nil, fmt.Errorf("invalid resource at index %d: %w", i, err)
		}

		if p.isKindAllowed(obj.GetKind()) {
			resources = append(resources, &ParsedResource{
				Object:     obj,
				SourceFile: sourcePath,
				Index:      i,
			})
		}
	}

	if len(resources) == 0 {
		return nil, fmt.Errorf("no valid Kubernetes resources found")
	}

	return resources, nil
}

// validateResource performs basic validation on a Kubernetes resource
func (p *ResourceParser) validateResource(obj *unstructured.Unstructured) error {
	if obj == nil || obj.Object == nil {
		return fmt.Errorf("resource is nil or empty")
	}

	// Check required fields
	apiVersion := obj.GetAPIVersion()
	if apiVersion == "" {
		return fmt.Errorf("missing required field: apiVersion")
	}

	kind := obj.GetKind()
	if kind == "" {
		return fmt.Errorf("missing required field: kind")
	}

	// Check metadata exists
	metadata, ok := obj.Object["metadata"]
	if !ok {
		return fmt.Errorf("missing required field: metadata")
	}

	// Validate metadata is a map
	metadataMap, ok := metadata.(map[string]interface{})
	if !ok {
		return fmt.Errorf("metadata must be an object")
	}

	// For strict validation, require name in metadata
	if p.StrictValidation {
		name, ok := metadataMap["name"]
		if !ok || name == "" {
			return fmt.Errorf("metadata.name is required")
		}
	}

	return nil
}

// isKindAllowed checks if a resource kind is allowed
func (p *ResourceParser) isKindAllowed(kind string) bool {
	// If no restrictions, allow all
	if len(p.AllowedKinds) == 0 {
		return true
	}

	// Check if kind is in allowed list
	for _, allowed := range p.AllowedKinds {
		if strings.EqualFold(kind, allowed) {
			return true
		}
	}

	return false
}

// SplitYAMLDocuments splits multi-document YAML into separate documents
// Returns array of individual YAML documents as strings
func SplitYAMLDocuments(content string) []string {
	var documents []string
	scanner := bufio.NewScanner(strings.NewReader(content))

	var currentDoc strings.Builder
	for scanner.Scan() {
		line := scanner.Text()

		// Check for document separator
		if strings.HasPrefix(strings.TrimSpace(line), "---") {
			// Save current document if not empty
			if currentDoc.Len() > 0 {
				documents = append(documents, strings.TrimSpace(currentDoc.String()))
				currentDoc.Reset()
			}
			continue
		}

		currentDoc.WriteString(line)
		currentDoc.WriteString("\n")
	}

	// Add last document
	if currentDoc.Len() > 0 {
		documents = append(documents, strings.TrimSpace(currentDoc.String()))
	}

	return documents
}

// ToYAML converts an unstructured object to YAML string
func ToYAML(obj *unstructured.Unstructured) (string, error) {
	if obj == nil {
		return "", fmt.Errorf("object is nil")
	}

	// Use JSON as intermediate format (K8s API uses JSON internally)
	jsonBytes, err := obj.MarshalJSON()
	if err != nil {
		return "", fmt.Errorf("failed to marshal to JSON: %w", err)
	}

	// Convert JSON to YAML using sigs.k8s.io/yaml
	yamlBytes, err := sigyaml.JSONToYAML(jsonBytes)
	if err != nil {
		return "", fmt.Errorf("failed to convert JSON to YAML: %w", err)
	}

	return string(yamlBytes), nil
}

// ToJSON converts an unstructured object to JSON string
func ToJSON(obj *unstructured.Unstructured, pretty bool) (string, error) {
	if obj == nil {
		return "", fmt.Errorf("object is nil")
	}

	jsonBytes, err := obj.MarshalJSON()
	if err != nil {
		return "", fmt.Errorf("failed to marshal to JSON: %w", err)
	}

	if pretty {
		var prettyJSON bytes.Buffer
		if err := json.Indent(&prettyJSON, jsonBytes, "", "  "); err != nil {
			return "", fmt.Errorf("failed to format JSON: %w", err)
		}
		return prettyJSON.String(), nil
	}

	return string(jsonBytes), nil
}

// ExtractResourceIdentifier extracts a human-readable identifier from a resource
// Returns "kind/name" or "kind/generateName" format
func ExtractResourceIdentifier(obj *unstructured.Unstructured) string {
	if obj == nil {
		return "<unknown>"
	}

	kind := obj.GetKind()
	name := obj.GetName()

	if name != "" {
		return fmt.Sprintf("%s/%s", kind, name)
	}

	generateName := obj.GetGenerateName()
	if generateName != "" {
		return fmt.Sprintf("%s/%s*", kind, generateName)
	}

	return fmt.Sprintf("%s/<unnamed>", kind)
}

// IsNamespaced checks if a resource is namespaced based on its metadata
func IsNamespaced(obj *unstructured.Unstructured) bool {
	if obj == nil {
		return false
	}

	namespace := obj.GetNamespace()
	return namespace != ""
}

// SetNamespace sets the namespace for a resource
func SetNamespace(obj *unstructured.Unstructured, namespace string) error {
	if obj == nil {
		return fmt.Errorf("object is nil")
	}

	obj.SetNamespace(namespace)
	return nil
}

// ValidateResourceForApply performs validation specific to apply operations
func ValidateResourceForApply(obj *unstructured.Unstructured) error {
	if obj == nil {
		return fmt.Errorf("resource is nil")
	}

	// Check required fields
	if obj.GetAPIVersion() == "" {
		return fmt.Errorf("apiVersion is required")
	}

	if obj.GetKind() == "" {
		return fmt.Errorf("kind is required")
	}

	// metadata.name is required for most resources
	// (except those with generateName)
	if obj.GetName() == "" && obj.GetGenerateName() == "" {
		return fmt.Errorf("metadata.name or metadata.generateName is required")
	}

	return nil
}
