"""AI pattern detection and replacement utilities for humanization."""
from typing import List, Dict, Tuple
import re


# Common AI-sounding phrases that should be replaced
COMMON_AI_PHRASES = [
    "In conclusion",
    "It is important to note",
    "Furthermore",
    "Moreover",
    "Additionally",
    "It should be noted that",
    "It is worth noting that",
    "It is crucial to understand",
    "It is essential to recognize",
    "As we have seen",
    "As previously mentioned",
    "As stated above",
    "In summary",
    "To summarize",
    "In other words",
    "That is to say",
    "Needless to say",
    "It goes without saying",
    "First and foremost",
    "Last but not least",
    "Without a doubt",
    "Undoubtedly",
    "It is clear that",
    "It is evident that",
    "It can be seen that",
    "One can observe that",
    "It is apparent that",
    "This demonstrates that",
    "This indicates that",
    "This suggests that",
    "This highlights the fact that",
    "This underscores the importance of",
    "This serves to",
    "This allows for",
    "This enables",
    "This facilitates",
    "This provides",
    "This offers",
    "This represents",
    "This constitutes",
    "This embodies",
    "This exemplifies",
    "This illustrates",
    "This showcases",
    "This reveals",
    "This unveils",
    "This sheds light on",
    "This brings to light",
    "This draws attention to",
    "This calls attention to",
    "This emphasizes",
    "This reinforces",
    "This validates",
    "This confirms",
]


# Media-type specific patterns
MEDIA_TYPE_PATTERNS = {
    "scientific_journal": [
        "It should be noted that",
        "It is important to note that",
        "As can be seen",
        "It is evident that",
        "This demonstrates",
        "This indicates",
        "This suggests",
    ],
    "research_magazine": [
        "It is worth noting",
        "This highlights",
        "This underscores",
        "This reveals",
        "This unveils",
    ],
    "tech_news": [
        "It goes without saying",
        "Needless to say",
        "This enables",
        "This allows for",
        "This facilitates",
    ],
    "academic_news": [
        "It is important to recognize",
        "This represents",
        "This constitutes",
        "This embodies",
    ],
}


def detect_ai_patterns(text: str, media_type: str = None) -> List[Tuple[str, int]]:
    """Detect AI-sounding phrases in text.
    
    Args:
        text: Text to analyze
        media_type: Optional media type for specific patterns
        
    Returns:
        List of tuples (phrase, count) for detected patterns
    """
    detected = []
    text_lower = text.lower()
    
    # Check common patterns
    for phrase in COMMON_AI_PHRASES:
        count = text_lower.count(phrase.lower())
        if count > 0:
            detected.append((phrase, count))
    
    # Check media-type specific patterns
    if media_type and media_type in MEDIA_TYPE_PATTERNS:
        for phrase in MEDIA_TYPE_PATTERNS[media_type]:
            count = text_lower.count(phrase.lower())
            if count > 0:
                detected.append((phrase, count))
    
    return detected


def get_replacement_suggestions(phrase: str, media_type: str = None) -> List[str]:
    """Get natural replacement suggestions for AI-sounding phrases.
    
    Args:
        phrase: AI-sounding phrase to replace
        media_type: Media type for context-appropriate replacements
        
    Returns:
        List of replacement suggestions
    """
    replacements = {
        "In conclusion": ["", "Ultimately", "Finally"],
        "It is important to note": ["", "Note that", "Keep in mind"],
        "Furthermore": ["", "Also", "Plus"],
        "Moreover": ["", "Additionally", "What's more"],
        "Additionally": ["", "Also", "Plus"],
        "It should be noted that": ["", "Note that", "Keep in mind"],
        "It is worth noting that": ["", "Notably", "Importantly"],
        "It is crucial to understand": ["", "Understanding", "It's key that"],
        "As we have seen": ["", "As shown", "As demonstrated"],
        "In summary": ["", "Overall", "In short"],
        "To summarize": ["", "In short", "Overall"],
        "Needless to say": ["", "Of course", "Clearly"],
        "It goes without saying": ["", "Obviously", "Clearly"],
        "First and foremost": ["", "First", "Primarily"],
        "Last but not least": ["", "Finally", "Lastly"],
        "Without a doubt": ["", "Certainly", "Definitely"],
        "Undoubtedly": ["", "Certainly", "Definitely"],
        "It is clear that": ["", "Clearly", "Obviously"],
        "It is evident that": ["", "Evidently", "Clearly"],
        "This demonstrates": ["", "This shows", "This proves"],
        "This indicates": ["", "This suggests", "This shows"],
        "This suggests": ["", "This implies", "This shows"],
        "This enables": ["", "This allows", "This makes possible"],
        "This allows for": ["", "This enables", "This makes possible"],
        "This facilitates": ["", "This helps", "This makes easier"],
        "This provides": ["", "This offers", "This gives"],
        "This represents": ["", "This is", "This shows"],
        "This constitutes": ["", "This is", "This forms"],
    }
    
    phrase_lower = phrase.lower()
    if phrase_lower in replacements:
        return replacements[phrase_lower]
    
    # Generic replacements for patterns not in dictionary
    return [""]


def analyze_sentence_variation(text: str) -> Dict[str, float]:
    """Analyze sentence variation metrics (burstiness and perplexity indicators).
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with metrics:
        - avg_sentence_length: Average words per sentence
        - sentence_length_std: Standard deviation of sentence lengths
        - sentence_count: Number of sentences
        - variation_score: Higher = more variation (better)
    """
    import re
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return {
            "avg_sentence_length": 0,
            "sentence_length_std": 0,
            "sentence_count": 0,
            "variation_score": 0,
        }
    
    # Calculate sentence lengths
    sentence_lengths = [len(s.split()) for s in sentences]
    
    avg_length = sum(sentence_lengths) / len(sentence_lengths)
    
    # Calculate standard deviation
    variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    std_dev = variance ** 0.5
    
    # Variation score: higher std_dev relative to avg = more variation
    variation_score = std_dev / avg_length if avg_length > 0 else 0
    
    return {
        "avg_sentence_length": avg_length,
        "sentence_length_std": std_dev,
        "sentence_count": len(sentences),
        "variation_score": variation_score,
    }
