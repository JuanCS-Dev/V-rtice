"""Maximus OSINT Service - Image Analyzer (Production-Hardened).

Production-grade image analyzer with real image processing capabilities.

Key improvements:
- ✅ Real EXIF metadata extraction (Pillow)
- ✅ Perceptual image hashing (imagehash - pHash, aHash, dHash, wHash)
- ✅ Image similarity comparison
- ✅ Basic image info (dimensions, format, mode, size)
- ✅ Structured JSON logging
- ✅ Prometheus metrics
- ✅ Inherits from BaseTool patterns

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, real image processing
    - Article V (Prior Legislation): Observability first

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 2.0.0
"""

import base64
import io
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import imagehash
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from core.base_tool import BaseTool


class ImageAnalyzerRefactored(BaseTool):
    """Production-grade image analyzer with EXIF, hashing, and similarity.

    Features:
    - EXIF metadata extraction
    - Perceptual hashing (pHash, aHash, dHash, wHash)
    - Image similarity comparison
    - Basic image info

    Usage:
        analyzer = ImageAnalyzerRefactored()

        # Analyze image from base64
        result = await analyzer.query(
            target=base64_string,
            analysis_types=["exif", "hash", "info"]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 5.0,
        timeout: int = 30,
        max_retries: int = 2,
        cache_ttl: int = 3600,
        cache_backend: str = "memory",
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """Initialize ImageAnalyzerRefactored."""
        super().__init__(
            api_key=api_key,
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
        )

        self.total_analyses = 0
        self.logger.info("image_analyzer_initialized")

    async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
        """Analyze image from base64 string.

        Args:
            target: Base64 encoded image
            **params:
                - analysis_types: List of types ['exif', 'hash', 'info', 'all']
                - compare_hash: Optional hash string to compare similarity

        Returns:
            Analysis result dictionary
        """
        analysis_types = params.get("analysis_types", ["all"])
        compare_hash = params.get("compare_hash", None)

        # Decode base64
        try:
            image_bytes = base64.b64decode(target)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            self.logger.error("image_decode_failed", error=str(e))
            raise ValueError(f"Failed to decode image: {e}")

        self.logger.info("image_analysis_started", format=image.format, size=image.size)

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_types": analysis_types,
        }

        # Perform analyses
        if "all" in analysis_types or "info" in analysis_types:
            result["info"] = self._extract_basic_info(image)

        if "all" in analysis_types or "exif" in analysis_types:
            result["exif"] = self._extract_exif(image)

        if "all" in analysis_types or "hash" in analysis_types:
            result["hashes"] = self._calculate_hashes(image)

        if compare_hash:
            result["similarity"] = self._compare_hashes(image, compare_hash)

        self.total_analyses += 1
        self.logger.info("image_analysis_complete", analyses=self.total_analyses)

        return result

    def _extract_basic_info(self, image: Image.Image) -> Dict[str, Any]:
        """Extract basic image information."""
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image.tobytes()) if image.mode else 0,
        }

    def _extract_exif(self, image: Image.Image) -> Dict[str, Any]:
        """Extract EXIF metadata from image."""
        exif_data = {}

        try:
            exif = image.getexif()
            if not exif:
                return {"available": False}

            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)

                # Handle GPS data specially
                if tag == "GPSInfo":
                    gps_data = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = str(gps_value)
                    exif_data["GPSInfo"] = gps_data
                else:
                    # Convert to string for JSON serialization
                    exif_data[tag] = str(value) if not isinstance(value, (str, int, float)) else value

            exif_data["available"] = True
            return exif_data

        except Exception as e:
            self.logger.warning("exif_extraction_failed", error=str(e))
            return {"available": False, "error": str(e)}

    def _calculate_hashes(self, image: Image.Image) -> Dict[str, str]:
        """Calculate perceptual hashes for image."""
        return {
            "phash": str(imagehash.phash(image)),
            "ahash": str(imagehash.average_hash(image)),
            "dhash": str(imagehash.dhash(image)),
            "whash": str(imagehash.whash(image)),
        }

    def _compare_hashes(self, image: Image.Image, compare_hash: str) -> Dict[str, Any]:
        """Compare image hash with provided hash."""
        try:
            current_phash = imagehash.phash(image)
            compare_phash = imagehash.hex_to_hash(compare_hash)

            hamming_distance = current_phash - compare_phash
            similarity = 100 - (hamming_distance * 100 / 64)  # 64 = max distance for 8x8 hash

            return {
                "hamming_distance": hamming_distance,
                "similarity_percent": max(0, similarity),
                "is_similar": hamming_distance <= 10,  # Threshold: 10 bits difference
            }
        except Exception as e:
            self.logger.error("hash_comparison_failed", error=str(e))
            return {"error": str(e)}

    async def get_status(self) -> Dict[str, Any]:
        """Get analyzer status."""
        status = await self.health_check()
        status.update({"total_analyses": self.total_analyses})
        return status

    def __repr__(self) -> str:
        return f"ImageAnalyzerRefactored(analyses={self.total_analyses})"
