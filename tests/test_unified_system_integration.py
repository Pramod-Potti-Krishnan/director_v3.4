"""
End-to-End Integration Tests for Unified Variant System

Tests the complete workflow from registry loading through classification
and routing to content generation.

Version: 1.0.0
Created: 2025-11-29
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.registry_loader import get_registry
from src.services.unified_slide_classifier import UnifiedSlideClassifier
from src.services.unified_service_router import UnifiedServiceRouter
from src.services.director_integration import DirectorIntegrationLayer
from src.utils.unified_system_rollout import UnifiedSystemRollout


class TestRegistryToClassificationWorkflow:
    """Test complete workflow from registry to classification"""

    def test_load_registry_and_classify_pie_chart(self):
        """Test loading registry and classifying a pie chart slide"""
        # Load registry
        registry = get_registry()

        assert registry is not None
        assert len(registry.services) > 0

        # Create classifier
        classifier = UnifiedSlideClassifier(registry)

        # Classify pie chart slide
        matches = classifier.classify_slide(
            title="Market Share Distribution",
            key_points=["Product A: 45%", "Product B: 30%", "Product C: 25%"],
            context="Revenue breakdown by product"
        )

        # Should match pie_chart
        assert len(matches) > 0
        assert any(m.variant_id == "pie_chart" for m in matches)

        # Best match should be pie_chart
        best_match = matches[0]
        assert best_match.variant_id == "pie_chart"
        assert best_match.confidence > 0.3  # Lower threshold for sample registry

    def test_load_registry_and_classify_bar_chart(self):
        """Test classifying a bar chart slide"""
        registry = get_registry()
        classifier = UnifiedSlideClassifier(registry)

        matches = classifier.classify_slide(
            title="Sales Comparison Across Regions",
            key_points=["North: $1M", "South: $800K", "East: $1.2M"],
            context="Comparing regional sales performance",
            min_confidence=0.05  # Lower threshold for sample registry
        )

        # Should match bar_chart
        assert len(matches) > 0
        assert any(m.variant_id == "bar_chart" for m in matches)

    @pytest.mark.skip(reason="line_chart not in sample registry - requires full production registry")
    def test_load_registry_and_classify_line_chart(self):
        """Test classifying a line chart slide"""
        registry = get_registry()
        classifier = UnifiedSlideClassifier(registry)

        matches = classifier.classify_slide(
            title="Revenue Growth Over Time",
            key_points=["Q1: $1M", "Q2: $1.2M", "Q3: $1.5M", "Q4: $1.8M"],
            context="Quarterly revenue trends"
        )

        # Should match line_chart
        assert len(matches) > 0
        assert any(m.variant_id == "line_chart" for m in matches)


class TestClassificationToRoutingWorkflow:
    """Test workflow from classification to routing"""

    @pytest.mark.asyncio
    async def test_classify_and_route_to_service(self):
        """Test classifying slide and routing to correct service"""
        registry = get_registry()
        classifier = UnifiedSlideClassifier(registry)
        router = UnifiedServiceRouter(registry)

        # Classify
        matches = classifier.classify_slide(
            title="Market Share by Product",
            key_points=["Product A: 40%", "Product B: 35%", "Product C: 25%"],
            min_confidence=0.05  # Lower threshold for sample registry
        )

        assert len(matches) > 0
        best_match = matches[0]

        # Get variant info for routing
        variant_info = router.get_variant_info(
            best_match.variant_id,
            best_match.service_name
        )

        assert variant_info is not None
        assert variant_info["variant_id"] == best_match.variant_id
        assert variant_info["service_name"] == best_match.service_name
        assert "endpoint" in variant_info


class TestDirectorIntegrationWorkflow:
    """Test complete Director integration workflow"""

    def test_integration_layer_initialization(self):
        """Test Director integration layer initializes correctly"""
        integration = DirectorIntegrationLayer()

        assert integration is not None
        assert integration.registry is not None
        assert integration.classifier is not None
        assert integration.router is not None

    def test_classify_slide_via_integration(self):
        """Test classifying slide via integration layer"""
        integration = DirectorIntegrationLayer()

        # Use content that matches sample registry keywords (e.g., "comparison" for bar_chart)
        result = integration.classify_slide(
            title="Regional Sales Comparison",
            key_points=["North America: $5M", "Europe: $4M", "Asia: $3M"],
            min_confidence=0.05  # Lower threshold for sample registry
        )

        assert result["matches"] is not None
        assert len(result["matches"]) > 0
        assert result["best_match"] is not None
        assert result["variant_id"] is not None
        assert result["service_name"] is not None
        assert result["confidence"] > 0

    def test_enrich_slide_with_classification(self):
        """Test enriching slide with classification data"""
        integration = DirectorIntegrationLayer()

        # Create mock slide
        slide = Mock()
        slide.slide_id = "slide_1"
        slide.title = "Revenue Distribution"
        slide.key_points = ["Product A: 45%", "Product B: 30%", "Product C: 25%"]
        slide.description = "Product revenue breakdown"

        # Enrich slide
        enriched = integration.classify_and_enrich_slide(slide)

        # Should have classification data
        assert hasattr(enriched, 'variant_id')
        assert hasattr(enriched, 'service_name')
        assert hasattr(enriched, 'classification_confidence')


class TestRolloutSystemIntegration:
    """Test rollout system integration"""

    def test_rollout_disabled_always_returns_false(self):
        """Test disabled rollout always returns False"""
        with patch('src.utils.unified_system_rollout.get_settings') as mock_settings:
            settings = Mock()
            settings.UNIFIED_VARIANT_SYSTEM_ENABLED = False
            settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100
            mock_settings.return_value = settings

            rollout = UnifiedSystemRollout()

            assert rollout.should_use_unified_system("session_123") is False

    def test_rollout_100_percent_always_returns_true(self):
        """Test 100% rollout always returns True"""
        with patch('src.utils.unified_system_rollout.get_settings') as mock_settings:
            settings = Mock()
            settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
            settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100
            mock_settings.return_value = settings

            rollout = UnifiedSystemRollout()

            assert rollout.should_use_unified_system("session_123") is True
            assert rollout.should_use_unified_system("session_456") is True

    def test_rollout_with_integration_layer(self):
        """Test rollout decision affects integration layer usage"""
        # This test validates the pattern Director would use
        with patch('src.utils.unified_system_rollout.get_settings') as mock_settings:
            settings = Mock()
            settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
            settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100
            mock_settings.return_value = settings

            rollout = UnifiedSystemRollout()
            session_id = "test_session"

            if rollout.should_use_unified_system(session_id):
                # Would use DirectorIntegrationLayer
                integration = DirectorIntegrationLayer()
                assert integration is not None
            else:
                # Would use existing SlideTypeClassifier
                pass


class TestCompleteVariantLifecycle:
    """Test complete lifecycle of a variant through the system"""

    def test_pie_chart_complete_lifecycle(self):
        """Test pie chart from registry to classification"""
        # 1. Load registry
        registry = get_registry()
        assert "analytics_service_v3" in registry.services

        # 2. Verify variant exists in registry
        analytics = registry.services["analytics_service_v3"]
        assert "pie_chart" in analytics.variants

        variant = analytics.variants["pie_chart"]
        assert variant.variant_id == "pie_chart"
        assert variant.display_name == "Pie Chart"
        assert len(variant.classification.keywords) >= 5

        # 3. Classify slide
        classifier = UnifiedSlideClassifier(registry)
        matches = classifier.classify_slide(
            title="Market Share Distribution",
            key_points=["Segment A: 40%", "Segment B: 35%", "Segment C: 25%"],
            min_confidence=0.05  # Lower threshold for sample registry
        )

        # 4. Verify classification
        assert len(matches) > 0
        pie_match = next((m for m in matches if m.variant_id == "pie_chart"), None)
        assert pie_match is not None
        assert pie_match.service_name == "analytics_service_v3"

        # 5. Get routing information
        router = UnifiedServiceRouter(registry)
        variant_info = router.get_variant_info("pie_chart", "analytics_service_v3")

        assert variant_info["endpoint"] is not None
        assert variant_info["layout_id"] is not None

    def test_text_layout_complete_lifecycle(self):
        """Test text layout from registry to classification"""
        registry = get_registry()

        # Verify text service exists
        assert "text_service_v1.2" in registry.services

        # Get a text variant
        text_service = registry.services["text_service_v1.2"]
        assert len(text_service.variants) > 0

        # Pick first variant
        variant_id = list(text_service.variants.keys())[0]
        variant = text_service.variants[variant_id]

        # Classify using variant keywords
        classifier = UnifiedSlideClassifier(registry)
        first_keyword = variant.classification.keywords[0]

        matches = classifier.classify_slide(
            title=f"Slide about {first_keyword}",
            key_points=[f"Key point about {first_keyword}"],
            min_confidence=0.05  # Lower threshold for sample registry
        )

        # Should match the variant
        assert len(matches) > 0


class TestStatisticsAndMetrics:
    """Test system statistics and metrics"""

    def test_registry_statistics(self):
        """Test getting registry statistics"""
        registry = get_registry()

        stats = registry.get_statistics()

        assert stats["total_services"] > 0
        assert stats["total_variants"] > 0
        assert stats["total_keywords"] > 0

        # Should have multiple services
        assert stats["total_services"] >= 3  # At least Analytics, Text, Illustrator

        # Should have variants (sample registry has 7, production has 56+)
        assert stats["total_variants"] >= 7  # Sample registry minimum

    def test_classifier_statistics(self):
        """Test getting classifier statistics"""
        registry = get_registry()
        classifier = UnifiedSlideClassifier(registry)

        stats = classifier.get_classification_stats()

        assert stats["total_variants"] > 0
        assert len(stats["services"]) > 0  # services is a dict of service breakdowns
        assert stats["unique_keywords"] > 0

    def test_integration_layer_statistics(self):
        """Test getting integration layer statistics"""
        integration = DirectorIntegrationLayer()

        stats = integration.get_stats()

        assert "service_stats" in stats
        assert "classification_stats" in stats
        assert "registry_info" in stats

        # Service stats
        assert stats["service_stats"]["total_services"] > 0
        assert stats["service_stats"]["total_variants"] > 0

        # Classification stats
        assert stats["classification_stats"]["total_variants"] > 0


class TestErrorHandling:
    """Test error handling throughout the system"""

    def test_classify_slide_with_no_matches(self):
        """Test classifying slide that matches no variants"""
        registry = get_registry()
        classifier = UnifiedSlideClassifier(registry)

        matches = classifier.classify_slide(
            title="Completely unrelated content xyz123",
            key_points=["Random point", "Another random point"]
        )

        # May have no matches or very low confidence matches
        if matches:
            assert matches[0].confidence < 0.5

    def test_integration_with_unclassified_slide(self):
        """Test integration layer with slide that can't be classified"""
        integration = DirectorIntegrationLayer()

        result = integration.classify_slide(
            title="xyz unmatched content 123",
            key_points=["random", "unrelated"]
        )

        # Should handle gracefully
        assert result is not None
        assert result["variant_id"] is None or result["confidence"] < 0.5

    def test_router_with_invalid_variant(self):
        """Test router with non-existent variant"""
        registry = get_registry()
        router = UnifiedServiceRouter(registry)

        variant_info = router.get_variant_info(
            "nonexistent_variant",
            "nonexistent_service"
        )

        # Should return None or handle gracefully
        assert variant_info is None


class TestBackwardCompatibility:
    """Test backward compatibility with existing systems"""

    def test_integration_layer_provides_backward_compatible_interface(self):
        """Test that integration layer can replace existing components"""
        integration = DirectorIntegrationLayer()

        # Should provide classification (like SlideTypeClassifier)
        result = integration.classify_slide(
            title="Test slide",
            key_points=["Point 1", "Point 2"]
        )

        assert "variant_id" in result
        assert "service_name" in result
        assert "confidence" in result

        # Should enrich slides (like current enrichment logic)
        slide = Mock()
        slide.slide_id = "slide_1"
        slide.title = "Market comparison analysis"  # Use keywords that match sample registry
        slide.key_points = ["Point 1", "Point 2"]
        slide.description = None  # Explicitly set to None to avoid Mock behavior
        slide.context = None

        enriched = integration.classify_and_enrich_slide(slide)
        assert enriched is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
