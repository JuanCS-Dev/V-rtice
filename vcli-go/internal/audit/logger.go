// Package audit implements immutable audit logging (Layer 7)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 7 of the "Guardian of Intent" v2.0:
// "AUDITORIA IMUTÁVEL - O que você fez?"
//
// Provides:
// - Append-only audit log with BadgerDB
// - Blockchain-like hash chaining for tamper detection
// - Digital signatures
// - Remote syslog shipping
package audit

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/dgraph-io/badger/v4"
	"github.com/verticedev/vcli-go/pkg/security"
)

// Logger handles audit logging with tamper detection
type Logger struct {
	db         *badger.DB
	signer     Signer
	remote     RemoteSyslog
	lastHash   string
	
	// Config
	flushInterval time.Duration
	batchSize     int
}

// NewLogger creates a new audit logger
func NewLogger(db *badger.DB, signer Signer, remote RemoteSyslog) *Logger {
	return &Logger{
		db:            db,
		signer:        signer,
		remote:        remote,
		lastHash:      "",
		flushInterval: 5 * time.Second,
		batchSize:     10,
	}
}

// Signer interface for digital signatures
type Signer interface {
	Sign(data []byte) (string, error)
	Verify(data []byte, signature string) (bool, error)
}

// RemoteSyslog interface for remote logging
type RemoteSyslog interface {
	Send(ctx context.Context, entry *security.AuditEntry) error
}

// Log records an audit entry
//
// This creates an immutable audit trail with:
// - Hash of previous entry (blockchain-like chain)
// - Hash of current entry
// - Digital signature
// - Local storage (BadgerDB)
// - Remote shipping (async)
func (l *Logger) Log(ctx context.Context, entry *security.AuditEntry) error {
	// Generate unique ID
	entry.ID = l.generateID()
	entry.Timestamp = time.Now()
	
	// Set previous hash (chain link)
	entry.PreviousHash = l.lastHash
	
	// Calculate hash of this entry
	hash, err := l.calculateHash(entry)
	if err != nil {
		return fmt.Errorf("failed to calculate hash: %w", err)
	}
	entry.Hash = hash
	
	// Sign the entry
	signature, err := l.signEntry(entry)
	if err != nil {
		return fmt.Errorf("failed to sign entry: %w", err)
	}
	entry.Signature = signature
	
	// Store in BadgerDB (append-only)
	if err := l.store(entry); err != nil {
		return fmt.Errorf("failed to store entry: %w", err)
	}
	
	// Update last hash
	l.lastHash = hash
	
	// Ship to remote (async - don't block on network)
	if l.remote != nil {
		go func() {
			remoteCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			
			if err := l.remote.Send(remoteCtx, entry); err != nil {
				// TODO: Add retry logic and error logging
				// For now, local log is authoritative
			}
		}()
	}
	
	return nil
}

// Query retrieves audit entries matching criteria
func (l *Logger) Query(ctx context.Context, query *AuditQuery) ([]*security.AuditEntry, error) {
	entries := make([]*security.AuditEntry, 0)
	
	err := l.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchSize = 100
		
		it := txn.NewIterator(opts)
		defer it.Close()
		
		prefix := []byte("audit:")
		for it.Seek(prefix); it.ValidForPrefix(prefix); it.Next() {
			item := it.Item()
			
			err := item.Value(func(val []byte) error {
				var entry security.AuditEntry
				if err := json.Unmarshal(val, &entry); err != nil {
					return err
				}
				
				// Apply filters
				if query.matchesFilters(&entry) {
					entries = append(entries, &entry)
				}
				
				return nil
			})
			
			if err != nil {
				return err
			}
			
			// Limit results
			if query.Limit > 0 && len(entries) >= query.Limit {
				break
			}
		}
		
		return nil
	})
	
	if err != nil {
		return nil, err
	}
	
	return entries, nil
}

// VerifyIntegrity verifies the integrity of the audit log
//
// This checks:
// - Hash chain is unbroken
// - Each entry's hash is correct
// - Each entry's signature is valid
func (l *Logger) VerifyIntegrity(ctx context.Context) (*IntegrityReport, error) {
	report := &IntegrityReport{
		Verified:   true,
		TotalCount: 0,
		Errors:     make([]IntegrityError, 0),
	}
	
	var previousHash string
	
	err := l.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchSize = 100
		
		it := txn.NewIterator(opts)
		defer it.Close()
		
		prefix := []byte("audit:")
		for it.Seek(prefix); it.ValidForPrefix(prefix); it.Next() {
			item := it.Item()
			
			err := item.Value(func(val []byte) error {
				var entry security.AuditEntry
				if err := json.Unmarshal(val, &entry); err != nil {
					return err
				}
				
				report.TotalCount++
				
				// Check hash chain
				if entry.PreviousHash != previousHash {
					report.Verified = false
					report.Errors = append(report.Errors, IntegrityError{
						EntryID: entry.ID,
						Type:    "broken_chain",
						Message: fmt.Sprintf("Expected previous hash %s, got %s", previousHash, entry.PreviousHash),
					})
				}
				
				// Verify hash
				calculatedHash, err := l.calculateHash(&entry)
				if err != nil || calculatedHash != entry.Hash {
					report.Verified = false
					report.Errors = append(report.Errors, IntegrityError{
						EntryID: entry.ID,
						Type:    "invalid_hash",
						Message: "Entry hash does not match calculated hash",
					})
				}
				
				// Verify signature
				if l.signer != nil {
					valid, err := l.verifySignature(&entry)
					if err != nil || !valid {
						report.Verified = false
						report.Errors = append(report.Errors, IntegrityError{
							EntryID: entry.ID,
							Type:    "invalid_signature",
							Message: "Entry signature verification failed",
						})
					}
				}
				
				previousHash = entry.Hash
				return nil
			})
			
			if err != nil {
				return err
			}
		}
		
		return nil
	})
	
	if err != nil {
		return nil, err
	}
	
	return report, nil
}

// store persists an audit entry to BadgerDB
func (l *Logger) store(entry *security.AuditEntry) error {
	// Serialize entry
	data, err := json.Marshal(entry)
	if err != nil {
		return err
	}
	
	// Store with composite key: audit:<timestamp>:<id>
	key := fmt.Sprintf("audit:%d:%s", entry.Timestamp.UnixNano(), entry.ID)
	
	return l.db.Update(func(txn *badger.Txn) error {
		return txn.Set([]byte(key), data)
	})
}

// calculateHash computes SHA-256 hash of entry
func (l *Logger) calculateHash(entry *security.AuditEntry) (string, error) {
	// Create a copy without hash and signature
	hashEntry := *entry
	hashEntry.Hash = ""
	hashEntry.Signature = ""
	
	// Serialize
	data, err := json.Marshal(hashEntry)
	if err != nil {
		return "", err
	}
	
	// Calculate SHA-256
	hash := sha256.Sum256(data)
	return hex.EncodeToString(hash[:]), nil
}

// signEntry creates a digital signature for the entry
func (l *Logger) signEntry(entry *security.AuditEntry) (string, error) {
	if l.signer == nil {
		return "", nil // Signing not configured
	}
	
	// Serialize entry without signature
	signEntry := *entry
	signEntry.Signature = ""
	
	data, err := json.Marshal(signEntry)
	if err != nil {
		return "", err
	}
	
	return l.signer.Sign(data)
}

// verifySignature verifies the digital signature of an entry
func (l *Logger) verifySignature(entry *security.AuditEntry) (bool, error) {
	if l.signer == nil {
		return true, nil // Signing not configured
	}
	
	// Serialize entry without signature
	verifyEntry := *entry
	verifyEntry.Signature = ""
	
	data, err := json.Marshal(verifyEntry)
	if err != nil {
		return false, err
	}
	
	return l.signer.Verify(data, entry.Signature)
}

// generateID generates a unique entry ID
func (l *Logger) generateID() string {
	// Use timestamp + random suffix for uniqueness
	return fmt.Sprintf("%d-%s", time.Now().UnixNano(), randomString(8))
}

// randomString generates a random alphanumeric string
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// AuditQuery defines query parameters for audit log search
type AuditQuery struct {
	UserID     string
	SessionID  string
	StartTime  time.Time
	EndTime    time.Time
	Intent     string
	RiskLevel  string
	Executed   *bool // nil = any, true = executed only, false = not executed only
	Limit      int
}

// matchesFilters checks if an entry matches query filters
func (q *AuditQuery) matchesFilters(entry *security.AuditEntry) bool {
	if q.UserID != "" && entry.User.ID != q.UserID {
		return false
	}
	
	if q.SessionID != "" && entry.Session.ID != q.SessionID {
		return false
	}
	
	if !q.StartTime.IsZero() && entry.Timestamp.Before(q.StartTime) {
		return false
	}
	
	if !q.EndTime.IsZero() && entry.Timestamp.After(q.EndTime) {
		return false
	}
	
	if q.Intent != "" && entry.Intent != q.Intent {
		return false
	}
	
	if q.RiskLevel != "" && entry.RiskLevel != q.RiskLevel {
		return false
	}
	
	if q.Executed != nil && entry.Executed != *q.Executed {
		return false
	}
	
	return true
}

// IntegrityReport contains results of integrity verification
type IntegrityReport struct {
	Verified   bool
	TotalCount int
	Errors     []IntegrityError
}

// IntegrityError represents an integrity violation
type IntegrityError struct {
	EntryID string
	Type    string
	Message string
}
