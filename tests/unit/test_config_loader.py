"""Tests for config_loader module."""
import pytest
import yaml
from pathlib import Path
from src.utils.config_loader import ConfigLoader, AppConfig
from src.utils.exceptions import ConfigurationError


def test_load_config_valid(temp_config_file):
    """Test loading valid config file."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    config = loader.load_config()
    
    assert isinstance(config, AppConfig)
    assert config.llm.provider == 'gemini'
    assert config.search.provider == 'exa'
    assert config.article.media_type == 'research_magazine'


def test_load_config_missing_file():
    """Test loading non-existent config file."""
    loader = ConfigLoader(config_path="nonexistent.yaml")
    
    with pytest.raises(FileNotFoundError):
        loader.load_config()


def test_load_config_invalid_yaml(tmp_path):
    """Test loading invalid YAML."""
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("invalid: yaml: content: [")
    
    loader = ConfigLoader(config_path=str(config_path))
    
    with pytest.raises(ConfigurationError):
        loader.load_config()


def test_load_config_missing_sections(tmp_path):
    """Test loading config with missing sections."""
    config_path = tmp_path / "incomplete.yaml"
    config_path.write_text("llm:\n  provider: gemini")
    
    loader = ConfigLoader(config_path=str(config_path))
    
    with pytest.raises(ConfigurationError):
        loader.load_config()


def test_load_tones(temp_config_file):
    """Test loading tones configuration."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    tones = loader.load_tones()
    
    assert isinstance(tones, dict)
    assert 'research_magazine' in tones


def test_load_templates(temp_config_file):
    """Test loading templates configuration."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    templates = loader.load_templates()
    
    assert isinstance(templates, dict)
    assert 'research_magazine' in templates


def test_validate_media_type_valid(temp_config_file):
    """Test validating existing media type."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    
    assert loader.validate_media_type('research_magazine') is True


def test_validate_media_type_invalid(temp_config_file):
    """Test validating non-existent media type."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    
    assert loader.validate_media_type('invalid_type') is False


def test_get_tone_config(temp_config_file):
    """Test getting tone configuration."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    tone_config = loader.get_tone_config('research_magazine')
    
    assert 'tone' in tone_config
    assert 'style_guide' in tone_config


def test_get_tone_config_invalid(temp_config_file):
    """Test getting tone config for invalid media type."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    
    with pytest.raises(ConfigurationError):
        loader.get_tone_config('invalid_type')


def test_get_template_config(temp_config_file):
    """Test getting template configuration."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    template_config = loader.get_template_config('research_magazine')
    
    assert 'structure' in template_config


def test_get_template_config_invalid(temp_config_file):
    """Test getting template config for invalid media type."""
    loader = ConfigLoader(config_path=str(temp_config_file))
    
    with pytest.raises(ConfigurationError):
        loader.get_template_config('invalid_type')
