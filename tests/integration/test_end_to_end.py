"""End-to-end tests for CLI execution."""
import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner
from src.main import main


@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


def test_e2e_basic_article_generation(cli_runner, temp_config_file, temp_env_file):
    """Test basic CLI execution."""
    with patch('src.main.ArticlePipeline') as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline.generate.return_value = {
            'metadata': {
                'media_type': 'research_magazine',
                'sources_count': 2
            }
        }
        mock_pipeline.save.return_value = '/tmp/test_output.md'
        mock_pipeline_class.return_value = mock_pipeline
        
        result = cli_runner.invoke(main, [
            '--topic', 'Test Topic',
            '--media-type', 'research_magazine',
            '--config', str(temp_config_file)
        ])
        
        assert result.exit_code == 0
        assert 'Article Generated Successfully' in result.output


def test_e2e_missing_api_keys(cli_runner, temp_config_file):
    """Test CLI with missing API keys."""
    with patch('src.main.EnvLoader') as mock_env_loader_class:
        mock_env_loader = Mock()
        mock_env_loader.validate_llm_keys.side_effect = ValueError("Missing API key")
        mock_env_loader_class.return_value = mock_env_loader
        
        result = cli_runner.invoke(main, [
            '--topic', 'Test Topic',
            '--config', str(temp_config_file)
        ])
        
        assert result.exit_code == 1
        assert 'API keys' in result.output


def test_e2e_invalid_topic(cli_runner, temp_config_file):
    """Test CLI with invalid topic."""
    result = cli_runner.invoke(main, [
        '--topic', '',
        '--config', str(temp_config_file)
    ])
    
    assert result.exit_code == 1
    assert 'Validation Error' in result.output or 'Error' in result.output
