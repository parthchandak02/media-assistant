"""Mock API responses for testing."""
from typing import Dict, Any, List


class MockExaResult:
    """Mock Exa search result."""
    def __init__(self, title: str, url: str, text: str = None):
        self.title = title
        self.url = url
        self.text = text or f"Sample text content for {title}"


class MockExaResponse:
    """Mock Exa API response."""
    def __init__(self, results: List[MockExaResult]):
        self.results = results


MOCK_EXA_SEARCH_RESPONSE = MockExaResponse([
    MockExaResult(
        title="Test Article 1",
        url="https://example.com/article1",
        text="This is a sample article about the topic with relevant information."
    ),
    MockExaResult(
        title="Test Article 2",
        url="https://example.com/article2",
        text="Another article with different perspectives on the topic."
    )
])


MOCK_GOOGLE_SEARCH_RESPONSE = {
    'items': [
        {
            'title': 'Test Article 1',
            'link': 'https://example.com/article1',
            'snippet': 'This is a sample snippet from Google search results.'
        },
        {
            'title': 'Test Article 2',
            'link': 'https://example.com/article2',
            'snippet': 'Another snippet with relevant information.'
        }
    ]
}


MOCK_GEMINI_RESPONSE_TEXT = "This is a generated response from Gemini API."


MOCK_PERPLEXITY_RESPONSE = {
    'choices': [
        {
            'message': {
                'content': 'This is a generated response from Perplexity API.'
            }
        }
    ]
}


MOCK_LLM_QUERY_RESPONSE = """query 1 about the topic
query 2 with different angle
query 3 focusing on specific aspect"""


MOCK_LLM_SYNTHESIS_RESPONSE = """Key findings:
1. Important point one
2. Important point two
3. Important point three

These findings suggest significant implications for the field."""


MOCK_LLM_CONTEXT_RESPONSE = """This topic is significant because it addresses fundamental questions
in the field. The research builds upon previous work and opens new avenues
for exploration. The implications extend beyond the immediate domain."""
