"""Tool Generator for LLM Agents.

Automatically generates tools from specifications, APIs, or descriptions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ToolType(Enum):
    """Types of tools."""
    FUNCTION = "function"
    API = "api"
    QUERY = "query"
    TRANSFORM = "transform"


@dataclass
class ToolSpec:
    """Tool specification."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    tool_type: ToolType = ToolType.FUNCTION

    # Parameters
    parameters: list[dict[str, Any]] = field(default_factory=list)

    # Implementation
    implementation: str = ""  # Code or API spec
    handler: Callable | None = None

    # Metadata
    version: str = "1.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedTool:
    """A generated tool."""
    spec: ToolSpec
    code: str = ""
    tests: list[str] = field(default_factory=list)
    documentation: str = ""


class ToolGenerator:
    """Generates tools from specifications.

    Features:
    - Generate from API specs
    - Generate from natural language
    - Generate from examples
    - Template-based generation
    """

    def __init__(self) -> None:
        """Initialize tool generator."""
        self._templates: dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load default templates."""
        self._templates["basic_function"] = '''def {name}({params}):
    """
    {description}

    Args:
        {param_docs}

    Returns:
        {return_type}: {return_desc}
    """
    # Implementation here
    pass
'''

        self._templates["api_endpoint"] = '''async def {name}({params}):
    """
    {description}

    Endpoint: {endpoint}
    Method: {method}
    """
    import requests

    url = f"{base_url}{endpoint}"
    response = await requests.{method}(url, params={{{param_mapping}}})
    response.raise_for_status()
    return response.json()
'''

    def generate_from_spec(
        self,
        name: str,
        description: str,
        parameters: list[dict[str, Any]],
        tool_type: ToolType = ToolType.FUNCTION,
    ) -> GeneratedTool:
        """Generate tool from specification."""
        spec = ToolSpec(
            name=name,
            description=description,
            tool_type=tool_type,
            parameters=parameters,
        )

        # Generate code from template
        template_name = "basic_function" if tool_type == ToolType.FUNCTION else "api_endpoint"
        template = self._templates.get(template_name, "")

        # Build parameter string
        param_str = ", ".join(p["name"] for p in parameters)
        param_docs = "\n        ".join(f"{p['name']}: {p.get('description', '')}" for p in parameters)

        code = template.format(
            name=name,
            description=description,
            params=param_str,
            param_docs=param_docs,
            return_type="Any",
            return_desc="Result of the operation",
            endpoint=f"/{name}",
            method="get",
            param_mapping=",".join(f"'{p['name']}': {p['name']}" for p in parameters),
            base_url="https://api.example.com",
        )

        # Generate documentation
        docs = self._generate_docs(spec)

        return GeneratedTool(
            spec=spec,
            code=code,
            documentation=docs,
        )

    def generate_from_api_spec(
        self,
        name: str,
        base_url: str,
        endpoints: list[dict[str, Any]],
    ) -> list[GeneratedTool]:
        """Generate tools from API specification."""
        tools = []

        for endpoint in endpoints:
            tool = self.generate_from_spec(
                name=endpoint.get("name", name),
                description=endpoint.get("description", ""),
                parameters=endpoint.get("parameters", []),
                tool_type=ToolType.API,
            )

            # Customize for API
            tool.code = self._templates["api_endpoint"].format(
                name=endpoint.get("name", name),
                description=endpoint.get("description", ""),
                params=", ".join(p["name"] for p in endpoint.get("parameters", [])),
                param_docs="\n        ".join(f"{p['name']}: {p.get('description', '')}" for p in endpoint.get("parameters", [])),
                return_type="dict",
                return_desc="API response",
                endpoint=endpoint.get("path", f"/{name}"),
                method=endpoint.get("method", "get").lower(),
                param_mapping=",".join(f"'{p['name']}': {p['name']}" for p in endpoint.get("parameters", [])),
                base_url=base_url,
            )

            tools.append(tool)

        return tools

    def _generate_docs(self, spec: ToolSpec) -> str:
        """Generate documentation for tool."""
        lines = [
            f"# {spec.name}",
            f"",
            f"**Type:** {spec.tool_type.value}",
            f"",
            f"**Description:** {spec.description}",
            f"",
            "## Parameters",
        ]

        for param in spec.parameters:
            required = "Required" if param.get("required") else "Optional"
            lines.append(f"- `{param['name']}` ({param.get('type', 'any')}) - {param.get('description', '')} [{required}]")

        return "\n".join(lines)

    def register_template(self, name: str, template: str) -> None:
        """Register a custom template."""
        self._templates[name] = template


# Global generator
_tool_generator: ToolGenerator | None = None


def get_tool_generator() -> ToolGenerator:
    """Get global tool generator."""
    global _tool_generator
    if _tool_generator is None:
        _tool_generator = ToolGenerator()
    return _tool_generator
