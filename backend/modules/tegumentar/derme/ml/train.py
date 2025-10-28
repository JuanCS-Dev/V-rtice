"""CLI helper to train the IsolationForest anomaly detector."""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path
from typing import List

import joblib
from sklearn.ensemble import IsolationForest  # type: ignore[import]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tegumentar.ml.train")


def load_dataset(path: Path) -> List[List[float]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            [
                float(row["payload_length"]),
                float(row["entropy"]),
                float(row["printable_ratio"]),
                float(row["digit_ratio"]),
                float(row["average_byte_value"]),
                float(row["tcp_flag_score"]),
                float(row["inter_packet_interval"]),
            ]
            for row in reader
        ]
    if not rows:
        raise ValueError(f"Dataset {path} is empty")
    return rows


def train(dataset: Path, output: Path, contamination: float) -> None:
    features = load_dataset(dataset)
    model = IsolationForest(
        n_estimators=256,
        contamination=contamination,
        max_features=1.0,
        bootstrap=True,
        random_state=42,
    )
    model.fit(features)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    logger.info("Model trained with %d samples and saved to %s", len(features), output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Tegumentar anomaly detector.")
    parser.add_argument("--dataset", type=Path, required=True, help="CSV dataset path.")
    parser.add_argument(
        "--output", type=Path, required=True, help="Output .joblib path."
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.02,
        help="Expected contamination ratio (default: 0.02).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train(args.dataset, args.output, args.contamination)


if __name__ == "__main__":
    main()
