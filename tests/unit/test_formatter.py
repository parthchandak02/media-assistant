"""Tests for formatter module."""
import pytest
from datetime import datetime
from src.utils.formatter import (
    format_article,
    format_sources,
    generate_filename,
    format_search_results_for_prompt
)
from src.utils.search import SearchResult


def test_format_article_basic(sample_article_dict):
    """Test basic article formatting."""
    template_config = {
        'structure': [
            {'section': 'headline', 'required': True},
            {'section': 'lead', 'required': True}
        ]
    }
    
    result = format_article(
        sample_article_dict,
        template_config,
        'Test Topic',
        'research_magazine'
    )
    
    assert '---' in result  # YAML frontmatter
    assert 'headline' in result.lower()
    assert 'lead' in result.lower()


def test_format_sources_empty():
    """Test formatting empty sources list."""
    result = format_sources([])
    assert result == ""


def test_format_sources_multiple():
    """Test formatting multiple sources."""
    sources = [
        {'title': 'Source 1', 'url': 'https://example.com/1', 'snippet': 'Snippet 1'},
        {'title': 'Source 2', 'url': 'https://example.com/2', 'snippet': 'Snippet 2'}
    ]
    
    result = format_sources(sources)
    
    assert 'Source 1' in result
    assert 'Source 2' in result
    assert 'https://example.com/1' in result
    assert 'https://example.com/2' in result


def test_generate_filename_basic():
    """Test generating filename from template."""
    template = "{date}_{topic}_{media_type}.md"
    filename = generate_filename(template, "Test Topic", "research_magazine")
    
    assert filename.endswith('.md')
    assert 'test_topic' in filename.lower()
    assert 'research_magazine' in filename


def test_generate_filename_special_chars():
    """Test generating filename with special characters."""
    template = "{date}_{topic}_{media_type}.md"
    filename = generate_filename(template, "Test/Topic & More!", "research_magazine")
    
    # Should sanitize special characters
    assert '/' not in filename
    assert '&' not in filename
    assert '!' not in filename


def test_format_search_results_for_prompt():
    """Test formatting search results for prompt."""
    results = [
        SearchResult(
            title="Test Article",
            url="https://example.com",
            snippet="Test snippet content"
        )
    ]
    
    result = format_search_results_for_prompt(results)
    
    assert 'Test Article' in result
    assert 'https://example.com' in result
    assert 'Test snippet' in result
