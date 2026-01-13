"""Markdown formatting utilities for articles."""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import urlparse, urlunparse
from .config_loader import ConfigLoader


def format_article(
    article_dict: Dict[str, str],
    template_config: Dict[str, Any],
    topic: str,
    media_type: str
) -> str:
    """Format article dictionary into markdown.
    
    Args:
        article_dict: Dictionary with article sections
        template_config: Template configuration from templates.yaml
        topic: Article topic
        media_type: Media type identifier
        
    Returns:
        Formatted markdown string
    """
    lines = []
    
    # Add metadata header
    lines.append("---")
    lines.append(f"title: {article_dict.get('headline') or article_dict.get('title', topic)}")
    lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"media_type: {media_type}")
    lines.append(f"topic: {topic}")
    lines.append("---")
    lines.append("")
    
    # Get structure from template
    structure = template_config.get('structure', [])
    
    # Format each section according to template - as continuous flowing text
    # First, add headline/title as H1
    headline_content = None
    if 'headline' in article_dict:
        headline_content = article_dict.get('headline')
    elif 'title' in article_dict:
        headline_content = article_dict.get('title')
    
    if headline_content and headline_content.strip():
        lines.append(f"# {headline_content.strip()}")
        lines.append("")
    
    # Track previous section for smooth transitions
    previous_section = None
    previous_content = None
    
    # Format each section according to template
    for section_def in structure:
        section_name = section_def.get('section')
        if not section_name:
            continue
        
        # Skip sources/references sections - they are added separately via format_sources()
        if section_name in ['sources', 'references']:
            continue
        
        # Skip title/headline (already added above)
        if section_name in ['title', 'headline']:
            continue
        
        # Check if section exists in article_dict
        section_content = article_dict.get(section_name)
        
        # Skip optional sections that don't exist
        if not section_content and not section_def.get('required', True):
            continue
        
        # Skip if content is empty
        if not section_content or not section_content.strip():
            if section_def.get('required', True):
                # For required sections, skip placeholder - let it be empty rather than show placeholder text
                continue
            else:
                continue
        
        # Skip placeholder text that looks like "[Description text]"
        if section_content.strip().startswith('[') and section_content.strip().endswith(']'):
            if section_def.get('required', True):
                # For required sections, skip placeholder
                continue
            else:
                continue
        
        # Clean up section content
        section_content = section_content.strip()
        
        # Add section content as continuous flowing text (no headers)
        # Ensure smooth transition from previous section
        if previous_content:
            # Check if previous section ended with punctuation
            prev_ends_punct = previous_content.rstrip()[-1:] in '.!?'
            # Check if current section starts with capital (likely new sentence)
            curr_starts_cap = section_content and section_content[0].isupper()
            
            # If previous ended properly and current starts properly, just add paragraph break
            if prev_ends_punct and curr_starts_cap:
                lines.append("")
                lines.append(section_content)
            else:
                # Otherwise, ensure proper spacing
                lines.append("")
                lines.append(section_content)
        else:
            # First section after headline
            lines.append(section_content)
        
        previous_section = section_name
        previous_content = section_content
    
    return "\n".join(lines)


def clean_source_url(url: str) -> str:
    """Clean and normalize a source URL.
    
    Args:
        url: Raw URL string
        
    Returns:
        Cleaned URL string
    """
    if not url or url == '#':
        return '#'
    
    # Remove trailing whitespace first
    url = url.strip()
    
    # Fix common malformed URLs (missing closing parentheses, etc.)
    # Count opening and closing parentheses
    open_parens = url.count('(')
    close_parens = url.count(')')
    
    # If there's an opening paren but no closing paren, and URL doesn't end properly
    if open_parens > close_parens:
        # Check if URL ends abruptly (common in markdown parsing errors)
        if not url.endswith((')', '.', '/', 'html', 'pdf', 'htm', 'php', 'asp', 'aspx')):
            # Try to find where the URL should end
            # Look for common URL endings
            for ending in ['.html', '.pdf', '.htm', '.php', '.asp', '.aspx', '/']:
                if ending in url:
                    idx = url.rfind(ending)
                    if idx > 0:
                        url = url[:idx + len(ending)]
                        break
            # Add missing closing parentheses
            url += ')' * (open_parens - close_parens)
        else:
            # URL seems complete, just add missing closing parens
            url += ')' * (open_parens - close_parens)
    
    # Remove trailing punctuation that might have been accidentally included
    # But be careful not to remove valid URL characters
    url = url.rstrip('.,;:!?')
    
    # Validate URL format
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            # If no scheme, assume https
            url = f"https://{url}"
            parsed = urlparse(url)
        
        # Ensure we have a valid netloc
        if not parsed.netloc:
            return url.rstrip('.,;:!?)')
        
        # Reconstruct URL to normalize it
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    except Exception:
        # If URL parsing fails, return cleaned original
        cleaned = url.rstrip('.,;:!?)')
        # Basic validation - if it looks like a URL, return it
        if cleaned.startswith(('http://', 'https://')):
            return cleaned
        return '#'


def clean_source_snippet(snippet: str) -> str:
    """Clean a source snippet by removing HTML and excessive whitespace.
    
    Args:
        snippet: Raw snippet text
        
    Returns:
        Cleaned snippet text (max 250 chars for better readability)
    """
    if not snippet:
        return ""
    
    # Remove HTML tags
    snippet = re.sub(r'<[^>]+>', '', snippet)
    
    # Remove common navigation elements and page structure
    navigation_patterns = [
        r'Skip to main content',
        r'Skip to content',
        r'Search in:.*',
        r'Advanced search',
        r'\[.*?\]',  # Remove markdown-style links in snippets
        r'Home.*?',
        r'Menu.*?',
        r'Font Type:.*',
        r'Open AccessArticle',
        r'by\s+\w+.*',  # Remove author lines that got scraped
        r'Hostname:.*',
        r'Total loading time:.*',
        r'Render date:.*',
        r'Has data issue:.*',
        r'hasContentIssue.*',
        r'Article Menu',
        r'## Article Menu',
    ]
    for pattern in navigation_patterns:
        snippet = re.sub(pattern, '', snippet, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove lines that are just navigation or metadata
    lines = snippet.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip empty lines, navigation elements, and metadata
        if not line:
            continue
        # Skip navigation/metadata patterns
        skip_patterns = [
            'skip to', 'search', 'menu', 'home', 'hostname', 'render date', 'font type',
            'next article', 'previous article', 'journals', 'about', 'copyright',
            'thank you for visiting', 'you are using a browser', 'limited support',
            'cookie', 'privacy', 'terms', 'sign in', 'log in', 'register',
            'vol.:', 'original article', 'published:', 'received:', 'doi:',
            'arxiv:', 'computer science', 'title:', 'author:', 'abstract:',
            'introduction', 'conclusion', 'references', 'keywords:',
            'full article', 'read more', 'continue reading'
        ]
        if any(skip in line.lower() for skip in skip_patterns):
            continue
        # Skip lines that are just punctuation, URLs, or very short
        if len(line) < 10:
            continue
        # Skip lines that are mostly URLs or markdown links
        if line.count('http') > 1 or (line.startswith('http') and len(line) < 50):
            continue
        # Skip lines that look like markdown formatting artifacts
        if line.startswith('![') or line.startswith('](') or line.startswith('*'):
            if 'http' in line and len(line) < 100:
                continue
        cleaned_lines.append(line)
    
    snippet = ' '.join(cleaned_lines)
    
    # Remove excessive whitespace
    snippet = re.sub(r'\s+', ' ', snippet)
    snippet = snippet.strip()
    
    # Truncate to reasonable length (longer for better context)
    if len(snippet) > 250:
        # Try to truncate at sentence boundary
        truncated = snippet[:247]
        last_period = truncated.rfind('.')
        last_space = truncated.rfind(' ')
        if last_period > 200:
            snippet = truncated[:last_period + 1]
        elif last_space > 200:
            snippet = truncated[:last_space] + "..."
        else:
            snippet = truncated + "..."
    
    return snippet


def normalize_url_for_dedup(url: str) -> str:
    """Normalize URL for deduplication purposes.
    
    Args:
        url: URL string
        
    Returns:
        Normalized URL string for comparison
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        # Normalize: scheme + netloc + path (ignore query params and fragments)
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"
        # Remove trailing slashes for consistency
        normalized = normalized.rstrip('/')
        return normalized
    except Exception:
        return url.lower().rstrip('/')


def format_sources(sources: List[Dict[str, str]]) -> str:
    """Format source citations as markdown in a cohesive, newspaper-style format.
    
    Args:
        sources: List of source dictionaries with 'title', 'url', and optionally 'snippet'
        
    Returns:
        Formatted markdown string for sources section
    """
    if not sources:
        return ""
    
    # Deduplicate sources by URL
    seen_urls = set()
    unique_sources = []
    for source in sources:
        url = source.get('url', '')
        normalized_url = normalize_url_for_dedup(url)
        if normalized_url and normalized_url not in seen_urls:
            seen_urls.add(normalized_url)
            unique_sources.append(source)
    
    if not unique_sources:
        return ""
    
    lines = []
    lines.append("## Sources")
    lines.append("")
    
    for i, source in enumerate(unique_sources, 1):
        title = source.get('title', 'Untitled')
        url = source.get('url', '#')
        snippet = source.get('snippet', '')
        
        # Clean URL and snippet
        url = clean_source_url(url)
        snippet = clean_source_snippet(snippet)
        
        # Clean and format title - remove common prefixes and clean up
        title = title.strip()
        # Remove common prefixes that make titles awkward
        title = re.sub(r'^(Full article|Article|Paper|Research|Study):\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^\[.*?\]\s*', '', title)  # Remove markdown links in title
        title = title.strip()
        
        # Truncate very long titles intelligently (at word boundary)
        if len(title) > 120:
            truncated = title[:117]
            # Try to truncate at word boundary
            last_space = truncated.rfind(' ')
            if last_space > 100:
                title = truncated[:last_space] + "..."
            else:
                title = truncated + "..."
        
        # Format as clean numbered list with link
        # Use a clean, readable format
        lines.append(f"{i}. [{title}]({url})")
        
        # Add snippet if available and meaningful (not just navigation elements)
        if snippet and len(snippet.strip()) > 20:
            # Clean snippet one more time to remove any remaining artifacts
            snippet_clean = snippet.strip()
            # Remove any trailing URLs or markdown artifacts
            snippet_clean = re.sub(r'\s*\(https?://[^\s]+\)\s*$', '', snippet_clean)
            snippet_clean = re.sub(r'\s*\[.*?\]\(.*?\)\s*$', '', snippet_clean)
            # Only add if still meaningful after cleaning
            if len(snippet_clean.strip()) > 20:
                lines.append(f"   {snippet_clean}")
        
        # Add spacing between sources for readability
        lines.append("")
    
    return "\n".join(lines)


def format_search_results_for_prompt(results: List[Any]) -> str:
    """Format search results for inclusion in LLM prompts.
    
    Args:
        results: List of SearchResult objects
        
    Returns:
        Formatted string for prompt
    """
    if not results:
        return "No search results available."
    
    lines = []
    lines.append("Research Sources:")
    lines.append("")
    
    for i, result in enumerate(results, 1):
        lines.append(f"{i}. **{result.title}**")
        lines.append(f"   URL: {result.url}")
        if result.snippet:
            lines.append(f"   Summary: {result.snippet[:300]}...")
        lines.append("")
    
    return "\n".join(lines)


def generate_filename(template: str, topic: str, media_type: str) -> str:
    """Generate filename from template.
    
    Args:
        template: Filename template with {date}, {topic}, {media_type} placeholders
        topic: Article topic
        media_type: Media type
        
    Returns:
        Generated filename
    """
    # Sanitize topic for filename
    safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in topic)
    safe_topic = safe_topic.replace(' ', '_').lower()[:50]  # Limit length
    
    filename = template.format(
        date=datetime.now().strftime('%Y%m%d'),
        topic=safe_topic,
        media_type=media_type
    )
    
    return filename
