"""
Tool Protocol - Standard Interface for MAXIMUS Tools

This module defines the standard protocol for tools that can be used by MAXIMUS.
All subordinate services expose their capabilities as tools following this protocol.

Key Features:
- Standardized tool interface
- Parameter validation
- Result serialization
- Error handling
- Metrics tracking

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ToolStatus(str, Enum):
    """Tool execution status."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PENDING = "pending"


class ToolParameterType(str, Enum):
    """Supported parameter types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class ToolParameter(BaseModel):
    """
    Tool parameter definition.

    Attributes:
        name: Parameter name
        type: Parameter type
        description: Human-readable description
        required: Whether parameter is required
        default: Default value if not provided
        enum: List of allowed values (optional)
    """

    name: str = Field(..., description="Parameter name")
    type: ToolParameterType = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any | None = Field(default=None, description="Default value")
    enum: list[Any] | None = Field(default=None, description="Allowed values")


class ToolInvocationRequest(BaseModel):
    """
    Tool invocation request.

    Attributes:
        tool_name: Name of the tool to invoke
        parameters: Tool parameters
        request_id: Unique request identifier
        source_service: Service requesting the tool
        timeout_seconds: Execution timeout
    """

    tool_name: str = Field(..., description="Tool name")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    request_id: str | None = Field(default=None, description="Request ID")
    source_service: str | None = Field(
        default="maximus_core_service", description="Source service"
    )
    timeout_seconds: int | None = Field(default=300, description="Execution timeout")

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout is reasonable."""
        if v is not None and (v <= 0 or v > 3600):
            raise ValueError("Timeout must be between 1 and 3600 seconds")
        return v


class ToolInvocationResponse(BaseModel):
    """
    Tool invocation response.

    Attributes:
        status: Execution status
        result: Tool result (if successful)
        error: Error message (if failed)
        execution_time_ms: Execution time in milliseconds
        request_id: Original request ID
        timestamp: Response timestamp
    """

    status: ToolStatus = Field(..., description="Execution status")
    result: dict[str, Any] | None = Field(default=None, description="Tool result")
    error: str | None = Field(default=None, description="Error message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    request_id: str | None = Field(default=None, description="Request ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Response timestamp",
    )

    @field_validator("error")
    @classmethod
    def error_requires_failed_status(cls, v, info):
        """Ensure error is only set when status is failed."""
        # In Pydantic V2, use info.data instead of values
        status = info.data.get("status") if hasattr(info, "data") else None
        if v and status not in [
            ToolStatus.FAILED,
            ToolStatus.TIMEOUT,
            ToolStatus.CANCELLED,
        ]:
            raise ValueError("Error message only valid for failed status")
        return v


class ToolBase(ABC):
    """
    Base class for all MAXIMUS tools.

    All tools must inherit from this class and implement the execute() method.
    Tools are automatically registered with MAXIMUS and can be invoked via API.

    Attributes:
        name: Unique tool identifier
        description: Human-readable description
        parameters: List of parameter definitions
        category: Tool category
        service_name: Service providing this tool
    """

    # Prometheus metrics
    invocations_total = Counter(
        "tool_invocations_total",
        "Total tool invocations",
        ["tool_name", "status", "service"],
    )

    invocation_duration = Histogram(
        "tool_invocation_duration_seconds",
        "Tool invocation duration",
        ["tool_name", "service"],
    )

    def __init__(
        self,
        name: str,
        description: str,
        parameters: list[ToolParameter],
        category: str,
        service_name: str,
    ):
        """
        Initialize tool.

        Args:
            name: Unique tool identifier
            description: Human-readable description
            parameters: Parameter definitions
            category: Tool category
            service_name: Service providing this tool
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.category = category
        self.service_name = service_name

        logger.debug(f"Initialized tool '{name}' in service '{service_name}'")

    @abstractmethod
    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the tool with given parameters.

        This method must be implemented by each tool. It should:
        1. Validate parameters
        2. Perform the tool's operation
        3. Return result dict

        Args:
            parameters: Tool parameters

        Returns:
            Result dict with tool output

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If execution fails
        """
        pass

    async def invoke(self, request: ToolInvocationRequest) -> ToolInvocationResponse:
        """
        Invoke the tool (wrapper around execute with metrics and error handling).

        Args:
            request: Tool invocation request

        Returns:
            Tool invocation response
        """
        start_time = datetime.utcnow()

        try:
            # Validate parameters
            self._validate_parameters(request.parameters)

            # Execute tool
            with self.invocation_duration.labels(
                tool_name=self.name, service=self.service_name
            ).time():
                result = await self.execute(request.parameters)

            # Calculate execution time
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Update metrics
            self.invocations_total.labels(
                tool_name=self.name,
                status=ToolStatus.SUCCESS.value,
                service=self.service_name,
            ).inc()

            return ToolInvocationResponse(
                status=ToolStatus.SUCCESS,
                result=result,
                execution_time_ms=execution_time_ms,
                request_id=request.request_id,
            )

        except ValueError as e:
            # Parameter validation error
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.invocations_total.labels(
                tool_name=self.name,
                status=ToolStatus.FAILED.value,
                service=self.service_name,
            ).inc()

            logger.error(f"Tool '{self.name}' parameter validation failed: {e}")

            return ToolInvocationResponse(
                status=ToolStatus.FAILED,
                error=f"Parameter validation error: {str(e)}",
                execution_time_ms=execution_time_ms,
                request_id=request.request_id,
            )

        except Exception as e:
            # Execution error
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.invocations_total.labels(
                tool_name=self.name,
                status=ToolStatus.FAILED.value,
                service=self.service_name,
            ).inc()

            logger.error(f"Tool '{self.name}' execution failed: {e}", exc_info=True)

            return ToolInvocationResponse(
                status=ToolStatus.FAILED,
                error=f"Execution error: {str(e)}",
                execution_time_ms=execution_time_ms,
                request_id=request.request_id,
            )

    def _validate_parameters(self, parameters: dict[str, Any]) -> None:
        """
        Validate parameters against tool definition.

        Args:
            parameters: Parameters to validate

        Raises:
            ValueError: If validation fails
        """
        for param in self.parameters:
            # Check required parameters
            if param.required and param.name not in parameters:
                raise ValueError(f"Required parameter '{param.name}' missing")

            # Check parameter exists
            if param.name in parameters:
                value = parameters[param.name]

                # Check enum values
                if param.enum and value not in param.enum:
                    raise ValueError(
                        f"Parameter '{param.name}' must be one of {param.enum}, got {value}"
                    )

                # Basic type checking
                if param.type == ToolParameterType.STRING and not isinstance(
                    value, str
                ):
                    raise ValueError(f"Parameter '{param.name}' must be string")
                elif param.type == ToolParameterType.INTEGER and not isinstance(
                    value, int
                ):
                    raise ValueError(f"Parameter '{param.name}' must be integer")
                elif param.type == ToolParameterType.BOOLEAN and not isinstance(
                    value, bool
                ):
                    raise ValueError(f"Parameter '{param.name}' must be boolean")
                elif param.type == ToolParameterType.ARRAY and not isinstance(
                    value, list
                ):
                    raise ValueError(f"Parameter '{param.name}' must be array")
                elif param.type == ToolParameterType.OBJECT and not isinstance(
                    value, dict
                ):
                    raise ValueError(f"Parameter '{param.name}' must be object")

    def get_manifest(self) -> dict[str, Any]:
        """
        Get tool manifest for registration with MAXIMUS.

        Returns:
            Tool manifest dict
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "service": self.service_name,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "enum": p.enum,
                }
                for p in self.parameters
            ],
        }
