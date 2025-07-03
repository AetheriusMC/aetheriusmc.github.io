"""
Dependency Injection Container for WebConsole Backend.

This module provides a centralized dependency injection container
that manages service lifetimes and dependencies.
"""

import asyncio
from typing import TypeVar, Type, Callable, Any, Dict, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum
import inspect
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime enumeration."""
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class ServiceDescriptor:
    """Service descriptor containing registration information."""
    
    def __init__(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Optional[Callable] = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance: Optional[T] = None


class ServiceScope:
    """Service scope for managing scoped services."""
    
    def __init__(self, container: 'DIContainer'):
        self.container = container
        self.scoped_services: Dict[Type, Any] = {}
        self._disposed = False
    
    async def get_service(self, service_type: Type[T]) -> T:
        """Get service from this scope."""
        if self._disposed:
            raise RuntimeError("Service scope has been disposed")
        
        descriptor = self.container._services.get(service_type)
        if not descriptor:
            raise ValueError(f"Service {service_type.__name__} not registered")
        
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type not in self.scoped_services:
                self.scoped_services[service_type] = await self.container._create_instance(descriptor, self)
            return self.scoped_services[service_type]
        
        return await self.container.get_service(service_type)
    
    async def dispose(self):
        """Dispose scoped services."""
        if self._disposed:
            return
        
        for service in self.scoped_services.values():
            if hasattr(service, 'dispose') and callable(service.dispose):
                try:
                    if inspect.iscoroutinefunction(service.dispose):
                        await service.dispose()
                    else:
                        service.dispose()
                except Exception as e:
                    logger.warning(f"Error disposing service: {e}")
        
        self.scoped_services.clear()
        self._disposed = True


class DIContainer:
    """Dependency Injection Container."""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._building: set = set()
    
    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T], T, None] = None
    ) -> 'DIContainer':
        """Register a singleton service."""
        impl = implementation or service_type
        descriptor = ServiceDescriptor(service_type, impl, ServiceLifetime.SINGLETON)
        self._services[service_type] = descriptor
        return self
    
    def register_scoped(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T], None] = None
    ) -> 'DIContainer':
        """Register a scoped service."""
        impl = implementation or service_type
        descriptor = ServiceDescriptor(service_type, impl, ServiceLifetime.SCOPED)
        self._services[service_type] = descriptor
        return self
    
    def register_transient(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T], None] = None
    ) -> 'DIContainer':
        """Register a transient service."""
        impl = implementation or service_type
        descriptor = ServiceDescriptor(service_type, impl, ServiceLifetime.TRANSIENT)
        self._services[service_type] = descriptor
        return self
    
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> 'DIContainer':
        """Register a service with a factory function."""
        descriptor = ServiceDescriptor(service_type, factory, lifetime, factory)
        self._services[service_type] = descriptor
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """Register a service instance."""
        descriptor = ServiceDescriptor(service_type, instance, ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor
        self._singletons[service_type] = instance
        return self
    
    async def get_service(self, service_type: Type[T]) -> T:
        """Get service instance."""
        descriptor = self._services.get(service_type)
        if not descriptor:
            raise ValueError(f"Service {service_type.__name__} not registered")
        
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type not in self._singletons:
                self._singletons[service_type] = await self._create_instance(descriptor)
            return self._singletons[service_type]
        
        return await self._create_instance(descriptor)
    
    def create_scope(self) -> ServiceScope:
        """Create a new service scope."""
        return ServiceScope(self)
    
    async def _create_instance(self, descriptor: ServiceDescriptor, scope: Optional[ServiceScope] = None):
        """Create service instance."""
        if descriptor.service_type in self._building:
            raise RuntimeError(f"Circular dependency detected for {descriptor.service_type.__name__}")
        
        self._building.add(descriptor.service_type)
        try:
            if descriptor.instance is not None:
                return descriptor.instance
            
            if descriptor.factory:
                return await self._invoke_factory(descriptor.factory, scope)
            
            implementation = descriptor.implementation
            
            if inspect.isclass(implementation):
                return await self._create_class_instance(implementation, scope)
            elif callable(implementation):
                return await self._invoke_factory(implementation, scope)
            else:
                return implementation
        finally:
            self._building.discard(descriptor.service_type)
    
    async def _create_class_instance(self, cls: Type[T], scope: Optional[ServiceScope] = None) -> T:
        """Create class instance with dependency injection."""
        # Get constructor signature
        sig = inspect.signature(cls.__init__)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation == inspect.Parameter.empty:
                raise ValueError(f"Parameter {param_name} in {cls.__name__} has no type annotation")
            
            # Get service from container or scope
            if scope:
                parameters[param_name] = await scope.get_service(param.annotation)
            else:
                parameters[param_name] = await self.get_service(param.annotation)
        
        return cls(**parameters)
    
    async def _invoke_factory(self, factory: Callable, scope: Optional[ServiceScope] = None):
        """Invoke factory function with dependency injection."""
        sig = inspect.signature(factory)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            if param.annotation == inspect.Parameter.empty:
                continue
            
            # Get service from container or scope
            if scope:
                parameters[param_name] = await scope.get_service(param.annotation)
            else:
                parameters[param_name] = await self.get_service(param.annotation)
        
        result = factory(**parameters)
        
        # Handle async factories
        if inspect.iscoroutine(result):
            return await result
        
        return result
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if service is registered."""
        return service_type in self._services
    
    async def dispose(self):
        """Dispose container and all singleton services."""
        for service in self._singletons.values():
            if hasattr(service, 'dispose') and callable(service.dispose):
                try:
                    if inspect.iscoroutinefunction(service.dispose):
                        await service.dispose()
                    else:
                        service.dispose()
                except Exception as e:
                    logger.warning(f"Error disposing service: {e}")
        
        self._singletons.clear()
        self._services.clear()


# Dependency injection decorators
def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """Mark a class as injectable with specified lifetime."""
    def decorator(cls: Type[T]) -> Type[T]:
        cls._injectable_lifetime = lifetime
        return cls
    return decorator


def singleton(cls: Type[T] = None) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """Mark a class as singleton."""
    def decorator(cls: Type[T]) -> Type[T]:
        cls._injectable_lifetime = ServiceLifetime.SINGLETON
        return cls
    
    if cls is not None:
        return decorator(cls)
    return decorator


def scoped(cls: Type[T] = None) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """Mark a class as scoped."""
    def decorator(cls: Type[T]) -> Type[T]:
        cls._injectable_lifetime = ServiceLifetime.SCOPED
        return cls
    
    if cls is not None:
        return decorator(cls)
    return decorator


def transient(cls: Type[T] = None) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """Mark a class as transient."""
    def decorator(cls: Type[T]) -> Type[T]:
        cls._injectable_lifetime = ServiceLifetime.TRANSIENT
        return cls
    
    if cls is not None:
        return decorator(cls)
    return decorator


# Global container instance
container = DIContainer()


def get_container() -> DIContainer:
    """Get the global DI container."""
    return container