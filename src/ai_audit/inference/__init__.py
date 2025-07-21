"""Inference engine for analyzing profile data."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import re
from ..models import ProfileData, Inference, InferenceType, Platform
from ..config import settings


class BaseInferenceEngine(ABC):
    """Base class for inference engines."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    async def make_inference(
        self, 
        profile_data: ProfileData, 
        inference_type: InferenceType
    ) -> Optional[Inference]:
        """Make a single inference about the profile data."""
        pass
    
    async def make_all_inferences(
        self, 
        profile_data: ProfileData
    ) -> List[Inference]:
        """Make all possible inferences about the profile data."""
        inferences = []
        
        for inference_type in InferenceType:
            try:
                inference = await self.make_inference(profile_data, inference_type)
                if inference:
                    inferences.append(inference)
            except Exception as e:
                print(f"Warning: Failed to make {inference_type} inference: {e}")
        
        return inferences
    
    def _parse_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse structured JSON response from LLM."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            # Clean up common formatting issues
            response_text = response_text.strip()
            if not response_text.startswith('{'):
                # Try to find the start of JSON
                start_idx = response_text.find('{')
                if start_idx != -1:
                    response_text = response_text[start_idx:]
            
            return json.loads(response_text)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Warning: Could not parse structured response: {e}")
            return {}


class OpenAIInferenceEngine(BaseInferenceEngine):
    """OpenAI-based inference engine."""
    
    def __init__(self):
        super().__init__("openai-gpt-4")
        try:
            import openai
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    async def make_inference(
        self, 
        profile_data: ProfileData, 
        inference_type: InferenceType
    ) -> Optional[Inference]:
        """Make inference using OpenAI API."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        prompt = self._build_prompt(profile_data, inference_type)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            return self._parse_inference_response(
                response_text, profile_data, inference_type
            )
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are an AI system that analyzes public profile data to make privacy-focused inferences. 

Your goal is to help users understand what personal information can be inferred from their public digital footprint.

For each analysis, provide a structured JSON response with:
- "value": The inferred value (be specific but not invasive)
- "confidence": A number between 0.0 and 1.0 indicating confidence
- "reasoning": Brief explanation of the inference basis
- "data_points": List of specific data points that led to this inference

Be ethical and responsible:
- Only make inferences that could reasonably be made by others
- Avoid overly sensitive or invasive conclusions
- Focus on helping users improve their privacy
- If you cannot make a confident inference, return confidence < 0.3"""
    
    def _build_prompt(self, profile_data: ProfileData, inference_type: InferenceType) -> str:
        """Build a prompt for the specific inference type."""
        base_info = f"""
Profile Platform: {profile_data.platform.value}
Username: {profile_data.username}
Profile Text:
{profile_data.profile_text}

Metadata: {json.dumps(profile_data.metadata, indent=2, default=str)}
"""
        
        inference_prompts = {
            InferenceType.PROGRAMMING_SKILLS: "Based on this profile, what programming languages, frameworks, or technical skills can you infer? Focus on concrete evidence from repositories, descriptions, or stated experience.",
            
            InferenceType.LOCATION: "What location information can be inferred from this profile? Consider stated location, time zone patterns, language use, or cultural references. Be specific about city/region if possible.",
            
            InferenceType.AGE_RANGE: "What age range can you infer for this person? Consider account creation date, cultural references, communication style, career stage indicators, or technology choices.",
            
            InferenceType.INTERESTS: "What interests, hobbies, or professional focus areas can you infer? Look for patterns in projects, descriptions, topics, or stated interests.",
            
            InferenceType.SENTIMENT: "What is the overall sentiment or personality style? Consider communication tone, emoji use, topic choices, and interaction patterns.",
            
            InferenceType.WORK_SCHEDULE: "What work schedule or time zone patterns can be inferred? Look at commit times, posting patterns, or activity schedules.",
            
            InferenceType.POLITICAL_LEANING: "Are there any political leanings that can be inferred? Be very careful and only note clear indicators from stated positions or causes supported.",
            
            InferenceType.EDUCATION_LEVEL: "What education level or background can be inferred? Consider communication style, technical depth, stated credentials, or project complexity.",
            
            InferenceType.HEALTH_SIGNALS: "Are there any health-related signals? Only note obvious mentions of health topics, fitness activities, or medical interests. Be extremely cautious.",
            
            InferenceType.PURCHASING_POWER: "What economic indicators can be inferred? Consider technology choices, travel mentions, lifestyle indicators, or professional level."
        }
        
        specific_prompt = inference_prompts.get(inference_type, "Analyze this profile data.")
        
        return f"{base_info}\n\nAnalysis Request: {specific_prompt}\n\nProvide your response as JSON with the required fields."
    
    def _parse_inference_response(
        self, 
        response_text: str, 
        profile_data: ProfileData, 
        inference_type: InferenceType
    ) -> Optional[Inference]:
        """Parse the LLM response into an Inference object."""
        parsed = self._parse_structured_response(response_text)
        
        if not parsed:
            # Try to extract key information from unstructured response
            parsed = self._extract_fallback_inference(response_text)
        
        if not parsed or "value" not in parsed:
            return None
        
        try:
            confidence = float(parsed.get("confidence", 0.0))
            
            # Skip low-confidence inferences
            if confidence < 0.3:
                return None
            
            return Inference(
                type=inference_type,
                value=str(parsed["value"]),
                confidence=confidence,
                reasoning=parsed.get("reasoning", ""),
                source_platforms=[profile_data.platform],
                model_used=self.model_name
            )
            
        except (ValueError, KeyError) as e:
            print(f"Warning: Could not parse inference response: {e}")
            return None
    
    def _extract_fallback_inference(self, response_text: str) -> Dict[str, Any]:
        """Extract inference from unstructured response as fallback."""
        # Simple pattern matching for common response formats
        patterns = {
            "confidence": r"confidence[:\s]+([0-9.]+)",
            "value": r"(?:value|conclusion|inference)[:\s]+([^\n]+)",
            "reasoning": r"(?:reasoning|explanation|because)[:\s]+([^\n]+)"
        }
        
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()
        
        return result


class AnthropicInferenceEngine(BaseInferenceEngine):
    """Anthropic Claude-based inference engine."""
    
    def __init__(self):
        super().__init__("anthropic-claude-3")
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
    
    async def make_inference(
        self, 
        profile_data: ProfileData, 
        inference_type: InferenceType
    ) -> Optional[Inference]:
        """Make inference using Anthropic API."""
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        
        # Similar implementation to OpenAI but using Anthropic's API
        # This would follow the same pattern but with Claude-specific formatting
        prompt = self._build_anthropic_prompt(profile_data, inference_type)
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            return self._parse_inference_response(
                response_text, profile_data, inference_type
            )
            
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return None
    
    def _build_anthropic_prompt(self, profile_data: ProfileData, inference_type: InferenceType) -> str:
        """Build Anthropic-specific prompt."""
        # Reuse the OpenAI prompt building logic for now
        openai_engine = OpenAIInferenceEngine()
        base_prompt = openai_engine._build_prompt(profile_data, inference_type)
        
        # Add Claude-specific instructions
        claude_instructions = """
Please analyze the profile data and respond with a JSON object containing your inference.

Be responsible and ethical in your analysis. Focus on helping the user understand their digital privacy exposure.
"""
        
        return f"{claude_instructions}\n\n{base_prompt}"
    
    def _parse_inference_response(self, response_text: str, profile_data: ProfileData, inference_type: InferenceType) -> Optional[Inference]:
        """Parse Anthropic response - reuse OpenAI logic for now."""
        openai_engine = OpenAIInferenceEngine()
        return openai_engine._parse_inference_response(response_text, profile_data, inference_type)


class InferenceOrchestrator:
    """Orchestrates inference across multiple engines and profile data."""
    
    def __init__(self):
        self.engines = {}
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available inference engines."""
        try:
            if settings.openai_api_key:
                self.engines["openai"] = OpenAIInferenceEngine()
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI engine: {e}")
        
        try:
            if settings.anthropic_api_key:
                self.engines["anthropic"] = AnthropicInferenceEngine()
        except Exception as e:
            print(f"Warning: Could not initialize Anthropic engine: {e}")
    
    async def analyze_profiles(self, profile_data_list: List[ProfileData]) -> List[Inference]:
        """Analyze multiple profiles and return all inferences."""
        all_inferences = []
        
        # Use the default LLM provider
        engine = self.engines.get(settings.default_llm_provider)
        if not engine and self.engines:
            # Fallback to any available engine
            engine = next(iter(self.engines.values()))
        
        if not engine:
            raise ValueError("No inference engines available. Please configure API keys.")
        
        for profile_data in profile_data_list:
            try:
                inferences = await engine.make_all_inferences(profile_data)
                all_inferences.extend(inferences)
            except Exception as e:
                print(f"Warning: Failed to analyze {profile_data.platform} profile: {e}")
        
        return all_inferences
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engine names."""
        return list(self.engines.keys())
