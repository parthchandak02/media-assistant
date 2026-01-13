"""Tests for research agent."""
import pytest
from unittest.mock import Mock, patch
from src.agents.research_agent import ResearchAgent
from src.utils.search import SearchResult
from tests.fixtures.mock_responses import MOCK_LLM_QUERY_RESPONSE, MOCK_LLM_SYNTHESIS_RESPONSE


def test_research_successful_flow(mock_env_loader):
    """Test complete research flow."""
    mock_search_provider = Mock()
    mock_search_provider.search = Mock(return_value=[
        SearchResult(
            title="Test Source",
            url="https://example.com",
            snippet="Test snippet"
        )
    ])
    
    mock_llm_provider = Mock()
    mock_llm_provider.generate = Mock(side_effect=[
        MOCK_LLM_QUERY_RESPONSE,
        MOCK_LLM_SYNTHESIS_RESPONSE,
        "Context information"
    ])
    
    agent = ResearchAgent(mock_search_provider, mock_llm_provider)
    result = agent.research("test topic", max_results=5)
    
    assert 'sources' in result
    assert 'key_findings' in result
    assert 'context' in result
    assert 'search_queries' in result


def test_generate_search_queries_success(mock_env_loader):
    """Test generating search queries successfully."""
    mock_search_provider = Mock()
    mock_llm_provider = Mock()
    mock_llm_provider.generate = Mock(return_value=MOCK_LLM_QUERY_RESPONSE)
    
    agent = ResearchAgent(mock_search_provider, mock_llm_provider)
    queries = agent._generate_search_queries("test topic")
    
    assert len(queries) > 0
    assert all(isinstance(q, str) for q in queries)


def test_generate_search_queries_llm_failure(mock_env_loader):
    """Test fallback when LLM fails to generate queries."""
    mock_search_provider = Mock()
    mock_llm_provider = Mock()
    mock_llm_provider.generate = Mock(side_effect=Exception("LLM Error"))
    
    agent = ResearchAgent(mock_search_provider, mock_llm_provider)
    queries = agent._generate_search_queries("test topic")
    
    # Should fallback to topic itself
    assert queries == ["test topic"]


def test_research_duplicate_removal(mock_env_loader):
    """Test removing duplicate URLs."""
    mock_search_provider = Mock()
    mock_search_provider.search = Mock(return_value=[
        SearchResult(title="Source 1", url="https://example.com/1", snippet="Snippet 1"),
        SearchResult(title="Source 2", url="https://example.com/1", snippet="Snippet 2"),  # Duplicate URL
        SearchResult(title="Source 3", url="https://example.com/2", snippet="Snippet 3")
    ])
    
    mock_llm_provider = Mock()
    mock_llm_provider.generate = Mock(side_effect=[
        "query 1\nquery 2",
        "Synthesized findings",
        "Context"
    ])
    
    agent = ResearchAgent(mock_search_provider, mock_llm_provider)
    result = agent.research("test topic", max_results=10)
    
    # Should have only 2 unique URLs
    urls = [s.url for s in result['sources']]
    assert len(urls) == len(set(urls))  # All unique


def test_research_no_results(mock_env_loader):
    """Test research with no search results."""
    mock_search_provider = Mock()
    mock_search_provider.search = Mock(return_value=[])
    
    mock_llm_provider = Mock()
    mock_llm_provider.generate = Mock(return_value="query 1")
    
    agent = ResearchAgent(mock_search_provider, mock_llm_provider)
    result = agent.research("test topic", max_results=5)
    
    assert result['sources'] == []
    assert "No relevant information found" in result['key_findings']
