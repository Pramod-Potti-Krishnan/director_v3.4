"""
Unit Tests for Error Classification and Summary (Tier 1 + Tier 2)

Tests the error classification helper and error summary generation
to ensure comprehensive debugging information for customer support.
"""

import pytest
from unittest.mock import Mock
import httpx
from src.utils.service_router_v1_2 import ServiceRouterV1_2


class TestErrorClassification:
    """Test error classification and summary generation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock clients
        self.mock_text_client = Mock()
        self.mock_analytics_client = Mock()
        self.mock_illustrator_client = Mock()

        # Create router with mock clients
        self.router = ServiceRouterV1_2(
            text_service_client=self.mock_text_client,
            analytics_client=self.mock_analytics_client,
            illustrator_client=self.mock_illustrator_client
        )

    def test_classify_timeout_error(self):
        """Timeout errors should be classified correctly."""
        error = httpx.TimeoutException("Request timeout")

        classification = self.router._classify_error(error)

        assert classification["error_category"] == "timeout"
        assert "timeout" in classification["suggested_action"].lower()
        assert classification["http_status"] is None

    def test_classify_http_4xx_error(self):
        """HTTP 4xx errors should be classified as client errors."""
        # Create mock response with 404 status
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

        classification = self.router._classify_error(error, response=mock_response)

        assert classification["error_category"] == "http_4xx"
        assert classification["http_status"] == 404
        assert "client error" in classification["suggested_action"].lower()

    def test_classify_http_5xx_error(self):
        """HTTP 5xx errors should be classified as server errors."""
        # Create mock response with 500 status
        mock_response = Mock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

        classification = self.router._classify_error(error, response=mock_response)

        assert classification["error_category"] == "http_5xx"
        assert classification["http_status"] == 500
        assert "server error" in classification["suggested_action"].lower()

    def test_classify_connection_error(self):
        """Connection errors should be classified correctly."""
        error = httpx.ConnectError("Connection refused")

        classification = self.router._classify_error(error)

        assert classification["error_category"] == "connection"
        assert "service" in classification["suggested_action"].lower()

    def test_classify_validation_error(self):
        """Validation errors should be classified correctly."""
        from pydantic import ValidationError

        # Create a simple validation error
        try:
            from pydantic import BaseModel, Field
            class TestModel(BaseModel):
                required_field: str
            TestModel(required_field=123)  # Wrong type
        except ValidationError as e:
            classification = self.router._classify_error(e)

            assert classification["error_category"] == "validation"
            assert "validation" in classification["suggested_action"].lower()

    def test_generate_error_summary_empty(self):
        """Empty failed_slides should return empty summary."""
        summary = self.router._generate_error_summary([])

        assert summary["total_failures"] == 0
        assert summary["by_category"] == {}
        assert summary["by_service"] == {}
        assert summary["critical_issues"] == []
        assert summary["recommended_actions"] == []

    def test_generate_error_summary_validation_errors(self):
        """Validation errors should trigger high-severity critical issue."""
        failed_slides = [
            {
                "slide_number": 1,
                "slide_id": "s1",
                "error": "Missing client",
                "service": "analytics_v3",
                "endpoint": None,
                "error_category": "validation",
                "suggested_action": "Initialize AnalyticsClient"
            },
            {
                "slide_number": 2,
                "slide_id": "s2",
                "error": "Missing client",
                "service": "illustrator_v1.0",
                "endpoint": None,
                "error_category": "validation",
                "suggested_action": "Initialize IllustratorClient"
            }
        ]

        summary = self.router._generate_error_summary(failed_slides)

        assert summary["total_failures"] == 2
        assert summary["by_category"]["validation"] == 2
        assert summary["by_service"]["analytics_v3"] == 1
        assert summary["by_service"]["illustrator_v1.0"] == 1

        # Should have critical issue
        assert len(summary["critical_issues"]) == 1
        assert summary["critical_issues"][0]["severity"] == "high"
        assert "client" in summary["critical_issues"][0]["issue"].lower()

        # Should have priority 1 recommendation
        assert summary["recommended_actions"][0]["priority"] == 1
        assert "client" in summary["recommended_actions"][0]["action"].lower()

    def test_generate_error_summary_timeout_errors(self):
        """Timeout errors should trigger medium-severity critical issue."""
        failed_slides = [
            {
                "slide_number": 3,
                "slide_id": "s3",
                "error": "Timeout",
                "service": "text_service_v1.2",
                "endpoint": "/v1.2/generate",
                "error_category": "timeout",
                "suggested_action": "Increase timeout"
            }
        ]

        summary = self.router._generate_error_summary(failed_slides)

        assert summary["total_failures"] == 1
        assert summary["by_category"]["timeout"] == 1

        # Should have critical issue with medium severity
        timeout_issues = [i for i in summary["critical_issues"] if i["issue"] == "Service timeout errors"]
        assert len(timeout_issues) == 1
        assert timeout_issues[0]["severity"] == "medium"

    def test_generate_error_summary_http_5xx_errors(self):
        """HTTP 5xx errors should trigger high-severity critical issue."""
        failed_slides = [
            {
                "slide_number": 4,
                "slide_id": "s4",
                "error": "Server error",
                "service": "analytics_v3",
                "endpoint": "/v3/generate-chart",
                "error_category": "http_5xx",
                "http_status": 500,
                "suggested_action": "Check service health"
            }
        ]

        summary = self.router._generate_error_summary(failed_slides)

        assert summary["total_failures"] == 1
        assert summary["by_category"]["http_5xx"] == 1
        assert summary["by_endpoint"]["/v3/generate-chart"] == 1

        # Should have critical issue
        http_5xx_issues = [i for i in summary["critical_issues"] if "5xx" in i["issue"]]
        assert len(http_5xx_issues) == 1
        assert http_5xx_issues[0]["severity"] == "high"

    def test_generate_error_summary_mixed_errors(self):
        """Mixed error types should be properly aggregated and prioritized."""
        failed_slides = [
            # Validation error (priority 1)
            {
                "slide_number": 1,
                "error": "Missing client",
                "service": "analytics_v3",
                "error_category": "validation"
            },
            # HTTP 5xx (priority 2)
            {
                "slide_number": 2,
                "error": "Server error",
                "service": "text_service_v1.2",
                "endpoint": "/v1.2/generate",
                "error_category": "http_5xx",
                "http_status": 500
            },
            # Timeout (priority 3)
            {
                "slide_number": 3,
                "error": "Timeout",
                "service": "illustrator_v1.0",
                "endpoint": "/v1.0/pyramid/generate",
                "error_category": "timeout"
            },
            # HTTP 4xx (priority 4)
            {
                "slide_number": 4,
                "error": "Bad request",
                "service": "analytics_v3",
                "endpoint": "/v3/generate-chart",
                "error_category": "http_4xx",
                "http_status": 400
            }
        ]

        summary = self.router._generate_error_summary(failed_slides)

        assert summary["total_failures"] == 4
        assert len(summary["by_category"]) == 4
        assert len(summary["critical_issues"]) == 4
        assert len(summary["recommended_actions"]) == 4

        # Actions should be sorted by priority
        priorities = [a["priority"] for a in summary["recommended_actions"]]
        assert priorities == [1, 2, 3, 4]

    def test_error_summary_includes_failure_details(self):
        """Error summary should include full failure records for support tickets."""
        failed_slides = [
            {
                "slide_number": 1,
                "slide_id": "s1",
                "error": "Test error",
                "service": "test_service",
                "error_category": "unknown"
            }
        ]

        summary = self.router._generate_error_summary(failed_slides)

        assert "failure_details" in summary
        assert summary["failure_details"] == failed_slides


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
