from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
import aiohttp
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the AI model"""
        pass
    
    @abstractmethod
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the AI model"""
        pass

class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible AI provider"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or settings.AI_PROVIDER_URL
        self.api_key = api_key or settings.AI_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the AI model"""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"AI API error: {response.status} - {error_text}")
                        raise Exception(f"AI API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise
    
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the AI model"""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"AI API error: {response.status} - {error_text}")
                        raise Exception(f"AI API error: {response.status} - {error_text}")
                    
                    async for line in response.content:
                        if line:
                            decoded_line = line.decode("utf-8")
                            if decoded_line.startswith("data: "):
                                data = decoded_line[6:]  # Remove "data: " prefix
                                if data.strip() == "[DONE]":
                                    break
                                try:
                                    json_data = json.loads(data)
                                    delta = json_data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.error(f"Error streaming AI response: {str(e)}")
            raise

# Factory function to get the appropriate AI provider
def get_ai_provider(provider_type: str = "openai") -> AIProvider:
    """Factory function to get the appropriate AI provider"""
    if provider_type == "openai":
        return OpenAICompatibleProvider()
    # Add other providers as needed
    else:
        return OpenAICompatibleProvider()