from __future__ import annotations
from typing import Dict, Any, List, Optional

import json
import os
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.config.settings import settings
from farmxpert.services.tools import SoilSensorTool, AmendmentRecommendationTool, LabTestAnalyzerTool, SoilTool
from farmxpert.services.gemini_service import gemini_service
from farmxpert.repositories.farm_repository import FarmRepository
from sqlalchemy.orm import Session


class SoilHealthAgent(EnhancedBaseAgent):
    name = "soil_health"
    description = "Analyzes soil data and provides recommendations for soil improvement and crop suitability"

    def _get_system_prompt(self) -> str:
        return """You are a Soil Health Agent specializing in comprehensive soil analysis and improvement recommendations.

Your expertise includes:
- Soil sensor data interpretation
- Laboratory test result analysis
- Soil amendment recommendations
- Nutrient management strategies
- Soil health monitoring
- Crop-specific soil requirements

Always provide practical, science-based recommendations with clear implementation steps."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "My soil pH is 5.8, what should I do?",
                "output": "Your soil is acidic (pH 5.8). I recommend applying agricultural lime at 2-3 tons per acre to raise pH to 6.5-7.0. Test soil again after 3-6 months to monitor progress."
            },
            {
                "input": "What amendments do I need for wheat cultivation?",
                "output": "For wheat cultivation, ensure pH 6.0-7.5, adequate phosphorus (15-20 ppm), and nitrogen (40-60 ppm). Apply DAP at planting and split nitrogen applications during growth stages."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle soil health analysis using dynamic tools and comprehensive analysis"""
        try:
            # Get tools from inputs
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")
            session_id = inputs.get("session_id")
            
            # Get soil data from various sources
            soil_data = await self._get_soil_data(context, session_id)
            location = context.get("farm_location", inputs.get("location", "unknown"))
            crop = self._extract_crop_from_query(query) or context.get("crop", "general")
            
            # Initialize data containers
            sensor_data = {}
            amendment_data = {}
            lab_analysis_data = {}
            soil_analysis_data = {}
            
            # Get soil sensor data analysis
            if "soil_sensor" in tools and soil_data:
                try:
                    sensor_data = await tools["soil_sensor"].integrate_sensor_data(soil_data, location)
                except Exception as e:
                    self.logger.warning(f"Failed to get sensor data: {e}")
            
            # Get amendment recommendations
            if "amendment_recommendation" in tools and soil_data:
                try:
                    amendment_data = await tools["amendment_recommendation"].recommend_soil_amendments(
                        soil_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to get amendment recommendations: {e}")
            
            # Get lab test analysis
            if "lab_test_analyzer" in tools and soil_data:
                try:
                    lab_analysis_data = await tools["lab_test_analyzer"].analyze_lab_results(
                        soil_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to get lab analysis: {e}")
            
            # Get comprehensive soil analysis
            if "soil" in tools and soil_data:
                try:
                    soil_analysis_data = await tools["soil"].analyze_soil_with_gemini(soil_data, location)
                except Exception as e:
                    self.logger.warning(f"Failed to get soil analysis: {e}")
            
            # Build comprehensive prompt for Gemini
            prompt = f"""
You are an expert soil health specialist. Based on the following comprehensive analysis, provide detailed soil health recommendations for the farmer.

Farmer's Query: "{query}"

Analysis Results:
- Location: {location}
- Crop: {crop}
- Soil Data: {json.dumps(soil_data, indent=2)}
- Sensor Analysis: {sensor_data.get('health_assessment', {})}
- Amendment Recommendations: {amendment_data.get('lime_recommendations', {})}
- Lab Analysis: {lab_analysis_data.get('health_score', {})}
- Soil Analysis: {soil_analysis_data.get('soil_health_score', {})}

Provide comprehensive soil health recommendations including:
1. Overall soil health assessment
2. Immediate action items
3. Long-term improvement strategies
4. Amendment application schedule
5. Monitoring and testing recommendations
6. Expected improvements and timeline
7. Cost considerations
8. Risk factors and mitigation

Format your response as a natural conversation with the farmer.
"""

            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "soil_health_analysis"})

            # If LLM quota/rate limit is hit, fall back to deterministic output
            resp_lower = (response or "").lower()
            if "429" in resp_lower or "quota" in resp_lower or "rate limit" in resp_lower:
                return await self._handle_traditional(inputs)
            
            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "soil_data": soil_data,
                    "location": location,
                    "crop": crop,
                    "sensor_data": sensor_data,
                    "amendment_data": amendment_data,
                    "lab_analysis_data": lab_analysis_data,
                    "soil_analysis_data": soil_analysis_data
                },
                "recommendations": self._extract_recommendations_from_data(amendment_data, soil_analysis_data),
                "warnings": self._extract_warnings_from_data(sensor_data, lab_analysis_data),
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
            
        except Exception as e:
            self.logger.error(f"Error in soil health agent: {e}")
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback traditional soil health analysis method"""
        context = inputs.get("context", {})
        session_id = inputs.get("session_id")
        soil_data = await self._get_soil_data(context, session_id)

        insights: List[str] = []
        recommendations: List[str] = []
        warnings: List[str] = []

        ph = soil_data.get("ph")
        if ph is not None:
            if ph < 6.0:
                insights.append("Soil is acidic")
                recommendations.append("Apply agricultural lime to raise pH towards 6.5–7.0")
            elif ph > 7.5:
                insights.append("Soil is alkaline")
                recommendations.append("Apply elemental sulfur/acidifying amendments to lower pH towards neutral")
            else:
                insights.append("Soil pH is near optimal for most field crops")

        npk = soil_data.get("npk") or {}
        if isinstance(npk, dict):
            if npk.get("nitrogen", 0) < 0.3:
                recommendations.append("Increase nitrogen via split urea applications or organic manures")
            if npk.get("phosphorus", 0) < 0.3:
                recommendations.append("Incorporate phosphorus sources (DAP/SSP) based on soil test rate")
            if npk.get("potassium", 0) < 0.3:
                recommendations.append("Apply muriate of potash where K is low")

        organic = soil_data.get("organic_content") or soil_data.get("organic_matter")
        if organic is not None and organic < 2.0:
            recommendations.append("Add compost/FYM and consider cover crops to lift organic matter >2%")

        moisture = soil_data.get("moisture")
        if moisture is not None and moisture < 15:
            warnings.append("Low soil moisture; plan irrigation or mulch to conserve water")

        return {
            "agent": self.name,
            "success": True,
            "response": {
                "summary": "Soil health assessment completed",
                "insights": insights,
                "recommendations": recommendations,
                "warnings": warnings
            },
            "data": {"soil": soil_data},
            "metadata": {"source": "traditional"}
        }
    
    async def _get_soil_data(self, context: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
        """Get soil data from various sources"""
        soil_data = context.get("farm_data", {}).get("soil", {}) or context.get("soil_data", {})

        # Optional static JSON fallback: {static_data_dir}/soil/{session_id}.json or {user_id}.json
        if not soil_data:
            static_dir = os.path.join(settings.static_data_dir, "soil")
            candidates = []
            if session_id:
                candidates.append(os.path.join(static_dir, f"{session_id}.json"))
            user_id = context.get("user_id")
            if user_id:
                candidates.append(os.path.join(static_dir, f"{user_id}.json"))
            for path in candidates:
                try:
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            payload = json.load(f)
                            soil_data = (payload.get("soil_data") or payload.get("soil") or {})
                            if soil_data:
                                break
                except Exception:
                    pass
        
        # Default soil data if none provided
        if not soil_data:
            soil_data = {
                "ph": 7.0,
                "npk": {"nitrogen": 45, "phosphorus": 25, "potassium": 30},
                "organic_matter": 2.0,
                "moisture": 20
            }
        
        return soil_data
    
    def _extract_crop_from_query(self, query: str) -> Optional[str]:
        """Extract mentioned crop from user query"""
        query_lower = query.lower()
        crops = ["wheat", "rice", "maize", "cotton", "sugarcane", "groundnut", "soybean", 
                "barley", "mustard", "chickpea", "lentil", "potato", "onion", "tomato"]
        
        for crop in crops:
            if crop in query_lower:
                return crop
        return None
    
    def _extract_recommendations_from_data(self, amendment_data: Dict[str, Any], soil_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis data"""
        recommendations = []
        
        if isinstance(amendment_data, dict):
            if "lime_recommendations" in amendment_data:
                recommendations.append("Lime application recommended for pH adjustment")
            if "organic_additions" in amendment_data:
                recommendations.append("Organic matter additions needed")
            if "compost_requirements" in amendment_data:
                recommendations.append("Compost application required")
        
        if isinstance(soil_analysis_data, dict):
            if "fertilizer_recommendations" in soil_analysis_data:
                recommendations.append("Fertilizer application schedule provided")
            if "soil_improvements" in soil_analysis_data:
                recommendations.append("Soil improvement strategies available")
        
        return recommendations
    
    def _extract_warnings_from_data(self, sensor_data: Dict[str, Any], lab_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from analysis data"""
        warnings = []
        
        if isinstance(sensor_data, dict):
            if "immediate_actions" in sensor_data:
                actions = sensor_data["immediate_actions"]
                if isinstance(actions, list) and actions:
                    warnings.append(f"Immediate actions needed: {', '.join(actions[:2])}")
        
        if isinstance(lab_analysis_data, dict):
            if "deficiency_analysis" in lab_analysis_data:
                deficiencies = lab_analysis_data["deficiency_analysis"]
                if isinstance(deficiencies, list) and deficiencies:
                    warnings.append(f"Nutrient deficiencies detected: {', '.join(deficiencies[:2])}")
        
        return warnings
    
    def _generate_long_term_recommendations(self, soil_data: Dict[str, Any], trend_data: List[Dict[str, Any]]) -> List[str]:
        """Generate long-term soil improvement recommendations"""
        recommendations = []
        
        # Analyze pH trends
        if soil_data.get('ph', 0) < 6.0:
            recommendations.append("Consider lime application to raise soil pH")
        elif soil_data.get('ph', 0) > 7.5:
            recommendations.append("Consider sulfur application to lower soil pH")
        
        # Analyze organic matter
        if soil_data.get('organic_matter', 0) < 2.0:
            recommendations.append("Increase organic matter through cover crops and compost")
        
        # Analyze nutrient trends
        if trend_data and len(trend_data) > 1:
            recent = trend_data[0]
            older = trend_data[-1]
            
            if recent.get('nitrogen', 0) < older.get('nitrogen', 0):
                recommendations.append("Nitrogen levels declining - review fertilization strategy")
            
            if recent.get('phosphorus', 0) < older.get('phosphorus', 0):
                recommendations.append("Phosphorus levels declining - consider phosphate application")
        
        return recommendations
    
    def _generate_crop_specific_advice(self, soil_data: Dict[str, Any], current_crops: List[str]) -> Dict[str, List[str]]:
        """Generate crop-specific soil advice"""
        crop_advice = {}
        
        for crop in current_crops:
            advice = []
            
            # pH requirements
            ph = soil_data.get('ph', 0)
            if crop.lower() in ['corn', 'wheat', 'soybeans'] and ph < 6.0:
                advice.append(f"{crop} prefers slightly acidic soil - current pH may be too low")
            elif crop.lower() in ['alfalfa', 'clover'] and ph < 6.5:
                advice.append(f"{crop} requires neutral to alkaline soil - current pH may be too low")
            
            # Nitrogen requirements
            nitrogen = soil_data.get('nitrogen', 0)
            if crop.lower() in ['corn', 'wheat'] and nitrogen < 20:
                advice.append(f"{crop} is a heavy nitrogen feeder - consider additional nitrogen application")
            
            # Phosphorus requirements
            phosphorus = soil_data.get('phosphorus', 0)
            if crop.lower() in ['corn', 'soybeans'] and phosphorus < 15:
                advice.append(f"{crop} benefits from adequate phosphorus - consider phosphate application")
            
            if advice:
                crop_advice[crop] = advice
        
        return crop_advice
