"""Custom exception classes for media article writer."""


class MediaArticleWriterError(Exception):
    """Base exception for all media article writer errors."""
    pass


class ConfigurationError(MediaArticleWriterError):
    """Raised when there's a configuration error."""
    pass


class SearchProviderError(MediaArticleWriterError):
    """Base exception for search provider errors."""
    pass


class ExaAPIError(SearchProviderError):
    """Raised when Exa API returns an error."""
    pass


class GoogleAPIError(SearchProviderError):
    """Raised when Google Custom Search API returns an error."""
    pass


class LLMProviderError(MediaArticleWriterError):
    """Base exception for LLM provider errors."""
    pass


class GeminiAPIError(LLMProviderError):
    """Raised when Gemini API returns an error."""
    pass


class PerplexityAPIError(LLMProviderError):
    """Raised when Perplexity API returns an error."""
    pass


class ValidationError(MediaArticleWriterError):
    """Raised when input validation fails."""
    pass
