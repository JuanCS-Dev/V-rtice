#!/bin/bash
#
# MAXIMUS AI 3.0 - Automated Model Retraining Script
#
# Automates the complete retraining pipeline:
# 1. Collect new data
# 2. Preprocess data
# 3. Build datasets
# 4. Validate data quality
# 5. Train models
# 6. Evaluate models
# 7. Deploy to production
#
# REGRA DE OURO: Production-ready automation
# Author: Claude Code + JuanCS-Dev
# Date: 2025-10-06

set -e  # Exit on error
set -u  # Error on undefined variables

# =============================================================================
# Configuration
# =============================================================================

# Directories
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRAINING_DIR="$PROJECT_DIR/training"
DATA_DIR="$TRAINING_DIR/data"
CHECKPOINT_DIR="$TRAINING_DIR/checkpoints"
LOG_DIR="$TRAINING_DIR/logs"

# Python executable
PYTHON="${PYTHON:-python3}"

# Logging
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/retrain_${TIMESTAMP}.log"

# Layers to retrain (space-separated)
LAYERS="${LAYERS:-layer1 layer2 layer3 layer4 layer5}"

# Training parameters
BATCH_SIZE="${BATCH_SIZE:-32}"
NUM_EPOCHS="${NUM_EPOCHS:-100}"
LEARNING_RATE="${LEARNING_RATE:-0.001}"

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
    exit 1
}

check_dependencies() {
    log "Checking dependencies..."

    if ! command -v $PYTHON &> /dev/null; then
        error "Python not found. Install Python 3.11+"
    fi

    # Check Python packages
    $PYTHON -c "import torch" 2>/dev/null || error "PyTorch not installed"
    $PYTHON -c "import numpy" 2>/dev/null || error "NumPy not installed"
    $PYTHON -c "import pandas" 2>/dev/null || error "Pandas not installed"

    log "✓ All dependencies available"
}

setup_directories() {
    log "Setting up directories..."

    mkdir -p "$DATA_DIR/raw"
    mkdir -p "$DATA_DIR/preprocessed"
    mkdir -p "$DATA_DIR/splits"
    mkdir -p "$CHECKPOINT_DIR"
    mkdir -p "$LOG_DIR"

    log "✓ Directories created"
}

# =============================================================================
# Data Pipeline
# =============================================================================

collect_data() {
    log "Step 1/7: Collecting data..."

    cd "$PROJECT_DIR"

    $PYTHON -c "
from training.data_collection import DataCollector, DataSource, DataSourceType
from pathlib import Path

# Example: Collect from demo dataset
source = DataSource(
    name='demo_events',
    source_type=DataSourceType.JSON_FILE,
    connection_params={'path': 'demo/synthetic_events.json'}
)

collector = DataCollector(
    sources=[source],
    output_dir=Path('$DATA_DIR/raw')
)

events = list(collector.collect(max_events=10000))
print(f'Collected {len(events)} events')

# Save
collector.save_to_file(events, 'collected_events_${TIMESTAMP}.json')
" 2>&1 | tee -a "$LOG_FILE"

    log "✓ Data collection complete"
}

preprocess_data() {
    local layer=$1
    log "Step 2/7: Preprocessing data for $layer..."

    cd "$PROJECT_DIR"

    $PYTHON -c "
from training.data_collection import DataCollector
from training.data_preprocessor import DataPreprocessor, LayerType
from pathlib import Path
import json

# Load collected events
with open('$DATA_DIR/raw/collected_events_${TIMESTAMP}.json') as f:
    events = json.load(f)

# Preprocess
preprocessor = DataPreprocessor(output_dir=Path('$DATA_DIR/preprocessed'))

layer_map = {
    'layer1': LayerType.LAYER1_SENSORY,
    'layer2': LayerType.LAYER2_BEHAVIORAL,
    'layer3': LayerType.LAYER3_OPERATIONAL
}

layer_type = layer_map.get('$layer', LayerType.LAYER1_SENSORY)

samples = []
for event in events:
    sample = preprocessor.preprocess_event(event, layers=[layer_type])
    samples.append(sample)

print(f'Preprocessed {len(samples)} samples for $layer')

# Save
preprocessor.save_samples(samples, '${layer}_samples_${TIMESTAMP}')
" 2>&1 | tee -a "$LOG_FILE"

    log "✓ Preprocessing complete for $layer"
}

build_datasets() {
    local layer=$1
    log "Step 3/7: Building datasets for $layer..."

    cd "$PROJECT_DIR"

    $PYTHON -c "
from training.dataset_builder import DatasetBuilder, SplitStrategy
from pathlib import Path
import numpy as np

# Load preprocessed samples
data = np.load('$DATA_DIR/preprocessed/${layer}_samples_${TIMESTAMP}.npz')
features = data['features']
labels = data['labels']
sample_ids = data['sample_ids'].tolist()

# Build datasets
builder = DatasetBuilder(
    features=features,
    labels=labels,
    sample_ids=sample_ids,
    output_dir=Path('$DATA_DIR/splits'),
    random_seed=42
)

# Create stratified splits
splits = builder.create_splits(
    strategy=SplitStrategy.STRATIFIED,
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
    balance_classes=True
)

print(f'Train: {len(splits[\"train\"])} samples')
print(f'Val: {len(splits[\"val\"])} samples')
print(f'Test: {len(splits[\"test\"])} samples')

# Save
builder.save_splits(splits, prefix='${layer}_${TIMESTAMP}')
" 2>&1 | tee -a "$LOG_FILE"

    log "✓ Dataset building complete for $layer"
}

validate_data() {
    local layer=$1
    log "Step 4/7: Validating data for $layer..."

    cd "$PROJECT_DIR"

    $PYTHON -c "
from training.data_validator import DataValidator
from pathlib import Path
import numpy as np

# Load training data
data = np.load('$DATA_DIR/splits/${layer}_${TIMESTAMP}_train.npz')
features = data['features']
labels = data['labels']

# Validate
validator = DataValidator(
    features=features,
    labels=labels
)

result = validator.validate(
    check_missing=True,
    check_outliers=True,
    check_labels=True,
    check_distributions=True
)

result.print_report()

if not result.passed:
    print('VALIDATION FAILED')
    exit(1)

print('VALIDATION PASSED')
" 2>&1 | tee -a "$LOG_FILE"

    if [ $? -ne 0 ]; then
        error "Data validation failed for $layer"
    fi

    log "✓ Data validation passed for $layer"
}

train_model() {
    local layer=$1
    log "Step 5/7: Training model for $layer..."

    cd "$PROJECT_DIR"

    case "$layer" in
        layer1)
            $PYTHON training/train_layer1_vae.py \
                --train_data "$DATA_DIR/splits/${layer}_${TIMESTAMP}_train.npz" \
                --val_data "$DATA_DIR/splits/${layer}_${TIMESTAMP}_val.npz" \
                --batch_size "$BATCH_SIZE" \
                --num_epochs "$NUM_EPOCHS" \
                --learning_rate "$LEARNING_RATE" \
                --checkpoint_dir "$CHECKPOINT_DIR" \
                --log_dir "$LOG_DIR" \
                2>&1 | tee -a "$LOG_FILE"
            ;;
        *)
            log "Training for $layer not implemented yet, skipping..."
            return 0
            ;;
    esac

    if [ $? -ne 0 ]; then
        error "Training failed for $layer"
    fi

    log "✓ Training complete for $layer"
}

evaluate_model() {
    local layer=$1
    log "Step 6/7: Evaluating model for $layer..."

    cd "$PROJECT_DIR"

    $PYTHON -c "
from training.evaluator import ModelEvaluator
from training.model_registry import ModelRegistry
from pathlib import Path
import numpy as np
import torch

# Load test data
data = np.load('$DATA_DIR/splits/${layer}_${TIMESTAMP}_test.npz')
test_features = data['features']
test_labels = data['labels']

# Load best model
registry = ModelRegistry(registry_dir=Path('$TRAINING_DIR/models'))
model_path = Path('$CHECKPOINT_DIR/${layer}_vae_best.pt')

if not model_path.exists():
    print(f'Model not found: {model_path}')
    exit(1)

# Load model architecture (example for layer1)
if '$layer' == 'layer1':
    from training.train_layer1_vae import Layer1VAE
    model = Layer1VAE(input_dim=test_features.shape[1])
    model.load_state_dict(torch.load(model_path, weights_only=True))

    # Evaluate
    evaluator = ModelEvaluator(
        model=model,
        test_features=test_features,
        test_labels=test_labels
    )

    metrics = evaluator.evaluate()
    evaluator.print_report(metrics)

    # Save report
    evaluator.save_report(metrics, Path('$LOG_DIR/${layer}_evaluation_${TIMESTAMP}.json'))
" 2>&1 | tee -a "$LOG_FILE"

    log "✓ Evaluation complete for $layer"
}

deploy_model() {
    local layer=$1
    log "Step 7/7: Deploying model for $layer..."

    # Model deployment logic would go here
    # For now, just copy to production directory

    PROD_DIR="$PROJECT_DIR/predictive_coding/models"
    mkdir -p "$PROD_DIR"

    if [ -f "$CHECKPOINT_DIR/${layer}_vae_best.pt" ]; then
        cp "$CHECKPOINT_DIR/${layer}_vae_best.pt" "$PROD_DIR/${layer}_model.pt"
        log "✓ Model deployed: $PROD_DIR/${layer}_model.pt"
    else
        log "⚠ Model not found, skipping deployment"
    fi
}

# =============================================================================
# Main Pipeline
# =============================================================================

run_pipeline_for_layer() {
    local layer=$1

    log "========================================"
    log "Processing $layer"
    log "========================================"

    preprocess_data "$layer"
    build_datasets "$layer"
    validate_data "$layer"
    train_model "$layer"
    evaluate_model "$layer"
    deploy_model "$layer"

    log "✓ Pipeline complete for $layer"
}

main() {
    log "=========================================="
    log "MAXIMUS AI 3.0 - Automated Retraining"
    log "=========================================="

    # Setup
    check_dependencies
    setup_directories

    # Collect data once (shared across all layers)
    collect_data

    # Process each layer
    for layer in $LAYERS; do
        run_pipeline_for_layer "$layer"
    done

    log "=========================================="
    log "✓ All pipelines complete!"
    log "=========================================="
    log "Log file: $LOG_FILE"
}

# =============================================================================
# Script Entry Point
# =============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --layers)
            LAYERS="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --epochs)
            NUM_EPOCHS="$2"
            shift 2
            ;;
        --lr)
            LEARNING_RATE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --layers LAYERS      Space-separated layer names (default: layer1 layer2 layer3 layer4 layer5)"
            echo "  --batch-size SIZE    Batch size (default: 32)"
            echo "  --epochs N           Number of epochs (default: 100)"
            echo "  --lr RATE            Learning rate (default: 0.001)"
            echo "  --help               Show this help"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main pipeline
main

exit 0
