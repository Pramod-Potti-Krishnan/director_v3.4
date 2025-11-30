"""
Tests for Variant Validator

Comprehensive tests for variant validation utilities.

Version: 1.0.0
Created: 2025-11-29
"""

import pytest
from src.utils.variant_validator import (
    VariantValidator,
    ValidationResult,
    validate_variant,
    validate_service
)


class TestValidationResult:
    """Test ValidationResult model"""

    def test_create_valid_result(self):
        """Test creating a valid result"""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self):
        """Test adding errors"""
        result = ValidationResult(valid=True)

        result.add_error("Test error")

        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding warnings"""
        result = ValidationResult(valid=True)

        result.add_warning("Test warning")

        assert result.valid is True  # Warnings don't invalidate
        assert "Test warning" in result.warnings

    def test_add_suggestion(self):
        """Test adding suggestions"""
        result = ValidationResult(valid=True)

        result.add_suggestion("Test suggestion")

        assert result.valid is True
        assert "Test suggestion" in result.suggestions

    def test_get_summary_valid(self):
        """Test summary for valid result"""
        result = ValidationResult(valid=True)

        summary = result.get_summary()

        assert "✅ Validation PASSED" in summary

    def test_get_summary_with_errors(self):
        """Test summary with errors"""
        result = ValidationResult(valid=True)
        result.add_error("Error 1")
        result.add_error("Error 2")

        summary = result.get_summary()

        assert "❌ Validation FAILED" in summary
        assert "Error 1" in summary
        assert "Error 2" in summary


class TestVariantValidation:
    """Test variant validation"""

    def test_valid_minimal_variant(self):
        """Test validating a minimal valid variant"""
        validator = VariantValidator()

        variant = {
            "variant_id": "pie_chart",
            "display_name": "Pie Chart",
            "description": "Circular chart showing proportional data",
            "endpoint": "/v3/charts/pie",
            "classification": {
                "keywords": ["pie", "donut", "chart", "percentage", "proportion"]
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_valid_complete_variant(self):
        """Test validating a complete valid variant"""
        validator = VariantValidator()

        variant = {
            "variant_id": "bar_chart",
            "display_name": "Bar Chart",
            "description": "Vertical or horizontal bar chart for comparing data",
            "endpoint": "/v3/charts/bar",
            "status": "production",
            "layout_id": "L02",
            "classification": {
                "keywords": ["bar", "column", "chart", "comparison", "vertical"],
                "priority": 2
            },
            "llm_guidance": {
                "use_cases": ["Sales comparison", "Year-over-year analysis"],
                "best_for": "Comparing discrete categories",
                "avoid_when": "Too many categories (>15)"
            },
            "parameters": {
                "required_fields": ["data", "title"],
                "optional_fields": ["orientation", "colors"],
                "output_format": "html"
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is True

    def test_missing_required_fields(self):
        """Test validation fails when required fields missing"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test"
            # Missing: display_name, description, endpoint
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("display_name" in error for error in result.errors)
        assert any("description" in error for error in result.errors)
        assert any("endpoint" in error for error in result.errors)

    def test_invalid_variant_id_format(self):
        """Test validation fails for invalid variant_id format"""
        validator = VariantValidator()

        # CamelCase (should be snake_case)
        variant = {
            "variant_id": "PieChart",
            "display_name": "Pie Chart",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("snake_case" in error.lower() for error in result.errors)

    def test_variant_id_too_short(self):
        """Test validation fails for very short variant_id"""
        validator = VariantValidator()

        variant = {
            "variant_id": "ab",  # Only 2 characters
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("at least 3 characters" in error for error in result.errors)

    def test_invalid_endpoint_no_slash(self):
        """Test validation fails when endpoint doesn't start with /"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "v3/charts/test",  # Missing leading /
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("start with '/'" in error for error in result.errors)

    def test_insufficient_keywords(self):
        """Test validation fails with too few keywords"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["one", "two", "three"]  # Only 3 keywords
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("at least 5" in error for error in result.errors)

    def test_invalid_priority(self):
        """Test validation fails for invalid priority"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"],
                "priority": 15  # Invalid (must be 1-10)
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("between 1 and 10" in error for error in result.errors)

    def test_invalid_status(self):
        """Test validation fails for invalid status"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "status": "invalid_status",  # Not in valid statuses
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is False
        assert any("production" in error or "beta" in error for error in result.errors)

    def test_duplicate_keywords_warning(self):
        """Test warning for duplicate keywords"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["pie", "chart", "pie", "donut", "percentage"]  # "pie" duplicated
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is True  # Still valid
        assert any("duplicate" in warning.lower() for warning in result.warnings)

    def test_short_description_warning(self):
        """Test warning for very short description"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Short",  # Very short
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is True
        assert any("very short" in warning.lower() for warning in result.warnings)


class TestServiceValidation:
    """Test service validation"""

    def test_valid_minimal_service(self):
        """Test validating a minimal valid service"""
        validator = VariantValidator()

        service = {
            "service_name": "test_service_v1",
            "base_url": "https://test.example.com",
            "variants": {
                "test_variant": {
                    "variant_id": "test_variant",
                    "display_name": "Test Variant",
                    "description": "Test description",
                    "endpoint": "/test",
                    "classification": {
                        "keywords": ["a", "b", "c", "d", "e"]
                    }
                }
            }
        }

        result = validator.validate_service(service)

        assert result.valid is True

    def test_missing_service_fields(self):
        """Test validation fails when service fields missing"""
        validator = VariantValidator()

        service = {
            "service_name": "test_service"
            # Missing: base_url, variants
        }

        result = validator.validate_service(service)

        assert result.valid is False
        assert any("base_url" in error for error in result.errors)
        assert any("variants" in error for error in result.errors)

    def test_invalid_base_url(self):
        """Test validation fails for invalid base_url"""
        validator = VariantValidator()

        service = {
            "service_name": "test_service_v1",
            "base_url": "ftp://test.example.com",  # Wrong protocol
            "variants": {}
        }

        result = validator.validate_service(service)

        assert result.valid is False
        assert any("http://" in error or "https://" in error for error in result.errors)

    def test_invalid_endpoint_pattern(self):
        """Test validation fails for invalid endpoint_pattern"""
        validator = VariantValidator()

        service = {
            "service_name": "test_service_v1",
            "base_url": "https://test.example.com",
            "endpoint_pattern": "invalid_pattern",  # Not a valid pattern
            "variants": {}
        }

        result = validator.validate_service(service)

        assert result.valid is False
        assert any("endpoint_pattern" in error for error in result.errors)

    def test_service_validates_all_variants(self):
        """Test service validation checks all variants"""
        validator = VariantValidator()

        service = {
            "service_name": "test_service_v1",
            "base_url": "https://test.example.com",
            "variants": {
                "valid_variant": {
                    "variant_id": "valid_variant",
                    "display_name": "Valid",
                    "description": "Valid description",
                    "endpoint": "/valid",
                    "classification": {
                        "keywords": ["a", "b", "c", "d", "e"]
                    }
                },
                "invalid_variant": {
                    "variant_id": "invalid_variant",
                    "display_name": "Invalid",
                    "description": "Invalid",
                    "endpoint": "/invalid",
                    "classification": {
                        "keywords": ["x", "y"]  # Too few keywords
                    }
                }
            }
        }

        result = validator.validate_service(service)

        assert result.valid is False
        assert any("invalid_variant" in error for error in result.errors)

    def test_duplicate_keywords_across_variants(self):
        """Test warning for duplicate keywords across variants"""
        validator = VariantValidator()

        service = {
            "service_name": "test_service_v1",
            "base_url": "https://test.example.com",
            "variants": {
                "variant1": {
                    "variant_id": "variant1",
                    "display_name": "Variant 1",
                    "description": "First variant",
                    "endpoint": "/v1",
                    "classification": {
                        "keywords": ["pie", "chart", "circular", "donut", "percentage"]
                    }
                },
                "variant2": {
                    "variant_id": "variant2",
                    "display_name": "Variant 2",
                    "description": "Second variant",
                    "endpoint": "/v2",
                    "classification": {
                        "keywords": ["bar", "chart", "column", "vertical", "horizontal"]
                        # "chart" is duplicated
                    }
                }
            }
        }

        result = validator.validate_service(service)

        assert result.valid is True  # Still valid
        assert any("chart" in warning.lower() for warning in result.warnings)


class TestStrictMode:
    """Test strict mode validation"""

    def test_strict_mode_converts_warnings_to_errors(self):
        """Test that strict mode treats warnings as errors"""
        validator = VariantValidator(strict=True)

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Short",  # Will generate warning
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        # In strict mode, warnings become errors
        assert result.valid is False
        assert any("STRICT MODE" in error for error in result.errors)

    def test_non_strict_mode_allows_warnings(self):
        """Test that non-strict mode allows warnings"""
        validator = VariantValidator(strict=False)

        variant = {
            "variant_id": "test_chart",
            "display_name": "Test",
            "description": "Short",  # Will generate warning
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validator.validate_variant(variant)

        # In non-strict mode, warnings don't invalidate
        assert result.valid is True
        assert len(result.warnings) > 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_validate_variant_function(self):
        """Test validate_variant convenience function"""
        variant = {
            "variant_id": "test",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validate_variant(variant)

        assert result.valid is True

    def test_validate_service_function(self):
        """Test validate_service convenience function"""
        service = {
            "service_name": "test_service_v1",
            "base_url": "https://test.example.com",
            "variants": {
                "test": {
                    "variant_id": "test",
                    "display_name": "Test",
                    "description": "Test description",
                    "endpoint": "/test",
                    "classification": {
                        "keywords": ["a", "b", "c", "d", "e"]
                    }
                }
            }
        }

        result = validate_service(service)

        assert result.valid is True

    def test_convenience_function_with_strict_mode(self):
        """Test convenience functions with strict mode"""
        variant = {
            "variant_id": "test",
            "display_name": "Test",
            "description": "Short",  # Warning
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            }
        }

        result = validate_variant(variant, strict=True)

        assert result.valid is False  # Strict mode converts warnings to errors


class TestSuggestions:
    """Test validation suggestions"""

    def test_suggestions_for_llm_guidance(self):
        """Test suggestions for missing LLM guidance"""
        validator = VariantValidator()

        variant = {
            "variant_id": "test",
            "display_name": "Test",
            "description": "Test description",
            "endpoint": "/test",
            "classification": {
                "keywords": ["a", "b", "c", "d", "e"]
            },
            "llm_guidance": {
                # Missing best_for and avoid_when
            }
        }

        result = validator.validate_variant(variant)

        assert result.valid is True
        assert any("best_for" in suggestion for suggestion in result.suggestions)
        assert any("avoid_when" in suggestion for suggestion in result.suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
