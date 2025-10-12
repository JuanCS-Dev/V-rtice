// Package auth - Device fingerprinting for trusted device tracking
//
// Device fingerprinting enables the Guardian to recognize returning devices
// and make context-aware authentication decisions (e.g., skip MFA for trusted devices).
//
// Security model: Defense in depth - device trust is one factor among many,
// never the sole determinant of authentication decisions.
package auth

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

// DeviceFingerprintGenerator creates unique device identifiers.
// Uses multiple signals to create collision-resistant fingerprints.
type DeviceFingerprintGenerator struct {
	// Stateless - pure functions only
}

// NewDeviceFingerprintGenerator creates a new device fingerprint generator.
func NewDeviceFingerprintGenerator() *DeviceFingerprintGenerator {
	return &DeviceFingerprintGenerator{}
}

// DeviceInfo contains information used to generate device fingerprint.
// Multiple signals are combined to create a unique identifier.
type DeviceInfo struct {
	// HTTP Headers
	UserAgent      string
	AcceptLanguage string
	AcceptEncoding string

	// Network
	IPAddress string

	// Browser/Client Fingerprinting
	ScreenResolution string
	Timezone         string
	Platform         string
	CPUCores         int
	DeviceMemory     int // MB

	// Advanced Fingerprinting (optional)
	Canvas string   // Canvas fingerprint
	WebGL  string   // WebGL fingerprint
	Fonts  []string // Installed fonts
}

// GenerateFingerprint creates a unique fingerprint for a device.
// Uses SHA-256 hash of combined signals for collision resistance.
//
// Returns: Hex-encoded SHA-256 hash (64 characters)
func (dfg *DeviceFingerprintGenerator) GenerateFingerprint(info *DeviceInfo) string {
	if info == nil {
		return ""
	}

	// Combine all available signals
	components := []string{
		info.UserAgent,
		info.IPAddress,
		info.AcceptLanguage,
		info.AcceptEncoding,
		info.ScreenResolution,
		info.Timezone,
		info.Platform,
		fmt.Sprintf("%d", info.CPUCores),
		fmt.Sprintf("%d", info.DeviceMemory),
		info.Canvas,
		info.WebGL,
		strings.Join(info.Fonts, ","),
	}

	// Join with pipe separator
	combined := strings.Join(components, "|")

	// SHA-256 hash for collision resistance
	hash := sha256.Sum256([]byte(combined))
	return hex.EncodeToString(hash[:])
}

// GenerateFingerprintQuick creates a fingerprint using only essential signals.
// Faster but less unique - use when full device info unavailable.
func (dfg *DeviceFingerprintGenerator) GenerateFingerprintQuick(userAgent, ipAddress string) string {
	if userAgent == "" && ipAddress == "" {
		return ""
	}

	combined := userAgent + "|" + ipAddress
	hash := sha256.Sum256([]byte(combined))
	return hex.EncodeToString(hash[:])
}

// TrustedDevice represents a device that has been verified and trusted.
// Tracks device history and trust level for context-aware authentication.
type TrustedDevice struct {
	// Identity
	DeviceID    string // Unique device identifier (generated)
	UserID      string // Owner of this device
	Fingerprint string // Device fingerprint hash

	// User-Friendly Info
	DeviceName string // User-assigned name (e.g., "Juan's MacBook Pro")
	DeviceType string // "desktop", "mobile", "tablet", "server"

	// Trust Level
	TrustLevel TrustLevel
	TrustedAt  time.Time // When explicitly verified (if TrustLevelVerified)

	// History
	FirstSeen time.Time
	LastSeen  time.Time

	// Behavioral History (for anomaly detection)
	IPAddresses []string       // Historical IPs seen from this device
	UserAgents  []string       // Historical user agents
	Locations   []*GeoLocation // Historical locations
	SeenCount   int            // Number of times device seen

	// Security
	Revoked   bool      // If device trust has been revoked
	RevokedAt time.Time // When revoked
}

// TrustLevel represents how much we trust a device.
// Trust escalates over time and frequency of use.
type TrustLevel string

const (
	// TrustLevelUnknown - Never seen before
	TrustLevelUnknown TrustLevel = "unknown"

	// TrustLevelLow - Seen once
	TrustLevelLow TrustLevel = "low"

	// TrustLevelMedium - Seen 2-5 times over multiple days
	TrustLevelMedium TrustLevel = "medium"

	// TrustLevelHigh - Seen 6+ times over 7+ days, no anomalies
	TrustLevelHigh TrustLevel = "high"

	// TrustLevelVerified - Explicitly verified by user (highest trust)
	TrustLevelVerified TrustLevel = "verified"
)

// DeviceTrustStore manages trusted devices.
// In-memory storage for v1.0 (will add persistence later).
type DeviceTrustStore struct {
	devices map[string]*TrustedDevice // fingerprint -> device
}

// NewDeviceTrustStore creates a new device trust store.
func NewDeviceTrustStore() *DeviceTrustStore {
	return &DeviceTrustStore{
		devices: make(map[string]*TrustedDevice),
	}
}

// GetDevice retrieves a trusted device by fingerprint.
// Returns device and whether it exists.
func (dts *DeviceTrustStore) GetDevice(fingerprint string) (*TrustedDevice, bool) {
	device, exists := dts.devices[fingerprint]
	if exists && device.Revoked {
		return nil, false // Treat revoked devices as non-existent
	}
	return device, exists
}

// AddOrUpdateDevice adds a new device or updates last seen time.
// Automatically escalates trust level based on frequency and time.
func (dts *DeviceTrustStore) AddOrUpdateDevice(userID, fingerprint, deviceName string, info *DeviceInfo) *TrustedDevice {
	device, exists := dts.devices[fingerprint]

	now := time.Now()

	if !exists {
		// New device
		device = &TrustedDevice{
			DeviceID:    generateDeviceID(),
			UserID:      userID,
			Fingerprint: fingerprint,
			DeviceName:  deviceName,
			FirstSeen:   now,
			LastSeen:    now,
			TrustLevel:  TrustLevelLow,
			SeenCount:   1,
			IPAddresses: []string{},
			UserAgents:  []string{},
			Locations:   []*GeoLocation{},
		}

		if info != nil {
			if info.IPAddress != "" {
				device.IPAddresses = append(device.IPAddresses, info.IPAddress)
			}
			if info.UserAgent != "" {
				device.UserAgents = append(device.UserAgents, info.UserAgent)
			}
		}

		dts.devices[fingerprint] = device
	} else {
		// Update existing device
		device.LastSeen = now
		device.SeenCount++

		// Add new IP if not seen before
		if info != nil && info.IPAddress != "" {
			if !contains(device.IPAddresses, info.IPAddress) {
				device.IPAddresses = append(device.IPAddresses, info.IPAddress)
			}

			// Add new user agent if not seen before
			if info.UserAgent != "" && !contains(device.UserAgents, info.UserAgent) {
				device.UserAgents = append(device.UserAgents, info.UserAgent)
			}
		}

		// Escalate trust level based on frequency and time (if not manually verified)
		if device.TrustLevel != TrustLevelVerified {
			timeSinceFirst := now.Sub(device.FirstSeen)

			if device.SeenCount >= 6 && timeSinceFirst > 7*24*time.Hour {
				// Seen 6+ times over 7+ days
				device.TrustLevel = TrustLevelHigh
			} else if device.SeenCount >= 2 && timeSinceFirst > 24*time.Hour {
				// Seen 2+ times over 1+ day
				device.TrustLevel = TrustLevelMedium
			}
		}
	}

	return device
}

// VerifyDevice explicitly marks a device as verified (highest trust).
// Use when user explicitly confirms device (e.g., "Remember this device").
func (dts *DeviceTrustStore) VerifyDevice(fingerprint string) error {
	device, exists := dts.devices[fingerprint]
	if !exists {
		return fmt.Errorf("device not found: %s", fingerprint)
	}

	device.TrustLevel = TrustLevelVerified
	device.TrustedAt = time.Now()

	return nil
}

// RevokeDevice removes trust from a device.
// Marks device as revoked rather than deleting for audit trail.
func (dts *DeviceTrustStore) RevokeDevice(fingerprint string) error {
	device, exists := dts.devices[fingerprint]
	if !exists {
		return fmt.Errorf("device not found: %s", fingerprint)
	}

	device.Revoked = true
	device.RevokedAt = time.Now()

	return nil
}

// DeleteDevice permanently removes a device from the store.
// Use with caution - prefer RevokeDevice for audit trail.
func (dts *DeviceTrustStore) DeleteDevice(fingerprint string) error {
	delete(dts.devices, fingerprint)
	return nil
}

// ListUserDevices returns all devices for a user.
// Excludes revoked devices by default.
func (dts *DeviceTrustStore) ListUserDevices(userID string) []*TrustedDevice {
	devices := []*TrustedDevice{}
	for _, device := range dts.devices {
		if device.UserID == userID && !device.Revoked {
			devices = append(devices, device)
		}
	}
	return devices
}

// ListAllUserDevices returns all devices for a user, including revoked.
// Use for audit purposes.
func (dts *DeviceTrustStore) ListAllUserDevices(userID string) []*TrustedDevice {
	devices := []*TrustedDevice{}
	for _, device := range dts.devices {
		if device.UserID == userID {
			devices = append(devices, device)
		}
	}
	return devices
}

// GetDeviceByID retrieves a device by its unique ID (not fingerprint).
func (dts *DeviceTrustStore) GetDeviceByID(deviceID string) (*TrustedDevice, bool) {
	for _, device := range dts.devices {
		if device.DeviceID == deviceID {
			return device, true
		}
	}
	return nil, false
}

// CountDevices returns the total number of devices in the store.
func (dts *DeviceTrustStore) CountDevices() int {
	return len(dts.devices)
}

// CountUserDevices returns the number of devices for a specific user.
func (dts *DeviceTrustStore) CountUserDevices(userID string) int {
	count := 0
	for _, device := range dts.devices {
		if device.UserID == userID && !device.Revoked {
			count++
		}
	}
	return count
}

// CleanupStaleDevices removes devices not seen in the specified duration.
// Use for periodic cleanup of abandoned devices.
func (dts *DeviceTrustStore) CleanupStaleDevices(maxAge time.Duration) int {
	threshold := time.Now().Add(-maxAge)
	removed := 0

	for fingerprint, device := range dts.devices {
		if device.LastSeen.Before(threshold) {
			delete(dts.devices, fingerprint)
			removed++
		}
	}

	return removed
}

// Helper functions

// generateDeviceID creates a unique device identifier.
func generateDeviceID() string {
	bytes := make([]byte, 16)
	_, _ = rand.Read(bytes)
	return hex.EncodeToString(bytes)
}

// contains checks if a string slice contains a specific string.
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// IsHighTrust checks if device has high or verified trust level.
func (td *TrustedDevice) IsHighTrust() bool {
	return td.TrustLevel == TrustLevelHigh || td.TrustLevel == TrustLevelVerified
}

// IsTrusted checks if device has at least medium trust level.
func (td *TrustedDevice) IsTrusted() bool {
	return td.TrustLevel == TrustLevelMedium ||
		td.TrustLevel == TrustLevelHigh ||
		td.TrustLevel == TrustLevelVerified
}

// DaysSinceFirstSeen returns how many days since device was first seen.
func (td *TrustedDevice) DaysSinceFirstSeen() int {
	return int(time.Since(td.FirstSeen).Hours() / 24)
}

// DaysSinceLastSeen returns how many days since device was last seen.
func (td *TrustedDevice) DaysSinceLastSeen() int {
	return int(time.Since(td.LastSeen).Hours() / 24)
}

// String returns a safe string representation of TrustedDevice.
func (td *TrustedDevice) String() string {
	return fmt.Sprintf("TrustedDevice{DeviceID:%s, UserID:%s, TrustLevel:%s, SeenCount:%d}",
		td.DeviceID, td.UserID, td.TrustLevel, td.SeenCount)
}
