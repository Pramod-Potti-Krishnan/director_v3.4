"""
Registry Loader Singleton

Singleton pattern for loading and caching the unified variant registry.
Ensures registry is loaded once and reused across the application.

Version: 2.0.0
Created: 2025-11-29
"""

import os
from pathlib import Path
from typing import Optional
from src.models.variant_registry import UnifiedVariantRegistry, load_registry_from_file
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RegistryLoader:
    """
    Singleton registry loader.

    Loads the unified variant registry once and caches it for reuse.
    Thread-safe singleton implementation using class-level instance.

    Features:
    - Lazy loading (loads on first access)
    - Caching (single instance reused)
    - Configurable registry path via environment variable
    - Automatic path resolution
    - Reload capability for development/testing

    Environment Variables:
        VARIANT_REGISTRY_PATH: Path to registry JSON file
                              (default: config/unified_variant_registry.json)

    Usage:
        # Get registry instance
        loader = RegistryLoader.get_instance()
        registry = loader.get_registry()

        # Use registry
        router = UnifiedServiceRouter(registry)
        classifier = UnifiedSlideClassifier(registry)

    Development:
        # Reload registry (useful for testing)
        loader = RegistryLoader.get_instance()
        loader.reload_registry()
    """

    _instance: Optional['RegistryLoader'] = None
    _registry: Optional[UnifiedVariantRegistry] = None
    _registry_path: Optional[str] = None

    def __new__(cls):
        """Singleton pattern - ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(RegistryLoader, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'RegistryLoader':
        """
        Get singleton instance of RegistryLoader.

        Returns:
            RegistryLoader singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """
        Initialize registry loader.

        Note: Due to singleton pattern, this is called only once.
        """
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._registry = None
            self._registry_path = None

            logger.info("RegistryLoader singleton initialized")

    def get_registry(self) -> UnifiedVariantRegistry:
        """
        Get unified variant registry.

        Loads registry on first call, then returns cached instance.

        Returns:
            UnifiedVariantRegistry instance

        Raises:
            FileNotFoundError: If registry file not found
            ValueError: If registry JSON is invalid

        Example:
            loader = RegistryLoader.get_instance()
            registry = loader.get_registry()
            router = UnifiedServiceRouter(registry)
        """
        if self._registry is None:
            self._load_registry()

        return self._registry

    def _load_registry(self):
        """
        Load registry from file.

        Resolves registry path from:
        1. Environment variable VARIANT_REGISTRY_PATH
        2. Default: config/unified_variant_registry.json

        Raises:
            FileNotFoundError: If registry file not found
            ValueError: If registry JSON is invalid
        """
        registry_path = self._resolve_registry_path()

        logger.info(
            f"Loading unified variant registry",
            extra={"registry_path": registry_path}
        )

        try:
            self._registry = load_registry_from_file(registry_path)
            self._registry_path = registry_path

            logger.info(
                f"Registry loaded successfully",
                extra={
                    "total_services": len(self._registry.services),
                    "total_variants": sum(
                        len(s.variants) for s in self._registry.services.values()
                    ),
                    "version": self._registry.version
                }
            )

        except FileNotFoundError as e:
            logger.error(
                f"Registry file not found: {registry_path}",
                extra={"error": str(e)}
            )
            raise

        except Exception as e:
            logger.error(
                f"Failed to load registry: {e}",
                extra={
                    "registry_path": registry_path,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    def _resolve_registry_path(self) -> str:
        """
        Resolve path to registry file.

        Priority:
        1. Environment variable VARIANT_REGISTRY_PATH (if set)
        2. config/unified_variant_registry.json (relative to project root)
        3. Absolute path if running from different directory

        Returns:
            Absolute path to registry file

        Raises:
            FileNotFoundError: If registry file cannot be found
        """
        # Check environment variable
        env_path = os.getenv("VARIANT_REGISTRY_PATH")
        if env_path:
            if os.path.isfile(env_path):
                return os.path.abspath(env_path)
            logger.warning(
                f"VARIANT_REGISTRY_PATH set but file not found: {env_path}"
            )

        # Try relative path from current directory
        default_path = "config/unified_variant_registry.json"
        if os.path.isfile(default_path):
            return os.path.abspath(default_path)

        # Try relative to this file's directory (src/services/)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # Go up 3 levels
        registry_path = project_root / "config" / "unified_variant_registry.json"

        if registry_path.is_file():
            return str(registry_path.absolute())

        # File not found anywhere
        raise FileNotFoundError(
            f"Registry file not found. Tried:\n"
            f"  - Environment: {env_path or 'not set'}\n"
            f"  - Relative: {default_path}\n"
            f"  - Project root: {registry_path}\n"
            f"\nSet VARIANT_REGISTRY_PATH environment variable or ensure "
            f"config/unified_variant_registry.json exists."
        )

    def reload_registry(self, force: bool = False):
        """
        Reload registry from file.

        Useful for development/testing when registry changes.

        Args:
            force: If True, reloads even if registry already loaded

        Example:
            # During development
            loader = RegistryLoader.get_instance()
            loader.reload_registry(force=True)
            # Registry now reflects latest changes
        """
        if force or self._registry is not None:
            logger.info("Reloading registry")
            self._registry = None
            self._load_registry()

    def get_registry_path(self) -> Optional[str]:
        """
        Get path to currently loaded registry file.

        Returns:
            Absolute path to registry file or None if not loaded
        """
        return self._registry_path

    def get_registry_info(self) -> dict:
        """
        Get information about the loaded registry.

        Returns:
            Dict with registry metadata

        Example:
            loader = RegistryLoader.get_instance()
            info = loader.get_registry_info()
            # {
            #     "loaded": True,
            #     "path": "/path/to/config/unified_variant_registry.json",
            #     "version": "2.0.0",
            #     "total_services": 3,
            #     "total_variants": 56,
            #     "services": ["illustrator_service_v1.0", "text_service_v1.2", ...]
            # }
        """
        if self._registry is None:
            return {
                "loaded": False,
                "path": None,
                "version": None,
                "total_services": 0,
                "total_variants": 0,
                "services": []
            }

        return {
            "loaded": True,
            "path": self._registry_path,
            "version": self._registry.version,
            "total_services": len(self._registry.services),
            "total_variants": sum(
                len(s.variants) for s in self._registry.services.values()
            ),
            "services": list(self._registry.services.keys())
        }

    @classmethod
    def reset_instance(cls):
        """
        Reset singleton instance.

        WARNING: This is for testing only. Do not use in production code.

        Example:
            # In test teardown
            RegistryLoader.reset_instance()
        """
        cls._instance = None
        cls._registry = None
        cls._registry_path = None


# Convenience functions for easy access
def get_registry() -> UnifiedVariantRegistry:
    """
    Get unified variant registry (convenience function).

    Returns:
        UnifiedVariantRegistry instance

    Example:
        from src.services.registry_loader import get_registry

        registry = get_registry()
        router = UnifiedServiceRouter(registry)
    """
    loader = RegistryLoader.get_instance()
    return loader.get_registry()


def get_registry_info() -> dict:
    """
    Get registry information (convenience function).

    Returns:
        Dict with registry metadata

    Example:
        from src.services.registry_loader import get_registry_info

        info = get_registry_info()
        print(f"Loaded {info['total_variants']} variants")
    """
    loader = RegistryLoader.get_instance()
    return loader.get_registry_info()


def reload_registry(force: bool = False):
    """
    Reload registry from file (convenience function).

    Args:
        force: If True, reloads even if registry already loaded

    Example:
        from src.services.registry_loader import reload_registry

        # During development
        reload_registry(force=True)
    """
    loader = RegistryLoader.get_instance()
    loader.reload_registry(force=force)
