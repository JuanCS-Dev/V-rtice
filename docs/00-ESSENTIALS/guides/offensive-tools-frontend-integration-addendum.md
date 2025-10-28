# Offensive Tools Frontend Integration - Addendum
## MAXIMUS VÉRTICE | New Tools Integration Plan

**Date:** 2025-10-12  
**Phase:** Sprint 2 - Fase 2.2 Frontend Integration  
**Status:** 🎯 **READY TO EXECUTE**  
**Parent Plan:** reactive-fabric-frontend-integration-plan.md

---

## 🆕 NEW OFFENSIVE TOOLS (Day 77)

### Backend Integration Complete ✅
**Service:** `offensive_tools_service:8010`  
**API:** 13 REST endpoints  
**Tests:** 81 passing (100%)

### New Tools Added:
1. **Privilege Escalation** (`/offensive/post-exploit/privilege-escalation`)
2. **Persistence** (`/offensive/post-exploit/persistence`)
3. **Lateral Movement** (`/offensive/post-exploit/lateral-movement`)
4. **Credential Harvesting** (`/offensive/post-exploit/credential-harvest`)
5. **Data Exfiltration** (`/offensive/post-exploit/data-exfiltration`)
6. **Payload Executor** (`/offensive/exploit/execute-payload`)

---

## 🎨 FRONTEND INTEGRATION STRATEGY

### Location
```
frontend/app/offensive/
├── page.tsx (main dashboard - EXISTING)
├── components/
│   ├── ToolSelector.tsx (update with new tools)
│   ├── PostExploitPanel.tsx ⭐ NEW
│   ├── PrivilegeEscalationForm.tsx ⭐ NEW
│   ├── PersistenceForm.tsx ⭐ NEW
│   ├── LateralMovementForm.tsx ⭐ NEW
│   ├── CredentialHarvestForm.tsx ⭐ NEW
│   ├── DataExfiltrationForm.tsx ⭐ NEW
│   └── PayloadExecutorForm.tsx ⭐ NEW
└── hooks/
    └── usePostExploit.js ⭐ NEW
```

### Design Pattern (PAGANI Compliance)
```jsx
// Component Structure
PostExploitPanel.jsx        // Only JSX + orchestration
PostExploitPanel.module.css // 100% design tokens
hooks/usePostExploit.js     // All business logic
```

---

## 📋 IMPLEMENTATION STEPS

### **STEP 1: API Integration Layer (30min)**

#### 1.1 Create API Client
**File:** `frontend/lib/api/offensiveTools.js`

```javascript
/**
 * Offensive Tools API Client
 * Integrates with offensive_tools_service:8010
 */

const BASE_URL = process.env.NEXT_PUBLIC_OFFENSIVE_TOOLS_API || 'http://localhost:8010';

// ============================================================================
// Post-Exploitation APIs
// ============================================================================

export async function privilegeEscalation(params) {
  const response = await fetch(`${BASE_URL}/offensive/post-exploit/privilege-escalation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${params.authToken}`
    },
    body: JSON.stringify({
      target_system: params.targetSystem,
      scan_type: params.scanType || 'comprehensive',
      context: {
        operation_mode: params.operationMode || 'defensive',
        authorization_token: params.authToken,
        target_justification: params.justification
      }
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Privilege escalation failed');
  }
  
  return response.json();
}

export async function establishPersistence(params) {
  const response = await fetch(`${BASE_URL}/offensive/post-exploit/persistence`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${params.authToken}`
    },
    body: JSON.stringify({
      target_platform: params.targetPlatform,
      persistence_type: params.persistenceType,
      stealth_level: params.stealthLevel || 2,
      context: {
        operation_mode: params.operationMode || 'red_team',
        authorization_token: params.authToken,
        target_justification: params.justification
      }
    })
  });
  
  if (!response.ok) throw new Error('Persistence establishment failed');
  return response.json();
}

export async function lateralMovement(params) {
  const response = await fetch(`${BASE_URL}/offensive/post-exploit/lateral-movement`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${params.authToken}`
    },
    body: JSON.stringify({
      source_host: params.sourceHost,
      target_hosts: params.targetHosts,
      method: params.method || 'smb',
      context: {
        operation_mode: params.operationMode || 'red_team',
        authorization_token: params.authToken,
        target_justification: params.justification
      }
    })
  });
  
  if (!response.ok) throw new Error('Lateral movement failed');
  return response.json();
}

export async function harvestCredentials(params) {
  const response = await fetch(`${BASE_URL}/offensive/post-exploit/credential-harvest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${params.authToken}`
    },
    body: JSON.stringify({
      target_system: params.targetSystem,
      harvest_types: params.harvestTypes || ['memory', 'registry', 'files'],
      context: {
        operation_mode: params.operationMode || 'red_team',
        authorization_token: params.authToken,
        target_justification: params.justification
      }
    })
  });
  
  if (!response.ok) throw new Error('Credential harvesting failed');
  return response.json();
}

export async function exfiltrateData(params) {
  const response = await fetch(`${BASE_URL}/offensive/post-exploit/data-exfiltration`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${params.authToken}`
    },
    body: JSON.stringify({
      source_path: params.sourcePath,
      exfil_method: params.exfilMethod || 'https',
      encryption: params.encryption !== false,
      context: {
        operation_mode: params.operationMode || 'red_team',
        authorization_token: params.authToken,
        target_justification: params.justification
      }
    })
  });
  
  if (!response.ok) throw new Error('Data exfiltration failed');
  return response.json();
}

export async function executePayload(params) {
  const response = await fetch(`${BASE_URL}/offensive/exploit/execute-payload`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${params.authToken}`
    },
    body: JSON.stringify({
      payload: params.payload,
      execution_method: params.executionMethod || 'direct',
      target_process: params.targetProcess,
      context: {
        operation_mode: params.operationMode || 'red_team',
        authorization_token: params.authToken,
        target_justification: params.justification
      }
    })
  });
  
  if (!response.ok) throw new Error('Payload execution failed');
  return response.json();
}

// ============================================================================
// Tool Discovery
// ============================================================================

export async function listTools(category = null) {
  const url = category 
    ? `${BASE_URL}/offensive/tools?category=${category}`
    : `${BASE_URL}/offensive/tools`;
    
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to list tools');
  return response.json();
}

export async function getToolInfo(toolName) {
  const response = await fetch(`${BASE_URL}/offensive/tools/${toolName}`);
  if (!response.ok) throw new Error('Tool not found');
  return response.json();
}

export async function getRegistryStats() {
  const response = await fetch(`${BASE_URL}/offensive/registry/stats`);
  if (!response.ok) throw new Error('Failed to get registry stats');
  return response.json();
}
```

---

### **STEP 2: Custom Hook (30min)**

#### 2.1 Create usePostExploit Hook
**File:** `frontend/app/offensive/hooks/usePostExploit.js`

```javascript
/**
 * usePostExploit Hook
 * Manages post-exploitation operations with state management
 */

import { useState, useCallback } from 'react';
import * as offensiveAPI from '@/lib/api/offensiveTools';

export function usePostExploit() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  // =========================================================================
  // Privilege Escalation
  // =========================================================================
  
  const scanPrivilegeEscalation = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await offensiveAPI.privilegeEscalation(params);
      
      setResult(result);
      setHistory(prev => [{
        id: Date.now(),
        tool: 'privilege_escalation',
        timestamp: new Date().toISOString(),
        success: result.success,
        data: result.data
      }, ...prev]);
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================================
  // Persistence
  // =========================================================================
  
  const setupPersistence = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await offensiveAPI.establishPersistence(params);
      
      setResult(result);
      setHistory(prev => [{
        id: Date.now(),
        tool: 'persistence',
        timestamp: new Date().toISOString(),
        success: result.success,
        data: result.data
      }, ...prev]);
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================================
  // Lateral Movement
  // =========================================================================
  
  const executeLateralMovement = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await offensiveAPI.lateralMovement(params);
      
      setResult(result);
      setHistory(prev => [{
        id: Date.now(),
        tool: 'lateral_movement',
        timestamp: new Date().toISOString(),
        success: result.success,
        data: result.data
      }, ...prev]);
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================================
  // Credential Harvesting
  // =========================================================================
  
  const harvestCredentials = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await offensiveAPI.harvestCredentials(params);
      
      setResult(result);
      setHistory(prev => [{
        id: Date.now(),
        tool: 'credential_harvesting',
        timestamp: new Date().toISOString(),
        success: result.success,
        data: result.data,
        sensitive: true // Mark as sensitive
      }, ...prev]);
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================================
  // Data Exfiltration
  // =========================================================================
  
  const exfiltrateData = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await offensiveAPI.exfiltrateData(params);
      
      setResult(result);
      setHistory(prev => [{
        id: Date.now(),
        tool: 'data_exfiltration',
        timestamp: new Date().toISOString(),
        success: result.success,
        data: result.data
      }, ...prev]);
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================================
  // Payload Execution
  // =========================================================================
  
  const executePayload = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await offensiveAPI.executePayload(params);
      
      setResult(result);
      setHistory(prev => [{
        id: Date.now(),
        tool: 'payload_executor',
        timestamp: new Date().toISOString(),
        success: result.success,
        data: result.data
      }, ...prev]);
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================================
  // Utility Functions
  // =========================================================================
  
  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    // State
    loading,
    error,
    result,
    history,
    
    // Actions
    scanPrivilegeEscalation,
    setupPersistence,
    executeLateralMovement,
    harvestCredentials,
    exfiltrateData,
    executePayload,
    
    // Utilities
    clearHistory,
    clearResult
  };
}
```

---

### **STEP 3: UI Components (60-90min)**

#### 3.1 Post-Exploit Panel (Main Container)
**File:** `frontend/app/offensive/components/PostExploitPanel.tsx`

```tsx
/**
 * PostExploitPanel Component
 * Container for all post-exploitation tools
 */

import { useState } from 'react';
import styles from './PostExploitPanel.module.css';
import { usePostExploit } from '../hooks/usePostExploit';
import PrivilegeEscalationForm from './PrivilegeEscalationForm';
import PersistenceForm from './PersistenceForm';
import LateralMovementForm from './LateralMovementForm';
import CredentialHarvestForm from './CredentialHarvestForm';
import DataExfiltrationForm from './DataExfiltrationForm';
import PayloadExecutorForm from './PayloadExecutorForm';
import ResultsViewer from './ResultsViewer';

const TOOLS = [
  { id: 'privilege_escalation', name: 'Privilege Escalation', icon: '⬆️', risk: 'HIGH' },
  { id: 'persistence', name: 'Persistence', icon: '🔒', risk: 'HIGH' },
  { id: 'lateral_movement', name: 'Lateral Movement', icon: '➡️', risk: 'HIGH' },
  { id: 'credential_harvest', name: 'Credential Harvesting', icon: '🔑', risk: 'CRITICAL' },
  { id: 'data_exfiltration', name: 'Data Exfiltration', icon: '📤', risk: 'CRITICAL' },
  { id: 'payload_executor', name: 'Payload Executor', icon: '⚡', risk: 'CRITICAL' }
];

export default function PostExploitPanel() {
  const [activeTool, setActiveTool] = useState(null);
  const postExploit = usePostExploit();

  const renderToolForm = () => {
    switch (activeTool) {
      case 'privilege_escalation':
        return <PrivilegeEscalationForm onExecute={postExploit.scanPrivilegeEscalation} />;
      case 'persistence':
        return <PersistenceForm onExecute={postExploit.setupPersistence} />;
      case 'lateral_movement':
        return <LateralMovementForm onExecute={postExploit.executeLateralMovement} />;
      case 'credential_harvest':
        return <CredentialHarvestForm onExecute={postExploit.harvestCredentials} />;
      case 'data_exfiltration':
        return <DataExfiltrationForm onExecute={postExploit.exfiltrateData} />;
      case 'payload_executor':
        return <PayloadExecutorForm onExecute={postExploit.executePayload} />;
      default:
        return <div className={styles.placeholder}>Select a tool to begin</div>;
    }
  };

  return (
    <div className={styles.panel}>
      {/* Tool Selector */}
      <div className={styles.toolSelector}>
        <h3>Post-Exploitation Arsenal</h3>
        <div className={styles.toolGrid}>
          {TOOLS.map(tool => (
            <button
              key={tool.id}
              className={`${styles.toolCard} ${activeTool === tool.id ? styles.active : ''}`}
              onClick={() => setActiveTool(tool.id)}
            >
              <span className={styles.toolIcon}>{tool.icon}</span>
              <span className={styles.toolName}>{tool.name}</span>
              <span className={`${styles.riskBadge} ${styles[tool.risk.toLowerCase()]}`}>
                {tool.risk}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Tool Form */}
      <div className={styles.toolForm}>
        {renderToolForm()}
      </div>

      {/* Results */}
      {postExploit.result && (
        <div className={styles.results}>
          <ResultsViewer 
            result={postExploit.result} 
            onClear={postExploit.clearResult}
          />
        </div>
      )}

      {/* History Sidebar */}
      <div className={styles.history}>
        <h4>Operation History</h4>
        {postExploit.history.map(entry => (
          <div key={entry.id} className={styles.historyEntry}>
            <span className={styles.historyTool}>{entry.tool}</span>
            <span className={styles.historyTime}>
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span className={`${styles.historyStatus} ${entry.success ? styles.success : styles.failure}`}>
              {entry.success ? '✅' : '❌'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 3.2 CSS Module
**File:** `frontend/app/offensive/components/PostExploitPanel.module.css`

```css
.panel {
  display: grid;
  grid-template-columns: 300px 1fr 250px;
  grid-template-rows: auto 1fr;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--bg-primary);
  min-height: 100vh;
}

.toolSelector {
  grid-row: 1 / -1;
  padding: var(--space-4);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.toolSelector h3 {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-lg);
  margin-bottom: var(--space-4);
}

.toolGrid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.toolCard {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}

.toolCard:hover {
  background: var(--bg-hover);
  border-color: var(--color-cyber-primary);
  transform: translateX(var(--space-1));
}

.toolCard.active {
  background: var(--color-cyber-primary);
  border-color: var(--color-cyber-bright);
  color: var(--bg-primary);
}

.toolIcon {
  font-size: var(--text-2xl);
}

.toolName {
  flex: 1;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.riskBadge {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
}

.riskBadge.high {
  background: var(--color-warning);
  color: var(--bg-primary);
}

.riskBadge.critical {
  background: var(--color-critical);
  color: var(--text-primary);
}

/* Tool Form Area */
.toolForm {
  padding: var(--space-6);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

/* Results */
.results {
  grid-column: 2;
  padding: var(--space-6);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-success);
}

/* History Sidebar */
.history {
  grid-row: 1 / -1;
  padding: var(--space-4);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  max-height: 100vh;
  overflow-y: auto;
}

.history h4 {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-base);
  margin-bottom: var(--space-3);
}

.historyEntry {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
}

.historyTool {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.historyTime {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.historyStatus.success {
  color: var(--color-success);
}

.historyStatus.failure {
  color: var(--color-critical);
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: var(--text-lg);
}
```

---

### **STEP 4: Individual Tool Forms (30min each)**

**Note:** Each form follows the same pattern. Example for Privilege Escalation:

#### 4.1 Privilege Escalation Form
**File:** `frontend/app/offensive/components/PrivilegeEscalationForm.tsx`

```tsx
import { useState } from 'react';
import styles from './ToolForm.module.css';
import Button from '@/components/shared/Button/Button';
import Input from '@/components/shared/Input/Input';
import Alert from '@/components/shared/Alert/Alert';

export default function PrivilegeEscalationForm({ onExecute }) {
  const [formData, setFormData] = useState({
    targetSystem: '',
    scanType: 'comprehensive',
    authToken: '',
    justification: '',
    operationMode: 'defensive'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.authToken) {
      setError('Authorization token required for high-risk operation');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await onExecute(formData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <h3 className={styles.title}>⬆️ Privilege Escalation Scan</h3>
      
      {error && <Alert type="error">{error}</Alert>}
      
      <Input
        label="Target System"
        value={formData.targetSystem}
        onChange={(e) => setFormData({...formData, targetSystem: e.target.value})}
        placeholder="IP or hostname"
        required
      />
      
      <div className={styles.field}>
        <label>Scan Type</label>
        <select
          value={formData.scanType}
          onChange={(e) => setFormData({...formData, scanType: e.target.value})}
          className={styles.select}
        >
          <option value="quick">Quick (common vectors)</option>
          <option value="comprehensive">Comprehensive (all techniques)</option>
        </select>
      </div>
      
      <div className={styles.field}>
        <label>Operation Mode</label>
        <select
          value={formData.operationMode}
          onChange={(e) => setFormData({...formData, operationMode: e.target.value})}
          className={styles.select}
        >
          <option value="defensive">Defensive (audit)</option>
          <option value="research">Research</option>
          <option value="red_team">Red Team</option>
        </select>
      </div>
      
      <Input
        label="Authorization Token"
        type="password"
        value={formData.authToken}
        onChange={(e) => setFormData({...formData, authToken: e.target.value})}
        placeholder="Required for execution"
        required
      />
      
      <Input
        label="Justification"
        value={formData.justification}
        onChange={(e) => setFormData({...formData, justification: e.target.value})}
        placeholder="Reason for this operation"
        required
      />
      
      <Button
        type="submit"
        variant="danger"
        loading={loading}
        fullWidth
      >
        Execute Scan
      </Button>
    </form>
  );
}
```

---

## ⏱️ TIMELINE & ESTIMATES

| Step | Task | Time | Status |
|------|------|------|--------|
| 1 | API Integration Layer | 30min | ⚪ Pending |
| 2 | Custom Hook | 30min | ⚪ Pending |
| 3 | Post-Exploit Panel | 60min | ⚪ Pending |
| 4.1 | Privilege Escalation Form | 30min | ⚪ Pending |
| 4.2 | Persistence Form | 30min | ⚪ Pending |
| 4.3 | Lateral Movement Form | 30min | ⚪ Pending |
| 4.4 | Credential Harvest Form | 30min | ⚪ Pending |
| 4.5 | Data Exfiltration Form | 30min | ⚪ Pending |
| 4.6 | Payload Executor Form | 30min | ⚪ Pending |
| 5 | Results Viewer Component | 20min | ⚪ Pending |
| 6 | Integration with OffensiveDashboard | 30min | ⚪ Pending |
| 7 | Testing & Polish | 30min | ⚪ Pending |

**Total Estimated Time:** 4-5 hours

---

## 🎯 ACCEPTANCE CRITERIA

- [ ] All 6 tools accessible from Offensive Dashboard
- [ ] Authorization token validation working
- [ ] Results display with proper formatting
- [ ] Operation history tracking
- [ ] Error handling with user-friendly messages
- [ ] PAGANI design compliance (100% CSS tokens)
- [ ] Responsive layout (mobile-friendly)
- [ ] Accessibility (keyboard navigation, ARIA labels)
- [ ] Loading states and progress indicators
- [ ] Export functionality (JSON/PDF)

---

## 🔐 SECURITY CONSIDERATIONS

1. **Authorization Tokens**
   - Never store tokens in localStorage
   - Use sessionStorage with short expiry
   - Validate token format before submission

2. **Sensitive Data**
   - Mark credential harvest results as sensitive
   - Implement data masking in UI
   - Provide clear export warnings

3. **Audit Trail**
   - Log all high-risk operations
   - Include justification in logs
   - Timestamp with millisecond precision

---

## 🚀 READY TO EXECUTE

All backend dependencies satisfied. Frontend integration can begin immediately.

**Next Command:** Start with Step 1 (API Integration Layer)

---

*Addendum to reactive-fabric-frontend-integration-plan.md*  
*MAXIMUS Session | Day 77 | PAGANI Compliance ✅*
