package auth

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

var (
	// ErrKeyNotFound is returned when a key is not found in the keyring
	ErrKeyNotFound = errors.New("key not found")
	
	// ErrInvalidKeyFormat is returned when key format is invalid
	ErrInvalidKeyFormat = errors.New("invalid key format")
	
	// ErrKeyAlreadyExists is returned when trying to add a duplicate key
	ErrKeyAlreadyExists = errors.New("key already exists")
)

// KeyPair represents an RSA key pair
type KeyPair struct {
	PrivateKey *rsa.PrivateKey
	PublicKey  *rsa.PublicKey
	KeyID      string
	CreatedAt  int64
}

// Keyring manages cryptographic keys for authentication
type Keyring struct {
	mu         sync.RWMutex
	keys       map[string]*KeyPair
	storePath  string
	keySize    int
}

// NewKeyring creates a new keyring
func NewKeyring(storePath string) *Keyring {
	return &Keyring{
		keys:      make(map[string]*KeyPair),
		storePath: storePath,
		keySize:   4096, // RSA 4096-bit as per Doutrina
	}
}

// GenerateKeyPair generates a new RSA key pair
func (k *Keyring) GenerateKeyPair(keyID string) (*KeyPair, error) {
	k.mu.Lock()
	defer k.mu.Unlock()

	// Check if key already exists
	if _, exists := k.keys[keyID]; exists {
		return nil, ErrKeyAlreadyExists
	}

	// Generate private key
	privateKey, err := rsa.GenerateKey(rand.Reader, k.keySize)
	if err != nil {
		return nil, fmt.Errorf("failed to generate private key: %w", err)
	}

	keyPair := &KeyPair{
		PrivateKey: privateKey,
		PublicKey:  &privateKey.PublicKey,
		KeyID:      keyID,
		CreatedAt:  currentTimestamp(),
	}

	// Store in memory
	k.keys[keyID] = keyPair

	// Persist to disk
	if err := k.saveKeyPair(keyPair); err != nil {
		delete(k.keys, keyID)
		return nil, fmt.Errorf("failed to persist key: %w", err)
	}

	return keyPair, nil
}

// GetKeyPair retrieves a key pair by ID
func (k *Keyring) GetKeyPair(keyID string) (*KeyPair, error) {
	k.mu.RLock()
	defer k.mu.RUnlock()

	keyPair, exists := k.keys[keyID]
	if !exists {
		return nil, ErrKeyNotFound
	}

	return keyPair, nil
}

// AddKeyPair adds an existing key pair to the keyring
func (k *Keyring) AddKeyPair(keyID string, privateKey *rsa.PrivateKey) error {
	k.mu.Lock()
	defer k.mu.Unlock()

	if _, exists := k.keys[keyID]; exists {
		return ErrKeyAlreadyExists
	}

	keyPair := &KeyPair{
		PrivateKey: privateKey,
		PublicKey:  &privateKey.PublicKey,
		KeyID:      keyID,
		CreatedAt:  currentTimestamp(),
	}

	k.keys[keyID] = keyPair

	if err := k.saveKeyPair(keyPair); err != nil {
		delete(k.keys, keyID)
		return fmt.Errorf("failed to persist key: %w", err)
	}

	return nil
}

// DeleteKeyPair removes a key pair from the keyring
func (k *Keyring) DeleteKeyPair(keyID string) error {
	k.mu.Lock()
	defer k.mu.Unlock()

	if _, exists := k.keys[keyID]; !exists {
		return ErrKeyNotFound
	}

	// Remove from memory
	delete(k.keys, keyID)

	// Remove from disk
	if err := k.deleteKeyFiles(keyID); err != nil {
		return fmt.Errorf("failed to delete key files: %w", err)
	}

	return nil
}

// ListKeys returns all key IDs in the keyring
func (k *Keyring) ListKeys() []string {
	k.mu.RLock()
	defer k.mu.RUnlock()

	keys := make([]string, 0, len(k.keys))
	for keyID := range k.keys {
		keys = append(keys, keyID)
	}

	return keys
}

// LoadFromDisk loads all keys from disk
func (k *Keyring) LoadFromDisk() error {
	k.mu.Lock()
	defer k.mu.Unlock()

	if k.storePath == "" {
		return errors.New("store path not configured")
	}

	// Create directory if it doesn't exist
	if err := os.MkdirAll(k.storePath, 0700); err != nil {
		return fmt.Errorf("failed to create store directory: %w", err)
	}

	// Read all .key files
	entries, err := os.ReadDir(k.storePath)
	if err != nil {
		return fmt.Errorf("failed to read store directory: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".key" {
			continue
		}

		keyID := entry.Name()[:len(entry.Name())-4] // Remove .key extension
		
		keyPair, err := k.loadKeyPair(keyID)
		if err != nil {
			// Log error but continue loading other keys
			fmt.Fprintf(os.Stderr, "Warning: failed to load key %s: %v\n", keyID, err)
			continue
		}

		k.keys[keyID] = keyPair
	}

	return nil
}

// saveKeyPair persists a key pair to disk
func (k *Keyring) saveKeyPair(keyPair *KeyPair) error {
	if k.storePath == "" {
		return errors.New("store path not configured")
	}

	// Create directory if it doesn't exist
	if err := os.MkdirAll(k.storePath, 0700); err != nil {
		return fmt.Errorf("failed to create store directory: %w", err)
	}

	// Save private key
	privateKeyPath := filepath.Join(k.storePath, keyPair.KeyID+".key")
	privateKeyPEM := k.encodePrivateKey(keyPair.PrivateKey)
	if err := os.WriteFile(privateKeyPath, privateKeyPEM, 0600); err != nil {
		return fmt.Errorf("failed to write private key: %w", err)
	}

	// Save public key
	publicKeyPath := filepath.Join(k.storePath, keyPair.KeyID+".pub")
	publicKeyPEM, err := k.encodePublicKey(keyPair.PublicKey)
	if err != nil {
		return fmt.Errorf("failed to encode public key: %w", err)
	}
	if err := os.WriteFile(publicKeyPath, publicKeyPEM, 0644); err != nil {
		return fmt.Errorf("failed to write public key: %w", err)
	}

	return nil
}

// loadKeyPair loads a key pair from disk
func (k *Keyring) loadKeyPair(keyID string) (*KeyPair, error) {
	if k.storePath == "" {
		return nil, errors.New("store path not configured")
	}

	// Load private key
	privateKeyPath := filepath.Join(k.storePath, keyID+".key")
	privateKeyPEM, err := os.ReadFile(privateKeyPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read private key: %w", err)
	}

	privateKey, err := k.decodePrivateKey(privateKeyPEM)
	if err != nil {
		return nil, fmt.Errorf("failed to decode private key: %w", err)
	}

	keyPair := &KeyPair{
		PrivateKey: privateKey,
		PublicKey:  &privateKey.PublicKey,
		KeyID:      keyID,
		CreatedAt:  currentTimestamp(),
	}

	return keyPair, nil
}

// deleteKeyFiles removes key files from disk
func (k *Keyring) deleteKeyFiles(keyID string) error {
	if k.storePath == "" {
		return errors.New("store path not configured")
	}

	privateKeyPath := filepath.Join(k.storePath, keyID+".key")
	publicKeyPath := filepath.Join(k.storePath, keyID+".pub")

	// Remove private key
	if err := os.Remove(privateKeyPath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove private key: %w", err)
	}

	// Remove public key
	if err := os.Remove(publicKeyPath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove public key: %w", err)
	}

	return nil
}

// encodePrivateKey encodes a private key to PEM format
func (k *Keyring) encodePrivateKey(privateKey *rsa.PrivateKey) []byte {
	privateKeyBytes := x509.MarshalPKCS1PrivateKey(privateKey)
	
	privateKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: privateKeyBytes,
	})

	return privateKeyPEM
}

// decodePrivateKey decodes a private key from PEM format
func (k *Keyring) decodePrivateKey(privateKeyPEM []byte) (*rsa.PrivateKey, error) {
	block, _ := pem.Decode(privateKeyPEM)
	if block == nil {
		return nil, ErrInvalidKeyFormat
	}

	privateKey, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse private key: %w", err)
	}

	return privateKey, nil
}

// encodePublicKey encodes a public key to PEM format
func (k *Keyring) encodePublicKey(publicKey *rsa.PublicKey) ([]byte, error) {
	publicKeyBytes, err := x509.MarshalPKIXPublicKey(publicKey)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal public key: %w", err)
	}

	publicKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PUBLIC KEY",
		Bytes: publicKeyBytes,
	})

	return publicKeyPEM, nil
}

// RotateKey generates a new key pair and marks the old one for deprecation
func (k *Keyring) RotateKey(oldKeyID, newKeyID string) (*KeyPair, error) {
	// Verify old key exists
	if _, err := k.GetKeyPair(oldKeyID); err != nil {
		return nil, fmt.Errorf("old key not found: %w", err)
	}

	// Generate new key
	newKeyPair, err := k.GenerateKeyPair(newKeyID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate new key: %w", err)
	}

	// In production, we'd mark the old key for deprecation and keep it
	// for a grace period to validate existing tokens
	// For now, we keep both keys

	return newKeyPair, nil
}

// ExportPublicKey exports a public key in PEM format
func (k *Keyring) ExportPublicKey(keyID string) ([]byte, error) {
	keyPair, err := k.GetKeyPair(keyID)
	if err != nil {
		return nil, err
	}

	return k.encodePublicKey(keyPair.PublicKey)
}

// currentTimestamp returns current Unix timestamp
func currentTimestamp() int64 {
	return time.Now().Unix()
}
