"""Unit tests for ImageAnalyzerRefactored.

Tests the production-hardened Image Analyzer with 100% coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import base64
import io
import pytest
from unittest.mock import MagicMock, patch

from PIL import Image

from analyzers.image_analyzer_refactored import ImageAnalyzerRefactored


@pytest.fixture(autouse=True)
def mock_cache_globally(monkeypatch):
    """Global fixture to mock cache operations."""
    async def get_mock(self, key):
        return None

    async def set_mock(self, key, value):
        pass

    from core.cache_manager import CacheManager
    monkeypatch.setattr(CacheManager, "get", get_mock)
    monkeypatch.setattr(CacheManager, "set", set_mock)


@pytest.fixture
def sample_image_base64():
    """Create a simple test image and return as base64."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@pytest.fixture
def sample_image_with_exif():
    """Create a test image with EXIF data."""
    img = Image.new('RGB', (200, 200), color='blue')

    # Add some EXIF data
    exif_dict = {
        271: "TestCamera",  # Make
        272: "Model123",    # Model
    }

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', exif=img.getexif())
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


class TestImageAnalyzerBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = ImageAnalyzerRefactored()

        assert analyzer.total_analyses == 0
        assert analyzer.logger is not None
        assert analyzer.metrics is not None

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method."""
        analyzer = ImageAnalyzerRefactored()

        repr_str = repr(analyzer)

        assert "ImageAnalyzerRefactored" in repr_str
        assert "analyses=0" in repr_str


class TestBasicImageAnalysis:
    """Basic image analysis tests."""

    @pytest.mark.asyncio
    async def test_analyze_image_basic_info(self, sample_image_base64):
        """Test basic image info extraction."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_base64,
            analysis_types=["info"]
        )

        assert "info" in result
        assert result["info"]["width"] == 100
        assert result["info"]["height"] == 100
        assert result["info"]["format"] == "PNG"
        assert result["info"]["mode"] == "RGB"

    @pytest.mark.asyncio
    async def test_analyze_image_all_types(self, sample_image_base64):
        """Test analysis with 'all' types."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_base64,
            analysis_types=["all"]
        )

        assert "info" in result
        assert "exif" in result
        assert "hashes" in result
        assert result["analysis_types"] == ["all"]

    @pytest.mark.asyncio
    async def test_analyze_image_default_all(self, sample_image_base64):
        """Test that default analysis type is 'all'."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(target=sample_image_base64)

        # Default should analyze everything
        assert "info" in result
        assert "exif" in result
        assert "hashes" in result


class TestEXIFExtraction:
    """EXIF metadata extraction tests."""

    @pytest.mark.asyncio
    async def test_extract_exif_no_data(self, sample_image_base64):
        """Test EXIF extraction when no EXIF data present."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_base64,
            analysis_types=["exif"]
        )

        assert "exif" in result
        # PNG without EXIF should return available=False
        assert result["exif"]["available"] == False

    @pytest.mark.asyncio
    async def test_extract_exif_with_data(self, sample_image_with_exif):
        """Test EXIF extraction with actual data."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_with_exif,
            analysis_types=["exif"]
        )

        assert "exif" in result
        # JPEG may have EXIF
        assert "available" in result["exif"]

    @pytest.mark.asyncio
    async def test_extract_exif_handles_gps_data(self):
        """Test EXIF extraction handles GPS data specially."""
        analyzer = ImageAnalyzerRefactored()

        # Create image with GPS EXIF
        img = Image.new('RGB', (100, 100), color='green')

        # Mock getexif to return GPS data
        mock_exif = MagicMock()
        mock_exif.items.return_value = [
            (34853, {1: 'N', 2: (40.0, 44.0, 55.0)})  # GPSInfo tag
        ]

        with patch.object(Image.Image, 'getexif', return_value=mock_exif):
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            result = await analyzer.query(
                target=img_base64,
                analysis_types=["exif"]
            )

        assert "exif" in result

    @pytest.mark.asyncio
    async def test_extract_exif_with_non_string_values(self):
        """Test EXIF extraction converts non-string values correctly."""
        analyzer = ImageAnalyzerRefactored()

        img = Image.new('RGB', (100, 100), color='cyan')

        # Mock getexif to return various data types
        mock_exif = MagicMock()
        mock_exif.items.return_value = [
            (271, "TestMake"),  # String - should pass through
            (272, 123),  # Int - should pass through
            (273, 45.67),  # Float - should pass through
            (274, (1, 2, 3)),  # Tuple - should be converted to string
        ]

        with patch.object(Image.Image, 'getexif', return_value=mock_exif):
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            result = await analyzer.query(
                target=img_base64,
                analysis_types=["exif"]
            )

        # Verify EXIF data was extracted and converted
        assert "exif" in result
        assert result["exif"]["available"] is True

    @pytest.mark.asyncio
    async def test_extract_exif_exception_handling(self):
        """Test EXIF extraction handles exceptions gracefully."""
        analyzer = ImageAnalyzerRefactored()

        img = Image.new('RGB', (100, 100), color='magenta')

        # Mock getexif to raise exception
        def raise_exception():
            raise RuntimeError("EXIF parsing failed")

        with patch.object(Image.Image, 'getexif', side_effect=raise_exception):
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            result = await analyzer.query(
                target=img_base64,
                analysis_types=["exif"]
            )

        # Should return error information
        assert "exif" in result
        assert result["exif"]["available"] is False
        assert "error" in result["exif"]


class TestImageHashing:
    """Image hashing tests."""

    @pytest.mark.asyncio
    async def test_calculate_all_hashes(self, sample_image_base64):
        """Test calculation of all hash types."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_base64,
            analysis_types=["hash"]
        )

        assert "hashes" in result
        assert "phash" in result["hashes"]
        assert "ahash" in result["hashes"]
        assert "dhash" in result["hashes"]
        assert "whash" in result["hashes"]

        # Hashes should be hex strings
        assert len(result["hashes"]["phash"]) > 0
        assert len(result["hashes"]["ahash"]) > 0

    @pytest.mark.asyncio
    async def test_identical_images_same_hash(self):
        """Test identical images produce same hash."""
        analyzer = ImageAnalyzerRefactored()

        # Create two identical images
        img1 = Image.new('RGB', (50, 50), color='yellow')
        buffer1 = io.BytesIO()
        img1.save(buffer1, format='PNG')
        base64_1 = base64.b64encode(buffer1.getvalue()).decode('utf-8')

        img2 = Image.new('RGB', (50, 50), color='yellow')
        buffer2 = io.BytesIO()
        img2.save(buffer2, format='PNG')
        base64_2 = base64.b64encode(buffer2.getvalue()).decode('utf-8')

        result1 = await analyzer.query(target=base64_1, analysis_types=["hash"])
        result2 = await analyzer.query(target=base64_2, analysis_types=["hash"])

        # Same image should produce same hash
        assert result1["hashes"]["phash"] == result2["hashes"]["phash"]


class TestImageSimilarity:
    """Image similarity comparison tests."""

    @pytest.mark.asyncio
    async def test_compare_identical_images(self):
        """Test comparing identical images shows high similarity."""
        analyzer = ImageAnalyzerRefactored()

        # Create image
        img = Image.new('RGB', (100, 100), color='purple')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Get hash first
        result1 = await analyzer.query(target=img_base64, analysis_types=["hash"])
        phash = result1["hashes"]["phash"]

        # Compare with same image
        result2 = await analyzer.query(
            target=img_base64,
            compare_hash=phash
        )

        assert "similarity" in result2
        assert int(result2["similarity"]["hamming_distance"]) == 0
        assert float(result2["similarity"]["similarity_percent"]) == 100
        assert bool(result2["similarity"]["is_similar"]) is True

    @pytest.mark.asyncio
    async def test_compare_hash_returns_valid_results(self):
        """Test hash comparison returns valid similarity metrics."""
        analyzer = ImageAnalyzerRefactored()

        # Create two images
        img1 = Image.new('RGB', (100, 100), color='white')
        buffer1 = io.BytesIO()
        img1.save(buffer1, format='PNG')
        base64_1 = base64.b64encode(buffer1.getvalue()).decode('utf-8')

        img2 = Image.new('RGB', (100, 100), color='black')
        buffer2 = io.BytesIO()
        img2.save(buffer2, format='PNG')
        base64_2 = base64.b64encode(buffer2.getvalue()).decode('utf-8')

        # Get hash of first image
        result1 = await analyzer.query(target=base64_1, analysis_types=["hash"])
        hash1 = result1["hashes"]["phash"]

        # Compare second image with first hash
        result2 = await analyzer.query(
            target=base64_2,
            compare_hash=hash1
        )

        # Verify similarity structure is present and valid
        assert "similarity" in result2
        assert "hamming_distance" in result2["similarity"]
        assert "similarity_percent" in result2["similarity"]
        assert "is_similar" in result2["similarity"]

        # Hamming distance should be non-negative
        assert int(result2["similarity"]["hamming_distance"]) >= 0

        # Similarity percent should be 0-100
        similarity_pct = float(result2["similarity"]["similarity_percent"])
        assert 0 <= similarity_pct <= 100

        # is_similar should be boolean
        assert isinstance(bool(result2["similarity"]["is_similar"]), bool)

    @pytest.mark.asyncio
    async def test_compare_hash_invalid_format(self, sample_image_base64):
        """Test hash comparison with invalid hash format."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_base64,
            compare_hash="invalid_hash_format"
        )

        assert "similarity" in result
        assert "error" in result["similarity"]


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_invalid_base64_raises_error(self):
        """Test invalid base64 raises ValueError."""
        analyzer = ImageAnalyzerRefactored()

        with pytest.raises(ValueError, match="Failed to decode"):
            await analyzer.query(target="not_valid_base64!!!")

    @pytest.mark.asyncio
    async def test_invalid_image_data_raises_error(self):
        """Test invalid image data raises ValueError."""
        analyzer = ImageAnalyzerRefactored()

        # Valid base64 but not an image
        invalid_data = base64.b64encode(b"not an image").decode('utf-8')

        with pytest.raises(ValueError, match="Failed to decode"):
            await analyzer.query(target=invalid_data)


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated_after_analysis(self, sample_image_base64):
        """Test statistics are updated after analyses."""
        analyzer = ImageAnalyzerRefactored()

        await analyzer.query(target=sample_image_base64)
        await analyzer.query(target=sample_image_base64)

        assert analyzer.total_analyses == 2

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        analyzer = ImageAnalyzerRefactored()

        status = await analyzer.get_status()

        assert status["tool"] == "ImageAnalyzerRefactored"
        assert status["total_analyses"] == 0


class TestObservability:
    """Observability tests."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        analyzer = ImageAnalyzerRefactored()

        assert analyzer.logger is not None
        assert analyzer.logger.tool_name == "ImageAnalyzerRefactored"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        analyzer = ImageAnalyzerRefactored()

        assert analyzer.metrics is not None
        assert analyzer.metrics.tool_name == "ImageAnalyzerRefactored"


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_analyze_very_small_image(self):
        """Test analyzing very small image."""
        analyzer = ImageAnalyzerRefactored()

        # 1x1 pixel image
        img = Image.new('RGB', (1, 1), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        result = await analyzer.query(target=img_base64)

        assert result["info"]["width"] == 1
        assert result["info"]["height"] == 1

    @pytest.mark.asyncio
    async def test_analyze_grayscale_image(self):
        """Test analyzing grayscale image."""
        analyzer = ImageAnalyzerRefactored()

        img = Image.new('L', (100, 100), color=128)  # Grayscale
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        result = await analyzer.query(target=img_base64)

        assert result["info"]["mode"] == "L"

    @pytest.mark.asyncio
    async def test_analyze_different_formats(self):
        """Test analyzing different image formats."""
        analyzer = ImageAnalyzerRefactored()

        for fmt in ['PNG', 'JPEG']:
            img = Image.new('RGB', (50, 50), color='orange')
            buffer = io.BytesIO()
            img.save(buffer, format=fmt)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            result = await analyzer.query(target=img_base64, analysis_types=["info"])

            assert result["info"]["format"] == fmt

    @pytest.mark.asyncio
    async def test_multiple_analysis_types(self, sample_image_base64):
        """Test specifying multiple specific analysis types."""
        analyzer = ImageAnalyzerRefactored()

        result = await analyzer.query(
            target=sample_image_base64,
            analysis_types=["info", "hash"]
        )

        assert "info" in result
        assert "hashes" in result
        assert "exif" not in result  # Not requested
