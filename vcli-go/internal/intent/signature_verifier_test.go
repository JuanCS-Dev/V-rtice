// Package intent - Signature Verifier Tests
package intent

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSignatureVerifier_Sign_Verify(t *testing.T) {
	secretKey := []byte("test-secret-key-123")
	verifier := NewSignatureVerifier(secretKey)

	data := []byte("delete namespace production")

	// Sign data
	signature, err := verifier.Sign(data)
	require.NoError(t, err)
	assert.NotEmpty(t, signature)

	// Verify signature
	valid, err := verifier.Verify(data, signature)
	require.NoError(t, err)
	assert.True(t, valid, "Signature should be valid")
}

func TestSignatureVerifier_Verify_InvalidSignature(t *testing.T) {
	secretKey := []byte("test-secret-key-123")
	verifier := NewSignatureVerifier(secretKey)

	data := []byte("delete namespace production")

	// Create fake signature
	fakeSignature := "fake-signature-xyz"

	// Verify should fail
	valid, err := verifier.Verify(data, fakeSignature)
	require.Error(t, err)
	assert.False(t, valid, "Fake signature should not be valid")
}

func TestSignatureVerifier_Verify_WrongData(t *testing.T) {
	secretKey := []byte("test-secret-key-123")
	verifier := NewSignatureVerifier(secretKey)

	originalData := []byte("delete namespace production")
	tamperedData := []byte("delete namespace development")

	// Sign original data
	signature, err := verifier.Sign(originalData)
	require.NoError(t, err)

	// Verify with tampered data should fail
	valid, err := verifier.Verify(tamperedData, signature)
	require.NoError(t, err)
	assert.False(t, valid, "Signature should not match tampered data")
}

func TestSignatureVerifier_NoSecretKey(t *testing.T) {
	verifier := NewSignatureVerifier(nil)

	data := []byte("test data")

	// Sign should fail without key
	_, err := verifier.Sign(data)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "no secret key")

	// Verify should fail without key
	_, err = verifier.Verify(data, "some-signature")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "no secret key")
}

func TestSignatureVerifier_DifferentKeys(t *testing.T) {
	verifier1 := NewSignatureVerifier([]byte("key-1"))
	verifier2 := NewSignatureVerifier([]byte("key-2"))

	data := []byte("test data")

	// Sign with verifier1
	signature, err := verifier1.Sign(data)
	require.NoError(t, err)

	// Verify with verifier2 should fail
	valid, err := verifier2.Verify(data, signature)
	require.NoError(t, err)
	assert.False(t, valid, "Signature from different key should not be valid")
}

func TestGenerateKeyPair(t *testing.T) {
	privateKey, publicKey, err := GenerateKeyPair()
	require.NoError(t, err)
	require.NotNil(t, privateKey)
	require.NotNil(t, publicKey)

	// Check key size
	assert.Equal(t, 2048, privateKey.N.BitLen())
}

func TestSignWithRSA_VerifyRSA(t *testing.T) {
	privateKey, publicKey, err := GenerateKeyPair()
	require.NoError(t, err)

	message := "delete namespace production"

	// Sign with RSA
	signature, err := SignWithRSA(message, privateKey)
	require.NoError(t, err)
	assert.NotEmpty(t, signature)

	// Verify with RSA
	err = VerifyRSA(message, signature, publicKey)
	assert.NoError(t, err, "RSA signature should be valid")
}

func TestSignWithRSA_VerifyRSA_TamperedMessage(t *testing.T) {
	privateKey, publicKey, err := GenerateKeyPair()
	require.NoError(t, err)

	originalMessage := "delete namespace production"
	tamperedMessage := "delete namespace development"

	// Sign original message
	signature, err := SignWithRSA(originalMessage, privateKey)
	require.NoError(t, err)

	// Verify with tampered message should fail
	err = VerifyRSA(tamperedMessage, signature, publicKey)
	assert.Error(t, err, "RSA verification should fail for tampered message")
}

func TestSignWithRSA_VerifyRSA_WrongPublicKey(t *testing.T) {
	privateKey1, _, err := GenerateKeyPair()
	require.NoError(t, err)

	_, publicKey2, err := GenerateKeyPair()
	require.NoError(t, err)

	message := "test message"

	// Sign with privateKey1
	signature, err := SignWithRSA(message, privateKey1)
	require.NoError(t, err)

	// Verify with publicKey2 should fail
	err = VerifyRSA(message, signature, publicKey2)
	assert.Error(t, err, "RSA verification should fail with wrong public key")
}
