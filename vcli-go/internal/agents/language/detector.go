package language

import (
	"os"
	"path/filepath"
	"strings"
)

// Detector performs automatic language detection based on project files
type Detector struct {
	// Indicators for each language (filename patterns)
	indicators map[Language][]string
}

// NewDetector creates a new language detector
func NewDetector() *Detector {
	return &Detector{
		indicators: map[Language][]string{
			LanguageGo: {
				"go.mod",
				"go.sum",
				"*.go",
			},
			LanguagePython: {
				"requirements.txt",
				"setup.py",
				"pyproject.toml",
				"Pipfile",
				"poetry.lock",
				"*.py",
			},
		},
	}
}

// Detect analyzes the target paths and detects languages
func (d *Detector) Detect(targets []string) (*DetectionResult, error) {
	evidence := make(map[Language][]string)

	// Scan all targets for language indicators
	for _, target := range targets {
		if err := d.scanPath(target, evidence); err != nil {
			return nil, err
		}
	}

	// Build detection result
	result := &DetectionResult{
		Primary:    LanguageUnknown,
		All:        make([]Language, 0),
		Confidence: 0.0,
		Evidence:   evidence,
	}

	// Determine detected languages
	langScores := make(map[Language]int)
	for lang, files := range evidence {
		if len(files) > 0 {
			result.All = append(result.All, lang)
			langScores[lang] = len(files)
		}
	}

	// Set primary language (most evidence)
	maxScore := 0
	for lang, score := range langScores {
		if score > maxScore {
			maxScore = score
			result.Primary = lang
		}
	}

	// Calculate confidence
	if len(result.All) > 0 {
		totalFiles := 0
		for _, score := range langScores {
			totalFiles += score
		}
		if totalFiles > 0 {
			result.Confidence = float64(langScores[result.Primary]) / float64(totalFiles)
		}
	}

	return result, nil
}

// scanPath recursively scans a path for language indicators
func (d *Detector) scanPath(path string, evidence map[Language][]string) error {
	info, err := os.Stat(path)
	if err != nil {
		return err
	}

	// Initialize evidence maps
	for lang := range d.indicators {
		if evidence[lang] == nil {
			evidence[lang] = make([]string, 0)
		}
	}

	if info.IsDir() {
		// Scan directory
		return filepath.Walk(path, func(filePath string, fileInfo os.FileInfo, err error) error {
			if err != nil {
				return nil // Skip errors, continue walking
			}

			// Skip hidden directories and common ignore patterns
			if fileInfo.IsDir() {
				name := fileInfo.Name()
				if strings.HasPrefix(name, ".") || name == "node_modules" ||
				   name == "__pycache__" || name == "venv" || name == ".venv" ||
				   name == "vendor" {
					return filepath.SkipDir
				}
				return nil
			}

			// Check file against indicators
			d.checkFile(filePath, evidence)
			return nil
		})
	}

	// Single file
	d.checkFile(path, evidence)
	return nil
}

// checkFile checks if a file matches any language indicators
func (d *Detector) checkFile(filePath string, evidence map[Language][]string) {
	fileName := filepath.Base(filePath)

	for lang, patterns := range d.indicators {
		for _, pattern := range patterns {
			if d.matchPattern(fileName, pattern) {
				evidence[lang] = append(evidence[lang], filePath)
				break
			}
		}
	}
}

// matchPattern checks if a filename matches a pattern
func (d *Detector) matchPattern(fileName, pattern string) bool {
	// Exact match
	if fileName == pattern {
		return true
	}

	// Wildcard match (*.ext)
	if strings.HasPrefix(pattern, "*.") {
		ext := pattern[1:] // Remove *
		return strings.HasSuffix(fileName, ext)
	}

	return false
}

// DetectSingle is a convenience function to detect language for a single path
func DetectSingle(path string) (*DetectionResult, error) {
	detector := NewDetector()
	return detector.Detect([]string{path})
}
