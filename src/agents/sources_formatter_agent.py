"""Sources Formatter Agent for cleaning and formatting source citations."""
from typing import List, Dict, Any
import json
from ..utils.llm import LLMProvider
from ..utils.logger import get_logger

logger = get_logger(__name__)

# #region agent log
DEBUG_LOG_PATH = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
# #endregion


class SourcesFormatterAgent:
    """Agent responsible for intelligently formatting and cleaning source citations."""
    
    def __init__(self, llm_provider: LLMProvider):
        """Initialize Sources Formatter Agent.
        
        Args:
            llm_provider: LLM provider for intelligent formatting
        """
        self.llm_provider = llm_provider
    
    def format_sources(
        self,
        sources: List[Dict[str, str]],
        verbose: bool = False
    ) -> str:
        """Format and clean source citations using LLM for intelligent processing.
        
        Args:
            sources: List of source dictionaries with 'title', 'url', and optionally 'snippet'
            verbose: Whether to log detailed progress
            
        Returns:
            Formatted markdown string for sources section
        """
        # #region agent log
        try:
            import os
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({"location":"sources_formatter_agent.py:34","message":"format_sources entry","data":{"sources_count":len(sources) if sources else 0},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C"}) + "\n")
        except Exception as e:
            logger.debug(f"Debug log write failed: {e}")
        # #endregion
        
        if not sources:
            return ""
        
        if verbose:
            logger.info(f"Formatting {len(sources)} sources with intelligent cleaning")
        
        try:
            # Build prompt for LLM to clean and format sources
            prompt = self._build_formatting_prompt(sources)
            
            # #region agent log
            try:
                import os
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({"location":"sources_formatter_agent.py:52","message":"before LLM generate","data":{"prompt_length":len(prompt)},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            except Exception as e:
                logger.debug(f"Debug log write failed: {e}")
            # #endregion
            
            # Get formatted sources from LLM
            # Use higher max_tokens for sources formatting (20 sources with descriptions need more tokens)
            # Estimate: ~200 tokens per source (title + URL + 50-150 word description) = ~4000 tokens minimum
            # Use 10000 to ensure we have enough headroom
            formatted_output = self.llm_provider.generate(prompt, max_tokens=10000)
            
            # #region agent log
            try:
                import os
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({"location":"sources_formatter_agent.py:56","message":"after LLM generate","data":{"output_length":len(formatted_output) if formatted_output else 0,"output_preview":formatted_output[:200] if formatted_output else "","output_end":formatted_output[-200:] if formatted_output and len(formatted_output) > 200 else ""},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            except Exception as e:
                logger.debug(f"Debug log write failed: {e}")
            # #endregion
            
            # Validate LLM output
            if not formatted_output or not formatted_output.strip():
                if verbose:
                    logger.warning("LLM returned empty output, using fallback")
                return self._fallback_format(sources)
            
            # Parse and validate the output
            formatted_sources = self._parse_formatted_output(formatted_output, sources)
            
            # #region agent log
            try:
                import os
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({"location":"sources_formatter_agent.py:66","message":"after parse_formatted_output","data":{"formatted_length":len(formatted_sources) if formatted_sources else 0,"formatted_preview":formatted_sources[:200] if formatted_sources else "","formatted_end":formatted_sources[-200:] if formatted_sources and len(formatted_sources) > 200 else ""},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except Exception as e:
                logger.debug(f"Debug log write failed: {e}")
            # #endregion
            
            return formatted_sources
            
        except Exception as e:
            # #region agent log
            try:
                import os
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({"location":"sources_formatter_agent.py:72","message":"exception in format_sources","data":{"error":str(e)},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            except Exception as e2:
                logger.debug(f"Debug log write failed: {e2}")
            # #endregion
            # Log error and fallback to basic formatter
            logger.warning(f"Sources formatting failed: {e}, using fallback")
            if verbose:
                logger.warning(f"Error details: {str(e)}")
            return self._fallback_format(sources)
    
    def _build_formatting_prompt(self, sources: List[Dict[str, str]]) -> str:
        """Build prompt for LLM to format sources intelligently.
        
        Args:
            sources: List of raw source dictionaries
            
        Returns:
            Formatting prompt
        """
        sources_text = []
        for i, source in enumerate(sources, 1):
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            snippet = source.get('snippet', '')
            
            sources_text.append(f"Source {i}:")
            sources_text.append(f"  Title: {title}")
            sources_text.append(f"  URL: {url}")
            if snippet:
                sources_text.append(f"  Snippet: {snippet[:300]}...")
            sources_text.append("")
        
        prompt = f"""You are an expert editor specializing in formatting academic and journalistic citations. Your task is to clean, format, and improve source citations for a professional article.

RAW SOURCES TO FORMAT:
{chr(10).join(sources_text)}

TASKS:
1. CLEAN TITLES: Remove navigation elements, markdown artifacts, prefixes like "Full article:", "[...]", etc. Extract the actual article/resource title.
2. VALIDATE URLs: Fix broken URLs, remove trailing parentheses or punctuation, ensure URLs are complete and valid.
3. IMPROVE SNIPPETS: Extract meaningful, relevant snippets (50-150 words) that provide context. Remove navigation elements, URLs, author lines, metadata, and other noise.
4. DEDUPLICATE: If multiple sources point to the same resource (same base URL), keep only the best one.
5. ORDER: Sort sources logically (by relevance or chronologically if appropriate).

OUTPUT FORMAT - CRITICAL CONSISTENCY:
Provide the formatted sources as clean markdown with ABSOLUTELY CONSISTENT formatting.

EXAMPLE OF EXACT FORMAT REQUIRED:

## Sources

1. [From Digital Twins to Digital Twin Prototypes: Concepts, Formalization, and Applications](https://arxiv.org/abs/2401.07985)
   This research explores the evolution of the digital twin concept, specifically formalizing the "Digital Twin Prototype" (DTP) as a distinct phase in the product lifecycle. The paper provides a theoretical framework for how DTPs serve as the precursor to operational twins, offering a structured approach to transition from initial design requirements to fully functional digital representations in complex engineering environments.

2. [Developing a Physical and Digital Twin: An Example Process Model](https://ieeexplore.ieee.org/document/9643681/)
   Published via IEEE, this paper outlines a comprehensive process model for the concurrent development of physical assets and their digital counterparts. It emphasizes the synchronization required between hardware engineering and software modeling, providing a roadmap for practitioners to ensure that the digital twin accurately reflects the physical system's behavior and specifications from the onset of the development cycle.

3. [Toward Digital Validation for Rapid Product Development Based on Digital Twin: A Framework](https://link.springer.com/article/10.1007/s00170-021-08475-4)
   This article presents a framework for digital validation, aiming to accelerate product development cycles. By utilizing digital twins, the authors demonstrate how virtual testing and validation can replace traditional, time-consuming physical iterations. The study highlights the role of high-fidelity models in predicting performance and identifying design flaws early in the prototyping phase.

CRITICAL REQUIREMENTS FOR CONSISTENCY:
- Titles must be clean, readable, and professional (no markdown artifacts, no navigation text, no prefixes like "Full article:")
- URLs must be valid and complete (no trailing parentheses, no broken links, properly formatted)
- Snippets must be meaningful and relevant (50-150 words, complete sentences, descriptive, professional)
- Each source MUST follow the EXACT same format:
  * Numbered list item (1., 2., 3., etc.) with markdown link [Title](URL)
  * Exactly three spaces of indentation for snippet (use spaces, not tabs)
  * Snippet length: 50-150 words (keep consistent across all sources - aim for similar length)
  * Snippet style: Complete sentences, descriptive, professional, no URLs or navigation elements
- Format must be ABSOLUTELY CONSISTENT across all sources:
  * Same indentation (exactly 3 spaces)
  * Same style (complete sentences, similar length)
  * Same structure (numbered item, link, indented snippet)
- Remove any sources that are duplicates or have invalid URLs
- Ensure all sources use the same formatting pattern - no variations in spacing, style, or structure
- Validate that URLs are complete and properly formatted before including

Format ALL sources following the example above with perfect consistency:
"""
        return prompt
    
    def _parse_formatted_output(
        self,
        formatted_output: str,
        original_sources: List[Dict[str, str]]
    ) -> str:
        """Parse LLM output and validate it.
        
        Args:
            formatted_output: LLM-generated formatted sources
            original_sources: Original source list for validation
            
        Returns:
            Validated formatted sources markdown
        """
        # #region agent log
        try:
            import os
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({"location":"sources_formatter_agent.py:150","message":"_parse_formatted_output entry","data":{"input_length":len(formatted_output) if formatted_output else 0},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except Exception as e:
            logger.debug(f"Debug log write failed: {e}")
        # #endregion
        
        # Extract the sources section from LLM output
        lines = formatted_output.split('\n')
        
        # Find the "## Sources" header
        sources_start = -1
        for i, line in enumerate(lines):
            if '## Sources' in line or '## SOURCES' in line:
                sources_start = i
                break
        
        if sources_start == -1:
            # If no header found, assume entire output is sources
            sources_start = 0
        
        # #region agent log
        try:
            import os
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({"location":"sources_formatter_agent.py:168","message":"found sources_start","data":{"sources_start":sources_start,"total_lines":len(lines)},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except Exception as e:
            logger.debug(f"Debug log write failed: {e}")
        # #endregion
        
        # Extract sources section
        sources_lines = lines[sources_start:]
        
        # Clean up the output
        formatted = '\n'.join(sources_lines).strip()
        
        # #region agent log
        try:
            import os
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({"location":"sources_formatter_agent.py:175","message":"after extraction","data":{"formatted_length":len(formatted) if formatted else 0,"formatted_end":formatted[-300:] if formatted and len(formatted) > 300 else formatted},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except Exception as e:
            logger.debug(f"Debug log write failed: {e}")
        # #endregion
        
        # Basic validation: ensure we have at least some sources
        if not formatted or len(formatted) < 50:
            logger.warning("LLM sources formatting produced minimal output, using fallback")
            # Fallback to basic formatting
            return self._fallback_format(original_sources)
        
        # Ensure we have the header
        if not formatted.startswith('##'):
            formatted = "## Sources\n\n" + formatted
        
        # #region agent log
        try:
            import os
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({"location":"sources_formatter_agent.py:189","message":"_parse_formatted_output exit","data":{"final_length":len(formatted) if formatted else 0,"final_end":formatted[-300:] if formatted and len(formatted) > 300 else formatted},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except Exception as e:
            logger.debug(f"Debug log write failed: {e}")
        # #endregion
        
        return formatted
    
    def _fallback_format(self, sources: List[Dict[str, str]]) -> str:
        """Fallback formatting if LLM output is invalid.
        
        Args:
            sources: Original source list
            
        Returns:
            Basic formatted sources
        """
        from ..utils.formatter import format_sources
        return format_sources(sources)
