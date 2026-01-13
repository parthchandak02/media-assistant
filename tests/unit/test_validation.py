"""Tests for validation module."""
import pytest
from src.utils.validation import (
    validate_topic,
    validate_media_type,
    validate_length,
    validate_max_results
)
from src.utils.exceptions import ValidationError


def test_validate_topic_valid():
    """Test validating valid topic."""
    validate_topic("Valid topic string")


def test_validate_topic_empty():
    """Test validating empty topic."""
    with pytest.raises(ValidationError):
        validate_topic("")
    
    with pytest.raises(ValidationError):
        validate_topic("   ")


def test_validate_topic_too_short():
    """Test validating topic that's too short."""
    with pytest.raises(ValidationError):
        validate_topic("ab")


def test_validate_media_type_valid():
    """Test validating valid media type."""
    valid_types = ['research_magazine', 'scientific_journal']
    validate_media_type('research_magazine', valid_types)


def test_validate_media_type_invalid():
    """Test validating invalid media type."""
    valid_types = ['research_magazine', 'scientific_journal']
    
    with pytest.raises(ValidationError):
        validate_media_type('invalid_type', valid_types)


def test_validate_media_type_empty():
    """Test validating empty media type."""
    valid_types = ['research_magazine']
    
    with pytest.raises(ValidationError):
        validate_media_type('', valid_types)


def test_validate_length_valid():
    """Test validating valid length."""
    validate_length('short')
    validate_length('medium')
    validate_length('long')


def test_validate_length_invalid():
    """Test validating invalid length."""
    with pytest.raises(ValidationError):
        validate_length('extra_long')
    
    with pytest.raises(ValidationError):
        validate_length('')


def test_validate_max_results_valid():
    """Test validating valid max_results."""
    validate_max_results(1)
    validate_max_results(10)
    validate_max_results(100)


def test_validate_max_results_invalid():
    """Test validating invalid max_results."""
    with pytest.raises(ValidationError):
        validate_max_results(0)
    
    with pytest.raises(ValidationError):
        validate_max_results(-1)
    
    with pytest.raises(ValidationError):
        validate_max_results(101)
    
    with pytest.raises(ValidationError):
        validate_max_results("10")  # Not an integer
