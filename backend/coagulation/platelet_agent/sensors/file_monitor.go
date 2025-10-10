package sensors

import (
	"context"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// FileMonitor monitors filesystem for suspicious activity.
//
// Biological Analogy: Detects "damage" to critical structures (like
// detecting endothelial cell lysis or membrane disruption).
type FileMonitor struct {
	logger       *logger.Logger
	metrics      *metrics.Collector
	anomalyScore float64
	mu           sync.RWMutex
	ctx          context.Context
	
	// File integrity baseline
	criticalFiles map[string]*FileProfile
	watchPaths    []string
}

// FileProfile represents file integrity baseline.
type FileProfile struct {
	Path      string
	Hash      string
	Size      int64
	Mode      os.FileMode
	ModTime   time.Time
	FirstSeen time.Time
}

// NewFileMonitor creates a new file monitoring sensor.
func NewFileMonitor(log *logger.Logger, m *metrics.Collector) *FileMonitor {
	return &FileMonitor{
		logger:        log,
		metrics:       m,
		anomalyScore:  0.0,
		criticalFiles: make(map[string]*FileProfile),
		watchPaths:    getCriticalPaths(),
	}
}

// getCriticalPaths returns paths to monitor.
//
// Phase 1: Common critical paths (Linux-focused).
// Future: Configurable, OS-aware path detection.
func getCriticalPaths() []string {
	return []string{
		"/etc/passwd",
		"/etc/shadow",
		"/etc/hosts",
		"/etc/ssh/sshd_config",
		"/root/.ssh",
		"/home/*/.ssh",
		// Add more critical paths
	}
}

// Start begins file monitoring.
func (fm *FileMonitor) Start(ctx context.Context) error {
	fm.ctx = ctx
	fm.logger.Debug("file_monitor_started")
	
	// Build initial integrity baseline
	fm.buildBaseline()
	
	// Start monitoring loop
	go fm.monitorLoop()
	
	return nil
}

// buildBaseline establishes file integrity baseline.
func (fm *FileMonitor) buildBaseline() {
	for _, watchPath := range fm.watchPaths {
		// Handle glob patterns
		matches, err := filepath.Glob(watchPath)
		if err != nil {
			fm.logger.Warn("glob error", logger.String("path", watchPath), logger.Error(err))
			continue
		}
		
		for _, path := range matches {
			if err := fm.addFileToBaseline(path); err != nil {
				fm.logger.Debug("skipped_file",
					logger.String("path", path),
					logger.Error(err),
				)
			}
		}
	}
	
	fm.logger.Debug("file_baseline_established",
		logger.Int("critical_files", len(fm.criticalFiles)),
	)
}

// addFileToBaseline adds file to integrity baseline.
func (fm *FileMonitor) addFileToBaseline(path string) error {
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	
	// Skip directories for Phase 1
	if info.IsDir() {
		return fmt.Errorf("directory skipped")
	}
	
	// Calculate hash
	hash, err := fm.calculateHash(path)
	if err != nil {
		return err
	}
	
	fm.mu.Lock()
	fm.criticalFiles[path] = &FileProfile{
		Path:      path,
		Hash:      hash,
		Size:      info.Size(),
		Mode:      info.Mode(),
		ModTime:   info.ModTime(),
		FirstSeen: time.Now(),
	}
	fm.mu.Unlock()
	
	return nil
}

// calculateHash computes SHA256 hash of file.
func (fm *FileMonitor) calculateHash(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer file.Close()
	
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", err
	}
	
	return fmt.Sprintf("%x", hash.Sum(nil)), nil
}

// monitorLoop continuously checks file integrity.
func (fm *FileMonitor) monitorLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-fm.ctx.Done():
			return
		case <-ticker.C:
			fm.checkIntegrity()
		}
	}
}

// checkIntegrity verifies file integrity against baseline.
func (fm *FileMonitor) checkIntegrity() {
	fm.mu.RLock()
	filesToCheck := make(map[string]*FileProfile)
	for k, v := range fm.criticalFiles {
		filesToCheck[k] = v
	}
	fm.mu.RUnlock()
	
	anomalies := 0
	totalFiles := len(filesToCheck)
	
	for path, baseline := range filesToCheck {
		if fm.isFileModified(path, baseline) {
			anomalies++
			
			fm.logger.Warn("file_integrity_violation",
				logger.String("path", path),
			)
		}
	}
	
	// Update anomaly score
	if totalFiles > 0 {
		score := float64(anomalies) / float64(totalFiles)
		fm.mu.Lock()
		fm.anomalyScore = score
		fm.mu.Unlock()
	}
}

// isFileModified checks if file has been modified.
func (fm *FileMonitor) isFileModified(path string, baseline *FileProfile) bool {
	info, err := os.Stat(path)
	if err != nil {
		// File deleted or inaccessible = anomaly
		return true
	}
	
	// Check size change
	if info.Size() != baseline.Size {
		return true
	}
	
	// Check modification time
	if info.ModTime() != baseline.ModTime {
		// Recalculate hash to confirm modification
		hash, err := fm.calculateHash(path)
		if err != nil {
			return true // Error = treat as anomaly
		}
		
		if hash != baseline.Hash {
			return true // Hash mismatch = modification
		}
	}
	
	return false
}

// GetAnomalyScore returns current file anomaly score.
func (fm *FileMonitor) GetAnomalyScore() float64 {
	fm.mu.RLock()
	defer fm.mu.RUnlock()
	return fm.anomalyScore
}

// GetMonitoredFileCount returns number of monitored files.
func (fm *FileMonitor) GetMonitoredFileCount() int {
	fm.mu.RLock()
	defer fm.mu.RUnlock()
	return len(fm.criticalFiles)
}
