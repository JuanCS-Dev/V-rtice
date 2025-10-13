package auth

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestAuthContext_IsValid(t *testing.T) {
	ctx := &AuthContext{
		Verified:  true,
		ExpiresAt: time.Now().Add(1 * time.Hour),
	}
	assert.True(t, ctx.IsValid())

	ctx.Verified = false
	assert.False(t, ctx.IsValid())

	ctx.Verified = true
	ctx.ExpiresAt = time.Now().Add(-1 * time.Hour)
	assert.False(t, ctx.IsValid())
}

func TestAuthContext_IsExpiringSoon(t *testing.T) {
	ctx := &AuthContext{
		ExpiresAt: time.Now().Add(4 * time.Minute),
	}
	assert.True(t, ctx.IsExpiringSoon(5*time.Minute))

	ctx.ExpiresAt = time.Now().Add(10 * time.Minute)
	assert.False(t, ctx.IsExpiringSoon(5*time.Minute))
}

func TestAuthContext_HasRole(t *testing.T) {
	ctx := &AuthContext{
		Roles: []string{"admin", "developer"},
	}

	assert.True(t, ctx.HasRole("admin"))
	assert.True(t, ctx.HasRole("developer"))
	assert.False(t, ctx.HasRole("viewer"))
}

func TestAuthContext_HasAnyRole(t *testing.T) {
	ctx := &AuthContext{
		Roles: []string{"admin", "developer"},
	}

	assert.True(t, ctx.HasAnyRole("admin", "viewer"))
	assert.True(t, ctx.HasAnyRole("developer", "operator"))
	assert.False(t, ctx.HasAnyRole("viewer", "operator"))
}

func TestAuthContext_HasPermission(t *testing.T) {
	ctx := &AuthContext{
		Permissions: []string{"read:pods", "write:deployments"},
	}

	assert.True(t, ctx.HasPermission("read:pods"))
	assert.True(t, ctx.HasPermission("write:deployments"))
	assert.False(t, ctx.HasPermission("delete:namespace"))
}

func TestAuthContext_UpdateActivity(t *testing.T) {
	ctx := &AuthContext{}
	initial := ctx.LastActivity

	time.Sleep(10 * time.Millisecond)
	ctx.UpdateActivity()

	assert.True(t, ctx.LastActivity.After(initial))
}

func TestAuthContext_IsHighRisk(t *testing.T) {
	ctx := &AuthContext{
		RiskScore: 0.8,
	}
	assert.True(t, ctx.IsHighRisk())

	ctx.RiskScore = 0.6
	assert.False(t, ctx.IsHighRisk())
}

func TestAuthContext_IsMediumRisk(t *testing.T) {
	ctx := &AuthContext{
		RiskScore: 0.5,
	}
	assert.True(t, ctx.IsMediumRisk())

	ctx.RiskScore = 0.2
	assert.False(t, ctx.IsMediumRisk())

	ctx.RiskScore = 0.8
	assert.False(t, ctx.IsMediumRisk()) // High risk, not medium
}

func TestAuthContext_SessionRemaining(t *testing.T) {
	ctx := &AuthContext{
		ExpiresAt: time.Now().Add(1 * time.Hour),
	}

	remaining := ctx.SessionRemaining()
	assert.Greater(t, remaining.Minutes(), 59.0)
	assert.Less(t, remaining.Minutes(), 61.0)
}

func TestAuthContext_SessionAge(t *testing.T) {
	ctx := &AuthContext{
		CreatedAt: time.Now().Add(-30 * time.Minute),
	}

	age := ctx.SessionAge()
	assert.Greater(t, age.Minutes(), 29.0)
	assert.Less(t, age.Minutes(), 31.0)
}

func TestAuthContext_String(t *testing.T) {
	ctx := &AuthContext{
		UserID:       "testuser",
		MFACompleted: true,
		Roles:        []string{"admin"},
		RiskScore:    0.3,
	}

	str := ctx.String()
	assert.Contains(t, str, "testuser")
	// String method may or may not include roles depending on implementation
}

func TestAuthContext_BoolToString(t *testing.T) {
	assert.Equal(t, "true", boolToString(true))
	assert.Equal(t, "false", boolToString(false))
}

func TestAuthContext_EdgeCases(t *testing.T) {
	t.Run("Empty roles HasRole", func(t *testing.T) {
		ctx := &AuthContext{Roles: []string{}}
		assert.False(t, ctx.HasRole("any"))
	})

	t.Run("Nil roles HasAnyRole", func(t *testing.T) {
		ctx := &AuthContext{}
		assert.False(t, ctx.HasAnyRole("role1", "role2"))
	})

	t.Run("Empty permissions HasPermission", func(t *testing.T) {
		ctx := &AuthContext{Permissions: []string{}}
		assert.False(t, ctx.HasPermission("any"))
	})

	t.Run("Zero time SessionRemaining", func(t *testing.T) {
		ctx := &AuthContext{}
		remaining := ctx.SessionRemaining()
		assert.Less(t, remaining, time.Duration(0))
	})

	t.Run("Zero RiskScore classifications", func(t *testing.T) {
		ctx := &AuthContext{RiskScore: 0.0}
		assert.False(t, ctx.IsHighRisk())
		assert.False(t, ctx.IsMediumRisk())
	})
}
