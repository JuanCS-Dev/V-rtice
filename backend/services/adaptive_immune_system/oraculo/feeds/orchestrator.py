"""
Feed Orchestrator - Coordinates CVE ingestion from multiple sources.

Manages parallel ingestion from NVD, GHSA, and OSV feeds,
deduplication, and database persistence.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from database import DatabaseClient
from database.models import Threat, FeedSyncStatus
from models.threat import ThreatCreate
from .nvd_client import NVDClient, NVDVulnerability
from .ghsa_client import GHSAClient, GHSAVulnerability
from .osv_client import OSVClient

logger = logging.getLogger(__name__)


class FeedOrchestrator:
    """
    Orchestrates CVE ingestion from multiple feeds.

    Features:
    - Parallel feed ingestion
    - CVE deduplication (by CVE ID)
    - Database persistence
    - Sync status tracking
    - Error handling per feed
    - Health monitoring
    """

    def __init__(
        self,
        db_client: DatabaseClient,
        nvd_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
    ):
        """
        Initialize feed orchestrator.

        Args:
            db_client: Database client instance
            nvd_api_key: Optional NVD API key (for higher rate limits)
            github_token: GitHub token for GHSA (required)
        """
        self.db_client = db_client

        self.nvd_client = NVDClient(api_key=nvd_api_key) if nvd_api_key else None
        self.ghsa_client = GHSAClient(github_token=github_token) if github_token else None
        self.osv_client = OSVClient()

        self.stats = {
            "nvd": {"total": 0, "new": 0, "updated": 0, "errors": 0},
            "ghsa": {"total": 0, "new": 0, "updated": 0, "errors": 0},
            "osv": {"total": 0, "new": 0, "updated": 0, "errors": 0},
        }

        logger.info(
            f"FeedOrchestrator initialized: "
            f"nvd={'enabled' if self.nvd_client else 'disabled'}, "
            f"ghsa={'enabled' if self.ghsa_client else 'disabled'}, "
            f"osv=enabled"
        )

    async def ingest_all_feeds(
        self,
        days_back: int = 7,
        parallel: bool = True,
    ) -> Dict[str, dict]:
        """
        Ingest CVEs from all available feeds.

        Args:
            days_back: Number of days to look back
            parallel: Run feeds in parallel (True) or sequentially (False)

        Returns:
            Dictionary with stats per feed
        """
        start_time = datetime.utcnow()

        logger.info(
            f"🚀 Starting feed ingestion: days_back={days_back}, parallel={parallel}"
        )

        # Reset stats
        for feed in self.stats:
            self.stats[feed] = {"total": 0, "new": 0, "updated": 0, "errors": 0}

        # Create tasks for each enabled feed
        tasks = []

        if self.nvd_client:
            tasks.append(self._ingest_nvd(days_back))

        if self.ghsa_client:
            tasks.append(self._ingest_ghsa(days_back))

        tasks.append(self._ingest_osv(days_back))

        # Run tasks
        if parallel:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for task in tasks:
                try:
                    await task
                except Exception as e:
                    logger.error(f"Feed ingestion error: {e}")

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log summary
        total_new = sum(s["new"] for s in self.stats.values())
        total_updated = sum(s["updated"] for s in self.stats.values())
        total_errors = sum(s["errors"] for s in self.stats.values())

        logger.info(
            f"✅ Feed ingestion complete: "
            f"duration={duration:.1f}s, new={total_new}, "
            f"updated={total_updated}, errors={total_errors}"
        )

        return {
            "stats": self.stats,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _ingest_nvd(self, days_back: int) -> None:
        """Ingest from NVD feed."""
        if not self.nvd_client:
            return

        feed_name = "nvd"
        logger.info(f"📥 Starting NVD ingestion (last {days_back} days)")

        start_time = datetime.utcnow()

        try:
            async with self.nvd_client:
                async for vuln in self.nvd_client.get_recent_cves(days=days_back):
                    self.stats[feed_name]["total"] += 1

                    try:
                        # Convert to ThreatCreate model
                        threat_data = self._convert_nvd_to_threat(vuln)

                        # Save to database
                        with self.db_client.get_session() as session:
                            is_new = self._upsert_threat(session, threat_data)

                            if is_new:
                                self.stats[feed_name]["new"] += 1
                            else:
                                self.stats[feed_name]["updated"] += 1

                    except Exception as e:
                        logger.error(f"Error processing NVD CVE {vuln.cve_id}: {e}")
                        self.stats[feed_name]["errors"] += 1

            # Update sync status
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._update_sync_status(
                feed_name,
                success=True,
                duration_ms=duration_ms,
                threats_ingested=self.stats[feed_name]["new"],
            )

            logger.info(
                f"✅ NVD ingestion complete: "
                f"total={self.stats[feed_name]['total']}, "
                f"new={self.stats[feed_name]['new']}"
            )

        except Exception as e:
            logger.error(f"NVD ingestion failed: {e}")
            self._update_sync_status(feed_name, success=False, error=str(e))

    async def _ingest_ghsa(self, days_back: int) -> None:
        """Ingest from GHSA feed."""
        if not self.ghsa_client:
            return

        feed_name = "ghsa"
        logger.info(f"📥 Starting GHSA ingestion (last {days_back} days)")

        start_time = datetime.utcnow()
        updated_since = datetime.utcnow() - timedelta(days=days_back)

        try:
            async with self.ghsa_client:
                async for vuln in self.ghsa_client.get_advisories(updated_since=updated_since):
                    self.stats[feed_name]["total"] += 1

                    try:
                        # Convert to ThreatCreate model
                        threat_data = self._convert_ghsa_to_threat(vuln)

                        # Save to database
                        with self.db_client.get_session() as session:
                            is_new = self._upsert_threat(session, threat_data)

                            if is_new:
                                self.stats[feed_name]["new"] += 1
                            else:
                                self.stats[feed_name]["updated"] += 1

                    except Exception as e:
                        logger.error(f"Error processing GHSA {vuln.ghsa_id}: {e}")
                        self.stats[feed_name]["errors"] += 1

            # Update sync status
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._update_sync_status(
                feed_name,
                success=True,
                duration_ms=duration_ms,
                threats_ingested=self.stats[feed_name]["new"],
            )

            logger.info(
                f"✅ GHSA ingestion complete: "
                f"total={self.stats[feed_name]['total']}, "
                f"new={self.stats[feed_name]['new']}"
            )

        except Exception as e:
            logger.error(f"GHSA ingestion failed: {e}")
            self._update_sync_status(feed_name, success=False, error=str(e))

    async def _ingest_osv(self, days_back: int) -> None:
        """
        Ingest from OSV feed.

        Note: OSV doesn't have a time-based query, so we query by ecosystem.
        """
        feed_name = "osv"
        logger.info("📥 Starting OSV ingestion")

        start_time = datetime.utcnow()

        try:
            async with self.osv_client:
                # OSV requires package-specific queries
                # For now, log that OSV ingestion requires dependency inventory
                logger.warning(
                    "OSV ingestion requires dependency inventory. "
                    "Will be queried per-package in APV generation phase."
                )

            # Update sync status
            self._update_sync_status(feed_name, success=True, duration_ms=0, threats_ingested=0)

        except Exception as e:
            logger.error(f"OSV ingestion failed: {e}")
            self._update_sync_status(feed_name, success=False, error=str(e))

    def _convert_nvd_to_threat(self, vuln: NVDVulnerability) -> ThreatCreate:
        """Convert NVD vulnerability to ThreatCreate model."""
        return ThreatCreate(
            cve_id=vuln.cve_id,
            source="nvd",
            title=vuln.cve_id,  # NVD doesn't have separate title
            description=self.nvd_client.extract_description(vuln),
            published_date=vuln.published,
            last_modified_date=vuln.last_modified,
            cvss_score=self.nvd_client.extract_cvss_score(vuln),
            cvss_vector=vuln.cvss_v3.get("cvssData", {}).get("vectorString") if vuln.cvss_v3 else None,
            severity=self.nvd_client.extract_severity(vuln),
            ecosystems=[],  # Will be populated from CPE data (future enhancement)
            affected_packages=None,
            cwe_ids=self.nvd_client.extract_cwe_ids(vuln),
            references=self.nvd_client.extract_references(vuln),
        )

    def _convert_ghsa_to_threat(self, vuln: GHSAVulnerability) -> ThreatCreate:
        """Convert GHSA vulnerability to ThreatCreate model."""
        ecosystem = self.ghsa_client.map_ecosystem_to_standard(vuln.package.ecosystem)

        return ThreatCreate(
            cve_id=vuln.cve_id or vuln.ghsa_id,  # Fallback to GHSA ID if no CVE
            source="ghsa",
            title=vuln.summary,
            description=vuln.description,
            published_date=vuln.published_at,
            last_modified_date=vuln.updated_at,
            cvss_score=None,  # GHSA doesn't provide CVSS score directly
            cvss_vector=None,
            severity=self.ghsa_client.map_severity_to_standard(vuln.severity),
            ecosystems=[ecosystem],
            affected_packages={
                "name": vuln.package.name,
                "ecosystem": ecosystem,
                "vulnerable_range": vuln.vulnerable_version_range,
                "fixed_version": vuln.first_patched_version,
            },
            cwe_ids=vuln.cwes,
            references=vuln.references,
        )

    def _upsert_threat(self, session: Session, threat_data: ThreatCreate) -> bool:
        """
        Insert or update threat in database.

        Args:
            session: Database session
            threat_data: ThreatCreate data

        Returns:
            True if new threat created, False if updated
        """
        # Check if threat exists
        existing = session.query(Threat).filter(Threat.cve_id == threat_data.cve_id).first()

        if existing:
            # Update existing threat
            for key, value in threat_data.model_dump().items():
                setattr(existing, key, value)
            session.commit()
            return False
        else:
            # Create new threat
            threat = Threat(**threat_data.model_dump())
            session.add(threat)
            session.commit()
            return True

    def _update_sync_status(
        self,
        feed_name: str,
        success: bool,
        duration_ms: int = 0,
        threats_ingested: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """Update feed sync status in database."""
        with self.db_client.get_session() as session:
            status = session.query(FeedSyncStatus).filter(
                FeedSyncStatus.feed_name == feed_name
            ).first()

            if not status:
                status = FeedSyncStatus(feed_name=feed_name)
                session.add(status)

            status.last_sync_at = datetime.utcnow()

            if success:
                status.last_success_at = datetime.utcnow()
                status.sync_count += 1
                status.total_threats_ingested += threats_ingested
                status.last_sync_duration_ms = duration_ms
                status.last_error = None
            else:
                status.error_count += 1
                status.last_error = error

            session.commit()

    def get_sync_status(self) -> Dict[str, dict]:
        """
        Get sync status for all feeds.

        Returns:
            Dictionary with status per feed
        """
        with self.db_client.get_session() as session:
            statuses = session.query(FeedSyncStatus).all()

            return {
                status.feed_name: {
                    "last_sync_at": status.last_sync_at.isoformat() if status.last_sync_at else None,
                    "last_success_at": status.last_success_at.isoformat() if status.last_success_at else None,
                    "sync_count": status.sync_count,
                    "error_count": status.error_count,
                    "total_threats_ingested": status.total_threats_ingested,
                    "last_sync_duration_ms": status.last_sync_duration_ms,
                    "last_error": status.last_error,
                }
                for status in statuses
            }

    def get_stats(self) -> Dict[str, dict]:
        """Get current ingestion stats."""
        return self.stats.copy()
