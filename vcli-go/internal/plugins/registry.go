package plugins

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// PluginRegistry manages plugin discovery and distribution
type PluginRegistry struct {
	// baseURL is the registry base URL
	baseURL string

	// httpClient is the HTTP client
	httpClient *http.Client

	// cacheDir is the local cache directory
	cacheDir string

	// index is the cached plugin index
	index map[string]*RegistryEntry

	// lastIndexUpdate is when index was last updated
	lastIndexUpdate time.Time

	// indexTTL is how long to cache index
	indexTTL time.Duration
}

// NewPluginRegistry creates a new plugin registry
func NewPluginRegistry(baseURL, cacheDir string) *PluginRegistry {
	return &PluginRegistry{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		cacheDir: cacheDir,
		index:    make(map[string]*RegistryEntry),
		indexTTL: 1 * time.Hour,
	}
}

// Search searches for plugins matching query
func (pr *PluginRegistry) Search(ctx context.Context, query string) ([]RegistryEntry, error) {
	// Update index if stale
	if err := pr.updateIndexIfStale(ctx); err != nil {
		return nil, fmt.Errorf("failed to update index: %w", err)
	}

	// Search in index
	results := make([]RegistryEntry, 0)
	query = strings.ToLower(query)

	for _, entry := range pr.index {
		// Match against name, description, tags
		if strings.Contains(strings.ToLower(entry.Name), query) ||
			strings.Contains(strings.ToLower(entry.Description), query) ||
			pr.matchTags(entry.Tags, query) {
			results = append(results, *entry)
		}
	}

	return results, nil
}

// Get gets plugin entry by name
func (pr *PluginRegistry) Get(ctx context.Context, name string) (*RegistryEntry, error) {
	// Update index if stale
	if err := pr.updateIndexIfStale(ctx); err != nil {
		return nil, fmt.Errorf("failed to update index: %w", err)
	}

	entry, exists := pr.index[name]
	if !exists {
		return nil, fmt.Errorf("plugin not found in registry: %s", name)
	}

	return entry, nil
}

// List lists all plugins in registry
func (pr *PluginRegistry) List(ctx context.Context) ([]RegistryEntry, error) {
	// Update index if stale
	if err := pr.updateIndexIfStale(ctx); err != nil {
		return nil, fmt.Errorf("failed to update index: %w", err)
	}

	entries := make([]RegistryEntry, 0, len(pr.index))
	for _, entry := range pr.index {
		entries = append(entries, *entry)
	}

	return entries, nil
}

// Download downloads plugin from registry
func (pr *PluginRegistry) Download(ctx context.Context, name, version string) (string, error) {
	// Get plugin entry
	entry, err := pr.Get(ctx, name)
	if err != nil {
		return "", err
	}

	// Validate version
	if !pr.versionExists(entry.Versions, version) {
		return "", fmt.Errorf("version %s not found for plugin %s", version, name)
	}

	// Build download URL
	downloadURL := fmt.Sprintf("%s/plugins/%s/%s/%s.so",
		pr.baseURL, name, version, name)

	// Create cache directory
	pluginCacheDir := filepath.Join(pr.cacheDir, "plugins", name, version)
	if err := os.MkdirAll(pluginCacheDir, 0755); err != nil {
		return "", fmt.Errorf("failed to create cache directory: %w", err)
	}

	// Download path
	downloadPath := filepath.Join(pluginCacheDir, name+".so")

	// Check if already downloaded
	if _, err := os.Stat(downloadPath); err == nil {
		return downloadPath, nil
	}

	// Download plugin
	req, err := http.NewRequestWithContext(ctx, "GET", downloadURL, nil)
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := pr.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to download plugin: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("download failed with status: %s", resp.Status)
	}

	// Create file
	file, err := os.Create(downloadPath)
	if err != nil {
		return "", fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Copy content
	if _, err := io.Copy(file, resp.Body); err != nil {
		os.Remove(downloadPath) // Clean up on error
		return "", fmt.Errorf("failed to write plugin: %w", err)
	}

	// Make executable
	if err := os.Chmod(downloadPath, 0755); err != nil {
		return "", fmt.Errorf("failed to set permissions: %w", err)
	}

	return downloadPath, nil
}

// Publish publishes plugin to registry
func (pr *PluginRegistry) Publish(ctx context.Context, path string, metadata Metadata) error {
	// Read plugin file
	file, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("failed to open plugin file: %w", err)
	}
	defer file.Close()

	// Build upload URL
	uploadURL := fmt.Sprintf("%s/plugins/%s/%s/upload",
		pr.baseURL, metadata.Name, metadata.Version)

	// Create multipart request
	req, err := http.NewRequestWithContext(ctx, "POST", uploadURL, file)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/octet-stream")

	// Add metadata as headers
	metadataJSON, _ := json.Marshal(metadata)
	req.Header.Set("X-Plugin-Metadata", string(metadataJSON))

	// Send request
	resp, err := pr.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to upload plugin: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return fmt.Errorf("upload failed with status: %s", resp.Status)
	}

	return nil
}

// updateIndexIfStale updates the plugin index if it's stale
func (pr *PluginRegistry) updateIndexIfStale(ctx context.Context) error {
	if time.Since(pr.lastIndexUpdate) < pr.indexTTL {
		return nil
	}

	return pr.updateIndex(ctx)
}

// updateIndex fetches the latest plugin index from registry
func (pr *PluginRegistry) updateIndex(ctx context.Context) error {
	indexURL := fmt.Sprintf("%s/plugins/index.json", pr.baseURL)

	req, err := http.NewRequestWithContext(ctx, "GET", indexURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := pr.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to fetch index: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("fetch failed with status: %s", resp.Status)
	}

	// Parse index
	var entries []RegistryEntry
	if err := json.NewDecoder(resp.Body).Decode(&entries); err != nil {
		return fmt.Errorf("failed to parse index: %w", err)
	}

	// Update index
	pr.index = make(map[string]*RegistryEntry)
	for i := range entries {
		pr.index[entries[i].Name] = &entries[i]
	}

	pr.lastIndexUpdate = time.Now()

	return nil
}

// matchTags checks if query matches any tag
func (pr *PluginRegistry) matchTags(tags []string, query string) bool {
	for _, tag := range tags {
		if strings.Contains(strings.ToLower(tag), query) {
			return true
		}
	}
	return false
}

// versionExists checks if version exists in version list
func (pr *PluginRegistry) versionExists(versions []string, version string) bool {
	for _, v := range versions {
		if v == version {
			return true
		}
	}
	return false
}

// LocalRegistry is a simple local file-based registry
type LocalRegistry struct {
	pluginsDir string
}

// NewLocalRegistry creates a new local registry
func NewLocalRegistry(pluginsDir string) *LocalRegistry {
	return &LocalRegistry{
		pluginsDir: pluginsDir,
	}
}

// Search searches local plugins
func (lr *LocalRegistry) Search(ctx context.Context, query string) ([]RegistryEntry, error) {
	entries, err := lr.List(ctx)
	if err != nil {
		return nil, err
	}

	query = strings.ToLower(query)
	results := make([]RegistryEntry, 0)

	for _, entry := range entries {
		if strings.Contains(strings.ToLower(entry.Name), query) ||
			strings.Contains(strings.ToLower(entry.Description), query) {
			results = append(results, entry)
		}
	}

	return results, nil
}

// Get gets local plugin entry by name
func (lr *LocalRegistry) Get(ctx context.Context, name string) (*RegistryEntry, error) {
	pluginPath := filepath.Join(lr.pluginsDir, name+".so")

	if _, err := os.Stat(pluginPath); err != nil {
		return nil, fmt.Errorf("plugin not found: %s", name)
	}

	return &RegistryEntry{
		Name:          name,
		LatestVersion: "local",
		Versions:      []string{"local"},
		Description:   "Local plugin",
		SourceURL:     pluginPath,
	}, nil
}

// List lists all local plugins
func (lr *LocalRegistry) List(ctx context.Context) ([]RegistryEntry, error) {
	entries, err := os.ReadDir(lr.pluginsDir)
	if err != nil {
		if os.IsNotExist(err) {
			return []RegistryEntry{}, nil
		}
		return nil, fmt.Errorf("failed to read plugins directory: %w", err)
	}

	results := make([]RegistryEntry, 0)

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".so") {
			continue
		}

		name := strings.TrimSuffix(entry.Name(), ".so")
		results = append(results, RegistryEntry{
			Name:          name,
			LatestVersion: "local",
			Versions:      []string{"local"},
			Description:   "Local plugin",
			SourceURL:     filepath.Join(lr.pluginsDir, entry.Name()),
		})
	}

	return results, nil
}

// Download returns local plugin path
func (lr *LocalRegistry) Download(ctx context.Context, name, version string) (string, error) {
	return filepath.Join(lr.pluginsDir, name+".so"), nil
}

// Publish copies plugin to local directory
func (lr *LocalRegistry) Publish(ctx context.Context, path string, metadata Metadata) error {
	// Ensure plugins directory exists
	if err := os.MkdirAll(lr.pluginsDir, 0755); err != nil {
		return fmt.Errorf("failed to create plugins directory: %w", err)
	}

	// Copy plugin to plugins directory
	destPath := filepath.Join(lr.pluginsDir, metadata.Name+".so")

	src, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("failed to open source: %w", err)
	}
	defer src.Close()

	dest, err := os.Create(destPath)
	if err != nil {
		return fmt.Errorf("failed to create destination: %w", err)
	}
	defer dest.Close()

	if _, err := io.Copy(dest, src); err != nil {
		return fmt.Errorf("failed to copy plugin: %w", err)
	}

	// Make executable
	if err := os.Chmod(destPath, 0755); err != nil {
		return fmt.Errorf("failed to set permissions: %w", err)
	}

	return nil
}
