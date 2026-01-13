"""Article Topic Extractor Agent for extracting research topics from articles."""
from typing import List
from ..utils.llm import LLMProvider
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ArticleTopicExtractor:
    """Agent responsible for extracting key research topics from article content."""
    
    def __init__(self, llm_provider: LLMProvider):
        """Initialize Article Topic Extractor Agent.
        
        Args:
            llm_provider: LLM provider for topic extraction
        """
        self.llm_provider = llm_provider
    
    def extract_topics(self, article_text: str, verbose: bool = False) -> List[str]:
        """Extract key research topics from article text.
        
        Args:
            article_text: Full article markdown/text content
            verbose: Whether to log detailed progress
            
        Returns:
            List of topic strings suitable for research queries
        """
        if not article_text or not article_text.strip():
            logger.warning("Empty article text provided")
            return []
        
        if verbose:
            logger.info("Extracting research topics from article...")
        
        try:
            prompt = self._build_extraction_prompt(article_text)
            
            # Get topics from LLM
            response = self.llm_provider.generate(prompt, max_tokens=2000)
            
            if verbose:
                logger.info("Parsing extracted topics...")
            
            # Parse response into list of topics
            topics = self._parse_topics(response)
            
            if verbose:
                logger.info(f"Extracted {len(topics)} research topics")
                for i, topic in enumerate(topics, 1):
                    logger.info(f"  Topic {i}: {topic}")
            
            return topics
            
        except Exception as e:
            logger.error(f"Failed to extract topics: {e}")
            if verbose:
                logger.error(f"Error details: {str(e)}")
            # Fallback: return empty list or try to extract from title
            return self._fallback_extraction(article_text)
    
    def _build_extraction_prompt(self, article_text: str) -> str:
        """Build prompt for LLM to extract research topics.
        
        Args:
            article_text: Full article content
            
        Returns:
            Extraction prompt
        """
        # Truncate article if too long (keep first 8000 chars for context)
        truncated_text = article_text[:8000] if len(article_text) > 8000 else article_text
        
        prompt = f"""You are an expert research analyst. Your task is to identify the key research topics, concepts, and claims mentioned in the following article that would benefit from academic or professional sources.

ARTICLE TEXT:
{truncated_text}

TASK:
Extract 3-5 key research topics or concepts from this article that would need sources or citations. Focus on:
1. Main concepts/theories mentioned (e.g., "Digital Twin Prototypes", "Physical Twin methodology")
2. Technologies/frameworks referenced (e.g., "sim-to-real gap", "autonomous vehicle validation")
3. Research areas discussed (e.g., "human-machine interaction", "hardware-software integration")
4. Key claims that need supporting sources (e.g., "shifting left in product development", "Level 4 and Level 5 autonomy")

OUTPUT FORMAT:
Return only the topics, one per line, without numbering, bullets, or additional text.
Each topic should be a concise, searchable research query (2-8 words).
Make topics specific enough to find relevant academic or professional sources.

Example output format:
Digital Twin Prototypes
Physical Twin methodology
sim-to-real gap in autonomous systems
hardware-software integration prototyping
human-machine interaction validation

Extract the research topics now:
"""
        return prompt
    
    def _parse_topics(self, response: str) -> List[str]:
        """Parse LLM response into list of topics.
        
        Args:
            response: LLM response text
            
        Returns:
            List of topic strings
        """
        if not response or not response.strip():
            return []
        
        # Split by newlines and clean up
        lines = response.split('\n')
        topics = []
        
        for line in lines:
            # Remove numbering, bullets, and whitespace
            cleaned = line.strip()
            
            # Skip empty lines
            if not cleaned:
                continue
            
            # Remove common prefixes
            prefixes_to_remove = ['- ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ', 
                                 '• ', '○ ', '▪ ', '▫ ']
            for prefix in prefixes_to_remove:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            
            # Remove trailing punctuation that might be part of formatting
            cleaned = cleaned.rstrip('.,;:')
            
            # Skip if too short or looks like a header/instruction
            if len(cleaned) < 5:
                continue
            if cleaned.lower().startswith(('example', 'output', 'format', 'task:', 'note:')):
                continue
            
            # Valid topic
            if cleaned:
                topics.append(cleaned)
        
        # Limit to 5 topics max
        topics = topics[:5]
        
        # If we got no valid topics, try a different parsing strategy
        if not topics:
            # Try splitting by common separators
            for separator in [';', '|', '•']:
                if separator in response:
                    parts = response.split(separator)
                    topics = [p.strip() for p in parts if p.strip() and len(p.strip()) > 5]
                    topics = topics[:5]
                    break
        
        return topics
    
    def _fallback_extraction(self, article_text: str) -> List[str]:
        """Fallback topic extraction if LLM extraction fails.
        
        Args:
            article_text: Article content
            
        Returns:
            List of fallback topics (may be empty)
        """
        # Try to extract title/first line as topic
        lines = article_text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for markdown header or first substantial line
            if line.startswith('# '):
                # Extract title, remove markdown
                title = line.replace('# ', '').replace('**', '').strip()
                if title and len(title) > 10:
                    return [title[:100]]  # Return title as single topic
            elif line and len(line) > 20 and not line.startswith('#'):
                # First substantial paragraph line
                # Extract first 10-15 words as topic
                words = line.split()[:15]
                return [' '.join(words)]
        
        return []