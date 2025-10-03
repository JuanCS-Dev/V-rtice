"""
Detection Engine - Advanced threat detection with ML capabilities
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from ..models import (
    ThreatDetection,
    ThreatIndicator,
    MITRETechnique,
    SeverityLevel,
    ThreatType,
    DetectionSource,
    AnalysisRequest,
    AnalysisResult
)

logger = logging.getLogger(__name__)


class DetectionEngine:
    """
    Advanced Detection Engine with ML capabilities

    Features:
    - Multi-layer detection (signature, heuristic, behavioral, ML)
    - MITRE ATT&CK mapping
    - Threat scoring and severity calculation
    - False positive reduction
    - Real-time and batch analysis
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.workers = config.get('workers', 4)

        # Detection components
        self.signature_db = {}
        self.yara_rules = []
        self.ml_model = None
        self.behavioral_analyzer = None

        # Statistics
        self.stats = {
            'total_analyses': 0,
            'total_detections': 0,
            'detections_by_type': {},
            'detections_by_severity': {},
            'avg_analysis_time_ms': 0
        }

        logger.info(f"Initialized Detection Engine with {self.workers} workers")

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Main analysis entry point

        Args:
            request: Analysis request with type and target

        Returns:
            Analysis result with detected threats
        """
        start_time = datetime.utcnow()
        detections = []
        errors = []

        try:
            if request.analysis_type == 'file':
                detections = await self.analyze_file(request.target, request.options)
            elif request.analysis_type == 'network':
                detections = await self.analyze_network(request.target, request.options)
            elif request.analysis_type == 'process':
                detections = await self.analyze_process(request.target, request.options)
            elif request.analysis_type == 'memory':
                detections = await self.analyze_memory(request.target, request.options)
            elif request.analysis_type == 'behavior':
                detections = await self.analyze_behavior(request.target, request.options)
            else:
                errors.append(f"Unknown analysis type: {request.analysis_type}")

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            errors.append(str(e))

        # Calculate execution time
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Update statistics
        self.stats['total_analyses'] += 1
        self.stats['total_detections'] += len(detections)
        for detection in detections:
            threat_type = detection.threat_type.value
            severity = detection.severity.value
            self.stats['detections_by_type'][threat_type] = \
                self.stats['detections_by_type'].get(threat_type, 0) + 1
            self.stats['detections_by_severity'][severity] = \
                self.stats['detections_by_severity'].get(severity, 0) + 1

        # Update average analysis time
        total = self.stats['total_analyses']
        current_avg = self.stats['avg_analysis_time_ms']
        self.stats['avg_analysis_time_ms'] = \
            (current_avg * (total - 1) + execution_time_ms) / total

        # Build result
        result = AnalysisResult(
            request_id=request.request_id,
            analysis_type=request.analysis_type,
            status='completed' if not errors else 'failed' if not detections else 'partial',
            detections=detections,
            execution_time_ms=execution_time_ms,
            errors=errors,
            summary={
                'total_detections': len(detections),
                'highest_severity': self._get_highest_severity(detections),
                'threat_types': list(set([d.threat_type.value for d in detections])),
                'max_score': max([d.score for d in detections]) if detections else 0
            }
        )

        logger.info(
            f"Analysis completed: {request.analysis_type} - "
            f"{len(detections)} detections in {execution_time_ms}ms"
        )

        return result

    async def analyze_file(
        self,
        file_path: str,
        options: Dict[str, Any]
    ) -> List[ThreatDetection]:
        """
        Analyze file for malware

        Detection layers:
        1. Hash-based signature matching
        2. YARA rule scanning
        3. PE/ELF header analysis
        4. String analysis
        5. ML-based classification
        """
        detections = []

        try:
            # Layer 1: Hash signature
            file_hash = await self._calculate_file_hash(file_path)
            if signature := self.signature_db.get(file_hash):
                detection = self._create_detection_from_signature(
                    file_hash,
                    signature,
                    file_path
                )
                detections.append(detection)

            # Layer 2: YARA rules
            yara_matches = await self._scan_with_yara(file_path)
            for match in yara_matches:
                detection = self._create_detection_from_yara(match, file_path)
                detections.append(detection)

            # Layer 3: Static analysis
            static_threats = await self._static_file_analysis(file_path)
            detections.extend(static_threats)

            # Layer 4: ML classification
            if self.ml_model:
                ml_result = await self._ml_classify_file(file_path)
                if ml_result and ml_result['is_malicious']:
                    detection = self._create_detection_from_ml(ml_result, file_path)
                    detections.append(detection)

        except Exception as e:
            logger.error(f"File analysis error for {file_path}: {e}")

        return detections

    async def analyze_network(
        self,
        target: str,
        options: Dict[str, Any]
    ) -> List[ThreatDetection]:
        """
        Analyze network traffic/connection

        Detects:
        - C2 communication patterns
        - Data exfiltration
        - Port scanning
        - DDoS traffic
        - Malicious protocols
        """
        detections = []

        try:
            # Parse network target (IP:port, pcap file, etc.)
            parsed = self._parse_network_target(target)

            # Analyze connection patterns
            if 'ip' in parsed:
                conn_threats = await self._analyze_connection_patterns(parsed)
                detections.extend(conn_threats)

            # Check for C2 indicators
            c2_threats = await self._detect_c2_communication(parsed)
            detections.extend(c2_threats)

            # Protocol analysis
            protocol_threats = await self._analyze_protocols(parsed)
            detections.extend(protocol_threats)

        except Exception as e:
            logger.error(f"Network analysis error for {target}: {e}")

        return detections

    async def analyze_process(
        self,
        target: str,
        options: Dict[str, Any]
    ) -> List[ThreatDetection]:
        """
        Analyze running process

        Detects:
        - Process injection
        - Privilege escalation
        - Suspicious parent-child relationships
        - Abnormal resource usage
        - Known malicious processes
        """
        detections = []

        try:
            # Parse process target (PID, name, etc.)
            parsed = self._parse_process_target(target)

            # Check process reputation
            rep_threats = await self._check_process_reputation(parsed)
            detections.extend(rep_threats)

            # Analyze process behavior
            behavior_threats = await self._analyze_process_behavior(parsed)
            detections.extend(behavior_threats)

            # Check for injection
            injection_threats = await self._detect_process_injection(parsed)
            detections.extend(injection_threats)

        except Exception as e:
            logger.error(f"Process analysis error for {target}: {e}")

        return detections

    async def analyze_memory(
        self,
        target: str,
        options: Dict[str, Any]
    ) -> List[ThreatDetection]:
        """
        Analyze memory dump

        Detects:
        - Memory-resident malware
        - Rootkits
        - Shellcode
        - Injected code
        """
        detections = []

        try:
            # Memory pattern matching
            pattern_threats = await self._scan_memory_patterns(target)
            detections.extend(pattern_threats)

            # Shellcode detection
            shellcode_threats = await self._detect_shellcode(target)
            detections.extend(shellcode_threats)

        except Exception as e:
            logger.error(f"Memory analysis error for {target}: {e}")

        return detections

    async def analyze_behavior(
        self,
        target: str,
        options: Dict[str, Any]
    ) -> List[ThreatDetection]:
        """
        Behavioral analysis

        Detects:
        - LOTL (Living Off The Land) techniques
        - Anomalous user behavior
        - Lateral movement
        - Persistence mechanisms
        """
        detections = []

        try:
            # Parse behavioral data
            behavior_data = options.get('behavior_data', {})

            # Detect LOTL techniques
            lotl_threats = await self._detect_lotl(behavior_data)
            detections.extend(lotl_threats)

            # Anomaly detection
            anomaly_threats = await self._detect_anomalies(behavior_data)
            detections.extend(anomaly_threats)

            # MITRE ATT&CK mapping
            for detection in detections:
                detection.mitre_techniques = self._map_to_mitre(detection)

        except Exception as e:
            logger.error(f"Behavioral analysis error: {e}")

        return detections

    # ========== Helper Methods ==========

    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    async def _scan_with_yara(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan file with YARA rules"""
        # Placeholder - integrate with actual YARA
        return []

    async def _static_file_analysis(self, file_path: str) -> List[ThreatDetection]:
        """Perform static analysis on file"""
        # Placeholder - implement PE/ELF analysis, entropy, etc.
        return []

    async def _ml_classify_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Classify file using ML model"""
        # Placeholder - integrate with ML engine
        return None

    def _create_detection_from_signature(
        self,
        file_hash: str,
        signature: Dict[str, Any],
        file_path: str
    ) -> ThreatDetection:
        """Create detection from signature match"""
        detection_id = hashlib.sha256(
            f"{file_hash}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        return ThreatDetection(
            detection_id=detection_id,
            severity=SeverityLevel(signature.get('severity', 'high')),
            threat_type=ThreatType(signature.get('type', 'malware')),
            confidence=0.95,
            score=signature.get('score', 85),
            source=DetectionSource.SIGNATURE_MATCH,
            source_details={'signature_name': signature.get('name')},
            title=f"Malware detected: {signature.get('name')}",
            description=f"File {file_path} matches known malware signature",
            indicators=[
                ThreatIndicator(
                    type='hash',
                    value=file_hash,
                    confidence=0.95,
                    source=DetectionSource.SIGNATURE_MATCH
                )
            ],
            affected_assets=[file_path],
            evidence={'file_hash': file_hash, 'signature': signature}
        )

    def _create_detection_from_yara(
        self,
        match: Dict[str, Any],
        file_path: str
    ) -> ThreatDetection:
        """Create detection from YARA match"""
        detection_id = hashlib.sha256(
            f"{file_path}:{match['rule']}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        return ThreatDetection(
            detection_id=detection_id,
            severity=SeverityLevel.HIGH,
            threat_type=ThreatType.MALWARE,
            confidence=0.85,
            score=75,
            source=DetectionSource.SIGNATURE_MATCH,
            source_details={'yara_rule': match['rule']},
            title=f"YARA rule matched: {match['rule']}",
            description=f"File {file_path} matched YARA rule {match['rule']}",
            affected_assets=[file_path],
            evidence={'yara_match': match}
        )

    def _create_detection_from_ml(
        self,
        ml_result: Dict[str, Any],
        file_path: str
    ) -> ThreatDetection:
        """Create detection from ML classification"""
        detection_id = hashlib.sha256(
            f"{file_path}:ml:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        score = int(ml_result['confidence'] * 100)
        severity = self._calculate_severity(score)

        return ThreatDetection(
            detection_id=detection_id,
            severity=severity,
            threat_type=ThreatType(ml_result.get('threat_type', 'unknown')),
            confidence=ml_result['confidence'],
            score=score,
            source=DetectionSource.ML_MODEL,
            source_details={'model': ml_result.get('model_name')},
            title=f"ML detected: {ml_result.get('threat_name', 'Unknown threat')}",
            description=f"ML model classified {file_path} as malicious",
            affected_assets=[file_path],
            evidence={'ml_result': ml_result},
            false_positive_likelihood=ml_result.get('fp_likelihood', 0.1)
        )

    def _calculate_severity(self, score: int) -> SeverityLevel:
        """Calculate severity from threat score"""
        if score >= 80:
            return SeverityLevel.CRITICAL
        elif score >= 60:
            return SeverityLevel.HIGH
        elif score >= 40:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    def _get_highest_severity(self, detections: List[ThreatDetection]) -> str:
        """Get highest severity from list of detections"""
        if not detections:
            return 'none'

        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        for sev in severity_order:
            if any(d.severity.value == sev for d in detections):
                return sev
        return 'info'

    def _map_to_mitre(self, detection: ThreatDetection) -> List[MITRETechnique]:
        """Map detection to MITRE ATT&CK techniques"""
        # Placeholder - implement MITRE mapping logic
        return []

    def _parse_network_target(self, target: str) -> Dict[str, Any]:
        """Parse network target string"""
        # Placeholder
        return {}

    def _parse_process_target(self, target: str) -> Dict[str, Any]:
        """Parse process target string"""
        # Placeholder
        return {}

    async def _analyze_connection_patterns(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Analyze network connection patterns"""
        return []

    async def _detect_c2_communication(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Detect C2 communication"""
        return []

    async def _analyze_protocols(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Analyze network protocols"""
        return []

    async def _check_process_reputation(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Check process reputation"""
        return []

    async def _analyze_process_behavior(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Analyze process behavior"""
        return []

    async def _detect_process_injection(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Detect process injection"""
        return []

    async def _scan_memory_patterns(self, target: str) -> List[ThreatDetection]:
        """Scan memory for malicious patterns"""
        return []

    async def _detect_shellcode(self, target: str) -> List[ThreatDetection]:
        """Detect shellcode in memory"""
        return []

    async def _detect_lotl(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Detect Living Off The Land techniques"""
        return []

    async def _detect_anomalies(self, data: Dict[str, Any]) -> List[ThreatDetection]:
        """Detect behavioral anomalies"""
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get detection engine statistics"""
        return self.stats.copy()
