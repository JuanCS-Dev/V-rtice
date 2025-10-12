// Package intent - Tests
package intent

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

// MockConfirmer implements UserConfirmer for testing
type MockConfirmer struct {
	ShouldConfirm   bool
	ConfirmError    error
	SignatureResult string
	SignatureError  error
}

func (mc *MockConfirmer) Confirm(ctx context.Context, prompt *ConfirmationPrompt) (bool, error) {
	if mc.ConfirmError != nil {
		return false, mc.ConfirmError
	}
	return mc.ShouldConfirm, nil
}

func (mc *MockConfirmer) RequestSignature(ctx context.Context, cmd *nlp.Command) (string, error) {
	if mc.SignatureError != nil {
		return "", mc.SignatureError
	}
	return mc.SignatureResult, nil
}

// MockSigner implements Signer for testing
type MockSigner struct {
	SignResult   string
	SignError    error
	VerifyResult bool
	VerifyError  error
}

func (ms *MockSigner) Sign(data []byte) (string, error) {
	if ms.SignError != nil {
		return "", ms.SignError
	}
	return ms.SignResult, nil
}

func (ms *MockSigner) Verify(data []byte, signature string) (bool, error) {
	if ms.VerifyError != nil {
		return false, ms.VerifyError
	}
	return ms.VerifyResult, nil
}

func TestValidator_Validate_LowRisk_AutoApprove(t *testing.T) {
	mockConfirmer := &MockConfirmer{ShouldConfirm: false}
	mockSigner := &MockSigner{}
	validator := NewValidator(mockConfirmer, mockSigner)

	ctx := context.Background()
	secCtx := &security.SecurityContext{
		User:    &security.User{ID: "test-user"},
		Session: &security.Session{ID: "test-session"},
	}

	cmd := &nlp.Command{
		Path: []string{"kubectl", "get", "pods"},
	}

	intent := &nlp.Intent{
		RiskLevel: nlp.RiskLevelLOW,
		Verb:      "get",
		Target:    "pods",
	}

	// LOW risk should auto-approve without calling confirmer
	err := validator.Validate(ctx, secCtx, cmd, intent)
	assert.NoError(t, err)
}

func TestValidator_Validate_MediumRisk_RequiresConfirmation(t *testing.T) {
	mockConfirmer := &MockConfirmer{ShouldConfirm: true}
	mockSigner := &MockSigner{}
	validator := NewValidator(mockConfirmer, mockSigner)

	ctx := context.Background()
	secCtx := &security.SecurityContext{
		User:      &security.User{ID: "test-user"},
		Session:   &security.Session{ID: "test-session"},
		RiskScore: 50,
	}

	cmd := &nlp.Command{
		Path: []string{"kubectl", "create", "deployment"},
		Args: []string{"webapp"},
	}

	intent := &nlp.Intent{
		RiskLevel:     nlp.RiskLevelMEDIUM,
		Verb:          "create",
		Target:        "deployment",
		OriginalInput: "create deployment webapp",
	}

	err := validator.Validate(ctx, secCtx, cmd, intent)
	assert.NoError(t, err)
}

func TestValidator_Validate_UserDenies(t *testing.T) {
	mockConfirmer := &MockConfirmer{ShouldConfirm: false}
	mockSigner := &MockSigner{}
	validator := NewValidator(mockConfirmer, mockSigner)

	ctx := context.Background()
	secCtx := &security.SecurityContext{
		User:    &security.User{ID: "test-user"},
		Session: &security.Session{ID: "test-session"},
	}

	cmd := &nlp.Command{
		Path: []string{"kubectl", "delete", "pod"},
		Args: []string{"test-pod"},
	}

	intent := &nlp.Intent{
		RiskLevel:     nlp.RiskLevelHIGH,
		Verb:          "delete",
		Target:        "pod",
		OriginalInput: "delete pod test-pod",
	}

	err := validator.Validate(ctx, secCtx, cmd, intent)
	require.Error(t, err)

	// Should be IntentNotConfirmedError
	var intentErr *security.IntentNotConfirmedError
	assert.ErrorAs(t, err, &intentErr)
}

func TestValidator_Validate_CriticalRisk_RequiresSignature(t *testing.T) {
	mockConfirmer := &MockConfirmer{
		ShouldConfirm:   true,
		SignatureResult: "valid-signature",
	}
	mockSigner := &MockSigner{
		VerifyResult: true,
	}
	validator := NewValidator(mockConfirmer, mockSigner)

	ctx := context.Background()
	secCtx := &security.SecurityContext{
		User:    &security.User{ID: "test-user"},
		Session: &security.Session{ID: "test-session"},
	}

	cmd := &nlp.Command{
		Path:  []string{"kubectl", "delete", "namespace"},
		Args:  []string{"production"},
		Flags: map[string]string{"--force": ""},
	}

	intent := &nlp.Intent{
		RiskLevel:     nlp.RiskLevelCRITICAL,
		Verb:          "delete",
		Target:        "namespace",
		OriginalInput: "delete namespace production --force",
	}

	err := validator.Validate(ctx, secCtx, cmd, intent)
	assert.NoError(t, err)
}

func TestValidator_Validate_CriticalRisk_InvalidSignature(t *testing.T) {
	mockConfirmer := &MockConfirmer{
		ShouldConfirm:   true,
		SignatureResult: "invalid-signature",
	}
	mockSigner := &MockSigner{
		VerifyResult: false,
	}
	validator := NewValidator(mockConfirmer, mockSigner)

	ctx := context.Background()
	secCtx := &security.SecurityContext{
		User:    &security.User{ID: "test-user"},
		Session: &security.Session{ID: "test-session"},
	}

	cmd := &nlp.Command{
		Path: []string{"kubectl", "delete", "namespace"},
		Args: []string{"production"},
	}

	intent := &nlp.Intent{
		RiskLevel:     nlp.RiskLevelCRITICAL,
		Verb:          "delete",
		Target:        "namespace",
		OriginalInput: "delete namespace production",
	}

	err := validator.Validate(ctx, secCtx, cmd, intent)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "Invalid signature")
}

func TestReverseTranslator_Translate(t *testing.T) {
	translator := NewReverseTranslator()

	tests := []struct {
		name            string
		cmd             *nlp.Command
		shouldContain   []string
		shouldNotContain []string
	}{
		{
			name: "simple get pods",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "get", "pods"},
				Flags: map[string]string{"-n": "default"},
			},
			shouldContain: []string{"listar", "pods"},
		},
		{
			name: "delete with namespace",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "delete", "pod"},
				Args:  []string{"kafka-0"},
				Flags: map[string]string{"-n": "kafka"},
			},
			shouldContain: []string{"deletar", "pod", "kafka"},
		},
		{
			name: "scale deployment",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "scale", "deployment"},
				Args:  []string{"webapp"},
				Flags: map[string]string{"--replicas": "5"},
			},
			shouldContain: []string{"escalar", "deployment"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := translator.Translate(tt.cmd)

			for _, expected := range tt.shouldContain {
				assert.Contains(t, result, expected,
					"Translation should contain '%s'. Got: %s", expected, result)
			}

			for _, notExpected := range tt.shouldNotContain {
				assert.NotContains(t, result, notExpected,
					"Translation should NOT contain '%s'. Got: %s", notExpected, result)
			}
		})
	}
}

func TestConfirmationPrompt_FormatPrompt(t *testing.T) {
	prompt := &ConfirmationPrompt{
		OriginalInput: "delete pod test-pod",
		Translation:   "Você está prestes a executar:\n  Ação: deletar pod",
		Impact: &Impact{
			AffectedResources: []string{"test-pod"},
			Severity:          "high",
			Reversible:        false,
			EstimatedTime:     "5 segundos",
		},
		RiskLevel: "HIGH",
		RiskScore: 75,
		Anomalies: []security.Anomaly{},
	}

	formatted := prompt.FormatPrompt()

	assert.Contains(t, formatted, "CONFIRMAÇÃO DE INTENÇÃO")
	assert.Contains(t, formatted, "deletar")
	assert.Contains(t, formatted, "HIGH")
	assert.Contains(t, formatted, "[C] Confirmar")
}

func TestConfirmationPrompt_FormatPrompt_Critical(t *testing.T) {
	prompt := &ConfirmationPrompt{
		OriginalInput: "delete namespace production",
		Translation:   "Você está prestes a executar:\n  Ação: deletar namespace production",
		Impact: &Impact{
			AffectedResources: []string{"production"},
			Severity:          "critical",
			Reversible:        false,
			EstimatedTime:     "30 segundos",
		},
		RiskLevel: "CRITICAL",
		RiskScore: 95,
		Anomalies: []security.Anomaly{
			{
				Type:     "unusual_namespace",
				Message:  "Tentativa de deletar namespace de produção",
				Severity: 0.9,
			},
		},
	}

	formatted := prompt.FormatPrompt()

	assert.Contains(t, formatted, "ASSINATURA DIGITAL")
	assert.Contains(t, formatted, "Anomalias detectadas")
	assert.Contains(t, formatted, "namespace de produção")
}
