"""
Logging system for the Physics Dropper addon.
"""

import sys
import traceback
import functools
from typing import Optional, Any, Dict, Callable
from datetime import datetime
from . import constants

class PhysicsDropperLogger:
    """
    Centralized logging system for the Physics Dropper addon.
    """

    def __init__(self, name: str = "PhysicsDropper", level: int = constants.DEFAULT_LOG_LEVEL):
        self.name = name
        self.level = level
        self.handlers: Dict[str, Callable] = {}

    def set_level(self, level: int) -> None:
        """Set the logging level."""
        if level in constants.LOG_LEVELS.values():
            self.level = level
        else:
            self.warning(f"Invalid log level: {level}")

    def add_handler(self, name: str, handler: Callable) -> None:
        """Add a custom log handler."""
        self.handlers[name] = handler

    def remove_handler(self, name: str) -> None:
        """Remove a log handler."""
        if name in self.handlers:
            del self.handlers[name]

    def _log(self, level: int, message: str, exception: Optional[Exception] = None) -> None:
        """Internal logging method."""
        if level < self.level:
            return

        # Get level name
        level_name = next((name for name, val in constants.LOG_LEVELS.items() if val == level), "UNKNOWN")

        # Format timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format message
        formatted_message = f"[{timestamp}] {self.name} {level_name}: {message}"

        # Add exception info if provided
        if exception:
            formatted_message += f"\nException: {str(exception)}"
            if level >= constants.LOG_LEVELS['ERROR']:
                formatted_message += f"\nTraceback: {traceback.format_exc()}"

        # Send to console
        print(formatted_message)

        # Send to custom handlers
        for handler in self.handlers.values():
            try:
                handler(level, message, exception)
            except Exception as e:
                # Prevent infinite recursion by printing directly
                print(f"[{timestamp}] {self.name} ERROR: Log handler failed: {str(e)}")

    def debug(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log debug message."""
        self._log(constants.LOG_LEVELS['DEBUG'], message, exception)

    def info(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log info message."""
        self._log(constants.LOG_LEVELS['INFO'], message, exception)

    def warning(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log warning message."""
        self._log(constants.LOG_LEVELS['WARNING'], message, exception)

    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log error message."""
        self._log(constants.LOG_LEVELS['ERROR'], message, exception)

    def critical(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log critical message."""
        self._log(constants.LOG_LEVELS['CRITICAL'], message, exception)

    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None) -> None:
        """Log function call for debugging."""
        kwargs = kwargs or {}
        message = f"Calling {func_name}"
        if args or kwargs:
            message += f" with args={args}, kwargs={kwargs}"
        self.debug(message)

    def log_performance(self, operation: str, duration: float, object_count: int = 0) -> None:
        """Log performance information."""
        message = f"Performance: {operation} took {duration:.3f}s"
        if object_count > 0:
            message += f" for {object_count} objects"
            if object_count > constants.LARGE_SCENE_THRESHOLD:
                message += " (LARGE SCENE WARNING)"
        self.info(message)

# Global logger instance
logger = PhysicsDropperLogger()

# Decorator for automatic function logging
def log_errors(func):
    """Decorator to automatically log function errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.log_function_call(func.__name__, args, kwargs)
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}", e)
            raise
    return wrapper

# Decorator for performance logging
def log_performance(operation_name: str = None):
    """Decorator to automatically log function performance."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                op_name = operation_name or func.__name__
                logger.log_performance(op_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                op_name = operation_name or func.__name__
                logger.error(f"Error in {op_name} after {duration:.3f}s", e)
                raise
        return wrapper
    return decorator

# Context manager for safe operations
class SafeOperation:
    """Context manager for safe Blender operations with logging."""

    def __init__(self, operation_name: str, logger_instance: PhysicsDropperLogger = None):
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.success = False

    def __enter__(self):
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            self.logger.debug(f"Completed operation: {self.operation_name}")
        else:
            self.logger.error(f"Failed operation: {self.operation_name}", exc_val)
        return False  # Don't suppress exceptions

# Utility functions for common Blender error patterns
def safe_object_access(obj, attribute: str, default: Any = None) -> Any:
    """Safely access object attributes with logging."""
    try:
        if obj is None:
            logger.warning(f"Attempted to access {attribute} on None object")
            return default

        if not hasattr(obj, attribute):
            logger.warning(f"Object {obj.name if hasattr(obj, 'name') else str(obj)} has no attribute {attribute}")
            return default

        return getattr(obj, attribute)

    except ReferenceError:
        logger.warning(f"Object was deleted while accessing {attribute}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error accessing {attribute}", e)
        return default

def safe_context_access(context_attr: str, default: Any = None) -> Any:
    """Safely access Blender context attributes."""
    try:
        import bpy
        context = bpy.context

        # Split nested attributes (e.g., "scene.rigidbody_world")
        attrs = context_attr.split('.')
        obj = context

        for attr in attrs:
            if hasattr(obj, attr):
                obj = getattr(obj, attr)
            else:
                logger.warning(f"Context has no attribute {context_attr}")
                return default

        return obj

    except Exception as e:
        logger.error(f"Error accessing context.{context_attr}", e)
        return default