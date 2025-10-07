/**
 * Offensive Workflow Integration Tests
 * =====================================
 *
 * End-to-end integration tests for Red Team operations:
 * - Network reconnaissance workflow
 * - Vulnerability scanning workflow
 * - Attack simulation workflow
 * - C2 orchestration workflow
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { waitFor } from '@testing-library/react';
import * as offensiveServices from '../../api/offensiveServices';

// Mock fetch globally
global.fetch = vi.fn();

describe('Offensive Workflow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('Network Reconnaissance Workflow', () => {
    it('should complete full recon workflow: scan → parse → analyze', async () => {
      // Step 1: Start network scan
      const scanResponse = {
        scan_id: 'scan_12345',
        status: 'running',
        target: '192.168.1.0/24',
        scan_type: 'full'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => scanResponse
      });

      const scan = await offensiveServices.startNmapScan('192.168.1.0/24', 'full');
      expect(scan.scan_id).toBe('scan_12345');
      expect(scan.status).toBe('running');

      // Step 2: Check scan status
      const statusResponse = {
        scan_id: 'scan_12345',
        status: 'completed',
        progress: 100,
        hosts_discovered: 15,
        ports_found: 48
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => statusResponse
      });

      const status = await offensiveServices.getScanStatus('scan_12345');
      expect(status.status).toBe('completed');
      expect(status.hosts_discovered).toBe(15);

      // Step 3: Get scan results
      const resultsResponse = {
        scan_id: 'scan_12345',
        hosts: [
          {
            ip: '192.168.1.10',
            hostname: 'server1.local',
            open_ports: [22, 80, 443],
            os: 'Linux 5.x',
            services: [
              { port: 22, service: 'ssh', version: 'OpenSSH 8.2' },
              { port: 80, service: 'http', version: 'nginx 1.18' }
            ]
          }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => resultsResponse
      });

      const results = await offensiveServices.getScanResults('scan_12345');
      expect(results.hosts).toHaveLength(1);
      expect(results.hosts[0].open_ports).toContain(22);
    });

    it('should complete masscan workflow for large networks', async () => {
      const masscanResponse = {
        scan_id: 'mass_99999',
        target: '10.0.0.0/16',
        ports: '1-65535',
        rate: 10000,
        status: 'running'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => masscanResponse
      });

      const scan = await offensiveServices.startMasscan('10.0.0.0/16', '1-65535');
      expect(scan.scan_id).toBe('mass_99999');
      expect(scan.rate).toBe(10000);
    });
  });

  describe('Vulnerability Intelligence Workflow', () => {
    it('should complete vuln scan workflow: discover → correlate → exploit', async () => {
      // Step 1: Start vulnerability scan
      const scanResponse = {
        scan_id: 'vuln_001',
        target: '192.168.1.10',
        templates: ['cves', 'misconfigs'],
        status: 'running'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => scanResponse
      });

      const scan = await offensiveServices.startVulnScan('192.168.1.10', ['cves', 'misconfigs']);
      expect(scan.scan_id).toBe('vuln_001');

      // Step 2: Get vulnerabilities found
      const vulnResponse = {
        scan_id: 'vuln_001',
        vulnerabilities: [
          {
            cve: 'CVE-2024-1234',
            severity: 'critical',
            cvss: 9.8,
            service: 'OpenSSH 7.4',
            exploit_available: true
          },
          {
            cve: 'CVE-2024-5678',
            severity: 'high',
            cvss: 7.5,
            service: 'nginx 1.14',
            exploit_available: false
          }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => vulnResponse
      });

      const vulns = await offensiveServices.getVulnResults('vuln_001');
      expect(vulns.vulnerabilities).toHaveLength(2);
      expect(vulns.vulnerabilities[0].exploit_available).toBe(true);

      // Step 3: Correlate with CVE database
      const cveResponse = {
        cve: 'CVE-2024-1234',
        description: 'Remote code execution in OpenSSH',
        references: ['https://nvd.nist.gov/vuln/detail/CVE-2024-1234'],
        exploits: [
          { name: 'exploit_001', reliability: 'excellent' }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => cveResponse
      });

      const cveDetails = await offensiveServices.getCVEDetails('CVE-2024-1234');
      expect(cveDetails.exploits).toHaveLength(1);
    });
  });

  describe('Web Attack Workflow', () => {
    it('should complete web attack workflow: crawl → scan → exploit', async () => {
      // Step 1: Start web scan with ZAP
      const zapResponse = {
        scan_id: 'zap_123',
        target: 'https://target.example.com',
        scan_type: 'active',
        status: 'running'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => zapResponse
      });

      const zapScan = await offensiveServices.startZAPScan('https://target.example.com', 'active');
      expect(zapScan.scan_id).toBe('zap_123');

      // Step 2: Get ZAP results
      const zapResultsResponse = {
        scan_id: 'zap_123',
        alerts: [
          { risk: 'High', name: 'SQL Injection', url: 'https://target.example.com/login' },
          { risk: 'Medium', name: 'XSS Reflected', url: 'https://target.example.com/search' }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => zapResultsResponse
      });

      const zapResults = await offensiveServices.getZAPResults('zap_123');
      expect(zapResults.alerts).toHaveLength(2);

      // Step 3: Start Burp Suite scan
      const burpResponse = {
        scan_id: 'burp_456',
        target: 'https://target.example.com',
        status: 'running'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => burpResponse
      });

      const burpScan = await offensiveServices.startBurpScan('https://target.example.com');
      expect(burpScan.scan_id).toBe('burp_456');
    });
  });

  describe('C2 Orchestration Workflow', () => {
    it('should complete C2 workflow: listener → payload → session', async () => {
      // Step 1: Start listener
      const listenerResponse = {
        listener_id: 'listener_001',
        type: 'http',
        host: '0.0.0.0',
        port: 8080,
        status: 'active'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => listenerResponse
      });

      const listener = await offensiveServices.startListener('http', { port: 8080 });
      expect(listener.listener_id).toBe('listener_001');
      expect(listener.status).toBe('active');

      // Step 2: Generate payload
      const payloadResponse = {
        payload_id: 'payload_001',
        type: 'windows/meterpreter/reverse_https',
        format: 'exe',
        lhost: '192.168.1.100',
        lport: 8080,
        file_path: '/tmp/payload.exe'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => payloadResponse
      });

      const payload = await offensiveServices.generatePayload('windows/meterpreter/reverse_https', {
        lhost: '192.168.1.100',
        lport: 8080
      });
      expect(payload.payload_id).toBe('payload_001');

      // Step 3: List active sessions
      const sessionsResponse = {
        sessions: [
          {
            session_id: 'session_001',
            type: 'meterpreter',
            target: '192.168.1.50',
            username: 'SYSTEM',
            os: 'Windows 10',
            established_at: '2024-03-22T10:30:00Z'
          }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => sessionsResponse
      });

      const sessions = await offensiveServices.listSessions();
      expect(sessions.sessions).toHaveLength(1);
      expect(sessions.sessions[0].username).toBe('SYSTEM');
    });

    it('should execute command in C2 session', async () => {
      const cmdResponse = {
        session_id: 'session_001',
        command: 'sysinfo',
        output: 'Computer: WIN-SERVER01\nOS: Windows Server 2019\nArchitecture: x64'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => cmdResponse
      });

      const result = await offensiveServices.executeCommand('session_001', 'sysinfo');
      expect(result.output).toContain('Windows Server 2019');
    });
  });

  describe('BAS (Breach & Attack Simulation) Workflow', () => {
    it('should complete BAS workflow: select technique → execute → measure detection', async () => {
      // Step 1: Get available MITRE ATT&CK techniques
      const techniquesResponse = {
        techniques: [
          { id: 'T1078', name: 'Valid Accounts', tactic: 'Initial Access' },
          { id: 'T1059', name: 'Command and Scripting Interpreter', tactic: 'Execution' }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => techniquesResponse
      });

      const techniques = await offensiveServices.getTechniques();
      expect(techniques.techniques).toHaveLength(2);

      // Step 2: Execute technique
      const execResponse = {
        execution_id: 'exec_001',
        technique_id: 'T1059',
        status: 'running',
        started_at: '2024-03-22T11:00:00Z'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => execResponse
      });

      const execution = await offensiveServices.executeTechnique('T1059', {
        target: '192.168.1.50'
      });
      expect(execution.execution_id).toBe('exec_001');

      // Step 3: Get execution results
      const resultsResponse = {
        execution_id: 'exec_001',
        technique_id: 'T1059',
        status: 'completed',
        detected: true,
        detection_time_seconds: 12,
        detection_tools: ['EDR', 'SIEM']
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => resultsResponse
      });

      const results = await offensiveServices.getExecutionResults('exec_001');
      expect(results.detected).toBe(true);
      expect(results.detection_tools).toContain('EDR');
    });

    it('should generate purple team report', async () => {
      const reportResponse = {
        report_id: 'report_001',
        techniques_tested: 15,
        techniques_detected: 12,
        coverage_percentage: 80,
        gaps: [
          { technique: 'T1078', reason: 'No detection rule' },
          { technique: 'T1547', reason: 'Low confidence detection' }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => reportResponse
      });

      const report = await offensiveServices.generateReport();
      expect(report.coverage_percentage).toBe(80);
      expect(report.gaps).toHaveLength(2);
    });
  });

  describe('Cross-Service Integration Workflows', () => {
    it('should complete full kill chain workflow', async () => {
      // 1. Reconnaissance
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ scan_id: 'scan_001', status: 'running' })
      });

      const recon = await offensiveServices.startNmapScan('192.168.1.0/24', 'full');

      // 2. Vulnerability Scanning
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ scan_id: 'vuln_001', status: 'running' })
      });

      const vulnScan = await offensiveServices.startVulnScan('192.168.1.10', ['cves']);

      // 3. Exploitation (C2)
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ payload_id: 'payload_001' })
      });

      const payload = await offensiveServices.generatePayload('windows/meterpreter/reverse_https', {});

      // 4. Post-Exploitation
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [{ session_id: 'session_001' }] })
      });

      const sessions = await offensiveServices.listSessions();

      // Verify complete workflow
      expect(recon.scan_id).toBe('scan_001');
      expect(vulnScan.scan_id).toBe('vuln_001');
      expect(payload.payload_id).toBe('payload_001');
      expect(sessions.sessions).toHaveLength(1);
    });
  });

  describe('Error Handling and Resilience', () => {
    it('should handle service unavailability', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable'
      });

      await expect(
        offensiveServices.startNmapScan('192.168.1.0/24', 'full')
      ).rejects.toThrow();
    });

    it('should handle authentication failures', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized'
      });

      await expect(
        offensiveServices.listSessions()
      ).rejects.toThrow();
    });

    it('should handle network timeouts', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network timeout'));

      await expect(
        offensiveServices.getTechniques()
      ).rejects.toThrow('Network timeout');
    });
  });
});
