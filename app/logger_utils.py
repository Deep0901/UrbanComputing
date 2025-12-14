# Logging Configuration and Utilities

import logging
import sys
from datetime import datetime

# ============================================================================
# Logger Setup
# ============================================================================

def setup_logger(name, level=logging.INFO):
    """
    Setup a logger with both file and console handlers.
    
    Args:
        name (str): Logger name
        level (int): Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    log_filename = f"logs/energy_explain_{datetime.now().strftime('%Y%m%d')}.log"
    try:
        import os
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    return logger


# ============================================================================
# Error Handlers
# ============================================================================

class EnergyExplainException(Exception):
    """Base exception class for the application."""
    pass


class DataLoadError(EnergyExplainException):
    """Raised when data loading fails."""
    pass


class ENTSOEAPIError(EnergyExplainException):
    """Raised when ENTSOE API call fails."""
    pass


class ModelTrainingError(EnergyExplainException):
    """Raised when model training fails."""
    pass


class FuzzyAnalysisError(EnergyExplainException):
    """Raised when fuzzy analysis fails."""
    pass


# ============================================================================
# Utility Functions
# ============================================================================

def log_exception(logger, exception, context=""):
    """
    Log exception with context information.
    
    Args:
        logger (logging.Logger): Logger instance
        exception (Exception): Exception to log
        context (str): Additional context information
    """
    error_msg = f"Error: {str(exception)}"
    if context:
        error_msg += f" [Context: {context}]"
    
    logger.error(error_msg, exc_info=True)


def safe_operation(logger, operation_name, operation_func, *args, **kwargs):
    """
    Execute operation with error handling and logging.
    
    Args:
        logger (logging.Logger): Logger instance
        operation_name (str): Name of operation for logging
        operation_func (callable): Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Result of operation_func or None if error occurred
    """
    try:
        logger.info(f"Starting operation: {operation_name}")
        result = operation_func(*args, **kwargs)
        logger.info(f"Completed operation: {operation_name}")
        return result
    except Exception as e:
        log_exception(logger, e, operation_name)
        return None


# Get default logger
logger = setup_logger(__name__)
