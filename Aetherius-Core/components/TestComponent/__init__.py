"""Test component for testing component system."""

import logging
from aetherius.core.component import Component

logger = logging.getLogger(__name__)


class TestComponent(Component):
    """Simple test component."""
    
    async def on_load(self):
        """Called when component is loaded."""
        logger.info("Test component loaded!")
    
    async def on_enable(self):
        """Called when component is enabled."""
        logger.info("Test component enabled!")
        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Using component logger")
    
    async def on_disable(self):
        """Called when component is disabled."""
        logger.info("Test component disabled!")
    
    async def on_unload(self):
        """Called when component is unloaded."""
        logger.info("Test component unloaded!")