package auth

import (
"crypto/ed25519"
"os"
"path/filepath"
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func TestNewCryptoKeyManager(t *testing.T) {
t.Run("Valid storage path", func(t *testing.T) {
tmpDir := t.TempDir()
manager, err := NewCryptoKeyManager(tmpDir)

require.NoError(t, err)
assert.NotNil(t, manager)
assert.Equal(t, tmpDir, manager.keyStorage)
assert.NotNil(t, manager.rotation)
assert.Equal(t, 90*24*time.Hour, manager.rotation.MaxKeyAge)
})

t.Run("Empty storage path", func(t *testing.T) {
manager, err := NewCryptoKeyManager("")

assert.Error(t, err)
assert.Nil(t, manager)
assert.Contains(t, err.Error(), "key storage path cannot be empty")
})

t.Run("Creates storage directory", func(t *testing.T) {
tmpDir := filepath.Join(t.TempDir(), "nested", "path")
manager, err := NewCryptoKeyManager(tmpDir)

require.NoError(t, err)
assert.NotNil(t, manager)

// Verify directory was created
info, err := os.Stat(tmpDir)
require.NoError(t, err)
assert.True(t, info.IsDir())
})
}

func TestGenerateKeyPair(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())

t.Run("Successful generation", func(t *testing.T) {
keyPair, err := manager.GenerateKeyPair("test-key-1")

require.NoError(t, err)
assert.NotNil(t, keyPair)
assert.Equal(t, "test-key-1", keyPair.KeyID)
assert.NotNil(t, keyPair.PublicKey)
assert.NotNil(t, keyPair.PrivateKey)
assert.Equal(t, ed25519.PublicKeySize, len(keyPair.PublicKey))
assert.Equal(t, ed25519.PrivateKeySize, len(keyPair.PrivateKey))
assert.False(t, keyPair.CreatedAt.IsZero())
assert.False(t, keyPair.ExpiresAt.IsZero())
assert.True(t, keyPair.ExpiresAt.After(keyPair.CreatedAt))
})

t.Run("Empty keyID", func(t *testing.T) {
keyPair, err := manager.GenerateKeyPair("")

assert.Error(t, err)
assert.Nil(t, keyPair)
assert.Contains(t, err.Error(), "keyID cannot be empty")
})

t.Run("Sets expiration correctly", func(t *testing.T) {
keyPair, err := manager.GenerateKeyPair("test-key-2")

require.NoError(t, err)
expectedExpiry := keyPair.CreatedAt.Add(90 * 24 * time.Hour)
assert.WithinDuration(t, expectedExpiry, keyPair.ExpiresAt, time.Second)
})

t.Run("Multiple generations produce different keys", func(t *testing.T) {
keyPair1, _ := manager.GenerateKeyPair("key-1")
keyPair2, _ := manager.GenerateKeyPair("key-2")

assert.NotEqual(t, keyPair1.PublicKey, keyPair2.PublicKey)
assert.NotEqual(t, keyPair1.PrivateKey, keyPair2.PrivateKey)
})
}

func TestSaveAndLoadKeyPair(t *testing.T) {
tmpDir := t.TempDir()
manager, _ := NewCryptoKeyManager(tmpDir)

t.Run("Save and load round-trip", func(t *testing.T) {
// Generate and save
original, err := manager.GenerateKeyPair("test-key")
require.NoError(t, err)

err = manager.SaveKeyPair(original)
require.NoError(t, err)

// Create new manager and load
manager2, _ := NewCryptoKeyManager(tmpDir)
loaded, err := manager2.LoadKeyPair("test-key")

require.NoError(t, err)
assert.Equal(t, original.KeyID, loaded.KeyID)
assert.Equal(t, original.PublicKey, loaded.PublicKey)
assert.Equal(t, original.PrivateKey, loaded.PrivateKey)
assert.WithinDuration(t, original.CreatedAt, loaded.CreatedAt, time.Second)
assert.WithinDuration(t, original.ExpiresAt, loaded.ExpiresAt, time.Second)
})

t.Run("Save with nil keyPair", func(t *testing.T) {
err := manager.SaveKeyPair(nil)

assert.Error(t, err)
assert.Contains(t, err.Error(), "keyPair cannot be nil")
})

t.Run("Load non-existent key", func(t *testing.T) {
loaded, err := manager.LoadKeyPair("non-existent")

assert.Error(t, err)
assert.Nil(t, loaded)
})

t.Run("Files have correct permissions", func(t *testing.T) {
keyPair, _ := manager.GenerateKeyPair("perm-test")
err := manager.SaveKeyPair(keyPair)
require.NoError(t, err)

// Check private key permissions (should be 0600)
privPath := filepath.Join(tmpDir, "perm-test.priv.pem")
privInfo, err := os.Stat(privPath)
require.NoError(t, err)
assert.Equal(t, os.FileMode(0600), privInfo.Mode().Perm())

// Check public key permissions (should be 0644)
pubPath := filepath.Join(tmpDir, "perm-test.pub.pem")
pubInfo, err := os.Stat(pubPath)
require.NoError(t, err)
assert.Equal(t, os.FileMode(0644), pubInfo.Mode().Perm())
})
}

func TestSign(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())

t.Run("Successful signing", func(t *testing.T) {
_, err := manager.GenerateKeyPair("test-key")
require.NoError(t, err)

message := []byte("critical command: delete all pods")
signedMsg, err := manager.Sign(message)

require.NoError(t, err)
assert.NotNil(t, signedMsg)
assert.Equal(t, message, signedMsg.Message)
assert.NotEmpty(t, signedMsg.Signature)
assert.Equal(t, "test-key", signedMsg.KeyID)
assert.False(t, signedMsg.Timestamp.IsZero())
assert.Equal(t, ed25519.SignatureSize, len(signedMsg.Signature))
})

t.Run("Sign without key pair", func(t *testing.T) {
manager2, _ := NewCryptoKeyManager(t.TempDir())
signedMsg, err := manager2.Sign([]byte("test"))

assert.Error(t, err)
assert.Nil(t, signedMsg)
assert.Contains(t, err.Error(), "no key pair loaded")
})

t.Run("Sign with expired key", func(t *testing.T) {
keyPair, _ := manager.GenerateKeyPair("expired-key")
keyPair.ExpiresAt = time.Now().Add(-time.Hour) // Expired 1 hour ago
manager.keyPair = keyPair

signedMsg, err := manager.Sign([]byte("test"))

assert.Error(t, err)
assert.Nil(t, signedMsg)
assert.Contains(t, err.Error(), "key pair has expired")
})

t.Run("Different messages produce different signatures", func(t *testing.T) {
_, err := manager.GenerateKeyPair("test-key-2")
require.NoError(t, err)

msg1, _ := manager.Sign([]byte("message 1"))
msg2, _ := manager.Sign([]byte("message 2"))

assert.NotEqual(t, msg1.Signature, msg2.Signature)
})
}

func TestVerify(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())
manager.GenerateKeyPair("test-key")

t.Run("Valid signature", func(t *testing.T) {
message := []byte("important command")
signedMsg, _ := manager.Sign(message)

valid, err := manager.Verify(signedMsg)

require.NoError(t, err)
assert.True(t, valid)
})

t.Run("Invalid signature", func(t *testing.T) {
message := []byte("original message")
signedMsg, _ := manager.Sign(message)

// Tamper with message
signedMsg.Message = []byte("tampered message")

valid, err := manager.Verify(signedMsg)

require.NoError(t, err)
assert.False(t, valid)
})

t.Run("Nil signed message", func(t *testing.T) {
valid, err := manager.Verify(nil)

assert.Error(t, err)
assert.False(t, valid)
assert.Contains(t, err.Error(), "signedMessage cannot be nil")
})

t.Run("Wrong key ID", func(t *testing.T) {
message := []byte("test")
signedMsg, _ := manager.Sign(message)
signedMsg.KeyID = "wrong-key-id"

valid, err := manager.Verify(signedMsg)

assert.Error(t, err)
assert.False(t, valid)
assert.Contains(t, err.Error(), "key ID mismatch")
})

t.Run("No key pair loaded", func(t *testing.T) {
manager2, _ := NewCryptoKeyManager(t.TempDir())
signedMsg := &SignedMessage{
Message:   []byte("test"),
Signature: make([]byte, 64),
KeyID:     "test",
}

valid, err := manager2.Verify(signedMsg)

assert.Error(t, err)
assert.False(t, valid)
assert.Contains(t, err.Error(), "no key pair loaded")
})
}

func TestVerifyWithPublicKey(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())
manager.GenerateKeyPair("test-key")

t.Run("Valid signature with explicit public key", func(t *testing.T) {
message := []byte("test message")
signedMsg, _ := manager.Sign(message)

valid := manager.VerifyWithPublicKey(signedMsg, manager.keyPair.PublicKey)

assert.True(t, valid)
})

t.Run("Invalid public key", func(t *testing.T) {
message := []byte("test message")
signedMsg, _ := manager.Sign(message)

// Generate different key
_, wrongPrivateKey, _ := ed25519.GenerateKey(nil)
wrongPublicKey := wrongPrivateKey.Public().(ed25519.PublicKey)

valid := manager.VerifyWithPublicKey(signedMsg, wrongPublicKey)

assert.False(t, valid)
})

t.Run("Nil signed message", func(t *testing.T) {
valid := manager.VerifyWithPublicKey(nil, manager.keyPair.PublicKey)
assert.False(t, valid)
})

t.Run("Nil public key", func(t *testing.T) {
signedMsg := &SignedMessage{
Message:   []byte("test"),
Signature: make([]byte, 64),
}
valid := manager.VerifyWithPublicKey(signedMsg, nil)
assert.False(t, valid)
})
}

func TestRotateKey(t *testing.T) {
tmpDir := t.TempDir()
manager, _ := NewCryptoKeyManager(tmpDir)

t.Run("Successful rotation", func(t *testing.T) {
// Generate original key
original, _ := manager.GenerateKeyPair("key-v1")
originalPublicKey := original.PublicKey

// Rotate
newKey, err := manager.RotateKey("key-v2")

require.NoError(t, err)
assert.NotNil(t, newKey)
assert.Equal(t, "key-v2", newKey.KeyID)
assert.NotEqual(t, originalPublicKey, newKey.PublicKey)

// Check archive exists
archivePath := filepath.Join(tmpDir, "archive")
entries, err := os.ReadDir(archivePath)
require.NoError(t, err)
assert.NotEmpty(t, entries)
})

t.Run("Rotation when locked", func(t *testing.T) {
manager.GenerateKeyPair("locked-key")
manager.LockRotation()

newKey, err := manager.RotateKey("new-key")

assert.Error(t, err)
assert.Nil(t, newKey)
assert.Contains(t, err.Error(), "rotation is locked")

manager.UnlockRotation()
})

t.Run("First rotation without existing key", func(t *testing.T) {
manager2, _ := NewCryptoKeyManager(t.TempDir())

newKey, err := manager2.RotateKey("first-key")

require.NoError(t, err)
assert.NotNil(t, newKey)
assert.Equal(t, "first-key", newKey.KeyID)
})
}

func TestNeedsRotation(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())

t.Run("No key pair", func(t *testing.T) {
assert.True(t, manager.NeedsRotation())
})

t.Run("Fresh key", func(t *testing.T) {
manager.GenerateKeyPair("fresh-key")
assert.False(t, manager.NeedsRotation())
})

t.Run("Old key", func(t *testing.T) {
keyPair, _ := manager.GenerateKeyPair("old-key")
keyPair.CreatedAt = time.Now().Add(-91 * 24 * time.Hour) // 91 days ago
manager.keyPair = keyPair

assert.True(t, manager.NeedsRotation())
})
}

func TestIsInGracePeriod(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())

t.Run("No key pair", func(t *testing.T) {
assert.False(t, manager.IsInGracePeriod())
})

t.Run("Key not expired", func(t *testing.T) {
manager.GenerateKeyPair("valid-key")
assert.False(t, manager.IsInGracePeriod())
})

t.Run("Key expired within grace period", func(t *testing.T) {
keyPair, _ := manager.GenerateKeyPair("grace-key")
keyPair.ExpiresAt = time.Now().Add(-3 * 24 * time.Hour) // Expired 3 days ago
manager.keyPair = keyPair

assert.True(t, manager.IsInGracePeriod())
})

t.Run("Key expired beyond grace period", func(t *testing.T) {
keyPair, _ := manager.GenerateKeyPair("expired-key")
keyPair.ExpiresAt = time.Now().Add(-10 * 24 * time.Hour) // Expired 10 days ago
manager.keyPair = keyPair

assert.False(t, manager.IsInGracePeriod())
})
}

func TestRotationConfig(t *testing.T) {
manager, _ := NewCryptoKeyManager(t.TempDir())

t.Run("Set custom rotation config", func(t *testing.T) {
customConfig := &RotationConfig{
MaxKeyAge:   30 * 24 * time.Hour,
GracePeriod: 3 * 24 * time.Hour,
AutoRotate:  false,
}

manager.SetRotationConfig(customConfig)

assert.Equal(t, 30*24*time.Hour, manager.rotation.MaxKeyAge)
assert.Equal(t, 3*24*time.Hour, manager.rotation.GracePeriod)
assert.False(t, manager.rotation.AutoRotate)
})

t.Run("Lock and unlock rotation", func(t *testing.T) {
assert.False(t, manager.rotation.RotationLock)

manager.LockRotation()
assert.True(t, manager.rotation.RotationLock)

manager.UnlockRotation()
assert.False(t, manager.rotation.RotationLock)
})
}

func TestPEMEncoding(t *testing.T) {
t.Run("Private key PEM round-trip", func(t *testing.T) {
publicKey, privateKey, _ := ed25519.GenerateKey(nil)
createdAt := time.Now()
expiresAt := createdAt.Add(90 * 24 * time.Hour)

// Encode
pemData := encodePrivateKeyPEM(privateKey, createdAt, expiresAt)
assert.NotEmpty(t, pemData)
assert.Contains(t, string(pemData), "BEGIN PRIVATE KEY")
assert.Contains(t, string(pemData), "END PRIVATE KEY")

// Decode
decodedKey, decodedCreated, decodedExpires, err := parsePrivateKeyPEM(pemData)
require.NoError(t, err)
assert.Equal(t, privateKey, decodedKey)
assert.WithinDuration(t, createdAt, decodedCreated, time.Second)
assert.WithinDuration(t, expiresAt, decodedExpires, time.Second)

// Verify derived public key matches
assert.Equal(t, publicKey, decodedKey.Public().(ed25519.PublicKey))
})

t.Run("Public key PEM round-trip", func(t *testing.T) {
publicKey, _, _ := ed25519.GenerateKey(nil)

// Encode
pemData := encodePublicKeyPEM(publicKey)
assert.NotEmpty(t, pemData)
assert.Contains(t, string(pemData), "BEGIN PUBLIC KEY")
assert.Contains(t, string(pemData), "END PUBLIC KEY")

// Decode
decodedKey, err := parsePublicKeyPEM(pemData)
require.NoError(t, err)
assert.Equal(t, publicKey, decodedKey)
})
}

// Benchmarks
func BenchmarkGenerateKeyPair(b *testing.B) {
manager, _ := NewCryptoKeyManager(b.TempDir())

b.ResetTimer()
for i := 0; i < b.N; i++ {
_, _ = manager.GenerateKeyPair("bench-key")
}
}

func BenchmarkSign(b *testing.B) {
manager, _ := NewCryptoKeyManager(b.TempDir())
manager.GenerateKeyPair("bench-key")
message := []byte("benchmark message for signing performance test")

b.ResetTimer()
for i := 0; i < b.N; i++ {
_, _ = manager.Sign(message)
}
}

func BenchmarkVerify(b *testing.B) {
manager, _ := NewCryptoKeyManager(b.TempDir())
manager.GenerateKeyPair("bench-key")
message := []byte("benchmark message for verification performance test")
signedMsg, _ := manager.Sign(message)

b.ResetTimer()
for i := 0; i < b.N; i++ {
_, _ = manager.Verify(signedMsg)
}
}

func BenchmarkSaveKeyPair(b *testing.B) {
manager, _ := NewCryptoKeyManager(b.TempDir())
keyPair, _ := manager.GenerateKeyPair("bench-key")

b.ResetTimer()
for i := 0; i < b.N; i++ {
_ = manager.SaveKeyPair(keyPair)
}
}

func BenchmarkLoadKeyPair(b *testing.B) {
tmpDir := b.TempDir()
manager, _ := NewCryptoKeyManager(tmpDir)
keyPair, _ := manager.GenerateKeyPair("bench-key")
manager.SaveKeyPair(keyPair)

b.ResetTimer()
for i := 0; i < b.N; i++ {
_, _ = manager.LoadKeyPair("bench-key")
}
}
