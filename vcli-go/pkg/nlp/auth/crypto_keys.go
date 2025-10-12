// Package auth provides Layer 1 (Authentication) of the Guardian Zero Trust Security.
package auth

import (
"crypto/ed25519"
"crypto/rand"
"crypto/x509"
"encoding/pem"
"errors"
"fmt"
"os"
"path/filepath"
"time"
)

// CryptoKeyManager manages Ed25519 cryptographic keys for signatures and verification.
// Part of Layer 1: Authentication - enables cryptographic signing of critical commands.
type CryptoKeyManager struct {
keyPair    *KeyPair
keyStorage string // Directory for persistent key storage
rotation   *RotationConfig
}

// KeyPair represents an Ed25519 public/private key pair.
type KeyPair struct {
PublicKey  ed25519.PublicKey
PrivateKey ed25519.PrivateKey
CreatedAt  time.Time
ExpiresAt  time.Time
KeyID      string // Unique identifier for this key
}

// RotationConfig defines key rotation policies.
type RotationConfig struct {
MaxKeyAge    time.Duration // Maximum age before rotation required
GracePeriod  time.Duration // Period where old key still accepted
AutoRotate   bool          // Enable automatic rotation
RotationLock bool          // Prevent rotation during critical operations
}

// SignedMessage represents a message signed with Ed25519.
type SignedMessage struct {
Message   []byte
Signature []byte
KeyID     string
Timestamp time.Time
}

// NewCryptoKeyManager creates a new cryptographic key manager.
func NewCryptoKeyManager(keyStorage string) (*CryptoKeyManager, error) {
if keyStorage == "" {
return nil, errors.New("key storage path cannot be empty")
}

// Ensure storage directory exists
if err := os.MkdirAll(keyStorage, 0700); err != nil {
return nil, fmt.Errorf("failed to create key storage directory: %w", err)
}

// Default rotation config: rotate every 90 days, 7-day grace period
rotation := &RotationConfig{
MaxKeyAge:   90 * 24 * time.Hour,
GracePeriod: 7 * 24 * time.Hour,
AutoRotate:  true,
}

return &CryptoKeyManager{
keyStorage: keyStorage,
rotation:   rotation,
}, nil
}

// GenerateKeyPair generates a new Ed25519 key pair.
func (m *CryptoKeyManager) GenerateKeyPair(keyID string) (*KeyPair, error) {
if keyID == "" {
return nil, errors.New("keyID cannot be empty")
}

publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
if err != nil {
return nil, fmt.Errorf("failed to generate Ed25519 key pair: %w", err)
}

now := time.Now()
keyPair := &KeyPair{
PublicKey:  publicKey,
PrivateKey: privateKey,
CreatedAt:  now,
ExpiresAt:  now.Add(m.rotation.MaxKeyAge),
KeyID:      keyID,
}

m.keyPair = keyPair
return keyPair, nil
}

// LoadKeyPair loads an existing key pair from disk.
func (m *CryptoKeyManager) LoadKeyPair(keyID string) (*KeyPair, error) {
if keyID == "" {
return nil, errors.New("keyID cannot be empty")
}

privateKeyPath := filepath.Join(m.keyStorage, fmt.Sprintf("%s.priv.pem", keyID))
publicKeyPath := filepath.Join(m.keyStorage, fmt.Sprintf("%s.pub.pem", keyID))

// Load private key
privateKeyPEM, err := os.ReadFile(privateKeyPath)
if err != nil {
return nil, fmt.Errorf("failed to read private key: %w", err)
}

privateKey, createdAt, expiresAt, err := parsePrivateKeyPEM(privateKeyPEM)
if err != nil {
return nil, fmt.Errorf("failed to parse private key: %w", err)
}

// Load public key
publicKeyPEM, err := os.ReadFile(publicKeyPath)
if err != nil {
return nil, fmt.Errorf("failed to read public key: %w", err)
}

publicKey, err := parsePublicKeyPEM(publicKeyPEM)
if err != nil {
return nil, fmt.Errorf("failed to parse public key: %w", err)
}

keyPair := &KeyPair{
PublicKey:  publicKey,
PrivateKey: privateKey,
CreatedAt:  createdAt,
ExpiresAt:  expiresAt,
KeyID:      keyID,
}

m.keyPair = keyPair
return keyPair, nil
}

// SaveKeyPair persists the key pair to disk in PEM format.
func (m *CryptoKeyManager) SaveKeyPair(keyPair *KeyPair) error {
if keyPair == nil {
return errors.New("keyPair cannot be nil")
}

privateKeyPath := filepath.Join(m.keyStorage, fmt.Sprintf("%s.priv.pem", keyPair.KeyID))
publicKeyPath := filepath.Join(m.keyStorage, fmt.Sprintf("%s.pub.pem", keyPair.KeyID))

// Save private key
privateKeyPEM := encodePrivateKeyPEM(keyPair.PrivateKey, keyPair.CreatedAt, keyPair.ExpiresAt)
if err := os.WriteFile(privateKeyPath, privateKeyPEM, 0600); err != nil {
return fmt.Errorf("failed to write private key: %w", err)
}

// Save public key
publicKeyPEM := encodePublicKeyPEM(keyPair.PublicKey)
if err := os.WriteFile(publicKeyPath, publicKeyPEM, 0644); err != nil {
return fmt.Errorf("failed to write public key: %w", err)
}

return nil
}

// Sign creates a digital signature for the given message.
func (m *CryptoKeyManager) Sign(message []byte) (*SignedMessage, error) {
if m.keyPair == nil {
return nil, errors.New("no key pair loaded; call GenerateKeyPair or LoadKeyPair first")
}

// Check if key is expired
if time.Now().After(m.keyPair.ExpiresAt) {
return nil, errors.New("key pair has expired; rotation required")
}

signature := ed25519.Sign(m.keyPair.PrivateKey, message)

return &SignedMessage{
Message:   message,
Signature: signature,
KeyID:     m.keyPair.KeyID,
Timestamp: time.Now(),
}, nil
}

// Verify validates a signature against the message using the current public key.
func (m *CryptoKeyManager) Verify(signedMsg *SignedMessage) (bool, error) {
if signedMsg == nil {
return false, errors.New("signedMessage cannot be nil")
}

if m.keyPair == nil {
return false, errors.New("no key pair loaded; call GenerateKeyPair or LoadKeyPair first")
}

// Verify key ID matches
if signedMsg.KeyID != m.keyPair.KeyID {
return false, fmt.Errorf("key ID mismatch: expected %s, got %s", m.keyPair.KeyID, signedMsg.KeyID)
}

// Verify signature
valid := ed25519.Verify(m.keyPair.PublicKey, signedMsg.Message, signedMsg.Signature)
return valid, nil
}

// VerifyWithPublicKey verifies a signature using an explicit public key.
// Useful for verifying messages signed with rotated keys.
func (m *CryptoKeyManager) VerifyWithPublicKey(signedMsg *SignedMessage, publicKey ed25519.PublicKey) bool {
if signedMsg == nil || publicKey == nil {
return false
}

return ed25519.Verify(publicKey, signedMsg.Message, signedMsg.Signature)
}

// RotateKey generates a new key pair and archives the old one.
func (m *CryptoKeyManager) RotateKey(newKeyID string) (*KeyPair, error) {
if m.rotation.RotationLock {
return nil, errors.New("key rotation is locked; critical operation in progress")
}

// Archive old key if exists
if m.keyPair != nil {
archivePath := filepath.Join(m.keyStorage, "archive")
if err := os.MkdirAll(archivePath, 0700); err != nil {
return nil, fmt.Errorf("failed to create archive directory: %w", err)
}

oldKeyPath := filepath.Join(archivePath, fmt.Sprintf("%s.%d.pem", m.keyPair.KeyID, time.Now().Unix()))
if err := m.archiveKey(m.keyPair, oldKeyPath); err != nil {
return nil, fmt.Errorf("failed to archive old key: %w", err)
}
}

// Generate new key pair
newKeyPair, err := m.GenerateKeyPair(newKeyID)
if err != nil {
return nil, fmt.Errorf("failed to generate new key pair: %w", err)
}

// Save new key pair
if err := m.SaveKeyPair(newKeyPair); err != nil {
return nil, fmt.Errorf("failed to save new key pair: %w", err)
}

return newKeyPair, nil
}

// NeedsRotation checks if the current key needs rotation.
func (m *CryptoKeyManager) NeedsRotation() bool {
if m.keyPair == nil {
return true
}

age := time.Since(m.keyPair.CreatedAt)
return age >= m.rotation.MaxKeyAge
}

// IsInGracePeriod checks if an expired key is still within grace period.
func (m *CryptoKeyManager) IsInGracePeriod() bool {
if m.keyPair == nil {
return false
}

if time.Now().Before(m.keyPair.ExpiresAt) {
return false // Not expired yet
}

gracePeriodEnd := m.keyPair.ExpiresAt.Add(m.rotation.GracePeriod)
return time.Now().Before(gracePeriodEnd)
}

// SetRotationConfig updates the rotation configuration.
func (m *CryptoKeyManager) SetRotationConfig(config *RotationConfig) {
if config != nil {
m.rotation = config
}
}

// LockRotation prevents key rotation (used during critical operations).
func (m *CryptoKeyManager) LockRotation() {
m.rotation.RotationLock = true
}

// UnlockRotation allows key rotation again.
func (m *CryptoKeyManager) UnlockRotation() {
m.rotation.RotationLock = false
}

// archiveKey archives an old key pair.
func (m *CryptoKeyManager) archiveKey(keyPair *KeyPair, archivePath string) error {
privateKeyPEM := encodePrivateKeyPEM(keyPair.PrivateKey, keyPair.CreatedAt, keyPair.ExpiresAt)
return os.WriteFile(archivePath, privateKeyPEM, 0600)
}

// encodePrivateKeyPEM encodes a private key to PEM format with metadata.
func encodePrivateKeyPEM(privateKey ed25519.PrivateKey, createdAt, expiresAt time.Time) []byte {
// PKCS#8 format for Ed25519
pkcs8Key, _ := x509.MarshalPKCS8PrivateKey(privateKey)

block := &pem.Block{
Type:  "PRIVATE KEY",
Bytes: pkcs8Key,
Headers: map[string]string{
"Created-At": createdAt.Format(time.RFC3339),
"Expires-At": expiresAt.Format(time.RFC3339),
},
}

return pem.EncodeToMemory(block)
}

// encodePublicKeyPEM encodes a public key to PEM format.
func encodePublicKeyPEM(publicKey ed25519.PublicKey) []byte {
pkixKey, _ := x509.MarshalPKIXPublicKey(publicKey)

block := &pem.Block{
Type:  "PUBLIC KEY",
Bytes: pkixKey,
}

return pem.EncodeToMemory(block)
}

// parsePrivateKeyPEM parses a PEM-encoded private key with metadata.
func parsePrivateKeyPEM(pemData []byte) (ed25519.PrivateKey, time.Time, time.Time, error) {
block, _ := pem.Decode(pemData)
if block == nil {
return nil, time.Time{}, time.Time{}, errors.New("failed to decode PEM block")
}

if block.Type != "PRIVATE KEY" {
return nil, time.Time{}, time.Time{}, fmt.Errorf("unexpected PEM block type: %s", block.Type)
}

// Parse timestamps from headers
createdAt, err := time.Parse(time.RFC3339, block.Headers["Created-At"])
if err != nil {
createdAt = time.Now()
}

expiresAt, err := time.Parse(time.RFC3339, block.Headers["Expires-At"])
if err != nil {
expiresAt = time.Now().Add(90 * 24 * time.Hour) // Default 90 days
}

// Parse PKCS#8 key
key, err := x509.ParsePKCS8PrivateKey(block.Bytes)
if err != nil {
return nil, time.Time{}, time.Time{}, fmt.Errorf("failed to parse PKCS8 private key: %w", err)
}

privateKey, ok := key.(ed25519.PrivateKey)
if !ok {
return nil, time.Time{}, time.Time{}, errors.New("not an Ed25519 private key")
}

return privateKey, createdAt, expiresAt, nil
}

// parsePublicKeyPEM parses a PEM-encoded public key.
func parsePublicKeyPEM(pemData []byte) (ed25519.PublicKey, error) {
block, _ := pem.Decode(pemData)
if block == nil {
return nil, errors.New("failed to decode PEM block")
}

if block.Type != "PUBLIC KEY" {
return nil, fmt.Errorf("unexpected PEM block type: %s", block.Type)
}

// Parse PKIX key
key, err := x509.ParsePKIXPublicKey(block.Bytes)
if err != nil {
return nil, fmt.Errorf("failed to parse PKIX public key: %w", err)
}

publicKey, ok := key.(ed25519.PublicKey)
if !ok {
return nil, errors.New("not an Ed25519 public key")
}

return publicKey, nil
}
