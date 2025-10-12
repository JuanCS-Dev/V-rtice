"""
PostgreSQL storage for A/B testing results.

Fundamentação: Sistema imunológico tem memória (B/T cells).
Digital equivalent = persistent storage of ML validation comparisons.
"""
import asyncpg
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class ABTestResult(BaseModel):
    """Single A/B test result."""
    apv_id: str
    cve_id: Optional[str] = None
    patch_id: str
    
    ml_confidence: float = Field(ge=0.0, le=1.0)
    ml_prediction: bool
    ml_execution_time_ms: int = Field(ge=0)
    
    wargaming_result: bool
    wargaming_execution_time_ms: int = Field(ge=0)
    
    ml_correct: bool
    disagreement_reason: Optional[str] = None
    
    model_version: str = "rf_v1"
    ab_test_version: str = "1.0"
    
    shap_values: Optional[Dict[str, float]] = None


class ConfusionMatrix(BaseModel):
    """Confusion matrix metrics."""
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        denominator = self.true_positive + self.false_positive
        if denominator == 0:
            return 0.0
        return self.true_positive / denominator
    
    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)"""
        denominator = self.true_positive + self.false_negative
        if denominator == 0:
            return 0.0
        return self.true_positive / denominator
    
    @property
    def f1_score(self) -> float:
        """F1 Score: harmonic mean of precision and recall"""
        prec_plus_rec = self.precision + self.recall
        if prec_plus_rec == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / prec_plus_rec
    
    @property
    def accuracy(self) -> float:
        """Accuracy: (TP + TN) / total"""
        total = (
            self.true_positive + self.false_positive +
            self.false_negative + self.true_negative
        )
        if total == 0:
            return 0.0
        return (self.true_positive + self.true_negative) / total


class ABTestStore:
    """
    Storage and retrieval for A/B test results.
    
    Fundamentação: Adaptive immunity requires memory of past encounters.
    This store enables continuous learning from ML vs wargaming comparisons.
    """
    
    def __init__(self, db_url: str):
        """
        Initialize A/B test store.
        
        Args:
            db_url: PostgreSQL connection URL
        """
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish database connection pool."""
        self.pool = await asyncpg.create_pool(
            self.db_url, 
            min_size=2, 
            max_size=10,
            command_timeout=60
        )
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def store_result(self, result: ABTestResult) -> int:
        """
        Store A/B test result.
        
        Args:
            result: A/B test result to store
            
        Returns:
            ID of inserted record
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ml_ab_tests (
                    apv_id, cve_id, patch_id,
                    ml_confidence, ml_prediction, ml_execution_time_ms,
                    wargaming_result, wargaming_execution_time_ms,
                    ml_correct, disagreement_reason,
                    model_version, ab_test_version, shap_values
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                RETURNING id
                """,
                result.apv_id,
                result.cve_id,
                result.patch_id,
                result.ml_confidence,
                result.ml_prediction,
                result.ml_execution_time_ms,
                result.wargaming_result,
                result.wargaming_execution_time_ms,
                result.ml_correct,
                result.disagreement_reason,
                result.model_version,
                result.ab_test_version,
                result.shap_values
            )
            return row['id']
    
    async def get_confusion_matrix(
        self,
        model_version: str = "rf_v1",
        time_range: timedelta = timedelta(hours=24)
    ) -> ConfusionMatrix:
        """
        Calculate confusion matrix for given timeframe.
        
        Args:
            model_version: Model version to filter by
            time_range: Time window (default: 24h)
            
        Returns:
            Confusion matrix with metrics
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM calculate_confusion_matrix($1, $2)
                """,
                model_version,
                time_range
            )
            
            return ConfusionMatrix(
                true_positive=row['true_positive'],
                false_positive=row['false_positive'],
                false_negative=row['false_negative'],
                true_negative=row['true_negative']
            )
    
    async def get_recent_tests(
        self,
        limit: int = 50,
        model_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent A/B test results.
        
        Args:
            limit: Maximum number of results (default: 50)
            model_version: Filter by model version (optional)
            
        Returns:
            List of recent test results
        """
        query = """
            SELECT 
                id, apv_id, cve_id, patch_id,
                ml_confidence, ml_prediction, ml_execution_time_ms,
                wargaming_result, wargaming_execution_time_ms,
                ml_correct, disagreement_reason,
                model_version, created_at
            FROM ml_ab_tests
        """
        
        if model_version:
            query += f" WHERE model_version = '{model_version}'"
        
        query += " ORDER BY created_at DESC LIMIT $1"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            
            return [dict(row) for row in rows]
    
    async def get_accuracy_over_time(
        self,
        model_version: str = "rf_v1",
        time_range: timedelta = timedelta(days=7),
        bucket_size: str = "1 hour"
    ) -> List[Dict[str, Any]]:
        """
        Get accuracy trends over time (bucketed).
        
        Args:
            model_version: Model version to filter by
            time_range: Total time window
            bucket_size: Size of each time bucket (e.g., '1 hour', '1 day')
            
        Returns:
            List of {bucket, total_tests, accuracy, avg_confidence}
        """
        async with self.pool.acquire() as conn:
            # Calculate cutoff time in Python to avoid SQL type issues
            cutoff_time = datetime.now() - time_range
            
            rows = await conn.fetch(
                """
                SELECT 
                    DATE_TRUNC('hour', created_at) as bucket,
                    COUNT(*) as total_tests,
                    AVG(CASE WHEN ml_correct THEN 1.0 ELSE 0.0 END) as accuracy,
                    AVG(ml_confidence) as avg_confidence
                FROM ml_ab_tests
                WHERE model_version = $1
                  AND created_at > $2
                GROUP BY bucket
                ORDER BY bucket DESC
                """,
                model_version,
                cutoff_time
            )
            
            return [dict(row) for row in rows]
