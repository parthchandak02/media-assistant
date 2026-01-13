"""Cache utility for storing and retrieving research results."""
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import asdict, dataclass

from .search import SearchResult
from .config_loader import SearchConfig
from .logger import get_logger

logger = get_logger(__name__)

# Cache version - increment when research agent logic changes significantly
CACHE_VERSION = "1.0"


@dataclass
class CacheMetadata:
    """Metadata for cached research."""
    version: str
    topic: str
    user_context_hash: str
    search_provider: str
    max_results: int
    timestamp: str


class ResearchCache:
    """Handles caching of research results to avoid repeated API calls."""
    
    def __init__(self, cache_dir: str = ".cache/research"):
        """Initialize research cache.
        
        Args:
            cache_dir: Base directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _normalize_topic(self, topic: str) -> str:
        """Normalize topic string for consistent hashing.
        
        Args:
            topic: Topic string
            
        Returns:
            Normalized topic string
        """
        return topic.strip().lower()
    
    def _hash_user_context(self, user_context: Optional[Dict[str, str]]) -> str:
        """Generate hash of user context.
        
        Args:
            user_context: User context dictionary
            
        Returns:
            SHA256 hash string
        """
        if not user_context:
            return ""
        
        # Sort keys for consistent hashing
        context_str = json.dumps(user_context, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]
    
    def _sanitize_filename(self, text: str, max_length: int = 30) -> str:
        """Sanitize text for use in filename.
        
        Args:
            text: Text to sanitize
            max_length: Maximum length
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove special characters, keep alphanumeric and underscores
        sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in text)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Limit length
        sanitized = sanitized[:max_length]
        return sanitized
    
    def get_cache_key(
        self,
        topic: str,
        user_context: Optional[Dict[str, str]] = None,
        search_config: Optional[SearchConfig] = None
    ) -> str:
        """Generate cache key for research data.
        
        Args:
            topic: Research topic
            user_context: Optional user context
            search_config: Search configuration
            
        Returns:
            Cache key string
        """
        normalized_topic = self._normalize_topic(topic)
        context_hash = self._hash_user_context(user_context)
        
        # Build hash components
        hash_components = [normalized_topic, context_hash]
        
        if search_config:
            hash_components.append(search_config.provider)
            hash_components.append(str(search_config.max_results))
        
        # Generate hash
        hash_input = "|".join(hash_components)
        cache_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Create readable cache key
        sanitized_topic = self._sanitize_filename(topic, max_length=30)
        cache_key = f"{cache_hash}_{sanitized_topic}"
        
        return cache_key
    
    def get_cache_path(self, cache_key: str) -> Path:
        """Get cache directory path for a cache key.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Path to cache directory
        """
        return self.cache_dir / cache_key
    
    def get_research_file(self, cache_key: str) -> Path:
        """Get research data file path.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Path to research.json file
        """
        return self.get_cache_path(cache_key) / "research.json"
    
    def get_metadata_file(self, cache_key: str) -> Path:
        """Get metadata file path.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Path to metadata.json file
        """
        return self.get_cache_path(cache_key) / "metadata.json"
    
    def _serialize_search_results(self, sources: List[SearchResult]) -> List[Dict[str, Any]]:
        """Serialize SearchResult objects to dictionaries.
        
        Args:
            sources: List of SearchResult objects
            
        Returns:
            List of dictionaries
        """
        serialized = []
        for source in sources:
            if isinstance(source, SearchResult):
                serialized.append(asdict(source))
            elif isinstance(source, dict):
                serialized.append(source)
            else:
                # Fallback: try to extract attributes
                serialized.append({
                    'title': getattr(source, 'title', 'No title'),
                    'url': getattr(source, 'url', ''),
                    'snippet': getattr(source, 'snippet', ''),
                    'text': getattr(source, 'text', None)
                })
        return serialized
    
    def _deserialize_search_results(self, sources_data: List[Dict[str, Any]]) -> List[SearchResult]:
        """Deserialize dictionaries to SearchResult objects.
        
        Args:
            sources_data: List of dictionaries
            
        Returns:
            List of SearchResult objects
        """
        results = []
        for source_dict in sources_data:
            results.append(SearchResult(
                title=source_dict.get('title', 'No title'),
                url=source_dict.get('url', ''),
                snippet=source_dict.get('snippet', ''),
                text=source_dict.get('text')
            ))
        return results
    
    def cache_exists(
        self,
        topic: str,
        user_context: Optional[Dict[str, str]] = None,
        search_config: Optional[SearchConfig] = None
    ) -> bool:
        """Check if cache exists for given parameters.
        
        Args:
            topic: Research topic
            user_context: Optional user context
            search_config: Search configuration
            
        Returns:
            True if cache exists and is valid
        """
        cache_key = self.get_cache_key(topic, user_context, search_config)
        research_file = self.get_research_file(cache_key)
        metadata_file = self.get_metadata_file(cache_key)
        
        if not research_file.exists() or not metadata_file.exists():
            return False
        
        # Check cache version
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Version mismatch invalidates cache
            if metadata.get('version') != CACHE_VERSION:
                logger.debug(f"Cache version mismatch: {metadata.get('version')} != {CACHE_VERSION}")
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error checking cache metadata: {e}")
            return False
    
    def load_research(
        self,
        topic: str,
        user_context: Optional[Dict[str, str]] = None,
        search_config: Optional[SearchConfig] = None
    ) -> Optional[Dict[str, Any]]:
        """Load cached research data.
        
        Args:
            topic: Research topic
            user_context: Optional user context
            search_config: Search configuration
            
        Returns:
            Research data dictionary or None if not found
        """
        cache_key = self.get_cache_key(topic, user_context, search_config)
        research_file = self.get_research_file(cache_key)
        
        if not research_file.exists():
            return None
        
        try:
            with open(research_file, 'r') as f:
                data = json.load(f)
            
            # Deserialize SearchResult objects
            if 'sources' in data:
                data['sources'] = self._deserialize_search_results(data['sources'])
            
            logger.info(f"Loaded research from cache: {cache_key}")
            return data
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
            return None
    
    def save_research(
        self,
        topic: str,
        research_data: Dict[str, Any],
        user_context: Optional[Dict[str, str]] = None,
        search_config: Optional[SearchConfig] = None
    ) -> bool:
        """Save research data to cache.
        
        Args:
            topic: Research topic
            research_data: Research data dictionary
            user_context: Optional user context
            search_config: Search configuration
            
        Returns:
            True if saved successfully
        """
        cache_key = self.get_cache_key(topic, user_context, search_config)
        cache_path = self.get_cache_path(cache_key)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        research_file = self.get_research_file(cache_key)
        metadata_file = self.get_metadata_file(cache_key)
        
        try:
            # Serialize SearchResult objects
            data_to_save = research_data.copy()
            if 'sources' in data_to_save:
                data_to_save['sources'] = self._serialize_search_results(data_to_save['sources'])
            
            # Save research data
            with open(research_file, 'w') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata = CacheMetadata(
                version=CACHE_VERSION,
                topic=topic,
                user_context_hash=self._hash_user_context(user_context),
                search_provider=search_config.provider if search_config else "unknown",
                max_results=search_config.max_results if search_config else 10,
                timestamp=datetime.now().isoformat()
            )
            
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            logger.info(f"Saved research to cache: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            return False
    
    def invalidate_cache(
        self,
        topic: str,
        user_context: Optional[Dict[str, str]] = None,
        search_config: Optional[SearchConfig] = None
    ) -> bool:
        """Invalidate cache for specific topic.
        
        Args:
            topic: Research topic
            user_context: Optional user context
            search_config: Search configuration
            
        Returns:
            True if cache was invalidated
        """
        cache_key = self.get_cache_key(topic, user_context, search_config)
        cache_path = self.get_cache_path(cache_key)
        
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                logger.info(f"Invalidated cache: {cache_key}")
                return True
            except Exception as e:
                logger.error(f"Error invalidating cache: {e}")
                return False
        
        return False
    
    def clear_all_cache(self) -> bool:
        """Clear all cached research data.
        
        Returns:
            True if cleared successfully
        """
        if self.cache_dir.exists():
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared all research cache")
                return True
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return False
        
        return True
