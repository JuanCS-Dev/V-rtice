"""Cost Tracker - Claude API Cost Monitoring and Budget Control.

Tracks Claude API usage costs and enforces budget limits to prevent
unexpected expenses. Monitors daily and monthly spending with alerts.

Cost Control Principle: Stewardship and financial responsibility
Biblical Foundation: Luke 14:28 - "Count the cost"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
from datetime import datetime
import logging
from typing import Any

from prometheus_client import Gauge

logger = logging.getLogger(__name__)


class CostTracker:
    """Track and limit Claude API costs.

    Monitors API usage costs in real-time and enforces budget limits.
    Provides alerts when approaching or exceeding budget thresholds.

    Architecture:
    - Per-request cost calculation based on token usage
    - Daily and monthly budget tracking
    - Thread-safe with asyncio.Lock
    - Prometheus metrics for monitoring
    - Alert logging for budget violations

    Pricing (Claude Sonnet 4.5, January 2025):
    - Input: $3.00 per million tokens
    - Output: $15.00 per million tokens

    Biblical Principle: Count the cost (Luke 14:28)
    """

    # Prometheus metrics
    cost_gauge = Gauge(
        "mvp_claude_cost_usd",
        "Claude API cost in USD",
        ["period"],  # daily, monthly
    )

    budget_remaining_gauge = Gauge(
        "mvp_claude_budget_remaining_usd",
        "Remaining budget in USD",
        ["period"],  # daily, monthly
    )

    def __init__(
        self,
        daily_budget_usd: float = 10.0,
        monthly_budget_usd: float = 300.0,
        input_cost_per_mtok: float = 3.00,
        output_cost_per_mtok: float = 15.00,
    ):
        """Initialize Cost Tracker.

        Args:
            daily_budget_usd: Daily budget limit in USD
            monthly_budget_usd: Monthly budget limit in USD
            input_cost_per_mtok: Cost per million input tokens (default: $3)
            output_cost_per_mtok: Cost per million output tokens (default: $15)
        """
        self.daily_budget = daily_budget_usd
        self.monthly_budget = monthly_budget_usd

        # Pricing (Sonnet 4.5, Jan 2025)
        self.input_cost_per_mtok = input_cost_per_mtok
        self.output_cost_per_mtok = output_cost_per_mtok

        # Cost tracking: date -> cost
        self.costs: dict[str, float] = {}

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Cost Tracker initialized: daily=${daily_budget_usd}, "
            f"monthly=${monthly_budget_usd}"
        )

    async def track_request(
        self,
        input_tokens: int,
        output_tokens: int,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        """Track API request cost and update budgets.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            timestamp: Request timestamp (default: now)

        Returns:
            Dict with cost details:
            - cost_usd: Cost of this request
            - input_cost: Input token cost
            - output_cost: Output token cost
            - daily_total: Total daily cost
            - monthly_total: Total monthly cost
            - daily_budget: Daily budget limit
            - monthly_budget: Monthly budget limit
            - within_daily_budget: Bool
            - within_monthly_budget: Bool
            - daily_remaining: Remaining daily budget
            - monthly_remaining: Remaining monthly budget
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_mtok
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_mtok
        total_cost = input_cost + output_cost

        date_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")

        async with self._lock:
            # Update daily cost
            if date_key not in self.costs:
                self.costs[date_key] = 0.0
            self.costs[date_key] += total_cost

            # Calculate totals
            daily_total = self.costs[date_key]
            monthly_total = sum(
                cost for key, cost in self.costs.items() if key.startswith(month_key)
            )

            # Check budgets
            within_daily = daily_total <= self.daily_budget
            within_monthly = monthly_total <= self.monthly_budget

            # Calculate remaining
            daily_remaining = max(0, self.daily_budget - daily_total)
            monthly_remaining = max(0, self.monthly_budget - monthly_total)

            result = {
                "cost_usd": total_cost,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "daily_total": daily_total,
                "monthly_total": monthly_total,
                "daily_budget": self.daily_budget,
                "monthly_budget": self.monthly_budget,
                "within_daily_budget": within_daily,
                "within_monthly_budget": within_monthly,
                "daily_remaining": daily_remaining,
                "monthly_remaining": monthly_remaining,
                "daily_percent_used": (daily_total / self.daily_budget * 100)
                if self.daily_budget > 0
                else 0,
                "monthly_percent_used": (monthly_total / self.monthly_budget * 100)
                if self.monthly_budget > 0
                else 0,
            }

            # Alert if over budget
            if not within_daily:
                logger.error(
                    f"🚨 Daily budget exceeded: ${daily_total:.4f} / ${self.daily_budget:.2f} "
                    f"({result['daily_percent_used']:.1f}%)"
                )

            if not within_monthly:
                logger.error(
                    f"🚨 Monthly budget exceeded: ${monthly_total:.2f} / ${self.monthly_budget:.2f} "
                    f"({result['monthly_percent_used']:.1f}%)"
                )

            # Warning at 80% threshold
            if (
                within_daily
                and result["daily_percent_used"] >= 80
                and result["daily_percent_used"] < 100
            ):
                logger.warning(
                    f"⚠️  Daily budget at {result['daily_percent_used']:.1f}% "
                    f"(${daily_total:.4f} / ${self.daily_budget:.2f})"
                )

            if (
                within_monthly
                and result["monthly_percent_used"] >= 80
                and result["monthly_percent_used"] < 100
            ):
                logger.warning(
                    f"⚠️  Monthly budget at {result['monthly_percent_used']:.1f}% "
                    f"(${monthly_total:.2f} / ${self.monthly_budget:.2f})"
                )

            # Update Prometheus metrics
            self.cost_gauge.labels(period="daily").set(daily_total)
            self.cost_gauge.labels(period="monthly").set(monthly_total)
            self.budget_remaining_gauge.labels(period="daily").set(daily_remaining)
            self.budget_remaining_gauge.labels(period="monthly").set(monthly_remaining)

            logger.debug(
                f"💰 Request cost: ${total_cost:.6f} "
                f"(input: {input_tokens} tokens, output: {output_tokens} tokens)"
            )

            return result

    async def is_within_budget(self, timestamp: datetime | None = None) -> bool:
        """Check if current usage is within budget limits.

        Args:
            timestamp: Timestamp to check (default: now)

        Returns:
            True if within both daily and monthly budgets
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        date_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")

        async with self._lock:
            daily_total = self.costs.get(date_key, 0.0)
            monthly_total = sum(
                cost for key, cost in self.costs.items() if key.startswith(month_key)
            )

            return (
                daily_total <= self.daily_budget
                and monthly_total <= self.monthly_budget
            )

    async def get_current_costs(
        self, timestamp: datetime | None = None
    ) -> dict[str, Any]:
        """Get current cost statistics.

        Args:
            timestamp: Timestamp to check (default: now)

        Returns:
            Dict with current daily and monthly costs, budgets, and remaining amounts
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        date_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")

        async with self._lock:
            daily_total = self.costs.get(date_key, 0.0)
            monthly_total = sum(
                cost for key, cost in self.costs.items() if key.startswith(month_key)
            )

            return {
                "daily_total": daily_total,
                "monthly_total": monthly_total,
                "daily_budget": self.daily_budget,
                "monthly_budget": self.monthly_budget,
                "daily_remaining": max(0, self.daily_budget - daily_total),
                "monthly_remaining": max(0, self.monthly_budget - monthly_total),
                "within_daily_budget": daily_total <= self.daily_budget,
                "within_monthly_budget": monthly_total <= self.monthly_budget,
                "daily_percent_used": (daily_total / self.daily_budget * 100)
                if self.daily_budget > 0
                else 0,
                "monthly_percent_used": (monthly_total / self.monthly_budget * 100)
                if self.monthly_budget > 0
                else 0,
            }

    async def reset_daily_costs(self, date: str | None = None) -> None:
        """Reset costs for a specific date (for testing).

        Args:
            date: Date key (YYYY-MM-DD) to reset, or None for today
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        async with self._lock:
            if date in self.costs:
                del self.costs[date]
                logger.info(f"Reset costs for {date}")

    async def get_all_costs(self) -> dict[str, float]:
        """Get all tracked costs (for debugging/monitoring).

        Returns:
            Dict of date -> cost
        """
        async with self._lock:
            return dict(self.costs)
