"""Maximus OSINT Service - AI Processor.

This module implements the AI Processor for the Maximus AI's OSINT Service.
It is responsible for leveraging advanced artificial intelligence capabilities,
particularly large language models (LLMs), to process, synthesize, and extract
meaningful insights from raw OSINT data.

Key functionalities include:
- Summarizing large volumes of unstructured text.
- Identifying key entities, relationships, and events.
- Performing sentiment analysis and credibility assessment.
- Generating initial hypotheses or contextual summaries from collected data.

This processor is crucial for transforming raw, often noisy, OSINT data into
structured, actionable intelligence, enabling other Maximus AI services to make
more informed decisions and conduct more effective investigations.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from openai import AsyncOpenAI


class AIProcessor:
    """Leverages Google Gemini and OpenAI to process, synthesize, and extract meaningful insights
    from raw OSINT data.

    Uses Gemini Pro and GPT-4 for advanced analysis of collected intelligence data.
    """

    def __init__(self):
        """Initializes the AIProcessor with Gemini and OpenAI configuration."""
        self.processing_history: List[Dict[str, Any]] = []
        self.last_processing_time: Optional[datetime] = None
        self.current_status: str = "ready_for_processing"
        
        # Configure Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            self.gemini_enabled = True
            print("[AIProcessor] Gemini API configured successfully")
        else:
            self.gemini_enabled = False
            print("[AIProcessor] WARNING: GEMINI_API_KEY not found")
        
        # Configure OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)
            self.openai_enabled = True
            print("[AIProcessor] OpenAI API configured successfully")
        else:
            self.openai_enabled = False
            print("[AIProcessor] WARNING: OPENAI_API_KEY not found")
        
        # Determine primary AI provider
        if not self.gemini_enabled and not self.openai_enabled:
            print("[AIProcessor] WARNING: No AI APIs configured, using fallback mode")

    async def process_raw_data(self, raw_data: List[Dict[str, Any]], query_context: str) -> Dict[str, Any]:
        """Processes raw OSINT data using AI to extract insights and generate summaries.

        Args:
            raw_data (List[Dict[str, Any]]): A list of raw data entries collected by scrapers.
            query_context (str): The original query or context of the OSINT investigation.

        Returns:
            Dict[str, Any]: A dictionary containing AI-generated insights and summaries.
        """
        print(f"[AIProcessor] Processing {len(raw_data)} raw data entries for query: {query_context}")
        
        # Try OpenAI first (more reliable), then Gemini, then fallback
        if self.openai_enabled and raw_data:
            try:
                processed_result = await self._process_with_openai(raw_data, query_context)
                processed_result["ai_provider"] = "openai"
            except Exception as e:
                print(f"[AIProcessor] OpenAI processing failed: {e}")
                if self.gemini_enabled:
                    try:
                        processed_result = await self._process_with_gemini(raw_data, query_context)
                        processed_result["ai_provider"] = "gemini"
                    except Exception as e2:
                        print(f"[AIProcessor] Gemini processing failed: {e2}, using fallback")
                        processed_result = self._fallback_processing(raw_data, query_context)
                else:
                    processed_result = self._fallback_processing(raw_data, query_context)
        elif self.gemini_enabled and raw_data:
            try:
                processed_result = await self._process_with_gemini(raw_data, query_context)
                processed_result["ai_provider"] = "gemini"
            except Exception as e:
                print(f"[AIProcessor] Gemini processing failed: {e}, using fallback")
                processed_result = self._fallback_processing(raw_data, query_context)
        else:
            processed_result = self._fallback_processing(raw_data, query_context)
        
        self.processing_history.append(processed_result)
        self.last_processing_time = datetime.now()
        return processed_result

    async def _process_with_openai(self, raw_data: List[Dict[str, Any]], query_context: str) -> Dict[str, Any]:
        """Process data using OpenAI GPT-4."""
        data_summary = self._build_data_summary(raw_data, query_context)
        
        prompt = f"""Analyze this OSINT investigation data and provide:
1. Executive summary (2-3 sentences)
2. Key entities identified (people, organizations, locations)
3. Risk assessment (LOW/MEDIUM/HIGH with brief justification)
4. Behavioral patterns detected
5. Recommended next actions

Investigation Target: {query_context}

Data Sources Analyzed:
{data_summary}

Provide analysis in structured format."""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert OSINT analyst. Provide concise, actionable intelligence analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_analysis = response.choices[0].message.content
        
        # Parse key insights
        extracted_entities = self._extract_entities_from_text(ai_analysis)
        risk_level = self._extract_risk_level(ai_analysis)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "query_context": query_context,
            "ai_summary": ai_analysis,
            "extracted_entities": extracted_entities,
            "risk_level": risk_level,
            "gemini_powered": False,
            "data_sources_count": len(raw_data)
        }

    async def _process_with_gemini(self, raw_data: List[Dict[str, Any]], query_context: str) -> Dict[str, Any]:
        """Process data using Google Gemini."""
        data_summary = self._build_data_summary(raw_data, query_context)
        
        prompt = f"""Analyze this OSINT investigation data and provide:
1. Executive summary (2-3 sentences)
2. Key entities identified (people, organizations, locations)
3. Risk assessment (LOW/MEDIUM/HIGH with brief justification)
4. Behavioral patterns detected
5. Recommended next actions

Investigation Target: {query_context}

Data Sources Analyzed:
{data_summary}

Provide analysis in structured format."""

        response = await asyncio.to_thread(
            self.gemini_model.generate_content, prompt
        )
        
        ai_analysis = response.text
        
        # Parse key insights
        extracted_entities = self._extract_entities_from_text(ai_analysis)
        risk_level = self._extract_risk_level(ai_analysis)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "query_context": query_context,
            "ai_summary": ai_analysis,
            "extracted_entities": extracted_entities,
            "risk_level": risk_level,
            "gemini_powered": True,
            "data_sources_count": len(raw_data)
        }

    def _build_data_summary(self, raw_data: List[Dict[str, Any]], query: str) -> str:
        """Build summary of collected data for AI prompt."""
        summary_parts = []
        for entry in raw_data[:5]:  # Limit to first 5 sources to avoid token limits
            source = entry.get("source", "unknown")
            data = entry.get("data", {})
            
            if isinstance(data, dict):
                # Extract key fields
                key_info = []
                if "found_platforms" in data:
                    platforms = [p["platform"] for p in data["found_platforms"] if p.get("found")]
                    key_info.append(f"Found on: {', '.join(platforms[:5])}")
                if "found_count" in data:
                    key_info.append(f"Total matches: {data['found_count']}")
                if "confidence_score" in data:
                    key_info.append(f"Confidence: {data['confidence_score']}%")
                
                if key_info:
                    summary_parts.append(f"- {source}: {' | '.join(key_info)}")
        
        return "\n".join(summary_parts) if summary_parts else "No detailed data available"

    def _extract_entities_from_text(self, text: str) -> List[str]:
        """Extract entity mentions from AI response."""
        entities = []
        keywords = ["username", "email", "phone", "location", "organization", "platform"]
        
        for keyword in keywords:
            if keyword.lower() in text.lower():
                entities.append(keyword)
        
        return entities

    def _extract_risk_level(self, text: str) -> str:
        """Extract risk level from AI response."""
        text_lower = text.lower()
        if "high risk" in text_lower or "risk: high" in text_lower:
            return "HIGH"
        elif "medium risk" in text_lower or "risk: medium" in text_lower:
            return "MEDIUM"
        elif "low risk" in text_lower or "risk: low" in text_lower:
            return "LOW"
        return "UNKNOWN"

    def _fallback_processing(self, raw_data: List[Dict[str, Any]], query_context: str) -> Dict[str, Any]:
        """Fallback processing when AI APIs are unavailable."""
        synthesized_summary = f"Basic analysis for query '{query_context}':\n"
        extracted_entities: List[str] = []
        
        for entry in raw_data:
            content = str(entry.get("data", ""))
            source = entry.get("source", "unknown")
            synthesized_summary += f"- {source}: {content[:100]}...\n"
            
            # Simple entity extraction
            if "email" in content.lower():
                extracted_entities.append("email_address")
            if "phone" in content.lower():
                extracted_entities.append("phone_number")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "query_context": query_context,
            "ai_summary": synthesized_summary,
            "extracted_entities": list(set(extracted_entities)),
            "risk_level": "LOW",
            "gemini_powered": False,
            "ai_provider": "fallback",
            "data_sources_count": len(raw_data)
        }

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the AI Processor.

        Returns:
            Dict[str, Any]: A dictionary summarizing the Processor's status.
        """
        return {
            "status": self.current_status,
            "gemini_enabled": self.gemini_enabled,
            "openai_enabled": self.openai_enabled,
            "total_processing_tasks": len(self.processing_history),
            "last_processing": (self.last_processing_time.isoformat() if self.last_processing_time else "N/A"),
        }
