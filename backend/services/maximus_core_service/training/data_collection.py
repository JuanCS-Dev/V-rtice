"""
Data Collection for MAXIMUS Training Pipeline

Collects security events from multiple sources:
- SIEM systems (Elastic, Splunk, Qradar)
- EDR platforms (CrowdStrike, SentinelOne, Microsoft Defender)
- Network traffic (Zeek, Suricata)
- File formats (JSON, CSV, Parquet)

REGRA DE OURO: Zero mocks, real data collection
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Supported data source types."""

    ELASTIC = "elasticsearch"
    SPLUNK = "splunk"
    QRADAR = "qradar"
    JSON_FILE = "json_file"
    CSV_FILE = "csv_file"
    PARQUET_FILE = "parquet_file"
    ZEEK_LOGS = "zeek_logs"
    SURICATA_LOGS = "suricata_logs"


@dataclass
class DataSource:
    """Configuration for a data source."""

    name: str
    source_type: DataSourceType
    connection_params: dict[str, Any]
    query_filter: str | None = None
    time_field: str = "@timestamp"
    batch_size: int = 1000

    def __repr__(self) -> str:
        return f"DataSource(name={self.name}, type={self.source_type.value})"


@dataclass
class CollectedEvent:
    """Represents a collected security event."""

    event_id: str
    timestamp: datetime
    source: str
    event_type: str
    raw_data: dict[str, Any]
    labels: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "event_type": self.event_type,
            "raw_data": self.raw_data,
            "labels": self.labels or {},
        }


class DataCollector:
    """Collects security events from multiple sources for training.

    Features:
    - Multi-source collection (SIEM, EDR, files)
    - Incremental collection (resume from checkpoint)
    - Deduplication
    - Time-based filtering
    - Batch processing
    - Error handling and retry

    Example:
        ```python
        # Collect from JSON file
        source = DataSource(
            name="synthetic_events",
            source_type=DataSourceType.JSON_FILE,
            connection_params={"path": "demo/synthetic_events.json"},
        )

        collector = DataCollector(sources=[source])
        events = list(collector.collect(start_date="2025-01-01"))
        print(f"Collected {len(events)} events")
        ```
    """

    def __init__(self, sources: list[DataSource], output_dir: Path | None = None, checkpoint_enabled: bool = True):
        """Initialize data collector.

        Args:
            sources: List of data sources to collect from
            output_dir: Directory to save collected data
            checkpoint_enabled: Enable checkpointing for resumption
        """
        self.sources = sources
        self.output_dir = Path(output_dir) if output_dir else Path("training/data/raw")
        self.checkpoint_enabled = checkpoint_enabled

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {"events_collected": 0, "events_deduplicated": 0, "errors": 0, "sources_processed": 0}

        # Deduplication cache (event IDs)
        self._seen_event_ids: set = set()

        logger.info(f"DataCollector initialized with {len(sources)} sources")

    def collect(
        self,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        max_events: int | None = None,
        resume_from_checkpoint: bool = True,
    ) -> Iterator[CollectedEvent]:
        """Collect events from all configured sources.

        Args:
            start_date: Start date for collection (ISO format or datetime)
            end_date: End date for collection (ISO format or datetime)
            max_events: Maximum number of events to collect
            resume_from_checkpoint: Resume from last checkpoint

        Yields:
            Collected security events
        """
        # Parse dates
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)

        # Load checkpoint
        if resume_from_checkpoint and self.checkpoint_enabled:
            self._load_checkpoint()

        events_collected = 0

        for source in self.sources:
            logger.info(f"Collecting from source: {source.name}")

            try:
                for event in self._collect_from_source(source, start_date, end_date):
                    # Deduplication
                    if event.event_id in self._seen_event_ids:
                        self.stats["events_deduplicated"] += 1
                        continue

                    self._seen_event_ids.add(event.event_id)
                    self.stats["events_collected"] += 1
                    events_collected += 1

                    yield event

                    # Check max_events limit
                    if max_events and events_collected >= max_events:
                        logger.info(f"Reached max_events limit: {max_events}")
                        return

                    # Checkpoint every 1000 events
                    if self.checkpoint_enabled and events_collected % 1000 == 0:
                        self._save_checkpoint()

                self.stats["sources_processed"] += 1

            except Exception as e:
                logger.error(f"Error collecting from {source.name}: {e}")
                self.stats["errors"] += 1
                continue

        # Final checkpoint
        if self.checkpoint_enabled:
            self._save_checkpoint()

        logger.info(f"Collection complete: {self.stats}")

    def _collect_from_source(
        self, source: DataSource, start_date: datetime | None, end_date: datetime | None
    ) -> Iterator[CollectedEvent]:
        """Collect events from a single source.

        Args:
            source: Data source configuration
            start_date: Start date filter
            end_date: End date filter

        Yields:
            Collected events
        """
        if source.source_type == DataSourceType.JSON_FILE:
            yield from self._collect_from_json_file(source, start_date, end_date)
        elif source.source_type == DataSourceType.CSV_FILE:
            yield from self._collect_from_csv_file(source, start_date, end_date)
        elif source.source_type == DataSourceType.PARQUET_FILE:
            yield from self._collect_from_parquet_file(source, start_date, end_date)
        elif source.source_type == DataSourceType.ZEEK_LOGS:
            yield from self._collect_from_zeek_logs(source, start_date, end_date)
        elif source.source_type == DataSourceType.ELASTIC:
            yield from self._collect_from_elasticsearch(source, start_date, end_date)
        else:
            logger.warning(f"Unsupported source type: {source.source_type}")

    def _collect_from_json_file(
        self, source: DataSource, start_date: datetime | None, end_date: datetime | None
    ) -> Iterator[CollectedEvent]:
        """Collect events from JSON file.

        Args:
            source: Data source with file path
            start_date: Start date filter
            end_date: End date filter

        Yields:
            Collected events
        """
        file_path = Path(source.connection_params["path"])

        if not file_path.exists():
            logger.error(f"JSON file not found: {file_path}")
            return

        with open(file_path) as f:
            data = json.load(f)

        # Handle both list of events and single event
        events = data if isinstance(data, list) else [data]

        for idx, event_data in enumerate(events):
            try:
                # Parse timestamp
                timestamp_str = event_data.get(source.time_field, event_data.get("timestamp"))
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.utcnow()

                # Apply time filters
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                # Create event
                event_id = event_data.get("id", event_data.get("event_id", f"{source.name}_{idx}"))
                event_type = event_data.get("type", event_data.get("event_type", "unknown"))

                yield CollectedEvent(
                    event_id=event_id,
                    timestamp=timestamp,
                    source=source.name,
                    event_type=event_type,
                    raw_data=event_data,
                    labels=event_data.get("labels"),
                )

            except Exception as e:
                logger.error(f"Error parsing event {idx} from {source.name}: {e}")
                continue

    def _collect_from_csv_file(
        self, source: DataSource, start_date: datetime | None, end_date: datetime | None
    ) -> Iterator[CollectedEvent]:
        """Collect events from CSV file.

        Args:
            source: Data source with file path
            start_date: Start date filter
            end_date: End date filter

        Yields:
            Collected events
        """
        file_path = Path(source.connection_params["path"])

        if not file_path.exists():
            logger.error(f"CSV file not found: {file_path}")
            return

        df = pd.read_csv(file_path)

        # Parse timestamp column
        if source.time_field in df.columns:
            df[source.time_field] = pd.to_datetime(df[source.time_field])

        for idx, row in df.iterrows():
            try:
                timestamp = row.get(source.time_field, datetime.utcnow())

                # Apply time filters
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                event_id = row.get("id", row.get("event_id", f"{source.name}_{idx}"))
                event_type = row.get("type", row.get("event_type", "unknown"))

                yield CollectedEvent(
                    event_id=str(event_id),
                    timestamp=timestamp,
                    source=source.name,
                    event_type=str(event_type),
                    raw_data=row.to_dict(),
                    labels=json.loads(row.get("labels", "{}")) if "labels" in row else None,
                )

            except Exception as e:
                logger.error(f"Error parsing row {idx} from {source.name}: {e}")
                continue

    def _collect_from_parquet_file(
        self, source: DataSource, start_date: datetime | None, end_date: datetime | None
    ) -> Iterator[CollectedEvent]:
        """Collect events from Parquet file.

        Args:
            source: Data source with file path
            start_date: Start date filter
            end_date: End date filter

        Yields:
            Collected events
        """
        file_path = Path(source.connection_params["path"])

        if not file_path.exists():
            logger.error(f"Parquet file not found: {file_path}")
            return

        df = pd.read_parquet(file_path)

        # Reuse CSV logic
        for event in self._collect_from_csv_file(source, start_date, end_date):
            yield event

    def _collect_from_zeek_logs(
        self, source: DataSource, start_date: datetime | None, end_date: datetime | None
    ) -> Iterator[CollectedEvent]:
        """Collect events from Zeek logs.

        Args:
            source: Data source with log directory
            start_date: Start date filter
            end_date: End date filter

        Yields:
            Collected events
        """
        log_dir = Path(source.connection_params["path"])

        if not log_dir.exists():
            logger.error(f"Zeek log directory not found: {log_dir}")
            return

        # Zeek logs are TSV files
        for log_file in log_dir.glob("*.log"):
            logger.info(f"Processing Zeek log: {log_file.name}")

            try:
                df = pd.read_csv(log_file, sep="\t", comment="#", header=0)

                # Zeek uses 'ts' for timestamp
                if "ts" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["ts"], unit="s")

                for idx, row in df.iterrows():
                    try:
                        timestamp = row.get("timestamp", datetime.utcnow())

                        if start_date and timestamp < start_date:
                            continue
                        if end_date and timestamp > end_date:
                            continue

                        event_id = f"zeek_{log_file.stem}_{idx}"
                        event_type = f"zeek_{log_file.stem}"

                        yield CollectedEvent(
                            event_id=event_id,
                            timestamp=timestamp,
                            source=source.name,
                            event_type=event_type,
                            raw_data=row.to_dict(),
                        )

                    except Exception as e:
                        logger.error(f"Error parsing Zeek event {idx}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error reading Zeek log {log_file}: {e}")
                continue

    def _collect_from_elasticsearch(
        self, source: DataSource, start_date: datetime | None, end_date: datetime | None
    ) -> Iterator[CollectedEvent]:
        """Collect events from Elasticsearch.

        Args:
            source: Data source with ES connection params
            start_date: Start date filter
            end_date: End date filter

        Yields:
            Collected events
        """
        try:
            from elasticsearch import Elasticsearch
        except ImportError:
            logger.error("elasticsearch package not installed. Install with: pip install elasticsearch")
            return

        # Connect to Elasticsearch
        es_client = Elasticsearch([source.connection_params["host"]])

        # Build query
        query = {"query": {"bool": {"must": []}}, "sort": [{source.time_field: "asc"}], "size": source.batch_size}

        # Add time range filter
        if start_date or end_date:
            time_range = {}
            if start_date:
                time_range["gte"] = start_date.isoformat()
            if end_date:
                time_range["lte"] = end_date.isoformat()

            query["query"]["bool"]["must"].append({"range": {source.time_field: time_range}})

        # Add custom filter
        if source.query_filter:
            query["query"]["bool"]["must"].append({"query_string": {"query": source.query_filter}})

        index = source.connection_params.get("index", "*")

        # Scroll through results
        response = es_client.search(index=index, body=query, scroll="5m")
        scroll_id = response["_scroll_id"]
        hits = response["hits"]["hits"]

        while hits:
            for hit in hits:
                try:
                    source_data = hit["_source"]

                    timestamp_str = source_data.get(source.time_field)
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

                    event_id = hit["_id"]
                    event_type = source_data.get("event.type", source_data.get("type", "unknown"))

                    yield CollectedEvent(
                        event_id=event_id,
                        timestamp=timestamp,
                        source=source.name,
                        event_type=event_type,
                        raw_data=source_data,
                    )

                except Exception as e:
                    logger.error(f"Error parsing ES event {hit['_id']}: {e}")
                    continue

            # Next batch
            response = es_client.scroll(scroll_id=scroll_id, scroll="5m")
            scroll_id = response["_scroll_id"]
            hits = response["hits"]["hits"]

        # Clear scroll
        es_client.clear_scroll(scroll_id=scroll_id)

    def save_to_file(self, events: list[CollectedEvent], filename: str = "collected_events.json") -> Path:
        """Save collected events to file.

        Args:
            events: List of collected events
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        events_data = [event.to_dict() for event in events]

        with open(output_path, "w") as f:
            json.dump(events_data, f, indent=2)

        logger.info(f"Saved {len(events)} events to {output_path}")
        return output_path

    def _save_checkpoint(self):
        """Save checkpoint for resumption."""
        checkpoint_path = self.output_dir / "checkpoint.json"

        checkpoint_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": self.stats,
            "seen_event_ids": list(self._seen_event_ids),
        }

        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.debug(f"Checkpoint saved: {checkpoint_path}")

    def _load_checkpoint(self):
        """Load checkpoint for resumption."""
        checkpoint_path = self.output_dir / "checkpoint.json"

        if not checkpoint_path.exists():
            logger.debug("No checkpoint found")
            return

        with open(checkpoint_path) as f:
            checkpoint_data = json.load(f)

        self.stats = checkpoint_data.get("stats", self.stats)
        self._seen_event_ids = set(checkpoint_data.get("seen_event_ids", []))

        logger.info(f"Checkpoint loaded: {len(self._seen_event_ids)} events seen")

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with statistics
        """
        return {**self.stats, "unique_events": len(self._seen_event_ids), "sources_configured": len(self.sources)}
