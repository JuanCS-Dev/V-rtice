# FASE C - Week 1 - Sprint 5-6: OSINT Integration

**Status**: ✅ COMPLETE
**Date**: 2025-10-07
**Sprint**: 5-6 of 12

---

## Overview

Integrated OSINT Service API into vCLI-Go with full HTTP client, visual formatters, and CLI commands.

## Architecture

### OSINT Service
- **Endpoint**: `http://localhost:8050`
- **Authentication**: None (internal service)
- **Timeout**: 120 seconds (OSINT investigations take longer)

### API Endpoints

1. **POST /start_investigation** - Start new OSINT investigation
2. **GET /investigation/{id}/status** - Get investigation status
3. **GET /investigation/{id}/report** - Get full investigation report
4. **GET /health** - Service health check

## Implementation

### 1. HTTP Client (`internal/osint/osint_client.go`)

**Lines**: 234

**Key Types**:
```go
type OSINTClient struct {
    baseURL    string
    httpClient *http.Client
}

type StartInvestigationRequest struct {
    Query              string                 `json:"query"`
    InvestigationType  string                 `json:"investigation_type"`
    Parameters         map[string]interface{} `json:"parameters,omitempty"`
}

type ReportResponse struct {
    InvestigationID   string    `json:"investigation_id"`
    Query             string    `json:"query"`
    InvestigationType string    `json:"investigation_type"`
    Status            string    `json:"status"`
    StartedAt         string    `json:"started_at"`
    CompletedAt       string    `json:"completed_at,omitempty"`
    Findings          []Finding `json:"findings,omitempty"`
    Summary           string    `json:"summary,omitempty"`
    RiskScore         float64   `json:"risk_score,omitempty"`
}

type Finding struct {
    Source      string                 `json:"source"`
    Category    string                 `json:"category"`
    Severity    string                 `json:"severity,omitempty"`
    Title       string                 `json:"title"`
    Description string                 `json:"description"`
    URL         string                 `json:"url,omitempty"`
    Timestamp   string                 `json:"timestamp,omitempty"`
}
```

**Methods**:
- `NewOSINTClient(baseURL string) *OSINTClient`
- `StartInvestigation(req StartInvestigationRequest) (*InvestigationResponse, error)`
- `GetStatus(investigationID string) (*StatusResponse, error)`
- `GetReport(investigationID string) (*ReportResponse, error)`
- `Health() error`
- `GetHealthDetails() (*HealthResponse, error)`

### 2. Visual Formatters (`internal/osint/formatters.go`)

**Lines**: 268

**Formatter Functions**:

1. **FormatInvestigationResponse** - Investigation start confirmation
   - Gradient header: "OSINT INVESTIGATION STARTED"
   - Investigation ID, status, message
   - Next step hint with command

2. **FormatStatusResponse** - Investigation progress
   - Gradient header: "OSINT INVESTIGATION STATUS"
   - Status with icons (✓ ◐ ✗ ○)
   - Progress bar with percentage
   - Current phase indicator

3. **FormatReportResponse** - Full investigation report
   - Gradient header: "OSINT INVESTIGATION REPORT"
   - Investigation overview (ID, query, type, timeline)
   - Risk score with bar visualization (HIGH/MEDIUM/LOW)
   - Findings list with severity color coding
   - Summary section

**Visual Features**:
- Progress bars: `█████████████░░░░░░░ 65.0%`
- Risk score bars with color-coded levels
- Status icons: `✓ COMPLETED`, `◐ IN_PROGRESS`, `✗ FAILED`, `○ PENDING`
- Severity styling: CRITICAL (red), MEDIUM (yellow), LOW (green)
- Consistent 70-char separator lines
- Gradient titles using `visual.GradientText()`

### 3. CLI Commands (`cmd/investigate.go`)

**Updated Commands**:

```bash
# Start OSINT investigation
vcli investigate osint start \
  --query "domain.com" \
  --type domain_analysis \
  --params-file investigation.json

# Check investigation status
vcli investigate osint status <investigation-id>

# Get full report
vcli investigate osint report <investigation-id>

# Health check
vcli investigate osint health
```

**Flags**:
- `--endpoint` - OSINT service URL (default: http://localhost:8050)
- `--query` - Investigation query/target (required for start)
- `--type` - Investigation type (required for start)
- `--params-file` - Optional JSON file with additional parameters

**Implementation Pattern**:
```go
func runOSINTStart(cmd *cobra.Command, args []string) error {
    client := osint.NewOSINTClient(osintEndpoint)

    req := osint.StartInvestigationRequest{
        Query:             osintQuery,
        InvestigationType: osintType,
        Parameters:        params,
    }

    result, err := client.StartInvestigation(req)
    if err != nil {
        return fmt.Errorf("failed to start OSINT investigation: %w", err)
    }

    fmt.Println(osint.FormatInvestigationResponse(result))
    return nil
}
```

## Investigation Types

Based on OSINT Service API:
- `person_recon` - Person reconnaissance
- `domain_analysis` - Domain and infrastructure analysis
- `email_investigation` - Email address investigation
- `social_media_scan` - Social media profiling
- `dark_web_search` - Dark web intelligence
- `data_breach_check` - Breach database searches

## Visual Output Examples

### Start Investigation
```
OSINT INVESTIGATION STARTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Investigation ID:    osint-20251007-abc123
  Status:              ○ QUEUED

Use 'vcli investigate osint status osint-20251007-abc123' to check progress
```

### Status Check
```
OSINT INVESTIGATION STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Investigation ID:    osint-20251007-abc123
  Status:              ◐ IN_PROGRESS
  Progress:            █████████████░░░░░░░ 65.0%
  Current Phase:       Analyzing social media presence
```

### Full Report
```
OSINT INVESTIGATION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Investigation Overview

  Investigation ID:    osint-20251007-abc123
  Query:               example.com
  Type:                domain_analysis
  Status:              ✓ COMPLETED
  Started:             2025-10-07 14:30:00
  Completed:           2025-10-07 14:45:23
  Risk Score:          ███████░░░░░░░░░░░░░ 7.2 (HIGH)

Summary

  Domain has suspicious DNS records and is hosted on known bulletproof hosting
  provider. Multiple indicators suggest phishing infrastructure.

Findings (3)

  [1] Suspicious DNS Configuration
      Category:    Infrastructure  |  Severity: HIGH
      Source:      DNS Analysis
      Domain uses fast-flux DNS technique commonly used by botnets
      URL:         https://threatdb.example.com/dns/abc123
      Timestamp:   2025-10-07 14:32:15

  [2] Bulletproof Hosting Detected
      Category:    Hosting  |  Severity: CRITICAL
      Source:      IP Reputation
      IP address 1.2.3.4 is known bulletproof hosting provider
      URL:         https://threatdb.example.com/ip/1.2.3.4
      Timestamp:   2025-10-07 14:35:42

  [3] SSL Certificate Anomaly
      Category:    Certificate  |  Severity: MEDIUM
      Source:      Certificate Transparency
      Recently issued Let's Encrypt certificate for newly registered domain
      Timestamp:   2025-10-07 14:40:11
```

## Files Modified

1. **cmd/investigate.go** - Added osint import, updated OSINT command implementations
2. **internal/osint/osint_client.go** - NEW - Full HTTP client
3. **internal/osint/formatters.go** - NEW - Visual formatters

## Build Status

✅ **Build successful** - No compilation errors

## Testing Checklist

- [ ] Start investigation with valid query
- [ ] Start investigation with params file
- [ ] Status check for running investigation
- [ ] Status check for completed investigation
- [ ] Get full report with findings
- [ ] Health check when service is up
- [ ] Health check when service is down
- [ ] Error handling for invalid investigation ID
- [ ] Error handling for network errors

## Integration Points

**Dependencies**:
- OSINT Service API (port 8050)
- `internal/visual` - Color palette and gradient text
- `github.com/charmbracelet/lipgloss` - Styling

**No Dependencies On**:
- Authentication (internal service)
- Database (stateless client)

## Next Sprint

**Sprint 7-8**: Brain Services Integration
- Digital Thalamus Service
- Cortex Service
- Cognitive processing commands

---

**Completion**: Sprint 5-6 ✅ COMPLETE (2/12 sprints done)
