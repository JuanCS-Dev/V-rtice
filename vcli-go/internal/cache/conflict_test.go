package cache

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewConflictResolver verifies resolver creation
func TestNewConflictResolver(t *testing.T) {
	resolver := NewConflictResolver(StrategyServerWins)
	assert.NotNil(t, resolver)
	assert.Equal(t, StrategyServerWins, resolver.strategy)
}

// TestResolve_ServerWins verifies server wins strategy
func TestResolve_ServerWins(t *testing.T) {
	resolver := NewConflictResolver(StrategyServerWins)

	conflict := &Conflict{
		Key:        "test:key",
		ServerData: "server data",
		ClientData: "client data",
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)
	assert.Equal(t, "server data", conflict.ResolvedData)
	assert.Equal(t, "server_wins", conflict.Resolution)
}

// TestResolve_ClientWins verifies client wins strategy
func TestResolve_ClientWins(t *testing.T) {
	resolver := NewConflictResolver(StrategyClientWins)

	conflict := &Conflict{
		Key:        "test:key",
		ServerData: "server data",
		ClientData: "client data",
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)
	assert.Equal(t, "client data", conflict.ResolvedData)
	assert.Equal(t, "client_wins", conflict.Resolution)
}

// TestResolve_Newest_ServerNewer verifies newest strategy when server is newer
func TestResolve_Newest_ServerNewer(t *testing.T) {
	resolver := NewConflictResolver(StrategyNewest)

	now := time.Now()
	conflict := &Conflict{
		Key:           "test:key",
		ServerData:    "server data",
		ClientData:    "client data",
		ServerModTime: now.Add(1 * time.Hour),
		ClientModTime: now,
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)
	assert.Equal(t, "server data", conflict.ResolvedData)
	assert.Equal(t, "server_newer", conflict.Resolution)
}

// TestResolve_Newest_ClientNewer verifies newest strategy when client is newer
func TestResolve_Newest_ClientNewer(t *testing.T) {
	resolver := NewConflictResolver(StrategyNewest)

	now := time.Now()
	conflict := &Conflict{
		Key:           "test:key",
		ServerData:    "server data",
		ClientData:    "client data",
		ServerModTime: now,
		ClientModTime: now.Add(1 * time.Hour),
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)
	assert.Equal(t, "client data", conflict.ResolvedData)
	assert.Equal(t, "client_newer", conflict.Resolution)
}

// TestResolve_Merge_BothMaps verifies merge strategy with maps
func TestResolve_Merge_BothMaps(t *testing.T) {
	resolver := NewConflictResolver(StrategyMerge)

	conflict := &Conflict{
		Key: "test:key",
		ServerData: map[string]interface{}{
			"key1": "server1",
			"key2": "server2",
		},
		ClientData: map[string]interface{}{
			"key2": "client2", // Conflicts with server
			"key3": "client3",
		},
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)

	merged, ok := conflict.ResolvedData.(map[string]interface{})
	require.True(t, ok)

	// Server key1 should be included
	assert.Equal(t, "server1", merged["key1"])
	// Client should win on key2 conflict
	assert.Equal(t, "client2", merged["key2"])
	// Client key3 should be included
	assert.Equal(t, "client3", merged["key3"])

	assert.Equal(t, "merged", conflict.Resolution)
}

// TestResolve_Merge_NonMaps verifies merge fallback to newest
func TestResolve_Merge_NonMaps(t *testing.T) {
	resolver := NewConflictResolver(StrategyMerge)

	now := time.Now()
	conflict := &Conflict{
		Key:           "test:key",
		ServerData:    "server string",
		ClientData:    "client string",
		ServerModTime: now.Add(1 * time.Hour),
		ClientModTime: now,
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)

	// Should fall back to newest (server is newer)
	assert.Equal(t, "server string", conflict.ResolvedData)
	assert.Equal(t, "server_newer", conflict.Resolution)
}

// TestResolve_UnknownStrategy verifies error on unknown strategy
func TestResolve_UnknownStrategy(t *testing.T) {
	resolver := &ConflictResolver{strategy: ConflictStrategy(999)}

	conflict := &Conflict{
		Key:        "test:key",
		ServerData: "data",
		ClientData: "data",
	}

	err := resolver.Resolve(conflict)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "unknown conflict strategy")
}

// TestDetectConflict_NoConflict verifies no conflict when data matches
func TestDetectConflict_NoConflict(t *testing.T) {
	sameData := map[string]interface{}{
		"key": "value",
	}

	conflict, err := DetectConflict("test:key", sameData, sameData, time.Now(), time.Now())
	require.NoError(t, err)
	assert.Nil(t, conflict, "Should return nil when data matches")
}

// TestDetectConflict_Conflict verifies conflict detection
func TestDetectConflict_Conflict(t *testing.T) {
	serverData := map[string]interface{}{
		"key": "server value",
	}
	clientData := map[string]interface{}{
		"key": "client value",
	}

	now := time.Now()
	conflict, err := DetectConflict("test:key", serverData, clientData, now, now.Add(1*time.Hour))
	require.NoError(t, err)
	require.NotNil(t, conflict)

	assert.Equal(t, "test:key", conflict.Key)
	assert.NotEqual(t, conflict.ServerHash, conflict.ClientHash)
	assert.Equal(t, serverData, conflict.ServerData)
	assert.Equal(t, clientData, conflict.ClientData)
}

// TestHashData_Consistent verifies hash consistency
func TestHashData_Consistent(t *testing.T) {
	data := map[string]interface{}{
		"key1": "value1",
		"key2": 42,
	}

	hash1, err1 := hashData(data)
	hash2, err2 := hashData(data)

	require.NoError(t, err1)
	require.NoError(t, err2)
	assert.Equal(t, hash1, hash2, "Same data should produce same hash")
}

// TestHashData_Different verifies different data produces different hashes
func TestHashData_Different(t *testing.T) {
	data1 := map[string]interface{}{"key": "value1"}
	data2 := map[string]interface{}{"key": "value2"}

	hash1, err1 := hashData(data1)
	hash2, err2 := hashData(data2)

	require.NoError(t, err1)
	require.NoError(t, err2)
	assert.NotEqual(t, hash1, hash2, "Different data should produce different hashes")
}

// TestNewDifferentialSync verifies differential sync creation
func TestNewDifferentialSync(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	sync := NewDifferentialSync(cache)
	assert.NotNil(t, sync)
	assert.NotNil(t, sync.cache)
	assert.NotZero(t, sync.lastSync)
	assert.Empty(t, sync.changes)
}

// TestDifferentialSync_TrackChange verifies change tracking
func TestDifferentialSync_TrackChange(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	sync := NewDifferentialSync(cache)

	sync.TrackChange("key1", "set", map[string]interface{}{"data": "value1"})
	sync.TrackChange("key2", "delete", nil)

	changes := sync.GetChanges()
	assert.Len(t, changes, 2)

	assert.Equal(t, "key1", changes[0].Key)
	assert.Equal(t, "set", changes[0].Operation)
	assert.NotNil(t, changes[0].Data)

	assert.Equal(t, "key2", changes[1].Key)
	assert.Equal(t, "delete", changes[1].Operation)
	assert.Nil(t, changes[1].Data)
}

// TestDifferentialSync_GetChanges verifies retrieving changes
func TestDifferentialSync_GetChanges(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	sync := NewDifferentialSync(cache)

	// Initially empty
	changes := sync.GetChanges()
	assert.Empty(t, changes)

	// Add changes
	sync.TrackChange("key1", "set", "value1")
	sync.TrackChange("key2", "set", "value2")

	changes = sync.GetChanges()
	assert.Len(t, changes, 2)
}

// TestDifferentialSync_ClearChanges verifies clearing changes
func TestDifferentialSync_ClearChanges(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	sync := NewDifferentialSync(cache)

	sync.TrackChange("key1", "set", "value1")
	sync.TrackChange("key2", "set", "value2")

	assert.Len(t, sync.GetChanges(), 2)

	lastSyncBefore := sync.GetLastSyncTime()
	time.Sleep(10 * time.Millisecond)

	sync.ClearChanges()

	assert.Empty(t, sync.GetChanges())
	assert.True(t, sync.GetLastSyncTime().After(lastSyncBefore))
}

// TestDifferentialSync_GetLastSyncTime verifies last sync time tracking
func TestDifferentialSync_GetLastSyncTime(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	sync := NewDifferentialSync(cache)

	initialSync := sync.GetLastSyncTime()
	assert.True(t, time.Now().After(initialSync) || time.Now().Equal(initialSync))

	time.Sleep(10 * time.Millisecond)
	sync.ClearChanges()

	newSync := sync.GetLastSyncTime()
	assert.True(t, newSync.After(initialSync))
}

// TestDifferentialSync_ChangeTimestamps verifies timestamps are set
func TestDifferentialSync_ChangeTimestamps(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	sync := NewDifferentialSync(cache)

	beforeTrack := time.Now()
	sync.TrackChange("key1", "set", "value1")
	afterTrack := time.Now()

	changes := sync.GetChanges()
	require.Len(t, changes, 1)

	timestamp := changes[0].Timestamp
	assert.True(t, timestamp.After(beforeTrack) || timestamp.Equal(beforeTrack))
	assert.True(t, timestamp.Before(afterTrack) || timestamp.Equal(afterTrack))
}

// TestConflictStrategy_String verifies strategy string representation
func TestConflictStrategy_String(t *testing.T) {
	tests := []struct {
		strategy ConflictStrategy
		name     string
	}{
		{StrategyServerWins, "StrategyServerWins"},
		{StrategyClientWins, "StrategyClientWins"},
		{StrategyNewest, "StrategyNewest"},
		{StrategyMerge, "StrategyMerge"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			resolver := NewConflictResolver(tt.strategy)
			assert.Equal(t, tt.strategy, resolver.strategy)
		})
	}
}

// TestResolve_Merge_EmptyMaps verifies merge with empty maps
func TestResolve_Merge_EmptyMaps(t *testing.T) {
	resolver := NewConflictResolver(StrategyMerge)

	conflict := &Conflict{
		Key:        "test:key",
		ServerData: map[string]interface{}{},
		ClientData: map[string]interface{}{"key": "value"},
	}

	err := resolver.Resolve(conflict)
	require.NoError(t, err)

	merged, ok := conflict.ResolvedData.(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, "value", merged["key"])
	assert.Equal(t, "merged", conflict.Resolution)
}

// TestDetectConflict_StringData verifies conflict detection with strings
func TestDetectConflict_StringData(t *testing.T) {
	conflict, err := DetectConflict("test:key", "server", "client", time.Now(), time.Now())
	require.NoError(t, err)
	require.NotNil(t, conflict)
	assert.NotEqual(t, conflict.ServerHash, conflict.ClientHash)
}

// TestDetectConflict_IntData verifies conflict detection with integers
func TestDetectConflict_IntData(t *testing.T) {
	conflict, err := DetectConflict("test:key", 123, 456, time.Now(), time.Now())
	require.NoError(t, err)
	require.NotNil(t, conflict)
	assert.NotEqual(t, conflict.ServerHash, conflict.ClientHash)
}

// BenchmarkResolve_ServerWins measures server wins performance
func BenchmarkResolve_ServerWins(b *testing.B) {
	resolver := NewConflictResolver(StrategyServerWins)
	conflict := &Conflict{
		Key:        "test:key",
		ServerData: "server data",
		ClientData: "client data",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resolver.Resolve(conflict)
	}
}

// BenchmarkResolve_Merge measures merge performance
func BenchmarkResolve_Merge(b *testing.B) {
	resolver := NewConflictResolver(StrategyMerge)
	conflict := &Conflict{
		Key: "test:key",
		ServerData: map[string]interface{}{
			"key1": "value1",
			"key2": "value2",
		},
		ClientData: map[string]interface{}{
			"key3": "value3",
			"key4": "value4",
		},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resolver.Resolve(conflict)
	}
}

// BenchmarkDetectConflict measures conflict detection performance
func BenchmarkDetectConflict(b *testing.B) {
	serverData := map[string]interface{}{"key": "server"}
	clientData := map[string]interface{}{"key": "client"}
	now := time.Now()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		DetectConflict("test:key", serverData, clientData, now, now)
	}
}

// BenchmarkHashData measures hashing performance
func BenchmarkHashData(b *testing.B) {
	data := map[string]interface{}{
		"key1": "value1",
		"key2": 42,
		"key3": true,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		hashData(data)
	}
}
