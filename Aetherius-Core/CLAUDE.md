# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start
```bash
python scripts/start.py   # Development mode start
./bin/aetherius start     # Full system start
aetherius console        # Interactive console mode
```

### Testing
```bash
pytest                    # Run tests
python -m pytest -v      # Verbose testing
```

### Code Quality
```bash
ruff check .              # Lint code
black .                   # Format code
```

### Installation
```bash
pip install -e .          # Install in development mode
pip install -e ".[dev]"   # Install with dev dependencies
```

### Server Management
```bash
aetherius start              # Start Aetherius Core
aetherius server start       # Start Minecraft server with persistent console
aetherius server stop        # Stop server
aetherius server restart     # Restart server
aetherius server status      # Show server status
aetherius console            # Interactive console mode (connects to persistent console)
aetherius cmd <command>      # Send command to server
```

### Component Management
```bash
aetherius component list     # List all components
aetherius component scan     # Scan and discover components
aetherius component load     # Load all components
aetherius component enable <name>   # Enable component (uses start script or manager)
aetherius component disable <name>  # Disable component
aetherius component reload <name>   # Reload component
aetherius component info <name>     # Show component details
aetherius component stats    # Show component statistics

# Legacy compatibility commands (mapped to enable/disable)
aetherius component start <name>    # Equivalent to enable
aetherius component stop <name>     # Equivalent to disable
```

## Architecture Overview

Aetherius is a Minecraft server management engine built with Python 3.11+ using async/await patterns. The core architecture consists of:

### Core Components
- **Persistent Console Architecture** (`aetherius/core/persistent_console.py`): Main daemon managing the Minecraft server as a child process with full stdin/stdout control, avoiding RCON dependency
- **Console Client** (`aetherius/core/console_client.py`): Client interface for connecting to the persistent console daemon through Unix socket communication
- **Server State Management** (`aetherius/core/server_state.py`): Cross-process server state tracking using PID files and process monitoring
- **ConfigManager** (`aetherius/core/config.py`): Enhanced configuration management with unified API, dot notation access, and change callbacks
- **PlayerDataManager** (`aetherius/core/player_data.py`): Structured player data management with helper plugin integration for detailed game information
- **Event System** (`aetherius/core/event_manager.py`, `aetherius/core/events.py`): Async event-driven architecture for server events (player join/leave, chat, death, etc.)
- **Log Parser** (`aetherius/core/log_parser.py`): Parses Minecraft server logs and converts them to typed events
- **Command Queue** (`aetherius/core/command_queue.py`): Cross-process command execution with output capture and file-based queuing
- **Server State** (`aetherius/core/server_state.py`): Global server state management across processes
- **Output Capture** (`aetherius/core/output_capture.py`): Captures and associates server output with executed commands

### Plugin & Component System
- **Plugin Manager** (`aetherius/plugins/`): Extensible plugin system for custom functionality
- **Component Manager** (`aetherius/components/`): Component system for modular features like database and web dashboard
- **Enhanced API** (`aetherius/api/enhanced.py`): Extended functionality for official components with performance monitoring, player data, and unified configuration
- Both systems support loading, enabling/disabling, and hot-reloading

### CLI Interface
- **Main CLI** (`aetherius/cli/main.py`): Rich-based CLI using Typer with colored output and event-driven display
- **Console Mode**: Interactive console with real-time event display and command feedback
- **Cross-process Communication**: Commands work across different process instances

## Key Patterns

### Async Architecture
The entire system is built around asyncio with proper async/await patterns. Server I/O, event handling, and command execution are all asynchronous.

### Event-Driven Design
Server events (player actions, server state changes) are parsed from logs and fired through the event system. CLI handlers display these events with rich formatting.

### Configuration Management
Uses Pydantic models with YAML serialization. Default configuration is automatically created at `config.yaml`.

### Persistent Console Architecture
The persistent console system provides robust server management:
- **Process Hierarchy**: Console daemon acts as parent process of Minecraft server for complete control
- **IO Pipeline**: Direct stdin/stdout communication eliminating RCON dependency
- **Unix Socket Communication**: Client-server communication through Unix domain sockets
- **Background Operation**: Server continues running when console clients disconnect
- **Multi-client Support**: Multiple console clients can connect simultaneously
- **Real-time Output**: Live server output streaming to all connected clients
- **Command Execution**: Direct command sending through server stdin with response capture

### Cross-Process State
The system maintains server state across different CLI invocations using file-based storage and PID tracking.

### Command Output Capture
Commands sent to the server can capture their output using a timing-based correlation system that matches commands to subsequent log output.

### Performance Monitoring
Built-in performance monitoring using psutil provides detailed metrics for CPU usage, memory consumption, thread count, open files, and network connections.

### Player Data Management
Structured player data system supports detailed information including location, stats, inventory, and permissions. Integrates with AetheriusHelper.jar for deep game data access.

## Web Console Component

The web console has been separated from the core framework as an optional component:

- **Location**: `components/ComponentWeb/`
- **Architecture**: Standalone FastAPI backend with Vue.js frontend
- **Integration**: Connects to core through API and persistent console
- **Development**: Independent development and deployment
- **Usage**: Start with `python components/ComponentWeb/start_component.py`

## Development Notes

- The project uses Black for formatting (88 char line length) and Ruff for linting
- Configuration is in `pyproject.toml` with comprehensive tool settings
- Server JAR should be placed at `server/server.jar` (configurable)
- Logs are stored in `logs/` directory with rotation
- Plugin/component hot-reloading is supported for development
- The persistent console runs in background, allowing clients to connect/disconnect freely
- Web console is now a separate component, not part of the core CLI
