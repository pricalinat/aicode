"""Plugin system for dynamic agent loading."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Type

from .agent import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a loaded plugin."""
    name: str
    version: str | None = None
    author: str | None = None
    description: str | None = None
    entry_point: str | None = None


class Plugin(ABC):
    """Base class for agent plugins."""
    
    @abstractmethod
    def get_agents(self) -> list[Type[BaseAgent]]:
        """Return list of agent classes provided by this plugin."""
        pass
    
    @abstractmethod
    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the plugin with configuration."""
        pass


class PluginLoader:
    """Dynamic plugin loader for agents.
    
    Supports:
    - Loading agents from Python files
    - Loading agents from installed packages
    - Hot-reloading of plugins
    """
    
    def __init__(self) -> None:
        self._loaded_plugins: dict[str, Plugin] = {}
        self._agent_factories: dict[str, Callable[[], BaseAgent]] = {}
    
    def load_from_file(self, file_path: Path, module_name: str | None = None) -> list[Type[BaseAgent]]:
        """Load agents from a Python file."""
        if module_name is None:
            module_name = f"plugin_{file_path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find agent classes in the module
        agent_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                agent_classes.append(obj)
                self._agent_factories[obj.name] = lambda cls=obj: cls()
                logger.info(f"Loaded agent: {obj.name} from {file_path}")
        
        return agent_classes
    
    def load_from_package(self, package_name: str) -> list[Type[BaseAgent]]:
        """Load agents from an installed package."""
        try:
            module = importlib.import_module(package_name)
        except ImportError as e:
            raise ImportError(f"Cannot import package {package_name}: {e}")
        
        agent_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                agent_classes.append(obj)
                self._agent_factories[obj.name] = lambda cls=obj: cls()
                logger.info(f"Loaded agent: {obj.name} from package {package_name}")
        
        return agent_classes
    
    def register_plugin(self, name: str, plugin: Plugin, config: dict[str, Any] | None = None) -> None:
        """Register a plugin instance."""
        plugin.initialize(config)
        self._loaded_plugins[name] = plugin
        
        for agent_class in plugin.get_agents():
            self._agent_factories[agent_class.name] = lambda cls=agent_class: cls()
            logger.info(f"Registered agent: {agent_class.name} from plugin {name}")
    
    def create_agent(self, agent_name: str) -> BaseAgent | None:
        """Create an agent instance by name."""
        factory = self._agent_factories.get(agent_name)
        if factory is None:
            return None
        return factory()
    
    def list_agents(self) -> list[str]:
        """List all available agent names."""
        return list(self._agent_factories.keys())
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin and its agents."""
        if name not in self._loaded_plugins:
            return False
        
        plugin = self._loaded_plugins[name]
        for agent_class in plugin.get_agents():
            self._agent_factories.pop(agent_class.name, None)
        
        del self._loaded_plugins[name]
        logger.info(f"Unloaded plugin: {name}")
        return True


class PluginManager:
    """High-level plugin manager with discovery and lifecycle management."""
    
    def __init__(self, loader: PluginLoader | None = None) -> None:
        self.loader = loader or PluginLoader()
        self._configs: dict[str, dict[str, Any]] = {}
    
    def discover_plugins(self, plugin_dir: Path) -> list[str]:
        """Discover plugins in a directory."""
        discovered = []
        
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return discovered
        
        for file_path in plugin_dir.glob("*.py"):
            if file_path.stem.startswith("_"):
                continue
            try:
                self.loader.load_from_file(file_path)
                discovered.append(file_path.stem)
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")
        
        return discovered
    
    def load_with_config(self, name: str, config: dict[str, Any]) -> list[Type[BaseAgent]]:
        """Load a plugin with configuration."""
        self._configs[name] = config
        
        try:
            return self.loader.load_from_package(name)
        except ImportError:
            plugin_path = Path(name)
            if plugin_path.exists():
                return self.loader.load_from_file(plugin_path)
            raise
    
    def reload(self, name: str) -> list[Type[BaseAgent]]:
        """Reload a plugin."""
        if name in self._configs:
            config = self._configs[name]
            self.unload(name)
            return self.load_with_config(name, config)
        return []
    
    def unload(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._configs:
            del self._configs[name]
        
        if self.loader.unload_plugin(name):
            return True
        
        return False
    
    def get_agent(self, agent_name: str) -> BaseAgent | None:
        """Get an agent instance by name."""
        return self.loader.create_agent(agent_name)
    
    def list_available_agents(self) -> list[str]:
        """List all available agent names."""
        return self.loader.list_agents()
