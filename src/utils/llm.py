"""LLM provider abstractions for Gemini and Perplexity."""
from abc import ABC, abstractmethod
from typing import Optional
from google import genai
from google.genai import types as genai_types
import requests
from .env import EnvLoader
from .config_loader import LLMConfig
from .exceptions import GeminiAPIError, PerplexityAPIError
from .logger import get_logger
from .retry import retry_with_backoff

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system/instruction prompt
            max_tokens: Optional override for max output tokens
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """Generate text with streaming.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system/instruction prompt
            
        Yields:
            Text chunks as they're generated
        """
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, config: LLMConfig, env_loader: EnvLoader):
        """Initialize Gemini provider.
        
        Args:
            config: LLM configuration
            env_loader: Environment loader for API keys
        """
        self.config = config
        api_key = env_loader.require('GEMINI_API_KEY')
        
        # Initialize client with new google.genai API
        self.client = genai.Client(api_key=api_key)
        self.model_name = config.model
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generate text using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            max_tokens: Optional override for max output tokens
            
        Returns:
            Generated text
            
        Raises:
            GeminiAPIError: If Gemini API returns an error
        """
        try:
            # Combine system prompt and user prompt
            contents = prompt
            if system_prompt:
                contents = f"{system_prompt}\n\n{prompt}"
            
            # Prepare generation config with optional max_tokens override
            config = genai_types.GenerateContentConfig(
                temperature=self.config.temperature,
                max_output_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
            )
            
            logger.debug(f"Generating text with Gemini model: {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # #region agent log
            try:
                import json, os
                log_path = "/Users/pchandak/Documents/media-article-writer/.cursor/debug.log"
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                response_text = response.text if response.text else ""
                actual_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"location":"llm.py:95","message":"LLM response received","data":{"response_length":len(response_text),"max_tokens":actual_max_tokens,"response_preview":response_text[:300] if response_text else "","response_end":response_text[-300:] if len(response_text) > 300 else response_text},"timestamp":__import__('time').time(),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            except Exception as e:
                pass
            # #endregion
            
            if not response.text:
                logger.warning("Gemini API returned empty response")
                raise GeminiAPIError("Gemini API returned empty response")
            
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Handle specific error types if available
            if "blocked" in error_msg.lower() or "safety" in error_msg.lower():
                logger.error(f"Gemini API blocked prompt: {error_msg}")
                raise GeminiAPIError(f"Gemini API blocked prompt: {error_msg}")
            logger.error(f"Gemini API error: {error_msg}")
            raise GeminiAPIError(f"Gemini API error: {error_msg}")
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """Generate text with streaming using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            
        Yields:
            Text chunks as they're generated
            
        Raises:
            GeminiAPIError: If Gemini API returns an error
        """
        try:
            contents = prompt
            if system_prompt:
                contents = f"{system_prompt}\n\n{prompt}"
            
            config = genai_types.GenerateContentConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )
            
            logger.debug(f"Streaming text generation with Gemini model: {self.model_name}")
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini API streaming error: {str(e)}")
            raise GeminiAPIError(f"Gemini API streaming error: {str(e)}")


class PerplexityProvider(LLMProvider):
    """Perplexity AI LLM provider."""
    
    def __init__(self, config: LLMConfig, env_loader: EnvLoader):
        """Initialize Perplexity provider.
        
        Args:
            config: LLM configuration
            env_loader: Environment loader for API keys
        """
        self.config = config
        self.api_key = env_loader.require('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
        # Map model names
        model_map = {
            'sonar-pro': 'sonar-pro',
            'sonar': 'sonar',
        }
        self.model_name = model_map.get(config.model, config.model)
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generate text using Perplexity API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            max_tokens: Optional override for max output tokens
            
        Returns:
            Generated text
            
        Raises:
            PerplexityAPIError: If Perplexity API returns an error
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            }
            
            logger.debug(f"Generating text with Perplexity model: {self.model_name}")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                logger.error("Perplexity API returned no choices")
                raise PerplexityAPIError("Perplexity API returned no choices")
            
            content = result['choices'][0]['message'].get('content', '')
            if not content:
                logger.warning("Perplexity API returned empty content")
                raise PerplexityAPIError("Perplexity API returned empty content")
            
            return content
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                logger.error("Perplexity API rate limit exceeded")
                raise PerplexityAPIError(f"Perplexity API rate limit exceeded: {str(e)}")
            logger.error(f"Perplexity API HTTP error: {str(e)}")
            raise PerplexityAPIError(f"Perplexity API HTTP error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API request error: {str(e)}")
            raise PerplexityAPIError(f"Perplexity API request error: {str(e)}")
        except KeyError as e:
            logger.error(f"Unexpected Perplexity API response format: {str(e)}")
            raise PerplexityAPIError(f"Unexpected Perplexity API response format: {str(e)}")
        except Exception as e:
            logger.error(f"Perplexity API unexpected error: {str(e)}")
            raise PerplexityAPIError(f"Perplexity API error: {str(e)}")
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """Generate text with streaming using Perplexity API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            
        Yields:
            Text chunks as they're generated
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                logger.error("Perplexity API rate limit exceeded during streaming")
                raise PerplexityAPIError(f"Perplexity API rate limit exceeded: {str(e)}")
            logger.error(f"Perplexity API HTTP error during streaming: {str(e)}")
            raise PerplexityAPIError(f"Perplexity API HTTP error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API request error during streaming: {str(e)}")
            raise PerplexityAPIError(f"Perplexity API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Perplexity API streaming error: {str(e)}")
            raise PerplexityAPIError(f"Perplexity API streaming error: {str(e)}")


def get_llm_provider(config: LLMConfig, env_loader: EnvLoader) -> LLMProvider:
    """Factory function to get appropriate LLM provider.
    
    Args:
        config: LLM configuration
        env_loader: Environment loader
        
    Returns:
        LLMProvider instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider_name = config.provider.lower()
    
    if provider_name == 'gemini':
        return GeminiProvider(config, env_loader)
    elif provider_name == 'perplexity':
        return PerplexityProvider(config, env_loader)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {config.provider}. "
            f"Supported providers: 'gemini', 'perplexity'"
        )
