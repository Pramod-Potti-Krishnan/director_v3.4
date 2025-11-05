"""
Variant Selector for Director v3.4
====================================

Selects variant_id from Text Service v1.2's 34 platinum variants using
randomization for visual variety.

Selection Strategy:
1. Map Director's 13-type classification → v1.2 slide type
2. Fetch available variants for that slide type
3. Randomly select one variant (equal probability)
4. Return selected variant_id

This introduces variability in presentation visuals while maintaining
appropriate content structure per slide type.
"""

import random
from typing import Optional, List
from src.utils.variant_catalog import VariantCatalog
from src.utils.slide_type_mapper import SlideTypeMapper
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class VariantSelector:
    """
    Selects variant_id using random selection for visual variety.

    Features:
    - Equal probability selection among available variants
    - Fallback to first variant if random selection fails
    - Validation of variant existence
    - Detailed logging for debugging
    """

    def __init__(self, catalog: VariantCatalog, random_seed: Optional[int] = None):
        """
        Initialize variant selector.

        Args:
            catalog: Loaded VariantCatalog instance
            random_seed: Optional seed for reproducible randomization (testing)
        """
        if not catalog.is_loaded():
            raise ValueError(
                "VariantCatalog must be loaded before creating VariantSelector. "
                "Call await catalog.load_catalog() first."
            )

        self.catalog = catalog
        self.mapper = SlideTypeMapper()

        # Set random seed if provided (for testing/reproducibility)
        if random_seed is not None:
            random.seed(random_seed)
            logger.info(f"Random seed set to {random_seed} for reproducible selection")

        logger.info("VariantSelector initialized")

    def select_variant(
        self,
        director_classification: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Select variant_id for a Director classification using randomization.

        Selection Process:
        1. Map director_classification → v1.2 slide type
        2. Get available variants for that slide type
        3. Randomly select one (equal probability)
        4. Return selected variant_id

        Args:
            director_classification: Director's 13-type classification
                (e.g., "matrix_2x2", "title_slide", "bilateral_comparison")
            context: Optional context hint (currently unused, reserved for future)

        Returns:
            Selected variant_id (e.g., "matrix_2x3", "hero_opening_centered")
            None if no variants found

        Example:
            >>> selector.select_variant("matrix_2x2")
            "matrix_2x3"  # Randomly selected from ["matrix_2x2", "matrix_2x3"]

            >>> selector.select_variant("grid_3x3")
            "grid_4x2_catalog"  # Randomly selected from 9 grid variants
        """
        logger.debug(f"Selecting variant for '{director_classification}'")

        # Step 1: Map to v1.2 slide type
        slide_type = self.mapper.map_to_slide_type(director_classification)
        if not slide_type:
            logger.error(
                f"Cannot map '{director_classification}' to v1.2 slide type. "
                f"Valid types: {self.mapper.get_all_director_types()}"
            )
            return None

        # Step 2: Get available variants
        variants = self.catalog.get_variants_for_slide_type(slide_type)
        if not variants:
            logger.error(
                f"No variants found for slide_type '{slide_type}' "
                f"(mapped from '{director_classification}')"
            )
            return None

        # Step 3: Random selection (equal probability)
        selected_variant = random.choice(variants)

        logger.info(
            f"Selected '{selected_variant}' from {len(variants)} variants "
            f"for '{director_classification}' (slide_type: '{slide_type}')"
        )
        logger.debug(f"Available variants were: {variants}")

        return selected_variant

    def select_variant_with_fallback(
        self,
        director_classification: str,
        fallback_variant_id: Optional[str] = None
    ) -> str:
        """
        Select variant with fallback to first available or provided fallback.

        This method never returns None - it always returns a valid variant_id.

        Args:
            director_classification: Director's classification
            fallback_variant_id: Specific fallback variant (optional)

        Returns:
            Selected variant_id (never None)

        Raises:
            ValueError: If no variants available and no fallback provided
        """
        # Try random selection
        selected = self.select_variant(director_classification)
        if selected:
            return selected

        # Fallback 1: Use provided fallback
        if fallback_variant_id:
            logger.warning(
                f"Using provided fallback variant: '{fallback_variant_id}' "
                f"for '{director_classification}'"
            )
            return fallback_variant_id

        # Fallback 2: Use first variant of slide type
        slide_type = self.mapper.map_to_slide_type(director_classification)
        if slide_type:
            variants = self.catalog.get_variants_for_slide_type(slide_type)
            if variants:
                fallback = variants[0]
                logger.warning(
                    f"Using first available variant: '{fallback}' "
                    f"for '{director_classification}'"
                )
                return fallback

        # No variants available at all
        raise ValueError(
            f"No variants available for '{director_classification}' and no fallback provided"
        )

    def get_variant_count_for_classification(
        self,
        director_classification: str
    ) -> int:
        """
        Get number of available variants for a classification.

        Args:
            director_classification: Director's classification

        Returns:
            Number of available variants (0 if none)
        """
        slide_type = self.mapper.map_to_slide_type(director_classification)
        if not slide_type:
            return 0

        variants = self.catalog.get_variants_for_slide_type(slide_type)
        return len(variants)

    def get_available_variants(
        self,
        director_classification: str
    ) -> List[str]:
        """
        Get list of all available variant_ids for a classification.

        Args:
            director_classification: Director's classification

        Returns:
            List of variant_ids (empty if none)
        """
        slide_type = self.mapper.map_to_slide_type(director_classification)
        if not slide_type:
            return []

        return self.catalog.get_variants_for_slide_type(slide_type)

    def validate_variant_selection(
        self,
        director_classification: str,
        variant_id: str
    ) -> bool:
        """
        Validate if a variant_id is valid for a classification.

        Args:
            director_classification: Director's classification
            variant_id: Variant ID to validate

        Returns:
            True if valid pairing, False otherwise
        """
        available = self.get_available_variants(director_classification)
        is_valid = variant_id in available

        if not is_valid:
            logger.warning(
                f"Invalid variant '{variant_id}' for '{director_classification}'. "
                f"Valid options: {available}"
            )

        return is_valid


# Convenience function
def select_random_variant(
    catalog: VariantCatalog,
    director_classification: str
) -> Optional[str]:
    """
    Select random variant (convenience function).

    Args:
        catalog: Loaded VariantCatalog
        director_classification: Director's classification

    Returns:
        Selected variant_id or None
    """
    selector = VariantSelector(catalog)
    return selector.select_variant(director_classification)


# Example usage
if __name__ == "__main__":
    import asyncio
    from src.utils.variant_catalog import load_variant_catalog

    async def test_selector():
        print("Variant Selector Test - Random Selection")
        print("=" * 70)

        # Load catalog
        print("\nLoading variant catalog...")
        catalog = await load_variant_catalog("https://web-production-5daf.up.railway.app")

        # Create selector (with seed for reproducible testing)
        selector = VariantSelector(catalog, random_seed=42)

        # Test selection for each Director type
        print("\nRandom Variant Selection (seed=42):")
        test_classifications = [
            "title_slide",
            "matrix_2x2",
            "grid_3x3",
            "bilateral_comparison",
            "sequential_3col",
            "metrics_grid",
            "styled_table"
        ]

        for classification in test_classifications:
            variants = selector.get_available_variants(classification)
            selected = selector.select_variant(classification)

            print(f"\n  {classification}:")
            print(f"    Available: {len(variants)} variants → {variants}")
            print(f"    Selected: '{selected}'")

        # Test multiple selections (show randomness)
        print("\n\nMultiple Selections for 'matrix_2x2' (no seed):")
        selector_random = VariantSelector(catalog)  # No seed = truly random
        for i in range(5):
            selected = selector_random.select_variant("matrix_2x2")
            print(f"  Selection {i+1}: {selected}")

        # Test variant counts
        print("\n\nVariant Counts by Classification:")
        for classification in test_classifications:
            count = selector.get_variant_count_for_classification(classification)
            print(f"  {classification:30s}: {count} variants")

        print("\n" + "=" * 70)
        print("Test complete!")

    asyncio.run(test_selector())
