"""Tests for search providers."""
import pytest
from unittest.mock import Mock, patch
from src.utils.search import ExaProvider, GoogleProvider, SearchResult, get_search_provider
from src.utils.config_loader import SearchConfig
from src.utils.exceptions import ExaAPIError, GoogleAPIError
from tests.fixtures.mock_responses import MOCK_EXA_SEARCH_RESPONSE, MOCK_GOOGLE_SEARCH_RESPONSE


def test_exa_search_success(mock_env_loader):
    """Test successful Exa search."""
    config = SearchConfig(provider='exa', max_results=10, include_domains=[])
    
    with patch('src.utils.search.Exa') as mock_exa_class:
        mock_client = Mock()
        mock_client.search_and_contents = Mock(return_value=MOCK_EXA_SEARCH_RESPONSE)
        mock_exa_class.return_value = mock_client
        
        provider = ExaProvider(config, mock_env_loader)
        results = provider.search("test query", max_results=5)
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        mock_client.search_and_contents.assert_called_once()


def test_exa_search_with_domains(mock_env_loader):
    """Test Exa search with domain filtering."""
    config = SearchConfig(
        provider='exa',
        max_results=10,
        include_domains=['example.com']
    )
    
    with patch('src.utils.search.Exa') as mock_exa_class:
        mock_client = Mock()
        mock_client.search_and_contents = Mock(return_value=MOCK_EXA_SEARCH_RESPONSE)
        mock_exa_class.return_value = mock_client
        
        provider = ExaProvider(config, mock_env_loader)
        provider.search("test query")
        
        call_kwargs = mock_client.search_and_contents.call_args[1]
        assert 'include_domains' in call_kwargs
        assert call_kwargs['include_domains'] == ['example.com']


def test_exa_search_empty_results(mock_env_loader):
    """Test Exa search with empty results."""
    config = SearchConfig(provider='exa', max_results=10, include_domains=[])
    
    with patch('src.utils.search.Exa') as mock_exa_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.results = []
        mock_client.search_and_contents = Mock(return_value=mock_response)
        mock_exa_class.return_value = mock_client
        
        provider = ExaProvider(config, mock_env_loader)
        results = provider.search("test query")
        
        assert results == []


def test_exa_search_api_error(mock_env_loader):
    """Test Exa search API error handling."""
    config = SearchConfig(provider='exa', max_results=10, include_domains=[])
    
    with patch('src.utils.search.Exa') as mock_exa_class:
        mock_client = Mock()
        mock_client.search_and_contents = Mock(side_effect=Exception("API Error"))
        mock_exa_class.return_value = mock_client
        
        provider = ExaProvider(config, mock_env_loader)
        
        with pytest.raises(ExaAPIError):
            provider.search("test query")


def test_google_search_success(mock_env_loader):
    """Test successful Google search."""
    config = SearchConfig(provider='google', max_results=10, include_domains=[])
    
    with patch('src.utils.search.build') as mock_build:
        mock_service = Mock()
        mock_cse = Mock()
        mock_list = Mock()
        mock_list.execute.return_value = MOCK_GOOGLE_SEARCH_RESPONSE
        mock_cse.list.return_value = mock_list
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service
        
        provider = GoogleProvider(config, mock_env_loader)
        results = provider.search("test query", max_results=5)
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)


def test_google_search_with_domains(mock_env_loader):
    """Test Google search with domain restrictions."""
    config = SearchConfig(
        provider='google',
        max_results=10,
        include_domains=['example.com']
    )
    
    with patch('src.utils.search.build') as mock_build:
        mock_service = Mock()
        mock_cse = Mock()
        mock_list = Mock()
        mock_list.execute.return_value = MOCK_GOOGLE_SEARCH_RESPONSE
        mock_cse.list.return_value = mock_list
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service
        
        provider = GoogleProvider(config, mock_env_loader)
        provider.search("test query")
        
        # Check that site: restriction was added to query
        call_args = mock_list.call_args
        assert 'site:example.com' in call_args[1]['q'] or 'site:example.com' in call_args[0][0]


def test_get_search_provider_exa(mock_env_loader):
    """Test factory function for Exa provider."""
    config = SearchConfig(provider='exa', max_results=10, include_domains=[])
    
    with patch('src.utils.search.Exa'):
        provider = get_search_provider(config, mock_env_loader)
        assert isinstance(provider, ExaProvider)


def test_get_search_provider_google(mock_env_loader):
    """Test factory function for Google provider."""
    config = SearchConfig(provider='google', max_results=10, include_domains=[])
    
    with patch('src.utils.search.build'):
        provider = get_search_provider(config, mock_env_loader)
        assert isinstance(provider, GoogleProvider)


def test_get_search_provider_invalid(mock_env_loader):
    """Test factory function with invalid provider."""
    config = SearchConfig(provider='invalid', max_results=10, include_domains=[])
    
    with pytest.raises(ValueError):
        get_search_provider(config, mock_env_loader)
