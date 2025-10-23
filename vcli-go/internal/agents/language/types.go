package language

// Language represents a programming language
type Language string

const (
	LanguageGo     Language = "go"
	LanguagePython Language = "python"
	LanguageUnknown Language = "unknown"
)

// String returns the string representation of the language
func (l Language) String() string {
	return string(l)
}

// IsValid checks if the language is valid
func (l Language) IsValid() bool {
	return l == LanguageGo || l == LanguagePython
}

// DetectionResult contains the result of language detection
type DetectionResult struct {
	// Primary language detected
	Primary Language

	// All languages detected (for multi-language projects)
	All []Language

	// Confidence score (0.0 - 1.0)
	Confidence float64

	// Evidence found for detection
	Evidence map[Language][]string
}

// IsMultiLanguage checks if multiple languages were detected
func (r *DetectionResult) IsMultiLanguage() bool {
	return len(r.All) > 1
}

// HasLanguage checks if a specific language was detected
func (r *DetectionResult) HasLanguage(lang Language) bool {
	for _, l := range r.All {
		if l == lang {
			return true
		}
	}
	return false
}
