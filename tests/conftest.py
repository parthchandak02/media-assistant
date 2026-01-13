"""Pytest configuration and fixtures."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
import yaml

from src.utils.config_loader import AppConfig, LLMConfig, SearchConfig, ArticleConfig, OutputConfig
from src.utils.env import EnvLoader
from tests.fixtures.sample_data import (
    SAMPLE_CONFIG_DATA,
    SAMPLE_TONES_CONFIG,
    SAMPLE_TEMPLATES_CONFIG
)


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config.yaml file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(SAMPLE_CONFIG_DATA, f)
    return config_path


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file."""
    env_path = tmp_path / ".env"
    env_content = """GEMINI_API_KEY=test-gemini-key
PERPLEXITY_API_KEY=test-perplexity-key
EXA_API_KEY=test-exa-key
GOOGLE_API_KEY=test-google-key
GOOGLE_CSE_ID=test-cse-id
"""
    env_path.write_text(env_content)
    return env_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def mock_config():
    """Create a mock AppConfig."""
    return AppConfig(
        llm=LLMConfig(
            provider='gemini',
            model='gemini-1.5-pro',
            temperature=0.7,
            max_tokens=4000
        ),
        search=SearchConfig(
            provider='exa',
            max_results=10,
            include_domains=[]
        ),
        article=ArticleConfig(
            media_type='research_magazine',
            length='medium',
            include_sources=True,
            fact_check=False
        ),
        output=OutputConfig(
            format='markdown',
            directory='./outputs',
            filename_template='{date}_{topic}_{media_type}.md'
        )
    )


@pytest.fixture
def mock_env_loader(monkeypatch):
    """Create a mock EnvLoader."""
    def mock_get(key, default=None):
        keys = {
            'GEMINI_API_KEY': 'test-gemini-key',
            'PERPLEXITY_API_KEY': 'test-perplexity-key',
            'EXA_API_KEY': 'test-exa-key',
            'GOOGLE_API_KEY': 'test-google-key',
            'GOOGLE_CSE_ID': 'test-cse-id'
        }
        return keys.get(key, default)
    
    def mock_require(key):
        value = mock_get(key)
        if not value:
            raise ValueError(f"Required environment variable '{key}' is not set.")
        return value
    
    loader = Mock(spec=EnvLoader)
    loader.get = Mock(side_effect=mock_get)
    loader.require = Mock(side_effect=mock_require)
    loader.validate_llm_keys = Mock(return_value={'api_key': 'test-key'})
    loader.validate_search_keys = Mock(return_value={'api_key': 'test-key'})
    return loader


@pytest.fixture
def mock_exa_client():
    """Create a mock Exa client."""
    from tests.fixtures.mock_responses import MOCK_EXA_SEARCH_RESPONSE
    
    client = Mock()
    client.search_and_contents = Mock(return_value=MOCK_EXA_SEARCH_RESPONSE)
    return client


@pytest.fixture
def mock_google_client():
    """Create a mock Google Custom Search client."""
    from tests.fixtures.mock_responses import MOCK_GOOGLE_SEARCH_RESPONSE
    
    service = Mock()
    service.cse.return_value.list.return_value.execute.return_value = MOCK_GOOGLE_SEARCH_RESPONSE
    return service


@pytest.fixture
def mock_gemini_model():
    """Create a mock Gemini model."""
    from tests.fixtures.mock_responses import MOCK_GEMINI_RESPONSE_TEXT
    
    model = Mock()
    response = Mock()
    response.text = MOCK_GEMINI_RESPONSE_TEXT
    model.generate_content = Mock(return_value=response)
    return model


@pytest.fixture
def mock_perplexity_response():
    """Create a mock Perplexity API response."""
    from tests.fixtures.mock_responses import MOCK_PERPLEXITY_RESPONSE
    import requests
    
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.json = Mock(return_value=MOCK_PERPLEXITY_RESPONSE)
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def sample_research_data():
    """Provide sample research data."""
    from tests.fixtures.sample_data import SAMPLE_RESEARCH_DATA
    from src.utils.search import SearchResult
    
    # Convert dict sources to SearchResult objects
    sources = [
        SearchResult(
            title=s['title'],
            url=s['url'],
            snippet=s['snippet']
        )
        for s in SAMPLE_RESEARCH_DATA['sources']
    ]
    
    return {
        'sources': sources,
        'key_findings': SAMPLE_RESEARCH_DATA['key_findings'],
        'context': SAMPLE_RESEARCH_DATA['context'],
        'search_queries': SAMPLE_RESEARCH_DATA['search_queries']
    }


@pytest.fixture
def sample_article_dict():
    """Provide sample article dictionary."""
    from tests.fixtures.sample_data import SAMPLE_ARTICLE_DICT
    return SAMPLE_ARTICLE_DICT.copy()
