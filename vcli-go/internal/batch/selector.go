package batch

import (
	"fmt"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
)

// Selector represents a resource selector with label and field selectors
type Selector struct {
	LabelSelector string
	FieldSelector string
	Namespace     string
}

// ParseSelector parses a selector string in the format "key=value,key2=value2"
func ParseSelector(selectorStr string) (*Selector, error) {
	if selectorStr == "" {
		return &Selector{}, nil
	}

	// Validate label selector syntax
	_, err := labels.Parse(selectorStr)
	if err != nil {
		return nil, fmt.Errorf("invalid selector syntax: %w", err)
	}

	return &Selector{
		LabelSelector: selectorStr,
	}, nil
}

// ToListOptions converts selector to Kubernetes ListOptions
func (s *Selector) ToListOptions() metav1.ListOptions {
	opts := metav1.ListOptions{}

	if s.LabelSelector != "" {
		opts.LabelSelector = s.LabelSelector
	}

	if s.FieldSelector != "" {
		opts.FieldSelector = s.FieldSelector
	}

	return opts
}

// String returns a string representation of the selector
func (s *Selector) String() string {
	parts := []string{}

	if s.LabelSelector != "" {
		parts = append(parts, fmt.Sprintf("labels=%s", s.LabelSelector))
	}

	if s.FieldSelector != "" {
		parts = append(parts, fmt.Sprintf("fields=%s", s.FieldSelector))
	}

	if s.Namespace != "" {
		parts = append(parts, fmt.Sprintf("namespace=%s", s.Namespace))
	}

	if len(parts) == 0 {
		return "all resources"
	}

	return strings.Join(parts, ", ")
}

// MatchesLabels checks if a label set matches the selector
func (s *Selector) MatchesLabels(resourceLabels map[string]string) (bool, error) {
	if s.LabelSelector == "" {
		return true, nil
	}

	selector, err := labels.Parse(s.LabelSelector)
	if err != nil {
		return false, err
	}

	return selector.Matches(labels.Set(resourceLabels)), nil
}
