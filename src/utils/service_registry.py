"""
Service Registry for Director v3.4
===================================

Maps slide type classifications to Text Service v1.1 specialized endpoints.
Provides centralized endpoint configuration for the 13-type taxonomy.
"""

from typing import Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ServiceRegistry:
    """
    Registry mapping slide types to Text Service v1.1 specialized endpoints.

    13 Slide Types → 15 Endpoints:
    - 3 Hero endpoints (L29)
    - 10 Content endpoints (L25)
    - 1 Legacy table endpoint (backward compatibility)
    - 1 Batch endpoint (parallel processing)
    """

    # Hero slide endpoints (L29)
    HERO_ENDPOINTS = {
        "title_slide": "/api/v1/generate/hero/title",
        "section_divider": "/api/v1/generate/hero/section",
        "closing_slide": "/api/v1/generate/hero/closing"
    }

    # Content slide endpoints (L25)
    CONTENT_ENDPOINTS = {
        "bilateral_comparison": "/api/v1/generate/content/bilateral",
        "sequential_3col": "/api/v1/generate/content/sequential",
        "impact_quote": "/api/v1/generate/content/quote",
        "metrics_grid": "/api/v1/generate/content/metrics",
        "matrix_2x2": "/api/v1/generate/content/matrix",
        "grid_3x3": "/api/v1/generate/content/grid",
        "asymmetric_8_4": "/api/v1/generate/content/asymmetric",
        "hybrid_1_2x2": "/api/v1/generate/content/hybrid",
        "single_column": "/api/v1/generate/content/single",
        "styled_table": "/api/v1/generate/content/table"
    }

    # Special endpoints
    BATCH_ENDPOINT = "/api/v1/generate/batch"
    LEGACY_TABLE_ENDPOINT = "/api/v1/generate/table"  # v1.0 compatibility

    # Combined registry
    ALL_ENDPOINTS = {**HERO_ENDPOINTS, **CONTENT_ENDPOINTS}

    @classmethod
    def get_endpoint(cls, slide_type_classification: str) -> Optional[str]:
        """
        Get specialized endpoint for a slide type.

        Args:
            slide_type_classification: Slide type from 13-type taxonomy

        Returns:
            Endpoint path (e.g., "/api/v1/generate/hero/title")
            None if slide_type not recognized
        """
        endpoint = cls.ALL_ENDPOINTS.get(slide_type_classification)

        if endpoint:
            logger.debug(f"Mapped '{slide_type_classification}' → {endpoint}")
        else:
            logger.warning(f"Unknown slide_type_classification: '{slide_type_classification}'")
            logger.warning(f"Valid types: {list(cls.ALL_ENDPOINTS.keys())}")

        return endpoint

    @classmethod
    def get_batch_endpoint(cls) -> str:
        """Get batch processing endpoint for parallel generation."""
        return cls.BATCH_ENDPOINT

    @classmethod
    def is_hero_type(cls, slide_type_classification: str) -> bool:
        """Check if slide type is a hero type (L29)."""
        return slide_type_classification in cls.HERO_ENDPOINTS

    @classmethod
    def is_content_type(cls, slide_type_classification: str) -> bool:
        """Check if slide type is a content type (L25)."""
        return slide_type_classification in cls.CONTENT_ENDPOINTS

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of all supported slide types."""
        return list(cls.ALL_ENDPOINTS.keys())

    @classmethod
    def get_endpoint_category(cls, slide_type_classification: str) -> Optional[str]:
        """
        Get endpoint category for a slide type.

        Returns:
            "hero", "content", or None if unknown
        """
        if slide_type_classification in cls.HERO_ENDPOINTS:
            return "hero"
        elif slide_type_classification in cls.CONTENT_ENDPOINTS:
            return "content"
        else:
            return None

    @classmethod
    def validate_slide_types(cls, slide_types: list[str]) -> Dict[str, any]:
        """
        Validate a list of slide types against the registry.

        Args:
            slide_types: List of slide_type_classification strings

        Returns:
            Validation result dict with:
            - valid: bool
            - valid_count: int
            - invalid_count: int
            - invalid_types: list[str]
        """
        valid_types = []
        invalid_types = []

        for slide_type in slide_types:
            if slide_type in cls.ALL_ENDPOINTS:
                valid_types.append(slide_type)
            else:
                invalid_types.append(slide_type)

        result = {
            "valid": len(invalid_types) == 0,
            "valid_count": len(valid_types),
            "invalid_count": len(invalid_types),
            "invalid_types": invalid_types
        }

        if invalid_types:
            logger.warning(
                f"Validation failed: {len(invalid_types)} invalid types: {invalid_types}"
            )
        else:
            logger.debug(f"Validation passed: All {len(valid_types)} types are valid")

        return result


# Convenience functions

def get_endpoint_for_slide_type(slide_type: str) -> Optional[str]:
    """Get endpoint for a slide type (convenience function)."""
    return ServiceRegistry.get_endpoint(slide_type)


def get_batch_endpoint() -> str:
    """Get batch endpoint (convenience function)."""
    return ServiceRegistry.get_batch_endpoint()


# Example usage
if __name__ == "__main__":
    print("Service Registry - Text Service v1.1 Endpoint Mapping")
    print("=" * 70)

    print("\nHero Endpoints (L29):")
    for slide_type, endpoint in ServiceRegistry.HERO_ENDPOINTS.items():
        print(f"  {slide_type:25s} → {endpoint}")

    print("\nContent Endpoints (L25):")
    for slide_type, endpoint in ServiceRegistry.CONTENT_ENDPOINTS.items():
        print(f"  {slide_type:25s} → {endpoint}")

    print("\nSpecial Endpoints:")
    print(f"  Batch Processing: {ServiceRegistry.BATCH_ENDPOINT}")
    print(f"  Legacy Table: {ServiceRegistry.LEGACY_TABLE_ENDPOINT}")

    print("\n" + "=" * 70)
    print(f"Total Specialized Endpoints: {len(ServiceRegistry.ALL_ENDPOINTS)}")

    # Test validation
    print("\nValidation Test:")
    test_types = ["title_slide", "bilateral_comparison", "invalid_type", "matrix_2x2"]
    validation = ServiceRegistry.validate_slide_types(test_types)
    print(f"  Valid: {validation['valid']}")
    print(f"  Valid count: {validation['valid_count']}")
    print(f"  Invalid types: {validation['invalid_types']}")
