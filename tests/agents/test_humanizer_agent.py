"""Tests for HumanizerAgent."""
import pytest
from unittest.mock import Mock, MagicMock
from src.agents.humanizer_agent import HumanizerAgent
from src.utils.config_loader import ConfigLoader


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.generate = Mock(return_value="## Title\nHumanized title\n\n## Introduction\nHumanized introduction content")
    return provider


@pytest.fixture
def mock_config_loader():
    """Create a mock config loader."""
    loader = Mock(spec=ConfigLoader)
    loader.get_tone_config = Mock(return_value={
        'description': 'Tech news publication',
        'tone': 'Conversational, forward-looking',
        'style_guide': ['Use active voice', 'Be engaging']
    })
    loader.get_template_config = Mock(return_value={
        'structure': [
            {'section': 'title', 'required': True},
            {'section': 'introduction', 'required': True}
        ]
    })
    return loader


@pytest.fixture
def sample_article_dict():
    """Sample article dictionary for testing."""
    return {
        'title': 'Test Article Title',
        'introduction': 'This is a test introduction. It demonstrates AI patterns. Furthermore, it shows how the system works.'
    }


def test_humanizer_agent_initialization(mock_llm_provider, mock_config_loader):
    """Test HumanizerAgent initialization."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=2,
        intensity='medium'
    )
    
    assert agent.enabled is True
    assert agent.passes == 2
    assert agent.intensity == 'medium'


def test_humanizer_agent_disabled(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test that humanizer returns original when disabled."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=False
    )
    
    result = agent.humanize(sample_article_dict, 'tech_news')
    
    assert result == sample_article_dict
    mock_llm_provider.generate.assert_not_called()


def test_humanizer_agent_passes_clamping(mock_llm_provider, mock_config_loader):
    """Test that passes are clamped between 1 and 3."""
    # Test too low
    agent1 = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        passes=0
    )
    assert agent1.passes == 1
    
    # Test too high
    agent2 = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        passes=5
    )
    assert agent2.passes == 3


def test_humanize_single_pass(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test humanization with single pass."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=1,
        intensity='medium'
    )
    
    result = agent.humanize(sample_article_dict, 'tech_news')
    
    assert 'title' in result
    assert 'introduction' in result
    assert mock_llm_provider.generate.call_count == 1


def test_humanize_multiple_passes(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test humanization with multiple passes."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=2,
        intensity='medium'
    )
    
    result = agent.humanize(sample_article_dict, 'tech_news')
    
    assert 'title' in result
    assert 'introduction' in result
    assert mock_llm_provider.generate.call_count == 2


def test_format_article_for_humanization(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test article formatting for humanization."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=1
    )
    
    formatted = agent._format_article_for_humanization(sample_article_dict)
    
    assert '## Title' in formatted
    assert '## Introduction' in formatted
    assert 'Test Article Title' in formatted
    assert 'test introduction' in formatted


def test_parse_humanized_sections(mock_llm_provider, mock_config_loader):
    """Test parsing humanized sections."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=1
    )
    
    humanized_text = """## Title
Humanized Title

## Introduction
Humanized introduction content here."""
    
    template_config = {
        'structure': [
            {'section': 'title'},
            {'section': 'introduction'}
        ]
    }
    
    original_sections = {'title', 'introduction'}
    
    result = agent._parse_humanized_sections(
        humanized_text,
        template_config,
        original_sections
    )
    
    assert 'title' in result
    assert 'introduction' in result
    assert 'Humanized Title' in result['title']
    assert 'Humanized introduction content here' in result['introduction']


def test_build_humanization_prompt_pass1(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test building humanization prompt for pass 1."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=2,
        intensity='medium'
    )
    
    tone_config = {
        'description': 'Tech news',
        'tone': 'Conversational',
        'style_guide': ['Use active voice']
    }
    
    template_config = {
        'structure': [
            {'section': 'title'},
            {'section': 'introduction'}
        ]
    }
    
    prompt = agent._build_humanization_prompt(
        sample_article_dict,
        'tech_news',
        tone_config,
        template_config,
        pass_num=1
    )
    
    assert 'Sentence Variation' in prompt
    assert 'Perplexity' in prompt
    assert 'Burstiness' in prompt
    assert 'tech_news' in prompt


def test_build_humanization_prompt_pass2(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test building humanization prompt for pass 2."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=2,
        intensity='medium'
    )
    
    tone_config = {
        'description': 'Tech news',
        'tone': 'Conversational',
        'style_guide': ['Use active voice']
    }
    
    template_config = {
        'structure': [
            {'section': 'title'},
            {'section': 'introduction'}
        ]
    }
    
    detected_patterns = [('Furthermore', 1), ('It is important to note', 1)]
    
    prompt = agent._build_humanization_prompt(
        sample_article_dict,
        'tech_news',
        tone_config,
        template_config,
        pass_num=2,
        detected_patterns=detected_patterns
    )
    
    assert 'Remove AI Patterns' in prompt
    assert 'Natural Transitions' in prompt
    assert 'Furthermore' in prompt or 'DETECTED AI PATTERNS' in prompt


def test_build_humanization_prompt_pass3(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test building humanization prompt for pass 3."""
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=3,
        intensity='medium'
    )
    
    tone_config = {
        'description': 'Tech news',
        'tone': 'Conversational',
        'style_guide': ['Use active voice']
    }
    
    template_config = {
        'structure': [
            {'section': 'title'},
            {'section': 'introduction'}
        ]
    }
    
    prompt = agent._build_humanization_prompt(
        sample_article_dict,
        'tech_news',
        tone_config,
        template_config,
        pass_num=3
    )
    
    assert 'Voice Refinement' in prompt
    assert 'Final Polish' in prompt


def test_intensity_levels(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test different intensity levels."""
    for intensity in ['low', 'medium', 'high']:
        agent = HumanizerAgent(
            mock_llm_provider,
            mock_config_loader,
            enabled=True,
            passes=1,
            intensity=intensity
        )
        
        tone_config = {
            'description': 'Tech news',
            'tone': 'Conversational',
            'style_guide': []
        }
        
        template_config = {'structure': []}
        
        prompt = agent._build_humanization_prompt(
            sample_article_dict,
            'tech_news',
            tone_config,
            template_config,
            pass_num=1
        )
        
        assert intensity.capitalize() in prompt or 'INTENSITY LEVEL' in prompt


def test_preserves_structure(mock_llm_provider, mock_config_loader, sample_article_dict):
    """Test that humanization preserves article structure."""
    mock_llm_provider.generate.return_value = """## Title
New Title

## Introduction
New Introduction"""
    
    agent = HumanizerAgent(
        mock_llm_provider,
        mock_config_loader,
        enabled=True,
        passes=1
    )
    
    result = agent.humanize(sample_article_dict, 'tech_news')
    
    # Should preserve all original sections
    assert set(result.keys()) == set(sample_article_dict.keys())
