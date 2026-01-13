"""Editor Agent for refining article quality and human-like writing."""
from typing import Dict, Any
from ..utils.llm import LLMProvider
from ..utils.config_loader import ConfigLoader
from ..utils.xml_parser import parse_xml_sections, validate_xml_structure, extract_headline_from_text


class EditorAgent:
    """Agent responsible for editing and refining articles."""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        config_loader: ConfigLoader
    ):
        """Initialize Editor Agent.
        
        Args:
            llm_provider: LLM provider for editing
            config_loader: Configuration loader for tone reference
        """
        self.llm_provider = llm_provider
        self.config_loader = config_loader
    
    def edit(
        self,
        article_dict: Dict[str, str],
        media_type: str,
        fact_check: bool = False,
        verbose: bool = False
    ) -> Dict[str, str]:
        """Edit and refine article for quality and human-like writing.
        
        Args:
            article_dict: Article sections dictionary
            media_type: Media type for tone reference
            fact_check: Whether to perform fact-checking
            
        Returns:
            Refined article dictionary
        """
        # Load tone config for reference
        tone_config = self.config_loader.get_tone_config(media_type)
        
        # Build editing prompt
        if verbose:
            from ..utils.logger import get_logger
            logger = get_logger(__name__)
            logger.info("Building editing prompt...")
        
        prompt = self._build_editing_prompt(article_dict, media_type, tone_config, fact_check)
        
        # Generate edited article
        if verbose:
            logger.info("Refining article quality...")
        edited_text = self.llm_provider.generate(prompt)
        
        # Parse edited article back into sections
        if verbose:
            logger.info("Parsing edited sections...")
        template_config = self.config_loader.get_template_config(media_type)
        edited_dict = self._parse_article_sections(edited_text, template_config)
        
        # Merge with original to preserve structure
        final_dict = {}
        for section_name in article_dict.keys():
            if section_name in edited_dict:
                final_dict[section_name] = edited_dict[section_name]
            else:
                final_dict[section_name] = article_dict[section_name]
        
        return final_dict
    
    def _build_editing_prompt(
        self,
        article_dict: Dict[str, str],
        media_type: str,
        tone_config: Dict[str, Any],
        fact_check: bool
    ) -> str:
        """Build editing prompt.
        
        Args:
            article_dict: Article sections
            media_type: Media type
            tone_config: Tone configuration
            fact_check: Whether to fact-check
            
        Returns:
            Editing prompt
        """
        # Format article for editing
        article_text = self._format_article_for_editing(article_dict)
        
        tone_description = tone_config.get('description', '')
        style_guide = tone_config.get('style_guide', [])
        
        prompt = f"""You are an experienced editor reviewing an article for a {tone_description} publication.

Your task is to refine this article to ensure it:
1. Reads naturally and human-like (not AI-generated)
2. Maintains consistent tone: {tone_config.get('tone', '')}
3. Has smooth transitions between sections
4. Uses natural language and avoids clichés
5. Is factually accurate (if fact-checking is enabled)
6. Follows style guidelines: {', '.join(style_guide[:3])}

ORIGINAL ARTICLE:
{article_text}

EDITING INSTRUCTIONS:
- Preserve the article structure and all sections
- Improve flow and readability - maintain smooth transitions between sections
- Remove any AI-sounding phrases or patterns
- Ensure the writing feels authentic and human-written
- Maintain the original meaning and key points
- Fix any awkward phrasing or transitions
- Ensure consistency in style throughout
- NO section headers in the output - write as continuous flowing narrative
- NO bullet points or lists - use flowing paragraphs
- Avoid bold or italics unless absolutely necessary
{f"- Verify factual claims are accurate" if fact_check else ""}

OUTPUT FORMAT - CRITICAL:
Use XML-style tags to mark sections. These tags are for parsing only and will NOT appear in the final article.

Format your output EXACTLY like this example:

<headline>The Future of Hardware Prototyping</headline>

<section name="opening">
Every hardware engineer has a ghost story. It's the "reality gap"—that gut-punch moment when months of perfect digital simulation meet the messy physics of the real world. Picture the scene: You've spent half a year perfecting a software feature in a flawless digital environment.
</section>

<section name="the_story">
The Physical Twin approach is a massive pivot in how we build things. We've spent the last decade obsessed with "Digital Twins"—virtual clones used to monitor machines that already exist. But the Physical Twin is different. It's about the birth of a product, not its maintenance.
</section>

<section name="why_it_matters">
As products get smarter and more connected, the cost of a manufacturing mistake has become catastrophic. The Physical Twin is essentially an insurance policy against the limits of pure simulation.
</section>

CRITICAL FORMATTING RULES:
- Use <headline>content</headline> for the headline
- Use <section name="section_name">content</section> for each section
- NO markdown headers (## or #) in the article body
- NO bullet points or lists - write in flowing paragraphs
- Write as one continuous narrative that flows smoothly from section to section
- Each section's content should flow naturally into the next section

Edit the entire article now, maintaining all sections but improving quality and human-like flow as one continuous narrative using the XML format shown above.
"""
        
        return prompt
    
    def _format_article_for_editing(self, article_dict: Dict[str, str]) -> str:
        """Format article dictionary for editing prompt.
        
        Args:
            article_dict: Article sections dictionary
            
        Returns:
            Formatted article text
        """
        lines = []
        
        # Order sections logically
        section_order = ['title', 'headline', 'subheadline', 'abstract', 'lead', 'opening',
                        'introduction', 'background', 'methodology', 'discovery', 'achievement',
                        'results', 'the_story', 'discussion', 'impact', 'why_it_matters',
                        'conclusion', 'future', 'what_next', 'context', 'recognition',
                        'sources', 'references']
        
        # Add headline/title first if present
        headline_content = None
        if 'headline' in article_dict:
            headline_content = article_dict['headline']
        elif 'title' in article_dict:
            headline_content = article_dict['title']
        
        if headline_content:
            lines.append(f"<headline>{headline_content}</headline>")
            lines.append("")
        
        # Add sections in order as continuous flow with XML section tags
        for section_name in section_order:
            if section_name in article_dict and section_name not in ['title', 'headline', 'sources', 'references']:
                content = article_dict[section_name].strip()
                if content:
                    lines.append(f'<section name="{section_name}">')
                    lines.append(content)
                    lines.append("</section>")
                    lines.append("")
        
        # Add any remaining sections (except sources/references)
        for section_name, content in article_dict.items():
            if section_name not in section_order and section_name not in ['title', 'headline', 'sources', 'references']:
                content = content.strip()
                if content:
                    lines.append(f'<section name="{section_name}">')
                    lines.append(content)
                    lines.append("</section>")
                    lines.append("")
        
        return "\n".join(lines)
    
    def _parse_article_sections(
        self,
        article_text: str,
        template_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Parse edited article text into section dictionary.
        
        Args:
            article_text: Edited article text
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
        
        # Fallback 3: Try parsing by markdown headers
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
                    normalized_header = header_text.lower().replace(' ', '_')
                    if section_name.lower() == normalized_header or \
                       section_name.lower() in normalized_header or \
                       normalized_header in section_name.lower():
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
        
        if current_section and current_content:
            article_dict[current_section] = '\n'.join(current_content).strip()
        
        if article_dict:
            logger.debug("Parsed sections using fallback markdown header format")
        
        return article_dict
