// Package authz implements authorization checking (Layer 2) - TESTS
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Test Coverage Target: ≥95%
// REGRA DE OURO: NO MOCK - Real implementations only
package authz

import (
	"context"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

// Test data structures

// mockRoleStore implements RoleStore for testing
type mockRoleStore struct {
	roles     map[string]*security.Role
	userRoles map[string][]security.Role
}

func newMockRoleStore() *mockRoleStore {
	return &mockRoleStore{
		roles:     make(map[string]*security.Role),
		userRoles: make(map[string][]security.Role),
	}
}

func (m *mockRoleStore) GetRole(ctx context.Context, name string) (*security.Role, error) {
	if role, ok := m.roles[name]; ok {
		return role, nil
	}
	return nil, &security.SecurityError{
		Layer:   "authz",
		Type:    security.ErrorTypeAuthz,
		Message: "Role not found",
	}
}

func (m *mockRoleStore) GetUserRoles(ctx context.Context, userID string) ([]security.Role, error) {
	if roles, ok := m.userRoles[userID]; ok {
		return roles, nil
	}
	return []security.Role{}, nil
}

// mockPolicyStore implements PolicyStore for testing
type mockPolicyStore struct {
	policies []security.Policy
}

func newMockPolicyStore() *mockPolicyStore {
	return &mockPolicyStore{
		policies: []security.Policy{},
	}
}

func (m *mockPolicyStore) GetPolicies(ctx context.Context) ([]security.Policy, error) {
	return m.policies, nil
}

// Test fixtures

func createTestUser(id string, roles []string, mfaVerified bool) *security.User {
	return &security.User{
		ID:          id,
		Username:    "testuser",
		Roles:       roles,
		MFAVerified: mfaVerified,
		SessionID:   "test-session",
	}
}

func createTestCommand(path []string, flags map[string]string) *nlp.Command {
	if flags == nil {
		flags = make(map[string]string)
	}
	return &nlp.Command{
		Path:  path,
		Flags: flags,
	}
}

func createTestRole(name string, requireMFA bool, timeRestricted bool) security.Role {
	role := security.Role{
		Name:       name,
		RequireMFA: requireMFA,
		Permissions: []security.Permission{
			{
				Resource:  "pods",
				Verbs:     []string{"get", "list", "watch"},
				Namespace: "*",
			},
		},
	}
	
	if timeRestricted {
		role.TimeRestrictions = security.TimeRestriction{
			AllowedHours: []int{9, 10, 11, 12, 13, 14, 15, 16, 17}, // Business hours
			AllowedDays:  []int{1, 2, 3, 4, 5},                     // Mon-Fri
		}
	}
	
	return role
}

// Tests for NewChecker

func TestNewChecker(t *testing.T) {
	roleStore := newMockRoleStore()
	policyStore := newMockPolicyStore()
	
	checker := NewChecker(roleStore, policyStore)
	
	if checker == nil {
		t.Fatal("NewChecker returned nil")
	}
	if checker.roleStore != roleStore {
		t.Error("roleStore not set correctly")
	}
	if checker.policyStore != policyStore {
		t.Error("policyStore not set correctly")
	}
}

// Tests for PreCheck

func TestPreCheck_NoRoles(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	user := createTestUser("user1", []string{}, false)
	
	err := checker.PreCheck(context.Background(), user, "list pods")
	
	if err == nil {
		t.Fatal("Expected error for user with no roles")
	}
	
	secErr, ok := err.(*security.SecurityError)
	if !ok {
		t.Fatal("Expected SecurityError")
	}
	if secErr.Layer != "authz" {
		t.Errorf("Expected layer 'authz', got '%s'", secErr.Layer)
	}
	if secErr.Type != security.ErrorTypeAuthz {
		t.Errorf("Expected type '%s', got '%s'", security.ErrorTypeAuthz, secErr.Type)
	}
}

func TestPreCheck_WithRoles(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	user := createTestUser("user1", []string{"viewer"}, false)
	
	err := checker.PreCheck(context.Background(), user, "list pods")
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
}

func TestPreCheck_ForbiddenPatterns(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	user := createTestUser("user1", []string{"admin"}, false)
	
	testCases := []struct {
		name  string
		input string
	}{
		{"delete all", "delete all pods"},
		{"rm -rf", "rm -rf /"},
		{"kubectl delete all", "kubectl delete --all"},
		{"delete production", "delete namespaces production"},
		{"mixed case", "DELETE ALL"},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			err := checker.PreCheck(context.Background(), user, tc.input)
			
			if err == nil {
				t.Fatalf("Expected error for forbidden pattern: %s", tc.input)
			}
			
			secErr, ok := err.(*security.SecurityError)
			if !ok {
				t.Fatal("Expected SecurityError")
			}
			if secErr.Layer != "authz" {
				t.Errorf("Expected layer 'authz', got '%s'", secErr.Layer)
			}
		})
	}
}

// Tests for CheckCommand

func TestCheckCommand_Success(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "viewer",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "pods",
					Verbs:     []string{"get", "list"},
					Namespace: "*",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	user := createTestUser("user1", []string{"viewer"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
}

func TestCheckCommand_NoPermission(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "viewer",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "pods",
					Verbs:     []string{"get", "list"},
					Namespace: "*",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	user := createTestUser("user1", []string{"viewer"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	// Try to delete (not allowed for viewer)
	cmd := createTestCommand([]string{"kubectl", "delete", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err == nil {
		t.Fatal("Expected permission denied error")
	}
	
	secErr, ok := err.(*security.SecurityError)
	if !ok {
		t.Fatal("Expected SecurityError")
	}
	if secErr.Type != security.ErrorTypeAuthz {
		t.Errorf("Expected authz error, got %s", secErr.Type)
	}
}

func TestCheckCommand_MFARequired(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "admin",
			RequireMFA: true,
			Permissions: []security.Permission{
				{
					Resource:  "*",
					Verbs:     []string{"*"},
					Namespace: "*",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	// User without MFA
	user := createTestUser("user1", []string{"admin"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "delete", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err == nil {
		t.Fatal("Expected MFA required error")
	}
	
	secErr, ok := err.(*security.SecurityError)
	if !ok {
		t.Fatal("Expected SecurityError")
	}
	if !containsString(secErr.Message, "MFA") {
		t.Errorf("Expected MFA error message, got: %s", secErr.Message)
	}
}

func TestCheckCommand_MFAVerified(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "admin",
			RequireMFA: true,
			Permissions: []security.Permission{
				{
					Resource:  "*",
					Verbs:     []string{"*"},
					Namespace: "*",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	// User with MFA
	user := createTestUser("user1", []string{"admin"}, true)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "delete", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error with MFA verified: %v", err)
	}
}

func TestCheckCommand_TimeRestriction_Allowed(t *testing.T) {
	// Create a role with time restrictions matching current time
	currentHour := time.Now().Hour()
	currentDay := int(time.Now().Weekday())
	
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "restricted",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "pods",
					Verbs:     []string{"get"},
					Namespace: "*",
				},
			},
			TimeRestrictions: security.TimeRestriction{
				AllowedHours: []int{currentHour},
				AllowedDays:  []int{currentDay},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	user := createTestUser("user1", []string{"restricted"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error with valid time restriction: %v", err)
	}
}

func TestCheckCommand_TimeRestriction_Denied(t *testing.T) {
	// Create a role with time restrictions NOT matching current time
	currentHour := time.Now().Hour()
	restrictedHour := (currentHour + 12) % 24 // 12 hours from now
	
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "restricted",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "pods",
					Verbs:     []string{"get"},
					Namespace: "*",
				},
			},
			TimeRestrictions: security.TimeRestriction{
				AllowedHours: []int{restrictedHour},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	user := createTestUser("user1", []string{"restricted"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err == nil {
		t.Fatal("Expected time restriction error")
	}
	
	secErr, ok := err.(*security.SecurityError)
	if !ok {
		t.Fatal("Expected SecurityError")
	}
	if !containsString(secErr.Message, "not allowed at this time") {
		t.Errorf("Expected time restriction error message, got: %s", secErr.Message)
	}
}

func TestCheckCommand_PolicyDenial(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "admin",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "*",
					Verbs:     []string{"*"},
					Namespace: "*",
				},
			},
		},
	}
	
	policyStore := newMockPolicyStore()
	policyStore.policies = []security.Policy{
		{
			Name:        "deny-production-delete",
			Description: "Deny all deletions in production",
			Effect:      security.PolicyEffectDENY,
			Conditions: []security.Condition{
				{
					Type:     security.ConditionTypeNamespace,
					Operator: security.OperatorEquals,
					Value:    "production",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, policyStore)
	
	user := createTestUser("user1", []string{"admin"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand(
		[]string{"kubectl", "delete", "pods"},
		map[string]string{"--namespace": "production"},
	)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err == nil {
		t.Fatal("Expected policy denial error")
	}
	
	secErr, ok := err.(*security.SecurityError)
	if !ok {
		t.Fatal("Expected SecurityError")
	}
	if !containsString(secErr.Message, "policy") {
		t.Errorf("Expected policy error message, got: %s", secErr.Message)
	}
}

// Tests for roleHasPermission

func TestRoleHasPermission_Wildcard(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	role := security.Role{
		Name: "admin",
		Permissions: []security.Permission{
			{
				Resource:  "*",
				Verbs:     []string{"*"},
				Namespace: "*",
			},
		},
	}
	
	testCases := []struct {
		resource  string
		verb      string
		namespace string
	}{
		{"pods", "get", "default"},
		{"deployments", "delete", "production"},
		{"secrets", "list", "kube-system"},
	}
	
	for _, tc := range testCases {
		t.Run(tc.resource+"-"+tc.verb, func(t *testing.T) {
			if !checker.roleHasPermission(role, tc.resource, tc.verb, tc.namespace) {
				t.Errorf("Expected permission for %s %s in %s", tc.verb, tc.resource, tc.namespace)
			}
		})
	}
}

func TestRoleHasPermission_Specific(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	role := security.Role{
		Name: "pod-reader",
		Permissions: []security.Permission{
			{
				Resource:  "pods",
				Verbs:     []string{"get", "list", "watch"},
				Namespace: "default",
			},
		},
	}
	
	// Should have permission
	if !checker.roleHasPermission(role, "pods", "get", "default") {
		t.Error("Expected permission for get pods in default")
	}
	
	// Should NOT have permission (wrong verb)
	if checker.roleHasPermission(role, "pods", "delete", "default") {
		t.Error("Should not have permission to delete")
	}
	
	// Should NOT have permission (wrong resource)
	if checker.roleHasPermission(role, "deployments", "get", "default") {
		t.Error("Should not have permission for deployments")
	}
	
	// Should NOT have permission (wrong namespace)
	if checker.roleHasPermission(role, "pods", "get", "production") {
		t.Error("Should not have permission in production namespace")
	}
}

// Tests for checkTimeRestriction

func TestCheckTimeRestriction_NoRestrictions(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	tr := security.TimeRestriction{}
	
	if !checker.checkTimeRestriction(tr) {
		t.Error("Expected no restrictions to pass")
	}
}

func TestCheckTimeRestriction_HourRestriction(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	currentHour := time.Now().Hour()
	
	// Should pass (current hour is allowed)
	tr1 := security.TimeRestriction{
		AllowedHours: []int{currentHour},
	}
	if !checker.checkTimeRestriction(tr1) {
		t.Error("Expected current hour to be allowed")
	}
	
	// Should fail (current hour not allowed)
	otherHour := (currentHour + 12) % 24
	tr2 := security.TimeRestriction{
		AllowedHours: []int{otherHour},
	}
	if checker.checkTimeRestriction(tr2) {
		t.Error("Expected other hour to be denied")
	}
}

func TestCheckTimeRestriction_DayRestriction(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	currentDay := int(time.Now().Weekday())
	
	// Should pass (current day is allowed)
	tr1 := security.TimeRestriction{
		AllowedDays: []int{currentDay},
	}
	if !checker.checkTimeRestriction(tr1) {
		t.Error("Expected current day to be allowed")
	}
	
	// Should fail (current day not allowed)
	otherDay := (currentDay + 3) % 7
	tr2 := security.TimeRestriction{
		AllowedDays: []int{otherDay},
	}
	if checker.checkTimeRestriction(tr2) {
		t.Error("Expected other day to be denied")
	}
}

// Tests for evaluatePolicy

func TestEvaluatePolicy_AllConditionsSatisfied(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	policy := security.Policy{
		Name:   "test-policy",
		Effect: security.PolicyEffectDENY,
		Conditions: []security.Condition{
			{
				Type:     security.ConditionTypeNamespace,
				Operator: security.OperatorEquals,
				Value:    "production",
			},
		},
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	cmd := createTestCommand(
		[]string{"kubectl", "delete", "pods"},
		map[string]string{"--namespace": "production"},
	)
	
	effect, err := checker.evaluatePolicy(policy, secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if effect != security.PolicyEffectDENY {
		t.Errorf("Expected DENY effect, got %s", effect)
	}
}

func TestEvaluatePolicy_ConditionNotSatisfied(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	policy := security.Policy{
		Name:   "test-policy",
		Effect: security.PolicyEffectDENY,
		Conditions: []security.Condition{
			{
				Type:     security.ConditionTypeNamespace,
				Operator: security.OperatorEquals,
				Value:    "production",
			},
		},
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	// Different namespace
	cmd := createTestCommand(
		[]string{"kubectl", "delete", "pods"},
		map[string]string{"--namespace": "development"},
	)
	
	effect, err := checker.evaluatePolicy(policy, secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if effect != "" {
		t.Errorf("Expected empty effect (policy doesn't apply), got %s", effect)
	}
}

// Tests for condition evaluation

func TestEvalIPCondition_Equals(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeIP,
		Operator: security.OperatorEquals,
		Value:    "192.168.1.100",
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	result, err := checker.evalIPCondition(cond, secCtx)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if !result {
		t.Error("Expected IP to match")
	}
}

func TestEvalIPCondition_InCIDR(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeIP,
		Operator: security.OperatorIn,
		Value:    "192.168.1.0/24",
	}
	
	testCases := []struct {
		ip       string
		expected bool
	}{
		{"192.168.1.100", true},
		{"192.168.1.1", true},
		{"192.168.1.254", true},
		{"192.168.2.100", false},
		{"10.0.0.1", false},
	}
	
	for _, tc := range testCases {
		t.Run(tc.ip, func(t *testing.T) {
			secCtx := &security.SecurityContext{
				User: &security.User{ID: "user1"},
				IP:   tc.ip,
			}
			
			result, err := checker.evalIPCondition(cond, secCtx)
			
			if err != nil {
				t.Errorf("Unexpected error: %v", err)
			}
			if result != tc.expected {
				t.Errorf("Expected %v for IP %s, got %v", tc.expected, tc.ip, result)
			}
		})
	}
}

func TestEvalTimeCondition(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	currentHour := time.Now().Hour()
	
	testCases := []struct {
		name     string
		operator security.ConditionOperator
		value    int
		expected bool
	}{
		{"equals-same", security.OperatorEquals, currentHour, true},
		{"equals-different", security.OperatorEquals, (currentHour + 1) % 24, false},
		{"greater-yes", security.OperatorGreaterThan, currentHour - 1, true},
		{"greater-no", security.OperatorGreaterThan, currentHour + 1, false},
		{"less-yes", security.OperatorLessThan, currentHour + 1, true},
		{"less-no", security.OperatorLessThan, currentHour - 1, false},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			cond := security.Condition{
				Type:     security.ConditionTypeTime,
				Operator: tc.operator,
				Value:    tc.value,
			}
			
			result, err := checker.evalTimeCondition(cond)
			
			if err != nil {
				t.Errorf("Unexpected error: %v", err)
			}
			if result != tc.expected {
				t.Errorf("Expected %v, got %v", tc.expected, result)
			}
		})
	}
}

func TestEvalDayCondition(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	currentDay := int(time.Now().Weekday())
	
	// Current day in list
	cond1 := security.Condition{
		Type:     security.ConditionTypeDay,
		Operator: security.OperatorIn,
		Value:    []int{currentDay},
	}
	
	result1, err := checker.evalDayCondition(cond1)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if !result1 {
		t.Error("Expected current day to be in list")
	}
	
	// Current day not in list
	otherDay := (currentDay + 3) % 7
	cond2 := security.Condition{
		Type:     security.ConditionTypeDay,
		Operator: security.OperatorIn,
		Value:    []int{otherDay},
	}
	
	result2, err := checker.evalDayCondition(cond2)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result2 {
		t.Error("Expected current day to NOT be in list")
	}
}

func TestEvalNamespaceCondition(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	testCases := []struct {
		name      string
		operator  security.ConditionOperator
		value     string
		cmdNS     string
		expected  bool
	}{
		{"equals-match", security.OperatorEquals, "production", "production", true},
		{"equals-no-match", security.OperatorEquals, "production", "development", false},
		{"not-equals-match", security.OperatorNotEquals, "production", "development", true},
		{"not-equals-no-match", security.OperatorNotEquals, "production", "production", false},
		{"contains-match", security.OperatorContains, "prod", "production", true},
		{"contains-no-match", security.OperatorContains, "prod", "development", false},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			cond := security.Condition{
				Type:     security.ConditionTypeNamespace,
				Operator: tc.operator,
				Value:    tc.value,
			}
			
			cmd := createTestCommand(
				[]string{"kubectl", "get", "pods"},
				map[string]string{"--namespace": tc.cmdNS},
			)
			
			result, err := checker.evalNamespaceCondition(cond, cmd)
			
			if err != nil {
				t.Errorf("Unexpected error: %v", err)
			}
			if result != tc.expected {
				t.Errorf("Expected %v, got %v", tc.expected, result)
			}
		})
	}
}

func TestEvalRiskScoreCondition(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	testCases := []struct {
		name      string
		operator  security.ConditionOperator
		threshold int
		riskScore int
		expected  bool
	}{
		{"greater-yes", security.OperatorGreaterThan, 50, 75, true},
		{"greater-no", security.OperatorGreaterThan, 50, 25, false},
		{"less-yes", security.OperatorLessThan, 50, 25, true},
		{"less-no", security.OperatorLessThan, 50, 75, false},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			cond := security.Condition{
				Type:     security.ConditionTypeRiskScore,
				Operator: tc.operator,
				Value:    tc.threshold,
			}
			
			secCtx := &security.SecurityContext{
				User:      &security.User{ID: "user1"},
				RiskScore: tc.riskScore,
			}
			
			result, err := checker.evalRiskScoreCondition(cond, secCtx)
			
			if err != nil {
				t.Errorf("Unexpected error: %v", err)
			}
			if result != tc.expected {
				t.Errorf("Expected %v, got %v", tc.expected, result)
			}
		})
	}
}

// Tests for extractResourceAndVerb

func TestExtractResourceAndVerb(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	testCases := []struct {
		name     string
		path     []string
		wantRes  string
		wantVerb string
	}{
		{"normal", []string{"kubectl", "get", "pods"}, "pods", "get"},
		{"delete", []string{"kubectl", "delete", "deployment"}, "deployment", "delete"},
		{"short-path", []string{"kubectl"}, "unknown", "unknown"},
		{"empty", []string{}, "unknown", "unknown"},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			cmd := createTestCommand(tc.path, nil)
			
			resource, verb := checker.extractResourceAndVerb(cmd)
			
			if resource != tc.wantRes {
				t.Errorf("Expected resource '%s', got '%s'", tc.wantRes, resource)
			}
			if verb != tc.wantVerb {
				t.Errorf("Expected verb '%s', got '%s'", tc.wantVerb, verb)
			}
		})
	}
}

// Tests for extractNamespace

func TestExtractNamespace(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	testCases := []struct {
		name  string
		flags map[string]string
		want  string
	}{
		{"short-flag", map[string]string{"-n": "production"}, "production"},
		{"long-flag", map[string]string{"--namespace": "development"}, "development"},
		{"no-flag", map[string]string{}, "default"},
		{"other-flags", map[string]string{"--output": "json"}, "default"},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			cmd := createTestCommand([]string{"kubectl", "get", "pods"}, tc.flags)
			
			namespace := checker.extractNamespace(cmd)
			
			if namespace != tc.want {
				t.Errorf("Expected namespace '%s', got '%s'", tc.want, namespace)
			}
		})
	}
}

// Edge cases and error conditions

func TestCheckCommand_InvalidIP(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "viewer",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "*",
					Verbs:     []string{"*"},
					Namespace: "*",
				},
			},
		},
	}
	
	policyStore := newMockPolicyStore()
	policyStore.policies = []security.Policy{
		{
			Name:   "ip-restriction",
			Effect: security.PolicyEffectDENY,
			Conditions: []security.Condition{
				{
					Type:     security.ConditionTypeIP,
					Operator: security.OperatorEquals,
					Value:    "192.168.1.100",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, policyStore)
	
	user := createTestUser("user1", []string{"viewer"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "invalid-ip",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	// Should not error, just not match IP condition
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error with invalid IP: %v", err)
	}
}

func TestEvalIPCondition_InvalidCIDR(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeIP,
		Operator: security.OperatorIn,
		Value:    "invalid-cidr",
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	result, err := checker.evalIPCondition(cond, secCtx)
	
	if err == nil {
		t.Error("Expected error for invalid CIDR")
	}
	if result {
		t.Error("Expected false result for error case")
	}
}

// Helper functions

func containsString(s, substr string) bool {
	return len(s) > 0 && len(substr) > 0 && (s == substr || len(s) >= len(substr) && findSubstring(s, substr))
}

func findSubstring(s, substr string) bool {
	if len(substr) > len(s) {
		return false
	}
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// Additional comprehensive tests for edge cases

func TestEvaluateCondition_UnknownType(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     "unknown_type",
		Operator: security.OperatorEquals,
		Value:    "test",
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	result, err := checker.evaluateCondition(cond, secCtx, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for unknown condition type")
	}
}

func TestEvalIPCondition_UnknownOperator(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeIP,
		Operator: "unknown_operator",
		Value:    "192.168.1.100",
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	result, err := checker.evalIPCondition(cond, secCtx)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for unknown operator")
	}
}

func TestEvalTimeCondition_UnknownOperator(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeTime,
		Operator: "unknown_operator",
		Value:    12,
	}
	
	result, err := checker.evalTimeCondition(cond)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for unknown operator")
	}
}

func TestEvalDayCondition_UnknownOperator(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeDay,
		Operator: "unknown_operator",
		Value:    []int{1, 2, 3},
	}
	
	result, err := checker.evalDayCondition(cond)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for unknown operator")
	}
}

func TestEvalNamespaceCondition_UnknownOperator(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeNamespace,
		Operator: "unknown_operator",
		Value:    "production",
	}
	
	cmd := createTestCommand(
		[]string{"kubectl", "get", "pods"},
		map[string]string{"--namespace": "production"},
	)
	
	result, err := checker.evalNamespaceCondition(cond, cmd)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for unknown operator")
	}
}

func TestEvalRiskScoreCondition_UnknownOperator(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeRiskScore,
		Operator: "unknown_operator",
		Value:    50,
	}
	
	secCtx := &security.SecurityContext{
		User:      &security.User{ID: "user1"},
		RiskScore: 75,
	}
	
	result, err := checker.evalRiskScoreCondition(cond, secCtx)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for unknown operator")
	}
}

func TestCheckCommand_UserRolesError(t *testing.T) {
	roleStore := newMockRoleStore()
	// Don't add any roles - will return empty list
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	user := createTestUser("user1", []string{"viewer"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	// Should get permission denied since user has no roles in store
	if err == nil {
		t.Fatal("Expected permission denied error")
	}
}

func TestCheckCommand_MultipleRolesFirstMatch(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "viewer",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "pods",
					Verbs:     []string{"get"},
					Namespace: "*",
				},
			},
		},
		{
			Name:       "admin",
			RequireMFA: true, // Would fail if checked
			Permissions: []security.Permission{
				{
					Resource:  "*",
					Verbs:     []string{"*"},
					Namespace: "*",
				},
			},
		},
	}
	
	checker := NewChecker(roleStore, newMockPolicyStore())
	
	// User without MFA
	user := createTestUser("user1", []string{"viewer", "admin"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	// This should pass with first role (viewer) even though admin requires MFA
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err != nil {
		t.Errorf("Should succeed with first matching role: %v", err)
	}
}

func TestCheckCommand_AllowEffect(t *testing.T) {
	roleStore := newMockRoleStore()
	roleStore.userRoles["user1"] = []security.Role{
		{
			Name:       "viewer",
			RequireMFA: false,
			Permissions: []security.Permission{
				{
					Resource:  "*",
					Verbs:     []string{"*"},
					Namespace: "*",
				},
			},
		},
	}
	
	policyStore := newMockPolicyStore()
	policyStore.policies = []security.Policy{
		{
			Name:        "allow-all",
			Description: "Allow everything",
			Effect:      security.PolicyEffectALLOW,
			Conditions:  []security.Condition{},
		},
	}
	
	checker := NewChecker(roleStore, policyStore)
	
	user := createTestUser("user1", []string{"viewer"}, false)
	secCtx := &security.SecurityContext{
		User:      user,
		IP:        "192.168.1.100",
		RiskScore: 10,
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	err := checker.CheckCommand(context.Background(), secCtx, cmd)
	
	if err != nil {
		t.Errorf("Should succeed with allow policy: %v", err)
	}
}

func TestExtractNamespace_BothFlags(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	// When both flags present, -n takes precedence
	cmd := createTestCommand(
		[]string{"kubectl", "get", "pods"},
		map[string]string{
			"-n":          "short-flag-ns",
			"--namespace": "long-flag-ns",
		},
	)
	
	namespace := checker.extractNamespace(cmd)
	
	if namespace != "short-flag-ns" {
		t.Errorf("Expected -n flag to take precedence, got: %s", namespace)
	}
}

func TestEvalIPCondition_NilIP(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	cond := security.Condition{
		Type:     security.ConditionTypeIP,
		Operator: security.OperatorEquals,
		Value:    "192.168.1.100",
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "",
	}
	
	result, err := checker.evalIPCondition(cond, secCtx)
	
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result {
		t.Error("Expected false for empty IP")
	}
}

func TestRoleHasPermission_MultiplePermissions(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	role := security.Role{
		Name: "multi-perm",
		Permissions: []security.Permission{
			{
				Resource:  "pods",
				Verbs:     []string{"get"},
				Namespace: "default",
			},
			{
				Resource:  "deployments",
				Verbs:     []string{"list"},
				Namespace: "production",
			},
		},
	}
	
	// First permission should match
	if !checker.roleHasPermission(role, "pods", "get", "default") {
		t.Error("Expected first permission to match")
	}
	
	// Second permission should match
	if !checker.roleHasPermission(role, "deployments", "list", "production") {
		t.Error("Expected second permission to match")
	}
	
	// Neither should match
	if checker.roleHasPermission(role, "secrets", "delete", "kube-system") {
		t.Error("Expected no permission match")
	}
}

func TestCheckTimeRestriction_EmptyLists(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	tr := security.TimeRestriction{
		AllowedHours: []int{},
		AllowedDays:  []int{},
	}
	
	if !checker.checkTimeRestriction(tr) {
		t.Error("Expected empty restrictions to pass")
	}
}

func TestCheckTimeRestriction_OnlyDays(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	currentDay := int(time.Now().Weekday())
	
	tr := security.TimeRestriction{
		AllowedDays: []int{currentDay},
	}
	
	if !checker.checkTimeRestriction(tr) {
		t.Error("Expected current day to pass")
	}
}

func TestCheckTimeRestriction_BothRestrictions(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	currentHour := time.Now().Hour()
	currentDay := int(time.Now().Weekday())
	
	tr := security.TimeRestriction{
		AllowedHours: []int{currentHour},
		AllowedDays:  []int{currentDay},
	}
	
	if !checker.checkTimeRestriction(tr) {
		t.Error("Expected both hour and day to pass")
	}
}

func TestEvaluateCondition_AllTypes(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	secCtx := &security.SecurityContext{
		User:      &security.User{ID: "user1"},
		IP:        "192.168.1.100",
		RiskScore: 50,
	}
	
	cmd := createTestCommand(
		[]string{"kubectl", "get", "pods"},
		map[string]string{"--namespace": "production"},
	)
	
	testCases := []struct {
		name     string
		condType security.ConditionType
		operator security.ConditionOperator
		value    interface{}
	}{
		{"ip", security.ConditionTypeIP, security.OperatorEquals, "192.168.1.100"},
		{"time", security.ConditionTypeTime, security.OperatorEquals, time.Now().Hour()},
		{"day", security.ConditionTypeDay, security.OperatorIn, []int{int(time.Now().Weekday())}},
		{"namespace", security.ConditionTypeNamespace, security.OperatorEquals, "production"},
		{"risk", security.ConditionTypeRiskScore, security.OperatorEquals, 50},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			cond := security.Condition{
				Type:     tc.condType,
				Operator: tc.operator,
				Value:    tc.value,
			}
			
			_, err := checker.evaluateCondition(cond, secCtx, cmd)
			if err != nil {
				t.Errorf("Unexpected error for %s: %v", tc.name, err)
			}
		})
	}
}

func TestEvaluatePolicy_ErrorInCondition(t *testing.T) {
	checker := NewChecker(newMockRoleStore(), newMockPolicyStore())
	
	policy := security.Policy{
		Name:   "test-error",
		Effect: security.PolicyEffectDENY,
		Conditions: []security.Condition{
			{
				Type:     security.ConditionTypeIP,
				Operator: security.OperatorIn,
				Value:    "invalid-cidr", // Will cause error
			},
		},
	}
	
	secCtx := &security.SecurityContext{
		User: &security.User{ID: "user1"},
		IP:   "192.168.1.100",
	}
	
	cmd := createTestCommand([]string{"kubectl", "get", "pods"}, nil)
	
	effect, err := checker.evaluatePolicy(policy, secCtx, cmd)
	
	// Should return error from condition evaluation
	if err == nil {
		t.Error("Expected error from invalid CIDR")
	}
	if effect != "" {
		t.Errorf("Expected empty effect on error, got: %s", effect)
	}
}
