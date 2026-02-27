"""
Structured logging configuration for Jamaah.in.
"""
import structlog
import logging


def configure_logging(app_name: str = "jamaah-in", log_level: str = "INFO"):
    """Configure structured logging for application."""
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.devel.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Get logger
    logger = structlog.get_logger()
    logger.info("Logging configured", app_name=app_name, level=log_level)
    
    return logger


def get_logger(name: str = None):
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestIdMiddleware:
    """Middleware to add X-Request-ID to logs."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract or generate request ID
            from uuid import uuid4
            headers = dict(scope.get("headers", []))
            request_id = headers.get(b"x-request-id", uuid4().hex.decode())
            
            # Add to structlog context
            structlog.contextvars.bind_contextvars(request_id=request_id)
        
        await self.app(scope, receive, send)
