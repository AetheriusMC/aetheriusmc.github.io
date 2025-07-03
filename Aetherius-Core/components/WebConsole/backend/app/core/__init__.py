"""
Core module for WebConsole backend.

Contains essential components like configuration, dependency injection,
security, and integration layers.
"""

from .config import settings, get_settings

__all__ = ["settings", "get_settings"]