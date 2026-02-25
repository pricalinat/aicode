"""Agent Tool Registry - Tool management and function calling for LLM agents.

Based on "Orchestral AI: A Framework for Agent Orchestration" and related work.
Provides tool registration, discovery, and execution capabilities.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ToolCategory(Enum):
    """Tool categories."""
    DATA = "data"          # Data retrieval, database queries
    COMPUTATION = "computation"  # Calculations, processing
    EXTERNAL = "external"  # API calls, web requests
    FILE = "file"         # File operations
    AGENT = "agent"        # Agent-to-agent communication
    UTILITY = "utility"    # Utilities, transformations
    CUSTOM = "custom"      # User-defined


class ToolStatus(Enum):
    """Tool availability status."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    BETA = "beta"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str = ""
    required: bool = False
    default: Any = None
    enum: list[Any] | None = None


@dataclass
class ToolDefinition:
    """Tool definition with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    category: ToolCategory = ToolCategory.CUSTOM
    status: ToolStatus = ToolStatus.ACTIVE

    # Function signature
    parameters: list[ToolParameter] = field(default_factory=list)

    # Execution
    handler: Callable | None = None  # Actual function

    # Metadata
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    # Performance
    avg_execution_time_ms: int = 0
    success_rate: float = 1.0
    call_count: int = 0

    # Constraints
    requires_auth: bool = False
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def validate_parameters(self, params: dict[str, Any]) -> tuple[bool, str]:
        """Validate parameters against definition."""
        for param in self.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter: {param.name}"

            if param.name in params:
                value = params[param.name]
                if param.enum and value not in param.enum:
                    return False, f"Invalid value for {param.name}: must be one of {param.enum}"

        return True, ""

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }


class ToolRegistry:
    """Registry for managing agent tools.

    Provides:
    - Tool registration and discovery
    - Category-based organization
    - Tool validation and execution
    - Usage tracking
    """

    def __init__(self) -> None:
        """Initialize tool registry."""
        self._tools: dict[str, ToolDefinition] = {}
        self._tools_by_name: dict[str, str] = {}  # name -> id
        self._tools_by_category: dict[ToolCategory, set[str]] = {
            c: set() for c in ToolCategory
        }
        self._call_history: list[dict[str, Any]] = []

    def register(self, tool: ToolDefinition) -> ToolDefinition:
        """Register a tool.

        Args:
            tool: Tool definition

        Returns:
            Registered tool
        """
        tool.updated_at = datetime.now()
        self._tools[tool.id] = tool
        self._tools_by_name[tool.name] = tool.id
        self._tools_by_category[tool.category].add(tool.id)

        return tool

    def register_handler(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        category: ToolCategory = ToolCategory.CUSTOM,
    ) -> ToolDefinition:
        """Register a function as a tool.

        Args:
            name: Tool name
            handler: Function to register
            description: Tool description
            category: Tool category

        Returns:
            Registered tool
        """
        # Extract parameters from handler signature
        import inspect
        sig = inspect.signature(handler)
        parameters = []

        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue

            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                ann = param.annotation
                if ann == int:
                    param_type = "number"
                elif ann == float:
                    param_type = "number"
                elif ann == bool:
                    param_type = "boolean"
                elif ann == dict:
                    param_type = "object"
                elif ann == list:
                    param_type = "array"

            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None,
            ))

        tool = ToolDefinition(
            name=name,
            description=description,
            category=category,
            handler=handler,
            parameters=parameters,
        )

        return self.register(tool)

    def get(self, tool_id: str) -> ToolDefinition | None:
        """Get tool by ID."""
        return self._tools.get(tool_id)

    def get_by_name(self, name: str) -> ToolDefinition | None:
        """Get tool by name."""
        tool_id = self._tools_by_name.get(name)
        if tool_id:
            return self._tools.get(tool_id)
        return None

    def list_tools(
        self,
        category: ToolCategory | None = None,
        status: ToolStatus | None = None,
        tags: list[str] | None = None,
    ) -> list[ToolDefinition]:
        """List tools with optional filters."""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if status:
            tools = [t for t in tools if t.status == status]

        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]

        return tools

    def search(self, query: str) -> list[ToolDefinition]:
        """Search tools by name or description."""
        query_lower = query.lower()
        results = []

        for tool in self._tools.values():
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower() or
                any(query_lower in tag.lower() for tag in tool.tags)):
                results.append(tool)

        return results

    async def execute(
        self,
        tool_id: str | None = None,
        tool_name: str | None = None,
        parameters: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Execute a tool.

        Args:
            tool_id: Tool ID
            tool_name: Tool name (alternative to tool_id)
            parameters: Tool parameters
            timeout: Execution timeout in seconds

        Returns:
            Execution result
        """
        # Get tool
        if tool_id:
            tool = self._tools.get(tool_id)
        elif tool_name:
            tool = self.get_by_name(tool_name)
        else:
            return {"success": False, "error": "Either tool_id or tool_name required"}

        if not tool:
            return {"success": False, "error": f"Tool not found"}

        if tool.status != ToolStatus.ACTIVE:
            return {"success": False, "error": f"Tool is {tool.status.value}"}

        # Validate parameters
        params = parameters or {}
        valid, error = tool.validate_parameters(params)
        if not valid:
            return {"success": False, "error": error}

        # Execute
        start_time = datetime.now()
        try:
            if tool.handler:
                # Run handler with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool.handler, **params),
                    timeout=timeout
                )

                # Track success
                tool.call_count += 1
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                tool.avg_execution_time_ms = (
                    (tool.avg_execution_time_ms * (tool.call_count - 1) + execution_time)
                    / tool.call_count
                )

                self._log_call(tool, params, result, True, None)

                return {
                    "success": True,
                    "result": result,
                    "execution_time_ms": execution_time,
                }
            else:
                return {"success": False, "error": "No handler registered"}

        except asyncio.TimeoutError:
            error = f"Execution timeout after {timeout}s"
            self._log_call(tool, params, None, False, error)
            return {"success": False, "error": error}

        except Exception as e:
            error = str(e)
            self._log_call(tool, params, None, False, error)
            return {"success": False, "error": error}

    def _log_call(
        self,
        tool: ToolDefinition,
        parameters: dict[str, Any],
        result: Any,
        success: bool,
        error: str | None,
    ) -> None:
        """Log tool call."""
        self._call_history.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "parameters": parameters,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })

    def get_statistics(self) -> dict[str, Any]:
        """Get tool usage statistics."""
        total_calls = len(self._call_history)
        successful = sum(1 for c in self._call_history if c["success"])

        tool_stats = {}
        for tool in self._tools.values():
            tool_calls = [c for c in self._call_history if c["tool_id"] == tool.id]
            tool_stats[tool.name] = {
                "call_count": len(tool_calls),
                "success_rate": sum(1 for c in tool_calls if c["success"]) / len(tool_calls) if tool_calls else 0,
                "avg_execution_time_ms": tool.avg_execution_time_ms,
            }

        return {
            "total_calls": total_calls,
            "successful_calls": successful,
            "success_rate": successful / total_calls if total_calls > 0 else 0,
            "tool_count": len(self._tools),
            "by_category": {
                c.value: len(ids) for c, ids in self._tools_by_category.items()
            },
            "tools": tool_stats,
        }


# Global registry
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


# Decorator for easy tool registration

def tool(
    name: str | None = None,
    description: str = "",
    category: ToolCategory = ToolCategory.CUSTOM,
):
    """Decorator to register a function as a tool.

    Example:
        @tool(name="add", description="Add two numbers")
        def add(a: int, b: int) -> int:
            return a + b
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        registry = get_tool_registry()
        registry.register_handler(tool_name, func, description, category)
        return func
    return decorator
