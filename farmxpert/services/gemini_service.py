import google.generativeai as genai
import asyncio
import json
import hashlib
from typing import Dict, Any, List, AsyncGenerator, Optional
from farmxpert.config.settings import settings
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.redis_cache_service import redis_cache

class GeminiService:
    def __init__(self):
        self.logger = get_logger("gemini_service")
        self.model = None
        self._cache = {}  # Fallback in-memory cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini API with fallback models"""
        try:
            if not settings.gemini_api_key:
                self.logger.warning("GEMINI_API_KEY not found in environment variables")
                return
            
            genai.configure(api_key=settings.gemini_api_key)
            
            # Try the configured model first, then fallback models
            fallback_models = [
                settings.gemini_model,
                "gemini-flash-latest",
                "gemini-pro-latest",
                "gemini-pro"
            ]
            
            for model_name in fallback_models:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.logger.info(f"Gemini API initialized successfully with model: {model_name}")
                    return
                except Exception as model_error:
                    self.logger.warning(f"Failed to initialize with model {model_name}: {model_error}")
                    continue
            
            # If all models fail
            self.logger.error("Failed to initialize with any available model")
            self.model = None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {e}")
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using Gemini API (non-streaming for backward compatibility)"""
        if not self.model:
            return "Gemini API not available. Please check your API key configuration."
        
        try:
            context = context or {}

            # Check cache first to reduce API usage
            cache_key = self._get_cache_key(prompt, context)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                return cached_response

            # Build the full prompt with context
            if context.get("raw_prompt"):
                full_prompt = prompt
            else:
                full_prompt = self._build_prompt(prompt, context)
            
            # Generate response
            safety_settings = None
            # Prefer concise JSON responses; cap tokens
            generation_config = {
                "temperature": min(0.4, settings.gemini_temperature or 0.4),
                "max_output_tokens": min(512, settings.gemini_max_output_tokens or 512),
            }
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=settings.gemini_request_timeout
            )
            
            # Ensure trimmed minimal text
            out = (response.text or "").strip()
            if out:
                await self._cache_response(cache_key, out)
            return out
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    async def generate_streaming_response(self, prompt: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini API with caching"""
        if not self.model:
            yield "Gemini API not available. Please check your API key configuration."
            return
        
        # Check cache first
        cache_key = self._get_cache_key(prompt, context)
        cached_response = await self._get_cached_response(cache_key)
        
        if cached_response:
            # Simulate streaming for cached responses
            words = cached_response.split()
            for i, word in enumerate(words):
                if i > 0:
                    yield " "
                yield word
                # Small delay to simulate streaming
                await asyncio.sleep(0.02)
            return
        
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Optimized generation config for faster responses
            generation_config = {
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_output_tokens,
                "top_p": settings.gemini_top_p,
                "top_k": settings.gemini_top_k,
            }
            
            safety_settings = None
            full_response = ""
            
            # Generate streaming response
            response_stream = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=True
                ),
                timeout=settings.gemini_request_timeout
            )
            
            # Stream the response chunks
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text
                    # Small delay to prevent overwhelming the frontend
                    await asyncio.sleep(0.01)
            
            # Cache the complete response
            if full_response:
                await self._cache_response(cache_key, full_response)
                    
        except asyncio.TimeoutError:
            self.logger.error("Gemini API request timed out")
            yield "Request timed out. Please try again with a shorter question."
        except Exception as e:
            self.logger.error(f"Error generating streaming response: {e}")
            yield f"Error generating response: {str(e)}"
    
    def _get_cache_key(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate a cache key for the prompt and context"""
        cache_data = {
            "prompt": prompt,
            "context": context or {},
            "model": settings.gemini_model,
            "temperature": settings.gemini_temperature,
            "top_p": settings.gemini_top_p,
            "top_k": settings.gemini_top_k
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        # Try Redis first
        if await redis_cache.is_available():
            cached_response = await redis_cache.get(cache_key)
            if cached_response:
                self.logger.info(f"Redis cache hit for key: {cache_key[:8]}...")
                return cached_response
        
        # Fallback to in-memory cache
        import time
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data["timestamp"] < self._cache_ttl:
                self.logger.info(f"In-memory cache hit for key: {cache_key[:8]}...")
                return cached_data["response"]
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    async def _cache_response(self, cache_key: str, response: str):
        """Cache the response"""
        # Try Redis first
        if await redis_cache.is_available():
            success = await redis_cache.set(cache_key, response, self._cache_ttl)
            if success:
                self.logger.info(f"Redis cached response for key: {cache_key[:8]}...")
                return
        
        # Fallback to in-memory cache
        import time
        self._cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        self.logger.info(f"In-memory cached response for key: {cache_key[:8]}...")
    
    def _build_prompt(self, farmer_question: str, context: Dict[str, Any] = None) -> str:
        """Build a prompt with formatting rules for FarmXpert.

        Notes:
        - For JSON/tooling tasks, we avoid verbose formatting wrappers to reduce token use and parsing failures.
        """

        context = context or {}

        # If the caller expects JSON, keep the wrapper minimal to avoid breaking parsers and wasting tokens.
        wants_json = bool(context.get("format") == "json") or ("format as json" in (farmer_question or "").lower())
        if wants_json:
            return f"""You are FarmXpert, an AI agricultural expert system.

Context (JSON):
{json.dumps(context, ensure_ascii=False)}

Task:
{farmer_question}
"""

        return f"""You are FarmXpert, an AI agricultural expert system.

CRITICAL FORMATTING RULES:
- Use proper line breaks between sections
- Use bullet points (-) for lists
- Each item should be on a new line
- Keep the response short and actionable

Farmer Context:
{json.dumps(context, ensure_ascii=False, indent=2) if context else "No context provided"}

Farmer Question:
{farmer_question}

Provide your response in this EXACT format with proper line breaks:

Direct Answer:
[1-2 short sentences]

Recommendations:
- Recommendation 1
- Recommendation 2
- Recommendation 3

Warnings / Considerations:
- Warning 1
- Warning 2

Next Steps:
- Step 1
- Step 2
"""
    
    async def analyze_soil_data(self, soil_data: Dict[str, Any]) -> str:
        """Analyze soil data using Gemini"""
        prompt = f"""
Analyze this soil data and provide recommendations:
Soil pH: {soil_data.get('ph', 'Unknown')}
Nitrogen (N): {soil_data.get('nitrogen', 'Unknown')} ppm
Phosphorus (P): {soil_data.get('phosphorus', 'Unknown')} ppm
Potassium (K): {soil_data.get('potassium', 'Unknown')} ppm
Organic Matter: {soil_data.get('organic_matter', 'Unknown')}%

Provide analysis in structured plain text format with soil health score, recommendations, suitable crops, and fertilizer needs.
"""
        
        response = await self.generate_response(prompt, {"data_type": "soil_analysis"})
        return response
    
    async def recommend_crops(self, location: str, season: str, soil_data: Dict[str, Any]) -> str:
        """Recommend crops using Gemini"""
        prompt = f"""
Based on the following information, recommend the best crops to plant:

Location: {location}
Season: {season}
Soil Data: {soil_data}

Provide recommendations in structured plain text format with crop suggestions, priorities, expected yields, market analysis, and risk assessment.
"""
        
        response = await self.generate_response(prompt, {"data_type": "crop_recommendation"})
        return response
    
    async def analyze_weather_impact(self, weather_data: Dict[str, Any], crops: List[str]) -> str:
        """Analyze weather impact on crops"""
        prompt = f"""
Analyze the impact of this weather data on the following crops:

Weather Data: {weather_data}
Current Crops: {crops}

Provide analysis in structured plain text format with weather risks, recommended actions, crop vulnerability, and timing recommendations.
"""
        
        response = await self.generate_response(prompt, {"data_type": "weather_analysis"})
        return response
    
    async def optimize_farm_operations(self, farm_data: Dict[str, Any]) -> str:
        """Optimize farm operations"""
        prompt = f"""
Optimize farm operations based on this data:

Farm Size: {farm_data.get('size', 'Unknown')} acres
Current Crops: {farm_data.get('crops', [])}
Available Equipment: {farm_data.get('equipment', [])}
Labor Availability: {farm_data.get('labor', 'Unknown')}
Budget: {farm_data.get('budget', 'Unknown')}

Provide optimization in structured plain text format with task schedules, resource allocation, cost optimization, yield improvement, and risk mitigation.
"""
        
        response = await self.generate_response(prompt, {"data_type": "farm_optimization"})
        return response
    
    async def predict_yield(self, historical_data: Dict[str, Any], current_conditions: Dict[str, Any]) -> str:
        """Predict crop yield"""
        prompt = f"""
Predict crop yield based on:

Historical Data: {historical_data}
Current Conditions: {current_conditions}

Provide prediction in structured plain text format with predicted yield, confidence level, factors affecting yield, improvement recommendations, and risk factors.
"""
        
        response = await self.generate_response(prompt, {"data_type": "yield_prediction"})
        return response
    
    async def analyze_market_trends(self, crop_data: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Analyze market trends"""
        prompt = f"""
Analyze market trends for:

Crops: {crop_data.get('crops', [])}
Market Data: {market_data}

Provide analysis in structured plain text format with price trends, market opportunities, risk assessment, selling recommendations, and alternative markets.
"""
        
        response = await self.generate_response(prompt, {"data_type": "market_analysis"})
        return response
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Gemini"""
        try:
            import json
            # Extract JSON from response if it's wrapped in markdown
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                # Try to find JSON in the response
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
            
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return {
                "error": "Failed to parse response",
                "raw_response": response
            }

# Global instance
gemini_service = GeminiService()
