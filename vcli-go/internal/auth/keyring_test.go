package auth

import (
	"os"
	"path/filepath"
	"testing"
)

func TestKeyring_GenerateKeyPair(t *testing.T) {
	// Create temporary directory for testing
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	tests := []struct {
		name    string
		keyID   string
		wantErr bool
	}{
		{
			name:    "valid key generation",
			keyID:   "test-key-1",
			wantErr: false,
		},
		{
			name:    "duplicate key",
			keyID:   "test-key-1", // Same as above
			wantErr: true,
		},
		{
			name:    "another valid key",
			keyID:   "test-key-2",
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			keyPair, err := keyring.GenerateKeyPair(tt.keyID)

			if (err != nil) != tt.wantErr {
				t.Errorf("GenerateKeyPair() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				if keyPair == nil {
					t.Error("GenerateKeyPair() returned nil key pair")
					return
				}
				if keyPair.PrivateKey == nil {
					t.Error("GenerateKeyPair() returned nil private key")
				}
				if keyPair.PublicKey == nil {
					t.Error("GenerateKeyPair() returned nil public key")
				}
				if keyPair.KeyID != tt.keyID {
					t.Errorf("GenerateKeyPair() keyID = %v, want %v", keyPair.KeyID, tt.keyID)
				}

				// Verify key size
				if keyPair.PrivateKey.Size()*8 != keyring.keySize {
					t.Errorf("GenerateKeyPair() key size = %v bits, want %v", keyPair.PrivateKey.Size()*8, keyring.keySize)
				}

				// Verify files were created
				privateKeyPath := filepath.Join(tmpDir, tt.keyID+".key")
				publicKeyPath := filepath.Join(tmpDir, tt.keyID+".pub")

				if _, err := os.Stat(privateKeyPath); os.IsNotExist(err) {
					t.Errorf("Private key file not created: %v", privateKeyPath)
				}
				if _, err := os.Stat(publicKeyPath); os.IsNotExist(err) {
					t.Errorf("Public key file not created: %v", publicKeyPath)
				}
			}
		})
	}
}

func TestKeyring_GetKeyPair(t *testing.T) {
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	// Generate a key
	keyID := "test-key"
	generatedPair, err := keyring.GenerateKeyPair(keyID)
	if err != nil {
		t.Fatalf("Failed to generate test key: %v", err)
	}

	tests := []struct {
		name    string
		keyID   string
		wantErr bool
	}{
		{
			name:    "existing key",
			keyID:   keyID,
			wantErr: false,
		},
		{
			name:    "non-existent key",
			keyID:   "non-existent",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			retrievedPair, err := keyring.GetKeyPair(tt.keyID)

			if (err != nil) != tt.wantErr {
				t.Errorf("GetKeyPair() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				if retrievedPair == nil {
					t.Error("GetKeyPair() returned nil")
					return
				}
				if retrievedPair.KeyID != generatedPair.KeyID {
					t.Errorf("GetKeyPair() keyID = %v, want %v", retrievedPair.KeyID, generatedPair.KeyID)
				}
				// Verify it's the same key
				if retrievedPair.PrivateKey.N.Cmp(generatedPair.PrivateKey.N) != 0 {
					t.Error("GetKeyPair() returned different key")
				}
			}
		})
	}
}

func TestKeyring_DeleteKeyPair(t *testing.T) {
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	// Generate a key
	keyID := "test-key-delete"
	_, err := keyring.GenerateKeyPair(keyID)
	if err != nil {
		t.Fatalf("Failed to generate test key: %v", err)
	}

	// Verify key exists
	_, err = keyring.GetKeyPair(keyID)
	if err != nil {
		t.Fatalf("Key should exist before deletion: %v", err)
	}

	// Delete key
	err = keyring.DeleteKeyPair(keyID)
	if err != nil {
		t.Errorf("DeleteKeyPair() error = %v", err)
	}

	// Verify key no longer exists
	_, err = keyring.GetKeyPair(keyID)
	if err != ErrKeyNotFound {
		t.Errorf("GetKeyPair() after delete error = %v, want %v", err, ErrKeyNotFound)
	}

	// Verify files were deleted
	privateKeyPath := filepath.Join(tmpDir, keyID+".key")
	publicKeyPath := filepath.Join(tmpDir, keyID+".pub")

	if _, err := os.Stat(privateKeyPath); !os.IsNotExist(err) {
		t.Error("Private key file should be deleted")
	}
	if _, err := os.Stat(publicKeyPath); !os.IsNotExist(err) {
		t.Error("Public key file should be deleted")
	}
}

func TestKeyring_ListKeys(t *testing.T) {
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	// Initially empty
	keys := keyring.ListKeys()
	if len(keys) != 0 {
		t.Errorf("ListKeys() returned %v keys, want 0", len(keys))
	}

	// Generate multiple keys
	keyIDs := []string{"key1", "key2", "key3"}
	for _, keyID := range keyIDs {
		if _, err := keyring.GenerateKeyPair(keyID); err != nil {
			t.Fatalf("Failed to generate key %s: %v", keyID, err)
		}
	}

	// Verify list
	keys = keyring.ListKeys()
	if len(keys) != len(keyIDs) {
		t.Errorf("ListKeys() returned %v keys, want %v", len(keys), len(keyIDs))
	}

	// Verify all keys are present (order may vary)
	keyMap := make(map[string]bool)
	for _, key := range keys {
		keyMap[key] = true
	}
	for _, expectedKey := range keyIDs {
		if !keyMap[expectedKey] {
			t.Errorf("ListKeys() missing key %v", expectedKey)
		}
	}
}

func TestKeyring_LoadFromDisk(t *testing.T) {
	tmpDir := t.TempDir()

	// Create first keyring and generate keys
	keyring1 := NewKeyring(tmpDir)
	keyIDs := []string{"key1", "key2"}
	for _, keyID := range keyIDs {
		if _, err := keyring1.GenerateKeyPair(keyID); err != nil {
			t.Fatalf("Failed to generate key %s: %v", keyID, err)
		}
	}

	// Create new keyring and load from disk
	keyring2 := NewKeyring(tmpDir)
	if err := keyring2.LoadFromDisk(); err != nil {
		t.Errorf("LoadFromDisk() error = %v", err)
	}

	// Verify keys were loaded
	loadedKeys := keyring2.ListKeys()
	if len(loadedKeys) != len(keyIDs) {
		t.Errorf("LoadFromDisk() loaded %v keys, want %v", len(loadedKeys), len(keyIDs))
	}

	// Verify each key can be retrieved and matches
	for _, keyID := range keyIDs {
		key1, _ := keyring1.GetKeyPair(keyID)
		key2, err := keyring2.GetKeyPair(keyID)
		
		if err != nil {
			t.Errorf("Failed to get loaded key %s: %v", keyID, err)
			continue
		}

		if key1.PrivateKey.N.Cmp(key2.PrivateKey.N) != 0 {
			t.Errorf("Loaded key %s does not match original", keyID)
		}
	}
}

func TestKeyring_RotateKey(t *testing.T) {
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	oldKeyID := "old-key"
	newKeyID := "new-key"

	// Generate old key
	oldKey, err := keyring.GenerateKeyPair(oldKeyID)
	if err != nil {
		t.Fatalf("Failed to generate old key: %v", err)
	}

	// Rotate to new key
	newKey, err := keyring.RotateKey(oldKeyID, newKeyID)
	if err != nil {
		t.Errorf("RotateKey() error = %v", err)
		return
	}

	if newKey == nil {
		t.Fatal("RotateKey() returned nil")
	}

	// Verify new key exists
	retrievedNew, err := keyring.GetKeyPair(newKeyID)
	if err != nil {
		t.Errorf("Failed to get new key: %v", err)
	}

	// Verify old key still exists (for grace period)
	retrievedOld, err := keyring.GetKeyPair(oldKeyID)
	if err != nil {
		t.Errorf("Failed to get old key: %v", err)
	}

	// Verify they are different keys
	if retrievedOld.PrivateKey.N.Cmp(retrievedNew.PrivateKey.N) == 0 {
		t.Error("Rotated key should be different from old key")
	}

	// Verify old key matches original
	if oldKey.PrivateKey.N.Cmp(retrievedOld.PrivateKey.N) != 0 {
		t.Error("Old key changed during rotation")
	}
}

func TestKeyring_ExportPublicKey(t *testing.T) {
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	keyID := "export-test"
	_, err := keyring.GenerateKeyPair(keyID)
	if err != nil {
		t.Fatalf("Failed to generate key: %v", err)
	}

	publicKeyPEM, err := keyring.ExportPublicKey(keyID)
	if err != nil {
		t.Errorf("ExportPublicKey() error = %v", err)
		return
	}

	if len(publicKeyPEM) == 0 {
		t.Error("ExportPublicKey() returned empty PEM")
	}

	// Verify PEM format
	if !containsString(string(publicKeyPEM), "BEGIN RSA PUBLIC KEY") {
		t.Error("ExportPublicKey() did not return valid PEM format")
	}
}

func TestKeyring_AddKeyPair(t *testing.T) {
	tmpDir := t.TempDir()
	keyring := NewKeyring(tmpDir)

	// Generate a key externally
	keyring2 := NewKeyring(t.TempDir())
	externalKey, err := keyring2.GenerateKeyPair("external")
	if err != nil {
		t.Fatalf("Failed to generate external key: %v", err)
	}

	// Add to first keyring
	keyID := "imported-key"
	err = keyring.AddKeyPair(keyID, externalKey.PrivateKey)
	if err != nil {
		t.Errorf("AddKeyPair() error = %v", err)
		return
	}

	// Verify key can be retrieved
	retrievedKey, err := keyring.GetKeyPair(keyID)
	if err != nil {
		t.Errorf("Failed to get added key: %v", err)
		return
	}

	// Verify it's the same key
	if retrievedKey.PrivateKey.N.Cmp(externalKey.PrivateKey.N) != 0 {
		t.Error("AddKeyPair() added different key")
	}
}

// Helper function
func containsString(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && contains(s, substr))
}

func contains(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// Benchmark tests
func BenchmarkGenerateKeyPair(b *testing.B) {
	tmpDir := b.TempDir()
	keyring := NewKeyring(tmpDir)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		keyID := filepath.Join("bench-key", string(rune(i)))
		_, err := keyring.GenerateKeyPair(keyID)
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkGetKeyPair(b *testing.B) {
	tmpDir := b.TempDir()
	keyring := NewKeyring(tmpDir)

	keyID := "bench-key"
	if _, err := keyring.GenerateKeyPair(keyID); err != nil {
		b.Fatal(err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := keyring.GetKeyPair(keyID)
		if err != nil {
			b.Fatal(err)
		}
	}
}
