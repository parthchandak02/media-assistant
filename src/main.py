#!/usr/bin/env python3
"""CLI interface for Media Article Writer."""
import sys
from pathlib import Path

# Handle both script and module execution
if __name__ == '__main__' and __package__ is None:
    # Running as script, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.panel import Panel

from src.pipeline import ArticlePipeline
from src.utils.config_loader import ConfigLoader
from src.utils.env import EnvLoader
from src.utils.validation import validate_topic, validate_media_type, validate_length
from src.utils.exceptions import ValidationError, ConfigurationError
from src.utils.context_gatherer import gather_user_context, load_context_from_file, UserContext
from src.utils.logger import setup_logger
from src.utils.cache import ResearchCache
import logging


console = Console()


@click.command()
@click.option(
    '--topic',
    required=False,
    help='Topic or achievement to write about (required unless using --find-sources)'
)
@click.option(
    '--media-type',
    type=click.Choice(['scientific_journal', 'research_magazine', 'tech_news', 'academic_news']),
    help='Media type (overrides config.yaml)'
)
@click.option(
    '--config',
    default='config.yaml',
    type=click.Path(exists=True),
    help='Path to config.yaml file'
)
@click.option(
    '--output',
    type=click.Path(),
    help='Output file path (auto-generated if not provided)'
)
@click.option(
    '--length',
    type=click.Choice(['short', 'medium', 'long']),
    help='Article length (overrides config.yaml)'
)
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Enable interactive context gathering (default: True)'
)
@click.option(
    '--context-file',
    type=click.Path(exists=True),
    help='Load user context from JSON file instead of interactive prompts'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    default=False,
    help='Enable verbose output showing detailed progress and operations'
)
@click.option(
    '--use-cache/--no-cache',
    default=True,
    help='Use cached research if available (default: True)'
)
@click.option(
    '--fresh-research',
    is_flag=True,
    default=False,
    help='Force fresh research (alias for --no-cache)'
)
@click.option(
    '--clear-cache',
    is_flag=True,
    default=False,
    help='Clear cache for the specified topic'
)
@click.option(
    '--clear-all-cache',
    is_flag=True,
    default=False,
    help='Clear all cached research data'
)
@click.option(
    '--find-sources',
    type=click.Path(exists=True),
    help='Find sources for an existing article file (path to article .md file)'
)
@click.option(
    '--sources-output',
    type=click.Path(),
    help='Output path for sources file (only used with --find-sources, defaults to {article-name}-sources.md)'
)
def main(topic, media_type, config, output, length, interactive, context_file, verbose, use_cache, fresh_research, clear_cache, clear_all_cache, find_sources, sources_output):
    """Generate a human-like media article about a topic.
    
    Example:
        python src/main.py --topic "My quantum computing research" --media-type research_magazine
    """
    try:
        # Initialize logger based on verbose flag
        # Use root logger ("") so all child loggers inherit the configuration
        log_level = logging.DEBUG if verbose else logging.INFO
        setup_logger(name="", level=log_level, console_output=True)
        
        # Handle find-sources mode (skip normal article generation)
        if find_sources:
            # Load configuration
            console.print("[cyan]Loading configuration...[/cyan]")
            config_loader = ConfigLoader(config_path=config)
            app_config = config_loader.load_config()
            
            # Validate environment
            console.print("[cyan]Validating API keys...[/cyan]")
            env_loader = EnvLoader()
            try:
                env_loader.validate_llm_keys(app_config.llm.provider)
                env_loader.validate_search_keys(app_config.search.provider)
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("\n[yellow]Please set up your .env file with required API keys.[/yellow]")
                console.print("See .env.example for reference.")
                sys.exit(1)
            
            # Initialize pipeline
            pipeline = ArticlePipeline(app_config, config_loader)
            
            # Find sources for article
            try:
                sources_path = pipeline.find_sources_for_article(
                    article_path=find_sources,
                    output_path=sources_output,
                    verbose=verbose,
                    use_cache=use_cache
                )
                
                # Success message
                console.print("\n")
                console.print(Panel.fit(
                    f"[bold green]Sources Found Successfully![/bold green]\n\n"
                    f"Article: {find_sources}\n"
                    f"Sources Output: [cyan]{sources_path}[/cyan]",
                    border_style="green"
                ))
            except FileNotFoundError as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
                sys.exit(1)
            
            sys.exit(0)
        
        # Handle cache clearing operations
        if clear_all_cache:
            cache = ResearchCache()
            if cache.clear_all_cache():
                console.print("[green]✓[/green] All research cache cleared")
            else:
                console.print("[yellow]⚠[/yellow] Failed to clear cache")
            sys.exit(0)
        
        # Validate input (needed for cache clearing with topic and normal article generation)
        if not topic:
            console.print("[red]Error: --topic is required unless using --find-sources[/red]")
            sys.exit(1)
        
        if clear_cache or not clear_all_cache:
            validate_topic(topic)
        
        # Handle cache clearing for specific topic
        if clear_cache:
            # Load config to get search config for cache key
            config_loader = ConfigLoader(config_path=config)
            app_config = config_loader.load_config()
            
            # Gather user context if provided
            user_context = None
            if context_file:
                context_obj = load_context_from_file(context_file)
                if context_obj:
                    user_context = context_obj.to_dict()
            
            cache = ResearchCache()
            if cache.invalidate_cache(topic, user_context, app_config.search):
                console.print(f"[green]✓[/green] Cache cleared for topic: {topic}")
            else:
                console.print(f"[yellow]⚠[/yellow] No cache found for topic: {topic}")
            sys.exit(0)
        
        # Handle fresh research flag
        if fresh_research:
            use_cache = False
        
        # Load configuration
        console.print("[cyan]Loading configuration...[/cyan]")
        config_loader = ConfigLoader(config_path=config)
        app_config = config_loader.load_config()
        
        # Get valid media types from config
        valid_media_types = list(config_loader.load_tones().keys())
        
        # Validate and override config with CLI arguments
        if media_type:
            validate_media_type(media_type, valid_media_types)
            app_config.article.media_type = media_type
        else:
            # Validate default media type from config
            validate_media_type(app_config.article.media_type, valid_media_types)
        
        if length:
            validate_length(length)
            app_config.article.length = length
        
        # Validate environment
        console.print("[cyan]Validating API keys...[/cyan]")
        env_loader = EnvLoader()
        try:
            env_loader.validate_llm_keys(app_config.llm.provider)
            env_loader.validate_search_keys(app_config.search.provider)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("\n[yellow]Please set up your .env file with required API keys.[/yellow]")
            console.print("See .env.example for reference.")
            sys.exit(1)
        
        # Gather user context if requested
        user_context = None
        if context_file:
            context_obj = load_context_from_file(context_file)
            if context_obj:
                user_context = context_obj.to_dict()
        elif interactive:
            context_obj = gather_user_context(interactive=True)
            if context_obj:
                user_context = context_obj.to_dict()
        
        # Initialize pipeline
        pipeline = ArticlePipeline(app_config, config_loader)
        
        # Generate article
        article_data = pipeline.generate(
            topic=topic,
            media_type=media_type,
            length=length,
            user_context=user_context,
            verbose=verbose,
            use_cache=use_cache
        )
        
        # Save article
        output_path = pipeline.save(article_data, output_path=output)
        
        # Success message
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]Article Generated Successfully![/bold green]\n\n"
            f"Topic: {topic}\n"
            f"Media Type: {article_data['metadata']['media_type']}\n"
            f"Sources: {article_data['metadata']['sources_count']}\n"
            f"Output: [cyan]{output_path}[/cyan]",
            border_style="green"
        ))
        
    except ValidationError as e:
        console.print(f"[red]Validation Error: {e}[/red]")
        sys.exit(1)
    except ConfigurationError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        console.print("\n[yellow]Please check your config.yaml file.[/yellow]")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Please ensure config.yaml exists.[/yellow]")
        console.print("Copy config.yaml.example to config.yaml and configure it.")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == '__main__':
    main()
