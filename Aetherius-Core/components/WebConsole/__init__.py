"""
Aetherius WebConsole Component

Enterprise-grade web management console for Aetherius Core.
Provides a modern, feature-rich interface for server administration.
"""

__version__ = "2.0.0"
__author__ = "Aetherius Team"
__email__ = "dev@aetherius.mc"

from .backend.app.main import WebConsoleComponent

# Export the main component class for Aetherius to discover
__all__ = ["WebConsoleComponent"]