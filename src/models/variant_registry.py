"""
Unified Variant Registry - Pydantic Models

Provides type-safe models for loading and validating the unified variant registry
configuration. Supports all content generation services (Text, Illustrator, Analytics).

Version: 2.0.0
Created: 2025-11-29
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import date


# ============================================================================
# Enums for Type Safety
# ============================================================================

class ServiceType(str, Enum):
    """Type of content generation service"""
    TEMPLATE_BASED = "template_based"        # Text/Table Service
    LLM_GENERATED = "llm_generated"          # Illustrator Service
    DATA_VISUALIZATION = "data_visualization" # Analytics Service


class EndpointPattern(str, Enum):
    """How service endpoints are structured"""
    SINGLE = "single"          # One endpoint, variant_id in request body
    PER_VARIANT = "per_variant"  # Dedicated endpoint per variant
    TYPED = "typed"            # Multiple endpoints by type (chartjs, d3)


class VariantStatus(str, Enum):
    """Variant availability status"""
    PRODUCTION = "production"
    BETA = "beta"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class DataStructure(str, Enum):
    """Data structure types for analytics variants"""
    LABEL_VALUE_PAIRS = "label_value_pairs"
    TIME_SERIES = "time_series"
    MULTI_SERIES = "multi_series"
    HIERARCHICAL = "hierarchical"
    NETWORK = "network"


class ValueType(str, Enum):
    """Value types for analytics data"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    MIXED = "mixed"


# ============================================================================
# Classification Models
# ============================================================================

class Classification(BaseModel):
    """
    Slide type classification configuration for LLM-based selection.

    Used in Stage 4 (Generate Strawman) to classify slides based on
    content analysis and keyword matching.
    """
    priority: int = Field(
        ge=1,
        le=100,
        description="Classification priority (lower = higher priority)"
    )
    keywords: List[str] = Field(
        min_length=5,
        max_length=200,
        description="Keywords for slide classification and matching"
    )

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Ensure keywords are non-empty and unique"""
        if not v:
            raise ValueError("Keywords list cannot be empty")

        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Keywords must be unique")

        # Ensure all keywords are non-empty strings
        for keyword in v:
            if not keyword or not keyword.strip():
                raise ValueError("Keywords cannot be empty strings")

        return v


# ============================================================================
# LLM Guidance Models
# ============================================================================

class LLMGuidanceExample(BaseModel):
    """Example for LLM guidance documentation"""
    title: str
    key_points: List[str]


class LLMGuidance(BaseModel):
    """
    Guidance for LLM when selecting and using variants.

    Embedded in Stage 4 prompt to help LLM make appropriate
    variant selections based on content context.
    """
    use_cases: List[str] = Field(
        min_length=1,
        description="When to use this variant"
    )
    best_for: Optional[str] = Field(
        None,
        description="What this variant excels at"
    )
    avoid_when: Optional[str] = Field(
        None,
        description="When NOT to use this variant"
    )
    examples: Optional[List[LLMGuidanceExample]] = Field(
        None,
        description="Example use cases with sample content"
    )


# ============================================================================
# Illustrator-Specific Models
# ============================================================================

class CountRange(BaseModel):
    """Valid range for element counts (levels, stages, circles, etc.)"""
    min: int = Field(ge=1)
    max: int = Field(ge=1)

    @field_validator('max')
    @classmethod
    def validate_max_greater_than_min(cls, v: int, info) -> int:
        """Ensure max >= min"""
        if 'min' in info.data and v < info.data['min']:
            raise ValueError(f"max ({v}) must be >= min ({info.data['min']})")
        return v


class IllustratorParameters(BaseModel):
    """
    Parameters specific to Illustrator service variants.

    Defines element count constraints and naming conventions
    for LLM-generated illustrations.
    """
    count_field: str = Field(
        description="Field name for element count (e.g., 'num_levels', 'num_stages')"
    )
    count_range: CountRange = Field(
        description="Valid range for element count"
    )
    optimal_count: int = Field(
        ge=1,
        description="Recommended element count for best visual results"
    )
    element_name: str = Field(
        description="Name of elements (e.g., 'levels', 'stages', 'circles')"
    )
    required_fields: Optional[List[str]] = Field(
        None,
        description="Required request fields"
    )


class IllustratorServiceConfig(BaseModel):
    """Service-specific configuration for Illustrator variants"""
    generation_type: str = "llm_powered"
    llm_model: str = Field(description="LLM model for content generation")
    character_constraints: bool = Field(
        default=True,
        description="Whether character limits apply to generated text"
    )
    supports_target_points: bool = Field(
        default=True,
        description="Whether variant supports target_points guidance"
    )
    supports_context: bool = Field(
        default=True,
        description="Whether variant supports context/background information"
    )


# ============================================================================
# Text Service Models
# ============================================================================

class TextServiceConfig(BaseModel):
    """Service-specific configuration for Text/Table service variants"""
    supports_subtitles: bool = Field(
        default=True,
        description="Whether variant supports subtitle field"
    )
    max_key_points: int = Field(
        ge=1,
        description="Maximum number of key points supported"
    )
    template_file: str = Field(
        description="Template filename for rendering"
    )


# ============================================================================
# Analytics Service Models
# ============================================================================

class DataRequirements(BaseModel):
    """
    Data requirements for analytics/chart variants.

    Defines expected data structure and validation rules
    for data visualization variants.
    """
    structure: DataStructure = Field(
        description="Required data structure type"
    )
    min_items: int = Field(
        ge=1,
        description="Minimum number of data points"
    )
    max_items: int = Field(
        ge=1,
        description="Maximum number of data points"
    )
    value_type: ValueType = Field(
        description="Type of values in the dataset"
    )
    supports_percentages: Optional[bool] = Field(
        None,
        description="Whether percentage values are supported"
    )

    @field_validator('max_items')
    @classmethod
    def validate_max_items(cls, v: int, info) -> int:
        """Ensure max_items >= min_items"""
        if 'min_items' in info.data and v < info.data['min_items']:
            raise ValueError(f"max_items ({v}) must be >= min_items ({info.data['min_items']})")
        return v


class AnalyticsServiceConfig(BaseModel):
    """Service-specific configuration for Analytics service variants"""
    library: str = Field(
        description="Visualization library (chartjs, d3, etc.)"
    )
    chart_type: str = Field(
        description="Chart type identifier"
    )
    endpoint_key: str = Field(
        description="Key for endpoint lookup in typed pattern"
    )
    supports_custom_colors: Optional[bool] = Field(
        None,
        description="Whether custom color palettes are supported"
    )
    supports_data_labels: Optional[bool] = Field(
        None,
        description="Whether data labels can be displayed"
    )
    supports_horizontal: Optional[bool] = Field(
        None,
        description="Whether horizontal orientation is supported (bar charts)"
    )
    supports_stacked: Optional[bool] = Field(
        None,
        description="Whether stacking is supported (bar/area charts)"
    )


# ============================================================================
# Variant Configuration Model
# ============================================================================

class VariantConfig(BaseModel):
    """
    Complete configuration for a single variant.

    This is the core model representing each variant in the registry.
    Different services use different subsets of fields.
    """
    # Core fields (all variants)
    variant_id: str = Field(
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Unique identifier (snake_case with optional numbers)"
    )
    display_name: str = Field(
        min_length=3,
        max_length=100,
        description="Human-readable name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Brief description"
    )
    status: VariantStatus = Field(
        default=VariantStatus.PRODUCTION,
        description="Availability status"
    )
    layout_id: Optional[str] = Field(
        None,
        pattern=r'^L\d+$',
        description="Layout ID (e.g., L25, L29)"
    )

    # Endpoint (for per_variant pattern)
    endpoint: Optional[str] = Field(
        None,
        description="Dedicated endpoint path for this variant"
    )

    # Classification (required)
    classification: Classification

    # LLM Guidance (optional but recommended)
    llm_guidance: Optional[LLMGuidance] = None

    # Illustrator-specific
    parameters: Optional[IllustratorParameters] = None

    # Analytics-specific
    data_requirements: Optional[DataRequirements] = None

    # Text service fields
    required_fields: Optional[List[str]] = None
    optional_fields: Optional[List[str]] = None

    # Service-specific configurations
    service_specific: Optional[Dict[str, Any]] = Field(
        None,
        description="Service-specific configuration (illustrator, text_service, analytics)"
    )

    class Config:
        use_enum_values = True


# ============================================================================
# Service Configuration Model
# ============================================================================

class ServiceConfig(BaseModel):
    """
    Configuration for a content generation service.

    Each service (Text, Illustrator, Analytics) has one ServiceConfig
    entry in the registry.
    """
    enabled: bool = Field(
        description="Whether this service is currently enabled"
    )
    base_url: HttpUrl = Field(
        description="Base URL for service API"
    )
    service_type: ServiceType = Field(
        description="Type of content generation"
    )
    endpoint_pattern: EndpointPattern = Field(
        description="How endpoints are structured"
    )
    timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Request timeout in seconds"
    )

    # Endpoint configuration (depends on pattern)
    default_endpoint: Optional[str] = Field(
        None,
        description="Default endpoint (for single pattern)"
    )
    endpoints: Optional[Dict[str, str]] = Field(
        None,
        description="Named endpoints (for typed pattern)"
    )

    # Variants
    variants: Dict[str, VariantConfig] = Field(
        min_length=1,
        description="Map of variant_id to VariantConfig"
    )

    @model_validator(mode='after')
    def validate_endpoint_configuration(self) -> 'ServiceConfig':
        """Ensure endpoint configuration matches pattern"""
        if self.endpoint_pattern == EndpointPattern.SINGLE and not self.default_endpoint:
            raise ValueError("default_endpoint required for single endpoint pattern")

        if self.endpoint_pattern == EndpointPattern.TYPED and not self.endpoints:
            raise ValueError("endpoints required for typed endpoint pattern")

        return self

    class Config:
        use_enum_values = True


# ============================================================================
# Root Registry Model
# ============================================================================

class UnifiedVariantRegistry(BaseModel):
    """
    Root model for the unified variant registry.

    This is the top-level model that loads the entire
    config/unified_variant_registry.json file.

    Usage:
        registry = UnifiedVariantRegistry.model_validate_json(json_content)
        pyramid_variant = registry.services['illustrator_service_v1.0'].variants['pyramid']
    """
    version: str = Field(
        pattern=r'^\d+\.\d+\.\d+$',
        description="Semantic version of registry format"
    )
    last_updated: date = Field(
        description="Date of last registry update"
    )
    total_services: Optional[int] = Field(
        None,
        ge=1,
        description="Total number of registered services (for documentation)"
    )
    total_variants: Optional[int] = Field(
        None,
        ge=1,
        description="Total variants across all services (for documentation)"
    )

    services: Dict[str, ServiceConfig] = Field(
        description="Map of service_name to ServiceConfig"
    )

    classification_priority_order: Optional[List[str]] = Field(
        None,
        description="Global priority order for slide classification"
    )

    @field_validator('services')
    @classmethod
    def validate_service_names(cls, v: Dict[str, ServiceConfig]) -> Dict[str, ServiceConfig]:
        """Ensure service names follow naming convention"""
        import re
        # Allow both v<major>.<minor> and v<major> formats
        pattern = re.compile(r'^[a-z_]+_v\d+(\.\d+)?$')

        for service_name in v.keys():
            if not pattern.match(service_name):
                raise ValueError(
                    f"Service name '{service_name}' must match pattern: "
                    f"lowercase_with_underscores_v<major> or v<major>.<minor> "
                    f"(e.g., 'text_service_v1.2' or 'analytics_service_v3')"
                )

        return v

    def get_variant(self, service_name: str, variant_id: str) -> Optional[VariantConfig]:
        """
        Retrieve a specific variant configuration.

        Args:
            service_name: Service identifier (e.g., 'illustrator_service_v1.0')
            variant_id: Variant identifier (e.g., 'pyramid')

        Returns:
            VariantConfig if found, None otherwise
        """
        service = self.services.get(service_name)
        if not service:
            return None
        return service.variants.get(variant_id)

    def get_all_variants(self, service_type: Optional[ServiceType] = None) -> Dict[str, VariantConfig]:
        """
        Get all variants, optionally filtered by service type.

        Args:
            service_type: Optional filter by service type

        Returns:
            Dict mapping variant_id to VariantConfig
        """
        all_variants = {}

        for service_name, service_config in self.services.items():
            if service_type and service_config.service_type != service_type:
                continue

            for variant_id, variant_config in service_config.variants.items():
                # Prefix with service name to avoid collisions
                full_key = f"{service_name}.{variant_id}"
                all_variants[full_key] = variant_config

        return all_variants

    def get_variants_by_priority(self) -> List[tuple[str, str, VariantConfig]]:
        """
        Get all variants sorted by classification priority.

        Returns:
            List of (service_name, variant_id, VariantConfig) tuples
            sorted by priority (lower priority number = higher precedence)
        """
        variants_with_priority = []

        for service_name, service_config in self.services.items():
            for variant_id, variant_config in service_config.variants.items():
                variants_with_priority.append(
                    (service_name, variant_id, variant_config, variant_config.classification.priority)
                )

        # Sort by priority (ascending)
        variants_with_priority.sort(key=lambda x: x[3])

        # Return without priority number
        return [(svc, vid, vcfg) for svc, vid, vcfg, _ in variants_with_priority]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with total_services, total_variants, total_keywords
        """
        total_keywords = 0
        for service_config in self.services.values():
            for variant_config in service_config.variants.values():
                total_keywords += len(variant_config.classification.keywords)

        return {
            "total_services": len(self.services),
            "total_variants": sum(
                len(svc.variants) for svc in self.services.values()
            ),
            "total_keywords": total_keywords
        }

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "version": "2.0.0",
                "last_updated": "2025-11-29",
                "total_services": 3,
                "total_variants": 56,
                "services": {
                    "illustrator_service_v1.0": {
                        "enabled": True,
                        "base_url": "http://localhost:8000",
                        "service_type": "llm_generated",
                        "endpoint_pattern": "per_variant",
                        "variants": {}
                    }
                }
            }
        }


# ============================================================================
# Utility Functions
# ============================================================================

def load_registry_from_file(file_path: str) -> UnifiedVariantRegistry:
    """
    Load and validate registry from JSON file.

    Args:
        file_path: Path to unified_variant_registry.json

    Returns:
        Validated UnifiedVariantRegistry instance

    Raises:
        ValidationError: If JSON doesn't match schema
        FileNotFoundError: If file doesn't exist
    """
    import json
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return UnifiedVariantRegistry.model_validate(data)


def validate_registry_json(json_content: str) -> tuple[bool, Optional[str]]:
    """
    Validate registry JSON without loading.

    Args:
        json_content: JSON string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        UnifiedVariantRegistry.model_validate_json(json_content)
        return (True, None)
    except Exception as e:
        return (False, str(e))
