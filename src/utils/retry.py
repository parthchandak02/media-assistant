"""Retry logic with exponential backoff for API calls."""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
import requests

from .exceptions import MediaArticleWriterError

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    retryable_status_codes: Optional[Tuple[int, ...]] = None
):
    """Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        retryable_exceptions: Tuple of exception types to retry on
        retryable_status_codes: Tuple of HTTP status codes to retry on (e.g., 429, 500)
        
    Returns:
        Decorated function
    """
    if retryable_exceptions is None:
        retryable_exceptions = (
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        )
    
    if retryable_status_codes is None:
        retryable_status_codes = (429, 500, 502, 503, 504)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Check if result is a requests.Response with retryable status code
                    if isinstance(result, requests.Response):
                        if result.status_code in retryable_status_codes:
                            if attempt < max_retries:
                                logger.warning(
                                    f"Received status code {result.status_code} on attempt {attempt + 1}. "
                                    f"Retrying in {delay:.2f}s..."
                                )
                                time.sleep(delay)
                                delay = min(delay * backoff_factor, max_delay)
                                continue
                            else:
                                result.raise_for_status()
                    
                    # Success - reset delay for next call
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise
                        
                except Exception as e:
                    # Non-retryable exception - raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise
            
            # Should not reach here, but handle just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Function {func.__name__} failed after {max_retries + 1} attempts")
        
        return wrapper
    return decorator
