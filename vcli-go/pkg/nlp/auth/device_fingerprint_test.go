package auth

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Test Suite 1: Fingerprint Generation
func TestGenerateFingerprint(t *testing.T) {
	gen := NewDeviceFingerprintGenerator()

	t.Run("Same device info produces same fingerprint", func(t *testing.T) {
		info := &DeviceInfo{
			UserAgent:        "Mozilla/5.0",
			IPAddress:        "192.168.1.100",
			AcceptLanguage:   "en-US",
			ScreenResolution: "1920x1080",
			Timezone:         "America/New_York",
			Platform:         "MacIntel",
			CPUCores:         8,
			DeviceMemory:     16000,
		}

		fp1 := gen.GenerateFingerprint(info)
		fp2 := gen.GenerateFingerprint(info)

		assert.Equal(t, fp1, fp2, "Same device info should produce same fingerprint")
		assert.NotEmpty(t, fp1, "Fingerprint should not be empty")
		assert.Equal(t, 64, len(fp1), "SHA-256 fingerprint should be 64 hex characters")
	})

	t.Run("Different device info produces different fingerprint", func(t *testing.T) {
		info1 := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		info2 := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.101", // Different IP
		}

		fp1 := gen.GenerateFingerprint(info1)
		fp2 := gen.GenerateFingerprint(info2)

		assert.NotEqual(t, fp1, fp2, "Different device info should produce different fingerprints")
	})

	t.Run("Nil device info returns empty fingerprint", func(t *testing.T) {
		fp := gen.GenerateFingerprint(nil)
		assert.Empty(t, fp, "Nil device info should return empty fingerprint")
	})

	t.Run("Collision resistance", func(t *testing.T) {
		// Generate fingerprints for multiple devices
		fingerprints := make(map[string]bool)

		for i := 0; i < 100; i++ {
			info := &DeviceInfo{
				UserAgent: "Mozilla/5.0",
				IPAddress: "192.168.1." + string(rune(i)),
			}
			fp := gen.GenerateFingerprint(info)
			assert.False(t, fingerprints[fp], "Collision detected")
			fingerprints[fp] = true
		}
	})
}

func TestGenerateFingerprintQuick(t *testing.T) {
	gen := NewDeviceFingerprintGenerator()

	t.Run("Quick fingerprint generation", func(t *testing.T) {
		fp := gen.GenerateFingerprintQuick("Mozilla/5.0", "192.168.1.100")

		assert.NotEmpty(t, fp)
		assert.Equal(t, 64, len(fp))
	})

	t.Run("Same inputs produce same quick fingerprint", func(t *testing.T) {
		fp1 := gen.GenerateFingerprintQuick("Mozilla/5.0", "192.168.1.100")
		fp2 := gen.GenerateFingerprintQuick("Mozilla/5.0", "192.168.1.100")

		assert.Equal(t, fp1, fp2)
	})

	t.Run("Empty inputs return empty fingerprint", func(t *testing.T) {
		fp := gen.GenerateFingerprintQuick("", "")
		assert.Empty(t, fp)
	})
}

// Test Suite 2: Device Trust Store
func TestDeviceTrustStore(t *testing.T) {
	t.Run("Add new device", func(t *testing.T) {
		store := NewDeviceTrustStore()
		info := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		device := store.AddOrUpdateDevice("user123", "fingerprint-abc", "My Laptop", info)

		assert.NotNil(t, device)
		assert.Equal(t, "user123", device.UserID)
		assert.Equal(t, "fingerprint-abc", device.Fingerprint)
		assert.Equal(t, "My Laptop", device.DeviceName)
		assert.Equal(t, TrustLevelLow, device.TrustLevel)
		assert.Equal(t, 1, device.SeenCount)
		assert.Contains(t, device.IPAddresses, "192.168.1.100")
	})

	t.Run("Update existing device", func(t *testing.T) {
		store := NewDeviceTrustStore()
		info := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		// Add device
		device1 := store.AddOrUpdateDevice("user123", "fingerprint-abc", "My Laptop", info)
		firstSeen := device1.FirstSeen

		time.Sleep(10 * time.Millisecond)

		// Update device
		device2 := store.AddOrUpdateDevice("user123", "fingerprint-abc", "My Laptop", info)

		assert.Equal(t, firstSeen, device2.FirstSeen, "FirstSeen should not change")
		assert.True(t, device2.LastSeen.After(firstSeen), "LastSeen should be updated")
		assert.Equal(t, 2, device2.SeenCount, "SeenCount should increment")
	})

	t.Run("Get device", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fingerprint-abc", "My Laptop", nil)

		device, exists := store.GetDevice("fingerprint-abc")

		assert.True(t, exists)
		assert.NotNil(t, device)
		assert.Equal(t, "fingerprint-abc", device.Fingerprint)
	})

	t.Run("Get non-existent device", func(t *testing.T) {
		store := NewDeviceTrustStore()

		device, exists := store.GetDevice("non-existent")

		assert.False(t, exists)
		assert.Nil(t, device)
	})
}

// Test Suite 3: Trust Levels
func TestTrustLevels(t *testing.T) {
	t.Run("New device has low trust", func(t *testing.T) {
		store := NewDeviceTrustStore()
		device := store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		assert.Equal(t, TrustLevelLow, device.TrustLevel)
		assert.False(t, device.IsHighTrust())
		assert.False(t, device.IsTrusted())
	})

	t.Run("Trust escalation to medium", func(t *testing.T) {
		store := NewDeviceTrustStore()

		// Add device (seen 1st time)
		device := store.AddOrUpdateDevice("user123", "fp1", "Device", nil)
		assert.Equal(t, TrustLevelLow, device.TrustLevel)

		// Manually adjust FirstSeen to simulate 1+ day ago
		device.FirstSeen = time.Now().Add(-25 * time.Hour)

		// Update device (seen 2nd time)
		device = store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		assert.Equal(t, TrustLevelMedium, device.TrustLevel)
		assert.True(t, device.IsTrusted())
		assert.False(t, device.IsHighTrust())
	})

	t.Run("Trust escalation to high", func(t *testing.T) {
		store := NewDeviceTrustStore()

		// Add device
		device := store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		// Manually adjust to simulate 7+ days ago and 6+ visits
		device.FirstSeen = time.Now().Add(-8 * 24 * time.Hour)
		device.SeenCount = 5 // Will become 6 on next update

		// Update device
		device = store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		assert.Equal(t, TrustLevelHigh, device.TrustLevel)
		assert.True(t, device.IsHighTrust())
		assert.True(t, device.IsTrusted())
	})

	t.Run("Verified trust level", func(t *testing.T) {
		store := NewDeviceTrustStore()
		device := store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		err := store.VerifyDevice("fp1")
		require.NoError(t, err)

		assert.Equal(t, TrustLevelVerified, device.TrustLevel)
		assert.True(t, device.IsHighTrust())
		assert.False(t, device.TrustedAt.IsZero())
	})

	t.Run("Verified trust does not downgrade", func(t *testing.T) {
		store := NewDeviceTrustStore()
		device := store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		// Verify device
		store.VerifyDevice("fp1")
		assert.Equal(t, TrustLevelVerified, device.TrustLevel)

		// Update device (should remain verified)
		device = store.AddOrUpdateDevice("user123", "fp1", "Device", nil)
		assert.Equal(t, TrustLevelVerified, device.TrustLevel)
	})
}

// Test Suite 4: Device Verification
func TestVerifyDevice(t *testing.T) {
	t.Run("Verify existing device", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		err := store.VerifyDevice("fp1")

		require.NoError(t, err)

		device, _ := store.GetDevice("fp1")
		assert.Equal(t, TrustLevelVerified, device.TrustLevel)
	})

	t.Run("Verify non-existent device", func(t *testing.T) {
		store := NewDeviceTrustStore()

		err := store.VerifyDevice("non-existent")

		assert.Error(t, err)
		assert.Contains(t, err.Error(), "device not found")
	})
}

// Test Suite 5: Device Revocation
func TestRevokeDevice(t *testing.T) {
	t.Run("Revoke existing device", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		err := store.RevokeDevice("fp1")
		require.NoError(t, err)

		// Revoked devices should not be retrievable
		device, exists := store.GetDevice("fp1")
		assert.False(t, exists)
		assert.Nil(t, device)
	})

	t.Run("Revoke non-existent device", func(t *testing.T) {
		store := NewDeviceTrustStore()

		err := store.RevokeDevice("non-existent")

		assert.Error(t, err)
	})

	t.Run("Revoked device has timestamp", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		store.RevokeDevice("fp1")

		// Access revoked device directly from map
		device := store.devices["fp1"]
		assert.True(t, device.Revoked)
		assert.False(t, device.RevokedAt.IsZero())
	})
}

// Test Suite 6: Device Deletion
func TestDeleteDevice(t *testing.T) {
	t.Run("Delete existing device", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		err := store.DeleteDevice("fp1")
		require.NoError(t, err)

		device, exists := store.GetDevice("fp1")
		assert.False(t, exists)
		assert.Nil(t, device)
	})

	t.Run("Delete non-existent device", func(t *testing.T) {
		store := NewDeviceTrustStore()

		err := store.DeleteDevice("non-existent")
		require.NoError(t, err) // Should not error
	})
}

// Test Suite 7: List Devices
func TestListUserDevices(t *testing.T) {
	t.Run("List devices for user", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device 1", nil)
		store.AddOrUpdateDevice("user123", "fp2", "Device 2", nil)
		store.AddOrUpdateDevice("user456", "fp3", "Device 3", nil)

		devices := store.ListUserDevices("user123")

		assert.Len(t, devices, 2)
	})

	t.Run("List devices excludes revoked", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device 1", nil)
		store.AddOrUpdateDevice("user123", "fp2", "Device 2", nil)

		store.RevokeDevice("fp1")

		devices := store.ListUserDevices("user123")
		assert.Len(t, devices, 1)
	})

	t.Run("List all devices includes revoked", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device 1", nil)
		store.AddOrUpdateDevice("user123", "fp2", "Device 2", nil)

		store.RevokeDevice("fp1")

		devices := store.ListAllUserDevices("user123")
		assert.Len(t, devices, 2)
	})
}

// Test Suite 8: Device Lookup
func TestGetDeviceByID(t *testing.T) {
	t.Run("Get device by ID", func(t *testing.T) {
		store := NewDeviceTrustStore()
		device1 := store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		device2, exists := store.GetDeviceByID(device1.DeviceID)

		assert.True(t, exists)
		assert.Equal(t, device1.DeviceID, device2.DeviceID)
	})

	t.Run("Get non-existent device by ID", func(t *testing.T) {
		store := NewDeviceTrustStore()

		device, exists := store.GetDeviceByID("non-existent")

		assert.False(t, exists)
		assert.Nil(t, device)
	})
}

// Test Suite 9: Device Counts
func TestCountDevices(t *testing.T) {
	t.Run("Count total devices", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device 1", nil)
		store.AddOrUpdateDevice("user456", "fp2", "Device 2", nil)

		count := store.CountDevices()
		assert.Equal(t, 2, count)
	})

	t.Run("Count user devices", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device 1", nil)
		store.AddOrUpdateDevice("user123", "fp2", "Device 2", nil)
		store.AddOrUpdateDevice("user456", "fp3", "Device 3", nil)

		count := store.CountUserDevices("user123")
		assert.Equal(t, 2, count)
	})

	t.Run("Count user devices excludes revoked", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device 1", nil)
		store.AddOrUpdateDevice("user123", "fp2", "Device 2", nil)

		store.RevokeDevice("fp1")

		count := store.CountUserDevices("user123")
		assert.Equal(t, 1, count)
	})
}

// Test Suite 10: Cleanup
func TestCleanupStaleDevices(t *testing.T) {
	t.Run("Cleanup stale devices", func(t *testing.T) {
		store := NewDeviceTrustStore()

		// Add devices with old LastSeen
		device1 := store.AddOrUpdateDevice("user123", "fp1", "Old Device", nil)
		device1.LastSeen = time.Now().Add(-40 * 24 * time.Hour) // 40 days ago

		// Add recent device
		store.AddOrUpdateDevice("user123", "fp2", "Recent Device", nil)

		removed := store.CleanupStaleDevices(30 * 24 * time.Hour)

		assert.Equal(t, 1, removed)
		assert.Equal(t, 1, store.CountDevices())
	})

	t.Run("Cleanup with no stale devices", func(t *testing.T) {
		store := NewDeviceTrustStore()
		store.AddOrUpdateDevice("user123", "fp1", "Device", nil)

		removed := store.CleanupStaleDevices(30 * 24 * time.Hour)

		assert.Equal(t, 0, removed)
		assert.Equal(t, 1, store.CountDevices())
	})
}

// Test Suite 11: IP and User Agent Tracking
func TestIPAndUserAgentTracking(t *testing.T) {
	t.Run("Track multiple IPs", func(t *testing.T) {
		store := NewDeviceTrustStore()

		info1 := &DeviceInfo{IPAddress: "192.168.1.100"}
		store.AddOrUpdateDevice("user123", "fp1", "Device", info1)

		info2 := &DeviceInfo{IPAddress: "192.168.1.101"}
		store.AddOrUpdateDevice("user123", "fp1", "Device", info2)

		device, _ := store.GetDevice("fp1")
		assert.Len(t, device.IPAddresses, 2)
		assert.Contains(t, device.IPAddresses, "192.168.1.100")
		assert.Contains(t, device.IPAddresses, "192.168.1.101")
	})

	t.Run("Do not duplicate IPs", func(t *testing.T) {
		store := NewDeviceTrustStore()

		info := &DeviceInfo{IPAddress: "192.168.1.100"}
		store.AddOrUpdateDevice("user123", "fp1", "Device", info)
		store.AddOrUpdateDevice("user123", "fp1", "Device", info)

		device, _ := store.GetDevice("fp1")
		assert.Len(t, device.IPAddresses, 1)
	})

	t.Run("Track multiple user agents", func(t *testing.T) {
		store := NewDeviceTrustStore()

		info1 := &DeviceInfo{UserAgent: "Mozilla/5.0"}
		store.AddOrUpdateDevice("user123", "fp1", "Device", info1)

		info2 := &DeviceInfo{UserAgent: "Chrome/95.0"}
		store.AddOrUpdateDevice("user123", "fp1", "Device", info2)

		device, _ := store.GetDevice("fp1")
		assert.Len(t, device.UserAgents, 2)
	})
}

// Test Suite 12: Device Helper Methods
func TestDeviceHelperMethods(t *testing.T) {
	t.Run("IsHighTrust", func(t *testing.T) {
		device := &TrustedDevice{TrustLevel: TrustLevelHigh}
		assert.True(t, device.IsHighTrust())

		device.TrustLevel = TrustLevelVerified
		assert.True(t, device.IsHighTrust())

		device.TrustLevel = TrustLevelMedium
		assert.False(t, device.IsHighTrust())
	})

	t.Run("IsTrusted", func(t *testing.T) {
		device := &TrustedDevice{TrustLevel: TrustLevelMedium}
		assert.True(t, device.IsTrusted())

		device.TrustLevel = TrustLevelHigh
		assert.True(t, device.IsTrusted())

		device.TrustLevel = TrustLevelVerified
		assert.True(t, device.IsTrusted())

		device.TrustLevel = TrustLevelLow
		assert.False(t, device.IsTrusted())

		device.TrustLevel = TrustLevelUnknown
		assert.False(t, device.IsTrusted())
	})

	t.Run("DaysSinceFirstSeen", func(t *testing.T) {
		device := &TrustedDevice{
			FirstSeen: time.Now().Add(-48 * time.Hour),
		}

		days := device.DaysSinceFirstSeen()
		assert.Equal(t, 2, days)
	})

	t.Run("DaysSinceLastSeen", func(t *testing.T) {
		device := &TrustedDevice{
			LastSeen: time.Now().Add(-24 * time.Hour),
		}

		days := device.DaysSinceLastSeen()
		assert.Equal(t, 1, days)
	})

	t.Run("String representation", func(t *testing.T) {
		device := &TrustedDevice{
			DeviceID:   "device-123",
			UserID:     "user-456",
			TrustLevel: TrustLevelHigh,
			SeenCount:  5,
		}

		str := device.String()
		assert.Contains(t, str, "device-123")
		assert.Contains(t, str, "user-456")
		assert.Contains(t, str, "high")
	})
}

// Benchmarks
func BenchmarkGenerateFingerprint(b *testing.B) {
	gen := NewDeviceFingerprintGenerator()
	info := &DeviceInfo{
		UserAgent:        "Mozilla/5.0",
		IPAddress:        "192.168.1.100",
		AcceptLanguage:   "en-US",
		ScreenResolution: "1920x1080",
		Timezone:         "America/New_York",
		Platform:         "MacIntel",
		CPUCores:         8,
		DeviceMemory:     16000,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = gen.GenerateFingerprint(info)
	}
}

func BenchmarkGenerateFingerprintQuick(b *testing.B) {
	gen := NewDeviceFingerprintGenerator()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = gen.GenerateFingerprintQuick("Mozilla/5.0", "192.168.1.100")
	}
}

func BenchmarkAddOrUpdateDevice(b *testing.B) {
	store := NewDeviceTrustStore()
	info := &DeviceInfo{
		UserAgent: "Mozilla/5.0",
		IPAddress: "192.168.1.100",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = store.AddOrUpdateDevice("user123", "fingerprint", "Device", info)
	}
}

func BenchmarkGetDevice(b *testing.B) {
	store := NewDeviceTrustStore()
	store.AddOrUpdateDevice("user123", "fingerprint", "Device", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = store.GetDevice("fingerprint")
	}
}
