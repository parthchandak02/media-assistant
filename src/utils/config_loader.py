"""Configuration loader for media article writer."""
import yaml
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
from .exceptions import ConfigurationError


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str
    model: str
    temperature: float
    max_tokens: int


@dataclass
class SearchConfig:
    """Search provider configuration."""
    provider: str
    max_results: int
    include_domains: list


@dataclass
class ArticleConfig:
    """Article generation configuration."""
    media_type: str
    length: str
    include_sources: bool
    fact_check: bool


@dataclass
class OutputConfig:
    """Output configuration."""
    format: str
    directory: str
    filename_template: str


@dataclass
class HumanizerConfig:
    """Humanizer configuration."""
    enabled: bool
    passes: int
    intensity: str


@dataclass
class AppConfig:
    """Complete application configuration."""
    llm: LLMConfig
    search: SearchConfig
    article: ArticleConfig
    output: OutputConfig
    humanizer: HumanizerConfig


class ConfigLoader:
    """Loads and validates configuration files."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize config loader.
        
        Args:
            config_path: Path to main config.yaml file
        """
        self.config_path = Path(config_path)
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "src" / "config"
    
    def load_config(self) -> AppConfig:
        """Load main configuration file.
        
        Returns:
            AppConfig object with all configuration
            
        Raises:
            FileNotFoundError: If config.yaml doesn't exist
            ValueError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Please copy config.yaml.example to config.yaml and configure it."
            )
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in config file {self.config_path}: {str(e)}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error reading config file {self.config_path}: {str(e)}"
            )
        
        if not config_data:
            raise ConfigurationError(f"Config file {self.config_path} is empty")
        
        # Validate and create config objects
        try:
            llm_config = LLMConfig(
                provider=config_data.get('llm', {}).get('provider'),
                model=config_data.get('llm', {}).get('model'),
                temperature=float(config_data.get('llm', {}).get('temperature', 0.7)),
                max_tokens=int(config_data.get('llm', {}).get('max_tokens', 4000))
            )
            
            if not llm_config.provider or not llm_config.model:
                raise ConfigurationError("Missing required LLM configuration: provider and model")
        except (KeyError, TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid LLM configuration: {str(e)}")
        
        try:
            search_config = SearchConfig(
                provider=config_data.get('search', {}).get('provider'),
                max_results=int(config_data.get('search', {}).get('max_results', 10)),
                include_domains=config_data.get('search', {}).get('include_domains', [])
            )
            
            if not search_config.provider:
                raise ConfigurationError("Missing required search configuration: provider")
        except (KeyError, TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid search configuration: {str(e)}")
        
        try:
            article_config = ArticleConfig(
                media_type=config_data.get('article', {}).get('media_type'),
                length=config_data.get('article', {}).get('length', 'medium'),
                include_sources=config_data.get('article', {}).get('include_sources', True),
                fact_check=config_data.get('article', {}).get('fact_check', False)
            )
            
            if not article_config.media_type:
                raise ConfigurationError("Missing required article configuration: media_type")
        except (KeyError, TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid article configuration: {str(e)}")
        
        try:
            output_config = OutputConfig(
                format=config_data.get('output', {}).get('format', 'markdown'),
                directory=config_data.get('output', {}).get('directory', './outputs'),
                filename_template=config_data.get('output', {}).get('filename_template', '{date}_{topic}_{media_type}.md')
            )
        except (KeyError, TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid output configuration: {str(e)}")
        
        try:
            humanizer_data = config_data.get('humanizer', {})
            humanizer_config = HumanizerConfig(
                enabled=humanizer_data.get('enabled', True),
                passes=int(humanizer_data.get('passes', 2)),
                intensity=humanizer_data.get('intensity', 'medium')
            )
            
            # Validate passes
            if humanizer_config.passes < 1 or humanizer_config.passes > 3:
                raise ConfigurationError("Humanizer passes must be between 1 and 3")
            
            # Validate intensity
            if humanizer_config.intensity not in ['low', 'medium', 'high']:
                raise ConfigurationError("Humanizer intensity must be 'low', 'medium', or 'high'")
        except (KeyError, TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid humanizer configuration: {str(e)}")
        
        return AppConfig(
            llm=llm_config,
            search=search_config,
            article=article_config,
            output=output_config,
            humanizer=humanizer_config
        )
    
    def load_tones(self) -> Dict[str, Any]:
        """Load tone definitions from tones.yaml.
        
        Returns:
            Dictionary with media types and their tone configurations
            
        Raises:
            FileNotFoundError: If tones.yaml doesn't exist
        """
        tones_path = self.config_dir / "tones.yaml"
        if not tones_path.exists():
            raise FileNotFoundError(f"Tones config not found: {tones_path}")
        
        with open(tones_path, 'r') as f:
            tones_data = yaml.safe_load(f)
        
        return tones_data.get('media_types', {})
    
    def load_templates(self) -> Dict[str, Any]:
        """Load article templates from templates.yaml.
        
        Returns:
            Dictionary with media types and their template structures
            
        Raises:
            FileNotFoundError: If templates.yaml doesn't exist
        """
        templates_path = self.config_dir / "templates.yaml"
        if not templates_path.exists():
            raise FileNotFoundError(f"Templates config not found: {templates_path}")
        
        with open(templates_path, 'r') as f:
            templates_data = yaml.safe_load(f)
        
        return templates_data.get('templates', {})
    
    def validate_media_type(self, media_type: str) -> bool:
        """Validate that media_type exists in tones configuration.
        
        Args:
            media_type: Media type to validate
            
        Returns:
            True if valid, False otherwise
        """
        tones = self.load_tones()
        return media_type in tones
    
    def get_tone_config(self, media_type: str) -> Dict[str, Any]:
        """Get tone configuration for a specific media type.
        
        Args:
            media_type: Media type identifier
            
        Returns:
            Tone configuration dictionary
            
        Raises:
            ValueError: If media_type is not found
        """
        tones = self.load_tones()
        if media_type not in tones:
            available = ', '.join(tones.keys())
            raise ConfigurationError(
                f"Invalid media_type: {media_type}\n"
                f"Available types: {available}"
            )
        return tones[media_type]
    
    def get_template_config(self, media_type: str) -> Dict[str, Any]:
        """Get template configuration for a specific media type.
        
        Args:
            media_type: Media type identifier
            
        Returns:
            Template configuration dictionary
            
        Raises:
            ValueError: If media_type is not found
        """
        templates = self.load_templates()
        if media_type not in templates:
            available = ', '.join(templates.keys())
            raise ConfigurationError(
                f"Invalid media_type: {media_type}\n"
                f"Available types: {available}"
            )
        return templates[media_type]
