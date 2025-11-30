"""
Tests for Unified Slide Classifier

Comprehensive tests for registry-driven slide classification.

Version: 2.0.0
Created: 2025-11-29
"""

import pytest
from src.services.unified_slide_classifier import UnifiedSlideClassifier, ClassificationMatch
from src.models.variant_registry import (
    UnifiedVariantRegistry,
    ServiceConfig,
    VariantConfig,
    Classification,
    ServiceType,
    EndpointPattern,
    VariantStatus
)


@pytest.fixture
def sample_registry():
    """Create sample registry with test variants"""
    return UnifiedVariantRegistry(
        version="2.0.0",
        last_updated="2025-11-29",
        total_services=2,
        total_variants=5,
        services={
            "illustrator_service_v1.0": ServiceConfig(
                enabled=True,
                base_url="http://localhost:8000",
                service_type=ServiceType.LLM_GENERATED,
                endpoint_pattern=EndpointPattern.PER_VARIANT,
                timeout=60,
                variants={
                    "pyramid": VariantConfig(
                        variant_id="pyramid",
                        display_name="Pyramid (Hierarchical)",
                        description="Multi-level hierarchical structure",
                        status=VariantStatus.PRODUCTION,
                        classification=Classification(
                            priority=4,
                            keywords=[
                                "pyramid", "hierarchical", "hierarchy",
                                "levels", "tier", "tiers", "organizational structure",
                                "org chart", "foundation to top"
                            ]
                        )
                    ),
                    "funnel": VariantConfig(
                        variant_id="funnel",
                        display_name="Funnel (Conversion)",
                        description="Multi-stage conversion funnel",
                        status=VariantStatus.PRODUCTION,
                        classification=Classification(
                            priority=5,
                            keywords=[
                                "funnel", "sales funnel", "conversion funnel",
                                "pipeline", "sales pipeline", "conversion",
                                "awareness", "consideration", "decision",
                                "tofu", "mofu", "bofu", "lead generation"
                            ]
                        )
                    ),
                    "concentric_circles": VariantConfig(
                        variant_id="concentric_circles",
                        display_name="Concentric Circles",
                        description="Nested circular layers",
                        status=VariantStatus.PRODUCTION,
                        classification=Classification(
                            priority=6,
                            keywords=[
                                "concentric", "concentric circles", "nested circles",
                                "rings", "orbital", "radial", "ripple effect",
                                "inner circle", "outer circle", "stakeholder map"
                            ]
                        )
                    )
                }
            ),
            "analytics_service_v3": ServiceConfig(
                enabled=True,
                base_url="http://localhost:8006",
                service_type=ServiceType.DATA_VISUALIZATION,
                endpoint_pattern=EndpointPattern.TYPED,
                timeout=60,
                endpoints={"chartjs": "/analytics/v3/chartjs/generate"},
                variants={
                    "pie_chart": VariantConfig(
                        variant_id="pie_chart",
                        display_name="Pie Chart",
                        description="Circular proportions chart",
                        status=VariantStatus.PRODUCTION,
                        classification=Classification(
                            priority=2,
                            keywords=[
                                "pie chart", "pie", "proportion", "percentage",
                                "share", "distribution", "breakdown", "composition",
                                "market share", "budget allocation"
                            ]
                        )
                    ),
                    "bar_chart": VariantConfig(
                        variant_id="bar_chart",
                        display_name="Bar Chart",
                        description="Categorical comparison bars",
                        status=VariantStatus.PRODUCTION,
                        classification=Classification(
                            priority=2,
                            keywords=[
                                "bar chart", "bar", "bars", "column chart",
                                "comparison", "compare categories", "categorical data",
                                "revenue by region", "sales by product"
                            ]
                        )
                    )
                }
            )
        }
    )


@pytest.fixture
def classifier(sample_registry):
    """Create classifier instance"""
    return UnifiedSlideClassifier(sample_registry)


class TestClassifierInitialization:
    """Test classifier initialization and keyword indexing"""

    def test_initialization(self, classifier):
        """Test classifier initializes correctly"""
        assert classifier is not None
        assert len(classifier.variant_keywords) == 5

    def test_keyword_index_structure(self, classifier):
        """Test keyword index has correct structure"""
        pyramid_info = classifier.variant_keywords.get("pyramid")
        assert pyramid_info is not None
        assert "keywords" in pyramid_info
        assert "priority" in pyramid_info
        assert "service_name" in pyramid_info
        assert "display_name" in pyramid_info

    def test_keywords_normalized(self, classifier):
        """Test keywords are normalized to lowercase"""
        pyramid_keywords = classifier.variant_keywords["pyramid"]["keywords"]
        # All keywords should be lowercase
        for keyword in pyramid_keywords:
            assert keyword == keyword.lower()

    def test_priority_mapping(self, classifier):
        """Test priority values are correctly mapped"""
        assert classifier.variant_keywords["pie_chart"]["priority"] == 2
        assert classifier.variant_keywords["pyramid"]["priority"] == 4
        assert classifier.variant_keywords["funnel"]["priority"] == 5


class TestSlideClassification:
    """Test slide classification functionality"""

    def test_classify_pie_chart_slide(self, classifier):
        """Test classification of pie chart content"""
        matches = classifier.classify_slide(
            title="Market Share Distribution",
            key_points=[
                "Product A: 45%",
                "Product B: 30%",
                "Product C: 25%"
            ],
            context="Revenue breakdown by product"
        )

        assert len(matches) > 0
        assert matches[0].variant_id == "pie_chart"
        assert matches[0].confidence > 0.1

    def test_classify_funnel_slide(self, classifier):
        """Test classification of funnel content"""
        matches = classifier.classify_slide(
            title="Sales Conversion Funnel",
            key_points=[
                "Awareness: 10,000 visitors",
                "Consideration: 1,000 leads",
                "Decision: 100 opportunities",
                "Conversion: 25 deals"
            ],
            context="TOFU to BOFU pipeline analysis"
        )

        assert len(matches) > 0
        assert matches[0].variant_id == "funnel"
        assert "funnel" in matches[0].matched_keywords or "conversion" in matches[0].matched_keywords

    def test_classify_pyramid_slide(self, classifier):
        """Test classification of pyramid content"""
        matches = classifier.classify_slide(
            title="Organizational Hierarchy",
            key_points=[
                "Executive Leadership",
                "Department Heads",
                "Team Managers",
                "Individual Contributors"
            ],
            context="4-tier organizational structure from top to foundation"
        )

        assert len(matches) > 0
        # Pyramid should be in top results
        pyramid_match = next((m for m in matches if m.variant_id == "pyramid"), None)
        assert pyramid_match is not None

    def test_classify_concentric_circles_slide(self, classifier):
        """Test classification of concentric circles content"""
        matches = classifier.classify_slide(
            title="Stakeholder Influence Map",
            key_points=[
                "Inner circle: Core team (direct control)",
                "Middle ring: Department leads (high influence)",
                "Outer ring: Company-wide teams (moderate influence)",
                "Periphery: External partners (low influence)"
            ],
            context="Concentric zones showing stakeholder proximity"
        )

        assert len(matches) > 0
        concentric_match = next((m for m in matches if m.variant_id == "concentric_circles"), None)
        assert concentric_match is not None

    def test_classify_bar_chart_slide(self, classifier):
        """Test classification of bar chart content"""
        matches = classifier.classify_slide(
            title="Revenue by Region",
            key_points=[
                "North America: $5M",
                "Europe: $3.2M",
                "Asia Pacific: $2.8M",
                "Latin America: $1.5M"
            ],
            context="Regional sales comparison for Q4"
        )

        assert len(matches) > 0
        bar_match = next((m for m in matches if m.variant_id == "bar_chart"), None)
        assert bar_match is not None

    def test_classification_with_title_only(self, classifier):
        """Test classification works with only title"""
        matches = classifier.classify_slide(
            title="Market Share Pie Chart Analysis"
        )

        assert len(matches) > 0
        assert matches[0].variant_id == "pie_chart"

    def test_classification_with_key_points_only(self, classifier):
        """Test classification works with only key points"""
        matches = classifier.classify_slide(
            key_points=[
                "Sales funnel stages",
                "Conversion rates at each level",
                "Pipeline optimization"
            ]
        )

        assert len(matches) > 0
        funnel_match = next((m for m in matches if m.variant_id == "funnel"), None)
        assert funnel_match is not None

    def test_classification_with_context_only(self, classifier):
        """Test classification works with only context"""
        matches = classifier.classify_slide(
            context="This slide shows the organizational hierarchy pyramid with 4 tiers"
        )

        assert len(matches) > 0
        pyramid_match = next((m for m in matches if m.variant_id == "pyramid"), None)
        assert pyramid_match is not None

    def test_no_matches_for_unrelated_content(self, classifier):
        """Test no matches for completely unrelated content"""
        matches = classifier.classify_slide(
            title="Random Unrelated Topic",
            key_points=["Point 1", "Point 2"],
            context="Nothing matching any keywords",
            min_confidence=0.5
        )

        # Should have no high-confidence matches
        assert len(matches) == 0


class TestMatchScoring:
    """Test match scoring and ranking"""

    def test_match_score_calculation(self, classifier):
        """Test match score reflects number of keywords matched"""
        matches = classifier.classify_slide(
            title="Sales Funnel Conversion Pipeline with Lead Generation",
            context="TOFU MOFU BOFU awareness consideration decision"
        )

        funnel_match = next((m for m in matches if m.variant_id == "funnel"), None)
        assert funnel_match is not None
        # Should have matched multiple funnel keywords
        assert funnel_match.match_score >= 5

    def test_confidence_calculation(self, classifier):
        """Test confidence score is between 0 and 1"""
        matches = classifier.classify_slide(
            title="Market Share Distribution",
            key_points=["Pie chart showing percentages"]
        )

        for match in matches:
            assert 0.0 <= match.confidence <= 1.0

    def test_priority_based_ranking(self, classifier):
        """Test results are ranked by priority"""
        # Both pie and bar have priority 2, funnel has priority 5
        matches = classifier.classify_slide(
            title="Data comparison chart showing pie and bar distributions"
        )

        # Lower priority number should come first (if matched)
        if len(matches) >= 2:
            # Pie and bar (priority 2) should come before funnel (priority 5)
            priority_2_matches = [m for m in matches if m.priority == 2]
            priority_5_matches = [m for m in matches if m.priority == 5]

            if priority_2_matches and priority_5_matches:
                # First priority 2 match should come before first priority 5 match
                idx_p2 = matches.index(priority_2_matches[0])
                idx_p5 = matches.index(priority_5_matches[0])
                assert idx_p2 < idx_p5

    def test_min_confidence_filtering(self, classifier):
        """Test min_confidence threshold filters results"""
        # Get matches with low threshold
        low_threshold_matches = classifier.classify_slide(
            title="Some vague content",
            min_confidence=0.1
        )

        # Get matches with high threshold
        high_threshold_matches = classifier.classify_slide(
            title="Some vague content",
            min_confidence=0.8
        )

        # High threshold should have fewer or equal matches
        assert len(high_threshold_matches) <= len(low_threshold_matches)

    def test_max_results_limiting(self, classifier):
        """Test max_results limits number of matches"""
        matches = classifier.classify_slide(
            title="chart data visualization pie bar funnel pyramid",
            max_results=2
        )

        assert len(matches) <= 2

    def test_matched_keywords_tracking(self, classifier):
        """Test matched keywords are tracked correctly"""
        matches = classifier.classify_slide(
            title="Organizational Hierarchy Pyramid Structure"
        )

        pyramid_match = next((m for m in matches if m.variant_id == "pyramid"), None)
        assert pyramid_match is not None
        assert len(pyramid_match.matched_keywords) > 0
        # Should have matched some relevant keywords
        relevant_keywords = ["organizational", "hierarchy", "pyramid", "structure"]
        matched_any = any(kw in pyramid_match.matched_keywords for kw in relevant_keywords)
        assert matched_any


class TestClassifierQueries:
    """Test classifier query methods"""

    def test_get_variant_keywords(self, classifier):
        """Test getting keywords for specific variant"""
        keywords = classifier.get_variant_keywords("pyramid")
        assert keywords is not None
        assert "pyramid" in keywords
        assert "hierarchy" in keywords

    def test_get_variant_keywords_not_found(self, classifier):
        """Test getting keywords for non-existent variant"""
        keywords = classifier.get_variant_keywords("nonexistent")
        assert keywords is None

    def test_get_all_keywords(self, classifier):
        """Test getting all unique keywords"""
        all_keywords = classifier.get_all_keywords()
        assert len(all_keywords) > 0
        # Should contain keywords from all variants
        assert "pyramid" in all_keywords
        assert "funnel" in all_keywords
        assert "pie" in all_keywords

    def test_find_variants_by_keyword(self, classifier):
        """Test finding variants by specific keyword"""
        # "hierarchy" should be in pyramid keywords
        variants = classifier.find_variants_by_keyword("hierarchy")
        assert "pyramid" in variants

    def test_find_variants_by_keyword_case_insensitive(self, classifier):
        """Test keyword search is case-insensitive"""
        lower_variants = classifier.find_variants_by_keyword("pyramid")
        upper_variants = classifier.find_variants_by_keyword("PYRAMID")
        mixed_variants = classifier.find_variants_by_keyword("PyRaMiD")

        assert lower_variants == upper_variants == mixed_variants

    def test_get_classification_stats(self, classifier):
        """Test getting classification statistics"""
        stats = classifier.get_classification_stats()

        assert "total_variants" in stats
        assert "total_keywords" in stats
        assert "unique_keywords" in stats
        assert "services" in stats
        assert "priority_range" in stats

        assert stats["total_variants"] == 5
        assert stats["total_keywords"] > 0
        assert stats["unique_keywords"] > 0


class TestCaseInsensitivity:
    """Test case-insensitive matching"""

    def test_uppercase_content_matches(self, classifier):
        """Test uppercase content matches lowercase keywords"""
        matches = classifier.classify_slide(
            title="SALES FUNNEL CONVERSION PIPELINE"
        )

        funnel_match = next((m for m in matches if m.variant_id == "funnel"), None)
        assert funnel_match is not None

    def test_mixed_case_content_matches(self, classifier):
        """Test mixed case content matches"""
        matches = classifier.classify_slide(
            title="Market Share Distribution Pie Chart Analysis"
        )

        pie_match = next((m for m in matches if m.variant_id == "pie_chart"), None)
        assert pie_match is not None

    def test_lowercase_content_matches(self, classifier):
        """Test lowercase content matches"""
        matches = classifier.classify_slide(
            title="organizational hierarchy pyramid structure"
        )

        pyramid_match = next((m for m in matches if m.variant_id == "pyramid"), None)
        assert pyramid_match is not None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_content(self, classifier):
        """Test classification with no content"""
        matches = classifier.classify_slide()
        assert len(matches) == 0

    def test_none_values(self, classifier):
        """Test classification with None values"""
        matches = classifier.classify_slide(
            title=None,
            key_points=None,
            context=None
        )
        assert len(matches) == 0

    def test_empty_strings(self, classifier):
        """Test classification with empty strings"""
        matches = classifier.classify_slide(
            title="",
            key_points=[""],
            context=""
        )
        # Might have no matches or very low confidence matches
        assert isinstance(matches, list)

    def test_classification_match_dataclass(self):
        """Test ClassificationMatch dataclass"""
        match = ClassificationMatch(
            variant_id="test",
            service_name="test_service",
            display_name="Test Variant",
            priority=1,
            match_score=5,
            matched_keywords=["test", "keyword"],
            confidence=0.75
        )

        assert match.variant_id == "test"
        assert match.confidence == 0.75
        assert len(match.matched_keywords) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
