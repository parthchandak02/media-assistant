"""Tests for retry logic."""
import pytest
import time
from unittest.mock import Mock, patch
from src.utils.retry import retry_with_backoff


def test_retry_success_first_attempt():
    """Test retry decorator with immediate success."""
    @retry_with_backoff(max_retries=3)
    def successful_func():
        return "success"
    
    result = successful_func()
    assert result == "success"


def test_retry_success_after_retries():
    """Test retry decorator succeeding after failures."""
    call_count = [0]
    
    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("Temporary failure")
        return "success"
    
    with patch('time.sleep'):  # Speed up test
        result = flaky_func()
    
    assert result == "success"
    assert call_count[0] == 2


def test_retry_max_attempts_exceeded():
    """Test retry decorator failing after max retries."""
    @retry_with_backoff(max_retries=2, initial_delay=0.1)
    def failing_func():
        raise Exception("Always fails")
    
    with patch('time.sleep'):  # Speed up test
        with pytest.raises(Exception, match="Always fails"):
            failing_func()


def test_retry_rate_limit_handling():
    """Test retry decorator handling rate limit errors."""
    import requests
    
    call_count = [0]
    
    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def rate_limited_func():
        call_count[0] += 1
        if call_count[0] < 2:
            error = requests.exceptions.HTTPError()
            error.response = Mock(status_code=429)
            raise error
        return "success"
    
    with patch('time.sleep'):  # Speed up test
        result = rate_limited_func()
    
    assert result == "success"
