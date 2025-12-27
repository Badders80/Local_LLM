"""
title: Hybrid LLM Pipeline (Groq + Gemini Watchdog)
author: open-webui
date: 2025-12-23
version: 1.0
license: MIT
description: A hybrid LLM pipeline that uses Groq for fast responses with optional Gemini verification
requirements: requests
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
import requests
import os


class Pipeline:
    class Valves(BaseModel):
        HYBRID_ORCHESTRATOR_URL: str = Field(
            default="http://host.docker.internal:8000",
            description="URL of the Hybrid LLM Orchestrator service"
        )
        ENABLE_VERIFICATION: bool = Field(
            default=True,
            description="Enable Gemini watchdog verification for all requests"
        )
        SHOW_CONFIDENCE: bool = Field(
            default=True,
            description="Display confidence scores in responses"
        )

    def __init__(self):
        self.type = "manifold"
        self.id = "hybrid_llm"
        self.name = "Hybrid LLM (Groq+Gemini)"
        self.valves = self.Valves()

    def pipelines(self) -> List[dict]:
        """Return available pipelines - same as get_models for compatibility"""
        return self.get_models()

    def get_models(self) -> List[dict]:
        """Return available models"""
        return [
            {
                "id": "hybrid-groq-gemini",
                "name": "Hybrid: Groq (fast) + Gemini (verify)"
            }
        ]

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Process the chat request through the hybrid orchestrator"""
        
        # Call the hybrid orchestrator with full message context
        try:
            response = requests.post(
                f"{self.valves.HYBRID_ORCHESTRATOR_URL}/hybrid-chat",
                json={
                    "messages": messages,  # Pass full conversation context
                    "verify": self.valves.ENABLE_VERIFICATION
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Build the response
            answer = result["content"]
            
            # Add metadata if enabled
            if self.valves.SHOW_CONFIDENCE:
                confidence = result["confidence"]
                timing = result["timing"]
                watchdog = result["watchdog"]
                
                metadata = f"\n\n---\n"
                metadata += f"**Confidence:** {confidence} | "
                metadata += f"**Response time:** {timing['groq_ms']:.0f}ms"
                
                if watchdog["enabled"]:
                    metadata += f" | **Verification:** {watchdog['status']}"
                    if watchdog['status'] == 'pending':
                        request_id = result['request_id']
                        metadata += f" (check `/watchdog/{request_id}` later)"
                
                answer = answer + metadata
            
            return answer
            
        except requests.exceptions.RequestException as e:
            return f"Error calling hybrid orchestrator: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
