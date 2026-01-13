"""Tests for env module."""
import pytest
import os
from unittest.mock import patch, Mock
from src.utils.env import EnvLoader
from src.utils.exceptions import ValidationError


def test_load_env_file_exists(temp_env_file):
    """Test loading existing .env file."""
    loader = EnvLoader(env_path=str(temp_env_file))
    assert loader.get('GEMINI_API_KEY') == 'test-gemini-key'


def test_load_env_file_missing(tmp_path):
    """Test loading missing .env file."""
    loader = EnvLoader(env_path=str(tmp_path / "nonexistent.env"))
    # Should not raise error, just return None for missing keys
    assert loader.get('NONEXISTENT_KEY') is None


def test_get_existing_key(temp_env_file):
    """Test getting existing environment variable."""
    loader = EnvLoader(env_path=str(temp_env_file))
    assert loader.get('GEMINI_API_KEY') == 'test-gemini-key'


def test_get_missing_key_with_default(temp_env_file):
    """Test getting missing key with default."""
    loader = EnvLoader(env_path=str(temp_env_file))
    assert loader.get('MISSING_KEY', 'default') == 'default'


def test_require_existing_key(temp_env_file):
    """Test require() with existing key."""
    loader = EnvLoader(env_path=str(temp_env_file))
    assert loader.require('GEMINI_API_KEY') == 'test-gemini-key'


def test_require_missing_key(tmp_path):
    """Test require() with missing key."""
    env_path = tmp_path / ".env"
    env_path.write_text("")
    loader = EnvLoader(env_path=str(env_path))
    
    with pytest.raises(ValueError):
        loader.require('MISSING_KEY')


def test_validate_llm_keys_gemini(temp_env_file):
    """Test validating Gemini API key."""
    loader = EnvLoader(env_path=str(temp_env_file))
    keys = loader.validate_llm_keys('gemini')
    
    assert 'api_key' in keys
    assert keys['api_key'] == 'test-gemini-key'


def test_validate_llm_keys_perplexity(temp_env_file):
    """Test validating Perplexity API key."""
    loader = EnvLoader(env_path=str(temp_env_file))
    keys = loader.validate_llm_keys('perplexity')
    
    assert 'api_key' in keys
    assert keys['api_key'] == 'test-perplexity-key'


def test_validate_llm_keys_invalid_provider(temp_env_file):
    """Test validating invalid LLM provider."""
    loader = EnvLoader(env_path=str(temp_env_file))
    
    with pytest.raises(ValueError):
        loader.validate_llm_keys('invalid_provider')


def test_validate_search_keys_exa(temp_env_file):
    """Test validating Exa API key."""
    loader = EnvLoader(env_path=str(temp_env_file))
    keys = loader.validate_search_keys('exa')
    
    assert 'api_key' in keys
    assert keys['api_key'] == 'test-exa-key'


def test_validate_search_keys_google(temp_env_file):
    """Test validating Google API keys."""
    loader = EnvLoader(env_path=str(temp_env_file))
    keys = loader.validate_search_keys('google')
    
    assert 'api_key' in keys
    assert 'cse_id' in keys
    assert keys['api_key'] == 'test-google-key'
    assert keys['cse_id'] == 'test-cse-id'


def test_validate_search_keys_missing_cse(tmp_path):
    """Test validating Google keys with missing CSE ID."""
    env_path = tmp_path / ".env"
    env_path.write_text("GOOGLE_API_KEY=test-key\n")
    loader = EnvLoader(env_path=str(env_path))
    
    with pytest.raises(ValueError):
        loader.validate_search_keys('google')
