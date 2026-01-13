"""CrewAI-based Research Agent following CrewAI best practices."""
from typing import Dict, List, Any, Optional
import os
from ..utils.logger import get_logger
from ..utils.exceptions import SearchProviderError

logger = get_logger(__name__)

# Optional CrewAI imports
try:
    from crewai import Agent, Task, Crew
    from crewai_tools import EXASearchTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None
    EXASearchTool = None


class CrewAIResearchAgent:
    """Research Agent using CrewAI framework with EXASearchTool.
    
    This agent follows CrewAI best practices:
    - Clear role definition
    - Strategic tool usage
    - Context-aware research
    - Proper error handling
    """
    
    def __init__(
        self,
        exa_api_key: str,
        llm_model: Optional[str] = None,
        llm_provider: Optional[str] = None,
        max_results: int = 10,
        include_domains: Optional[List[str]] = None
    ):
        """Initialize CrewAI Research Agent.
        
        Args:
            exa_api_key: Exa API key for EXASearchTool
            llm_model: Optional LLM model name (defaults to OpenAI GPT-4)
            llm_provider: Optional LLM provider (defaults to OpenAI)
            max_results: Maximum number of search results
            include_domains: Optional list of domains to restrict search
            
        Raises:
            ImportError: If CrewAI is not installed
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI not available. Install with: pip install crewai crewai-tools"
            )
        
        self.max_results = max_results
        self.include_domains = include_domains or []
        
        # Initialize EXASearchTool following CrewAI best practices
        # CrewAI tools automatically use environment variables, but we can pass API key
        os.environ['EXA_API_KEY'] = exa_api_key
        self.exa_tool = EXASearchTool()
        
        # Configure LLM if provided
        self.llm_config = {}
        if llm_model:
            self.llm_config['model'] = llm_model
        if llm_provider:
            self.llm_config['provider'] = llm_provider
        
        # Create research agent following CrewAI best practices
        # Clear role definition, specific goal, detailed backstory
        self.research_agent = Agent(
            role="Research Specialist",
            goal="Conduct thorough, in-depth research on topics using advanced web search capabilities",
            backstory="""You are an expert researcher with access to advanced semantic search tools.
            You excel at finding relevant, authoritative sources and synthesizing information
            from multiple perspectives. You always verify information and provide comprehensive
            research findings with proper source attribution.""",
            tools=[self.exa_tool],
            verbose=True,
            allow_delegation=False,  # Specialist agent, no delegation needed
            **self.llm_config
        )
        
        logger.info("Initialized CrewAI Research Agent")
    
    def research(self, topic: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Research a topic using CrewAI agent framework.
        
        This method uses CrewAI's agent framework to conduct research,
        which provides better query optimization and result synthesis.
        
        Args:
            topic: Research topic
            max_results: Maximum number of results (overrides instance default)
            
        Returns:
            Dictionary with research findings:
            {
                'sources': List[Dict] with source information,
                'key_findings': str,
                'context': str,
                'search_queries': List[str],
                'research_summary': str
            }
        """
        if max_results is None:
            max_results = self.max_results
        
        try:
            # Create research task following CrewAI best practices
            # Clear description, expected output format
            research_task = Task(
                description=f"""Conduct comprehensive research on the following topic: {topic}
                
                Your research should:
                1. Use the EXASearchTool to find relevant, authoritative sources
                2. Synthesize information from multiple sources
                3. Identify key findings and important facts
                4. Provide context about why this topic matters
                5. Note any search queries you used
                
                Focus on finding academic, professional, or reputable sources.
                {"Limit search to these domains: " + ", ".join(self.include_domains) if self.include_domains else ""}
                """,
                expected_output="""A comprehensive research report containing:
                - Key findings (3-5 main points)
                - Context and significance
                - List of search queries used
                - Summary of sources found
                """,
                agent=self.research_agent,
                tools=[self.exa_tool]
            )
            
            # Create crew with single agent (research specialist)
            # Following CrewAI best practices: clear agent roles, proper task assignment
            crew = Crew(
                agents=[self.research_agent],
                tasks=[research_task],
                verbose=True,
                # Enable memory for context retention
                memory=True,
                # Enable caching for efficiency
                cache=True,
                # Set max RPM to avoid rate limits
                max_rpm=100
            )
            
            logger.info(f"Starting CrewAI research for topic: {topic}")
            
            # Execute research task
            result = crew.kickoff(inputs={"topic": topic})
            
            # Parse CrewAI result into our standard format
            research_data = self._parse_crewai_result(result, topic)
            
            logger.info(f"CrewAI research completed. Found {len(research_data.get('sources', []))} sources")
            
            return research_data
            
        except Exception as e:
            logger.error(f"CrewAI research error: {str(e)}")
            raise SearchProviderError(f"CrewAI research failed: {str(e)}")
    
    def _parse_crewai_result(self, result: Any, topic: str) -> Dict[str, Any]:
        """Parse CrewAI crew result into standard research data format.
        
        Args:
            result: CrewAI crew execution result
            topic: Original research topic
            
        Returns:
            Dictionary with research findings in standard format
        """
        # CrewAI returns a result object with various attributes
        # Extract the main content
        if hasattr(result, 'raw'):
            content = result.raw
        elif hasattr(result, 'content'):
            content = result.content
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)
        
        # Parse the content to extract structured information
        # CrewAI agents typically return well-formatted text
        sources = []
        key_findings = ""
        context = ""
        search_queries = []
        
        # Try to extract structured information from the result
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Identify sections
            if 'key findings' in line_lower or 'findings' in line_lower:
                current_section = 'findings'
                continue
            elif 'context' in line_lower or 'significance' in line_lower:
                current_section = 'context'
                continue
            elif 'sources' in line_lower or 'references' in line_lower:
                current_section = 'sources'
                continue
            elif 'queries' in line_lower or 'searches' in line_lower:
                current_section = 'queries'
                continue
            
            # Extract URLs as sources
            if 'http' in line:
                # Try to extract title and URL
                parts = line.split()
                url = None
                title = None
                
                for part in parts:
                    if part.startswith('http'):
                        url = part.rstrip('.,;')
                        break
                
                if url:
                    # Look for title in surrounding context
                    title = line.replace(url, '').strip(' -:.,;')
                    if not title or len(title) < 5:
                        title = "Source"
                    
                    sources.append({
                        'title': title,
                        'url': url,
                        'snippet': ''
                    })
            
            # Collect content by section
            if current_section == 'findings' and line.strip():
                if key_findings:
                    key_findings += '\n' + line
                else:
                    key_findings = line
            elif current_section == 'context' and line.strip():
                if context:
                    context += '\n' + line
                else:
                    context = line
        
        # If no structured data found, use the full content
        if not key_findings and content:
            key_findings = content[:1000]  # First 1000 chars as findings
            context = f"Research context for {topic}."
        
        return {
            'sources': sources[:self.max_results],
            'key_findings': key_findings or f"Research findings about {topic}.",
            'context': context or f"Context about {topic}.",
            'search_queries': search_queries,
            'research_summary': content  # Full CrewAI output
        }
