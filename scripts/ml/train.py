#!/usr/bin/env python3
"""
Train Random Forest classifier for patch validity prediction.

Usage:
    python scripts/ml/train.py
    python scripts/ml/train.py --dataset data/ml/custom.csv
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        classification_report,
        confusion_matrix,
        roc_auc_score,
        precision_recall_curve,
    )
    import joblib
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install pandas numpy scikit-learn joblib")
    sys.exit(1)


def train_patch_validity_classifier(
    dataset_path: str = "data/ml/wargaming_dataset.csv",
    model_output_path: str = "models/patch_validity_rf.joblib",
    metrics_output_path: str = "models/patch_validity_metrics.json",
) -> dict:
    """
    Train Random Forest classifier to predict patch validity.
    
    Args:
        dataset_path: Path to CSV with wargaming results
        model_output_path: Where to save trained model
        metrics_output_path: Where to save metrics JSON
        
    Returns:
        Dict with training metrics
    """
    
    print("=" * 80)
    print("🧠 ML PATCH VALIDITY CLASSIFIER TRAINING")
    print("=" * 80)
    
    # Load dataset
    print(f"\n📊 Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"   Samples: {len(df)}")
    
    # Separate features and target
    X = df.drop('patch_validated', axis=1)
    y = df['patch_validated']
    
    print(f"\n📋 Features: {list(X.columns)}")
    print(f"   Feature count: {len(X.columns)}")
    
    print(f"\n📊 Class distribution:")
    class_counts = y.value_counts()
    for label, count in class_counts.items():
        label_name = "Valid" if label == 1 else "Invalid"
        pct = 100.0 * count / len(y)
        print(f"   {label_name} patches: {count} ({pct:.1f}%)")
    
    # Check minimum samples
    if len(df) < 10:
        print(f"\n⚠️  WARNING: Only {len(df)} samples. Need 20+ for good training.")
        print("   Model will be trained but may have low accuracy.")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(df) >= 10 else None
    )
    
    print(f"\n🔀 Train/Test split:")
    print(f"   Train: {len(X_train)} samples")
    print(f"   Test: {len(X_test)} samples")
    
    # Train Random Forest
    print(f"\n🌲 Training Random Forest...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,  # More lenient for small datasets
        min_samples_leaf=1,
        random_state=42,
        class_weight='balanced',  # Handle imbalance
    )
    
    clf.fit(X_train, y_train)
    print(f"   ✅ Model trained")
    
    # Cross-validation (if enough samples)
    if len(X_train) >= 5:
        cv_scores = cross_val_score(clf, X_train, y_train, cv=min(5, len(X_train)), scoring='f1')
        print(f"   CV F1 scores: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    # Evaluate on test set
    print(f"\n📈 Evaluating on test set...")
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]  # Probability of valid patch
    
    # Metrics
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    # ROC-AUC (if both classes present)
    try:
        roc_auc = roc_auc_score(y_test, y_proba)
    except ValueError:
        roc_auc = 0.0  # Only one class in test set
    
    metrics = {
        'accuracy': float(report['accuracy']),
        'precision': float(report.get('1', {}).get('precision', 0.0)),
        'recall': float(report.get('1', {}).get('recall', 0.0)),
        'f1': float(report.get('1', {}).get('f1-score', 0.0)),
        'roc_auc': float(roc_auc),
        'support_train': int(len(y_train)),
        'support_test': int(len(y_test)),
        'confusion_matrix': cm.tolist(),
        'feature_importance': {
            feat: float(imp) 
            for feat, imp in zip(X.columns, clf.feature_importances_)
        },
        'class_distribution': {
            'train': y_train.value_counts().to_dict(),
            'test': y_test.value_counts().to_dict(),
        }
    }
    
    # Print results
    print(f"\n✅ TRAINING COMPLETE")
    print(f"\n📊 Metrics:")
    print(f"   Accuracy:  {metrics['accuracy']:.3f}")
    print(f"   Precision: {metrics['precision']:.3f} (valid patch predictions)")
    print(f"   Recall:    {metrics['recall']:.3f} (valid patches caught)")
    print(f"   F1:        {metrics['f1']:.3f}")
    print(f"   ROC-AUC:   {metrics['roc_auc']:.3f}")
    
    print(f"\n🎯 Confusion Matrix:")
    print(f"   {cm}")
    print(f"   [[TN, FP]")
    print(f"    [FN, TP]]")
    
    # Top features
    print(f"\n🔝 Top 5 Features (importance):")
    sorted_features = sorted(
        metrics['feature_importance'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for feat, imp in sorted_features[:5]:
        print(f"   {feat:30s}: {imp:.4f}")
    
    # Save model
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_output_path)
    print(f"\n💾 Model saved: {model_output_path}")
    
    # Save metrics
    Path(metrics_output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"📊 Metrics saved: {metrics_output_path}")
    
    # Success criteria
    print(f"\n🎯 Success Criteria:")
    success = True
    
    if metrics['accuracy'] >= 0.90:
        print(f"   ✅ Accuracy ≥0.90: {metrics['accuracy']:.3f}")
    else:
        print(f"   ⚠️  Accuracy <0.90: {metrics['accuracy']:.3f} (target: 0.90)")
        success = False
    
    if metrics['precision'] >= 0.95:
        print(f"   ✅ Precision ≥0.95: {metrics['precision']:.3f}")
    else:
        print(f"   ⚠️  Precision <0.95: {metrics['precision']:.3f} (target: 0.95)")
        success = False
    
    if metrics['recall'] >= 0.85:
        print(f"   ✅ Recall ≥0.85: {metrics['recall']:.3f}")
    else:
        print(f"   ⚠️  Recall <0.85: {metrics['recall']:.3f} (target: 0.85)")
        success = False
    
    if success:
        print(f"\n🔥 ALL CRITERIA MET - PRODUCTION-READY!")
    else:
        print(f"\n⚠️  Some criteria not met. Consider:")
        print(f"   - Collect more training data (current: {len(df)} samples)")
        print(f"   - Add more features (semantic analysis, etc)")
        print(f"   - Try different hyperparameters")
    
    print(f"\n" + "=" * 80)
    print(f"🚀 Next step: Test prediction")
    print(f"   Use the model via API or Python:")
    print(f"   POST /ml/predict with patch_content")
    print(f"=" * 80)
    
    return metrics


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Train ML model for patch validity prediction"
    )
    parser.add_argument(
        '--dataset',
        default='data/ml/wargaming_dataset.csv',
        help='Input CSV with training data'
    )
    parser.add_argument(
        '--model',
        default='models/patch_validity_rf.joblib',
        help='Output model path'
    )
    parser.add_argument(
        '--metrics',
        default='models/patch_validity_metrics.json',
        help='Output metrics path'
    )
    
    args = parser.parse_args()
    
    try:
        metrics = train_patch_validity_classifier(
            dataset_path=args.dataset,
            model_output_path=args.model,
            metrics_output_path=args.metrics,
        )
        
        # Exit code: 0 if successful, 1 if metrics below threshold
        success = (
            metrics['accuracy'] >= 0.90 and
            metrics['precision'] >= 0.95 and
            metrics['recall'] >= 0.85
        )
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
