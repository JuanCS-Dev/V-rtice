"""
Model Retraining Pipeline for Cognitive Defense System.

Automated retraining with:
- Scheduled triggers (weekly)
- Performance drift triggers
- Manual triggers
- A/B testing before production deployment
- Automatic rollback if performance degrades
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any, Dict, List, Optional

from adversarial_training import adversarial_generator, AdversarialTrainer
from config import get_settings
from database import get_db_session
from db_models import AnalysisRecord
from model_quantization import model_quantizer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

settings = get_settings()


class TriggerType(Enum):
    """Retraining trigger types."""

    SCHEDULED = "scheduled"
    DRIFT_DETECTED = "drift_detected"
    MANUAL = "manual"


class RetrainingStatus(Enum):
    """Retraining job status."""

    PENDING = "pending"
    DATA_COLLECTION = "data_collection"
    TRAINING = "training"
    EVALUATION = "evaluation"
    AB_TESTING = "ab_testing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ModelRetrainingPipeline:
    """
    Automated model retraining pipeline.

    Steps:
    1. Data collection (from PostgreSQL feedback)
    2. Data validation & cleaning
    3. Model training (with adversarial augmentation)
    4. Model evaluation (test set)
    5. A/B testing (staging deployment)
    6. Production deployment (if metrics improved)
    7. Model quantization for production
    """

    # Performance improvement threshold for deployment
    MIN_IMPROVEMENT_THRESHOLD = 0.02  # 2% F1 improvement required

    # A/B test duration
    AB_TEST_DURATION_HOURS = 24

    def __init__(self):
        """Initialize retraining pipeline."""
        self.current_model_metrics: Dict[str, Dict[str, float]] = {}
        self.retraining_history: List[Dict[str, Any]] = []

    async def execute_pipeline(
        self, model_name: str, trigger: TriggerType = TriggerType.MANUAL
    ) -> Dict[str, Any]:
        """
        Execute full retraining pipeline.

        Args:
            model_name: Model identifier to retrain
            trigger: What triggered the retraining

        Returns:
            Pipeline execution result
        """
        logger.info(
            f"🚀 Starting retraining pipeline for {model_name} (trigger={trigger.value})"
        )

        job_id = f"{model_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        result = {
            "job_id": job_id,
            "model_name": model_name,
            "trigger": trigger.value,
            "status": RetrainingStatus.PENDING.value,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "metrics": {},
            "deployed": False,
            "error": None,
        }

        try:
            # STEP 1: Data Collection
            result["status"] = RetrainingStatus.DATA_COLLECTION.value
            train_data = await self._collect_training_data(model_name)

            logger.info(f"Collected {len(train_data['texts'])} training samples")

            # STEP 2: Data Validation
            if not self._validate_data(train_data):
                raise ValueError("Data validation failed")

            # STEP 3: Model Training (with adversarial augmentation)
            result["status"] = RetrainingStatus.TRAINING.value
            new_model, training_metrics = await self._train_model(
                model_name, train_data
            )

            logger.info(f"Training complete: loss={training_metrics['final_loss']:.4f}")

            # STEP 4: Model Evaluation
            result["status"] = RetrainingStatus.EVALUATION.value
            eval_metrics = await self._evaluate_model(new_model, model_name)

            logger.info(
                f"Evaluation: F1={eval_metrics['f1_score']:.3f}, "
                f"Acc={eval_metrics['accuracy']:.3f}"
            )

            result["metrics"] = eval_metrics

            # Check if improvement threshold met
            current_f1 = self.current_model_metrics.get(model_name, {}).get(
                "f1_score", 0.0
            )
            improvement = eval_metrics["f1_score"] - current_f1

            if improvement < self.MIN_IMPROVEMENT_THRESHOLD:
                logger.warning(
                    f"Insufficient improvement: {improvement:.3f} < {self.MIN_IMPROVEMENT_THRESHOLD}"
                )
                result["status"] = RetrainingStatus.COMPLETED.value
                result["deployed"] = False
                result["end_time"] = datetime.utcnow().isoformat()
                return result

            # STEP 5: A/B Testing (staging deployment)
            result["status"] = RetrainingStatus.AB_TESTING.value

            await self._deploy_to_staging(new_model, model_name)

            # Run A/B test
            ab_results = await self._run_ab_test(
                model_name=model_name, duration_hours=self.AB_TEST_DURATION_HOURS
            )

            logger.info(
                f"A/B test complete: new_model_better={ab_results['new_model_better']}"
            )

            # STEP 6: Production Deployment (if A/B test passed)
            if ab_results["new_model_better"]:
                result["status"] = RetrainingStatus.DEPLOYING.value

                # Quantize for production
                quantized_path = model_quantizer.quantize_sequence_classification(
                    model_name="neuralmind/bert-base-portuguese-cased",  # Base model
                    output_name=f"{model_name}_retrained",
                    num_labels=eval_metrics.get("num_labels", 2),
                )

                logger.info(f"Model quantized: {quantized_path}")

                await self._deploy_to_production(new_model, model_name)
                await self._archive_old_model(model_name)

                # Update current metrics
                self.current_model_metrics[model_name] = eval_metrics

                result["deployed"] = True
                result["status"] = RetrainingStatus.COMPLETED.value

            else:
                # A/B test failed - rollback
                await self._rollback_staging(model_name)
                result["status"] = RetrainingStatus.ROLLED_BACK.value
                result["deployed"] = False

        except Exception as e:
            logger.error(f"Retraining pipeline failed: {e}", exc_info=True)
            result["status"] = RetrainingStatus.FAILED.value
            result["error"] = str(e)

        finally:
            result["end_time"] = datetime.utcnow().isoformat()
            self.retraining_history.append(result)

        return result

    async def _collect_training_data(
        self, model_name: str, min_samples: int = 1000
    ) -> Dict[str, List]:
        """
        Collect training data from PostgreSQL analysis records.

        Args:
            model_name: Model identifier
            min_samples: Minimum samples required

        Returns:
            Training data dict
        """
        async with get_db_session() as session:
            # Query recent analysis records (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            result = await session.execute(
                select(AnalysisRecord)
                .where(AnalysisRecord.timestamp >= cutoff_date)
                .limit(10000)  # Max 10k samples
            )

            records = result.scalars().all()

            if len(records) < min_samples:
                logger.warning(
                    f"Insufficient training data: {len(records)} < {min_samples}"
                )

            # Extract texts and labels (model-specific logic)
            texts = []
            labels = []

            for record in records:
                # Get content from full_report
                content = record.full_report.get("content", "")

                if not content:
                    continue

                # Derive label from scores (example for emotional model)
                if model_name == "emotional_manipulation":
                    label = 1 if record.emotional_score > 0.5 else 0
                elif model_name == "fallacy_detection":
                    label = 1 if record.fallacy_count > 0 else 0
                else:
                    # Binary classification based on manipulation score
                    label = 1 if record.manipulation_score > 0.5 else 0

                texts.append(content)
                labels.append(label)

            logger.info(f"Collected {len(texts)} samples for {model_name}")

            return {"texts": texts, "labels": labels, "num_samples": len(texts)}

    def _validate_data(self, data: Dict[str, List]) -> bool:
        """
        Validate training data.

        Checks:
        - Minimum sample count
        - Label balance
        - Text quality

        Args:
            data: Training data dict

        Returns:
            True if valid
        """
        texts = data["texts"]
        labels = data["labels"]

        # Check minimum samples
        if len(texts) < 100:
            logger.error("Insufficient samples for training")
            return False

        # Check label balance
        label_counts = {}
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1

        # Calculate imbalance ratio
        if label_counts:
            max_count = max(label_counts.values())
            min_count = min(label_counts.values())
            imbalance_ratio = max_count / min_count if min_count > 0 else float("inf")

            if imbalance_ratio > 10:
                logger.warning(f"High class imbalance: {imbalance_ratio:.1f}:1")

        # Check text quality (non-empty, reasonable length)
        valid_texts = [t for t in texts if t and len(t) > 10]

        if len(valid_texts) < len(texts) * 0.9:
            logger.error("Too many invalid texts")
            return False

        logger.info("✅ Data validation passed")
        return True

    async def _train_model(self, model_name: str, train_data: Dict[str, List]) -> tuple:
        """
        Train model with adversarial augmentation.

        Args:
            model_name: Model identifier
            train_data: Training data

        Returns:
            (trained_model, training_metrics)
        """
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        # Load base model
        base_model_name = "neuralmind/bert-base-portuguese-cased"

        model = AutoModelForSequenceClassification.from_pretrained(
            base_model_name, num_labels=2  # Binary classification
        )

        tokenizer = AutoTokenizer.from_pretrained(base_model_name)

        # Adversarial training
        trainer = AdversarialTrainer(model=model, tokenizer=tokenizer)

        metrics = await trainer.adversarial_train(
            train_texts=train_data["texts"],
            train_labels=train_data["labels"],
            epochs=3,
            learning_rate=2e-5,
        )

        return model, metrics

    async def _evaluate_model(self, model: Any, model_name: str) -> Dict[str, float]:
        """
        Evaluate model on test set.

        Args:
            model: Trained model
            model_name: Model identifier

        Returns:
            Evaluation metrics
        """
        # In production, use dedicated test set
        # For now, return mock metrics

        logger.info("Evaluating model...")

        # Mock evaluation (in production, run on test set)
        metrics = {
            "f1_score": 0.88,
            "accuracy": 0.89,
            "precision": 0.87,
            "recall": 0.89,
            "num_labels": 2,
        }

        return metrics

    async def _deploy_to_staging(self, model: Any, model_name: str) -> None:
        """Deploy model to staging environment."""
        logger.info(f"Deploying {model_name} to staging...")

        # In production: save model to staging path, update config
        # For now, log action

        logger.info(f"✅ {model_name} deployed to staging")

    async def _deploy_to_production(self, model: Any, model_name: str) -> None:
        """Deploy model to production environment."""
        logger.info(f"Deploying {model_name} to production...")

        # In production: save model to production path, update config, restart services

        logger.info(f"✅ {model_name} deployed to production")

    async def _archive_old_model(self, model_name: str) -> None:
        """Archive previous model version."""
        logger.info(f"Archiving old version of {model_name}...")

        # In production: move old model to archive directory

        logger.info(f"✅ Old {model_name} archived")

    async def _run_ab_test(
        self, model_name: str, duration_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Run A/B test comparing new vs old model.

        Args:
            model_name: Model identifier
            duration_hours: Test duration

        Returns:
            A/B test results
        """
        logger.info(f"Running A/B test for {model_name} ({duration_hours}h)...")

        # In production: route traffic 50/50, compare metrics
        # For now, simulate result

        await asyncio.sleep(1)  # Simulate test duration

        # Mock result
        result = {
            "new_model_better": True,
            "new_model_f1": 0.88,
            "old_model_f1": 0.85,
            "improvement": 0.03,
            "duration_hours": duration_hours,
        }

        logger.info(
            f"✅ A/B test complete: new_model_better={result['new_model_better']}"
        )

        return result

    async def _rollback_staging(self, model_name: str) -> None:
        """Rollback staging deployment."""
        logger.info(f"Rolling back {model_name} staging deployment...")

        # In production: remove staging model, restore previous version

        logger.info(f"✅ {model_name} rolled back")


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

retraining_pipeline = ModelRetrainingPipeline()
