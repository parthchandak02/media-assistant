"""Integration tests for pipeline."""
import pytest
from unittest.mock import Mock, patch
from src.pipeline import ArticlePipeline
from src.utils.config_loader import ConfigLoader


def test_pipeline_full_flow(mock_config, temp_output_dir, mock_env_loader):
    """Test complete pipeline execution."""
    with patch('src.pipeline.get_llm_provider') as mock_llm, \
         patch('src.pipeline.get_search_provider') as mock_search:
        
        # Mock providers
        mock_llm_provider = Mock()
        mock_llm_provider.generate = Mock(side_effect=[
            "query 1\nquery 2",
            "Synthesized findings",
            "Context",
            "## headline\nTest Headline\n\n## lead\nTest lead",
            "## headline\nEdited Headline\n\n## lead\nEdited lead"
        ])
        
        mock_search_provider = Mock()
        mock_search_provider.search = Mock(return_value=[])
        
        mock_llm.return_value = mock_llm_provider
        mock_search.return_value = mock_search_provider
        
        # Mock config loader
        mock_config_loader = Mock(spec=ConfigLoader)
        mock_config_loader.load_tones.return_value = {
            'research_magazine': {'tone': 'test', 'style_guide': []}
        }
        mock_config_loader.load_templates.return_value = {
            'research_magazine': {
                'structure': [
                    {'section': 'headline', 'required': True},
                    {'section': 'lead', 'required': True}
                ]
            }
        }
        mock_config_loader.get_tone_config.return_value = {'tone': 'test'}
        mock_config_loader.get_template_config.return_value = {
            'structure': [
                {'section': 'headline', 'required': True},
                {'section': 'lead', 'required': True}
            ]
        }
        mock_config_loader.validate_media_type.return_value = True
        
        # Update config output directory
        mock_config.output.directory = str(temp_output_dir)
        
        pipeline = ArticlePipeline(mock_config, mock_config_loader)
        result = pipeline.generate(
            topic="Test Topic",
            media_type="research_magazine",
            length="short"
        )
        
        assert 'article_dict' in result
        assert 'article_markdown' in result
        assert 'metadata' in result


def test_pipeline_save_article(mock_config, temp_output_dir, mock_env_loader):
    """Test saving article to file."""
    with patch('src.pipeline.get_llm_provider'), \
         patch('src.pipeline.get_search_provider'):
        
        mock_config_loader = Mock(spec=ConfigLoader)
        mock_config.output.directory = str(temp_output_dir)
        
        pipeline = ArticlePipeline(mock_config, mock_config_loader)
        
        article_data = {
            'article_markdown': '# Test Article\n\nContent here.',
            'metadata': {
                'topic': 'Test Topic',
                'media_type': 'research_magazine'
            }
        }
        
        output_path = pipeline.save(article_data)
        
        assert Path(output_path).exists()
        assert Path(output_path).read_text() == article_data['article_markdown']
