"""Humanizer Agent for transforming AI-generated text into natural human-like writing."""
from typing import Dict, Any, Optional
from ..utils.llm import LLMProvider
from ..utils.config_loader import ConfigLoader
from ..utils.ai_patterns import detect_ai_patterns, analyze_sentence_variation
from ..utils.xml_parser import parse_xml_sections, validate_xml_structure, extract_headline_from_text


class HumanizerAgent:
    """Agent responsible for humanizing AI-generated articles."""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        config_loader: ConfigLoader,
        enabled: bool = True,
        passes: int = 2,
        intensity: str = "medium"
    ):
        """Initialize Humanizer Agent.
        
        Args:
            llm_provider: LLM provider for humanization
            config_loader: Configuration loader for tone reference
            enabled: Whether humanization is enabled
            passes: Number of refinement passes (1-3)
            intensity: Intensity level (low, medium, high)
        """
        self.llm_provider = llm_provider
        self.config_loader = config_loader
        self.enabled = enabled
        self.passes = max(1, min(3, passes))  # Clamp between 1 and 3
        self.intensity = intensity
    
    def humanize(
        self,
        article_dict: Dict[str, str],
        media_type: str,
        verbose: bool = False
    ) -> Dict[str, str]:
        """Humanize article to make it sound more natural and human-written.
        
        Args:
            article_dict: Article sections dictionary
            media_type: Media type for tone reference
            verbose: Whether to log detailed progress
            
        Returns:
            Humanized article dictionary
        """
        if not self.enabled:
            if verbose:
                from ..utils.logger import get_logger
                logger = get_logger(__name__)
                logger.info("Humanization is disabled, returning original article")
            return article_dict
        
        # Load tone config for reference
        tone_config = self.config_loader.get_tone_config(media_type)
        template_config = self.config_loader.get_template_config(media_type)
        
        # Initialize logger if verbose
        logger = None
        if verbose:
            from ..utils.logger import get_logger
            logger = get_logger(__name__)
        
        # Analyze current article quality
        article_text = self._format_article_for_humanization(article_dict)
        patterns = detect_ai_patterns(article_text, media_type)
        variation = analyze_sentence_variation(article_text)
        
        if verbose and logger:
            logger.info(f"Detected {len(patterns)} AI patterns")
            logger.info(f"Sentence variation score: {variation['variation_score']:.2f}")
        
        # Apply multi-pass humanization
        current_dict = article_dict
        for pass_num in range(1, self.passes + 1):
            if verbose and logger:
                logger.info(f"Humanization pass {pass_num}/{self.passes}")
            
            prompt = self._build_humanization_prompt(
                current_dict,
                media_type,
                tone_config,
                template_config,
                pass_num,
                patterns if pass_num == 1 else None,
                variation if pass_num == 1 else None
            )
            
            humanized_text = self.llm_provider.generate(prompt)
            current_dict = self._parse_humanized_sections(
                humanized_text,
                template_config,
                article_dict.keys()
            )
            
            # Update article text for next pass analysis
            if pass_num < self.passes:
                article_text = self._format_article_for_humanization(current_dict)
                variation = analyze_sentence_variation(article_text)
        
        # Merge with original to preserve structure
        final_dict = {}
        for section_name in article_dict.keys():
            if section_name in current_dict:
                final_dict[section_name] = current_dict[section_name]
            else:
                final_dict[section_name] = article_dict[section_name]
        
        return final_dict
    
    def _build_humanization_prompt(
        self,
        article_dict: Dict[str, str],
        media_type: str,
        tone_config: Dict[str, Any],
        template_config: Dict[str, Any],
        pass_num: int,
        detected_patterns: Optional[list] = None,
        variation_metrics: Optional[Dict[str, float]] = None
    ) -> str:
        """Build humanization prompt for a specific pass.
        
        Args:
            article_dict: Article sections
            media_type: Media type
            tone_config: Tone configuration
            template_config: Template configuration
            pass_num: Current pass number (1, 2, or 3)
            detected_patterns: AI patterns detected (for pass 1)
            variation_metrics: Sentence variation metrics (for pass 1)
            
        Returns:
            Humanization prompt
        """
        article_text = self._format_article_for_humanization(article_dict)
        tone_description = tone_config.get('description', '')
        style_guide = tone_config.get('style_guide', [])
        
        # Pass-specific instructions
        if pass_num == 1:
            # First pass: Focus on perplexity and burstiness - AGGRESSIVE
            focus = """CRITICAL FOCUS FOR THIS PASS: Sentence Variation (Perplexity & Burstiness) - BE AGGRESSIVE

1. DRAMATICALLY VARY SENTENCE LENGTH: 
   - Add SHORT punchy sentences (3-8 words) for impact: "This changes everything." "The implications are huge."
   - Mix with MEDIUM sentences (12-18 words) for flow
   - Include LONGER complex sentences (25-35 words) for depth
   - Humans write with WILD variation - break every uniform pattern!

2. VARY SENTENCE STRUCTURE AGGRESSIVELY:
   - Start some sentences with verbs: "Consider the implications."
   - Start some with conjunctions: "But here's the thing."
   - Use fragments for emphasis: "Not anymore."
   - Alternate simple, compound, complex, and compound-complex sentences

3. CREATE NATURAL RHYTHM:
   - Break up any sequence of similar-length sentences
   - Add intentional pauses with shorter sentences
   - Use longer sentences to build momentum, then break with short ones

4. ADD SENTENCE COMPLEXITY VARIATION:
   - Some sentences should be dead simple: "The problem is clear."
   - Others should be nuanced and layered
   - Vary the complexity within paragraphs"""
            
            if variation_metrics and variation_metrics['variation_score'] < 0.5:
                focus += "\n\n⚠️ LOW VARIATION DETECTED: The current text has very uniform sentence lengths. DRAMATICALLY increase variation - add many more short sentences and vary lengths aggressively."
        
        elif pass_num == 2:
            # Second pass: Remove AI patterns and improve transitions - AGGRESSIVE
            focus = """CRITICAL FOCUS FOR THIS PASS: Remove AI Patterns & Natural Transitions - BE AGGRESSIVE

1. ELIMINATE ALL AI-SOUNDING PHRASES:
   - Remove: "In conclusion", "It is important to note", "Furthermore", "Moreover", "Additionally", "This demonstrates", "This indicates", "This suggests", "It is worth noting", "It should be noted"
   - Replace with NOTHING (just delete) or natural alternatives: "Also" → delete or use context, "This demonstrates" → "This shows" or delete
   - Be ruthless - if it sounds like AI wrote it, remove it

2. IMPROVE TRANSITIONS RADICALLY:
   - Delete formulaic connectors entirely where possible
   - Use context-based transitions: reference previous content naturally
   - Start paragraphs with specific details, not generic connectors
   - Let ideas flow organically without forcing connections

3. REMOVE REPETITIVE STRUCTURES:
   - If multiple sentences start the same way, rewrite them
   - Vary paragraph openings dramatically
   - Break any patterns that feel formulaic

4. USE NATURAL CONNECTORS:
   - Instead of "Furthermore" → delete or use "Plus" or "Also" or nothing
   - Instead of "Moreover" → delete or use "What's more" or nothing
   - Instead of "In addition" → delete or use "Also" or nothing
   - Prefer deleting connectors over replacing them"""
            
            if detected_patterns:
                patterns_list = ", ".join([p[0] for p in detected_patterns[:15]])
                focus += f"\n\n⚠️ DETECTED AI PATTERNS TO REMOVE: {patterns_list}\n\nREMOVE ALL OF THESE - be aggressive!"
        
        else:
            # Third pass: Final polish and voice refinement - AGGRESSIVE
            focus = """CRITICAL FOCUS FOR THIS PASS: Voice Refinement & Final Polish - BE AGGRESSIVE

1. ADD STRONG PERSONALITY:
   - Inject natural voice appropriate for the media type
   - Add personality markers: opinions, asides, natural expressions
   - Make it sound like a real person wrote this, not a machine

2. REFINE TONE AGGRESSIVELY:
   - Ensure tone matches publication style throughout
   - Remove any remaining formal/AI-sounding language
   - Add appropriate casualness for the media type

3. FINAL POLISH:
   - Smooth ALL awkward phrasing
   - Remove any remaining robotic patterns
   - Ensure every sentence flows naturally

4. ENSURE CONSISTENCY:
   - Check that voice is consistent throughout
   - Make sure personality doesn't disappear in later sections"""
        
        # Intensity adjustments
        intensity_instructions = {
            "low": "Make subtle improvements while preserving most of the original structure.",
            "medium": "Make noticeable improvements to naturalness while maintaining the core content.",
            "high": "Aggressively transform the text to sound completely human-written, even if it means more significant restructuring."
        }
        intensity_note = intensity_instructions.get(self.intensity, intensity_instructions["medium"])
        
        prompt = f"""You are an expert editor specializing in transforming AI-generated text into natural, human-written content for {tone_description} publications.

{focus}

INTENSITY LEVEL: {intensity_note}

MEDIA TYPE CONTEXT:
- Tone: {tone_config.get('tone', '')}
- Style Guidelines: {', '.join(style_guide[:5])}

ORIGINAL ARTICLE:
{article_text}

HUMANIZATION REQUIREMENTS:
1. PRESERVE ALL FACTUAL CONTENT: Do not change facts, data, names, or key information
2. MAINTAIN ARTICLE STRUCTURE: Keep all sections intact but write as continuous flowing narrative
3. PRESERVE MEANING: The core message and meaning must remain identical
4. APPLY FOCUS AREA: Follow the critical focus instructions above for this pass
5. NATURAL LANGUAGE: Write as a professional human journalist/researcher would
6. AVOID AI PATTERNS: Eliminate robotic, formulaic, or AI-sounding language
7. MEDIA TYPE APPROPRIATE: Match the tone and style for {media_type}
8. NO SECTION HEADERS: Write as one continuous flowing article without headers
9. NO BULLET POINTS: Use flowing paragraphs instead
10. AVOID BOLD/ITALICS: Only use if absolutely necessary for emphasis

SPECIFIC INSTRUCTIONS FOR {media_type}:
"""
        
        # Media-type specific instructions
        if media_type == "tech_news":
            prompt += """- Use VERY conversational, forward-looking language - write like you're telling a story to a friend
- USE CONTRACTIONS FREQUENTLY: it's, that's, we're, don't, can't, won't, they're, you're
- Use active voice throughout - NO passive voice
- Make it engaging and accessible - add personality, opinions, natural expressions
- Avoid ALL overly formal academic language - if it sounds academic, make it casual
- Add natural asides and observations: "Here's the thing...", "The catch?", "Here's why this matters..."
- Use shorter paragraphs (2-4 sentences max)
- Start paragraphs with specific details, not generic statements
- Add rhetorical questions where appropriate: "But what does this mean?"
- Use natural, everyday language - write like TechCrunch or Wired, not Nature"""
        elif media_type == "scientific_journal":
            prompt += """- Maintain formal but natural tone
- Use precise, evidence-based language
- Avoid casual contractions
- Keep technical accuracy while improving flow
- Natural transitions between concepts"""
        elif media_type == "research_magazine":
            prompt += """- Balance accessibility with rigor
- Use engaging but authoritative voice
- Natural explanations of complex concepts
- Smooth narrative flow
- Connect ideas organically"""
        else:  # academic_news
            prompt += """- Professional but not overly formal
- Respectful and achievement-focused
- Natural transitions
- Clear, readable prose
- Appropriate for academic audience"""
        
        prompt += f"""

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

CRITICAL FORMATTING RULES:
- Use <headline>content</headline> for the headline
- Use <section name="section_name">content</section> for each section
- NO markdown headers (## or #) in the article body
- NO bullet points or lists - write in flowing paragraphs
- Avoid bold/italics unless absolutely necessary
- Write as one continuous narrative that flows smoothly from section to section
- Each section's content should flow naturally into the next section

Transform the article now, applying the focus area for pass {pass_num} while preserving all factual content and structure as one flowing narrative using the XML format shown above.
"""
        
        return prompt
    
    def _format_article_for_humanization(self, article_dict: Dict[str, str]) -> str:
        """Format article dictionary for humanization prompt.
        
        Args:
            article_dict: Article sections dictionary
            
        Returns:
            Formatted article text with XML tags
        """
        lines = []
        
        # Order sections logically
        section_order = ['title', 'headline', 'subheadline', 'abstract', 'lead', 'opening',
                        'introduction', 'background', 'methodology', 'discovery', 'achievement',
                        'results', 'the_story', 'discussion', 'impact', 'why_it_matters',
                        'conclusion', 'future', 'what_next', 'context', 'recognition']
        
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
            if section_name in article_dict and section_name not in ['title', 'headline']:
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
    
    def _parse_humanized_sections(
        self,
        humanized_text: str,
        template_config: Dict[str, Any],
        original_sections: set
    ) -> Dict[str, str]:
        """Parse humanized article text into section dictionary.
        
        Args:
            humanized_text: Humanized article text
            template_config: Template configuration
            original_sections: Set of original section names
            
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
        article_dict, parsed_sections = parse_xml_sections(
            humanized_text, 
            section_names, 
            list(original_sections) if original_sections else None
        )
        
        if parsed_sections:
            # Validate XML structure
            structure = template_config.get('structure', [])
            required_sections = [s['section'] for s in structure if s.get('required', True)]
            is_valid, missing = validate_xml_structure(humanized_text, required_sections)
            if not is_valid and missing:
                logger.warning(f"XML structure missing required sections: {missing}")
            
            return article_dict
        
        # Fallback 1: Try extracting headline using utility
        headline_text = extract_headline_from_text(humanized_text)
        if headline_text:
            if 'title' in section_names:
                article_dict['title'] = headline_text
            elif 'headline' in section_names:
                article_dict['headline'] = headline_text
            # Remove headline from article text for further parsing
            if 'HEADLINE:' in humanized_text:
                headline_lines = humanized_text.split('HEADLINE:', 1)
                if len(headline_lines) > 1:
                    humanized_text = '\n'.join(headline_lines[1].split('\n')[1:]) if len(headline_lines[1].split('\n')) > 1 else ''
        
        # Fallback 2: Try old delimiter format (---SECTION: name---)
        if '---SECTION:' in humanized_text:
            sections = humanized_text.split('---SECTION:')
            
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
                    
                    if not matched_section:
                        for section_name in original_sections:
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
        lines = humanized_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith('##'):
                if current_section and current_content:
                    article_dict[current_section] = '\n'.join(current_content).strip()
                
                header_text = line_stripped.replace('##', '').strip()
                normalized_header = header_text.lower().replace(' ', '_')
                
                current_section = None
                for section_name in section_names:
                    if section_name.lower() == normalized_header or \
                       section_name.lower() in normalized_header or \
                       normalized_header in section_name.lower():
                        current_section = section_name
                        break
                
                if not current_section:
                    for section_name in original_sections:
                        if section_name.lower() == normalized_header or \
                           section_name.lower() in normalized_header or \
                           normalized_header in section_name.lower():
                            current_section = section_name
                            break
                
                if not current_section:
                    current_section = normalized_header
                
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
