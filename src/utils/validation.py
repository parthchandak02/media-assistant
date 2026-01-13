"""Input validation utilities."""
from .exceptions import ValidationError


def validate_topic(topic: str) -> None:
    """Validate topic is not empty.
    
    Args:
        topic: Topic string to validate
        
    Raises:
        ValidationError: If topic is invalid
    """
    if not topic or not topic.strip():
        raise ValidationError("Topic cannot be empty")
    
    if len(topic.strip()) < 3:
        raise ValidationError("Topic must be at least 3 characters long")


def validate_media_type(media_type: str, valid_types: list) -> None:
    """Validate media type is in valid list.
    
    Args:
        media_type: Media type to validate
        valid_types: List of valid media types
        
    Raises:
        ValidationError: If media type is invalid
    """
    if not media_type:
        raise ValidationError("Media type cannot be empty")
    
    if media_type not in valid_types:
        available = ', '.join(valid_types)
        raise ValidationError(
            f"Invalid media_type: {media_type}. "
            f"Valid types: {available}"
        )


def validate_length(length: str) -> None:
    """Validate article length parameter.
    
    Args:
        length: Length string to validate
        
    Raises:
        ValidationError: If length is invalid
    """
    valid_lengths = ['short', 'medium', 'long']
    
    if not length:
        raise ValidationError("Length cannot be empty")
    
    if length not in valid_lengths:
        raise ValidationError(
            f"Invalid length: {length}. "
            f"Valid lengths: {', '.join(valid_lengths)}"
        )


def validate_max_results(max_results: int) -> None:
    """Validate max_results is positive.
    
    Args:
        max_results: Maximum number of results
        
    Raises:
        ValidationError: If max_results is invalid
    """
    if not isinstance(max_results, int):
        raise ValidationError(f"max_results must be an integer, got {type(max_results)}")
    
    if max_results <= 0:
        raise ValidationError(f"max_results must be positive, got {max_results}")
    
    if max_results > 100:
        raise ValidationError(f"max_results cannot exceed 100, got {max_results}")
