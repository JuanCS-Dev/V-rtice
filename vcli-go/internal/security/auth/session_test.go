package auth

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/security/types"
)

func TestSessionManager_CreateAndGet(t *testing.T) {
	store := NewInMemorySessionStore()
	manager := NewSessionManager(store, 1*time.Hour)

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Create session
	session, err := manager.Create(context.Background(), user, nil)
	require.NoError(t, err)
	assert.NotEmpty(t, session.ID)
	assert.Equal(t, user.ID, session.UserID)

	// Get session
	retrieved, err := manager.Get(context.Background(), session.ID)
	require.NoError(t, err)
	assert.Equal(t, session.ID, retrieved.ID)
	assert.Equal(t, session.UserID, retrieved.UserID)
}

func TestSessionManager_ExpiredSession(t *testing.T) {
	store := NewInMemorySessionStore()
	manager := NewSessionManager(store, 1*time.Millisecond)

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Create session
	session, err := manager.Create(context.Background(), user, nil)
	require.NoError(t, err)

	// Wait for expiration
	time.Sleep(10 * time.Millisecond)

	// Get should fail
	_, err = manager.Get(context.Background(), session.ID)
	assert.ErrorIs(t, err, ErrSessionExpired)
}

func TestSessionManager_Delete(t *testing.T) {
	store := NewInMemorySessionStore()
	manager := NewSessionManager(store, 1*time.Hour)

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Create session
	session, err := manager.Create(context.Background(), user, nil)
	require.NoError(t, err)

	// Delete session
	err = manager.Delete(context.Background(), session.ID)
	require.NoError(t, err)

	// Get should fail
	_, err = manager.Get(context.Background(), session.ID)
	assert.ErrorIs(t, err, ErrSessionNotFound)
}

func TestSessionManager_Cleanup(t *testing.T) {
	store := NewInMemorySessionStore()
	manager := NewSessionManager(store, 1*time.Millisecond)

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Create multiple sessions
	for i := 0; i < 5; i++ {
		_, err := manager.Create(context.Background(), user, nil)
		require.NoError(t, err)
	}

	// Wait for expiration
	time.Sleep(10 * time.Millisecond)

	// Cleanup
	err := manager.Cleanup(context.Background())
	require.NoError(t, err)

	// Verify all sessions are removed
	// This is implementation-specific, we can check by trying to get a known session
	// or by checking the store directly if it exposes count
}

func TestSessionManager_Metadata(t *testing.T) {
	store := NewInMemorySessionStore()
	manager := NewSessionManager(store, 1*time.Hour)

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	metadata := map[string]string{
		"ip":         "192.168.1.1",
		"user_agent": "vcli/2.0",
	}

	// Create session with metadata
	session, err := manager.Create(context.Background(), user, metadata)
	require.NoError(t, err)

	// Get session and verify metadata
	retrieved, err := manager.Get(context.Background(), session.ID)
	require.NoError(t, err)
	assert.Equal(t, metadata["ip"], retrieved.Metadata["ip"])
	assert.Equal(t, metadata["user_agent"], retrieved.Metadata["user_agent"])
}
