"""
Gemini Client - Google Gemini Integration for Maximus AI
========================================================

Cliente para Google Gemini com suporte a:
- Text generation
- Tool calling (function calling)
- Chain-of-Thought prompting
- Embeddings

Model: gemini-2.0-flash-exp (mais rápido e barato)
Alternative: gemini-1.5-pro (mais poderoso)
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GeminiConfig:
    """Configuração do Gemini"""
    api_key: str
    model: str = "gemini-2.0-flash-exp"  # Fastest & cheapest
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


class GeminiClient:
    """
    Cliente para Google Gemini API

    Suporta:
    - Text generation
    - Function calling (tool use)
    - Streaming (opcional)
    - Embeddings
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: GeminiConfig):
        self.config = config
        self.api_key = config.api_key
        self.model = config.model

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Gera texto usando Gemini.

        Args:
            prompt: Prompt do usuário
            system_instruction: Instrução de sistema
            tools: Lista de tools (function declarations)
            temperature: Temperatura (0-1)
            max_tokens: Máximo de tokens

        Returns:
            Response do Gemini com text e tool_calls
        """
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"

        # Build request
        request_body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature or self.config.temperature,
                "maxOutputTokens": max_tokens or self.config.max_tokens,
            }
        }

        # Add system instruction
        if system_instruction:
            request_body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Add tools (function declarations)
        if tools:
            request_body["tools"] = [
                {
                    "functionDeclarations": self._convert_tools_to_gemini_format(tools)
                }
            ]

        # Call API
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Gemini API error: {response.status_code} - {error_detail}")

            result = response.json()

        # Parse response
        return self._parse_gemini_response(result)

    async def generate_with_conversation(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Gera texto com histórico de conversa.

        Args:
            messages: Lista de mensagens [{"role": "user"|"model", "content": "..."}]
            system_instruction: Instrução de sistema
            tools: Lista de tools

        Returns:
            Response do Gemini
        """
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "model" if msg["role"] in ["assistant", "model"] else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        request_body = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            }
        }

        if system_instruction:
            request_body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if tools:
            request_body["tools"] = [
                {
                    "functionDeclarations": self._convert_tools_to_gemini_format(tools)
                }
            ]

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

            result = response.json()

        return self._parse_gemini_response(result)

    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Gera embeddings para texto.

        Args:
            text: Texto para embedding

        Returns:
            Lista de floats (embedding vector)
        """
        url = f"{self.BASE_URL}/models/text-embedding-004:embedContent"

        request_body = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise Exception(f"Gemini Embeddings error: {response.status_code}")

            result = response.json()

        return result.get("embedding", {}).get("values", [])

    def _convert_tools_to_gemini_format(self, tools: List[Dict]) -> List[Dict]:
        """
        Converte tools do formato Anthropic/OpenAI para Gemini.

        Input format (Anthropic-style):
        {
            "name": "get_weather",
            "description": "Get weather",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }

        Output format (Gemini-style):
        {
            "name": "get_weather",
            "description": "Get weather",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        gemini_tools = []

        for tool in tools:
            gemini_tool = {
                "name": tool["name"],
                "description": tool.get("description", ""),
            }

            # Convert input_schema to parameters
            if "input_schema" in tool:
                gemini_tool["parameters"] = tool["input_schema"]
            elif "parameters" in tool:
                gemini_tool["parameters"] = tool["parameters"]

            gemini_tools.append(gemini_tool)

        return gemini_tools

    def _parse_gemini_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse resposta do Gemini para formato unificado.

        Returns:
            {
                "text": str,
                "tool_calls": List[Dict],
                "finish_reason": str,
                "raw": Dict
            }
        """
        candidates = result.get("candidates", [])

        if not candidates:
            return {
                "text": "",
                "tool_calls": [],
                "finish_reason": "error",
                "raw": result
            }

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        text = ""
        tool_calls = []

        for part in parts:
            # Text response
            if "text" in part:
                text += part["text"]

            # Function call (tool use)
            elif "functionCall" in part:
                func_call = part["functionCall"]
                tool_calls.append({
                    "name": func_call.get("name"),
                    "arguments": func_call.get("args", {})
                })

        finish_reason = candidate.get("finishReason", "STOP")

        return {
            "text": text,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "raw": result
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do Gemini client"""

    # Setup
    config = GeminiConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-2.0-flash-exp",
        temperature=0.7
    )

    client = GeminiClient(config)

    # Exemplo 1: Text generation simples
    print("=== EXAMPLE 1: Simple Text Generation ===")
    response = await client.generate_text(
        prompt="What are the top 3 cybersecurity threats in 2024?",
        system_instruction="You are Maximus, an elite cybersecurity AI analyst."
    )
    print(f"Text: {response['text'][:200]}...")

    # Exemplo 2: With tools (function calling)
    print("\n=== EXAMPLE 2: Function Calling ===")
    tools = [
        {
            "name": "analyze_ip",
            "description": "Analyze an IP address for threats",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ip": {"type": "string", "description": "IP address to analyze"}
                },
                "required": ["ip"]
            }
        }
    ]

    response = await client.generate_text(
        prompt="Analyze the IP 8.8.8.8 for threats",
        system_instruction="You are Maximus. Use the available tools to answer.",
        tools=tools
    )

    print(f"Text: {response['text']}")
    print(f"Tool calls: {response['tool_calls']}")

    # Exemplo 3: Conversation
    print("\n=== EXAMPLE 3: Conversation ===")
    messages = [
        {"role": "user", "content": "What is a DDoS attack?"},
        {"role": "model", "content": "A DDoS is a distributed denial-of-service attack..."},
        {"role": "user", "content": "How can I protect against it?"}
    ]

    response = await client.generate_with_conversation(
        messages=messages,
        system_instruction="You are Maximus, a cybersecurity expert."
    )
    print(f"Response: {response['text'][:200]}...")

    # Exemplo 4: Embeddings
    print("\n=== EXAMPLE 4: Embeddings ===")
    embedding = await client.generate_embeddings("CVE-2024-1234 critical vulnerability")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
