"""
Tests for Registry Loader Singleton

Comprehensive tests for registry loading, caching, and singleton pattern.

Version: 2.0.0
Created: 2025-11-29
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from src.services.registry_loader import (
    RegistryLoader,
    get_registry,
    get_registry_info,
    reload_registry
)
from src.models.variant_registry import UnifiedVariantRegistry


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before and after each test"""
    RegistryLoader.reset_instance()
    yield
    RegistryLoader.reset_instance()


@pytest.fixture
def sample_registry_file(tmp_path):
    """Create a temporary registry file for testing"""
    registry_data = {
        "version": "2.0.0",
        "last_updated": "2025-11-29",
        "total_services": 1,
        "total_variants": 2,
        "services": {
            "test_service_v1.0": {
                "enabled": True,
                "base_url": "http://localhost:8000",
                "service_type": "llm_generated",
                "endpoint_pattern": "per_variant",
                "timeout": 60,
                "variants": {
                    "test_variant_1": {
                        "variant_id": "test_variant_1",
                        "display_name": "Test Variant 1",
                        "status": "production",
                        "classification": {
                            "priority": 1,
                            "keywords": ["test", "variant", "one", "first", "initial"]
                        }
                    },
                    "test_variant_2": {
                        "variant_id": "test_variant_2",
                        "display_name": "Test Variant 2",
                        "status": "production",
                        "classification": {
                            "priority": 2,
                            "keywords": ["test", "variant", "two", "second", "next"]
                        }
                    }
                }
            }
        }
    }

    registry_file = tmp_path / "test_registry.json"
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f)

    return str(registry_file)


class TestSingletonPattern:
    """Test singleton pattern implementation"""

    def test_singleton_returns_same_instance(self):
        """Test that get_instance always returns the same instance"""
        instance1 = RegistryLoader.get_instance()
        instance2 = RegistryLoader.get_instance()

        assert instance1 is instance2

    def test_direct_instantiation_returns_singleton(self):
        """Test that direct instantiation also returns singleton"""
        instance1 = RegistryLoader()
        instance2 = RegistryLoader()

        assert instance1 is instance2

    def test_mixed_access_returns_singleton(self):
        """Test that mixed access methods return same instance"""
        instance1 = RegistryLoader.get_instance()
        instance2 = RegistryLoader()
        instance3 = RegistryLoader.get_instance()

        assert instance1 is instance2 is instance3

    def test_reset_instance_clears_singleton(self):
        """Test that reset_instance clears the singleton"""
        instance1 = RegistryLoader.get_instance()
        RegistryLoader.reset_instance()
        instance2 = RegistryLoader.get_instance()

        assert instance1 is not instance2


class TestRegistryLoading:
    """Test registry loading functionality"""

    def test_load_registry_from_environment_variable(self, sample_registry_file):
        """Test loading registry from VARIANT_REGISTRY_PATH environment variable"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()
            registry = loader.get_registry()

            assert isinstance(registry, UnifiedVariantRegistry)
            assert registry.version == "2.0.0"
            assert len(registry.services) == 1
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_load_registry_from_default_path(self):
        """Test loading registry from default path (if exists)"""
        # This test assumes the actual registry file exists
        if not os.path.isfile("config/unified_variant_registry.json"):
            pytest.skip("Default registry file not found")

        loader = RegistryLoader.get_instance()
        registry = loader.get_registry()

        assert isinstance(registry, UnifiedVariantRegistry)
        assert registry.version is not None
        assert len(registry.services) > 0

    def test_registry_loaded_only_once(self, sample_registry_file):
        """Test that registry is loaded only once and cached"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()

            # First call - loads registry
            registry1 = loader.get_registry()
            # Second call - returns cached registry
            registry2 = loader.get_registry()

            assert registry1 is registry2
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_registry_not_found_raises_error(self, tmp_path, monkeypatch):
        """Test that FileNotFoundError is raised if registry not found"""
        # Skip if default registry exists (fallback will find it)
        if os.path.isfile("config/unified_variant_registry.json"):
            pytest.skip("Default registry exists - fallback will find it")

        # Change to a directory where no default registry exists
        monkeypatch.chdir(tmp_path)
        os.environ['VARIANT_REGISTRY_PATH'] = "/nonexistent/path/registry.json"

        try:
            loader = RegistryLoader.get_instance()

            with pytest.raises(FileNotFoundError):
                loader.get_registry()
        finally:
            if 'VARIANT_REGISTRY_PATH' in os.environ:
                del os.environ['VARIANT_REGISTRY_PATH']

    def test_invalid_registry_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises appropriate error"""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        os.environ['VARIANT_REGISTRY_PATH'] = str(invalid_file)

        try:
            loader = RegistryLoader.get_instance()

            with pytest.raises(Exception):  # Could be JSONDecodeError or ValidationError
                loader.get_registry()
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']


class TestRegistryReload:
    """Test registry reload functionality"""

    def test_reload_registry_updates_cache(self, sample_registry_file, tmp_path):
        """Test that reload_registry updates the cached registry"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()

            # Load initial registry
            registry1 = loader.get_registry()
            assert registry1.version == "2.0.0"

            # Modify registry file
            modified_data = {
                "version": "3.0.0",
                "last_updated": "2025-11-30",
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
                            "test_variant_1": {
                                "variant_id": "test_variant_1",
                                "display_name": "Test Variant 1",
                                "status": "production",
                                "classification": {
                                    "priority": 1,
                                    "keywords": ["test", "modified", "reload", "updated", "changed"]
                                }
                            }
                        }
                    }
                }
            }

            with open(sample_registry_file, 'w') as f:
                json.dump(modified_data, f)

            # Reload registry
            loader.reload_registry(force=True)
            registry2 = loader.get_registry()

            assert registry2.version == "3.0.0"
            assert registry1 is not registry2
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_reload_without_force_does_nothing_if_not_loaded(self, sample_registry_file):
        """Test that reload without force doesn't load if not already loaded"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()
            # Don't call get_registry() yet

            loader.reload_registry(force=False)

            # Registry should still be None
            assert loader._registry is None
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']


class TestRegistryInfo:
    """Test registry information methods"""

    def test_get_registry_path_before_loading(self):
        """Test get_registry_path before registry is loaded"""
        loader = RegistryLoader.get_instance()
        path = loader.get_registry_path()

        assert path is None

    def test_get_registry_path_after_loading(self, sample_registry_file):
        """Test get_registry_path after registry is loaded"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()
            loader.get_registry()
            path = loader.get_registry_path()

            assert path == os.path.abspath(sample_registry_file)
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_get_registry_info_before_loading(self):
        """Test get_registry_info before registry is loaded"""
        loader = RegistryLoader.get_instance()
        info = loader.get_registry_info()

        assert info["loaded"] is False
        assert info["path"] is None
        assert info["version"] is None
        assert info["total_services"] == 0
        assert info["total_variants"] == 0
        assert info["services"] == []

    def test_get_registry_info_after_loading(self, sample_registry_file):
        """Test get_registry_info after registry is loaded"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()
            loader.get_registry()
            info = loader.get_registry_info()

            assert info["loaded"] is True
            assert info["path"] == os.path.abspath(sample_registry_file)
            assert info["version"] == "2.0.0"
            assert info["total_services"] == 1
            assert info["total_variants"] == 2
            assert "test_service_v1.0" in info["services"]
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_registry_convenience_function(self, sample_registry_file):
        """Test get_registry convenience function"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            registry = get_registry()

            assert isinstance(registry, UnifiedVariantRegistry)
            assert registry.version == "2.0.0"
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_get_registry_info_convenience_function(self, sample_registry_file):
        """Test get_registry_info convenience function"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            # Load registry first
            get_registry()

            info = get_registry_info()

            assert info["loaded"] is True
            assert info["version"] == "2.0.0"
            assert info["total_services"] == 1
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_reload_registry_convenience_function(self, sample_registry_file):
        """Test reload_registry convenience function"""
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            # Load registry
            registry1 = get_registry()

            # Reload registry
            reload_registry(force=True)
            registry2 = get_registry()

            # Should be different instances after reload
            assert registry1 is not registry2
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']


class TestPathResolution:
    """Test registry path resolution logic"""

    def test_environment_variable_takes_precedence(self, sample_registry_file, tmp_path):
        """Test that VARIANT_REGISTRY_PATH environment variable takes precedence"""
        # Create a different registry in default location
        default_registry = tmp_path / "default_registry.json"
        default_data = {
            "version": "1.0.0",
            "last_updated": "2025-01-01",
            "total_services": 0,
            "total_variants": 0,
            "services": {}
        }
        with open(default_registry, 'w') as f:
            json.dump(default_data, f)

        # Set environment variable to sample registry
        os.environ['VARIANT_REGISTRY_PATH'] = sample_registry_file

        try:
            loader = RegistryLoader.get_instance()
            registry = loader.get_registry()

            # Should load from environment variable (version 2.0.0), not default
            assert registry.version == "2.0.0"
        finally:
            del os.environ['VARIANT_REGISTRY_PATH']

    def test_fallback_to_default_when_env_path_invalid(self):
        """Test that system falls back to default registry if env path is invalid"""
        os.environ['VARIANT_REGISTRY_PATH'] = "/invalid/path/registry.json"

        try:
            # If default registry exists, it should be used as fallback
            if os.path.isfile("config/unified_variant_registry.json"):
                loader = RegistryLoader.get_instance()
                registry = loader.get_registry()

                # Should successfully load from default path despite invalid env var
                assert isinstance(registry, UnifiedVariantRegistry)
            else:
                # If no default exists, should raise FileNotFoundError
                pytest.skip("No default registry file found")
        finally:
            if 'VARIANT_REGISTRY_PATH' in os.environ:
                del os.environ['VARIANT_REGISTRY_PATH']


class TestThreadSafety:
    """Test thread safety of singleton (basic tests)"""

    def test_concurrent_instantiation_returns_same_instance(self):
        """Test that concurrent instantiation returns same instance"""
        import threading

        instances = []

        def create_instance():
            instance = RegistryLoader.get_instance()
            instances.append(instance)

        # Create multiple threads
        threads = [threading.Thread(target=create_instance) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All instances should be the same
        assert all(instance is instances[0] for instance in instances)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
