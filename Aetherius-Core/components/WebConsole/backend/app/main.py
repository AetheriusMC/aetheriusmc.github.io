"""
Main WebConsole FastAPI application and Aetherius component integration.
"""

import asyncio
import logging
import subprocess
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Aetherius Core imports
try:
    from aetherius.core.component import Component, ComponentInfo, WebComponent
    from aetherius.api.core import AetheriusCoreAPI
    AETHERIUS_AVAILABLE = True
except ImportError:
    # Fallback for development without Aetherius Core
    AETHERIUS_AVAILABLE = False
    Component = object
    WebComponent = object
    ComponentInfo = dict
    AetheriusCoreAPI = None

from .core.config import settings
from .core.container import container, get_container
from .middleware.simple_security import SimpleSecurityMiddleware
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limiting import RateLimitingMiddleware
from .utils.logging import setup_logging


# Configure logging
logger = logging.getLogger(__name__)


# Application lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting WebConsole application...")
    
    # Setup logging
    setup_logging(settings.logging)
    
    # Initialize services
    await initialize_services()
    
    # Register API routes
    register_routes(app)
    
    logger.info("WebConsole application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down WebConsole application...")
    await cleanup_services()
    logger.info("WebConsole application shutdown complete")


async def initialize_services():
    """Initialize application services."""
    try:
        # Initialize database
        await initialize_database()
        
        # Initialize cache
        await initialize_cache()
        
        # Initialize WebSocket manager
        await initialize_websocket_manager()
        
        # Initialize Aetherius integration
        await initialize_aetherius_integration()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def cleanup_services():
    """Cleanup application services."""
    try:
        # Dispose DI container
        await container.dispose()
        logger.info("Services cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


async def initialize_database():
    """Initialize database connection and create tables."""
    try:
        from .services.database import DatabaseService
        
        # Register database service
        container.register_singleton(DatabaseService)
        
        # Initialize database
        db_service = await container.get_service(DatabaseService)
        await db_service.initialize()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def initialize_cache():
    """Initialize cache service."""
    try:
        from .services.cache import CacheService
        
        # Register cache service
        container.register_singleton(CacheService)
        
        # Initialize cache
        cache_service = await container.get_service(CacheService)
        await cache_service.initialize()
        
        logger.info("Cache service initialized successfully")
    except Exception as e:
        logger.warning(f"Cache initialization failed, continuing without cache: {e}")
        # Don't raise, continue without cache


async def initialize_websocket_manager():
    """Initialize WebSocket manager."""
    try:
        from .websocket.manager import WebSocketManager
        
        # Register WebSocket manager
        container.register_singleton(WebSocketManager)
        
        logger.info("WebSocket manager initialized successfully")
    except Exception as e:
        logger.error(f"WebSocket manager initialization failed: {e}")
        raise


async def initialize_aetherius_integration():
    """Initialize Aetherius Core integration."""
    try:
        # 总是尝试使用真实的Aetherius适配器
        from .core.aetherius_adapter import AetheriusAdapter
        
        # Register Aetherius adapter
        container.register_singleton(AetheriusAdapter)
        
        # Initialize adapter
        adapter = await container.get_service(AetheriusAdapter)
        await adapter.initialize()
        
        logger.info("Aetherius integration initialized successfully")
        
    except Exception as e:
        logger.error(f"Aetherius integration initialization failed: {e}")
        raise


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add middleware
    add_middleware(app)
    
    # Add exception handlers
    add_exception_handlers(app)
    
    return app


def add_middleware(app: FastAPI):
    """Add middleware to the application."""
    # Simple security middleware (first)
    app.add_middleware(SimpleSecurityMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitingMiddleware)
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # CORS middleware
    if settings.cors.origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.origins,
            allow_credentials=True,
            allow_methods=settings.cors.methods,
            allow_headers=settings.cors.headers,
        )
    
    # Trusted host middleware (for production)
    if settings.is_production():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.aetherius.local"]
        )


def add_exception_handlers(app: FastAPI):
    """Add global exception handlers."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error"
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.exception(f"Unhandled exception: {exc}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error" if settings.is_production() else str(exc),
                    "type": "internal_error"
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )


def register_routes(app: FastAPI):
    """Register API routes."""
    from .api.v1 import api_router
    from .websocket.routes import router as websocket_router
    
    # API v1 routes
    app.include_router(api_router, prefix="/api/v1")
    
    # WebSocket routes
    app.include_router(websocket_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "docs_url": "/docs" if settings.debug else None
        }


# Create FastAPI app instance
app = create_app()


class WebConsoleComponent(WebComponent if AETHERIUS_AVAILABLE else object):
    """WebConsole component for Aetherius Core integration."""
    
    def __init__(self, core_instance=None, config=None):
        if AETHERIUS_AVAILABLE:
            super().__init__(core_instance, config)
        self.app: Optional[FastAPI] = None
        self.server: Optional[uvicorn.Server] = None
        self.server_task: Optional[asyncio.Task] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.startup_script_process: Optional[subprocess.Popen] = None
        self.use_startup_script: bool = True  # 使用新的启动脚本
    
    async def on_load(self) -> None:
        """Called when component is loaded."""
        logger.info("WebConsole component loading...")
        
        # Create FastAPI app
        self.app = create_app()
        
        # Store component reference in container
        container.register_instance(WebConsoleComponent, self)
        
        # Store Aetherius core reference if available
        if AETHERIUS_AVAILABLE and hasattr(self, 'core'):
            container.register_instance(AetheriusCoreAPI, self.core)
        
        logger.info("WebConsole component loaded successfully")
    
    async def on_enable(self) -> None:
        """Called when component is enabled."""
        logger.info("WebConsole component enabling...")
        
        if self.use_startup_script:
            # 使用增强的启动脚本
            await self.start_with_script()
        else:
            # 传统方式仅启动后端
            await self.start_server()
        
        logger.info("WebConsole component enabled successfully")
    
    async def on_disable(self) -> None:
        """Called when component is disabled."""
        logger.info("WebConsole component disabling...")
        
        if self.use_startup_script:
            # 停止启动脚本进程
            await self.stop_script_process()
        else:
            # 传统方式仅停止后端
            await self.stop_server()
        
        logger.info("WebConsole component disabled successfully")
    
    async def on_unload(self) -> None:
        """Called when component is unloaded."""
        logger.info("WebConsole component unloading...")
        
        # Cleanup services
        await cleanup_services()
        
        logger.info("WebConsole component unloaded successfully")
    
    async def start_server(self) -> None:
        """Start the web server."""
        if self.server_task and not self.server_task.done():
            logger.warning("Server is already running")
            return
        
        try:
            # Create server configuration
            config = uvicorn.Config(
                app=self.app,
                host=settings.host,
                port=settings.port,
                log_level="info" if settings.debug else "warning",
                access_log=settings.debug,
                reload=False,  # Disable reload in component mode
            )
            
            # Create and start server
            self.server = uvicorn.Server(config)
            
            # Run server in background task
            self.server_task = asyncio.create_task(self.server.serve())
            
            logger.info(f"WebConsole server started on {settings.host}:{settings.port}")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    async def stop_server(self) -> None:
        """Stop the web server."""
        if self.server:
            logger.info("Stopping WebConsole server...")
            self.server.should_exit = True
            
            if self.server_task:
                try:
                    await asyncio.wait_for(self.server_task, timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("Server shutdown timeout, cancelling task")
                    self.server_task.cancel()
                    try:
                        await self.server_task
                    except asyncio.CancelledError:
                        pass
            
            self.server = None
            self.server_task = None
            logger.info("WebConsole server stopped")
    
    async def start_with_script(self) -> None:
        """使用启动脚本启动前端和后端."""
        try:
            # 获取组件根目录
            component_root = Path(__file__).parent.parent.parent
            script_path = component_root / "start_component.py"
            
            if not script_path.exists():
                logger.error(f"Startup script not found: {script_path}")
                # 降级到传统模式
                await self.start_server()
                return
            
            # 检查前置条件
            if not self._check_script_prerequisites():
                logger.warning("Prerequisites not met, falling back to backend-only mode")
                await self.start_server()
                return
            
            logger.info("Starting WebConsole with enhanced startup script...")
            
            # 直接使用启动脚本启动完整服务
            self.startup_script_process = subprocess.Popen(
                ["python", str(script_path)],  # 启动完整服务（前端+后端）
                cwd=component_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待启动脚本启动
            await asyncio.sleep(5)
            
            if self.startup_script_process.poll() is None:
                logger.info("Enhanced startup script started successfully")
                logger.info("Frontend: http://localhost:3000")
                logger.info("Backend: http://localhost:8000")
                logger.info("WebConsole component using enhanced startup script!")
            else:
                stdout, stderr = self.startup_script_process.communicate()
                logger.error(f"Startup script failed: {stderr}")
                # 降级到传统模式
                logger.info("Falling back to traditional backend-only mode")
                await self.start_server()
                
        except Exception as e:
            logger.error(f"Failed to start with script: {e}")
            # 降级到传统模式
            logger.info("Falling back to traditional backend-only mode")
            await self.start_server()
    
    async def _start_frontend_only(self) -> None:
        """仅启动前端开发服务器."""
        try:
            component_root = Path(__file__).parent.parent.parent
            frontend_dir = component_root / "frontend"
            
            if not frontend_dir.exists():
                logger.warning("Frontend directory not found, skipping frontend startup")
                return
            
            logger.info("Starting frontend development server...")
            
            # 启动前端开发服务器
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待前端服务器启动
            await asyncio.sleep(5)
            
            if self.frontend_process.poll() is None:
                logger.info("Frontend development server started successfully")
                logger.info("Frontend: http://localhost:3000")
                logger.info("Backend: http://localhost:8000")
            else:
                stdout, stderr = self.frontend_process.communicate()
                logger.error(f"Frontend server failed to start: {stderr}")
                
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
    
    def _check_script_prerequisites(self) -> bool:
        """检查启动脚本的前置条件."""
        # 检查Node.js和npm
        if not shutil.which("node"):
            logger.warning("Node.js not found")
            return False
            
        if not shutil.which("npm"):
            logger.warning("npm not found")
            return False
            
        # 检查前端目录和依赖
        component_root = Path(__file__).parent.parent.parent
        frontend_dir = component_root / "frontend"
        
        if not frontend_dir.exists():
            logger.warning("Frontend directory not found")
            return False
            
        if not (frontend_dir / "node_modules").exists():
            logger.info("Frontend dependencies not found, will install automatically")
            # 可以尝试自动安装，或者返回False让用户手动安装
            
        return True
    
    async def stop_script_process(self) -> None:
        """停止启动脚本和相关进程."""
        try:
            # 停止启动脚本进程（它会自动处理前端和后端的关闭）
            if self.startup_script_process and self.startup_script_process.poll() is None:
                logger.info("Stopping enhanced startup script...")
                self.startup_script_process.terminate()
                await asyncio.sleep(3)
                if self.startup_script_process.poll() is None:
                    logger.warning("Force killing startup script process...")
                    self.startup_script_process.kill()
                self.startup_script_process = None
                logger.info("Enhanced startup script stopped")
            
            # 清理前端进程引用
            if self.frontend_process:
                self.frontend_process = None
            
            # 如果使用了传统模式作为后备，也要停止它
            if self.server:
                await self.stop_server()
            
        except Exception as e:
            logger.error(f"Error stopping script process: {e}")


# Component info for Aetherius discovery
component_info = ComponentInfo(
    name="webconsole",
    display_name="Aetherius WebConsole",
    description="Enterprise-grade web management console",
    version="2.0.0",
    author="Aetherius Team",
    dependencies=["aetherius-core>=1.0.0"],
    permissions=[
        "aetherius.console.read",
        "aetherius.console.execute",
        "aetherius.status.read",
        "aetherius.players.read",
        "aetherius.players.manage",
        "aetherius.files.read",
        "aetherius.files.write",
        "aetherius.config.read",
        "aetherius.config.write",
        "aetherius.server.control",
        "aetherius.monitoring.read",
        "aetherius.events.listen"
    ]
) if AETHERIUS_AVAILABLE else {}


# Development server entry point
if __name__ == "__main__":
    # Run in development mode
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="debug" if settings.debug else "info"
    )