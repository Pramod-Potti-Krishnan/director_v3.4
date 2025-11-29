"""
Unit Tests for Unified Variant Registry Loading

Tests the Pydantic models and registry loading functionality.
Ensures registry JSON validates correctly and models work as expected.

Version: 2.0.0
Created: 2025-11-29
"""

import pytest
import json
from pathlib import Path
from pydantic import ValidationError

from src.models.variant_registry import (
    UnifiedVariantRegistry,
    ServiceConfig,
    VariantConfig,
    Classification,
    ServiceType,
    EndpointPattern,
    VariantStatus,
    load_registry_from_file,
    validate_registry_json,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry_path():
    """Path to the actual registry JSON file"""
    return Path(__file__).parent.parent / "config" / "unified_variant_registry.json"


@pytest.fixture
def sample_registry_data():
    """Sample registry data for testing"""
    return {
        "version": "2.0.0",
        "last_updated": "2025-11-29",
        "total_services": 1,
        "total_variants": 1,
        "services": {
            "test_service_v1.0": {
                "enabled": True,
                "base_url": "http://localhost:8000",
                "service_type": "llm_generated",
                "endpoint_pattern": "per_variant",
                "timeout": 60,
                "variants": {
                    "test_variant": {
                        "variant_id": "test_variant",
                        "display_name": "Test Variant",
                        "description": "A test variant",
                        "status": "production",
                        "layout_id": "L25",
                        "endpoint": "/v1.0/test/generate",
                        "classification": {
                            "priority": 5,
                            "keywords": ["test", "sample", "demo", "example", "mock"]
                        }
                    }
                }
            }
        }
    }


# ============================================================================
# Registry Loading Tests
# ============================================================================

class TestRegistryLoading:
    """Test loading and parsing registry files"""

    def test_load_actual_registry(self, registry_path):
        """Test loading the actual registry JSON file"""
        assert registry_path.exists(), f"Registry file not found: {registry_path}"

        registry = load_registry_from_file(str(registry_path))

        assert isinstance(registry, UnifiedVariantRegistry)
        assert registry.version == "2.0.0"
        assert registry.total_services == 3
        assert registry.total_variants == 56  # May be 7 if only samples exist

    def test_load_sample_registry(self, sample_registry_data):
        """Test loading sample registry data"""
        registry = UnifiedVariantRegistry.model_validate(sample_registry_data)

        assert registry.version == "2.0.0"
        assert registry.total_services == 1
        assert len(registry.services) == 1
        assert "test_service_v1.0" in registry.services

    def test_registry_validation_success(self, sample_registry_data):
        """Test successful registry validation"""
        json_str = json.dumps(sample_registry_data)
        is_valid, error = validate_registry_json(json_str)

        assert is_valid
        assert error is None

    def test_registry_validation_failure(self):
        """Test registry validation with invalid data"""
        invalid_data = {
            "version": "2.0.0",
            # Missing required fields
        }
        json_str = json.dumps(invalid_data)
        is_valid, error = validate_registry_json(json_str)

        assert not is_valid
        assert error is not None

    def test_invalid_service_name_format(self, sample_registry_data):
        """Test that invalid service names are rejected"""
        invalid_data = sample_registry_data.copy()
        invalid_data["services"] = {
            "InvalidServiceName": {  # Should be lowercase_v1.0 format
                "enabled": True,
                "base_url": "http://localhost:8000",
                "service_type": "llm_generated",
                "endpoint_pattern": "per_variant",
                "variants": {
                    "test": {
                        "variant_id": "test",
                        "display_name": "Test",
                        "classification": {
                            "priority": 5,
                            "keywords": ["test", "demo", "sample", "example", "mock"]
                        }
                    }
                }
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            UnifiedVariantRegistry.model_validate(invalid_data)

        error_str = str(exc_info.value)
        # The error should be about the service name pattern
        assert "must match pattern" in error_str or "Service name" in error_str


# ============================================================================
# Service Configuration Tests
# ============================================================================

class TestServiceConfig:
    """Test ServiceConfig model validation"""

    def test_service_with_single_endpoint_pattern(self):
        """Test service with single endpoint pattern"""
        service_data = {
            "enabled": True,
            "base_url": "http://localhost:8001",
            "service_type": "template_based",
            "endpoint_pattern": "single",
            "default_endpoint": "/v1.2/generate",
            "variants": {
                "test": {
                    "variant_id": "test",
                    "display_name": "Test",
                    "classification": {
                        "priority": 5,
                        "keywords": ["test", "demo", "sample", "example", "mock"]
                    }
                }
            }
        }

        service = ServiceConfig.model_validate(service_data)
        assert service.endpoint_pattern == EndpointPattern.SINGLE
        assert service.default_endpoint == "/v1.2/generate"

    def test_service_with_per_variant_pattern(self):
        """Test service with per_variant endpoint pattern"""
        service_data = {
            "enabled": True,
            "base_url": "http://localhost:8000",
            "service_type": "llm_generated",
            "endpoint_pattern": "per_variant",
            "variants": {
                "pyramid": {
                    "variant_id": "pyramid",
                    "display_name": "Pyramid",
                    "endpoint": "/v1.0/pyramid/generate",
                    "classification": {
                        "priority": 4,
                        "keywords": ["pyramid", "hierarchical", "hierarchy", "levels", "tiers"]
                    }
                }
            }
        }

        service = ServiceConfig.model_validate(service_data)
        assert service.endpoint_pattern == EndpointPattern.PER_VARIANT
        assert service.variants["pyramid"].endpoint == "/v1.0/pyramid/generate"

    def test_service_with_typed_pattern(self):
        """Test service with typed endpoint pattern"""
        service_data = {
            "enabled": True,
            "base_url": "http://localhost:8006",
            "service_type": "data_visualization",
            "endpoint_pattern": "typed",
            "endpoints": {
                "chartjs": "/analytics/v3/chartjs/generate",
                "d3": "/analytics/v3/d3/generate"
            },
            "variants": {
                "pie_chart": {
                    "variant_id": "pie_chart",
                    "display_name": "Pie Chart",
                    "classification": {
                        "priority": 2,
                        "keywords": ["pie", "chart", "proportion", "percentage", "share"]
                    }
                }
            }
        }

        service = ServiceConfig.model_validate(service_data)
        assert service.endpoint_pattern == EndpointPattern.TYPED
        assert "chartjs" in service.endpoints
        assert "d3" in service.endpoints

    def test_single_pattern_requires_default_endpoint(self):
        """Test that single pattern requires default_endpoint"""
        service_data = {
            "enabled": True,
            "base_url": "http://localhost:8001",
            "service_type": "template_based",
            "endpoint_pattern": "single",
            # Missing default_endpoint
            "variants": {
                "test": {
                    "variant_id": "test",
                    "display_name": "Test",
                    "classification": {
                        "priority": 5,
                        "keywords": ["test", "demo", "sample", "example", "mock"]
                    }
                }
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            ServiceConfig.model_validate(service_data)

        assert "default_endpoint required" in str(exc_info.value)

    def test_typed_pattern_requires_endpoints(self):
        """Test that typed pattern requires endpoints dict"""
        service_data = {
            "enabled": True,
            "base_url": "http://localhost:8006",
            "service_type": "data_visualization",
            "endpoint_pattern": "typed",
            # Missing endpoints
            "variants": {
                "test": {
                    "variant_id": "test",
                    "display_name": "Test",
                    "classification": {
                        "priority": 5,
                        "keywords": ["test", "demo", "sample", "example", "mock"]
                    }
                }
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            ServiceConfig.model_validate(service_data)

        assert "endpoints required" in str(exc_info.value)


# ============================================================================
# Variant Configuration Tests
# ============================================================================

class TestVariantConfig:
    """Test VariantConfig model validation"""

    def test_valid_variant_id_format(self):
        """Test that variant_id accepts valid snake_case"""
        variant_data = {
            "variant_id": "valid_variant_name",
            "display_name": "Valid Variant",
            "classification": {
                "priority": 5,
                "keywords": ["test", "valid", "sample", "example", "demo"]
            }
        }

        variant = VariantConfig.model_validate(variant_data)
        assert variant.variant_id == "valid_variant_name"

    def test_invalid_variant_id_format(self):
        """Test that variant_id rejects invalid formats"""
        invalid_ids = [
            "InvalidCamelCase",
            "invalid-kebab-case",
            "invalid.dot.case",
            "invalid space",
            "123numeric",
        ]

        for invalid_id in invalid_ids:
            variant_data = {
                "variant_id": invalid_id,
                "display_name": "Test",
                "classification": {
                    "priority": 5,
                    "keywords": ["test", "demo", "sample", "example", "mock"]
                }
            }

            with pytest.raises(ValidationError):
                VariantConfig.model_validate(variant_data)

    def test_valid_layout_id_format(self):
        """Test that layout_id accepts valid format"""
        variant_data = {
            "variant_id": "test",
            "display_name": "Test",
            "layout_id": "L25",
            "classification": {
                "priority": 5,
                "keywords": ["test", "demo", "sample", "example", "mock"]
            }
        }

        variant = VariantConfig.model_validate(variant_data)
        assert variant.layout_id == "L25"

    def test_invalid_layout_id_format(self):
        """Test that layout_id rejects invalid formats"""
        variant_data = {
            "variant_id": "test",
            "display_name": "Test",
            "layout_id": "25",  # Missing 'L' prefix
            "classification": {
                "priority": 5,
                "keywords": ["test", "demo", "sample", "example", "mock"]
            }
        }

        with pytest.raises(ValidationError):
            VariantConfig.model_validate(variant_data)


# ============================================================================
# Classification Tests
# ============================================================================

class TestClassification:
    """Test Classification model validation"""

    def test_valid_classification(self):
        """Test valid classification with sufficient keywords"""
        classification_data = {
            "priority": 5,
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
        }

        classification = Classification.model_validate(classification_data)
        assert classification.priority == 5
        assert len(classification.keywords) == 5

    def test_priority_range_validation(self):
        """Test priority must be between 1 and 100"""
        # Valid priorities
        for priority in [1, 50, 100]:
            data = {
                "priority": priority,
                "keywords": ["k1", "k2", "k3", "k4", "k5"]
            }
            classification = Classification.model_validate(data)
            assert classification.priority == priority

        # Invalid priorities
        for priority in [0, -1, 101, 200]:
            data = {
                "priority": priority,
                "keywords": ["k1", "k2", "k3", "k4", "k5"]
            }
            with pytest.raises(ValidationError):
                Classification.model_validate(data)

    def test_minimum_keywords_required(self):
        """Test that at least 5 keywords are required"""
        # Too few keywords
        data = {
            "priority": 5,
            "keywords": ["k1", "k2", "k3", "k4"]  # Only 4
        }
        with pytest.raises(ValidationError):
            Classification.model_validate(data)

    def test_duplicate_keywords_rejected(self):
        """Test that duplicate keywords are rejected"""
        data = {
            "priority": 5,
            "keywords": ["duplicate", "duplicate", "k3", "k4", "k5"]
        }
        with pytest.raises(ValidationError) as exc_info:
            Classification.model_validate(data)

        assert "must be unique" in str(exc_info.value)

    def test_empty_keywords_rejected(self):
        """Test that empty string keywords are rejected"""
        data = {
            "priority": 5,
            "keywords": ["k1", "k2", "", "k4", "k5"]
        }
        with pytest.raises(ValidationError):
            Classification.model_validate(data)


# ============================================================================
# Registry Helper Methods Tests
# ============================================================================

class TestRegistryHelperMethods:
    """Test UnifiedVariantRegistry helper methods"""

    def test_get_variant(self, sample_registry_data):
        """Test get_variant method"""
        registry = UnifiedVariantRegistry.model_validate(sample_registry_data)

        variant = registry.get_variant("test_service_v1.0", "test_variant")
        assert variant is not None
        assert variant.variant_id == "test_variant"

        # Non-existent variant
        variant = registry.get_variant("test_service_v1.0", "nonexistent")
        assert variant is None

        # Non-existent service
        variant = registry.get_variant("nonexistent_service_v1.0", "test_variant")
        assert variant is None

    def test_get_all_variants(self, sample_registry_data):
        """Test get_all_variants method"""
        registry = UnifiedVariantRegistry.model_validate(sample_registry_data)

        all_variants = registry.get_all_variants()
        assert len(all_variants) == 1
        assert "test_service_v1.0.test_variant" in all_variants

    def test_get_variants_by_priority(self, registry_path):
        """Test get_variants_by_priority returns sorted variants"""
        registry = load_registry_from_file(str(registry_path))

        sorted_variants = registry.get_variants_by_priority()

        # Verify sorted by priority (ascending)
        priorities = [variant.classification.priority for _, _, variant in sorted_variants]
        assert priorities == sorted(priorities), "Variants should be sorted by priority"

        # Verify we have variants from all services
        service_names = set(service_name for service_name, _, _ in sorted_variants)
        assert len(service_names) > 0, "Should have variants from at least one service"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests with actual registry file"""

    def test_registry_has_all_required_services(self, registry_path):
        """Test that registry includes all expected services"""
        registry = load_registry_from_file(str(registry_path))

        expected_services = [
            "illustrator_service_v1.0",
            "text_service_v1.2",
            "analytics_service_v3"
        ]

        for service_name in expected_services:
            assert service_name in registry.services, f"Missing service: {service_name}"

    def test_illustrator_variants_have_parameters(self, registry_path):
        """Test that illustrator variants have required parameters"""
        registry = load_registry_from_file(str(registry_path))

        illustrator_service = registry.services.get("illustrator_service_v1.0")
        if not illustrator_service:
            pytest.skip("Illustrator service not in registry")

        for variant_id, variant in illustrator_service.variants.items():
            assert variant.parameters is not None, \
                f"Illustrator variant '{variant_id}' missing parameters"
            assert variant.parameters.count_field is not None
            assert variant.parameters.count_range is not None
            assert variant.parameters.optimal_count is not None

    def test_analytics_variants_have_data_requirements(self, registry_path):
        """Test that analytics variants have data requirements"""
        registry = load_registry_from_file(str(registry_path))

        analytics_service = registry.services.get("analytics_service_v3")
        if not analytics_service:
            pytest.skip("Analytics service not in registry")

        for variant_id, variant in analytics_service.variants.items():
            assert variant.data_requirements is not None, \
                f"Analytics variant '{variant_id}' missing data_requirements"
            assert variant.data_requirements.structure is not None
            assert variant.data_requirements.min_items >= 1
            assert variant.data_requirements.max_items >= variant.data_requirements.min_items

    def test_all_variants_have_classification(self, registry_path):
        """Test that all variants have valid classification"""
        registry = load_registry_from_file(str(registry_path))

        for service_name, service_config in registry.services.items():
            for variant_id, variant in service_config.variants.items():
                assert variant.classification is not None, \
                    f"Variant '{service_name}.{variant_id}' missing classification"
                assert variant.classification.priority >= 1
                assert len(variant.classification.keywords) >= 5, \
                    f"Variant '{service_name}.{variant_id}' has too few keywords"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
