# HITL Console Integration - vcli-go

## Overview

The HITL (Human-in-the-Loop) Console integration provides command-line access to the Reactive Fabric HITL decision management system. Security analysts can review, approve, reject, or escalate critical security decisions identified by the CANDI threat analysis engine.

## Installation

The HITL commands are built into vcli. Build the latest version:

```bash
cd /home/juan/vertice-dev/vcli-go
/home/juan/go-sdk/bin/go build -o bin/vcli ./cmd/
```

## Authentication

HITL requires authentication. You can authenticate in two ways:

### Method 1: Username/Password

```bash
vcli hitl list --username admin --password 'ChangeMe123!' --endpoint http://localhost:8000/api
```

### Method 2: Access Token

```bash
# Login once to get token (not implemented yet, use Method 1 for now)
vcli hitl list --token <your-access-token> --endpoint http://localhost:8000/api
```

### Method 3: Environment Variables (Recommended)

```bash
export HITL_ENDPOINT=http://localhost:8000/api
export HITL_USERNAME=admin
export HITL_PASSWORD='ChangeMe123!'

# Now you can use commands without flags
vcli hitl list
vcli hitl stats
```

## Commands

### System Status

Get current HITL system status:

```bash
vcli hitl status
```

**Output:**
```
HITL System Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status:             operational
Pending Decisions:  12
Critical Pending:   3
In Review:          2
Decisions Today:    47
```

### List Decisions

List all pending decisions:

```bash
# All decisions
vcli hitl list

# Critical only
vcli hitl list --priority critical

# JSON format
vcli hitl list --output json
```

**Output:**
```
ANALYSIS_ID       THREAT     SOURCE_IP        ATTRIBUTION           PRIORITY   AGE
CANDI-apt28-001   APT        185.86.148.10    APT28 (Fancy Bear)   critical   5m
CANDI-unc2452-01  APT        192.168.1.50     UNC2452 (SVR)        critical   12m
CANDI-lazarus-05  TARGETED   10.0.5.100       Lazarus Group        high       45m

3 pending decision(s)
```

### Show Decision Details

Display complete forensic details for a specific decision:

```bash
vcli hitl show CANDI-apt28-001
```

**Output:**
```
Decision: CANDI-apt28-001
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Threat Assessment:
  Threat Level:     APT
  Priority:         critical
  Status:           pending

Attack Details:
  Source IP:        185.86.148.10
  Attribution:      APT28 (Fancy Bear) (94.5% confidence)
  Incident ID:      INC-2025-04-15-001

Indicators of Compromise (8):
  - 185.86.148.10 (IP)
  - hxxp://apt28-c2.example.com/implant.elf (URL)
  - 7d8f2a3e5c9b1a4f6e8d3c2b5a9e4f1c (MD5)
  - T1566.001 (Phishing: Spearphishing Attachment)
  ...

TTPs (5):
  - T1566.001 - Phishing: Spearphishing Attachment
  - T1059.003 - Command and Scripting Interpreter: Windows Command Shell
  - T1053.005 - Scheduled Task/Job: Scheduled Task
  - T1003.001 - OS Credential Dumping: LSASS Memory
  - T1071.001 - Application Layer Protocol: Web Protocols

Recommended Actions:
  - block_ip
  - quarantine_system
  - activate_killswitch
  - escalate_to_soc

Forensic Summary:
  Threat Level: APT | Attribution: APT28 (Fancy Bear) (confidence: 94.5%) |
  Behaviors: ssh_brute_force, custom_malware, persistence_cron, credential_dump |
  IOCs: 8 indicators identified | TTPs: T1566.001, T1059.003, T1053.005, T1003.001, T1071.001 |
  Sophistication: 9.2/10

Timeline:
  Created:  2025-04-15T14:23:45Z
  Updated:  2025-04-15T14:23:45Z
  Age:      5m
```

### Approve Decision

Approve decision and execute specified actions:

```bash
# Approve with specific actions
vcli hitl approve CANDI-apt28-001 --actions block_ip,quarantine_system

# Approve with notes
vcli hitl approve CANDI-apt28-001 \
  --actions block_ip,quarantine_system \
  --notes "Confirmed APT28 C2 communication. Blocked at perimeter."

# Approve all recommended actions (default)
vcli hitl approve CANDI-apt28-001

# Approve but don't execute automated actions
vcli hitl approve CANDI-apt28-001 \
  --actions no_action \
  --notes "Manual response initiated via SOC playbook"
```

**Available Actions:**
- `block_ip` - Block source IP at firewall
- `quarantine_system` - Isolate affected systems
- `activate_killswitch` - Trigger emergency kill switch
- `deploy_countermeasure` - Deploy active countermeasures
- `escalate_to_soc` - Escalate to SOC team
- `no_action` - Approve but take no automated action

**Output:**
```
✅ Decision approved: CANDI-apt28-001
Status:      approved
Decided by:  admin
Decided at:  2025-04-15T14:30:12Z

Approved actions (2):
  - block_ip
  - quarantine_system

Notes: Confirmed APT28 C2 communication. Blocked at perimeter.
```

### Reject Decision

Reject a decision with reason:

```bash
vcli hitl reject CANDI-apt28-001 --notes "False positive - legitimate admin activity from VPN"
```

**Output:**
```
✅ Decision rejected: CANDI-apt28-001
Status:      rejected
Decided by:  admin
Decided at:  2025-04-15T14:35:22Z
Notes:       False positive - legitimate admin activity from VPN
```

### Escalate Decision

Escalate to higher authority:

```bash
vcli hitl escalate CANDI-apt28-001 --reason "Potential nation-state actor - requires CISO approval"
```

**Output:**
```
⬆️  Decision escalated: CANDI-apt28-001
Status:      escalated
Escalated by: admin
Escalated at: 2025-04-15T14:40:33Z
Reason:       Potential nation-state actor - requires CISO approval
```

### Statistics

View decision statistics:

```bash
vcli hitl stats
vcli hitl stats --output json
```

**Output:**
```
HITL Decision Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pending Decisions:
  Total:     12
  Critical:  3
  High:      5
  Medium:    3
  Low:       1

Completed Decisions:
  Approved:  45
  Rejected:  8
  Escalated: 3

Performance Metrics:
  Approval Rate:        84.9%
  Avg Response Time:    12.5 minutes
  Oldest Pending:       45.2 minutes
```

### Watch (Real-Time Monitoring)

Watch for new decisions in real-time:

```bash
# Watch all decisions
vcli hitl watch

# Watch critical only
vcli hitl watch --priority critical
```

**Output:**
```
👁️  Watching for new HITL decisions (priority: critical)...
Press Ctrl+C to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tracking 3 existing decision(s)

[14:45:12] 🚨 NEW DECISION
  Analysis ID:  CANDI-lazarus-007
  Threat Level: APT
  Priority:     critical
  Source IP:    192.168.50.100
  Attribution:  Lazarus Group (89.2% confidence)
  Actions:      block_ip, quarantine_system, escalate_to_soc

[14:47:33] 🚨 NEW DECISION
  Analysis ID:  CANDI-apt29-003
  Threat Level: APT
  Priority:     critical
  Source IP:    10.0.100.50
  Attribution:  APT29 (Cozy Bear) (92.7% confidence)
  Actions:      block_ip, activate_killswitch
```

## Testing

### Prerequisites

1. **HITL Backend Running:**
   ```bash
   cd /home/juan/vertice-dev/backend/services/reactive_fabric_core
   python hitl/hitl_backend.py
   ```

2. **Default Admin Credentials:**
   - Username: `admin`
   - Password: `ChangeMe123!`

### Manual Testing

#### Test 1: System Status

```bash
./bin/vcli hitl status \
  --endpoint http://localhost:8000/api \
  --username admin \
  --password 'ChangeMe123!'
```

**Expected:** Status display with pending counts.

#### Test 2: List Decisions

```bash
./bin/vcli hitl list \
  --endpoint http://localhost:8000/api \
  --username admin \
  --password 'ChangeMe123!'
```

**Expected:** Table of pending decisions (or "No pending decisions").

#### Test 3: Show Decision

First, get an analysis ID from the list, then:

```bash
./bin/vcli hitl show <ANALYSIS_ID> \
  --endpoint http://localhost:8000/api \
  --username admin \
  --password 'ChangeMe123!'
```

**Expected:** Detailed forensic report.

#### Test 4: Approve Decision

```bash
./bin/vcli hitl approve <ANALYSIS_ID> \
  --actions block_ip,quarantine_system \
  --notes "Test approval" \
  --endpoint http://localhost:8000/api \
  --username admin \
  --password 'ChangeMe123!'
```

**Expected:** Approval confirmation.

#### Test 5: Statistics

```bash
./bin/vcli hitl stats \
  --endpoint http://localhost:8000/api \
  --username admin \
  --password 'ChangeMe123!'
```

**Expected:** Decision statistics display.

### Integration Testing

#### Test Scenario: Complete Workflow

1. **Start HITL Backend:**
   ```bash
   cd /home/juan/vertice-dev/backend/services/reactive_fabric_core
   python hitl/hitl_backend.py
   ```

2. **Start CANDI + HITL Integration:**
   ```bash
   python hitl/example_usage.py workflow
   ```

3. **Monitor via vcli (in separate terminal):**
   ```bash
   export HITL_ENDPOINT=http://localhost:8000/api
   export HITL_USERNAME=admin
   export HITL_PASSWORD='ChangeMe123!'

   ./bin/vcli hitl watch --priority critical
   ```

4. **Review and Approve:**
   ```bash
   # List pending
   ./bin/vcli hitl list --priority critical

   # Show details
   ./bin/vcli hitl show <ANALYSIS_ID>

   # Approve
   ./bin/vcli hitl approve <ANALYSIS_ID> --actions block_ip
   ```

## Troubleshooting

### Authentication Failed

**Error:** `authentication failed: request failed with status 401`

**Solution:** Verify credentials. Default admin password is `ChangeMe123!` (with exclamation mark).

### Connection Refused

**Error:** `failed to execute request: dial tcp: connection refused`

**Solution:** Ensure HITL backend is running on `localhost:8000`. Check with:
```bash
curl http://localhost:8000/health
```

### Decision Not Found

**Error:** `decision not found: CANDI-abc123`

**Solution:** Verify analysis ID with `vcli hitl list` first.

## Configuration

### Environment Variables

For convenience, set these in your shell:

```bash
export HITL_ENDPOINT=http://localhost:8000/api
export HITL_USERNAME=admin
export HITL_PASSWORD='ChangeMe123!'
```

Then add to `~/.bashrc` or `~/.zshrc` for persistence.

### Custom Endpoint

For remote HITL instances:

```bash
vcli hitl list --endpoint https://hitl.example.com/api
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        vcli-go                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           cmd/hitl.go (Cobra Commands)             │ │
│  │  - hitl status   - hitl list   - hitl approve     │ │
│  │  - hitl show     - hitl reject - hitl escalate    │ │
│  │  - hitl stats    - hitl watch                     │ │
│  └───────────────────────┬────────────────────────────┘ │
│                          │                              │
│  ┌───────────────────────▼────────────────────────────┐ │
│  │      internal/hitl/client.go (HTTP Client)        │ │
│  │  - Login()          - ListPendingDecisions()      │ │
│  │  - GetDecision()    - MakeDecision()              │ │
│  │  - GetStatus()      - EscalateDecision()          │ │
│  └───────────────────────┬────────────────────────────┘ │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP REST API
                             │ (JWT Authentication)
┌────────────────────────────▼────────────────────────────┐
│           Reactive Fabric Core Service                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │     hitl/hitl_backend.py (FastAPI Backend)        │ │
│  │  - Authentication (JWT + 2FA)                     │ │
│  │  - Decision Management API                        │ │
│  │  - WebSocket Real-Time Alerts                     │ │
│  └───────────────────────┬────────────────────────────┘ │
│                          │                              │
│  ┌───────────────────────▼────────────────────────────┐ │
│  │  hitl/candi_integration.py (Bridge)               │ │
│  │  - Auto-submit HITL-required decisions            │ │
│  │  - Map threat levels to priorities                │ │
│  └───────────────────────┬────────────────────────────┘ │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                    CANDI Core Engine                    │
│  - Threat Analysis                                      │
│  - Attribution                                          │
│  - Forensic Analysis                                    │
└─────────────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ HITL Client (`internal/hitl/client.go`) - **COMPLETE**
2. ✅ vcli Commands (`cmd/hitl.go`) - **COMPLETE**
3. ⏳ Integration Testing - **IN PROGRESS**
4. ⏳ Documentation - **IN PROGRESS**
5. 🔜 WebSocket Support (real-time alerts)
6. 🔜 Config File Support (~/.vcli/hitl.yaml)
7. 🔜 Bash Completion

## License

Part of the Vértice Reactive Fabric system.
