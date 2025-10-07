"""Homeostatic Control Loop (HCL) Orchestrator

Main control loop implementing Monitor → Analyze → Plan → Execute → Knowledge cycle.
Bio-inspired self-regulation with Sympathetic/Parasympathetic operational modes.
"""

import asyncio
from datetime import datetime
import logging
import time
from typing import Any, Dict, Optional

from .analyze.anomaly_detector import AnomalyDetector
from .analyze.degradation_detector import PerformanceDegradationDetector
from .analyze.demand_forecaster import ResourceDemandForecaster
from .analyze.failure_predictor import FailurePredictor
from .execute.cache_actuator import CacheActuator
from .execute.database_actuator import DatabaseActuator
from .execute.docker_actuator import DockerActuator
from .execute.kubernetes_actuator import KubernetesActuator
from .execute.loadbalancer_actuator import LoadBalancerActuator
from .execute.safety_manager import SafetyManager
from .knowledge_base.decision_api import DecisionAPI
from .monitor.system_monitor import SystemMonitor
from .plan.fuzzy_controller import FuzzyLogicController
from .plan.mode_definitions import get_mode_policy, OPERATIONAL_MODES
from .plan.rl_agent import SACAgent

logger = logging.getLogger(__name__)


class HomeostaticControlLoop:
    """Main HCL orchestrator - autonomous self-regulation loop."""

    def __init__(
        self,
        dry_run_mode: bool = True,
        loop_interval_seconds: int = 30,
        db_url: str = "postgresql://localhost/vertice",
    ):
        self.dry_run_mode = dry_run_mode
        self.loop_interval = loop_interval_seconds
        self.running = False

        # Monitor
        self.monitor = SystemMonitor()

        # Analyze
        self.demand_forecaster = ResourceDemandForecaster()
        self.anomaly_detector = AnomalyDetector()
        self.failure_predictor = FailurePredictor()
        self.degradation_detector = PerformanceDegradationDetector()

        # Plan
        self.fuzzy_controller = FuzzyLogicController()
        self.rl_agent = SACAgent()
        self.current_mode = "BALANCED"

        # Execute
        self.k8s_actuator = KubernetesActuator(dry_run_mode=dry_run_mode)
        self.docker_actuator = DockerActuator(dry_run_mode=dry_run_mode)
        self.db_actuator = DatabaseActuator(dry_run_mode=dry_run_mode)
        self.cache_actuator = CacheActuator(dry_run_mode=dry_run_mode)
        self.lb_actuator = LoadBalancerActuator(dry_run_mode=dry_run_mode)
        self.safety_manager = SafetyManager()

        # Knowledge Base
        self.decision_api = DecisionAPI(db_url=db_url)

        logger.info(
            f"HCL Orchestrator initialized (dry_run={dry_run_mode}, interval={loop_interval_seconds}s)"
        )

    async def initialize(self):
        """Initialize components and database pool."""
        try:
            # Initialize database connection pool
            import asyncpg

            self.decision_api.pool = await asyncpg.create_pool(
                self.decision_api.db_url, min_size=2, max_size=10
            )

            # Create schema if needed
            from .knowledge_base.database_schema import create_schema

            async with self.decision_api.pool.acquire() as conn:
                await create_schema(conn)

            logger.info("HCL components initialized successfully")

        except Exception as e:
            logger.error(f"HCL initialization error: {e}")
            raise

    async def run(self):
        """Main control loop."""
        self.running = True
        logger.info("HCL loop started")

        loop_count = 0

        while self.running:
            try:
                loop_start = time.time()
                loop_count += 1

                logger.info(f"=== HCL Cycle {loop_count} ===")

                # 1. MONITOR - Collect system metrics
                metrics = await self.monitor.collect_metrics()
                logger.info(f"Monitor: Collected {len(metrics)} metrics")

                # 2. ANALYZE - Detect anomalies, predict failures
                analysis = await self._analyze_metrics(metrics)
                logger.info(f"Analyze: {analysis.get('summary', 'Complete')}")

                # 3. PLAN - Determine operational mode and actions
                plan = await self._plan_actions(metrics, analysis)
                logger.info(
                    f"Plan: Mode={plan['operational_mode']}, Actions={len(plan['actions'])}"
                )

                # 4. EXECUTE - Apply actions with safety checks
                execution = await self._execute_plan(plan, metrics)
                logger.info(
                    f"Execute: Success={execution['success']}, Applied={execution['applied_count']}"
                )

                # 5. KNOWLEDGE - Store decision for learning
                await self._store_decision(metrics, analysis, plan, execution)

                # Wait for next cycle
                elapsed = time.time() - loop_start
                wait_time = max(0, self.loop_interval - elapsed)
                logger.info(
                    f"HCL cycle completed in {elapsed:.1f}s, waiting {wait_time:.1f}s"
                )

                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"HCL loop error: {e}", exc_info=True)
                await asyncio.sleep(self.loop_interval)

        logger.info("HCL loop stopped")

    async def _analyze_metrics(self, metrics: Dict) -> Dict:
        """Analyze metrics for anomalies, failures, degradation."""
        analysis = {}

        try:
            # Anomaly detection
            metric_array = self._metrics_to_array(metrics)
            anomaly_result = self.anomaly_detector.detect(metric_array)
            analysis["anomaly"] = anomaly_result

            # Failure prediction
            failure_features = self._extract_failure_features(metrics)
            failure_result = self.failure_predictor.predict(failure_features)
            analysis["failure_prediction"] = failure_result

            # Performance degradation
            degradation_result = self.degradation_detector.detect_degradation(
                metrics.get("latency_p99", 0)
            )
            analysis["degradation"] = degradation_result

            # Demand forecasting
            forecast = self.demand_forecaster.predict(horizon="1h")
            analysis["forecast"] = forecast

            # Summary
            issues = []
            if anomaly_result.get("is_anomaly"):
                issues.append(f"Anomaly detected (score={anomaly_result['score']:.2f})")
            if failure_result.get("failure_probability", 0) > 0.7:
                issues.append(
                    f"High failure risk ({failure_result['failure_probability']:.0%})"
                )
            if degradation_result.get("is_degraded"):
                issues.append("Performance degradation detected")

            analysis["summary"] = ", ".join(issues) if issues else "System healthy"

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            analysis["error"] = str(e)

        return analysis

    async def _plan_actions(self, metrics: Dict, analysis: Dict) -> Dict:
        """Plan operational mode and resource actions."""
        plan = {"operational_mode": self.current_mode, "actions": [], "reasoning": []}

        try:
            # Determine operational mode using fuzzy logic
            cpu_usage = metrics.get("cpu_percent", 0)
            error_rate = metrics.get("error_rate", 0)
            latency = metrics.get("latency_p99", 0)

            mode = self.fuzzy_controller.select_mode(cpu_usage, error_rate, latency)
            plan["operational_mode"] = mode
            plan["reasoning"].append(f"Fuzzy logic selected {mode} mode")

            # Get mode policy
            policy = get_mode_policy(mode)

            # Generate actions based on mode and analysis
            if analysis.get("anomaly", {}).get("is_anomaly"):
                # Anomaly detected - apply corrective actions
                plan["actions"].extend(self._generate_anomaly_actions(policy, metrics))
                plan["reasoning"].append("Anomaly mitigation actions")

            if (
                analysis.get("failure_prediction", {}).get("failure_probability", 0)
                > 0.7
            ):
                # High failure risk - preventive actions
                plan["actions"].extend(
                    self._generate_preventive_actions(policy, metrics)
                )
                plan["reasoning"].append("Preventive actions for predicted failure")

            if analysis.get("degradation", {}).get("is_degraded"):
                # Performance degradation - optimization actions
                plan["actions"].extend(
                    self._generate_optimization_actions(policy, metrics)
                )
                plan["reasoning"].append("Performance optimization actions")

            # RL agent fine-tuning (optional)
            if hasattr(self, "rl_agent") and self.rl_agent.model:
                state = self._get_rl_state(metrics)
                rl_allocation = self.rl_agent.predict_allocation(state)
                plan["rl_allocation"] = rl_allocation
                plan["reasoning"].append("RL agent allocation computed")

            # Update current mode
            self.current_mode = mode

        except Exception as e:
            logger.error(f"Planning error: {e}")
            plan["error"] = str(e)

        return plan

    async def _execute_plan(self, plan: Dict, metrics_before: Dict) -> Dict:
        """Execute planned actions with safety checks."""
        execution = {
            "success": True,
            "applied_count": 0,
            "failed_count": 0,
            "actions_log": [],
        }

        try:
            for action in plan.get("actions", []):
                # Safety check: rate limiting
                if not self.safety_manager.check_rate_limit(
                    action.get("type", "NORMAL")
                ):
                    logger.warning(f"Action throttled: {action}")
                    execution["failed_count"] += 1
                    continue

                # Execute action
                result = await self._execute_action(action)

                execution["actions_log"].append(
                    {
                        "action": action,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                if result.get("success"):
                    execution["applied_count"] += 1
                    self.safety_manager.log_action(action)
                else:
                    execution["failed_count"] += 1
                    execution["success"] = False

            # Auto-rollback check (wait 60s, then check metrics)
            if execution["applied_count"] > 0 and not self.dry_run_mode:
                await asyncio.sleep(60)
                metrics_after = await self.monitor.collect_metrics()

                should_rollback = self.safety_manager.auto_rollback(
                    action=plan,
                    metrics_before=metrics_before,
                    metrics_after=metrics_after,
                )

                if should_rollback:
                    logger.error("AUTO-ROLLBACK TRIGGERED")
                    execution["rollback"] = True
                    execution["success"] = False

        except Exception as e:
            logger.error(f"Execution error: {e}")
            execution["error"] = str(e)
            execution["success"] = False

        return execution

    async def _execute_action(self, action: Dict) -> Dict:
        """Execute individual action using appropriate actuator."""
        action_type = action.get("actuator")

        try:
            if action_type == "kubernetes":
                if action["operation"] == "adjust_hpa":
                    return self.k8s_actuator.adjust_hpa(
                        action["service"],
                        action["min_replicas"],
                        action["max_replicas"],
                    )
                elif action["operation"] == "update_resources":
                    return self.k8s_actuator.update_resource_limits(
                        action["service"], action["cpu_limit"], action["memory_limit"]
                    )

            elif action_type == "docker":
                if action["operation"] == "scale":
                    return await self.docker_actuator.scale_service(
                        action["service"], action["replicas"]
                    )

            elif action_type == "database":
                if action["operation"] == "adjust_pool":
                    return await self.db_actuator.adjust_connection_pool(
                        action["database"],
                        action["pool_size"],
                        action.get("pool_mode", "transaction"),
                    )

            elif action_type == "cache":
                if action["operation"] == "set_strategy":
                    return await self.cache_actuator.set_cache_strategy(
                        action["strategy"]
                    )

            elif action_type == "loadbalancer":
                if action["operation"] == "shift_traffic":
                    return await self.lb_actuator.shift_traffic(
                        action["service"],
                        action["target_version"],
                        action["weight_percent"],
                    )

            return {"success": False, "error": f"Unknown action type: {action_type}"}

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _store_decision(
        self, metrics: Dict, analysis: Dict, plan: Dict, execution: Dict
    ):
        """Store decision in knowledge base for learning."""
        try:
            decision = {
                "trigger": analysis.get("summary", "Routine cycle"),
                "operational_mode": plan["operational_mode"],
                "actions_taken": plan["actions"],
                "state_before": metrics,
                "state_after": {},  # Will be filled in next cycle
                "outcome": "SUCCESS" if execution["success"] else "FAILED",
                "reward_signal": self._calculate_reward(metrics, execution),
                "human_feedback": None,
            }

            await self.decision_api.create_decision(decision)

        except Exception as e:
            logger.error(f"Decision storage error: {e}")

    def _generate_anomaly_actions(self, policy: Dict, metrics: Dict) -> list:
        """Generate actions for anomaly mitigation."""
        actions = []

        if metrics.get("cpu_percent", 0) > 80:
            actions.append(
                {
                    "actuator": "kubernetes",
                    "operation": "adjust_hpa",
                    "service": "maximus-core",
                    "min_replicas": 3,
                    "max_replicas": 10,
                    "type": "CRITICAL",
                }
            )

        if metrics.get("memory_percent", 0) > 80:
            actions.append(
                {
                    "actuator": "cache",
                    "operation": "set_strategy",
                    "strategy": "conservative",
                    "type": "NORMAL",
                }
            )

        return actions

    def _generate_preventive_actions(self, policy: Dict, metrics: Dict) -> list:
        """Generate preventive actions for predicted failures."""
        actions = []

        # Increase replicas preemptively
        actions.append(
            {
                "actuator": "docker",
                "operation": "scale",
                "service": "maximus-core",
                "replicas": 4,
                "type": "CRITICAL",
            }
        )

        # Enable circuit breaker
        actions.append(
            {
                "actuator": "loadbalancer",
                "operation": "enable_circuit_breaker",
                "service": "maximus-core",
                "enabled": True,
                "type": "NORMAL",
            }
        )

        return actions

    def _generate_optimization_actions(self, policy: Dict, metrics: Dict) -> list:
        """Generate performance optimization actions."""
        actions = []

        if metrics.get("latency_p99", 0) > 1000:  # >1s
            # Optimize database
            actions.append(
                {
                    "actuator": "database",
                    "operation": "adjust_pool",
                    "database": "vertice",
                    "pool_size": 50,
                    "pool_mode": "transaction",
                    "type": "NORMAL",
                }
            )

            # Aggressive caching
            actions.append(
                {
                    "actuator": "cache",
                    "operation": "set_strategy",
                    "strategy": "aggressive",
                    "type": "NORMAL",
                }
            )

        return actions

    def _metrics_to_array(self, metrics: Dict) -> list:
        """Convert metrics dict to array for ML models."""
        return [
            metrics.get("cpu_percent", 0),
            metrics.get("memory_percent", 0),
            metrics.get("latency_p99", 0),
            metrics.get("error_rate", 0),
            # Add more features as needed
        ]

    def _extract_failure_features(self, metrics: Dict) -> Dict:
        """Extract features for failure prediction."""
        return {
            "error_rate_trend": metrics.get("error_rate", 0),
            "memory_leak_indicator": metrics.get("memory_percent", 0) > 85,
            "cpu_spike_pattern": metrics.get("cpu_percent", 0) > 90,
            "disk_io_degradation": metrics.get("disk_io_wait", 0) > 50,
        }

    def _get_rl_state(self, metrics: Dict) -> list:
        """Get RL agent state vector."""
        return [
            metrics.get("cpu_percent", 0) / 100.0,
            metrics.get("memory_percent", 0) / 100.0,
            metrics.get("requests_per_second", 0) / 1000.0,
            metrics.get("latency_p99", 0) / 1000.0,
        ]

    def _calculate_reward(self, metrics: Dict, execution: Dict) -> float:
        """Calculate reward signal for RL training."""
        reward = 0.0

        # Positive reward for low latency
        if metrics.get("latency_p99", 1000) < 500:
            reward += 1.0

        # Positive reward for low error rate
        if metrics.get("error_rate", 1.0) < 0.01:
            reward += 1.0

        # Penalty for high resource usage
        if metrics.get("cpu_percent", 0) > 80:
            reward -= 0.5

        # Penalty for failed actions
        if not execution.get("success", False):
            reward -= 2.0

        return reward

    async def stop(self):
        """Stop the control loop."""
        self.running = False
        logger.info("HCL loop stop requested")

        # Close connections
        if self.decision_api.pool:
            await self.decision_api.pool.close()

        if self.cache_actuator.client:
            await self.cache_actuator.close()


# Convenience function to run HCL
async def run_homeostatic_control_loop(
    dry_run: bool = True,
    interval: int = 30,
    db_url: str = "postgresql://localhost/vertice",
):
    """Run the Homeostatic Control Loop."""
    hcl = HomeostaticControlLoop(
        dry_run_mode=dry_run, loop_interval_seconds=interval, db_url=db_url
    )

    await hcl.initialize()
    await hcl.run()
