"""
Unit Tests for Service Adapters

Tests the adapter pattern implementation for all three services:
- Text/Table Service Adapter
- Illustrator Service Adapter
- Analytics Service Adapter

Version: 2.0.0
Created: 2025-11-29
"""

import pytest
from pathlib import Path
from src.models.variant_registry import load_registry_from_file
from src.services.adapters import (
    BaseServiceAdapter,
    TextServiceAdapter,
    IllustratorServiceAdapter,
    AnalyticsServiceAdapter
)
from src.services.adapters.base_adapter import (
    InvalidRequestError,
    InvalidResponseError,
    EndpointResolutionError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Load actual registry for testing"""
    registry_path = Path(__file__).parent.parent / "config" / "unified_variant_registry.json"
    return load_registry_from_file(str(registry_path))


@pytest.fixture
def text_service_config(registry):
    """Get Text Service configuration"""
    return registry.services["text_service_v1.2"]


@pytest.fixture
def illustrator_service_config(registry):
    """Get Illustrator Service configuration"""
    return registry.services["illustrator_service_v1.0"]


@pytest.fixture
def analytics_service_config(registry):
    """Get Analytics Service configuration"""
    return registry.services["analytics_service_v3"]


@pytest.fixture
def text_adapter(text_service_config):
    """Create Text Service adapter"""
    return TextServiceAdapter(text_service_config)


@pytest.fixture
def illustrator_adapter(illustrator_service_config):
    """Create Illustrator Service adapter"""
    return IllustratorServiceAdapter(illustrator_service_config)


@pytest.fixture
def analytics_adapter(analytics_service_config):
    """Create Analytics Service adapter"""
    return AnalyticsServiceAdapter(analytics_service_config)


# ============================================================================
# Text Service Adapter Tests
# ============================================================================

class TestTextServiceAdapter:
    """Tests for Text/Table Service Adapter"""

    def test_adapter_initialization(self, text_adapter, text_service_config):
        """Test adapter initializes correctly"""
        assert str(text_adapter.service_type) == "template_based"
        assert str(text_adapter.endpoint_pattern) == "single"
        assert text_adapter.base_url == str(text_service_config.base_url)
        assert len(text_adapter.list_variants()) >= 2  # bilateral_comparison, matrix_2x2 (maybe more)

    def test_build_request_bilateral_comparison(self, text_adapter, text_service_config):
        """Test building request for bilateral_comparison"""
        variant = text_service_config.variants["bilateral_comparison"]
        parameters = {
            "title": "AWS vs GCP",
            "key_points": [
                "AWS: Mature ecosystem, higher cost",
                "GCP: Better ML tools, cost-effective"
            ]
        }
        context = {"tone": "professional", "audience": "executives"}

        request = text_adapter.build_request(variant, parameters, context)

        assert request["variant_id"] == "bilateral_comparison"
        assert request["title"] == "AWS vs GCP"
        assert len(request["key_points"]) == 2
        assert request["tone"] == "professional"
        assert request["audience"] == "executives"

    def test_build_request_missing_required_field(self, text_adapter, text_service_config):
        """Test build_request raises error when title missing"""
        variant = text_service_config.variants["bilateral_comparison"]
        parameters = {}  # Missing title

        with pytest.raises(InvalidRequestError) as exc_info:
            text_adapter.build_request(variant, parameters)

        assert "Missing required fields" in str(exc_info.value)
        assert "title" in str(exc_info.value)

    def test_get_endpoint_url(self, text_adapter, text_service_config):
        """Test endpoint URL resolution for single pattern"""
        variant = text_service_config.variants["bilateral_comparison"]
        url = text_adapter.get_endpoint_url(variant)

        assert url == "https://web-production-5daf.up.railway.app/v1.2/generate"
        assert text_adapter.default_endpoint in url

    def test_validate_response_valid(self, text_adapter):
        """Test validation of valid response"""
        response = {
            "html_content": "<div>Generated content</div>"
        }

        assert text_adapter.validate_response(response) is True

    def test_validate_response_empty_content(self, text_adapter):
        """Test validation rejects empty html_content"""
        response = {
            "html_content": ""
        }

        assert text_adapter.validate_response(response) is False

    def test_validate_response_missing_html_content(self, text_adapter):
        """Test validation rejects missing html_content"""
        response = {}

        assert text_adapter.validate_response(response) is False

    def test_validate_response_error_field(self, text_adapter):
        """Test validation rejects response with error"""
        response = {
            "error": "Generation failed"
        }

        assert text_adapter.validate_response(response) is False

    def test_transform_response(self, text_adapter, text_service_config):
        """Test response transformation"""
        variant = text_service_config.variants["bilateral_comparison"]
        response = {
            "html_content": "<div>Content</div>"
        }

        transformed = text_adapter.transform_response(response, variant)

        assert transformed["html_content"] == "<div>Content</div>"
        assert transformed["variant_id"] == "bilateral_comparison"
        assert transformed["service_type"] == "template_based"

    def test_get_required_fields(self, text_adapter):
        """Test getting required fields for variant"""
        required = text_adapter.get_required_fields("bilateral_comparison")

        assert "variant_id" in required
        assert "title" in required

    def test_get_optional_fields(self, text_adapter):
        """Test getting optional fields for variant"""
        optional = text_adapter.get_optional_fields("bilateral_comparison")

        assert "subtitle" in optional
        assert "key_points" in optional
        assert "tone" in optional
        assert "audience" in optional


# ============================================================================
# Illustrator Service Adapter Tests
# ============================================================================

class TestIllustratorServiceAdapter:
    """Tests for Illustrator Service Adapter"""

    def test_adapter_initialization(self, illustrator_adapter, illustrator_service_config):
        """Test adapter initializes correctly"""
        assert str(illustrator_adapter.service_type) == "llm_generated"
        assert str(illustrator_adapter.endpoint_pattern) == "per_variant"
        assert illustrator_adapter.base_url == str(illustrator_service_config.base_url)
        assert len(illustrator_adapter.list_variants()) >= 3  # pyramid, funnel, concentric_circles (maybe more)

    def test_build_request_pyramid(self, illustrator_adapter, illustrator_service_config):
        """Test building request for pyramid"""
        variant = illustrator_service_config.variants["pyramid"]
        parameters = {
            "num_levels": 4,
            "topic": "Organizational Hierarchy",
            "target_points": ["Vision", "Strategy", "Tactics", "Execution"]
        }
        context = {
            "presentation_title": "Company Overview",
            "previous_slides": []
        }

        request = illustrator_adapter.build_request(variant, parameters, context)

        assert request["num_levels"] == 4
        assert request["topic"] == "Organizational Hierarchy"
        assert len(request["target_points"]) == 4
        assert request["context"]["presentation_title"] == "Company Overview"

    def test_build_request_uses_optimal_count(self, illustrator_adapter, illustrator_service_config):
        """Test build_request uses optimal count when not specified"""
        variant = illustrator_service_config.variants["pyramid"]
        parameters = {
            "topic": "Test Topic"
            # num_levels not provided
        }

        request = illustrator_adapter.build_request(variant, parameters)

        # Should use optimal_count from config (4)
        assert request["num_levels"] == 4

    def test_build_request_validates_count_range(self, illustrator_adapter, illustrator_service_config):
        """Test build_request validates count is in range"""
        variant = illustrator_service_config.variants["pyramid"]
        parameters = {
            "num_levels": 10,  # Max is 6
            "topic": "Test Topic"
        }

        with pytest.raises(InvalidRequestError) as exc_info:
            illustrator_adapter.build_request(variant, parameters)

        assert "must be between" in str(exc_info.value)

    def test_build_request_missing_topic(self, illustrator_adapter, illustrator_service_config):
        """Test build_request raises error when topic missing"""
        variant = illustrator_service_config.variants["pyramid"]
        parameters = {
            "num_levels": 4
            # topic missing
        }

        with pytest.raises(InvalidRequestError) as exc_info:
            illustrator_adapter.build_request(variant, parameters)

        assert "topic" in str(exc_info.value).lower()

    def test_get_endpoint_url_pyramid(self, illustrator_adapter, illustrator_service_config):
        """Test endpoint URL resolution for pyramid"""
        variant = illustrator_service_config.variants["pyramid"]
        url = illustrator_adapter.get_endpoint_url(variant)

        assert url == "http://localhost:8000/v1.0/pyramid/generate"

    def test_get_endpoint_url_funnel(self, illustrator_adapter, illustrator_service_config):
        """Test endpoint URL resolution for funnel"""
        variant = illustrator_service_config.variants["funnel"]
        url = illustrator_adapter.get_endpoint_url(variant)

        assert url == "http://localhost:8000/v1.0/funnel/generate"

    def test_validate_response_valid(self, illustrator_adapter):
        """Test validation of valid response"""
        response = {
            "html_content": "<svg>...</svg>",
            "metadata": {
                "levels_generated": 4
            }
        }

        assert illustrator_adapter.validate_response(response) is True

    def test_validate_response_without_metadata(self, illustrator_adapter):
        """Test validation accepts response without metadata"""
        response = {
            "html_content": "<svg>...</svg>"
        }

        assert illustrator_adapter.validate_response(response) is True

    def test_validate_response_empty_content(self, illustrator_adapter):
        """Test validation rejects empty html_content"""
        response = {
            "html_content": ""
        }

        assert illustrator_adapter.validate_response(response) is False

    def test_transform_response(self, illustrator_adapter, illustrator_service_config):
        """Test response transformation"""
        variant = illustrator_service_config.variants["pyramid"]
        response = {
            "html_content": "<svg>...</svg>",
            "metadata": {"levels": 4}
        }

        transformed = illustrator_adapter.transform_response(response, variant)

        assert transformed["html_content"] == "<svg>...</svg>"
        assert transformed["variant_id"] == "pyramid"
        assert transformed["service_type"] == "llm_generated"
        assert transformed["metadata"] == {"levels": 4}

    def test_get_count_range(self, illustrator_adapter):
        """Test getting count range for variant"""
        count_range = illustrator_adapter.get_count_range("pyramid")

        assert count_range["min"] == 3
        assert count_range["max"] == 6
        assert count_range["optimal"] == 4

    def test_get_element_name(self, illustrator_adapter):
        """Test getting element name for variant"""
        element_name = illustrator_adapter.get_element_name("pyramid")
        assert element_name == "levels"

        element_name = illustrator_adapter.get_element_name("funnel")
        assert element_name == "stages"


# ============================================================================
# Analytics Service Adapter Tests
# ============================================================================

class TestAnalyticsServiceAdapter:
    """Tests for Analytics Service Adapter"""

    def test_adapter_initialization(self, analytics_adapter, analytics_service_config):
        """Test adapter initializes correctly"""
        assert str(analytics_adapter.service_type) == "data_visualization"
        assert str(analytics_adapter.endpoint_pattern) == "typed"
        assert analytics_adapter.base_url == str(analytics_service_config.base_url)
        assert len(analytics_adapter.list_variants()) >= 2  # pie_chart, bar_chart (maybe more)

    def test_build_request_pie_chart(self, analytics_adapter, analytics_service_config):
        """Test building request for pie chart"""
        variant = analytics_service_config.variants["pie_chart"]
        parameters = {
            "data": [
                {"label": "Product A", "value": 45},
                {"label": "Product B", "value": 30},
                {"label": "Product C", "value": 25}
            ],
            "narrative": "Market share distribution"
        }
        context = {
            "tone": "professional",
            "audience": "executives"
        }

        request = analytics_adapter.build_request(variant, parameters, context)

        assert request["chart_type"] == "pie"
        assert len(request["data"]) == 3
        assert request["narrative"] == "Market share distribution"
        assert request["context"]["tone"] == "professional"

    def test_build_request_missing_data(self, analytics_adapter, analytics_service_config):
        """Test build_request raises error when data missing"""
        variant = analytics_service_config.variants["pie_chart"]
        parameters = {}  # Missing data

        with pytest.raises(InvalidRequestError) as exc_info:
            analytics_adapter.build_request(variant, parameters)

        assert "data" in str(exc_info.value).lower()

    def test_build_request_validates_data_min_items(self, analytics_adapter, analytics_service_config):
        """Test build_request validates minimum data items"""
        variant = analytics_service_config.variants["pie_chart"]
        parameters = {
            "data": [{"label": "A", "value": 100}]  # Only 1 item, min is 2
        }

        with pytest.raises(InvalidRequestError) as exc_info:
            analytics_adapter.build_request(variant, parameters)

        assert "at least" in str(exc_info.value)

    def test_build_request_validates_data_max_items(self, analytics_adapter, analytics_service_config):
        """Test build_request validates maximum data items"""
        variant = analytics_service_config.variants["pie_chart"]
        # Create data with 13 items (max is 12)
        parameters = {
            "data": [{"label": f"Item {i}", "value": i} for i in range(13)]
        }

        with pytest.raises(InvalidRequestError) as exc_info:
            analytics_adapter.build_request(variant, parameters)

        assert "at most" in str(exc_info.value)

    def test_get_endpoint_url_chartjs(self, analytics_adapter, analytics_service_config):
        """Test endpoint URL resolution for Chart.js variant"""
        variant = analytics_service_config.variants["pie_chart"]
        url = analytics_adapter.get_endpoint_url(variant)

        assert url == "http://localhost:8006/analytics/v3/chartjs/generate"

    def test_validate_response_valid_l02(self, analytics_adapter):
        """Test validation of valid L02 response (chart + observations)"""
        response = {
            "element_3": "<div>chart HTML</div>",
            "element_2": "AI-generated observations"
        }

        assert analytics_adapter.validate_response(response) is True

    def test_validate_response_valid_l01(self, analytics_adapter):
        """Test validation of valid L01 response (chart only)"""
        response = {
            "element_3": "<div>chart HTML</div>"
        }

        assert analytics_adapter.validate_response(response) is True

    def test_validate_response_missing_chart(self, analytics_adapter):
        """Test validation rejects missing element_3 (chart)"""
        response = {
            "element_2": "observations"
        }

        assert analytics_adapter.validate_response(response) is False

    def test_validate_response_empty_chart(self, analytics_adapter):
        """Test validation rejects empty element_3"""
        response = {
            "element_3": ""
        }

        assert analytics_adapter.validate_response(response) is False

    def test_transform_response(self, analytics_adapter, analytics_service_config):
        """Test response transformation to semantic names"""
        variant = analytics_service_config.variants["pie_chart"]
        response = {
            "element_3": "<div>chart</div>",
            "element_2": "observations"
        }

        transformed = analytics_adapter.transform_response(response, variant)

        # Semantic names
        assert transformed["chart_html"] == "<div>chart</div>"
        assert transformed["observations"] == "observations"
        assert transformed["variant_id"] == "pie_chart"
        assert transformed["service_type"] == "data_visualization"

        # Backward compatibility - original names preserved
        assert transformed["element_3"] == "<div>chart</div>"
        assert transformed["element_2"] == "observations"

    def test_get_data_requirements(self, analytics_adapter):
        """Test getting data requirements for variant"""
        requirements = analytics_adapter.get_data_requirements("pie_chart")

        # Structure is returned as string from enum
        assert "label_value_pairs" in requirements["structure"].lower()
        assert requirements["min_items"] == 2
        assert requirements["max_items"] == 12
        assert "numeric" in requirements["value_type"].lower()
        assert requirements["supports_percentages"] is True

    def test_get_chart_library(self, analytics_adapter):
        """Test getting chart library for variant"""
        library = analytics_adapter.get_chart_library("pie_chart")
        assert library == "chartjs"

    def test_get_chart_type(self, analytics_adapter):
        """Test getting chart type for variant"""
        chart_type = analytics_adapter.get_chart_type("pie_chart")
        assert chart_type == "pie"

    def test_supports_custom_colors(self, analytics_adapter):
        """Test checking custom color support"""
        assert analytics_adapter.supports_custom_colors("pie_chart") is True

    def test_supports_data_labels(self, analytics_adapter):
        """Test checking data label support"""
        assert analytics_adapter.supports_data_labels("pie_chart") is True


# ============================================================================
# Base Adapter Tests
# ============================================================================

class TestBaseAdapterCommon:
    """Tests for common base adapter functionality"""

    def test_get_variant(self, text_adapter):
        """Test getting variant by ID"""
        variant = text_adapter.get_variant("bilateral_comparison")
        assert variant is not None
        assert variant.variant_id == "bilateral_comparison"

    def test_get_variant_not_found(self, text_adapter):
        """Test getting non-existent variant"""
        variant = text_adapter.get_variant("nonexistent")
        assert variant is None

    def test_list_variants(self, illustrator_adapter):
        """Test listing all variants"""
        variants = illustrator_adapter.list_variants()
        assert len(variants) == 3
        assert "pyramid" in variants
        assert "funnel" in variants
        assert "concentric_circles" in variants

    def test_is_variant_enabled(self, text_adapter):
        """Test checking if variant is enabled"""
        assert text_adapter.is_variant_enabled("bilateral_comparison") is True
        assert text_adapter.is_variant_enabled("nonexistent") is False

    def test_get_timeout(self, analytics_adapter):
        """Test getting timeout"""
        timeout = analytics_adapter.get_timeout()
        assert timeout == 60

    def test_handle_error(self, text_adapter, text_service_config):
        """Test error handling"""
        variant = text_service_config.variants["bilateral_comparison"]
        error = Exception("Test error")
        request = {"test": "request"}

        error_response = text_adapter.handle_error(error, variant, request)

        assert error_response["error"] is True
        assert error_response["error_type"] == "Exception"
        assert error_response["error_message"] == "Test error"
        assert error_response["variant_id"] == "bilateral_comparison"

    def test_adapter_repr(self, text_adapter):
        """Test adapter string representation"""
        repr_str = repr(text_adapter)
        assert "TextServiceAdapter" in repr_str
        assert "template_based" in repr_str


# ============================================================================
# Integration Tests
# ============================================================================

class TestAdapterIntegration:
    """Integration tests using actual registry"""

    def test_all_text_variants_have_required_config(self, text_adapter):
        """Test all text variants have required configuration"""
        for variant_id in text_adapter.list_variants():
            variant = text_adapter.get_variant(variant_id)
            assert variant is not None
            assert variant.classification is not None
            assert len(variant.classification.keywords) >= 5

    def test_all_illustrator_variants_have_parameters(self, illustrator_adapter):
        """Test all illustrator variants have parameters"""
        for variant_id in illustrator_adapter.list_variants():
            variant = illustrator_adapter.get_variant(variant_id)
            assert variant is not None
            assert variant.parameters is not None
            assert variant.parameters.count_field is not None
            assert variant.parameters.count_range is not None

    def test_all_analytics_variants_have_data_requirements(self, analytics_adapter):
        """Test all analytics variants have data requirements"""
        for variant_id in analytics_adapter.list_variants():
            variant = analytics_adapter.get_variant(variant_id)
            assert variant is not None
            assert variant.data_requirements is not None
            assert variant.data_requirements.min_items >= 1

    def test_endpoint_resolution_for_all_variants(self, text_adapter, illustrator_adapter, analytics_adapter):
        """Test endpoint resolution works for all variants"""
        # Text service - all use same endpoint
        for variant_id in text_adapter.list_variants():
            variant = text_adapter.get_variant(variant_id)
            url = text_adapter.get_endpoint_url(variant)
            assert url.startswith("https://")

        # Illustrator - each has unique endpoint
        for variant_id in illustrator_adapter.list_variants():
            variant = illustrator_adapter.get_variant(variant_id)
            url = illustrator_adapter.get_endpoint_url(variant)
            assert f"/{variant_id}/generate" in url

        # Analytics - endpoints by library type
        for variant_id in analytics_adapter.list_variants():
            variant = analytics_adapter.get_variant(variant_id)
            url = analytics_adapter.get_endpoint_url(variant)
            assert "/analytics/v3/" in url


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
