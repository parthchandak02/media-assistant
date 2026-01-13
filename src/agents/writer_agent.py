"""Writer Agent for generating articles with tone and template."""
from typing import Dict, Any, Optional
from ..utils.llm import LLMProvider
from ..utils.config_loader import ConfigLoader
from ..utils.xml_parser import parse_xml_sections, validate_xml_structure, extract_headline_from_text


class WriterAgent:
    """Agent responsible for writing articles based on research and style guidelines."""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        config_loader: ConfigLoader
    ):
        """Initialize Writer Agent.
        
        Args:
            llm_provider: LLM provider for article generation
            config_loader: Configuration loader for tones and templates
        """
        self.llm_provider = llm_provider
        self.config_loader = config_loader
    
    def write(
        self,
        research_data: Dict[str, Any],
        topic: str,
        media_type: str,
        length: str = "medium",
        user_context: Optional[Dict[str, str]] = None,
        verbose: bool = False
    ) -> Dict[str, str]:
        """Write an article based on research and style guidelines.
        
        Args:
            research_data: Research findings from ResearchAgent
            topic: Article topic
            media_type: Media type (scientific_journal, research_magazine, etc.)
            length: Article length (short, medium, long)
            user_context: Optional user-provided context about their innovation
            
        Returns:
            Dictionary with article sections
        """
        # Load tone and template configurations
        tone_config = self.config_loader.get_tone_config(media_type)
        template_config = self.config_loader.get_template_config(media_type)
        
        # Get word count targets
        word_counts = {
            'short': '500-800',
            'medium': '1000-1500',
            'long': '2000+'
        }
        target_words = word_counts.get(length, '1000-1500')
        
        # Extract user context from research_data if not provided directly
        if not user_context and 'user_context' in research_data:
            user_context = research_data['user_context']
        
        # Build comprehensive prompt
        if verbose:
            from ..utils.logger import get_logger
            logger = get_logger(__name__)
            logger.info("Building writing prompt...")
        
        prompt = self._build_writing_prompt(
            topic,
            research_data,
            tone_config,
            template_config,
            target_words,
            user_context
        )
        
        # Generate article
        if verbose:
            logger.info("Generating article content...")
        article_text = self.llm_provider.generate(prompt)
        
        # Parse article into sections
        if verbose:
            logger.info("Parsing article sections...")
        article_dict = self._parse_article_sections(article_text, template_config)
        
        if verbose:
            logger.info(f"Parsed {len(article_dict)} sections from article")
        
        return article_dict
    
    def _build_writing_prompt(
        self,
        topic: str,
        research_data: Dict[str, Any],
        tone_config: Dict[str, Any],
        template_config: Dict[str, Any],
        target_words: str,
        user_context: Optional[Dict[str, str]] = None
    ) -> str:
        """Build comprehensive writing prompt.
        
        Args:
            topic: Article topic
            research_data: Research findings
            tone_config: Tone configuration
            template_config: Template configuration
            target_words: Target word count
            user_context: Optional user-provided context about their innovation
            
        Returns:
            Complete writing prompt
        """
        # Extract tone information
        tone_description = tone_config.get('description', '')
        tone_style = tone_config.get('tone', '')
        style_guide = tone_config.get('style_guide', [])
        example_phrases = tone_config.get('example_phrases', [])
        
        # Extract template structure
        structure = template_config.get('structure', [])
        required_sections = [s['section'] for s in structure if s.get('required', True)]
        optional_sections = [s['section'] for s in structure if not s.get('required', True)]
        
        # Build section descriptions
        section_descriptions = []
        for section_def in structure:
            section_name = section_def['section']
            description = section_def.get('description', '')
            section_descriptions.append(f"- {section_name}: {description}")
        
        sections_text = "\n".join(section_descriptions)
        
        # Build prompt
        prompt = f"""You are a professional writer creating a {tone_config.get('description', 'media')} article.

TOPIC: {topic}

TONE AND STYLE:
{tone_description}
Tone: {tone_style}

Style Guidelines:
{chr(10).join(f"- {guideline}" for guideline in style_guide)}

Example phrases to use:
{chr(10).join(f"- {phrase}" for phrase in example_phrases)}

ARTICLE STRUCTURE:
Follow this structure exactly. Generate content for each required section:

{sections_text}

Required sections: {', '.join(required_sections)}
Optional sections: {', '.join(optional_sections) if optional_sections else 'None'}

CRITICAL DISTINCTION - READ CAREFULLY:
{('The USER-PROVIDED CONTEXT section below contains the user\'s NOVEL and UNIQUE technology/approach - created by them. This is the PRIMARY SUBJECT of the article.' if user_context else '')}
The RESEARCH FINDINGS and CONTEXT sections below represent RELATED WORK by OTHER industry experts and researchers.
These findings provide INDUSTRY CONTEXT showing what others in the field are doing.

RESEARCH FINDINGS (Related Work by Other Industry Experts):
{research_data.get('key_findings', 'No research findings available.')}

CONTEXT (Industry Context from Other Experts):
{research_data.get('context', 'No context available.')}

SOURCES (Work by Other Researchers):
{self._format_sources_for_prompt(research_data.get('sources', []))}
{self._build_user_context_section(user_context) if user_context else ''}

WRITING REQUIREMENTS:
1. Write in a natural, human-like style that reads authentically
2. Target word count: {target_words} words total
3. Maintain the specified tone throughout
4. Use the research findings to inform your writing, but write naturally
5. Avoid AI-sounding phrases like "In conclusion" or "It is important to note"
6. Write as if you're a professional journalist or researcher
7. Make transitions smooth and natural - write as ONE CONTINUOUS FLOWING ARTICLE
8. Each section should flow seamlessly into the next without breaks or headers
9. Use specific details from research when relevant
10. Write about the topic as if it's about someone else (third person perspective)
11. NO bullet points, numbered lists, or formatting that feels AI-generated
12. NO section headers in the article body - write as continuous narrative
13. Avoid bold or italics unless absolutely necessary for emphasis
14. Use natural paragraph breaks and transitions instead of headers

CRITICAL DISTINCTION REQUIREMENTS:
{('11. Clearly distinguish between the user\'s novel technology (from USER-PROVIDED CONTEXT) and related work by others (from RESEARCH FINDINGS)' if user_context else '')}
{('12. The user\'s technology is NOVEL and UNIQUE - created by them. Present it as the PRIMARY SUBJECT of the article' if user_context else '')}
{('13. Position research findings as INDUSTRY CONTEXT showing what OTHER experts are doing, NOT as tools/frameworks the user\'s technology uses' if user_context else '')}
{('14. Use phrases like "Other researchers have explored...", "Industry experts working in similar areas...", "Researchers in the field have investigated..." when referencing research findings' if user_context else '')}
{('15. DO NOT suggest the user\'s technology uses, depends on, or is built from the research findings' if user_context else '')}
{('16. Instead, show how the user\'s approach is unique while research findings provide context about the broader field' if user_context else '')}
{('17. When integrating research findings, frame them as complementary work: "While others have explored X, this approach does Y uniquely..."' if user_context else '')}

OUTPUT FORMAT - CRITICAL:
Use XML-style tags to mark sections. These tags are for parsing only and will NOT appear in the final article.

Format your output EXACTLY like this example:

<headline>The Future of Hardware Prototyping</headline>

<section name="opening">
Every hardware engineer has a ghost story. It's the "reality gap"—that gut-punch moment when months of perfect digital simulation meet the messy physics of the real world. Picture the scene: You've spent half a year perfecting a software feature in a flawless digital environment. It's sleek, it's fast, and the code is clean. Then comes the moment of truth. You plug that code into a physical prototype, and the whole thing falls apart.
</section>

<section name="the_story">
The Physical Twin approach is a massive pivot in how we build things. We've spent the last decade obsessed with "Digital Twins"—virtual clones used to monitor machines that already exist. But the Physical Twin is different. It's about the birth of a product, not its maintenance. It starts with "curated hardware." We're talking about the actual steering wheels, the high-res screens, or the specific chassis components that define how a person actually feels a product.
</section>

<section name="why_it_matters">
As products get smarter and more connected, the cost of a manufacturing mistake has become catastrophic. The Physical Twin is essentially an insurance policy against the limits of pure simulation. This shift is vital for Human-System Integration (HSI). When a team can test ergonomics and cognitive load on day one, they can make data-driven decisions about safety that virtual models often miss.
</section>

<section name="what_next">
We're heading toward a future defined by autonomous transport, smart cities, and medical robotics. In that world, the Physical Twin approach is poised to become the gold standard. The applications go way beyond cars. We're already seeing this framework move into the IoT space.
</section>

CRITICAL FORMATTING RULES:
- Use <headline>content</headline> for the headline (required)
- Use <section name="section_name">content</section> for each section
- NO markdown headers (## or #) in the article body
- NO bullet points or lists - write in flowing paragraphs
- NO bold (**text**) or italics (*text*) unless absolutely necessary for emphasis
- Write as one continuous narrative that flows smoothly from section to section
- Use natural transitions between sections - make it read like a single cohesive article
- Each section's content should flow naturally into the next section

REQUIRED SECTIONS TO INCLUDE: {', '.join(required_sections)}

Generate the complete article now, following all guidelines above. Write it as one smooth, flowing narrative using the XML format shown in the example.
"""
        
        return prompt
    
    def _build_user_context_section(self, user_context: Dict[str, str]) -> str:
        """Build user context section for writing prompt.
        
        Args:
            user_context: User-provided context dictionary
            
        Returns:
            Formatted user context section
        """
        novel_aspect = user_context.get('novel_aspect', '')
        technology_details = user_context.get('technology_details', '')
        problem_solved = user_context.get('problem_solved', '')
        use_cases = user_context.get('use_cases', '')
        confidential_info = user_context.get('confidential_info', '')
        additional_notes = user_context.get('additional_notes', '')
        
        section = "\n\nUSER-PROVIDED CONTEXT (CRITICAL - This is the user's NOVEL and UNIQUE technology/approach, created by them):\n"
        section += f"Novel Aspect: {novel_aspect}\n\n"
        section += f"Technology Details: {technology_details}\n\n"
        section += f"Problem Solved: {problem_solved}\n"
        
        if use_cases:
            section += f"\nUse Cases: {use_cases}\n"
        
        if additional_notes:
            section += f"\nAdditional Notes: {additional_notes}\n"
        
        if confidential_info:
            section += f"\nCRITICAL: Do NOT mention the following in the article: {confidential_info}\n"
        
        section += "\nCRITICAL INSTRUCTIONS FOR USER'S TECHNOLOGY:\n"
        section += "- This is the user's NOVEL and UNIQUE technology/approach - created by them\n"
        section += "- Present this as the PRIMARY SUBJECT and INNOVATION of the article\n"
        section += "- This should be presented as unique and novel, NOT as something built on others' work\n"
        section += "- Ensure the article prominently features the novel aspects described above\n"
        section += "- Integrate user-provided details naturally into the narrative\n"
        section += "- The novel aspect should be a central theme throughout the article\n"
        section += "- Use the technology details to provide concrete examples\n"
        section += "- Connect the problem solved to broader industry challenges\n"
        section += "- When mentioning related work from research findings, clearly distinguish it as 'other industry experts' or 'researchers in the field'\n"
        section += "- DO NOT suggest the user's technology uses, depends on, or is built from the research findings\n"
        section += "- Instead, position research findings as complementary work showing what others are doing in similar areas\n"
        
        if confidential_info:
            section += f"- Absolutely do not mention: {confidential_info}\n"
        
        return section
    
    def _format_sources_for_prompt(self, sources: list) -> str:
        """Format sources for inclusion in prompt.
        
        Args:
            sources: List of SearchResult objects
            
        Returns:
            Formatted sources text
        """
        if not sources:
            return "No sources available."
        
        lines = []
        for i, source in enumerate(sources[:10], 1):  # Limit to 10 sources
            lines.append(f"{i}. {source.title} - {source.url}")
            if hasattr(source, 'snippet') and source.snippet:
                lines.append(f"   {source.snippet[:150]}...")
        
        return "\n".join(lines)
    
    def _parse_article_sections(
        self,
        article_text: str,
        template_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Parse generated article text into section dictionary.
        
        Args:
            article_text: Generated article text
            template_config: Template configuration
            
        Returns:
            Dictionary mapping section names to content
        """
        import re
        from ..utils.logger import get_logger
        
        logger = get_logger(__name__)
        article_dict = {}
        
        # Get section names from template
        structure = template_config.get('structure', [])
        section_names = [s['section'] for s in structure]
        
        # Primary: Try parsing XML-style tags using utility function
        article_dict, parsed_sections = parse_xml_sections(article_text, section_names)
        
        if parsed_sections:
            # Validate XML structure
            required_sections = [s['section'] for s in structure if s.get('required', True)]
            is_valid, missing = validate_xml_structure(article_text, required_sections)
            if not is_valid and missing:
                logger.warning(f"XML structure missing required sections: {missing}")
            
            return article_dict
        
        # Fallback 1: Try extracting headline using utility
        headline_text = extract_headline_from_text(article_text)
        if headline_text:
            if 'title' in section_names:
                article_dict['title'] = headline_text
            elif 'headline' in section_names:
                article_dict['headline'] = headline_text
            # Remove headline from article text for further parsing
            if 'HEADLINE:' in article_text:
                headline_lines = article_text.split('HEADLINE:', 1)
                if len(headline_lines) > 1:
                    article_text = '\n'.join(headline_lines[1].split('\n')[1:]) if len(headline_lines[1].split('\n')) > 1 else ''
        
        # Fallback 2: Try old delimiter format (---SECTION: name---)
        if '---SECTION:' in article_text:
            sections = article_text.split('---SECTION:')
            
            first_part = sections[0].strip()
            if first_part and first_part not in ['HEADLINE:', '']:
                if 'opening' in section_names and 'opening' not in article_dict:
                    article_dict['opening'] = first_part
                elif 'lead' in section_names and 'lead' not in article_dict:
                    article_dict['lead'] = first_part
            
            for section_block in sections[1:]:
                lines = section_block.split('\n', 1)
                if len(lines) >= 2:
                    section_name_line = lines[0].strip().rstrip('---').strip()
                    section_content = lines[1].strip()
                    
                    normalized_marker = section_name_line.lower().replace(' ', '_')
                    matched_section = None
                    for section_name in section_names:
                        if section_name.lower() == normalized_marker or \
                           section_name.lower() in normalized_marker or \
                           normalized_marker in section_name.lower():
                            matched_section = section_name
                            break
                    
                    if matched_section:
                        article_dict[matched_section] = section_content
                    elif section_content:
                        article_dict[normalized_marker] = section_content
            
            if article_dict:
                logger.debug("Parsed sections using fallback delimiter format")
                return article_dict
        
        # Fallback 3: Try parsing by markdown headers (## or #)
        lines = article_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith('##'):
                if current_section and current_content:
                    article_dict[current_section] = '\n'.join(current_content).strip()
                
                header_text = line_stripped.replace('##', '').strip()
                current_section = None
                for section_name in section_names:
                    if section_name.lower() in header_text.lower() or \
                       header_text.lower() in section_name.lower():
                        current_section = section_name
                        break
                
                if not current_section:
                    current_section = header_text.lower().replace(' ', '_')
                
                current_content = []
            elif line_stripped.startswith('#'):
                if current_section and current_content:
                    article_dict[current_section] = '\n'.join(current_content).strip()
                
                header_text = line_stripped.replace('#', '').strip()
                if 'title' in section_names:
                    article_dict['title'] = header_text
                elif 'headline' in section_names:
                    article_dict['headline'] = header_text
                current_section = None
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
                elif not current_section and line_stripped:
                    if 'title' not in article_dict and 'headline' not in article_dict:
                        if 'title' in section_names:
                            article_dict['title'] = line_stripped
                        elif 'headline' in section_names:
                            article_dict['headline'] = line_stripped
        
        if current_section and current_content:
            article_dict[current_section] = '\n'.join(current_content).strip()
        
        if article_dict:
            logger.debug("Parsed sections using fallback markdown header format")
        
        return article_dict
