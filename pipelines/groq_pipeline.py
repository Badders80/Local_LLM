"""
title: Groq LLM Pipeline
author: open-webui
date: 2025-12-23
version: 1.0
license: MIT
description: Direct Groq API pipeline using llama-3.3-70b-versatile
requirements: groq, python-dotenv
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
import os
import asyncio
from groq import AsyncGroq


class Pipeline:
    class Valves(BaseModel):
        GROQ_API_KEY: str = Field(
            default="",
            description="Groq API Key - leave empty to use environment variable"
        )
        GROQ_MODEL: str = Field(
            default="llama-3.3-70b-versatile",
            description="Groq model to use"
        )
        TEMPERATURE: float = Field(
            default=0.7,
            description="Model temperature (0.0-2.0)"
        )
        MAX_TOKENS: int = Field(
            default=2048,
            description="Maximum tokens in response"
        )

    def __init__(self):
        self.type = "manifold"
        self.id = "groq"
        self.name = "Groq"
        self.valves = self.Valves()
        self.client = None

    def get_groq_client(self):
        """Initialize Groq client with API key from valves or environment"""
        api_key = self.valves.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in valves or environment")
        return AsyncGroq(api_key=api_key)

    def pipelines(self) -> List[dict]:
        """Return available pipelines"""
        return [
            {
                "id": "llama-3.3-70b-versatile",
                "name": "Llama 3.3 70B (Groq)"
            },
            {
                "id": "llama-3.1-405b-reasoning",
                "name": "Llama 3.1 405B Reasoning (Groq)"
            },
            {
                "id": "mixtral-8x7b-32768",
                "name": "Mixtral 8x7B (Groq)"
            }
        ]

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Process chat request through Groq"""
        
        try:
            # Initialize client
            self.client = self.get_groq_client()
            
            # Use the model_id if it's from our pipelines, otherwise use valve setting
            model = model_id if "groq" in model_id.lower() or "llama" in model_id.lower() or "mixtral" in model_id.lower() else self.valves.GROQ_MODEL
            
            # Run async call
            result = asyncio.run(self._groq_call(messages, model))
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"

    async def _groq_call(self, messages: List[dict], model: str) -> str:
        """Make async call to Groq API"""
        
        # Convert OpenWebUI message format to Groq format
        groq_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            groq_messages.append({"role": role, "content": content})
        
        # Call Groq
        chat_completion = await self.client.chat.completions.create(
            messages=groq_messages,
            model=model,
            temperature=self.valves.TEMPERATURE,
            max_tokens=self.valves.MAX_TOKENS,
        )
        
        return chat_completion.choices[0].message.content
