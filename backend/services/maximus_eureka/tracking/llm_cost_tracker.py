"""
LLM Cost Tracker - Monitor and control LLM API costs.

Tracks token usage and costs for all LLM calls (Claude, GPT-4, Gemini).
Exports Prometheus metrics and enforces budget limits.

Theoretical Foundation:
    LLM costs can spiral out of control without proper monitoring.
    OpenAI GPT-4: $0.01/1K input, $0.03/1K output
    Anthropic Claude: $0.003/1K input, $0.015/1K output
    Google Gemini: FREE currently (Flash), $0.00125/1K input (Pro)
    
    Budget management strategy:
    - Track per-request costs
    - Aggregate daily/monthly totals
    - Alert at 80% threshold
    - Throttle at 100% limit
    - Export Prometheus metrics for dashboards
    
Performance Targets:
    - Cost calculation: <10ms
    - Metric export: Real-time
    - Budget check: <5ms
    - Monthly target: <$50 USD

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Provider of all resources
"""

import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import json

from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


class LLMModel(str, Enum):
    """Supported LLM models"""
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GEMINI_2_5_PRO = "gemini-2-5-pro"
    GEMINI_2_0_FLASH = "gemini-2-0-flash-exp"


# Prometheus Metrics
llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'type', 'strategy']  # type = input/output
)

llm_cost_usd_total = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['model', 'strategy']
)

llm_cost_per_request_usd = Histogram(
    'llm_cost_per_request_usd',
    'Cost per LLM request',
    ['model', 'strategy'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'strategy', 'status']  # status = success/error
)

llm_monthly_budget_remaining_usd = Gauge(
    'llm_monthly_budget_remaining_usd',
    'Remaining monthly budget in USD'
)


@dataclass
class CostRecord:
    """Single cost record"""
    
    timestamp: datetime
    model: LLMModel
    strategy: str  # e.g., "dependency_upgrade", "code_patch_llm"
    input_tokens: int
    output_tokens: int
    cost_usd: float
    metadata: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "model": self.model.value
        }


class LLMCostTracker:
    """
    Track LLM API costs and enforce budget limits.
    
    Monitors token usage, calculates costs, exports metrics, and
    enforces monthly budget limits.
    
    Usage:
        >>> tracker = LLMCostTracker(monthly_budget=50.0)
        >>> record = await tracker.track_request(
        ...     model=LLMModel.CLAUDE_3_7_SONNET,
        ...     strategy="code_patch_llm",
        ...     input_tokens=1500,
        ...     output_tokens=800,
        ...     metadata={"apv_id": "apv_001"}
        ... )
        >>> print(f"Cost: ${record.cost_usd:.4f}")
    """
    
    # Pricing per 1K tokens (as of 2025-10)
    PRICING = {
        LLMModel.CLAUDE_3_7_SONNET: {"input": 0.003, "output": 0.015},
        LLMModel.CLAUDE_3_5_SONNET: {"input": 0.003, "output": 0.015},
        LLMModel.GPT_4_TURBO: {"input": 0.01, "output": 0.03},
        LLMModel.GPT_4O: {"input": 0.005, "output": 0.015},
        LLMModel.GEMINI_2_5_PRO: {"input": 0.00125, "output": 0.005},
        LLMModel.GEMINI_2_0_FLASH: {"input": 0.0, "output": 0.0},  # FREE
    }
    
    def __init__(
        self,
        monthly_budget: float = 50.0,
        storage_path: Optional[Path] = None,
        enable_throttling: bool = True
    ):
        """
        Initialize cost tracker.
        
        Args:
            monthly_budget: Monthly budget limit in USD
            storage_path: Path to store cost records (JSON)
            enable_throttling: Enable throttling at budget limit
        """
        self.monthly_budget = monthly_budget
        self.enable_throttling = enable_throttling
        
        # Storage
        self.storage_path = storage_path or Path("data/llm_costs.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing records
        self.records: List[CostRecord] = self._load_records()
        
        # Update Prometheus gauge
        self._update_budget_gauge()
        
        logger.info(
            f"Initialized LLMCostTracker: budget=${monthly_budget:.2f}/month, "
            f"throttling={'enabled' if enable_throttling else 'disabled'}"
        )
    
    async def track_request(
        self,
        model: LLMModel,
        strategy: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict] = None,
        status: str = "success"
    ) -> CostRecord:
        """
        Track LLM request and calculate cost.
        
        Args:
            model: LLM model used
            strategy: Strategy name (e.g., "code_patch_llm")
            input_tokens: Input token count
            output_tokens: Output token count
            metadata: Optional metadata dict
            status: Request status (success/error)
        
        Returns:
            CostRecord with calculated cost
        
        Raises:
            BudgetExceededError: If budget limit reached and throttling enabled
        """
        # Check budget before processing
        if self.enable_throttling:
            monthly_cost = self.get_monthly_cost()
            if monthly_cost >= self.monthly_budget:
                logger.error(
                    f"Monthly budget ${self.monthly_budget:.2f} exceeded! "
                    f"Current: ${monthly_cost:.2f}"
                )
                raise BudgetExceededError(
                    f"Monthly budget ${self.monthly_budget:.2f} exceeded"
                )
        
        # Calculate cost
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Create record
        record = CostRecord(
            timestamp=datetime.now(),
            model=model,
            strategy=strategy,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            metadata=metadata or {}
        )
        
        # Store record
        self.records.append(record)
        self._save_records()
        
        # Update Prometheus metrics
        llm_tokens_total.labels(
            model=model.value,
            type="input",
            strategy=strategy
        ).inc(input_tokens)
        
        llm_tokens_total.labels(
            model=model.value,
            type="output",
            strategy=strategy
        ).inc(output_tokens)
        
        llm_cost_usd_total.labels(
            model=model.value,
            strategy=strategy
        ).inc(cost_usd)
        
        llm_cost_per_request_usd.labels(
            model=model.value,
            strategy=strategy
        ).observe(cost_usd)
        
        llm_requests_total.labels(
            model=model.value,
            strategy=strategy,
            status=status
        ).inc()
        
        self._update_budget_gauge()
        
        logger.debug(
            f"Tracked LLM request: {model.value} | {strategy} | "
            f"{input_tokens}+{output_tokens} tokens | ${cost_usd:.4f}"
        )
        
        return record
    
    def _calculate_cost(
        self,
        model: LLMModel,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost in USD"""
        pricing = self.PRICING.get(model)
        if not pricing:
            logger.warning(f"No pricing for {model}, assuming $0")
            return 0.0
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_monthly_cost(self, month: Optional[datetime] = None) -> float:
        """
        Get total cost for a month.
        
        Args:
            month: Month to query (default: current month)
        
        Returns:
            Total cost in USD
        """
        if month is None:
            month = datetime.now()
        
        start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        
        total = sum(
            record.cost_usd
            for record in self.records
            if start <= record.timestamp < end
        )
        
        return total
    
    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """Get total cost for a day"""
        if date is None:
            date = datetime.now()
        
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        total = sum(
            record.cost_usd
            for record in self.records
            if start <= record.timestamp < end
        )
        
        return total
    
    def get_cost_by_strategy(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get cost breakdown by strategy.
        
        Args:
            start: Start date (default: current month start)
            end: End date (default: now)
        
        Returns:
            Dictionary {strategy: cost_usd}
        """
        if start is None:
            start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if end is None:
            end = datetime.now()
        
        breakdown: Dict[str, float] = {}
        
        for record in self.records:
            if start <= record.timestamp <= end:
                breakdown[record.strategy] = (
                    breakdown.get(record.strategy, 0.0) + record.cost_usd
                )
        
        return breakdown
    
    def get_cost_by_model(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get cost breakdown by model"""
        if start is None:
            start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if end is None:
            end = datetime.now()
        
        breakdown: Dict[str, float] = {}
        
        for record in self.records:
            if start <= record.timestamp <= end:
                model_name = record.model.value
                breakdown[model_name] = (
                    breakdown.get(model_name, 0.0) + record.cost_usd
                )
        
        return breakdown
    
    def check_budget_status(self) -> Dict:
        """
        Check current budget status.
        
        Returns:
            Dictionary with budget info
        """
        monthly_cost = self.get_monthly_cost()
        remaining = self.monthly_budget - monthly_cost
        percentage_used = (monthly_cost / self.monthly_budget) * 100
        
        status = "ok"
        if percentage_used >= 100:
            status = "exceeded"
        elif percentage_used >= 80:
            status = "warning"
        
        return {
            "monthly_budget": self.monthly_budget,
            "monthly_cost": monthly_cost,
            "remaining": remaining,
            "percentage_used": percentage_used,
            "status": status
        }
    
    async def send_budget_alert(self, level: str, message: str) -> None:
        """
        Send budget alert.
        
        Args:
            level: Alert level (warning/critical)
            message: Alert message
        
        Note: Override this method to integrate with alerting system
        (Slack, email, PagerDuty, etc)
        """
        logger.warning(f"[BUDGET ALERT] {level.upper()}: {message}")
        
        # Integrate with multi-channel alerting
        await self._send_alert_to_channels(level, message, budget_info)
    
    async def _send_alert_to_channels(
        self, level: str, message: str, budget_info: dict
    ) -> None:
        """Send alerts to configured channels."""
        alert_payload = {
            "level": level.upper(),
            "message": message,
            "budget_info": budget_info,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Write to alert file for external consumption
        alert_file = Path("/var/log/vertice/budget_alerts.jsonl")
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(alert_file, "a") as f:
                import json
                f.write(json.dumps(alert_payload) + "\n")
            logger.debug(f"Budget alert written to {alert_file}")
        except Exception as e:
            logger.error(f"Failed to write budget alert: {e}")
    
    def generate_monthly_report(self, month: Optional[datetime] = None) -> str:
        """
        Generate monthly cost report.
        
        Args:
            month: Month to report (default: current month)
        
        Returns:
            Formatted report string
        """
        if month is None:
            month = datetime.now()
        
        monthly_cost = self.get_monthly_cost(month)
        breakdown_strategy = self.get_cost_by_strategy()
        breakdown_model = self.get_cost_by_model()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║            LLM COST REPORT - {month.strftime('%B %Y')}                      
╠══════════════════════════════════════════════════════════════════╣
║ BUDGET SUMMARY                                                    ║
║   Monthly Budget:    ${self.monthly_budget:>10.2f}                         ║
║   Total Cost:        ${monthly_cost:>10.2f}                         ║
║   Remaining:         ${self.monthly_budget - monthly_cost:>10.2f}                         ║
║   Usage:             {(monthly_cost / self.monthly_budget * 100):>9.1f}%                          ║
╠══════════════════════════════════════════════════════════════════╣
║ BY STRATEGY                                                       ║
"""
        
        for strategy, cost in sorted(breakdown_strategy.items(), key=lambda x: -x[1]):
            report += f"║   {strategy:<30} ${cost:>10.4f}               ║\n"
        
        report += "╠══════════════════════════════════════════════════════════════════╣\n"
        report += "║ BY MODEL                                                          ║\n"
        
        for model, cost in sorted(breakdown_model.items(), key=lambda x: -x[1]):
            report += f"║   {model:<30} ${cost:>10.4f}               ║\n"
        
        report += "╚══════════════════════════════════════════════════════════════════╝\n"
        
        return report
    
    def _load_records(self) -> List[CostRecord]:
        """Load cost records from storage"""
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            
            records = []
            for item in data:
                records.append(CostRecord(
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    model=LLMModel(item["model"]),
                    strategy=item["strategy"],
                    input_tokens=item["input_tokens"],
                    output_tokens=item["output_tokens"],
                    cost_usd=item["cost_usd"],
                    metadata=item.get("metadata", {})
                ))
            
            logger.info(f"Loaded {len(records)} cost records from {self.storage_path}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to load cost records: {e}")
            return []
    
    def _save_records(self) -> None:
        """Save cost records to storage"""
        try:
            data = [record.to_dict() for record in self.records]
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save cost records: {e}")
    
    def _update_budget_gauge(self) -> None:
        """Update Prometheus budget gauge"""
        monthly_cost = self.get_monthly_cost()
        remaining = self.monthly_budget - monthly_cost
        llm_monthly_budget_remaining_usd.set(max(0, remaining))


class BudgetExceededError(Exception):
    """Raised when monthly budget is exceeded"""
    pass


# Convenience function
def get_cost_tracker(
    monthly_budget: Optional[float] = None
) -> LLMCostTracker:
    """
    Get global cost tracker instance.
    
    Args:
        monthly_budget: Optional budget override
    
    Returns:
        LLMCostTracker singleton
    
    Example:
        >>> tracker = get_cost_tracker()
        >>> await tracker.track_request(
        ...     model=LLMModel.CLAUDE_3_7_SONNET,
        ...     strategy="code_patch",
        ...     input_tokens=1000,
        ...     output_tokens=500
        ... )
    """
    # Singleton pattern
    if not hasattr(get_cost_tracker, "_instance"):
        budget = monthly_budget or float(os.getenv("LLM_BUDGET_MONTHLY", "50.0"))
        get_cost_tracker._instance = LLMCostTracker(monthly_budget=budget)
    
    return get_cost_tracker._instance
