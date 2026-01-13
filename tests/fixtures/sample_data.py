"""Sample data for testing."""
from typing import Dict, Any


SAMPLE_CONFIG_DATA = {
    'llm': {
        'provider': 'gemini',
        'model': 'gemini-1.5-pro',
        'temperature': 0.7,
        'max_tokens': 4000
    },
    'search': {
        'provider': 'exa',
        'max_results': 10,
        'include_domains': []
    },
    'article': {
        'media_type': 'research_magazine',
        'length': 'medium',
        'include_sources': True,
        'fact_check': False
    },
    'output': {
        'format': 'markdown',
        'directory': './outputs',
        'filename_template': '{date}_{topic}_{media_type}.md'
    }
}


SAMPLE_RESEARCH_DATA = {
    'sources': [
        {
            'title': 'Test Source 1',
            'url': 'https://example.com/source1',
            'snippet': 'This is a test snippet from source 1.'
        },
        {
            'title': 'Test Source 2',
            'url': 'https://example.com/source2',
            'snippet': 'This is a test snippet from source 2.'
        }
    ],
    'key_findings': 'Key findings about the topic.',
    'context': 'Contextual information about the topic.',
    'search_queries': ['test query 1', 'test query 2']
}


SAMPLE_ARTICLE_DICT = {
    'headline': 'Test Article Headline',
    'lead': 'This is the lead paragraph.',
    'background': 'Background information here.',
    'discovery': 'The main discovery or achievement.',
    'impact': 'Why this matters.',
    'future': 'Future implications.'
}


SAMPLE_TONES_CONFIG = {
    'research_magazine': {
        'description': 'Research-focused magazines',
        'tone': 'Engaging but authoritative',
        'style_guide': [
            'Balance technical accuracy with readability',
            'Use active voice when possible'
        ],
        'example_phrases': [
            'The breakthrough opens new possibilities...'
        ]
    }
}


SAMPLE_TEMPLATES_CONFIG = {
    'research_magazine': {
        'name': 'Research Magazine Article',
        'structure': [
            {'section': 'headline', 'description': 'Engaging headline', 'required': True},
            {'section': 'lead', 'description': 'Compelling opening', 'required': True},
            {'section': 'background', 'description': 'Context and setting', 'required': True},
            {'section': 'discovery', 'description': 'Main achievement', 'required': True},
            {'section': 'impact', 'description': 'Why this matters', 'required': True},
            {'section': 'future', 'description': 'Future implications', 'required': True}
        ]
    }
}
