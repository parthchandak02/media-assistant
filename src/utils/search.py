"""Search provider abstractions for Exa, Google, and CrewAI."""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
import requests
from exa_py import Exa
from googleapiclient.discovery import build
from .env import EnvLoader
from .config_loader import SearchConfig
from .exceptions import ExaAPIError, GoogleAPIError
from .logger import get_logger
from .retry import retry_with_backoff

logger = get_logger(__name__)

# Optional CrewAI import
try:
    from crewai_tools import EXASearchTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    EXASearchTool = None


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    text: Optional[str] = None  # Full text if available


class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        pass


class ExaProvider(SearchProvider):
    """Exa AI search provider."""
    
    def __init__(self, config: SearchConfig, env_loader: EnvLoader):
        """Initialize Exa provider.
        
        Args:
            config: Search configuration
            env_loader: Environment loader for API keys
        """
        self.config = config
        api_key = env_loader.require('EXA_API_KEY')
        self.client = Exa(api_key=api_key)
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Exa API with content extraction.
        
        Uses search_and_contents() for better text extraction and supports
        domain filtering and highlights.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
            
        Raises:
            ExaAPIError: If Exa API returns an error
        """
        try:
            num_results = min(max_results, self.config.max_results)
            
            # Build search parameters
            search_params = {
                "query": query,
                "num_results": num_results,
                "text": {"max_characters": 1000},
            }
            
            # Add domain filtering if specified
            if self.config.include_domains:
                search_params["include_domains"] = self.config.include_domains
            
            # Use search_and_contents for better text extraction
            logger.info(f"Searching Exa with query: {query[:50]}...")
            results = self.client.search_and_contents(**search_params)
            
            # Handle empty results
            if not results or not hasattr(results, 'results') or not results.results:
                logger.warning(f"No results found for query: {query}")
                return []
            
            search_results = []
            for result in results.results:
                # Extract snippet from text or use highlights if available
                snippet = None
                if hasattr(result, 'text') and result.text:
                    snippet = result.text[:500]
                elif hasattr(result, 'highlights') and result.highlights:
                    # Use first highlight as snippet
                    snippet = result.highlights[0][:500] if isinstance(result.highlights, list) else str(result.highlights)[:500]
                
                search_results.append(SearchResult(
                    title=result.title or "No title",
                    url=result.url,
                    snippet=snippet or "No snippet available",
                    text=getattr(result, 'text', None)
                ))
            
            logger.info(f"Found {len(search_results)} results from Exa")
            return search_results
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                logger.error("Exa API rate limit exceeded")
                raise ExaAPIError(f"Exa API rate limit exceeded: {str(e)}")
            logger.error(f"Exa API HTTP error: {str(e)}")
            raise ExaAPIError(f"Exa API HTTP error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Exa API request error: {str(e)}")
            raise ExaAPIError(f"Exa API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Exa API unexpected error: {str(e)}")
            raise ExaAPIError(f"Exa API error: {str(e)}")


class GoogleProvider(SearchProvider):
    """Google Custom Search provider."""
    
    def __init__(self, config: SearchConfig, env_loader: EnvLoader):
        """Initialize Google provider.
        
        Args:
            config: Search configuration
            env_loader: Environment loader for API keys
        """
        self.config = config
        api_key = env_loader.require('GOOGLE_API_KEY')
        cse_id = env_loader.require('GOOGLE_CSE_ID')
        
        self.service = build("customsearch", "v1", developerKey=api_key)
        self.cse_id = cse_id
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Google Custom Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
            
        Raises:
            GoogleAPIError: If Google API returns an error
        """
        try:
            logger.info(f"Searching Google with query: {query[:50]}...")
            # Google Custom Search returns max 10 results per request
            num_results = min(max_results, self.config.max_results, 10)
            
            # Build query with domain restrictions if specified
            search_query = query
            if self.config.include_domains:
                site_restriction = " OR ".join([f"site:{domain}" for domain in self.config.include_domains])
                search_query = f"{query} ({site_restriction})"
            
            result = self.service.cse().list(
                q=search_query,
                cx=self.cse_id,
                num=num_results
            ).execute()
            
            search_results = []
            items = result.get('items', [])
            
            if not items:
                logger.warning(f"No results found for query: {query}")
                return []
            
            for item in items:
                search_results.append(SearchResult(
                    title=item.get('title', 'No title'),
                    url=item.get('link', ''),
                    snippet=item.get('snippet', 'No snippet available')
                ))
            
            logger.info(f"Found {len(search_results)} results from Google")
            return search_results
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                logger.error("Google Custom Search API rate limit exceeded")
                raise GoogleAPIError(f"Google API rate limit exceeded: {str(e)}")
            logger.error(f"Google Custom Search API HTTP error: {str(e)}")
            raise GoogleAPIError(f"Google Custom Search API HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Google Custom Search API error: {str(e)}")
            raise GoogleAPIError(f"Google Custom Search API error: {str(e)}")


class CrewAIExaProvider(SearchProvider):
    """CrewAI-based Exa search provider using EXASearchTool.
    
    This provider uses CrewAI's EXASearchTool which provides enhanced
    semantic search capabilities and better integration with agent workflows.
    """
    
    def __init__(self, config: SearchConfig, env_loader: EnvLoader):
        """Initialize CrewAI Exa provider.
        
        Args:
            config: Search configuration
            env_loader: Environment loader for API keys
            
        Raises:
            ImportError: If crewai-tools is not installed
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI tools not available. Install with: pip install crewai-tools"
            )
        
        self.config = config
        api_key = env_loader.require('EXA_API_KEY')
        
        # Initialize CrewAI EXASearchTool with configuration
        # CrewAI's EXASearchTool automatically uses EXA_API_KEY from environment
        # but we can also pass it explicitly
        self.tool = EXASearchTool(api_key=api_key)
        
        logger.info("Initialized CrewAI EXASearchTool")
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using CrewAI's EXASearchTool.
        
        CrewAI's EXASearchTool provides enhanced semantic search with
        automatic query optimization and better result formatting.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
            
        Raises:
            ExaAPIError: If search fails
        """
        try:
            num_results = min(max_results, self.config.max_results)
            
            logger.info(f"Searching with CrewAI Exa tool: {query[:50]}...")
            
            # CrewAI's EXASearchTool returns formatted results
            # The tool handles query optimization automatically
            result = self.tool._run(query)
            
            # Parse CrewAI tool output
            # The tool returns a formatted string with search results
            search_results = self._parse_crewai_result(result, num_results)
            
            logger.info(f"Found {len(search_results)} results from CrewAI Exa")
            return search_results
            
        except Exception as e:
            logger.error(f"CrewAI Exa search error: {str(e)}")
            raise ExaAPIError(f"CrewAI Exa search error: {str(e)}")
    
    def _parse_crewai_result(self, result: str, max_results: int) -> List[SearchResult]:
        """Parse CrewAI tool output into SearchResult objects.
        
        CrewAI's EXASearchTool returns formatted text with search results.
        This method extracts structured data from the formatted output.
        
        Args:
            result: Raw result string from CrewAI tool
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        search_results = []
        
        if not result or not result.strip():
            logger.warning("Empty result from CrewAI Exa tool")
            return []
        
        # CrewAI EXASearchTool typically returns results in a structured format
        # Try multiple parsing strategies
        
        # Strategy 1: Look for markdown-style links [title](url)
        import re
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', result)
        if markdown_links:
            for title, url in markdown_links[:max_results]:
                if url.startswith('http'):
                    search_results.append(SearchResult(
                        title=title or "No title",
                        url=url,
                        snippet="",  # Will be filled from surrounding text
                        text=None
                    ))
        
        # Strategy 2: Look for plain URLs with surrounding context
        if not search_results:
            url_pattern = r'https?://[^\s\)]+'
            urls = re.findall(url_pattern, result)
            
            for url in urls[:max_results]:
                # Try to find title before URL (common pattern: "Title: URL")
                # Look backwards from URL position
                url_pos = result.find(url)
                if url_pos > 0:
                    # Get text before URL (up to 200 chars)
                    before_url = result[max(0, url_pos-200):url_pos].strip()
                    # Try to extract title (last line or sentence)
                    title_lines = [l.strip() for l in before_url.split('\n') if l.strip()]
                    title = title_lines[-1] if title_lines else "No title"
                    
                    # Get text after URL for snippet (up to 300 chars)
                    after_url = result[url_pos+len(url):url_pos+len(url)+300].strip()
                    snippet_lines = [l.strip() for l in after_url.split('\n')[:3] if l.strip() and not l.startswith('http')]
                    snippet = ' '.join(snippet_lines[:2]) if snippet_lines else ""
                    
                    search_results.append(SearchResult(
                        title=title[:100],  # Limit title length
                        url=url.rstrip('.,;'),  # Clean URL
                        snippet=snippet[:500],
                        text=None
                    ))
        
        # Strategy 3: If still no results, check if result contains structured data
        # CrewAI might return JSON-like or structured text
        if not search_results:
            # Try to find any URLs in the text
            urls = re.findall(url_pattern, result)
            if urls:
                for url in urls[:max_results]:
                    search_results.append(SearchResult(
                        title="Search Result",
                        url=url.rstrip('.,;'),
                        snippet=result[:500] if len(result) > 500 else result,
                        text=result
                    ))
        
        # Strategy 4: Fallback - create a single result from entire output
        if not search_results:
            logger.warning("Could not parse structured results from CrewAI, using fallback")
            search_results.append(SearchResult(
                title="Research Results",
                url="",
                snippet=result[:500],
                text=result
            ))
        
        return search_results[:max_results]


def get_search_provider(config: SearchConfig, env_loader: EnvLoader) -> SearchProvider:
    """Factory function to get appropriate search provider.
    
    Args:
        config: Search configuration
        env_loader: Environment loader
        
    Returns:
        SearchProvider instance
        
    Raises:
        ValueError: If provider is not supported
        ImportError: If CrewAI is requested but not installed
    """
    provider_name = config.provider.lower()
    
    if provider_name == 'exa':
        return ExaProvider(config, env_loader)
    elif provider_name == 'google':
        return GoogleProvider(config, env_loader)
    elif provider_name == 'crewai':
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI tools not available. Install with: pip install crewai-tools"
            )
        return CrewAIExaProvider(config, env_loader)
    else:
        raise ValueError(
            f"Unsupported search provider: {config.provider}. "
            f"Supported providers: 'exa', 'google', 'crewai'"
        )
