"""Pipeline orchestrator for article generation workflow."""
from typing import Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .agents.research_agent import ResearchAgent
from .agents.writer_agent import WriterAgent
from .agents.editor_agent import EditorAgent
from .agents.humanizer_agent import HumanizerAgent
from .agents.sources_formatter_agent import SourcesFormatterAgent
from .agents.article_topic_extractor import ArticleTopicExtractor
from .utils.llm import get_llm_provider
from .utils.search import get_search_provider
from .utils.config_loader import ConfigLoader, AppConfig
from .utils.formatter import format_article, format_sources, generate_filename
from .utils.validation import validate_topic, validate_media_type, validate_length, validate_max_results
from .utils.exceptions import ValidationError, ConfigurationError


class ArticlePipeline:
    """Orchestrates the article generation pipeline."""
    
    def __init__(self, config: AppConfig, config_loader: ConfigLoader):
        """Initialize pipeline.
        
        Args:
            config: Application configuration
            config_loader: Configuration loader
        """
        self.config = config
        self.config_loader = config_loader
        self.console = Console()
        
        # Initialize providers
        from .utils.env import EnvLoader
        env_loader = EnvLoader()
        
        self.llm_provider = get_llm_provider(config.llm, env_loader)
        self.search_provider = get_search_provider(config.search, env_loader)
        
        # Initialize agents
        self.research_agent = ResearchAgent(self.search_provider, self.llm_provider, config.search)
        self.writer_agent = WriterAgent(self.llm_provider, config_loader)
        self.editor_agent = EditorAgent(self.llm_provider, config_loader)
        self.humanizer_agent = HumanizerAgent(
            self.llm_provider,
            config_loader,
            enabled=config.humanizer.enabled,
            passes=config.humanizer.passes,
            intensity=config.humanizer.intensity
        )
        self.sources_formatter_agent = SourcesFormatterAgent(self.llm_provider)
        self.topic_extractor = ArticleTopicExtractor(self.llm_provider)
    
    def generate(
        self,
        topic: str,
        media_type: Optional[str] = None,
        length: Optional[str] = None,
        user_context: Optional[Dict[str, str]] = None,
        verbose: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate an article.
        
        Args:
            topic: Article topic
            media_type: Override media type from config
            length: Override length from config
            user_context: Optional user-provided context about their innovation
            verbose: Enable verbose output
            use_cache: Whether to use cached research if available
            
        Returns:
            Dictionary with article data and metadata
        """
        # Validate inputs
        validate_topic(topic)
        
        # Use provided values or fall back to config
        media_type = media_type or self.config.article.media_type
        length = length or self.config.article.length
        
        # Validate media type and length
        valid_media_types = list(self.config_loader.load_tones().keys())
        validate_media_type(media_type, valid_media_types)
        validate_length(length)
        validate_max_results(self.config.search.max_results)
        
        # Display context summary if provided
        context_summary = ""
        if user_context:
            novel_aspect = user_context.get('novel_aspect', '')[:100]
            context_summary = f"\nNovel Aspect: {novel_aspect}..."
        
        self.console.print(Panel.fit(
            f"[bold cyan]Generating Article[/bold cyan]\n"
            f"Topic: {topic}\n"
            f"Media Type: {media_type}\n"
            f"Length: {length}"
            + context_summary,
            border_style="cyan"
        ))
        
        # Step 1: Research
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Researching topic...", total=None)
            try:
                # Check cache status
                if use_cache and verbose:
                    from .utils.cache import ResearchCache
                    cache = ResearchCache()
                    if cache.cache_exists(topic, user_context, self.config.search):
                        self.console.print("[dim]Cache found, loading...[/dim]")
                    else:
                        self.console.print("[dim]Cache miss, performing fresh research...[/dim]")
                
                research_data = self.research_agent.research(
                    topic,
                    max_results=self.config.search.max_results,
                    user_context=user_context,
                    verbose=verbose,
                    use_cache=use_cache
                )
                progress.update(task, description="[green]Research complete")
            except Exception as e:
                progress.update(task, description=f"[red]Research failed: {e}")
                raise
        
        sources_count = len(research_data.get('sources', []))
        if verbose:
            queries = research_data.get('search_queries', [])
            self.console.print(f"[dim]Executed {len(queries)} search queries[/dim]")
            for i, query in enumerate(queries[:3], 1):
                self.console.print(f"[dim]  Query {i}: {query}[/dim]")
        self.console.print(f"[green]✓[/green] Found {sources_count} sources")
        
        # Step 2: Write
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Writing article...", total=None)
            try:
                article_dict = self.writer_agent.write(
                    research_data,
                    topic,
                    media_type,
                    length,
                    user_context=user_context,
                    verbose=verbose
                )
                progress.update(task, description="[green]Writing complete")
            except Exception as e:
                progress.update(task, description=f"[red]Writing failed: {e}")
                raise
        
        sections_count = len(article_dict)
        if verbose:
            section_names = list(article_dict.keys())
            self.console.print(f"[dim]Generated sections: {', '.join(section_names[:5])}{'...' if len(section_names) > 5 else ''}[/dim]")
        self.console.print(f"[green]✓[/green] Article written ({sections_count} sections)")
        
        # Step 3: Edit
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Editing article...", total=None)
            try:
                edited_dict = self.editor_agent.edit(
                    article_dict,
                    media_type,
                    fact_check=self.config.article.fact_check,
                    verbose=verbose
                )
                progress.update(task, description="[green]Editing complete")
            except Exception as e:
                progress.update(task, description=f"[red]Editing failed: {e}")
                # Use original if editing fails
                edited_dict = article_dict
                self.console.print(f"[yellow]⚠[/yellow] Editing failed, using original: {e}")
        
        if verbose:
            self.console.print("[dim]Refined article quality and flow[/dim]")
        self.console.print("[green]✓[/green] Article refined")
        
        # Step 4: Humanize
        if self.config.humanizer.enabled:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Humanizing article...", total=None)
                try:
                    humanized_dict = self.humanizer_agent.humanize(
                        edited_dict,
                        media_type,
                        verbose=verbose
                    )
                    progress.update(task, description="[green]Humanization complete")
                except Exception as e:
                    progress.update(task, description=f"[red]Humanization failed: {e}")
                    # Use edited version if humanization fails
                    humanized_dict = edited_dict
                    self.console.print(f"[yellow]⚠[/yellow] Humanization failed, using edited version: {e}")
            
            if verbose:
                self.console.print("[dim]Applied humanization techniques for natural writing[/dim]")
            self.console.print("[green]✓[/green] Article humanized")
        else:
            humanized_dict = edited_dict
        
        # Remove sources section from article_dict if it exists (to prevent duplication)
        # Sources will be added separately via format_sources()
        if 'sources' in humanized_dict:
            del humanized_dict['sources']
        if 'references' in humanized_dict:
            del humanized_dict['references']
        
        # Format article
        template_config = self.config_loader.get_template_config(media_type)
        article_markdown = format_article(
            humanized_dict,
            template_config,
            topic,
            media_type
        )
        
        # Add sources if enabled - use Sources Formatter Agent for intelligent formatting
        if self.config.article.include_sources and research_data.get('sources'):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Formatting sources...", total=None)
                try:
                    # Handle both SearchResult objects and dictionaries
                    sources_list = []
                    for source in research_data['sources']:
                        if isinstance(source, dict):
                            sources_list.append({
                                'title': source.get('title', 'No title'),
                                'url': source.get('url', ''),
                                'snippet': source.get('snippet', '')
                            })
                        else:
                            # SearchResult object
                            sources_list.append({
                                'title': source.title,
                                'url': source.url,
                                'snippet': source.snippet
                            })
                    
                    # Use Sources Formatter Agent for intelligent formatting
                    # #region agent log
                    import json, os
                    try:
                        log_path = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"location":"pipeline.py:263","message":"before format_sources call","data":{"sources_count":len(sources_list),"article_length_before":len(article_markdown)},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"D,E"}) + "\n")
                    except Exception as e:
                        pass
                    # #endregion
                    
                    sources_markdown = self.sources_formatter_agent.format_sources(
                        sources_list,
                        verbose=verbose
                    )
                    
                    # #region agent log
                    import json, os
                    try:
                        log_path = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"location":"pipeline.py:270","message":"after format_sources call","data":{"sources_markdown_length":len(sources_markdown) if sources_markdown else 0,"sources_markdown_preview":sources_markdown[:200] if sources_markdown else "","sources_markdown_end":sources_markdown[-300:] if sources_markdown and len(sources_markdown) > 300 else sources_markdown},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"D,E"}) + "\n")
                    except Exception as e:
                        pass
                    # #endregion
                    
                    # Fallback to basic formatter if agent output is empty
                    if not sources_markdown or len(sources_markdown.strip()) < 50:
                        if verbose:
                            self.console.print("[dim]Sources formatter produced minimal output, using fallback[/dim]")
                        sources_markdown = format_sources(sources_list)
                    
                    if sources_markdown:
                        article_markdown += "\n\n" + sources_markdown
                    
                    # #region agent log
                    import json, os
                    try:
                        log_path = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"location":"pipeline.py:278","message":"after appending sources","data":{"article_length_after":len(article_markdown),"article_end":article_markdown[-500:] if len(article_markdown) > 500 else article_markdown},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"D,E"}) + "\n")
                    except Exception as e:
                        pass
                    # #endregion
                    
                    progress.update(task, description="[green]Sources formatted")
                except Exception as e:
                    progress.update(task, description=f"[yellow]Sources formatting failed, using fallback: {e}")
                    # Fallback to basic formatter on error
                    sources_list = []
                    for source in research_data['sources']:
                        if isinstance(source, dict):
                            sources_list.append({
                                'title': source.get('title', 'No title'),
                                'url': source.get('url', ''),
                                'snippet': source.get('snippet', '')
                            })
                        else:
                            sources_list.append({
                                'title': source.title,
                                'url': source.url,
                                'snippet': source.snippet
                            })
                    sources_markdown = format_sources(sources_list)
                    if sources_markdown:
                        article_markdown += "\n\n" + sources_markdown
        
        return {
            'article_dict': humanized_dict,
            'article_markdown': article_markdown,
            'research_data': research_data,
            'metadata': {
                'topic': topic,
                'media_type': media_type,
                'length': length,
                'sources_count': len(research_data.get('sources', []))
            }
        }
    
    def save(self, article_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Save article to file.
        
        Args:
            article_data: Article data from generate()
            output_path: Optional output path (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        import os
        from pathlib import Path
        
        if output_path:
            file_path = Path(output_path)
        else:
            # Generate filename
            output_dir = Path(self.config.output.directory)
            output_dir.mkdir(exist_ok=True)
            
            filename = generate_filename(
                self.config.output.filename_template,
                article_data['metadata']['topic'],
                article_data['metadata']['media_type']
            )
            file_path = output_dir / filename
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        # #region agent log
        import json, os
        try:
            log_path = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a') as f:
                f.write(json.dumps({"location":"pipeline.py:343","message":"before file write","data":{"file_path":str(file_path),"content_length":len(article_data['article_markdown']),"content_end":article_data['article_markdown'][-500:] if len(article_data['article_markdown']) > 500 else article_data['article_markdown']},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + "\n")
        except Exception as e:
            pass
        # #endregion
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(article_data['article_markdown'])
        
        # #region agent log
        import json, os
        try:
            log_path = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            file_size = os.path.getsize(file_path)
            with open(log_path, 'a') as f:
                f.write(json.dumps({"location":"pipeline.py:348","message":"after file write","data":{"file_path":str(file_path),"file_size":file_size,"expected_size":len(article_data['article_markdown'].encode('utf-8'))},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + "\n")
        except Exception as e:
            pass
        # #endregion
        
        return str(file_path)
    
    def find_sources_for_article(
        self,
        article_path: str,
        output_path: Optional[str] = None,
        verbose: bool = False,
        use_cache: bool = True
    ) -> str:
        """Find and format sources for an existing article.
        
        Args:
            article_path: Path to the article markdown file
            output_path: Optional output path for sources (auto-generated if not provided)
            verbose: Enable verbose output
            use_cache: Whether to use cached research if available
            
        Returns:
            Path to the saved sources file
            
        Raises:
            FileNotFoundError: If article file doesn't exist
            ValueError: If article file is empty or invalid
        """
        from pathlib import Path
        
        # Read article file
        article_file = Path(article_path)
        if not article_file.exists():
            raise FileNotFoundError(f"Article file not found: {article_path}")
        
        # Check if it's a directory
        if article_file.is_dir():
            raise ValueError(f"Path is a directory, not a file: {article_path}")
        
        # Check file size
        file_size = article_file.stat().st_size
        if file_size == 0:
            raise ValueError(
                f"Article file is empty (0 bytes): {article_path}\n"
                "Please ensure the file has been saved with content."
            )
        
        if verbose:
            self.console.print(f"[cyan]Reading article from: {article_path}[/cyan]")
            self.console.print(f"[dim]File size: {file_size} bytes[/dim]")
        
        try:
            with open(article_file, 'r', encoding='utf-8') as f:
                article_text = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read article file: {e}")
        
        if not article_text or not article_text.strip():
            raise ValueError(
                f"Article file appears empty after reading: {article_path}\n"
                "The file may contain only whitespace or have encoding issues."
            )
        
        self.console.print(Panel.fit(
            f"[bold cyan]Finding Sources for Article[/bold cyan]\n"
            f"Article: {article_file.name}",
            border_style="cyan"
        ))
        
        # Step 1: Extract topics from article
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Extracting research topics...", total=None)
            try:
                topics = self.topic_extractor.extract_topics(article_text, verbose=verbose)
                progress.update(task, description="[green]Topics extracted")
            except Exception as e:
                progress.update(task, description=f"[red]Topic extraction failed: {e}")
                raise
        
        if not topics:
            self.console.print("[yellow]⚠[/yellow] No topics extracted, using article title as fallback")
            # Fallback: use first line or filename as topic
            first_line = article_text.split('\n')[0].strip()
            if first_line.startswith('#'):
                topics = [first_line.replace('#', '').replace('*', '').strip()]
            else:
                topics = [article_file.stem]
        
        self.console.print(f"[green]✓[/green] Extracted {len(topics)} research topics")
        if verbose:
            for i, topic in enumerate(topics, 1):
                self.console.print(f"[dim]  Topic {i}: {topic}[/dim]")
        
        # Step 2: Research each topic and collect sources
        all_sources = []
        seen_urls = set()
        
        for i, topic in enumerate(topics, 1):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Researching topic {i}/{len(topics)}: {topic[:50]}...", total=None)
                try:
                    research_data = self.research_agent.research(
                        topic,
                        max_results=self.config.search.max_results,
                        user_context=None,
                        verbose=verbose,
                        use_cache=use_cache
                    )
                    
                    # Collect unique sources
                    for source in research_data.get('sources', []):
                        if isinstance(source, dict):
                            url = source.get('url', '')
                        else:
                            url = source.url
                        
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_sources.append(source)
                    
                    progress.update(task, description=f"[green]Topic {i} researched")
                except Exception as e:
                    progress.update(task, description=f"[yellow]Topic {i} research failed: {e}")
                    if verbose:
                        self.console.print(f"[dim]  Warning: {e}[/dim]")
                    continue
        
        sources_count = len(all_sources)
        self.console.print(f"[green]✓[/green] Found {sources_count} unique sources")
        
        if sources_count == 0:
            self.console.print("[yellow]⚠[/yellow] No sources found. Check your search configuration.")
            # Still create an empty sources file
            sources_markdown = "## Sources\n\nNo sources found."
        else:
            # Step 3: Format sources
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Formatting sources...", total=None)
                try:
                    # Convert sources to dict format for formatter
                    sources_list = []
                    for source in all_sources:
                        if isinstance(source, dict):
                            sources_list.append({
                                'title': source.get('title', 'No title'),
                                'url': source.get('url', ''),
                                'snippet': source.get('snippet', '')
                            })
                        else:
                            sources_list.append({
                                'title': source.title,
                                'url': source.url,
                                'snippet': source.snippet
                            })
                    
                    sources_markdown = self.sources_formatter_agent.format_sources(
                        sources_list,
                        verbose=verbose
                    )
                    
                    # Fallback to basic formatter if agent output is empty
                    if not sources_markdown or len(sources_markdown.strip()) < 50:
                        if verbose:
                            self.console.print("[dim]Sources formatter produced minimal output, using fallback[/dim]")
                        from .utils.formatter import format_sources
                        sources_markdown = format_sources(sources_list)
                    
                    progress.update(task, description="[green]Sources formatted")
                except Exception as e:
                    progress.update(task, description=f"[yellow]Formatting failed: {e}")
                    # Fallback to basic formatter
                    from .utils.formatter import format_sources
                    sources_list = []
                    for source in all_sources:
                        if isinstance(source, dict):
                            sources_list.append({
                                'title': source.get('title', 'No title'),
                                'url': source.get('url', ''),
                                'snippet': source.get('snippet', '')
                            })
                        else:
                            sources_list.append({
                                'title': source.title,
                                'url': source.url,
                                'snippet': source.snippet
                            })
                    sources_markdown = format_sources(sources_list)
        
        # Step 4: Determine output path
        if output_path:
            output_file = Path(output_path)
        else:
            # Generate output filename: {original_basename}-sources.md in same directory
            output_file = article_file.parent / f"{article_file.stem}-sources.md"
        
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write sources to file
        if verbose:
            self.console.print(f"[cyan]Writing sources to: {output_file}[/cyan]")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sources_markdown)
        except Exception as e:
            raise ValueError(f"Failed to write sources file: {e}")
        
        return str(output_file)