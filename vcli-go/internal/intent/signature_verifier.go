// Package intent - Signature Verifier
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Handles cryptographic signatures for CRITICAL operations.
package intent

import (
	"crypto"
	"crypto/hmac"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"
)

// SignatureVerifier handles cryptographic signatures
//
// For CRITICAL operations (e.g., "delete namespace production"),
// we require the user to cryptographically sign the action.
// This prevents accidental execution and provides non-repudiation.
type SignatureVerifier struct {
	secretKey []byte
}

// NewSignatureVerifier creates a new signature verifier
func NewSignatureVerifier(secretKey []byte) *SignatureVerifier {
	return &SignatureVerifier{
		secretKey: secretKey,
	}
}

// Sign signs data using HMAC-SHA256
//
// For now, we use HMAC-SHA256 for simplicity.
// In production, we would support:
// - GPG signing: echo "message" | gpg --sign
// - SSH signing: echo "message" | ssh-keygen -Y sign
// - PKCS#11 hardware token
// - WebAuthn for browser-based
func (sv *SignatureVerifier) Sign(data []byte) (string, error) {
	if len(sv.secretKey) == 0 {
		return "", errors.New("no secret key configured")
	}

	mac := hmac.New(sha256.New, sv.secretKey)
	mac.Write(data)
	signature := mac.Sum(nil)

	return base64.StdEncoding.EncodeToString(signature), nil
}

// Verify verifies an HMAC-SHA256 signature
func (sv *SignatureVerifier) Verify(data []byte, signatureB64 string) (bool, error) {
	if len(sv.secretKey) == 0 {
		return false, errors.New("no secret key configured")
	}

	// Decode signature
	signature, err := base64.StdEncoding.DecodeString(signatureB64)
	if err != nil {
		return false, fmt.Errorf("invalid signature format: %w", err)
	}

	// Compute expected signature
	mac := hmac.New(sha256.New, sv.secretKey)
	mac.Write(data)
	expectedSignature := mac.Sum(nil)

	// Compare using constant-time comparison
	return hmac.Equal(signature, expectedSignature), nil
}

// GenerateKeyPair generates RSA key pair for user (helper function)
//
// This is provided as a utility for users who want to use
// RSA signing instead of HMAC.
func GenerateKeyPair() (*rsa.PrivateKey, *rsa.PublicKey, error) {
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, nil, err
	}

	return privateKey, &privateKey.PublicKey, nil
}

// SignWithRSA signs message with RSA private key
//
// This is an alternative to HMAC signing for users who
// prefer asymmetric cryptography.
func SignWithRSA(message string, privateKey *rsa.PrivateKey) (string, error) {
	hashed := sha256.Sum256([]byte(message))

	signature, err := rsa.SignPKCS1v15(rand.Reader, privateKey, crypto.SHA256, hashed[:])
	if err != nil {
		return "", err
	}

	return base64.StdEncoding.EncodeToString(signature), nil
}

// VerifyRSA verifies RSA signature
func VerifyRSA(message string, signatureB64 string, publicKey *rsa.PublicKey) error {
	signature, err := base64.StdEncoding.DecodeString(signatureB64)
	if err != nil {
		return err
	}

	hashed := sha256.Sum256([]byte(message))

	return rsa.VerifyPKCS1v15(publicKey, crypto.SHA256, hashed[:], signature)
}
