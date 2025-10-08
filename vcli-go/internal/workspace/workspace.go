package workspace

import (
	tea "github.com/charmbracelet/bubbletea"
)

// Workspace represents a TUI workspace
type Workspace interface {
	// ID returns the unique identifier for this workspace
	ID() string

	// Name returns the display name
	Name() string

	// Icon returns the workspace icon/emoji
	Icon() string

	// Description returns a short description
	Description() string

	// Init initializes the workspace
	Init() tea.Cmd

	// Update handles messages
	Update(tea.Msg) (Workspace, tea.Cmd)

	// View renders the workspace
	View(width, height int) string

	// IsActive returns whether this workspace is currently active
	IsActive() bool

	// SetActive sets the active state
	SetActive(bool)
}

// BaseWorkspace provides common workspace functionality
type BaseWorkspace struct {
	id          string
	name        string
	icon        string
	description string
	active      bool
}

// NewBaseWorkspace creates a new base workspace
func NewBaseWorkspace(id, name, icon, description string) BaseWorkspace {
	return BaseWorkspace{
		id:          id,
		name:        name,
		icon:        icon,
		description: description,
		active:      false,
	}
}

// ID returns the workspace ID
func (w *BaseWorkspace) ID() string {
	return w.id
}

// Name returns the workspace name
func (w *BaseWorkspace) Name() string {
	return w.name
}

// Icon returns the workspace icon
func (w *BaseWorkspace) Icon() string {
	return w.icon
}

// Description returns the workspace description
func (w *BaseWorkspace) Description() string {
	return w.description
}

// IsActive returns whether workspace is active
func (w *BaseWorkspace) IsActive() bool {
	return w.active
}

// SetActive sets the active state
func (w *BaseWorkspace) SetActive(active bool) {
	w.active = active
}
