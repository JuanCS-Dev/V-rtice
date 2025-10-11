"""
Two-Phase Attack Simulator - Validates patches via exploit execution.

Executes exploits in two phases:
1. Phase 1: Attack vulnerable version (MUST succeed)
2. Phase 2: Attack patched version (MUST fail)

Both phases passing = patch validated!

Theoretical Foundation:
    Empirical validation is the ultimate test. A patch is only proven
    effective when it demonstrably blocks real exploits.
    
    Two-phase methodology ensures:
    - Phase 1: Exploit works (vulnerability confirmed)
    - Phase 2: Exploit fails (patch effective)
    - False positives eliminated (both must pass)
    
    Biological analogy: Test immune response by exposing to pathogen.
    Digital: Test patch by exposing to exploit.

Performance Targets:
    - Container deployment: <60s per version
    - Exploit execution: <30s per exploit
    - Total wargaming: <5 min
    - Success rate: 100% (both phases)

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - The Ultimate Validator
"""

import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List
import tempfile

logger = logging.getLogger(__name__)


class WargamingPhase(str, Enum):
    """Wargaming phases"""
    PHASE_1_VULNERABLE = "phase_1_vulnerable"
    PHASE_2_PATCHED = "phase_2_patched"


class WargamingStatus(str, Enum):
    """Overall wargaming status"""
    SUCCESS = "success"          # Both phases passed
    FAILED = "failed"            # One or both phases failed
    ERROR = "error"              # Execution error
    TIMEOUT = "timeout"          # Execution timeout


@dataclass
class PhaseResult:
    """Result of a single phase"""
    
    phase: WargamingPhase
    exploit_id: str
    exploit_success: bool  # Did exploit succeed?
    expected_result: bool  # What we expected
    phase_passed: bool     # Did phase pass? (exploit_success == expected_result)
    output: str
    error: Optional[str]
    duration_seconds: float
    metadata: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "phase": self.phase.value,
            "exploit_id": self.exploit_id,
            "exploit_success": self.exploit_success,
            "expected_result": self.expected_result,
            "phase_passed": self.phase_passed,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata
        }


@dataclass
class WargamingResult:
    """Complete wargaming result (both phases)"""
    
    apv_id: str
    cve_id: str
    exploit_id: str
    phase_1_result: PhaseResult
    phase_2_result: PhaseResult
    status: WargamingStatus
    patch_validated: bool  # True if both phases passed
    total_duration_seconds: float
    executed_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "apv_id": self.apv_id,
            "cve_id": self.cve_id,
            "exploit_id": self.exploit_id,
            "phase_1": self.phase_1_result.to_dict(),
            "phase_2": self.phase_2_result.to_dict(),
            "status": self.status.value,
            "patch_validated": self.patch_validated,
            "total_duration_seconds": self.total_duration_seconds,
            "executed_at": self.executed_at.isoformat()
        }
    
    def summary(self) -> str:
        """Human-readable summary"""
        if self.patch_validated:
            return f"✅ PATCH VALIDATED: {self.cve_id}\n" \
                   f"   Phase 1: Exploit succeeded on vulnerable ✓\n" \
                   f"   Phase 2: Exploit blocked on patched ✓\n" \
                   f"   Duration: {self.total_duration_seconds:.1f}s"
        else:
            return f"❌ PATCH VALIDATION FAILED: {self.cve_id}\n" \
                   f"   Phase 1: {'✓' if self.phase_1_result.phase_passed else '✗'}\n" \
                   f"   Phase 2: {'✓' if self.phase_2_result.phase_passed else '✗'}\n" \
                   f"   Status: {self.status.value}"


class TwoPhaseSimulator:
    """
    Executes two-phase wargaming to validate patches.
    
    Simulates attacks against vulnerable and patched versions to
    empirically validate patch effectiveness.
    
    Usage:
        >>> simulator = TwoPhaseSimulator()
        >>> result = await simulator.execute_wargaming(
        ...     apv=apv_object,
        ...     patch=patch_object,
        ...     exploit=exploit_script
        ... )
        >>> if result.patch_validated:
        ...     print("Patch validated! Safe to deploy.")
        >>> else:
        ...     print("Patch validation failed! Do not deploy.")
    """
    
    def __init__(
        self,
        timeout_seconds: int = 300,  # 5 min max
        cleanup_on_complete: bool = True
    ):
        """
        Initialize simulator.
        
        Args:
            timeout_seconds: Max total execution time
            cleanup_on_complete: Cleanup temp files after execution
        """
        self.timeout_seconds = timeout_seconds
        self.cleanup_on_complete = cleanup_on_complete
        
        logger.info(
            f"Initialized TwoPhaseSimulator: timeout={timeout_seconds}s, "
            f"cleanup={cleanup_on_complete}"
        )
    
    async def execute_wargaming(
        self,
        apv: "APV",
        patch: "Patch",
        exploit: "ExploitScript",
        target_base_url: str = "http://localhost:8080"
    ) -> WargamingResult:
        """
        Execute two-phase wargaming.
        
        Args:
            apv: APV object (vulnerability info)
            patch: Patch object (fix to test)
            exploit: ExploitScript to execute
            target_base_url: Base URL for target application
        
        Returns:
            WargamingResult with validation status
        
        Flow:
            1. Deploy vulnerable version
            2. Execute exploit (Phase 1 - should succeed)
            3. Deploy patched version
            4. Execute exploit (Phase 2 - should fail)
            5. Validate both phases
            6. Cleanup
        """
        start_time = datetime.now()
        
        logger.info(
            f"Starting wargaming: {apv.cve_id} with exploit {exploit.exploit_id}"
        )
        
        try:
            # Phase 1: Attack vulnerable version
            logger.info("Phase 1: Deploying vulnerable version...")
            phase_1_result = await self._execute_phase_1(
                apv, exploit, target_base_url
            )
            
            # Phase 2: Attack patched version
            logger.info("Phase 2: Deploying patched version...")
            phase_2_result = await self._execute_phase_2(
                apv, patch, exploit, target_base_url
            )
            
            # Determine overall status
            both_passed = (
                phase_1_result.phase_passed and 
                phase_2_result.phase_passed
            )
            
            # Check for errors in phases
            has_errors = (
                phase_1_result.error is not None or
                phase_2_result.error is not None
            )
            
            if has_errors:
                status = WargamingStatus.ERROR
                patch_validated = False
            elif both_passed:
                status = WargamingStatus.SUCCESS
                patch_validated = True
            else:
                status = WargamingStatus.FAILED
                patch_validated = False
            
            total_duration = (datetime.now() - start_time).total_seconds()
            
            result = WargamingResult(
                apv_id=apv.apv_id,
                cve_id=apv.cve_id,
                exploit_id=exploit.exploit_id,
                phase_1_result=phase_1_result,
                phase_2_result=phase_2_result,
                status=status,
                patch_validated=patch_validated,
                total_duration_seconds=total_duration,
                executed_at=start_time
            )
            
            logger.info(
                f"Wargaming complete: {result.status.value} "
                f"(validated={patch_validated})"
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Wargaming timeout after {self.timeout_seconds}s")
            
            # Return error result
            return WargamingResult(
                apv_id=apv.apv_id,
                cve_id=apv.cve_id,
                exploit_id=exploit.exploit_id,
                phase_1_result=self._create_error_phase_result(
                    WargamingPhase.PHASE_1_VULNERABLE,
                    exploit.exploit_id,
                    "Timeout"
                ),
                phase_2_result=self._create_error_phase_result(
                    WargamingPhase.PHASE_2_PATCHED,
                    exploit.exploit_id,
                    "Timeout"
                ),
                status=WargamingStatus.TIMEOUT,
                patch_validated=False,
                total_duration_seconds=self.timeout_seconds,
                executed_at=start_time
            )
        
        except Exception as e:
            logger.error(f"Wargaming error: {e}", exc_info=True)
            
            return WargamingResult(
                apv_id=apv.apv_id,
                cve_id=apv.cve_id,
                exploit_id=exploit.exploit_id,
                phase_1_result=self._create_error_phase_result(
                    WargamingPhase.PHASE_1_VULNERABLE,
                    exploit.exploit_id,
                    str(e)
                ),
                phase_2_result=self._create_error_phase_result(
                    WargamingPhase.PHASE_2_PATCHED,
                    exploit.exploit_id,
                    str(e)
                ),
                status=WargamingStatus.ERROR,
                patch_validated=False,
                total_duration_seconds=(datetime.now() - start_time).total_seconds(),
                executed_at=start_time
            )
    
    async def _execute_phase_1(
        self,
        apv: "APV",
        exploit: "ExploitScript",
        target_url: str
    ) -> PhaseResult:
        """
        Execute Phase 1: Attack vulnerable version.
        
        Expected: Exploit SHOULD succeed (vulnerability present)
        """
        import time
        start = time.time()
        
        # For now: Mock deployment (Docker integration comes next)
        # In production: Deploy vulnerable version in Docker container
        logger.info(f"Phase 1: Executing exploit against vulnerable version...")
        
        try:
            # Execute exploit
            exploit_result = await exploit.execute_func(
                target_url=target_url,
                timeout=30
            )
            
            # Phase 1 expects exploit to SUCCEED
            expected_result = True
            phase_passed = (exploit_result.success == expected_result)
            
            duration = time.time() - start
            
            return PhaseResult(
                phase=WargamingPhase.PHASE_1_VULNERABLE,
                exploit_id=exploit.exploit_id,
                exploit_success=exploit_result.success,
                expected_result=expected_result,
                phase_passed=phase_passed,
                output=exploit_result.output,
                error=exploit_result.error,
                duration_seconds=duration,
                metadata={
                    "apv_id": apv.apv_id,
                    "version": "vulnerable",
                    "exploit_status": exploit_result.status.value
                }
            )
            
        except Exception as e:
            logger.error(f"Phase 1 execution error: {e}")
            return self._create_error_phase_result(
                WargamingPhase.PHASE_1_VULNERABLE,
                exploit.exploit_id,
                str(e)
            )
    
    async def _execute_phase_2(
        self,
        apv: "APV",
        patch: "Patch",
        exploit: "ExploitScript",
        target_url: str
    ) -> PhaseResult:
        """
        Execute Phase 2: Attack patched version.
        
        Expected: Exploit SHOULD fail (patch blocks it)
        """
        import time
        start = time.time()
        
        # For now: Mock deployment (Docker integration comes next)
        # In production: Deploy patched version in Docker container
        logger.info(f"Phase 2: Executing exploit against patched version...")
        
        try:
            # Execute exploit
            exploit_result = await exploit.execute_func(
                target_url=target_url,
                timeout=30
            )
            
            # Phase 2 expects exploit to FAIL
            expected_result = False
            phase_passed = (exploit_result.success == expected_result)
            
            duration = time.time() - start
            
            return PhaseResult(
                phase=WargamingPhase.PHASE_2_PATCHED,
                exploit_id=exploit.exploit_id,
                exploit_success=exploit_result.success,
                expected_result=expected_result,
                phase_passed=phase_passed,
                output=exploit_result.output,
                error=exploit_result.error,
                duration_seconds=duration,
                metadata={
                    "apv_id": apv.apv_id,
                    "version": "patched",
                    "patch_id": patch.patch_id,
                    "exploit_status": exploit_result.status.value
                }
            )
            
        except Exception as e:
            logger.error(f"Phase 2 execution error: {e}")
            return self._create_error_phase_result(
                WargamingPhase.PHASE_2_PATCHED,
                exploit.exploit_id,
                str(e)
            )
    
    def _create_error_phase_result(
        self,
        phase: WargamingPhase,
        exploit_id: str,
        error_message: str
    ) -> PhaseResult:
        """Create error phase result"""
        return PhaseResult(
            phase=phase,
            exploit_id=exploit_id,
            exploit_success=False,
            expected_result=True if phase == WargamingPhase.PHASE_1_VULNERABLE else False,
            phase_passed=False,
            output="",
            error=error_message,
            duration_seconds=0.0,
            metadata={"error": True}
        )


# Convenience function
async def validate_patch_via_wargaming(
    apv: "APV",
    patch: "Patch",
    exploit: "ExploitScript",
    target_url: str = "http://localhost:8080"
) -> WargamingResult:
    """
    Quick function to validate patch via wargaming.
    
    Args:
        apv: APV object
        patch: Patch to validate
        exploit: Exploit script
        target_url: Target base URL
    
    Returns:
        WargamingResult
    
    Example:
        >>> result = await validate_patch_via_wargaming(apv, patch, exploit)
        >>> if result.patch_validated:
        ...     print("Patch is safe to deploy!")
        >>> else:
        ...     print(f"Patch validation failed: {result.summary()}")
    """
    simulator = TwoPhaseSimulator()
    return await simulator.execute_wargaming(apv, patch, exploit, target_url)
