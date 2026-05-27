"""Generic plugin registry with discovery and lifecycle management."""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class PluginRegistry(Generic[T]):
    """A registry of plugin implementations of a given Protocol.

    Plugins are registered by a string key and instantiated lazily on first
    access via ``get()``.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._factories: dict[str, Callable[[], T]] = {}
        self._instances: dict[str, T] = {}

    def register(self, key: str, factory: Callable[[], T]) -> None:
        """Register a plugin under *key*.

        ``factory`` will be called exactly once, on first ``get(key)``.
        """
        if key in self._factories:
            raise ValueError(f"Plugin {key!r} already registered in {self._name}")
        self._factories[key] = factory

    def register_class(self, key: str, cls: type[T]) -> None:
        """Register a no-arg instantiable class."""
        self.register(key, cls)

    def get(self, key: str) -> T:
        """Return the singleton instance for *key*."""
        if key not in self._instances:
            if key not in self._factories:
                raise KeyError(f"No plugin {key!r} registered in {self._name}; available: {self.list()}")
            self._instances[key] = self._factories[key]()
        return self._instances[key]

    def list(self) -> list[str]:
        return list(self._factories.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._factories

    def __len__(self) -> int:
        return len(self._factories)


class PluginLoader:
    """Discovers and loads plugins via Python entry points or file paths."""

    @staticmethod
    def discover(group: str = "promptcompiler.plugins") -> None:
        """Discover plugins registered as console_scripts entry points."""
        for entry in importlib.metadata.entry_points(group=group):
            cls = entry.load()
            # Convention: the class registers itself at import time.
            # We just trigger the import.
            pass

    @staticmethod
    def load_from_path(path: str) -> None:
        """Execute a Python file so its module-level registrations run."""
        spec = importlib.util.spec_from_file_location("_plugin_loader", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin from {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
