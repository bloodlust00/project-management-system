import logging
import sys
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    Default handler from python logging to loguru.
    See: https://loguru.readthedocs.io/en/stable/resources/recipes.html#integrating-with-redirection-compatibility-with-standard-logging
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """
    Configures Loguru logging format and intercepts standard logging.
    """
    # Remove default loguru handler
    logger.remove()

    # Add standard output handler with customized formatting
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level="INFO"
    )

    # Intercept standard library logging messages
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Re-route specific libraries' logs to logger (e.g. uvicorn, sqlalchemy)
    for logger_name in ("uvicorn.backend", "uvicorn.access", "sqlalchemy.engine"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    logger.info("Logging successfully initialized with Loguru.")
