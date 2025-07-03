"""Example plugin for testing plugin system."""

import logging
from aetherius.api.plugin import Plugin

logger = logging.getLogger(__name__)


class ExamplePlugin(Plugin):
    """Simple example plugin."""
    
    async def on_load(self):
        """Called when plugin is loaded."""
        logger.info("Example plugin loaded!")
    
    async def on_enable(self):
        """Called when plugin is enabled."""
        logger.info("Example plugin enabled!")
        if self.context:
            self.context.logger.info("Using plugin context logger")
    
    async def on_disable(self):
        """Called when plugin is disabled."""
        logger.info("Example plugin disabled!")
    
    async def on_unload(self):
        """Called when plugin is unloaded."""
        logger.info("Example plugin unloaded!")