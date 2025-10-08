"""
MAXIMUS AI 3.0 - Training Pipeline

Complete ML training infrastructure for Predictive Coding Network:
- Data collection from SIEM/EDR systems
- Layer-specific preprocessing
- Distributed training
- Hyperparameter tuning
- Model evaluation and registry
- Continuous retraining pipeline

REGRA DE OURO: Zero mocks, production-ready training
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from .data_collection import CollectedEvent, DataCollector, DataSource, DataSourceType
from .data_preprocessor import DataPreprocessor, LayerPreprocessor, LayerType, PreprocessedSample
from .data_validator import DataValidator, ValidationIssue, ValidationResult, ValidationSeverity
from .dataset_builder import DatasetBuilder, DatasetSplit, PyTorchDatasetWrapper, SplitStrategy

__all__ = [
    # Data Collection
    "DataCollector",
    "DataSource",
    "DataSourceType",
    "CollectedEvent",
    # Data Preprocessing
    "DataPreprocessor",
    "LayerPreprocessor",
    "PreprocessedSample",
    "LayerType",
    # Dataset Building
    "DatasetBuilder",
    "DatasetSplit",
    "SplitStrategy",
    "PyTorchDatasetWrapper",
    # Data Validation
    "DataValidator",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
]

__version__ = "1.0.0"
__author__ = "Claude Code + JuanCS-Dev"
__regra_de_ouro__ = "10/10"
