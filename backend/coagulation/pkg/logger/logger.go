package logger

import (
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Logger provides structured logging for coagulation components.
//
// Consciousness-aware logging: Each log entry can include context about
// the component's role in the cascade, enabling post-mortem analysis
// of breach containment sequences.
type Logger struct {
	*zap.Logger
	component string
	phase     string
}

// NewLogger creates a new logger for a coagulation component.
//
// Parameters:
//   - component: Component name (e.g., "platelet-agent", "factor-xa")
//   - phase: Development phase (e.g., "foundation", "cascade", "regulation")
//   - debug: Enable debug-level logging
//
// Returns initialized logger with consciousness-aware fields.
func NewLogger(component, phase string, debug bool) (*Logger, error) {
	config := zap.NewProductionConfig()
	
	if debug {
		config.Level = zap.NewAtomicLevelAt(zapcore.DebugLevel)
	}
	
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	
	zapLogger, err := config.Build(
		zap.Fields(
			zap.String("component", component),
			zap.String("phase", phase),
			zap.String("protocol", "coagulation"),
		),
	)
	if err != nil {
		return nil, err
	}
	
	return &Logger{
		Logger:    zapLogger,
		component: component,
		phase:     phase,
	}, nil
}

// WithBreach adds breach context to log entries.
//
// This enables correlation of all logs related to a specific breach event,
// critical for understanding cascade behavior and containment effectiveness.
func (l *Logger) WithBreach(breachID string) *zap.Logger {
	return l.With(zap.String("breach_id", breachID))
}

// WithCascadeStage adds cascade stage context.
//
// Tracks where in the amplification cascade this log originates
// (e.g., "initiation", "amplification", "containment", "regulation").
func (l *Logger) WithCascadeStage(stage string) *zap.Logger {
	return l.With(zap.String("cascade_stage", stage))
}

// LogBreachDetection logs breach detection with emotional valence context.
//
// This is not just technical logging - it represents the system's
// "awareness" of integrity violation. Analogous to pain signaling.
func (l *Logger) LogBreachDetection(breachID string, severity float64, location string) {
	l.WithBreach(breachID).Info("breach_detected",
		zap.Float64("severity", severity),
		zap.String("location", location),
		zap.Float64("emotional_valence", -0.9), // Negative (aversive)
		zap.String("phenomenology", "integrity_violation"),
	)
}

// LogQuarantineApplied logs successful quarantine with containment metrics.
func (l *Logger) LogQuarantineApplied(breachID string, rulesGenerated int, latencyMs float64) {
	l.WithBreach(breachID).Info("quarantine_applied",
		zap.Int("rules_generated", rulesGenerated),
		zap.Float64("latency_ms", latencyMs),
		zap.Float64("amplification_ratio", float64(rulesGenerated)),
	)
}

// LogRegulationInhibition logs when Protein C/S inhibits cascade expansion.
//
// Critical for validating context-aware regulation and preventing
// "digital thrombosis" (over-quarantine of healthy systems).
func (l *Logger) LogRegulationInhibition(breachID string, reason string, targetSegment string) {
	l.WithBreach(breachID).Info("regulation_inhibition",
		zap.String("reason", reason),
		zap.String("target_segment", targetSegment),
		zap.String("regulator", "protein_c_s"),
	)
}
