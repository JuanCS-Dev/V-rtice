#!/usr/bin/env python3
"""
Export wargaming results to CSV for ML training.

Usage:
    python scripts/ml/export_training_data.py
    python scripts/ml/export_training_data.py --output custom_path.csv
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import pandas as pd
except ImportError:
    print("❌ pandas not installed. Install: pip install pandas")
    sys.exit(1)


async def export_dataset(output_path: str = "data/ml/wargaming_dataset.csv") -> int:
    """
    Export wargaming results as CSV for training.
    
    Args:
        output_path: Where to save CSV
        
    Returns:
        Number of samples exported
    """
    print(f"📊 Exporting wargaming results to {output_path}...")
    
    # For now, since we don't have real database connection yet,
    # create synthetic dataset for testing
    
    # TODO: Replace with real database query when PostgreSQL is available
    # from backend.database import get_db_session
    # async with get_db_session() as session:
    #     query = "SELECT ... FROM wargaming_results WHERE execution_time_ms > 0"
    #     result = await session.execute(query)
    #     rows = result.fetchall()
    
    # TEMPORARY: Generate synthetic data for testing
    print("⚠️  Using synthetic data (no database connected yet)")
    
    synthetic_data = [
        # Valid patches (SQL Injection)
        {
            'lines_added': 5, 'lines_removed': 2, 'files_modified': 1,
            'complexity_delta': 2.0,
            'has_input_validation': 1, 'has_sanitization': 1,
            'has_encoding': 0, 'has_parameterization': 1,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 1
        },
        {
            'lines_added': 3, 'lines_removed': 1, 'files_modified': 1,
            'complexity_delta': 1.0,
            'has_input_validation': 1, 'has_sanitization': 0,
            'has_encoding': 0, 'has_parameterization': 1,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 1
        },
        {
            'lines_added': 8, 'lines_removed': 3, 'files_modified': 2,
            'complexity_delta': 3.0,
            'has_input_validation': 1, 'has_sanitization': 1,
            'has_encoding': 1, 'has_parameterization': 1,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 1
        },
        
        # Invalid patches (SQL Injection - insufficient fix)
        {
            'lines_added': 1, 'lines_removed': 0, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 0,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 0
        },
        {
            'lines_added': 2, 'lines_removed': 1, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 1,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 0
        },
        
        # Valid patches (XSS)
        {
            'lines_added': 4, 'lines_removed': 2, 'files_modified': 1,
            'complexity_delta': 1.0,
            'has_input_validation': 1, 'has_sanitization': 1,
            'has_encoding': 1, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-79',
            'patch_validated': 1
        },
        {
            'lines_added': 3, 'lines_removed': 1, 'files_modified': 1,
            'complexity_delta': 1.0,
            'has_input_validation': 0, 'has_sanitization': 1,
            'has_encoding': 1, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-79',
            'patch_validated': 1
        },
        
        # Invalid patches (XSS - no encoding)
        {
            'lines_added': 2, 'lines_removed': 0, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 1,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-79',
            'patch_validated': 0
        },
        {
            'lines_added': 1, 'lines_removed': 0, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 0,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-79',
            'patch_validated': 0
        },
        
        # Command Injection - valid
        {
            'lines_added': 6, 'lines_removed': 2, 'files_modified': 1,
            'complexity_delta': 2.0,
            'has_input_validation': 1, 'has_sanitization': 1,
            'has_encoding': 1, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-78',
            'patch_validated': 1
        },
        
        # Command Injection - invalid
        {
            'lines_added': 1, 'lines_removed': 0, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 0,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-78',
            'patch_validated': 0
        },
        
        # More diverse samples...
        {
            'lines_added': 10, 'lines_removed': 5, 'files_modified': 3,
            'complexity_delta': 4.0,
            'has_input_validation': 1, 'has_sanitization': 1,
            'has_encoding': 1, 'has_parameterization': 1,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 1
        },
        {
            'lines_added': 7, 'lines_removed': 3, 'files_modified': 2,
            'complexity_delta': 2.0,
            'has_input_validation': 1, 'has_sanitization': 1,
            'has_encoding': 1, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-79',
            'patch_validated': 1
        },
        {
            'lines_added': 2, 'lines_removed': 1, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 0,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-89',
            'patch_validated': 0
        },
        {
            'lines_added': 3, 'lines_removed': 1, 'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 0, 'has_sanitization': 0,
            'has_encoding': 0, 'has_parameterization': 0,
            'exploit_cwe': 'CWE-79',
            'patch_validated': 0
        },
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(synthetic_data)
    
    print(f"📊 Dataset: {len(df)} samples")
    print(f"   Valid patches: {df['patch_validated'].sum()}")
    print(f"   Invalid patches: {(~df['patch_validated'].astype(bool)).sum()}")
    print(f"   CWE distribution:")
    print(df['exploit_cwe'].value_counts().to_dict())
    
    # One-hot encode CWE
    df = pd.get_dummies(df, columns=['exploit_cwe'], prefix='cwe')
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} samples to {output_path}")
    
    # Show first few rows
    print("\n📝 Sample data:")
    print(df.head(3))
    
    return len(df)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Export wargaming results for ML training"
    )
    parser.add_argument(
        '--output',
        default='data/ml/wargaming_dataset.csv',
        help='Output CSV path (default: data/ml/wargaming_dataset.csv)'
    )
    
    args = parser.parse_args()
    
    # Run async export
    count = asyncio.run(export_dataset(args.output))
    
    print(f"\n🎯 Ready for training! Use: python scripts/ml/train.py")
    return 0 if count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
