"""
Tests for Service Metadata Exporter

Comprehensive tests for service metadata export utilities.

Version: 1.0.0
Created: 2025-11-29
"""

import pytest
import json
import tempfile
import os
from src.utils.service_metadata_exporter import (
    ServiceMetadataExporter,
    VariantMetadata,
    ServiceMetadata,
    create_exporter_from_registry
)


class TestVariantMetadata:
    """Test VariantMetadata model"""

    def test_create_variant_metadata(self):
        """Test creating variant metadata"""
        variant = VariantMetadata(
            variant_id="pie_chart",
            display_name="Pie Chart",
            description="Circular chart showing proportional data",
            endpoint="/v3/charts/pie",
            keywords=["pie", "donut", "chart", "percentage", "proportion"],
            priority=2
        )

        assert variant.variant_id == "pie_chart"
        assert variant.display_name == "Pie Chart"
        assert len(variant.keywords) == 5
        assert variant.priority == 2

    def test_variant_requires_minimum_keywords(self):
        """Test that variant requires minimum 5 keywords"""
        with pytest.raises(Exception):  # Pydantic validation error
            VariantMetadata(
                variant_id="test",
                display_name="Test",
                description="Test variant",
                endpoint="/test",
                keywords=["one", "two", "three"]  # Only 3 keywords
            )

    def test_variant_with_optional_fields(self):
        """Test variant with all optional fields"""
        variant = VariantMetadata(
            variant_id="bar_chart",
            display_name="Bar Chart",
            description="Vertical or horizontal bar chart",
            endpoint="/v3/charts/bar",
            keywords=["bar", "column", "chart", "comparison", "horizontal"],
            priority=2,
            layout_id="L02",
            status="production",
            use_cases=["Sales comparison", "Year-over-year analysis"],
            best_for="Comparing discrete categories",
            avoid_when="Too many categories (>15)",
            required_fields=["data", "title"],
            optional_fields=["orientation", "colors"],
            output_format="html"
        )

        assert variant.layout_id == "L02"
        assert len(variant.use_cases) == 2
        assert variant.best_for is not None
        assert "data" in variant.required_fields


class TestServiceMetadata:
    """Test ServiceMetadata model"""

    def test_create_service_metadata(self):
        """Test creating service metadata"""
        variant = VariantMetadata(
            variant_id="pie_chart",
            display_name="Pie Chart",
            description="Test",
            endpoint="/test",
            keywords=["one", "two", "three", "four", "five"]
        )

        metadata = ServiceMetadata(
            service_name="analytics_service_v3",
            service_version="3.0.0",
            service_type="data_visualization",
            base_url="https://analytics.example.com",
            variants=[variant]
        )

        assert metadata.service_name == "analytics_service_v3"
        assert len(metadata.variants) == 1
        assert metadata.last_updated is not None


class TestServiceMetadataExporter:
    """Test ServiceMetadataExporter class"""

    def test_create_exporter(self):
        """Test creating exporter instance"""
        exporter = ServiceMetadataExporter(
            service_name="test_service",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        assert exporter.metadata.service_name == "test_service"
        assert exporter.get_variant_count() == 0

    def test_add_variant(self):
        """Test adding variant to exporter"""
        exporter = ServiceMetadataExporter(
            service_name="test_service",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="test_variant",
            display_name="Test Variant",
            description="Test description",
            endpoint="/test",
            keywords=["one", "two", "three", "four", "five"]
        )

        assert exporter.get_variant_count() == 1
        assert exporter.get_keyword_count() == 5

    def test_method_chaining(self):
        """Test method chaining for add_variant"""
        exporter = ServiceMetadataExporter(
            service_name="test_service",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="variant1",
            display_name="Variant 1",
            description="First variant",
            endpoint="/v1",
            keywords=["a", "b", "c", "d", "e"]
        ).add_variant(
            variant_id="variant2",
            display_name="Variant 2",
            description="Second variant",
            endpoint="/v2",
            keywords=["f", "g", "h", "i", "j"]
        )

        assert exporter.get_variant_count() == 2
        assert exporter.get_keyword_count() == 10

    def test_export_to_registry_format_single_endpoint(self):
        """Test export with single endpoint pattern"""
        exporter = ServiceMetadataExporter(
            service_name="test_service",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="only_variant",
            display_name="Only Variant",
            description="Single variant",
            endpoint="/generate",
            keywords=["one", "two", "three", "four", "five"]
        )

        registry = exporter.export_to_registry_format()

        assert "test_service" in registry
        assert registry["test_service"]["endpoint_pattern"] == "single"
        assert "only_variant" in registry["test_service"]["variants"]

    def test_export_to_registry_format_typed_endpoints(self):
        """Test export with typed endpoint pattern"""
        exporter = ServiceMetadataExporter(
            service_name="analytics_service",
            service_version="1.0.0",
            service_type="data_visualization",
            base_url="https://analytics.example.com"
        )

        exporter.add_variant(
            variant_id="pie_chart",
            display_name="Pie Chart",
            description="Pie chart",
            endpoint="/charts/pie",
            keywords=["pie", "donut", "chart", "circular", "proportion"]
        ).add_variant(
            variant_id="bar_chart",
            display_name="Bar Chart",
            description="Bar chart",
            endpoint="/charts/bar",
            keywords=["bar", "column", "chart", "comparison", "vertical"]
        )

        registry = exporter.export_to_registry_format()

        assert registry["analytics_service"]["endpoint_pattern"] == "typed"

    def test_export_to_registry_format_per_variant_endpoints(self):
        """Test export with per_variant endpoint pattern"""
        exporter = ServiceMetadataExporter(
            service_name="mixed_service",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://mixed.example.com"
        )

        exporter.add_variant(
            variant_id="variant_a",
            display_name="Variant A",
            description="First",
            endpoint="/api/variant_a/generate",
            keywords=["a", "b", "c", "d", "e"]
        ).add_variant(
            variant_id="variant_b",
            display_name="Variant B",
            description="Second",
            endpoint="/api/variant_b/create",
            keywords=["f", "g", "h", "i", "j"]
        )

        registry = exporter.export_to_registry_format()

        assert registry["mixed_service"]["endpoint_pattern"] == "per_variant"

    def test_export_includes_all_metadata(self):
        """Test that export includes all metadata fields"""
        exporter = ServiceMetadataExporter(
            service_name="full_service",
            service_version="2.0.0",
            service_type="llm_generated",
            base_url="https://full.example.com",
            supports_batch=True,
            supports_streaming=True,
            authentication_required=True,
            maintainer="team@example.com",
            documentation_url="https://docs.example.com"
        )

        exporter.add_variant(
            variant_id="test",
            display_name="Test",
            description="Test variant",
            endpoint="/test",
            keywords=["a", "b", "c", "d", "e"],
            priority=3,
            layout_id="L01",
            use_cases=["Use case 1", "Use case 2"],
            best_for="Testing",
            avoid_when="Production",
            required_fields=["field1"],
            optional_fields=["field2"],
            output_format="json"
        )

        registry = exporter.export_to_registry_format()
        service = registry["full_service"]

        assert service["service_version"] == "2.0.0"
        assert service["service_type"] == "llm_generated"
        assert service["capabilities"]["batch_processing"] is True
        assert service["capabilities"]["streaming"] is True
        assert service["authentication"]["required"] is True
        assert service["metadata"]["maintainer"] == "team@example.com"

        variant = service["variants"]["test"]
        assert variant["classification"]["priority"] == 3
        assert variant["layout_id"] == "L01"
        assert len(variant["llm_guidance"]["use_cases"]) == 2
        assert variant["parameters"]["output_format"] == "json"

    def test_export_to_json(self):
        """Test export to JSON string"""
        exporter = ServiceMetadataExporter(
            service_name="json_test",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="test",
            display_name="Test",
            description="Test",
            endpoint="/test",
            keywords=["a", "b", "c", "d", "e"]
        )

        json_str = exporter.export_to_json()

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert "json_test" in parsed
        assert parsed["json_test"]["service_version"] == "1.0.0"

    def test_export_to_file(self):
        """Test export to file"""
        exporter = ServiceMetadataExporter(
            service_name="file_test",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="test",
            display_name="Test",
            description="Test",
            endpoint="/test",
            keywords=["a", "b", "c", "d", "e"]
        )

        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            exporter.export_to_file(temp_path)

            # Verify file exists and contains valid JSON
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)

            assert "file_test" in data
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_stats(self):
        """Test getting statistics"""
        exporter = ServiceMetadataExporter(
            service_name="stats_test",
            service_version="1.0.0",
            service_type="data_visualization",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="variant1",
            display_name="Variant 1",
            description="First",
            endpoint="/v1",
            keywords=["a", "b", "c", "d", "e"],
            priority=2,
            layout_id="L01",
            status="production"
        ).add_variant(
            variant_id="variant2",
            display_name="Variant 2",
            description="Second",
            endpoint="/v2",
            keywords=["f", "g", "h", "i", "j", "k"],
            priority=2,
            layout_id="L02",
            status="production"
        ).add_variant(
            variant_id="variant3",
            display_name="Variant 3",
            description="Third",
            endpoint="/v3",
            keywords=["l", "m", "n", "o", "p"],
            priority=5,
            layout_id="L01",
            status="beta"
        )

        stats = exporter.get_stats()

        assert stats["variant_count"] == 3
        assert stats["total_keywords"] == 16
        assert stats["avg_keywords_per_variant"] == pytest.approx(16/3)
        assert stats["status_breakdown"]["production"] == 2
        assert stats["status_breakdown"]["beta"] == 1
        assert stats["priority_distribution"][2] == 2
        assert stats["priority_distribution"][5] == 1
        assert "L01" in stats["layout_ids"]
        assert "L02" in stats["layout_ids"]


class TestCreateExporterFromRegistry:
    """Test create_exporter_from_registry function"""

    def test_create_from_registry_data(self):
        """Test creating exporter from existing registry data"""
        registry_data = {
            "services": {
                "test_service": {
                    "service_name": "test_service",
                    "service_version": "2.0.0",
                    "service_type": "template_based",
                    "base_url": "https://test.example.com",
                    "endpoint_pattern": "single",
                    "authentication": {
                        "required": False
                    },
                    "capabilities": {
                        "batch_processing": True,
                        "streaming": False
                    },
                    "metadata": {
                        "maintainer": "dev@example.com",
                        "documentation_url": "https://docs.example.com"
                    },
                    "variants": {
                        "test_variant": {
                            "variant_id": "test_variant",
                            "display_name": "Test Variant",
                            "description": "Test description",
                            "status": "production",
                            "endpoint": "/generate",
                            "layout_id": "L01",
                            "classification": {
                                "priority": 3,
                                "keywords": ["one", "two", "three", "four", "five"]
                            },
                            "llm_guidance": {
                                "use_cases": ["Use case"],
                                "best_for": "Testing",
                                "avoid_when": "Production"
                            },
                            "parameters": {
                                "required_fields": ["field1"],
                                "optional_fields": ["field2"],
                                "output_format": "html"
                            }
                        }
                    }
                }
            }
        }

        exporter = create_exporter_from_registry(registry_data, "test_service")

        assert exporter.metadata.service_name == "test_service"
        assert exporter.metadata.service_version == "2.0.0"
        assert exporter.get_variant_count() == 1
        assert exporter.metadata.supports_batch is True
        assert exporter.metadata.maintainer == "dev@example.com"

        # Verify variant was added correctly
        variant = exporter.metadata.variants[0]
        assert variant.variant_id == "test_variant"
        assert variant.priority == 3
        assert len(variant.keywords) == 5

    def test_roundtrip_export_and_import(self):
        """Test exporting and re-importing produces same data"""
        # Create original exporter
        original = ServiceMetadataExporter(
            service_name="roundtrip_test",
            service_version="1.5.0",
            service_type="llm_generated",
            base_url="https://roundtrip.example.com",
            supports_batch=True,
            maintainer="test@example.com"
        )

        original.add_variant(
            variant_id="variant1",
            display_name="Variant 1",
            description="First variant",
            endpoint="/v1",
            keywords=["a", "b", "c", "d", "e"],
            priority=2,
            layout_id="L10",
            use_cases=["Case 1"],
            best_for="Testing roundtrips"
        )

        # Export to registry format
        registry_data = {"services": original.export_to_registry_format()}

        # Re-import
        reimported = create_exporter_from_registry(registry_data, "roundtrip_test")

        # Verify same data
        assert reimported.metadata.service_name == original.metadata.service_name
        assert reimported.metadata.service_version == original.metadata.service_version
        assert reimported.get_variant_count() == original.get_variant_count()
        assert reimported.metadata.supports_batch == original.metadata.supports_batch

        # Verify variant details
        original_variant = original.metadata.variants[0]
        reimported_variant = reimported.metadata.variants[0]

        assert reimported_variant.variant_id == original_variant.variant_id
        assert reimported_variant.priority == original_variant.priority
        assert reimported_variant.keywords == original_variant.keywords


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_exporter_with_no_variants(self):
        """Test exporter with no variants added"""
        exporter = ServiceMetadataExporter(
            service_name="empty_service",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://empty.example.com"
        )

        assert exporter.get_variant_count() == 0
        assert exporter.get_keyword_count() == 0

        stats = exporter.get_stats()
        assert stats["variant_count"] == 0
        assert stats["avg_keywords_per_variant"] == 0

    def test_variant_with_many_keywords(self):
        """Test variant with large number of keywords"""
        exporter = ServiceMetadataExporter(
            service_name="many_keywords",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        # Add variant with 50 keywords
        keywords = [f"keyword{i}" for i in range(50)]

        exporter.add_variant(
            variant_id="keyword_heavy",
            display_name="Keyword Heavy",
            description="Variant with many keywords",
            endpoint="/test",
            keywords=keywords
        )

        assert exporter.get_keyword_count() == 50

    def test_variant_priority_boundaries(self):
        """Test variant priority at boundaries (1 and 10)"""
        exporter = ServiceMetadataExporter(
            service_name="priority_test",
            service_version="1.0.0",
            service_type="template_based",
            base_url="https://test.example.com"
        )

        exporter.add_variant(
            variant_id="highest",
            display_name="Highest Priority",
            description="Priority 1",
            endpoint="/high",
            keywords=["a", "b", "c", "d", "e"],
            priority=1
        ).add_variant(
            variant_id="lowest",
            display_name="Lowest Priority",
            description="Priority 10",
            endpoint="/low",
            keywords=["f", "g", "h", "i", "j"],
            priority=10
        )

        stats = exporter.get_stats()
        assert 1 in stats["priority_distribution"]
        assert 10 in stats["priority_distribution"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
