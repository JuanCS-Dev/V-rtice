# Autonomous Investigation Service Integration

## Overview

Complete integration of the **Autonomous Investigation Service** into vCLI-Go, providing threat actor profiling, incident attribution, campaign correlation, and autonomous investigation capabilities.

**Service Endpoint**: `http://localhost:8042`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    vCLI-Go Investigation Module                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐      ┌──────────────────────────────┐    │
│  │  CLI Commands    │─────▶│  InvestigationClient         │    │
│  │  (investigate)   │      │  - HTTP Client               │    │
│  └──────────────────┘      │  - Request/Response Types    │    │
│                            │  - Error Handling            │    │
│                            └──────────────┬───────────────┘    │
│                                           │                     │
│  ┌──────────────────┐                     │                     │
│  │  Formatters      │◀────────────────────┘                     │
│  │  - Profiles      │                                           │
│  │  - Attribution   │                                           │
│  │  - Campaigns     │                                           │
│  │  - Reports       │                                           │
│  └──────────────────┘                                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ HTTP/JSON
                               │
                               ▼
         ┌──────────────────────────────────────────┐
         │  Autonomous Investigation Service         │
         │  (Port 8042)                             │
         │                                          │
         │  - Threat Actor Database                 │
         │  - Incident Attribution Engine           │
         │  - Campaign Correlation                  │
         │  - Autonomous Investigation Playbooks    │
         └──────────────────────────────────────────┘
```

## Components

### 1. InvestigationClient (`internal/investigation/investigation_client.go`)

HTTP client for the Autonomous Investigation Service API.

**Key Methods**:
- `RegisterThreatActor(req ThreatActorRegistrationRequest)` - Register new threat actor
- `GetActorProfile(actorID string)` - Retrieve threat actor profile
- `ListThreatActors()` - List all known threat actors
- `IngestIncident(req SecurityIncidentRequest)` - Ingest security incident
- `AttributeIncident(incidentID string)` - Attribute incident to threat actor
- `CorrelateCampaigns()` - Correlate incidents into campaigns
- `GetCampaign(campaignID string)` - Retrieve campaign details
- `ListCampaigns()` - List all campaigns
- `InitiateInvestigation(incidentID string)` - Start autonomous investigation
- `GetInvestigation(investigationID string)` - Get investigation status
- `Health()` - Check service health
- `GetStatus()` - Get service status
- `GetStats()` - Get service statistics

### 2. Data Structures

**Threat Actor Registration**:
```go
type ThreatActorRegistrationRequest struct {
    ActorID              string   `json:"actor_id"`
    ActorName            string   `json:"actor_name"`
    KnownTTPs            []string `json:"known_ttps"`
    KnownInfrastructure  []string `json:"known_infrastructure,omitempty"`
    SophisticationScore  float64  `json:"sophistication_score"`
}
```

**Security Incident**:
```go
type SecurityIncidentRequest struct {
    IncidentID      string                 `json:"incident_id"`
    Timestamp       *string                `json:"timestamp,omitempty"`
    IncidentType    string                 `json:"incident_type"`
    AffectedAssets  []string               `json:"affected_assets"`
    IOCs            []string               `json:"iocs"`
    TTPsObserved    []string               `json:"ttps_observed"`
    Severity        float64                `json:"severity"`
    RawEvidence     map[string]interface{} `json:"raw_evidence,omitempty"`
}
```

**Threat Actor Profile Response**:
```go
type ThreatActorProfileResponse struct {
    ActorID               string   `json:"actor_id"`
    ActorName             string   `json:"actor_name"`
    TTPs                  []string `json:"ttps"`
    Infrastructure        []string `json:"infrastructure"`
    MalwareFamilies       []string `json:"malware_families"`
    Targets               []string `json:"targets"`
    SophisticationScore   float64  `json:"sophistication_score"`
    ActivityCount         int      `json:"activity_count"`
    AttributionConfidence float64  `json:"attribution_confidence"`
}
```

### 3. Visual Formatters (`internal/investigation/formatters.go`)

Rich terminal output with gradient headers, progress bars, and color-coded information:

- `FormatThreatActorProfile()` - Display threat actor profiles
- `FormatAttributionReport()` - Display incident attribution results
- `FormatCampaignReport()` - Display campaign analysis
- `FormatInvestigationReport()` - Display investigation results
- `FormatServiceStatus()` - Display service status

### 4. CLI Commands (`cmd/investigate.go`)

#### Threat Actor Operations

```bash
# Register a new threat actor
vcli investigate autonomous register-actor --actor-file actor.json

# Get threat actor profile
vcli investigate autonomous get-actor APT28

# List all threat actors
vcli investigate autonomous list-actors
```

#### Incident Operations

```bash
# Ingest security incident
vcli investigate autonomous ingest-incident --incident-file incident.json

# Attribute incident to threat actor
vcli investigate autonomous attribute-incident INC-2025-001

# Initiate autonomous investigation
vcli investigate autonomous initiate --incident-id INC-2025-001

# Get investigation status
vcli investigate autonomous get-investigation INV-ABC123
```

#### Campaign Operations

```bash
# Correlate incidents into campaigns
vcli investigate autonomous correlate-campaigns --threshold 0.7 --time-window 30d

# Get campaign details
vcli investigate autonomous get-campaign CAMP-2025-001

# List all campaigns
vcli investigate autonomous list-campaigns
```

#### Service Operations

```bash
# Check service health
vcli investigate autonomous health

# Get service status
vcli investigate autonomous status
```

## Usage Examples

### Example 1: Register APT28 Threat Actor

**actor.json**:
```json
{
  "actor_id": "APT28",
  "actor_name": "Fancy Bear",
  "known_ttps": [
    "T1566.001 - Spearphishing Attachment",
    "T1078 - Valid Accounts",
    "T1071.001 - Web Protocols",
    "T1003 - Credential Dumping"
  ],
  "known_infrastructure": [
    "185.86.148.227",
    "193.29.187.60",
    "carberp.su",
    "sofacy-group.org"
  ],
  "sophistication_score": 0.92
}
```

```bash
vcli investigate autonomous register-actor --actor-file actor.json
```

**Output**:
```
╔════════════════════════════════════════════════════════════════╗
║              THREAT ACTOR PROFILE                              ║
╚════════════════════════════════════════════════════════════════╝

Actor Identity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ID:                  APT28
  Name:                Fancy Bear
  Sophistication:      ████████████████████ 92.0% (ADVANCED)
  Activity Count:      0
  Attribution Conf:    ████████████████░░░░ 85.0%

Tactics, Techniques & Procedures (TTPs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1. T1566.001 - Spearphishing Attachment
   2. T1078 - Valid Accounts
   3. T1071.001 - Web Protocols
   4. T1003 - Credential Dumping

Known Infrastructure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • 185.86.148.227
  • 193.29.187.60
  • carberp.su
  • sofacy-group.org
```

### Example 2: Ingest and Attribute Security Incident

**incident.json**:
```json
{
  "incident_id": "INC-2025-001",
  "incident_type": "targeted_intrusion",
  "affected_assets": [
    "webserver-prod-01",
    "database-main",
    "fileserver-backup"
  ],
  "iocs": [
    "185.86.148.227",
    "malware.exe",
    "C2.carberp.su"
  ],
  "ttps_observed": [
    "T1566.001 - Spearphishing Attachment",
    "T1078 - Valid Accounts",
    "T1003 - Credential Dumping"
  ],
  "severity": 0.85,
  "raw_evidence": {
    "email_headers": "...",
    "network_logs": "...",
    "memory_dump": "..."
  }
}
```

```bash
# Ingest incident
vcli investigate autonomous ingest-incident --incident-file incident.json

# Attribute to threat actor
vcli investigate autonomous attribute-incident INC-2025-001
```

**Output**:
```
╔════════════════════════════════════════════════════════════════╗
║           INCIDENT ATTRIBUTION REPORT                          ║
╚════════════════════════════════════════════════════════════════╝

Incident Information
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Incident ID:         INC-2025-001
  Timestamp:           2025-10-07T14:23:45Z
  Attributed Actor:    APT28
  Actor Name:          Fancy Bear
  Confidence:          ██████████████████░░ 89.5%

Matching TTPs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1. T1566.001 - Spearphishing Attachment
   2. T1078 - Valid Accounts
   3. T1003 - Credential Dumping
```

### Example 3: Autonomous Investigation

```bash
vcli investigate autonomous initiate --incident-id INC-2025-001
```

**Output**:
```
╔════════════════════════════════════════════════════════════════╗
║        AUTONOMOUS INVESTIGATION REPORT                         ║
╚════════════════════════════════════════════════════════════════╝

Investigation Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Investigation ID:    INV-ABC123
  Incident ID:         INC-2025-001
  Status:              ● COMPLETED
  Playbook Used:       apt_investigation_v2
  Duration:            127.45 seconds
  Evidence Count:      34
  Confidence:          ██████████████████░░ 91.2%

Attribution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Attributed Actor:    APT28

Key Findings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1. Spearphishing email delivered XAgentOSX payload
   2. Valid credentials stolen from compromised workstation
   3. Lateral movement to database server detected
   4. Data exfiltration to known APT28 infrastructure

Related Campaigns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1. CAMP-2024-087

Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Isolate affected systems immediately
  ✓ Reset credentials for all accessed accounts
  ✓ Block C2 infrastructure at network perimeter
  ✓ Deploy detection rules for APT28 TTPs
```

### Example 4: Campaign Correlation

```bash
vcli investigate autonomous correlate-campaigns --threshold 0.75 --time-window 60d
```

**Output**:
```
╔════════════════════════════════════════════════════════════════╗
║                CAMPAIGN ANALYSIS                               ║
╚════════════════════════════════════════════════════════════════╝

Campaign Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Campaign ID:         CAMP-2025-001
  Campaign Name:       Eastern European Government Targeting
  Attributed Actor:    APT28
  Pattern:             targeted_spearphishing_campaign
  Confidence:          ████████████████░░░░ 82.3%

Timeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Start Date:          2025-08-15
  Last Activity:       2025-10-06
  Incident Count:      7

Related Incidents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1. INC-2025-001
   2. INC-2025-045
   3. INC-2025-087
   4. INC-2025-123
   5. INC-2025-156
   6. INC-2025-189
   7. INC-2025-201

Campaign TTPs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1. T1566.001 - Spearphishing Attachment
   2. T1078 - Valid Accounts
   3. T1071.001 - Web Protocols
   4. T1003 - Credential Dumping
   5. T1027 - Obfuscated Files or Information

Targeted Entities
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Ministry of Foreign Affairs
  • Defense Contractor Alpha
  • Government Agency Beta
```

## API Reference

### Threat Actor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/actor/register` | Register new threat actor |
| GET | `/actor/{id}` | Get threat actor profile |
| GET | `/actor` | List all threat actors |

### Incident Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/incident/ingest` | Ingest security incident |
| POST | `/incident/attribute` | Attribute incident to actor |

### Campaign Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/campaign/correlate` | Correlate incidents into campaigns |
| GET | `/campaign/{id}` | Get campaign details |
| GET | `/campaign` | List all campaigns |

### Investigation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/investigation/initiate` | Start autonomous investigation |
| GET | `/investigation/{id}` | Get investigation status |

### Service Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Service status |
| GET | `/stats` | Service statistics |

## Integration with Orchestration

The Investigation Service is integrated into orchestration workflows for APT simulation and threat hunting:

```go
// APT Simulation Workflow
workflow := offensive.NewAPTSimulationWorkflow(offensive.APTSimulationOptions{
    ActorName:        "APT28",
    TargetDomain:     "target-org.com",
    SimulationPhases: []string{"reconnaissance", "weaponization", "delivery", "exploitation"},
    EthicalContext:   "Authorized Red Team Exercise 2025-Q4",
})
```

See:
- `/internal/orchestrator/offensive/apt_simulation.go`
- `/docs/ORCHESTRATION_WORKFLOWS.md`

## Testing

```bash
# Start Investigation Service (backend)
cd /home/juan/vertice-dev/backend/services/autonomous_investigation_service
python api.py

# Run vCLI-Go
./bin/vcli investigate autonomous health

# Test full workflow
./bin/vcli investigate autonomous register-actor --actor-file test/data/apt28.json
./bin/vcli investigate autonomous ingest-incident --incident-file test/data/incident.json
./bin/vcli investigate autonomous attribute-incident INC-TEST-001
./bin/vcli investigate autonomous initiate --incident-id INC-TEST-001
```

## Error Handling

The client implements comprehensive error handling:

- **Connection Errors**: Returns clear error messages when service is unreachable
- **HTTP Errors**: Captures HTTP status codes and error responses
- **Validation Errors**: Validates request data before sending
- **Timeout Handling**: 60-second timeout for long-running operations

## Performance

- **HTTP Timeouts**: 60 seconds (configurable)
- **Keep-Alive**: HTTP connection reuse enabled
- **JSON Streaming**: Efficient JSON decoding

## Security Considerations

1. **Authentication**: Service requires authentication token (when enabled)
2. **Input Validation**: All inputs validated before processing
3. **Rate Limiting**: Respects backend rate limits
4. **Secure Communication**: HTTPS support (configure via baseURL)

## Future Enhancements

- [ ] WebSocket support for real-time investigation updates
- [ ] Export investigation reports (PDF, JSON, STIX)
- [ ] Interactive TUI for campaign visualization
- [ ] Integration with threat intel feeds (MISP, OpenCTI)
- [ ] Machine learning model insights for attribution
- [ ] Collaborative investigation workspace

## Related Documentation

- [Backend Investigation Service](../../backend/services/autonomous_investigation_service/README.md)
- [Orchestration Workflows](./ORCHESTRATION_WORKFLOWS.md)
- [Narrative Filter Integration](./NARRATIVE_FILTER_INTEGRATION.md)

---

**Sprint 4 Complete** ✅
vCLI-Go now has full autonomous investigation capabilities with beautiful terminal UX.
