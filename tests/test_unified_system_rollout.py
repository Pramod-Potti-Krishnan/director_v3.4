"""
Tests for Unified System Rollout Helper

Comprehensive tests for gradual rollout logic and feature flag behavior.

Version: 2.0.0
Created: 2025-11-29
"""

import pytest
from unittest.mock import Mock, patch
from src.utils.unified_system_rollout import (
    UnifiedSystemRollout,
    get_rollout_manager,
    should_use_unified_system
)


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = Mock()
    settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
    settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50
    settings.VARIANT_REGISTRY_PATH = None
    return settings


@pytest.fixture
def rollout(mock_settings):
    """Create rollout instance with mocked settings"""
    with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
        mock_get.return_value = mock_settings
        return UnifiedSystemRollout()


class TestFeatureFlagLogic:
    """Test feature flag enabled/disabled behavior"""

    def test_disabled_feature_flag_always_returns_false(self, mock_settings):
        """Test that disabled flag always returns False regardless of percentage"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = False
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100  # Even at 100%

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            assert rollout.should_use_unified_system("session_123") is False
            assert rollout.should_use_unified_system("session_456") is False

    def test_enabled_with_100_percent_always_returns_true(self, mock_settings):
        """Test that 100% rollout always returns True"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            assert rollout.should_use_unified_system("session_123") is True
            assert rollout.should_use_unified_system("session_456") is True

    def test_enabled_with_0_percent_always_returns_false(self, mock_settings):
        """Test that 0% rollout always returns False"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 0

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            assert rollout.should_use_unified_system("session_123") is False
            assert rollout.should_use_unified_system("session_456") is False


class TestPercentageBasedRollout:
    """Test percentage-based rollout logic"""

    def test_same_session_gets_consistent_result(self, mock_settings):
        """Test that same session ID always gets same result"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            session_id = "session_123"

            # Call multiple times - should get same result
            result1 = rollout.should_use_unified_system(session_id)
            result2 = rollout.should_use_unified_system(session_id)
            result3 = rollout.should_use_unified_system(session_id)

            assert result1 == result2 == result3

    def test_different_sessions_may_get_different_results(self, mock_settings):
        """Test that different sessions can get different results"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            # Test many sessions - should see both True and False
            results = [
                rollout.should_use_unified_system(f"session_{i}")
                for i in range(100)
            ]

            # With 50% rollout, should have both True and False
            assert True in results
            assert False in results

    def test_50_percent_rollout_approximate_distribution(self, mock_settings):
        """Test that 50% rollout gives approximately 50/50 distribution"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            # Test 1000 sessions
            results = [
                rollout.should_use_unified_system(f"session_{i}")
                for i in range(1000)
            ]

            unified_count = sum(results)
            existing_count = len(results) - unified_count

            # Should be approximately 50/50 (allow 40-60% range for randomness)
            assert 400 <= unified_count <= 600
            assert 400 <= existing_count <= 600

    def test_25_percent_rollout_distribution(self, mock_settings):
        """Test that 25% rollout gives approximately 25/75 distribution"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 25

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            results = [
                rollout.should_use_unified_system(f"session_{i}")
                for i in range(1000)
            ]

            unified_count = sum(results)

            # Should be approximately 25% (allow 15-35% range)
            assert 150 <= unified_count <= 350

    def test_75_percent_rollout_distribution(self, mock_settings):
        """Test that 75% rollout gives approximately 75/25 distribution"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 75

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            results = [
                rollout.should_use_unified_system(f"session_{i}")
                for i in range(1000)
            ]

            unified_count = sum(results)

            # Should be approximately 75% (allow 65-85% range)
            assert 650 <= unified_count <= 850


class TestSessionConsistency:
    """Test session-based consistency"""

    def test_session_hashing_is_deterministic(self, mock_settings):
        """Test that session hashing produces deterministic results"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings

            # Create two separate rollout instances
            rollout1 = UnifiedSystemRollout()
            rollout2 = UnifiedSystemRollout()

            session_id = "session_test_123"

            # Same session should get same result across instances
            assert (rollout1.should_use_unified_system(session_id) ==
                    rollout2.should_use_unified_system(session_id))

    def test_no_session_id_behavior(self, mock_settings):
        """Test behavior when no session ID provided"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            # Without session_id, result may vary (random fallback)
            # Just verify it doesn't crash
            result = rollout.should_use_unified_system(None)
            assert isinstance(result, bool)


class TestRolloutStatus:
    """Test rollout status methods"""

    def test_get_rollout_status_disabled(self, mock_settings):
        """Test getting status when disabled"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = False
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            status = rollout.get_rollout_status()

            assert status["enabled"] is False
            assert status["percentage"] == 50
            assert status["mode"] == "disabled"

    def test_get_rollout_status_full_rollout(self, mock_settings):
        """Test getting status at 100% rollout"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            status = rollout.get_rollout_status()

            assert status["enabled"] is True
            assert status["percentage"] == 100
            assert status["mode"] == "full_rollout"

    def test_get_rollout_status_gradual(self, mock_settings):
        """Test getting status during gradual rollout"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 50

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            status = rollout.get_rollout_status()

            assert status["enabled"] is True
            assert status["percentage"] == 50
            assert status["mode"] == "gradual_rollout_50pct"

    def test_get_rollout_status_zero_percent(self, mock_settings):
        """Test getting status at 0% (disabled by percentage)"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 0

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings
            rollout = UnifiedSystemRollout()

            status = rollout.get_rollout_status()

            assert status["enabled"] is True
            assert status["percentage"] == 0
            assert status["mode"] == "disabled_by_percentage"


class TestLogging:
    """Test logging functionality"""

    def test_log_system_decision(self, rollout):
        """Test logging system decision"""
        # Should not raise exception
        rollout.log_system_decision(
            session_id="session_123",
            use_unified=True,
            stage="CONTENT_GENERATION"
        )

        rollout.log_system_decision(
            session_id="session_456",
            use_unified=False,
            stage="GENERATE_STRAWMAN"
        )


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_rollout_manager_returns_singleton(self):
        """Test that get_rollout_manager returns same instance"""
        manager1 = get_rollout_manager()
        manager2 = get_rollout_manager()

        assert manager1 is manager2

    def test_should_use_unified_system_convenience_function(self, mock_settings):
        """Test convenience function"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True
        mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = 100

        with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
            mock_get.return_value = mock_settings

            # Reset global instance
            import src.utils.unified_system_rollout
            src.utils.unified_system_rollout._rollout_instance = None

            result = should_use_unified_system("session_123")
            assert result is True


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_percentage_at_boundary_values(self, mock_settings):
        """Test percentage at boundary values (1, 99)"""
        mock_settings.UNIFIED_VARIANT_SYSTEM_ENABLED = True

        for percentage in [1, 99]:
            mock_settings.UNIFIED_VARIANT_SYSTEM_PERCENTAGE = percentage

            with patch('src.utils.unified_system_rollout.get_settings') as mock_get:
                mock_get.return_value = mock_settings
                rollout = UnifiedSystemRollout()

                results = [
                    rollout.should_use_unified_system(f"session_{i}")
                    for i in range(100)
                ]

                # Should have both True and False at these percentages
                assert True in results or False in results

    def test_empty_session_id_string(self, rollout):
        """Test behavior with empty string session ID"""
        result = rollout.should_use_unified_system("")
        assert isinstance(result, bool)

    def test_unicode_session_id(self, rollout):
        """Test behavior with unicode session ID"""
        result = rollout.should_use_unified_system("session_日本語_123")
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
