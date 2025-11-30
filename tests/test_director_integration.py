"""
Tests for Director Integration Layer

Comprehensive tests for Director Agent integration with unified variant system.

Version: 2.0.0
Created: 2025-11-29
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.director_integration import DirectorIntegrationLayer
from src.models.agents import Slide, PresentationStrawman
from src.services.unified_slide_classifier import ClassificationMatch


@pytest.fixture
def mock_registry():
    """Create mock registry for testing"""
    with patch('src.services.director_integration.get_registry') as mock:
        registry = Mock()
        registry.services = {}
        registry.version = "2.0.0"
        registry.last_updated = "2025-11-29"
        mock.return_value = registry
        yield mock


@pytest.fixture
def integration(mock_registry):
    """Create integration layer instance with mocked registry"""
    return DirectorIntegrationLayer()


class TestIntegrationInitialization:
    """Test integration layer initialization"""

    def test_initialization(self, integration):
        """Test integration layer initializes correctly"""
        assert integration is not None
        assert integration.registry is not None
        assert integration.classifier is not None
        assert integration.router is not None


class TestSlideClassification:
    """Test slide classification methods"""

    def test_classify_slide_with_title(self, integration):
        """Test classifying slide with only title"""
        with patch.object(integration.classifier, 'classify_slide') as mock_classify:
            mock_classify.return_value = [
                ClassificationMatch(
                    variant_id="pie_chart",
                    service_name="analytics_service_v3",
                    display_name="Pie Chart",
                    priority=2,
                    match_score=5,
                    matched_keywords=["pie", "chart", "percentage"],
                    confidence=0.75
                )
            ]

            result = integration.classify_slide(
                title="Market Share Distribution"
            )

            assert result["variant_id"] == "pie_chart"
            assert result["service_name"] == "analytics_service_v3"
            assert result["confidence"] == 0.75
            assert result["best_match"] is not None

    def test_classify_slide_with_multiple_fields(self, integration):
        """Test classifying slide with title, key_points, and description"""
        with patch.object(integration.classifier, 'classify_slide') as mock_classify:
            mock_classify.return_value = [
                ClassificationMatch(
                    variant_id="funnel",
                    service_name="illustrator_service_v1.0",
                    display_name="Funnel (Conversion)",
                    priority=5,
                    match_score=8,
                    matched_keywords=["funnel", "conversion", "pipeline"],
                    confidence=0.85
                )
            ]

            result = integration.classify_slide(
                title="Sales Conversion Funnel",
                key_points=["Awareness", "Consideration", "Decision"],
                description="TOFU to BOFU pipeline"
            )

            assert result["variant_id"] == "funnel"
            assert result["confidence"] == 0.85

    def test_classify_slide_no_matches(self, integration):
        """Test classifying slide with no matches"""
        with patch.object(integration.classifier, 'classify_slide') as mock_classify:
            mock_classify.return_value = []

            result = integration.classify_slide(
                title="Unrelated Content"
            )

            assert result["variant_id"] is None
            assert result["service_name"] is None
            assert result["confidence"] == 0.0
            assert result["best_match"] is None


class TestSlideEnrichment:
    """Test slide enrichment with classification"""

    def test_classify_and_enrich_slide(self, integration):
        """Test enriching slide with classification data"""
        # Use Mock instead of Slide to avoid required field validation
        slide = Mock()
        slide.slide_id = "slide_1"
        slide.title = "Market Share Analysis"
        slide.key_points = ["Product A: 45%", "Product B: 30%"]
        slide.description = "Revenue breakdown"

        with patch.object(integration.classifier, 'classify_slide') as mock_classify:
            mock_classify.return_value = [
                ClassificationMatch(
                    variant_id="pie_chart",
                    service_name="analytics_service_v3",
                    display_name="Pie Chart",
                    priority=2,
                    match_score=6,
                    matched_keywords=["pie", "percentage", "share"],
                    confidence=0.80
                )
            ]

            enriched = integration.classify_and_enrich_slide(slide)

            assert enriched.variant_id == "pie_chart"
            assert enriched.service_name == "analytics_service_v3"
            assert enriched.slide_type_classification == "pie_chart"
            assert enriched.classification_confidence == 0.80

    def test_enrich_slide_no_classification(self, integration):
        """Test enriching slide when no classification found"""
        # Use Mock instead of Slide
        slide = Mock()
        slide.slide_id = "slide_1"
        slide.title = "Unrelated Content"

        with patch.object(integration.classifier, 'classify_slide') as mock_classify:
            mock_classify.return_value = []

            enriched = integration.classify_and_enrich_slide(slide)

            # Slide should be returned unchanged (no classification)
            assert enriched.slide_id == "slide_1"


class TestContentGeneration:
    """Test content generation methods"""

    @pytest.mark.asyncio
    async def test_generate_slide_content_success(self, integration):
        """Test successful content generation"""
        with patch.object(integration.router, 'generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "html_content": "<div>Generated content</div>",
                "variant_id": "pie_chart",
                "service_name": "analytics_service_v3"
            }

            result = await integration.generate_slide_content(
                variant_id="pie_chart",
                service_name="analytics_service_v3",
                parameters={"data": [{"label": "A", "value": 45}]},
                context={"presentation_title": "Q4 Review"}
            )

            assert result["success"] is True
            assert "html_content" in result
            assert result["variant_id"] == "pie_chart"

    @pytest.mark.asyncio
    async def test_generate_slide_content_failure(self, integration):
        """Test failed content generation"""
        with patch.object(integration.router, 'generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "success": False,
                "error": "Service timeout",
                "error_type": "timeout",
                "variant_id": "pie_chart",
                "service_name": "analytics_service_v3"
            }

            result = await integration.generate_slide_content(
                variant_id="pie_chart",
                service_name="analytics_service_v3",
                parameters={"data": [{"label": "A", "value": 45}]}
            )

            assert result["success"] is False
            assert "error" in result
            assert result["error_type"] == "timeout"


class TestPresentationContentGeneration:
    """Test full presentation content generation"""

    @pytest.mark.asyncio
    async def test_generate_presentation_content(self, integration):
        """Test generating content for entire presentation"""
        # Create mock strawman
        slide1 = Mock(spec=Slide)
        slide1.slide_id = "slide_1"
        slide1.title = "Market Share"
        slide1.variant_id = "pie_chart"
        slide1.service_name = "analytics_service_v3"
        slide1.chart_data = [{"label": "A", "value": 45}]

        slide2 = Mock(spec=Slide)
        slide2.slide_id = "slide_2"
        slide2.title = "Sales Funnel"
        slide2.variant_id = "funnel"
        slide2.service_name = "illustrator_service_v1.0"
        slide2.topic = "Sales Pipeline"
        slide2.target_points = ["Leads", "Qualified", "Closed"]

        strawman = Mock(spec=PresentationStrawman)
        strawman.main_title = "Q4 Business Review"
        strawman.slides = [slide1, slide2]

        with patch.object(integration, 'generate_slide_content', new_callable=AsyncMock) as mock_generate:
            # Mock successful generation for both slides
            mock_generate.side_effect = [
                {
                    "success": True,
                    "chart_html": "<div>Pie chart</div>",
                    "variant_id": "pie_chart",
                    "service_name": "analytics_service_v3"
                },
                {
                    "success": True,
                    "html_content": "<div>Funnel diagram</div>",
                    "variant_id": "funnel",
                    "service_name": "illustrator_service_v1.0"
                }
            ]

            result = await integration.generate_presentation_content(
                strawman=strawman,
                session_id="session_123"
            )

            assert result["metadata"]["successful_count"] == 2
            assert result["metadata"]["failed_count"] == 0
            assert result["metadata"]["skipped_count"] == 0
            assert len(result["generated_slides"]) == 2

    @pytest.mark.asyncio
    async def test_generate_presentation_with_failures(self, integration):
        """Test presentation generation with some failures"""
        slide1 = Mock(spec=Slide)
        slide1.slide_id = "slide_1"
        slide1.title = "Chart 1"
        slide1.variant_id = "pie_chart"
        slide1.service_name = "analytics_service_v3"
        slide1.chart_data = [{"label": "A", "value": 45}]

        slide2 = Mock(spec=Slide)
        slide2.slide_id = "slide_2"
        slide2.title = "Chart 2"
        slide2.variant_id = "bar_chart"
        slide2.service_name = "analytics_service_v3"
        slide2.chart_data = [{"label": "B", "value": 30}]

        strawman = Mock(spec=PresentationStrawman)
        strawman.main_title = "Test Presentation"
        strawman.slides = [slide1, slide2]

        with patch.object(integration, 'generate_slide_content', new_callable=AsyncMock) as mock_generate:
            # First succeeds, second fails
            mock_generate.side_effect = [
                {
                    "success": True,
                    "chart_html": "<div>Chart 1</div>",
                    "variant_id": "pie_chart",
                    "service_name": "analytics_service_v3"
                },
                {
                    "success": False,
                    "error": "Service error",
                    "error_type": "http_error",
                    "variant_id": "bar_chart",
                    "service_name": "analytics_service_v3"
                }
            ]

            result = await integration.generate_presentation_content(strawman=strawman)

            assert result["metadata"]["successful_count"] == 1
            assert result["metadata"]["failed_count"] == 1
            assert len(result["generated_slides"]) == 1
            assert len(result["failed_slides"]) == 1

    @pytest.mark.asyncio
    async def test_generate_presentation_skips_unclassified(self, integration):
        """Test presentation generation skips slides without classification"""
        slide1 = Mock(spec=Slide)
        slide1.slide_id = "slide_1"
        slide1.title = "Classified Slide"
        slide1.variant_id = "pie_chart"
        slide1.service_name = "analytics_service_v3"
        slide1.chart_data = [{"label": "A", "value": 45}]

        slide2 = Mock(spec=Slide)
        slide2.slide_id = "slide_2"
        slide2.title = "Unclassified Slide"
        # No variant_id or service_name

        strawman = Mock(spec=PresentationStrawman)
        strawman.main_title = "Test"
        strawman.slides = [slide1, slide2]

        with patch.object(integration, 'generate_slide_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "chart_html": "<div>Chart</div>",
                "variant_id": "pie_chart",
                "service_name": "analytics_service_v3"
            }

            result = await integration.generate_presentation_content(strawman=strawman)

            assert result["metadata"]["successful_count"] == 1
            assert result["metadata"]["skipped_count"] == 1
            assert mock_generate.call_count == 1  # Only called once


class TestParameterBuilding:
    """Test parameter building from slides"""

    def test_build_parameters_from_slide(self, integration):
        """Test building parameters from slide attributes"""
        slide = Mock(spec=Slide)
        slide.title = "Test Title"
        slide.key_points = ["Point 1", "Point 2"]
        slide.description = "Test description"
        slide.variant_id = "pie_chart"
        slide.chart_data = [{"label": "A", "value": 45}]

        params = integration._build_parameters_from_slide(slide)

        assert params["title"] == "Test Title"
        assert params["key_points"] == ["Point 1", "Point 2"]
        assert params["description"] == "Test description"
        assert params["variant_id"] == "pie_chart"
        assert params["data"] == [{"label": "A", "value": 45}]

    def test_build_parameters_minimal_slide(self, integration):
        """Test building parameters from minimal slide"""
        slide = Mock(spec=Slide)
        slide.title = "Title Only"
        slide.variant_id = "funnel"

        params = integration._build_parameters_from_slide(slide)

        assert params["title"] == "Title Only"
        assert params["variant_id"] == "funnel"
        assert "key_points" not in params
        assert "description" not in params


class TestUtilityMethods:
    """Test utility methods"""

    def test_get_variant_info(self, integration):
        """Test getting variant information"""
        with patch.object(integration.router, 'get_variant_info') as mock_info:
            mock_info.return_value = {
                "variant_id": "pie_chart",
                "display_name": "Pie Chart",
                "status": "production"
            }

            info = integration.get_variant_info("pie_chart", "analytics_service_v3")

            assert info["variant_id"] == "pie_chart"
            assert info["display_name"] == "Pie Chart"

    def test_list_all_variants(self, integration):
        """Test listing all variants"""
        with patch.object(integration.router, 'list_all_variants') as mock_list:
            mock_list.return_value = [
                {"variant_id": "pie_chart", "priority": 2},
                {"variant_id": "bar_chart", "priority": 2},
                {"variant_id": "funnel", "priority": 5}
            ]

            variants = integration.list_all_variants()

            assert len(variants) == 3
            assert variants[0]["variant_id"] == "pie_chart"

    def test_get_stats(self, integration):
        """Test getting comprehensive statistics"""
        with patch.object(integration.router, 'get_service_stats') as mock_router_stats, \
             patch.object(integration.classifier, 'get_classification_stats') as mock_classifier_stats:

            mock_router_stats.return_value = {
                "total_services": 3,
                "total_variants": 56
            }

            mock_classifier_stats.return_value = {
                "total_variants": 56,
                "unique_keywords": 250
            }

            stats = integration.get_stats()

            assert "service_stats" in stats
            assert "classification_stats" in stats
            assert "registry_info" in stats
            assert stats["service_stats"]["total_services"] == 3
            assert stats["classification_stats"]["unique_keywords"] == 250


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
