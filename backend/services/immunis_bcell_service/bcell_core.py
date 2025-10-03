"""
Immunis - B Cell Service
========================
Antibody production and memory formation.

Biological inspiration: B Lymphocytes
- Recognize specific antigens via BCR (B Cell Receptor)
- Clonal selection and expansion
- Differentiate into plasma cells (antibody factories)
- Affinity maturation (somatic hypermutation)
- Memory B cells (long-lived immunity)
- Antibody isotype switching (IgM → IgG)

Computational implementation:
- Signature generation from antigens (YARA, Snort, Suricata)
- A/B testing for signature quality (affinity maturation)
- Clonal expansion (deploy signatures to all sensors)
- Memory storage (signature database)
- Version control (antibody isotypes)
- Feedback loop (test → improve → redeploy)
"""

import logging
import time
import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AntibodyIsotype(str, Enum):
    """
    Antibody classes (isotypes).

    Biological: IgM, IgG, IgA, IgE, IgD
    Computational: Signature types
    """
    IGM = "igm"  # Early response, low specificity (generic patterns)
    IGG = "igg"  # Mature response, high specificity (precise signatures)
    IGA = "iga"  # Mucosal immunity (network-level detection)
    IGE = "ige"  # Allergic response (high sensitivity, many false positives)


class SignatureType(str, Enum):
    """Signature format types"""
    YARA = "yara"
    SNORT = "snort"
    SURICATA = "suricata"
    SIGMA = "sigma"  # Log detection
    CUSTOM = "custom"


class AffinityLevel(str, Enum):
    """Signature quality (affinity)"""
    LOW = "low"  # Many false positives
    MEDIUM = "medium"
    HIGH = "high"  # Few false positives
    VERY_HIGH = "very_high"  # Zero false positives


@dataclass
class Antibody:
    """
    Antibody (signature/rule).

    Like biological antibodies that bind specific antigens,
    these are detection signatures that match specific threats.
    """
    antibody_id: str
    antigen_id: str  # What antigen this was generated from
    isotype: AntibodyIsotype
    signature_type: SignatureType

    # The actual signature
    signature_content: str

    # Metadata
    malware_family: str
    severity: str
    version: int  # For affinity maturation
    affinity: AffinityLevel

    # Test results
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    # Deployment
    deployed: bool = False
    deployed_at: Optional[float] = None

    created_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """F1 = 2 * (precision * recall) / (precision + recall)"""
        p = self.precision
        r = self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


@dataclass
class MemoryBCell:
    """
    Memory B cell - long-lived immune memory.

    Stores successful antibodies for rapid recall.
    """
    memory_id: str
    antibody: Antibody
    recall_count: int = 0
    last_recalled: Optional[float] = None
    half_life_days: int = 365  # How long memory lasts


@dataclass
class ClonalExpansion:
    """
    Clonal expansion event.

    Successful antibody is replicated and deployed widely.
    """
    expansion_id: str
    parent_antibody: Antibody
    clone_count: int
    deployment_targets: List[str]  # Sensors, agents, firewalls
    started_at: float
    completed_at: Optional[float] = None
    success: bool = False


class BCellCore:
    """
    B Cell - Antibody production and memory.

    Lifecycle:
    1. Naive B cell receives antigen from DC
    2. BCR recognizes antigen
    3. Clonal selection (generate candidate signatures)
    4. Affinity maturation (test and improve signatures)
    5. Differentiate to plasma cell (deploy signature)
    6. Clonal expansion (deploy to all sensors)
    7. Memory formation (store for future)

    Key processes:
    - Signature generation (YARA, Snort, etc.)
    - A/B testing (somatic hypermutation)
    - Quality metrics (precision, recall)
    - Version control (isotype switching)
    - Deployment automation
    """

    def __init__(
        self,
        bcell_id: str,
        signature_types: List[SignatureType] = None,
        min_affinity: AffinityLevel = AffinityLevel.MEDIUM
    ):
        self.bcell_id = bcell_id
        self.signature_types = signature_types or [SignatureType.YARA, SignatureType.SNORT]
        self.min_affinity = min_affinity

        # Antibody production
        self.antibodies: Dict[str, Antibody] = {}

        # Memory storage
        self.memory_cells: Dict[str, MemoryBCell] = {}

        # Clonal expansions
        self.expansions: List[ClonalExpansion] = []

        # Statistics
        self.stats = {
            "antibodies_generated": 0,
            "high_affinity_antibodies": 0,
            "deployed_antibodies": 0,
            "memory_cells_formed": 0,
            "clonal_expansions": 0,
            "avg_precision": 0.0,
            "avg_recall": 0.0
        }

        logger.info(
            f"B Cell {bcell_id} initialized "
            f"(signature_types={[st.value for st in self.signature_types]}, "
            f"min_affinity={min_affinity.value})"
        )

    async def generate_antibodies(
        self,
        antigen: Dict,
        cytokine_signal: Optional[Dict] = None
    ) -> List[Antibody]:
        """
        Generate antibodies from antigen.

        Biological: BCR binds antigen → clonal selection → antibody production
        Computational: Generate signatures from malware features

        Args:
            antigen: Processed antigen from dendritic cell
            cytokine_signal: IL-4 signal (promotes B cell activation)

        Returns:
            List of generated antibodies
        """
        logger.info(
            f"[{self.bcell_id}] Generating antibodies for antigen {antigen.get('antigen_id')}"
        )

        antibodies = []

        # Generate different signature types
        for sig_type in self.signature_types:
            if sig_type == SignatureType.YARA:
                antibody = self._generate_yara_signature(antigen)
            elif sig_type == SignatureType.SNORT:
                antibody = self._generate_snort_signature(antigen)
            elif sig_type == SignatureType.SURICATA:
                antibody = self._generate_suricata_signature(antigen)
            elif sig_type == SignatureType.SIGMA:
                antibody = self._generate_sigma_signature(antigen)
            else:
                continue

            if antibody:
                antibodies.append(antibody)
                self.antibodies[antibody.antibody_id] = antibody

        self.stats["antibodies_generated"] += len(antibodies)

        logger.info(
            f"[{self.bcell_id}] Generated {len(antibodies)} antibodies"
        )

        return antibodies

    def _generate_yara_signature(self, antigen: Dict) -> Optional[Antibody]:
        """
        Generate YARA signature from antigen.

        Uses antigen features to create detection rule.
        """
        antigen_id = antigen.get('antigen_id', 'unknown')
        malware_family = antigen.get('malware_family', 'unknown')
        severity = antigen.get('severity', 'medium')

        # Extract features
        static_features = antigen.get('static_features', {})
        iocs = antigen.get('iocs', [])

        # Build YARA rule
        rule_name = f"{malware_family}_{hashlib.md5(antigen_id.encode()).hexdigest()[:8]}"

        strings_section = ""
        condition_parts = []

        # Add file hash
        sample_hash = antigen.get('sample_hash')
        if sample_hash:
            strings_section += f'        $hash = "{sample_hash}"\n'
            condition_parts.append("$hash")

        # Add IOC-based strings
        for i, ioc in enumerate(iocs[:10]):
            if ioc.get('ioc_type') in ['domain', 'url', 'ip']:
                value = ioc['value'].replace('.', '\\.')
                strings_section += f'        $ioc{i} = /{value}/ ascii wide\n'
                condition_parts.append(f"$ioc{i}")

        # Add entropy check if high
        entropy = static_features.get('entropy', 0)
        if entropy > 7.0:
            condition_parts.append("math.entropy(0, filesize) > 7.0")

        # Build full rule
        if not condition_parts:
            condition_parts.append("any of them")

        signature = f"""
rule {rule_name}
{{
    meta:
        description = "Auto-generated signature for {malware_family}"
        severity = "{severity}"
        family = "{malware_family}"
        generated_by = "B Cell {self.bcell_id}"
        antigen_id = "{antigen_id}"
        version = "1"

    strings:
{strings_section}

    condition:
        {' or '.join(condition_parts)}
}}
""".strip()

        antibody_id = f"ab_yara_{rule_name}"

        return Antibody(
            antibody_id=antibody_id,
            antigen_id=antigen_id,
            isotype=AntibodyIsotype.IGM,  # Start with IgM (low specificity)
            signature_type=SignatureType.YARA,
            signature_content=signature,
            malware_family=malware_family,
            severity=severity,
            version=1,
            affinity=AffinityLevel.MEDIUM,  # Will be tested
            metadata={
                "rule_name": rule_name,
                "ioc_count": len(iocs)
            }
        )

    def _generate_snort_signature(self, antigen: Dict) -> Optional[Antibody]:
        """
        Generate Snort IDS signature.

        Format: alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"..."; content:"..."; sid:...; rev:1;)
        """
        antigen_id = antigen.get('antigen_id', 'unknown')
        malware_family = antigen.get('malware_family', 'unknown')

        # Extract network IOCs
        iocs = antigen.get('iocs', [])
        network_iocs = [ioc for ioc in iocs if ioc.get('ioc_type') in ['ip', 'domain', 'url']]

        if not network_iocs:
            return None

        # Use first IOC as primary indicator
        primary_ioc = network_iocs[0]
        ioc_type = primary_ioc['ioc_type']
        ioc_value = primary_ioc['value']

        # Generate SID (signature ID)
        sid = 1000000 + (hash(antigen_id) % 900000)

        if ioc_type == 'ip':
            signature = (
                f'alert ip any any -> {ioc_value} any '
                f'(msg:"{malware_family} communication to known malicious IP"; '
                f'reference:url,immunis/antigen/{antigen_id}; '
                f'classtype:trojan-activity; '
                f'sid:{sid}; rev:1;)'
            )
        elif ioc_type in ['domain', 'url']:
            signature = (
                f'alert tcp $HOME_NET any -> $EXTERNAL_NET any '
                f'(msg:"{malware_family} DNS/HTTP to malicious domain"; '
                f'content:"{ioc_value}"; nocase; '
                f'reference:url,immunis/antigen/{antigen_id}; '
                f'classtype:trojan-activity; '
                f'sid:{sid}; rev:1;)'
            )
        else:
            return None

        antibody_id = f"ab_snort_{sid}"

        return Antibody(
            antibody_id=antibody_id,
            antigen_id=antigen_id,
            isotype=AntibodyIsotype.IGA,  # Network-level detection
            signature_type=SignatureType.SNORT,
            signature_content=signature,
            malware_family=malware_family,
            severity=antigen.get('severity', 'medium'),
            version=1,
            affinity=AffinityLevel.MEDIUM,
            metadata={
                "sid": sid,
                "ioc_type": ioc_type,
                "ioc_value": ioc_value
            }
        )

    def _generate_suricata_signature(self, antigen: Dict) -> Optional[Antibody]:
        """Generate Suricata signature (similar to Snort)"""
        # For now, reuse Snort logic (Suricata is Snort-compatible)
        snort_sig = self._generate_snort_signature(antigen)
        if snort_sig:
            snort_sig.signature_type = SignatureType.SURICATA
            snort_sig.antibody_id = snort_sig.antibody_id.replace('snort', 'suricata')
        return snort_sig

    def _generate_sigma_signature(self, antigen: Dict) -> Optional[Antibody]:
        """
        Generate Sigma log detection rule.

        Sigma is YAML-based detection for logs.
        """
        antigen_id = antigen.get('antigen_id', 'unknown')
        malware_family = antigen.get('malware_family', 'unknown')

        # Extract process/file IOCs
        iocs = antigen.get('iocs', [])
        file_iocs = [ioc for ioc in iocs if ioc.get('ioc_type') == 'file_path']

        if not file_iocs:
            return None

        signature = f"""
title: {malware_family} Detection
id: {hashlib.md5(antigen_id.encode()).hexdigest()}
status: experimental
description: Auto-generated detection for {malware_family}
author: Immunis B Cell {self.bcell_id}
date: {time.strftime('%Y/%m/%d')}
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4688
        NewProcessName|contains:
"""

        for ioc in file_iocs[:5]:
            signature += f'            - "{ioc["value"]}"\n'

        signature += """
    condition: selection
falsepositives:
    - Legitimate software with similar paths
level: high
"""

        antibody_id = f"ab_sigma_{hashlib.md5(antigen_id.encode()).hexdigest()[:8]}"

        return Antibody(
            antibody_id=antibody_id,
            antigen_id=antigen_id,
            isotype=AntibodyIsotype.IGG,  # High specificity (log-based)
            signature_type=SignatureType.SIGMA,
            signature_content=signature.strip(),
            malware_family=malware_family,
            severity=antigen.get('severity', 'medium'),
            version=1,
            affinity=AffinityLevel.HIGH,
            metadata={"log_source": "windows_security"}
        )

    async def affinity_maturation(
        self,
        antibody: Antibody,
        test_results: Dict
    ) -> Optional[Antibody]:
        """
        Affinity maturation - improve antibody through testing.

        Biological: Somatic hypermutation in germinal centers
        Computational: A/B testing and iterative refinement

        Args:
            antibody: Antibody to improve
            test_results: Results from testing (TP, FP, TN, FN)

        Returns:
            Improved antibody (new version) or None if no improvement
        """
        # Update test results
        antibody.true_positives += test_results.get('true_positives', 0)
        antibody.false_positives += test_results.get('false_positives', 0)
        antibody.true_negatives += test_results.get('true_negatives', 0)
        antibody.false_negatives += test_results.get('false_negatives', 0)

        # Check if improvement needed
        if antibody.precision < 0.8 or antibody.recall < 0.7:
            logger.info(
                f"[{self.bcell_id}] Antibody {antibody.antibody_id} needs improvement "
                f"(precision={antibody.precision:.2f}, recall={antibody.recall:.2f})"
            )

            # Mutate signature (improve specificity)
            improved = self._mutate_signature(antibody)

            if improved:
                improved.version = antibody.version + 1
                improved.affinity = self._determine_affinity(improved)

                # Isotype switching (IgM → IgG for high affinity)
                if improved.affinity in [AffinityLevel.HIGH, AffinityLevel.VERY_HIGH]:
                    improved.isotype = AntibodyIsotype.IGG

                self.antibodies[improved.antibody_id] = improved

                logger.info(
                    f"[{self.bcell_id}] Generated improved antibody v{improved.version} "
                    f"(affinity={improved.affinity.value})"
                )

                return improved

        return None

    def _mutate_signature(self, antibody: Antibody) -> Optional[Antibody]:
        """
        Mutate signature to improve specificity.

        Strategies:
        - Add more specific strings
        - Tighten regex patterns
        - Add context (parent process, file location)
        """
        # For now: increment version and mark as improved
        # In production: actual signature mutation logic

        new_antibody = Antibody(
            antibody_id=f"{antibody.antibody_id}_v{antibody.version + 1}",
            antigen_id=antibody.antigen_id,
            isotype=antibody.isotype,
            signature_type=antibody.signature_type,
            signature_content=antibody.signature_content,  # Would mutate here
            malware_family=antibody.malware_family,
            severity=antibody.severity,
            version=antibody.version + 1,
            affinity=antibody.affinity,
            metadata={**antibody.metadata, "mutated_from": antibody.antibody_id}
        )

        return new_antibody

    def _determine_affinity(self, antibody: Antibody) -> AffinityLevel:
        """Determine affinity level from test results"""
        if antibody.precision >= 0.95 and antibody.recall >= 0.90:
            return AffinityLevel.VERY_HIGH
        elif antibody.precision >= 0.85 and antibody.recall >= 0.75:
            return AffinityLevel.HIGH
        elif antibody.precision >= 0.70 and antibody.recall >= 0.60:
            return AffinityLevel.MEDIUM
        else:
            return AffinityLevel.LOW

    async def clonal_expansion(
        self,
        antibody: Antibody,
        deployment_targets: List[str]
    ) -> ClonalExpansion:
        """
        Clonal expansion - deploy antibody widely.

        Biological: Successful B cell clones proliferate massively
        Computational: Deploy signature to all sensors/agents

        Args:
            antibody: Antibody to deploy
            deployment_targets: List of targets (sensors, firewalls, etc.)

        Returns:
            ClonalExpansion record
        """
        logger.info(
            f"[{self.bcell_id}] Clonal expansion: deploying {antibody.antibody_id} "
            f"to {len(deployment_targets)} targets"
        )

        expansion = ClonalExpansion(
            expansion_id=f"exp_{int(time.time())}_{hash(antibody.antibody_id) % 10000}",
            parent_antibody=antibody,
            clone_count=len(deployment_targets),
            deployment_targets=deployment_targets,
            started_at=time.time()
        )

        # Simulate deployment
        await asyncio.sleep(0.1)  # Real deployment would be async

        expansion.completed_at = time.time()
        expansion.success = True

        # Mark antibody as deployed
        antibody.deployed = True
        antibody.deployed_at = time.time()

        self.expansions.append(expansion)
        self.stats["clonal_expansions"] += 1
        self.stats["deployed_antibodies"] += 1

        logger.info(
            f"[{self.bcell_id}] Clonal expansion complete: {expansion.clone_count} clones deployed"
        )

        return expansion

    async def form_memory(self, antibody: Antibody) -> MemoryBCell:
        """
        Form memory B cell for long-term immunity.

        Biological: Some activated B cells become memory cells
        Computational: Store successful signatures in memory database

        Args:
            antibody: Successful antibody to store

        Returns:
            MemoryBCell record
        """
        memory_id = f"mem_{antibody.antibody_id}"

        memory_cell = MemoryBCell(
            memory_id=memory_id,
            antibody=antibody,
            recall_count=0,
            last_recalled=None,
            half_life_days=365  # Signatures last 1 year
        )

        self.memory_cells[memory_id] = memory_cell
        self.stats["memory_cells_formed"] += 1

        logger.info(
            f"[{self.bcell_id}] Formed memory cell {memory_id} for {antibody.malware_family}"
        )

        return memory_cell

    async def recall_memory(self, malware_family: str) -> Optional[Antibody]:
        """
        Recall memory B cell for rapid response.

        Biological: Memory cells enable faster secondary response
        Computational: Retrieve stored signature for known threat

        Args:
            malware_family: Threat family to recall

        Returns:
            Stored antibody if found
        """
        for memory in self.memory_cells.values():
            if memory.antibody.malware_family == malware_family:
                memory.recall_count += 1
                memory.last_recalled = time.time()

                logger.info(
                    f"[{self.bcell_id}] Recalled memory for {malware_family} "
                    f"(recalled {memory.recall_count} times)"
                )

                return memory.antibody

        return None

    def get_stats(self) -> Dict:
        """Get B cell statistics"""
        # Calculate averages
        if self.antibodies:
            self.stats["avg_precision"] = sum(
                ab.precision for ab in self.antibodies.values()
            ) / len(self.antibodies)

            self.stats["avg_recall"] = sum(
                ab.recall for ab in self.antibodies.values()
            ) / len(self.antibodies)

            self.stats["high_affinity_antibodies"] = sum(
                1 for ab in self.antibodies.values()
                if ab.affinity in [AffinityLevel.HIGH, AffinityLevel.VERY_HIGH]
            )

        return {
            **self.stats,
            "total_antibodies": len(self.antibodies),
            "memory_cells": len(self.memory_cells)
        }


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("B CELL SERVICE - ANTIBODY PRODUCTION")
    print("="*80 + "\n")

    async def test_bcell():
        # Initialize B cell
        bcell = BCellCore(
            bcell_id="bcell_001",
            signature_types=[SignatureType.YARA, SignatureType.SNORT, SignatureType.SIGMA]
        )

        # Mock antigen
        antigen = {
            "antigen_id": "ag_test_001",
            "malware_family": "ransomware",
            "severity": "critical",
            "sample_hash": "abc123def456",
            "static_features": {"entropy": 7.8, "file_size": 500000},
            "iocs": [
                {"ioc_type": "ip", "value": "192.168.1.100"},
                {"ioc_type": "domain", "value": "malicious.com"},
                {"ioc_type": "file_path", "value": "C:\\\\Windows\\\\Temp\\\\evil.exe"}
            ]
        }

        # Generate antibodies
        print("Generating antibodies from antigen...\n")
        antibodies = await bcell.generate_antibodies(antigen)

        for ab in antibodies:
            print(f"Antibody: {ab.antibody_id}")
            print(f"  Type: {ab.signature_type.value}")
            print(f"  Isotype: {ab.isotype.value}")
            print(f"  Affinity: {ab.affinity.value}")
            print(f"  Signature preview:")
            print("  " + "\n  ".join(ab.signature_content.split("\n")[:10]))
            print()

        # Test affinity maturation
        if antibodies:
            print("Testing affinity maturation...\n")
            test_antibody = antibodies[0]

            # Simulate test results
            test_results = {
                "true_positives": 45,
                "false_positives": 5,
                "true_negatives": 900,
                "false_negatives": 10
            }

            improved = await bcell.affinity_maturation(test_antibody, test_results)

            print(f"Original antibody:")
            print(f"  Precision: {test_antibody.precision:.2f}")
            print(f"  Recall: {test_antibody.recall:.2f}")
            print(f"  F1: {test_antibody.f1_score:.2f}")
            print()

            # Deploy best antibody
            best_antibody = antibodies[0]
            if improved and improved.affinity.value > best_antibody.affinity.value:
                best_antibody = improved

            print("Performing clonal expansion...\n")
            targets = ["sensor_1", "sensor_2", "sensor_3", "firewall_1", "ids_1"]
            expansion = await bcell.clonal_expansion(best_antibody, targets)

            print(f"Expansion: {expansion.clone_count} clones deployed")
            print(f"  Targets: {expansion.deployment_targets}")
            print()

            # Form memory
            print("Forming memory B cell...\n")
            memory = await bcell.form_memory(best_antibody)
            print(f"Memory: {memory.memory_id}")
            print(f"  Half-life: {memory.half_life_days} days")
            print()

            # Recall memory
            print("Testing memory recall...\n")
            recalled = await bcell.recall_memory("ransomware")
            if recalled:
                print(f"Recalled: {recalled.antibody_id}")
            print()

        # Stats
        print("="*80)
        print("STATISTICS")
        print("="*80)
        stats = bcell.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n" + "="*80)
        print("B CELL TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_bcell())
