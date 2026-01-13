"""XML parsing utilities for article section extraction."""
import re
from typing import Dict, List, Optional, Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


def parse_xml_sections(
    article_text: str,
    section_names: List[str],
    original_sections: Optional[List[str]] = None
) -> Tuple[Dict[str, str], List[str]]:
    """Parse article text with XML-style section tags.
    
    Args:
        article_text: Article text containing XML tags
        section_names: List of valid section names from template
        original_sections: Optional list of original section names for matching
        
    Returns:
        Tuple of (article_dict, parsed_section_names) where:
        - article_dict: Dictionary mapping section names to content
        - parsed_section_names: List of section names that were successfully parsed
    """
    article_dict = {}
    parsed_sections = []
    
    # Extract headline/title using XML tags
    headline_pattern = r'<(?:headline|title)>(.*?)</(?:headline|title)>'
    headline_match = re.search(headline_pattern, article_text, re.DOTALL | re.IGNORECASE)
    if headline_match:
        headline_text = headline_match.group(1).strip()
        if headline_text:
            if 'title' in section_names:
                article_dict['title'] = headline_text
                parsed_sections.append('title')
            elif 'headline' in section_names:
                article_dict['headline'] = headline_text
                parsed_sections.append('headline')
    
    # Parse XML section tags: <section name="section_name">content</section>
    section_pattern = r'<section\s+name=["\']([^"\']+)["\']>(.*?)</section>'
    section_matches = re.finditer(section_pattern, article_text, re.DOTALL | re.IGNORECASE)
    
    for match in section_matches:
        section_name_raw = match.group(1).strip()
        section_content = match.group(2).strip()
        
        if not section_content:
            continue
        
        # Normalize section name
        normalized_name = section_name_raw.lower().replace(' ', '_')
        
        # Try to match to known section names
        matched_section = None
        for section_name in section_names:
            if section_name.lower() == normalized_name or \
               section_name.lower() in normalized_name or \
               normalized_name in section_name.lower():
                matched_section = section_name
                break
        
        # If no match and original_sections provided, try matching those
        if not matched_section and original_sections:
            for section_name in original_sections:
                if section_name.lower() == normalized_name or \
                   section_name.lower() in normalized_name or \
                   normalized_name in section_name.lower():
                    matched_section = section_name
                    break
        
        if matched_section:
            article_dict[matched_section] = section_content
            parsed_sections.append(matched_section)
        elif section_content:
            # Use normalized name if no match found
            article_dict[normalized_name] = section_content
            parsed_sections.append(normalized_name)
    
    if parsed_sections:
        logger.debug(f"Parsed {len(parsed_sections)} sections using XML format: {parsed_sections}")
    
    return article_dict, parsed_sections


def validate_xml_structure(
    article_text: str,
    required_sections: List[str]
) -> Tuple[bool, List[str]]:
    """Validate that XML structure contains required sections.
    
    Args:
        article_text: Article text to validate
        required_sections: List of required section names
        
    Returns:
        Tuple of (is_valid, missing_sections) where:
        - is_valid: True if all required sections are present
        - missing_sections: List of required sections that are missing
    """
    # Extract all section names from XML tags
    section_pattern = r'<section\s+name=["\']([^"\']+)["\']>'
    found_sections = set()
    
    for match in re.finditer(section_pattern, article_text, re.IGNORECASE):
        section_name = match.group(1).strip().lower().replace(' ', '_')
        found_sections.add(section_name)
    
    # Check for headline/title
    headline_pattern = r'<(?:headline|title)>'
    if re.search(headline_pattern, article_text, re.IGNORECASE):
        found_sections.add('headline')
        found_sections.add('title')
    
    # Check which required sections are missing
    missing_sections = []
    for required in required_sections:
        normalized_required = required.lower().replace(' ', '_')
        found = False
        for found_section in found_sections:
            if normalized_required == found_section or \
               normalized_required in found_section or \
               found_section in normalized_required:
                found = True
                break
        if not found:
            missing_sections.append(required)
    
    is_valid = len(missing_sections) == 0
    
    if not is_valid:
        logger.warning(f"XML structure validation failed. Missing sections: {missing_sections}")
    
    return is_valid, missing_sections


def extract_headline_from_text(article_text: str) -> Optional[str]:
    """Extract headline from various formats.
    
    Args:
        article_text: Article text that may contain headline
        
    Returns:
        Headline text if found, None otherwise
    """
    # Try XML format first
    xml_pattern = r'<(?:headline|title)>(.*?)</(?:headline|title)>'
    match = re.search(xml_pattern, article_text, re.DOTALL | re.IGNORECASE)
    if match:
        headline = match.group(1).strip()
        if headline:
            return headline
    
    # Try HEADLINE: format
    if 'HEADLINE:' in article_text:
        headline_lines = article_text.split('HEADLINE:', 1)
        if len(headline_lines) > 1:
            headline = headline_lines[1].split('\n', 1)[0].strip()
            if headline:
                return headline
    
    return None
