"""Research Agent for gathering information via web search."""
from typing import Dict, List, Any, Optional
from ..utils.search import SearchProvider, SearchResult
from ..utils.llm import LLMProvider
from ..utils.formatter import format_search_results_for_prompt
from ..utils.logger import get_logger
from ..utils.exceptions import LLMProviderError, SearchProviderError
from ..utils.cache import ResearchCache
from ..utils.config_loader import SearchConfig

logger = get_logger(__name__)


class ResearchAgent:
    """Agent responsible for researching a topic via web search."""
    
    def __init__(self, search_provider: SearchProvider, llm_provider: LLMProvider, search_config: Optional[SearchConfig] = None):
        """Initialize Research Agent.
        
        Args:
            search_provider: Search provider instance
            llm_provider: LLM provider for query generation and synthesis
            search_config: Search configuration for cache key generation
        """
        self.search_provider = search_provider
        self.llm_provider = llm_provider
        self.search_config = search_config
        self.cache = ResearchCache()
    
    def research(self, topic: str, max_results: int = 10, user_context: Optional[Dict[str, str]] = None, verbose: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """Research a topic and gather relevant information.
        
        Args:
            topic: Topic to research
            max_results: Maximum number of search results
            user_context: Optional user-provided context about their innovation
            verbose: Enable verbose logging
            use_cache: Whether to use cached research if available
            
        Returns:
            Dictionary with research findings:
            {
                'sources': List[SearchResult],
                'key_findings': str,
                'context': str,
                'search_queries': List[str],
                'user_context': Optional[Dict[str, str]]
            }
        """
        # Create search config for cache key if not provided
        cache_search_config = self.search_config
        if cache_search_config is None:
            # Try to extract from search provider
            if hasattr(self.search_provider, 'config'):
                cache_search_config = self.search_provider.config
            else:
                # Create a minimal SearchConfig for cache key generation
                from ..utils.config_loader import SearchConfig
                # Try to determine provider from class name
                provider_name = self.search_provider.__class__.__name__.replace('Provider', '').lower()
                cache_search_config = SearchConfig(
                    provider=provider_name if provider_name != 'searchprovider' else "unknown",
                    max_results=max_results,
                    include_domains=[]
                )
        
        # Check cache first
        if use_cache:
            cached_research = self.cache.load_research(topic, user_context, cache_search_config)
            if cached_research:
                if verbose:
                    logger.info("Cache hit: Using cached research data")
                else:
                    logger.debug("Cache hit: Using cached research data")
                return cached_research
        
        if verbose:
            logger.info("Cache miss: Performing fresh research")
        
        # Step 1: Generate effective search queries (enhanced with user context)
        search_queries = self._generate_search_queries(topic, user_context, verbose=verbose)
        
        # Step 2: Execute searches
        all_results = []
        queries_to_execute = search_queries[:3]  # Limit to 3 queries to avoid too many API calls
        
        if verbose:
            logger.info(f"Executing {len(queries_to_execute)} search queries")
        
        for i, query in enumerate(queries_to_execute, 1):
            if verbose:
                logger.info(f"Query {i}/{len(queries_to_execute)}: {query}")
            try:
                results = self.search_provider.search(query, max_results=max_results)
                all_results.extend(results)
                if verbose:
                    logger.info(f"  → Found {len(results)} results")
            except SearchProviderError as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                if verbose:
                    logger.warning(f"  → Query failed: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error during search for query '{query}': {e}")
                if verbose:
                    logger.warning(f"  → Unexpected error: {e}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        if verbose:
            logger.info(f"Deduplicated sources: {len(all_results)} → {len(unique_results)} unique")
        
        # Limit to max_results
        unique_results = unique_results[:max_results]
        
        if verbose and len(unique_results) < len(all_results):
            logger.info(f"Limited to {max_results} sources (from {len(unique_results)} unique)")
        
        # Step 3: Synthesize findings using LLM (enhanced with user context)
        if unique_results:
            if verbose:
                logger.info("Synthesizing findings from search results...")
            key_findings = self._synthesize_findings(topic, unique_results, user_context)
            if verbose:
                logger.info("Extracting broader context...")
            context = self._extract_context(topic, unique_results, user_context)
        else:
            key_findings = "No relevant information found."
            context = f"Limited information available about: {topic}"
            # If no results but user context provided, use it as fallback
            if user_context:
                key_findings = user_context.get('novel_aspect', key_findings)
                context = user_context.get('technology_details', context)
            if verbose:
                logger.warning("No search results found, using fallback context")
        
        result = {
            'sources': unique_results,
            'key_findings': key_findings,
            'context': context,
            'search_queries': search_queries
        }
        
        # Include user context in result for writer agent
        if user_context:
            result['user_context'] = user_context
        
        # Save to cache
        if use_cache:
            self.cache.save_research(topic, result, user_context, cache_search_config)
            if verbose:
                logger.info("Saved research to cache")
        
        return result
    
    def _generate_search_queries(self, topic: str, user_context: Optional[Dict[str, str]] = None, verbose: bool = False) -> List[str]:
        """Generate effective search queries from topic, enhanced with user context.
        
        Args:
            topic: Research topic
            user_context: Optional user-provided context about their innovation
            
        Returns:
            List of search query strings
        """
        # Build enhanced prompt with user context
        context_section = ""
        if user_context:
            novel_aspect = user_context.get('novel_aspect', '')
            technology_details = user_context.get('technology_details', '')
            use_cases = user_context.get('use_cases', '')
            
            context_section = f"""

IMPORTANT USER CONTEXT:
- Novel Aspect: {novel_aspect}
- Technology Details: {technology_details}
- Use Cases: {use_cases if use_cases else 'Not specified'}

Generate search queries that will help find information related to both the topic AND the user's novel approach.
Include terms from the user context to find relevant research and comparisons.
"""
        
        prompt = f"""Generate 3-5 effective web search queries to research the following topic.
The queries should be specific, focused, and likely to return relevant academic or professional information.

Topic: {topic}
{context_section}
Return only the search queries, one per line, without numbering or bullets.
Make queries diverse to cover different aspects of the topic.
"""
        
        try:
            if verbose:
                logger.info("Generating search queries using LLM...")
            response = self.llm_provider.generate(prompt)
            # Parse response into list of queries
            queries = [q.strip() for q in response.split('\n') if q.strip()]
            # Filter out any non-query lines
            queries = [q for q in queries if not q.startswith(('1.', '2.', '3.', '-', '*'))]
            # If parsing failed, use topic as query
            if not queries:
                queries = [topic]
            queries = queries[:5]  # Limit to 5 queries
            if verbose:
                logger.info(f"Generated {len(queries)} search queries")
            return queries
        except LLMProviderError as e:
            logger.warning(f"Failed to generate search queries: {e}. Using topic as fallback.")
            if verbose:
                logger.warning("Using topic as fallback query")
            return [topic]  # Fallback to topic itself
        except Exception as e:
            logger.warning(f"Unexpected error generating search queries: {e}. Using topic as fallback.")
            if verbose:
                logger.warning("Using topic as fallback query")
            return [topic]  # Fallback to topic itself
    
    def _synthesize_findings(self, topic: str, results: List[SearchResult], user_context: Optional[Dict[str, str]] = None) -> str:
        """Synthesize search results into key findings, prioritizing user-provided novel aspects.
        
        Args:
            topic: Research topic
            results: List of search results
            user_context: Optional user-provided context about their innovation
            
        Returns:
            Synthesized findings as text
        """
        results_text = format_search_results_for_prompt(results)
        
        user_context_section = ""
        if user_context:
            novel_aspect = user_context.get('novel_aspect', '')
            technology_details = user_context.get('technology_details', '')
            
            user_context_section = f"""

USER-PROVIDED NOVEL ASPECTS (FOR REFERENCE ONLY):
- Novel Approach: {novel_aspect}
- Technology Details: {technology_details}

IMPORTANT: The research findings below represent RELATED WORK by OTHER industry experts and researchers.
These findings show what others in the field are doing in similar or complementary areas.
Do NOT suggest that the user's technology uses, depends on, or is built from these research findings.
Instead, frame these findings as industry context showing what other experts are exploring.
"""
        
        # Extract conditional note to avoid f-string syntax issues
        note_text = ""
        if user_context:
            note_text = "Note how these findings relate to similar areas as the user-provided novel aspects, but keep them distinct as work by others."
        
        prompt = f"""Based on the following search results, synthesize the key findings related to this topic.

Topic: {topic}
{user_context_section}
{results_text}

CRITICAL INSTRUCTIONS:
- These search results represent work by OTHER industry experts and researchers, NOT the user's technology
- Synthesize findings as "related work" or "industry context" showing what others in the field are doing
- Frame findings as: "Other researchers have explored...", "Industry experts working in similar areas...", "Related work includes..."
- Do NOT suggest the user's technology uses, depends on, or incorporates these tools/frameworks
- Show what others are doing in similar/complementary areas to provide industry context

Provide a comprehensive summary of the key findings, facts, and relevant information.
Focus on information that would be useful for writing a professional article about this topic.
Be specific and cite which sources mention important points.
{note_text}
"""
        
        try:
            return self.llm_provider.generate(prompt)
        except LLMProviderError as e:
            logger.warning(f"Failed to synthesize findings: {e}. Using snippet fallback.")
            # Fallback: concatenate snippets
            return "\n\n".join([r.snippet for r in results[:5]])
        except Exception as e:
            logger.warning(f"Unexpected error synthesizing findings: {e}. Using snippet fallback.")
            # Fallback: concatenate snippets
            return "\n\n".join([r.snippet for r in results[:5]])
    
    def _extract_context(self, topic: str, results: List[SearchResult], user_context: Optional[Dict[str, str]] = None) -> str:
        """Extract broader context about the topic, incorporating user-provided context.
        
        Args:
            topic: Research topic
            results: List of search results
            user_context: Optional user-provided context about their innovation
            
        Returns:
            Contextual information as text
        """
        results_text = format_search_results_for_prompt(results)
        
        user_context_section = ""
        if user_context:
            problem_solved = user_context.get('problem_solved', '')
            use_cases = user_context.get('use_cases', '')
            
            user_context_section = f"""

USER-PROVIDED CONTEXT (FOR REFERENCE):
- Problem Being Solved: {problem_solved}
- Use Cases: {use_cases if use_cases else 'Not specified'}

IMPORTANT: The search results represent work by OTHER industry experts and researchers.
These findings show what others in the field are doing and provide industry context.
"""
        
        # Extract conditional note to avoid f-string syntax issues
        note_text = ""
        if user_context:
            note_text = "Note how the problem being solved relates to broader industry challenges, but keep the user's approach distinct from the research findings."
        
        prompt = f"""Based on the search results, provide broader context about this topic.
Explain why this topic matters, its significance, and how it fits into the larger field or domain.

Topic: {topic}
{user_context_section}
{results_text}

CRITICAL INSTRUCTIONS:
- These search results represent work by OTHER industry experts and researchers, NOT the user's technology
- Extract broader industry context showing what others in the field are doing
- Position findings as "industry context" or "related work by other experts"
- Frame as: "Researchers in this field have explored...", "Industry experts working on similar problems...", "The broader context includes work on..."
- Do NOT suggest the user's technology uses or depends on these research findings
- Provide context that helps readers understand the importance and background of the topic area

Provide context that would help a reader understand the importance and background of this topic.
{note_text}
"""
        
        try:
            return self.llm_provider.generate(prompt)
        except LLMProviderError as e:
            logger.warning(f"Failed to extract context: {e}. Using fallback context.")
            return f"Context about {topic} based on available sources."
        except Exception as e:
            logger.warning(f"Unexpected error extracting context: {e}. Using fallback context.")
            return f"Context about {topic} based on available sources."
