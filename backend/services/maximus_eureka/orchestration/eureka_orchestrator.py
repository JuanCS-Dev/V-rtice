"""
Eureka Orchestrator - Vulnerability Confirmation + Remediation Pipeline.

Orchestrates the complete vulnerability remediation pipeline:
1. APV Consumer (Kafka) → receives APVs from Oráculo
2. Vulnerability Confirmer (ast-grep) → confirms code-level presence
3. Strategy Selector → chooses remediation approach
4. Patch Generator → creates fix via strategy
5. Metrics Collection → tracks MTTR, success rates

Phase 2 Scope: Consumer → Confirmation ✅
Phase 3 Scope: + Remediation Strategies ✅
Phase 4 Will Add: Git Integration + PR Creation

Architectural Philosophy:
    Orchestrator implements the Coordinator pattern, decoupling individual
    components while providing centralized lifecycle management and metrics.
    
    Each component maintains single responsibility:
    - APVConsumer: Kafka message handling + deserialization
    - VulnerabilityConfirmer: Code analysis via ast-grep
    - StrategySelector: Strategy selection logic
    - RemediationStrategies: Patch generation (dependency upgrade, LLM, etc)
    - EurekaOrchestrator: Coordination + error handling + metrics
    
    This enables independent testing, scaling, and evolution of each component.

Performance Targets:
    - APV processing latency: < 2min (confirmation + remediation)
    - Consumer lag: < 5 seconds
    - Memory footprint: < 1GB per orchestrator instance
    - Throughput: ≥ 50 APVs/min

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - The God who orchestrates all things for His purpose
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

# APV from Oráculo
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "maximus_oraculo"))
from models.apv import APV

from consumers.apv_consumer import APVConsumer, APVConsumerConfig
from confirmation.vulnerability_confirmer import (
    VulnerabilityConfirmer,
    ConfirmationConfig,
)
from eureka_models.confirmation.confirmation_result import (
    ConfirmationResult,
    ConfirmationStatus,
)
from strategies import StrategySelector, NoStrategyAvailableError
from eureka_models.patch import Patch, PatchStatus

logger = logging.getLogger(__name__)


@dataclass
class EurekaMetrics:
    """
    Operational metrics for Eureka orchestrator.
    
    Tracks pipeline performance across confirmation AND remediation phases.
    """

    # Counters
    apvs_received: int = 0
    apvs_confirmed: int = 0
    apvs_false_positive: int = 0
    apvs_failed: int = 0
    
    # Phase 3: Remediation metrics
    patches_generated: int = 0
    patches_failed: int = 0
    strategy_dependency_upgrade: int = 0
    strategy_code_patch_llm: int = 0

    # Timing (seconds)
    total_processing_time: float = 0.0
    min_processing_time: Optional[float] = None
    max_processing_time: Optional[float] = None

    # Lifecycle
    started_at: Optional[datetime] = None
    last_apv_at: Optional[datetime] = None

    def record_processing(self, duration: float, status: ConfirmationStatus) -> None:
        """
        Record APV processing metrics.
        
        Args:
            duration: Processing time in seconds
            status: Confirmation status
        """
        self.apvs_received += 1
        self.total_processing_time += duration
        self.last_apv_at = datetime.utcnow()

        # Update min/max
        if self.min_processing_time is None or duration < self.min_processing_time:
            self.min_processing_time = duration
        if self.max_processing_time is None or duration > self.max_processing_time:
            self.max_processing_time = duration

        # Update status counters
        if status == ConfirmationStatus.CONFIRMED:
            self.apvs_confirmed += 1
        elif status == ConfirmationStatus.FALSE_POSITIVE:
            self.apvs_false_positive += 1
        elif status == ConfirmationStatus.ERROR:
            self.apvs_failed += 1
    
    def record_patch(self, patch: Optional[Patch], strategy_used: str) -> None:
        """
        Record patch generation metrics.
        
        Args:
            patch: Generated patch (None if failed)
            strategy_used: Strategy that was used
        """
        if patch:
            self.patches_generated += 1
            
            # Track strategy usage
            if strategy_used == "dependency_upgrade":
                self.strategy_dependency_upgrade += 1
            elif strategy_used == "code_patch":
                self.strategy_code_patch_llm += 1
        else:
            self.patches_failed += 1

    @property
    def avg_processing_time(self) -> float:
        """Average processing time per APV."""
        if self.apvs_received == 0:
            return 0.0
        return self.total_processing_time / self.apvs_received

    @property
    def success_rate(self) -> float:
        """Success rate (confirmed / total processed)."""
        total = self.apvs_confirmed + self.apvs_false_positive + self.apvs_failed
        if total == 0:
            return 0.0
        return self.apvs_confirmed / total

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "apvs_received": self.apvs_received,
            "apvs_confirmed": self.apvs_confirmed,
            "apvs_false_positive": self.apvs_false_positive,
            "apvs_failed": self.apvs_failed,
            "total_processing_time": self.total_processing_time,
            "min_processing_time": self.min_processing_time,
            "max_processing_time": self.max_processing_time,
            "avg_processing_time": self.avg_processing_time,
            "success_rate": self.success_rate,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_apv_at": self.last_apv_at.isoformat() if self.last_apv_at else None,
        }


class EurekaOrchestrator:
    """
    Orchestrates Eureka vulnerability confirmation pipeline.
    
    Phase 2 (Current): APV Consumer → Vulnerability Confirmation
    Phase 3 (Future): Add Remediation Strategy Selection + Patch Generation
    Phase 4 (Future): Add Git Integration + PR Creation
    
    The orchestrator provides:
    - Centralized lifecycle management (start/stop)
    - Error handling and recovery
    - Metrics collection and reporting
    - Graceful degradation on component failures
    
    Usage:
        >>> config_consumer = APVConsumerConfig()
        >>> config_confirmer = ConfirmationConfig(codebase_root=Path("/app"))
        >>> orchestrator = EurekaOrchestrator(config_consumer, config_confirmer)
        >>> await orchestrator.start()  # Runs until stopped
        >>> await orchestrator.stop()
    """

    def __init__(
        self,
        consumer_config: APVConsumerConfig,
        confirmer_config: ConfirmationConfig,
        strategy_selector: Optional[StrategySelector] = None,
    ):
        """
        Initialize Eureka Orchestrator.
        
        Args:
            consumer_config: Configuration for APV Kafka consumer
            confirmer_config: Configuration for vulnerability confirmer
            strategy_selector: Strategy selector for remediation (optional)
        """
        self.consumer_config = consumer_config
        self.confirmer_config = confirmer_config
        self.strategy_selector = strategy_selector

        # Components (initialized in start())
        self._consumer: Optional[APVConsumer] = None
        self._confirmer: Optional[VulnerabilityConfirmer] = None

        # State
        self._running = False
        self.metrics = EurekaMetrics()

        logger.info("Eureka Orchestrator initialized")
        if strategy_selector:
            strategies = [s.strategy_type.value for s in strategy_selector.get_strategies()]
            logger.info(f"Remediation strategies enabled: {strategies}")
        else:
            logger.info("Remediation strategies DISABLED (confirmation only mode)")

    async def start(self) -> None:
        """
        Start Eureka orchestration pipeline.
        
        Initializes components and begins consuming APVs from Kafka.
        Runs indefinitely until stop() is called.
        
        Raises:
            Exception: If component initialization fails
        """
        if self._running:
            logger.warning("Orchestrator already running")
            return

        logger.info("🚀 Starting Eureka Orchestrator...")
        self.metrics.started_at = datetime.utcnow()

        try:
            # Initialize confirmer
            self._confirmer = VulnerabilityConfirmer(self.confirmer_config)
            logger.info("✅ Vulnerability Confirmer initialized")

            # Initialize consumer with our processing handler
            self._consumer = APVConsumer(
                config=self.consumer_config, apv_handler=self._process_apv
            )

            self._running = True

            # Start consuming (blocks until stopped)
            logger.info("✅ Starting APV Consumer...")
            await self._consumer.start()

        except Exception as e:
            logger.error(f"❌ Failed to start orchestrator: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """
        Stop Eureka orchestration pipeline gracefully.
        
        Stops consumer, waits for pending confirmations, logs final metrics.
        """
        if not self._running:
            return

        logger.info("🛑 Stopping Eureka Orchestrator...")
        self._running = False

        # Stop consumer
        if self._consumer:
            await self._consumer.stop()
            logger.info("✅ APV Consumer stopped")

        # Log final metrics
        logger.info(f"📊 Final metrics: {self.metrics.to_dict()}")

    async def _process_apv(self, apv: APV) -> None:
        """
        Process single APV through confirmation pipeline.
        
        Phase 2: Confirmation only
        Phase 3: Will add strategy selection + patch generation
        Phase 4: Will add Git integration + PR creation
        
        Args:
            apv: APV from Oráculo to process
            
        Raises:
            Exception: On processing failure (logged, not propagated to consumer)
        """
        start_time = time.time()

        try:
            logger.info(
                f"🔍 Processing APV: {apv.cve_id}",
                extra={
                    "cve_id": apv.cve_id,
                    "priority": apv.priority.value if apv.priority else None,
                    "packages": len(apv.affected_packages),
                },
            )

            # Phase 2: Confirm vulnerability
            if self._confirmer is None:
                raise RuntimeError("Confirmer not initialized")
            
            confirmation = await self._confirmer.confirm_vulnerability(apv)

            # Record metrics
            elapsed = time.time() - start_time
            self.metrics.record_processing(elapsed, confirmation.status)

            # Log result
            if confirmation.status == ConfirmationStatus.CONFIRMED:
                logger.info(
                    f"✅ Confirmed: {apv.cve_id} "
                    f"({len(confirmation.vulnerable_locations)} locations) "
                    f"in {elapsed:.2f}s",
                    extra={
                        "cve_id": apv.cve_id,
                        "locations": len(confirmation.vulnerable_locations),
                        "elapsed": elapsed,
                    },
                )

                # Phase 3: Select and apply remediation strategy
                if self.strategy_selector:
                    try:
                        logger.info(f"🎯 Selecting remediation strategy for {apv.cve_id}")
                        strategy = await self.strategy_selector.select_strategy(apv, confirmation)
                        
                        logger.info(
                            f"✅ Selected {strategy.strategy_type.value} for {apv.cve_id}"
                        )
                        
                        # Generate patch
                        patch = await strategy.apply_strategy(apv, confirmation)
                        
                        logger.info(
                            f"🔧 Generated patch for {apv.cve_id}: "
                            f"{len(patch.files_modified)} files, "
                            f"confidence={patch.confidence_score:.2f}"
                        )
                        
                        # Record patch metrics
                        self.metrics.record_patch(patch, strategy.strategy_type.value)
                        
                        # TODO Phase 4: Apply patch to Git + create PR
                        # git_service.apply_patch(patch)
                        # pr_url = github_service.create_pr(patch)
                        
                    except NoStrategyAvailableError as e:
                        logger.warning(
                            f"⚠️ No remediation strategy available for {apv.cve_id}: {e}"
                        )
                        self.metrics.record_patch(None, "none")
                        
                    except Exception as e:
                        logger.error(
                            f"❌ Remediation failed for {apv.cve_id}: {e}",
                            exc_info=True,
                        )
                        self.metrics.record_patch(None, "error")
                else:
                    logger.debug(
                        f"Remediation disabled, skipping patch generation for {apv.cve_id}"
                    )

            elif confirmation.status == ConfirmationStatus.FALSE_POSITIVE:
                logger.info(
                    f"ℹ️ False positive: {apv.cve_id} in {elapsed:.2f}s",
                    extra={"cve_id": apv.cve_id, "elapsed": elapsed},
                )

            else:  # ERROR
                logger.warning(
                    f"⚠️ Confirmation error: {apv.cve_id} - {confirmation.error_message}",
                    extra={
                        "cve_id": apv.cve_id,
                        "error": confirmation.error_message,
                        "elapsed": elapsed,
                    },
                )

        except Exception as e:
            elapsed = time.time() - start_time
            self.metrics.record_processing(elapsed, ConfirmationStatus.ERROR)

            logger.error(
                f"❌ Failed to process {apv.cve_id}: {e}",
                exc_info=True,
                extra={"cve_id": apv.cve_id, "elapsed": elapsed},
            )
            # Don't propagate - let consumer continue

    def get_metrics(self) -> dict[str, Any]:
        """
        Get current orchestrator metrics.
        
        Returns:
            Dictionary with metrics snapshot
        """
        return self.metrics.to_dict()

    @property
    def is_running(self) -> bool:
        """Check if orchestrator is running."""
        return self._running
