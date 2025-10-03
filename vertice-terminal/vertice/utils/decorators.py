
"""
Command decorators for Vertice CLI.
Eliminates code duplication across all command modules.
"""
import asyncio
import functools
from typing import Type, Callable, Any
from rich.console import Console
from .output import spinner_task, print_error, print_json
from .auth import require_auth

console = Console()


def with_connector(connector_class: Type, require_authentication: bool = True):
    """
    Decorator que automatiza:
    - Autenticação
    - Criação de connector
    - Health check
    - Error handling
    - Cleanup (close)
    
    Uso:
        @with_connector(IPIntelConnector)
        async def analyze(target: str, json_output: bool = False, **kwargs):
            # connector está disponível como kwargs['connector']
            result = await kwargs['connector'].analyze_ip(target)
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Autenticação
            if require_authentication:
                require_auth()
            
            # Cria connector
            connector = connector_class()
            
            async def async_wrapper():
                try:
                    # Health check
                    with spinner_task(f"Connecting to {connector.service_name}..."):
                        if not await connector.health_check():
                            print_error(f"{connector.service_name} is not available")
                            return None
                    
                    # Injeta connector nos kwargs
                    kwargs['connector'] = connector
                    
                    # Executa função original
                    result = await func(*args, **kwargs)
                    
                    return result
                    
                except Exception as e:
                    print_error(f"Error: {str(e)}")
                    return None
                    
                finally:
                    # Cleanup
                    await connector.close()
            
            # Executa async
            return asyncio.run(async_wrapper())
        
        return wrapper
    return decorator
