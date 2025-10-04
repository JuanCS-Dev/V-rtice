"""
Hook System
===========

Event-driven hook system for plugin integration.
"""

from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List, Optional
from enum import Enum, auto
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class HookPriority(Enum):
    """
    Hook execution priority.

    Hooks execute in order: HIGHEST → HIGH → NORMAL → LOW → LOWEST
    """
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


@dataclass
class HookContext:
    """
    Context passed to hook handlers.

    Contains:
    - event_name: Name of event being triggered
    - data: Event data
    - metadata: Additional metadata
    - stop_propagation: If True, stops calling remaining hooks
    """
    event_name: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    stop_propagation: bool = False


@dataclass
class HookRegistration:
    """
    Hook registration metadata.

    Attributes:
        event_name: Event to hook into
        handler: Callable to execute
        priority: Execution priority
        plugin_name: Name of plugin that registered this hook
    """
    event_name: str
    handler: Callable
    priority: HookPriority = HookPriority.NORMAL
    plugin_name: str = "unknown"


class HookSystem:
    """
    Central hook system for event management.

    Features:
    - Event registration and triggering
    - Priority-based execution
    - Stop propagation support
    - Hook lifecycle management

    Example:
        hook_system = HookSystem()

        # Register hook
        @hook("on_host_discovered")
        def my_handler(context):
            print(f"Host discovered: {context.data['host']}")

        # Trigger event
        hook_system.emit("on_host_discovered", host=host_obj)
    """

    def __init__(self):
        """Initialize hook system."""
        self._hooks: Dict[str, List[HookRegistration]] = {}
        self._event_log: List[Dict[str, Any]] = []

        logger.info("HookSystem initialized")

    def register(
        self,
        event_name: str,
        handler: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        plugin_name: str = "unknown",
    ) -> None:
        """
        Register hook handler for event.

        Args:
            event_name: Event name (e.g., "on_host_discovered")
            handler: Callable to execute when event triggers
            priority: Execution priority
            plugin_name: Plugin registering this hook
        """
        if event_name not in self._hooks:
            self._hooks[event_name] = []

        registration = HookRegistration(
            event_name=event_name,
            handler=handler,
            priority=priority,
            plugin_name=plugin_name,
        )

        self._hooks[event_name].append(registration)

        # Sort by priority
        self._hooks[event_name].sort(key=lambda h: h.priority.value)

        logger.debug(
            f"Hook registered: {plugin_name}.{handler.__name__} "
            f"→ {event_name} (priority: {priority.name})"
        )

    def unregister(self, event_name: str, handler: Callable) -> None:
        """
        Unregister hook handler.

        Args:
            event_name: Event name
            handler: Handler to remove
        """
        if event_name not in self._hooks:
            return

        self._hooks[event_name] = [
            h for h in self._hooks[event_name]
            if h.handler != handler
        ]

        logger.debug(f"Hook unregistered: {handler.__name__} from {event_name}")

    def unregister_plugin(self, plugin_name: str) -> None:
        """
        Unregister all hooks from a plugin.

        Args:
            plugin_name: Plugin name
        """
        for event_name in list(self._hooks.keys()):
            self._hooks[event_name] = [
                h for h in self._hooks[event_name]
                if h.plugin_name != plugin_name
            ]

        logger.info(f"All hooks unregistered for plugin: {plugin_name}")

    def emit(
        self,
        event_name: str,
        **kwargs: Any
    ) -> List[Any]:
        """
        Emit event and trigger hooks.

        Args:
            event_name: Event to trigger
            **kwargs: Event data

        Returns:
            List of results from hook handlers

        Example:
            results = hook_system.emit(
                "on_host_discovered",
                host=host_obj,
                workspace=workspace
            )
        """
        if event_name not in self._hooks:
            logger.debug(f"No hooks registered for event: {event_name}")
            return []

        context = HookContext(
            event_name=event_name,
            data=kwargs,
        )

        results = []

        logger.debug(f"Emitting event: {event_name} ({len(self._hooks[event_name])} hooks)")

        for registration in self._hooks[event_name]:
            if context.stop_propagation:
                logger.debug(f"Propagation stopped at {registration.plugin_name}")
                break

            try:
                result = registration.handler(context)
                results.append(result)

                logger.debug(
                    f"Hook executed: {registration.plugin_name}.{registration.handler.__name__}"
                )

            except Exception as e:
                logger.error(
                    f"Hook execution failed: {registration.plugin_name}.{registration.handler.__name__}: {e}",
                    exc_info=True
                )

                # Continue executing other hooks
                continue

        # Log event
        self._event_log.append({
            "event_name": event_name,
            "data": kwargs,
            "hooks_executed": len(results),
        })

        return results

    def get_hooks(self, event_name: Optional[str] = None) -> Dict[str, List[HookRegistration]]:
        """
        Get registered hooks.

        Args:
            event_name: If specified, only return hooks for this event

        Returns:
            Dict of hooks by event name
        """
        if event_name:
            return {event_name: self._hooks.get(event_name, [])}

        return self._hooks.copy()

    def get_event_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent event log.

        Args:
            limit: Max events to return

        Returns:
            List of event records
        """
        return self._event_log[-limit:]

    def clear_event_log(self) -> None:
        """Clear event log."""
        self._event_log.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get hook system statistics.

        Returns:
            Stats dict
        """
        total_handlers = sum(len(hooks) for hooks in self._hooks.values())

        # Collect unique plugin names
        active_plugins = set()
        for hooks in self._hooks.values():
            for registration in hooks:
                active_plugins.add(registration.plugin_name)

        return {
            "total_hooks": len(self._hooks),  # Number of unique event names
            "registered_handlers": total_handlers,  # Total number of handlers
            "active_plugins": len(active_plugins),  # Number of unique plugins
            "events": {
                name: len(hooks)
                for name, hooks in self._hooks.items()
            },
            "events_emitted": len(self._event_log),
        }


# Global hook system instance
_hook_system = HookSystem()


def hook(
    event_name: str,
    priority: HookPriority = HookPriority.NORMAL
) -> Callable:
    """
    Decorator to register method as hook handler.

    Args:
        event_name: Event to hook into
        priority: Execution priority

    Returns:
        Decorated function

    Example:
        class MyPlugin(BasePlugin):
            @hook("on_host_discovered")
            def enrich_host(self, context):
                host = context.data["host"]
                # Enrich host with external data
                return {"shodan_data": self.query_shodan(host.ip)}

            @hook("on_scan_complete", priority=HookPriority.HIGH)
            def send_notification(self, context):
                # Send Slack notification
                slack.notify("Scan complete!")
    """
    def decorator(func: Callable) -> Callable:
        # Store hook metadata on function
        if not hasattr(func, '_hook_metadata'):
            func._hook_metadata = []

        func._hook_metadata.append({
            "event_name": event_name,
            "priority": priority,
        })

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_hook_system() -> HookSystem:
    """
    Get global hook system instance.

    Returns:
        HookSystem instance
    """
    return _hook_system
