"""Environment variable loading and validation."""
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv


class EnvLoader:
    """Loads and validates environment variables."""
    
    def __init__(self, env_path: Optional[str] = None):
        """Initialize environment loader.
        
        Args:
            env_path: Path to .env file (default: .env in project root)
        """
        if env_path is None:
            project_root = Path(__file__).parent.parent.parent
            env_path = project_root / ".env"
        
        self.env_path = Path(env_path)
        self._load_env()
    
    def _load_env(self):
        """Load .env file if it exists."""
        if self.env_path.exists():
            load_dotenv(self.env_path)
        else:
            # Try to load from current directory as fallback
            load_dotenv()
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    def require(self, key: str) -> str:
        """Require an environment variable to exist.
        
        Args:
            key: Environment variable name
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable '{key}' is not set.\n"
                f"Please set it in your .env file or environment.\n"
                f"Expected location: {self.env_path}"
            )
        return value
    
    def validate_llm_keys(self, provider: str) -> Dict[str, str]:
        """Validate and return required API keys for LLM provider.
        
        Args:
            provider: LLM provider name ('gemini' or 'perplexity')
            
        Returns:
            Dictionary with API key(s)
            
        Raises:
            ValueError: If required keys are missing
        """
        keys = {}
        
        if provider.lower() == 'gemini':
            keys['api_key'] = self.require('GEMINI_API_KEY')
        elif provider.lower() == 'perplexity':
            keys['api_key'] = self.require('PERPLEXITY_API_KEY')
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
        
        return keys
    
    def validate_search_keys(self, provider: str) -> Dict[str, str]:
        """Validate and return required API keys for search provider.
        
        Args:
            provider: Search provider name ('exa', 'google', or 'ref')
            
        Returns:
            Dictionary with API key(s)
            
        Raises:
            ValueError: If required keys are missing
        """
        keys = {}
        
        if provider.lower() == 'exa':
            keys['api_key'] = self.require('EXA_API_KEY')
        elif provider.lower() == 'google':
            keys['api_key'] = self.require('GOOGLE_API_KEY')
            keys['cse_id'] = self.require('GOOGLE_CSE_ID')
        elif provider.lower() == 'crewai':
            keys['api_key'] = self.require('EXA_API_KEY')  # CrewAI uses Exa under the hood
        else:
            raise ValueError(
                f"Unknown search provider: {provider}. "
                f"Supported providers: 'exa', 'google', 'crewai'"
            )
        
        return keys
    
    def get_all_required_keys(self, llm_provider: str, search_provider: str) -> Dict[str, str]:
        """Get all required API keys for the configuration.
        
        Args:
            llm_provider: LLM provider name
            search_provider: Search provider name
            
        Returns:
            Dictionary mapping key names to values
            
        Raises:
            ValueError: If any required keys are missing
        """
        all_keys = {}
        
        # LLM keys
        llm_keys = self.validate_llm_keys(llm_provider)
        all_keys.update({f"{llm_provider.upper()}_{k.upper()}": v for k, v in llm_keys.items()})
        
        # Search keys
        search_keys = self.validate_search_keys(search_provider)
        all_keys.update({f"{search_provider.upper()}_{k.upper()}": v for k, v in search_keys.items()})
        
        return all_keys
