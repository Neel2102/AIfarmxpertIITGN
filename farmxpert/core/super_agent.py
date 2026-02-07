"""
Super Agent for FarmXpert
Orchestrates all agents and provides unified interface for user queries
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
import re
from farmxpert.core.utils.logger import get_logger
from farmxpert.core.base_agent.agent_registry import AgentRegistry
from farmxpert.config.settings import settings
from farmxpert.services.gemini_service import gemini_service
from farmxpert.services.tools import SoilTool, WeatherTool, MarketTool, CropTool, FertilizerTool, PestDiseaseTool, IrrigationTool, WebScrapingTool, ClimatePredictionTool, MarketAnalysisTool, GeneticDatabaseTool, SoilSuitabilityTool, YieldPredictionTool, SoilSensorTool, AmendmentRecommendationTool, LabTestAnalyzerTool, FertilizerDatabaseTool, WeatherForecastTool, PlantGrowthSimulationTool, EvapotranspirationModelTool, IoTSoilMoistureTool, WeatherAPITool, ImageRecognitionTool, VoiceToTextTool, DiseasePredictionTool, WeatherMonitoringTool, AlertSystemTool, SatelliteImageProcessingTool, DroneImageProcessingTool, GrowthStagePredictionTool, TaskPrioritizationTool, RealTimeTrackingTool, MaintenanceTrackerTool, PredictiveMaintenanceTool, FieldMappingTool, YieldModelTool, ProfitOptimizationTool, MarketIntelligenceTool, LogisticsTool, ProcurementTool, InsuranceRiskTool, FarmerCoachTool, ComplianceCertificationTool, CommunityEngagementTool, CarbonSustainabilityTool
from farmxpert.core.super_agent_nl_formatter import format_response_as_natural_language, create_simple_greeting_response, is_simple_query

@dataclass
class AgentResponse:
    """Response from an individual agent"""
    agent_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class SuperAgentResponse:
    """Final response from SuperAgent"""
    query: str
    success: bool
    response: Dict[str, Any]
    natural_language: str = ""  # Clean natural language response for UI
    agent_responses: List[AgentResponse] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    session_id: Optional[str] = None


class SuperAgent:
    """
    Super Agent that orchestrates all FarmXpert agents
    Uses Gemini to determine which agents to call and synthesizes responses
    """
    
    def __init__(self):
        self.logger = get_logger("super_agent")
        self.agent_registry = AgentRegistry()
        self.available_agents = self._get_available_agents()
        self.tools = {
            "soil": SoilTool(),
            "weather": WeatherTool(),
            "market": MarketTool(),
            "crop": CropTool(),
            "fertilizer": FertilizerTool(),
            "pest_disease": PestDiseaseTool(),
            "irrigation": IrrigationTool(),
            "web_scraping": WebScrapingTool(),
            "climate_prediction": ClimatePredictionTool(),
            "market_analysis": MarketAnalysisTool(),
            "genetic_database": GeneticDatabaseTool(),
            "soil_suitability": SoilSuitabilityTool(),
            "yield_prediction": YieldPredictionTool(),
            "soil_sensor": SoilSensorTool(),
            "amendment_recommendation": AmendmentRecommendationTool(),
            "lab_test_analyzer": LabTestAnalyzerTool(),
            "fertilizer_database": FertilizerDatabaseTool(),
            "weather_forecast": WeatherForecastTool(),
            "plant_growth_simulation": PlantGrowthSimulationTool(),
            "evapotranspiration_model": EvapotranspirationModelTool(),
            "iot_soil_moisture": IoTSoilMoistureTool(),
            "weather_api": WeatherAPITool(),
            "image_recognition": ImageRecognitionTool(),
            "voice_to_text": VoiceToTextTool(),
            "disease_prediction": DiseasePredictionTool(),
            "weather_monitoring": WeatherMonitoringTool(),
            "alert_system": AlertSystemTool(),
            "satellite_image_processing": SatelliteImageProcessingTool(),
            "drone_image_processing": DroneImageProcessingTool(),
            "growth_stage_prediction": GrowthStagePredictionTool(),
            "task_prioritization": TaskPrioritizationTool(),
            "real_time_tracking": RealTimeTrackingTool(),
            "maintenance_tracker": MaintenanceTrackerTool(),
            "predictive_maintenance": PredictiveMaintenanceTool(),
            "field_mapping": FieldMappingTool(),
            "yield_model": YieldModelTool(),
            "profit_optimization": ProfitOptimizationTool(),
            "market_intelligence": MarketIntelligenceTool(),
            "logistics": LogisticsTool(),
            "procurement": ProcurementTool(),
            "insurance_risk": InsuranceRiskTool(),
            "farmer_coach": FarmerCoachTool(),
            "compliance_cert": ComplianceCertificationTool(),
            "community": CommunityEngagementTool(),
            "carbon_sustainability": CarbonSustainabilityTool()
        }

    def _safe_list(self, items: List[str], max_items: int = 5) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items or []:
            if not item or not isinstance(item, str):
                continue
            if item in seen:
                continue
            if item not in self.available_agents:
                continue
            seen.add(item)
            out.append(item)
            if len(out) >= max_items:
                break
        return out

    def _get_strategy_from_context(self, context: Optional[Dict[str, Any]]) -> Optional[str]:
        if not context or not isinstance(context, dict):
            return None
        strategy = context.get("strategy")
        if not strategy and isinstance(context.get("routing"), dict):
            strategy = context["routing"].get("strategy")
        if not strategy:
            return None
        return str(strategy).strip().lower()

    def _select_agents_by_strategy(self, context: Optional[Dict[str, Any]]) -> Optional[List[str]]:
        strategy = self._get_strategy_from_context(context)
        if not strategy:
            return None
        mapping = {
            "weather": ["weather_watcher"],
            "weather_only": ["weather_watcher"],
            "growth": ["growth_stage_monitor"],
            "growth_only": ["growth_stage_monitor"],
            "irrigation": ["irrigation_planner"],
            "irrigation_only": ["irrigation_planner"],
            "fertilizer": ["fertilizer_advisor"],
            "fertilizer_only": ["fertilizer_advisor"],
            "soil": ["soil_health"],
            "soil_health": ["soil_health"],
            "soil_health_only": ["soil_health"],
            "market": ["market_intelligence"],
            "market_only": ["market_intelligence"],
            "tasks": ["task_scheduler"],
            "task_scheduler": ["task_scheduler"],
            "task_scheduling": ["task_scheduler"],
            "both": ["weather_watcher", "growth_stage_monitor"],
            "comprehensive": ["weather_watcher", "soil_health", "irrigation_planner", "fertilizer_advisor", "market_intelligence", "task_scheduler"],
            "comprehensive_analysis": ["weather_watcher", "soil_health", "irrigation_planner", "fertilizer_advisor", "market_intelligence", "task_scheduler"],
            "auto": None,
        }
        selected = mapping.get(strategy)
        if selected is None:
            return None
        return self._safe_list(selected)

    def _select_agents_by_payload(self, context: Optional[Dict[str, Any]]) -> Optional[List[str]]:
        if not context or not isinstance(context, dict):
            return None
        location = context.get("location") or {}
        crop = context.get("crop") or context.get("crop_data") or {}
        has_location = isinstance(location, dict) and (
            bool(location.get("latitude") and location.get("longitude"))
            or bool(location.get("lat") and location.get("lon"))
        )
        has_crop = bool(crop)
        if has_location and has_crop:
            return self._safe_list(["weather_watcher", "growth_stage_monitor", "irrigation_planner", "fertilizer_advisor", "soil_health"])
        if has_location:
            return self._safe_list(["weather_watcher"])
        if has_crop:
            return self._safe_list(["growth_stage_monitor", "soil_health"])
        return None

    def _select_agents_by_keywords(self, query: str) -> Optional[List[str]]:
        q = (query or "").lower()
        if not q:
            return None

        def has_any(keywords: List[str]) -> bool:
            return any(re.search(r"\b" + re.escape(k) + r"\b", q) for k in keywords)

        wants_seeds = has_any([
            "seed", "seeds", "variety", "varieties", "hybrid", "gmo"
        ])
        wants_crop_planning = has_any([
            "crop", "crops", "plant", "sow", "kharif", "rabi", "season"
        ])
        wants_weather = has_any([
             "weather", "rain", "rainfall", "temperature", "forecast", "humidity", "wind", "storm", "drought"
         ])
        wants_growth = has_any([
            "growth", "stage", "seedling", "vegetative", "flowering", "maturity", "harvest", "crop health", "plant health"
         ])
        wants_irrigation = has_any([
            "irrigation", "irrigate", "watering", "drip", "sprinkler", "pump"
        ])
        wants_fertilizer = has_any([
            "fertilizer", "nutrient", "npk", "urea", "dap", "mop", "compost", "manure"
        ])
        wants_soil = has_any([
            "soil", "ph", "salinity", "organic matter", "soil test"
        ])
        wants_pest = has_any([
            "pest", "disease", "fungus", "blight", "leaf spot", "insect", "spots", "yellow", "yellowing", "wilting", "curl", "mosaic", "rot"
         ])
        wants_market = has_any([
            "market", "price", "sell", "mandi", "apmc", "profit", "revenue"
        ])
        wants_tasks = has_any([
            "task", "schedule", "plan", "today", "tomorrow", "weekly", "daily", "reminder"
        ])
        wants_insurance = has_any([
            "insurance", "risk", "claim"
        ])

        selected: List[str] = []
        if wants_crop_planning:
            selected.append("crop_selector")
        if wants_seeds:
             selected.append("seed_selection")
        if wants_weather:
            selected.append("weather_watcher")
        if wants_growth:
            selected.append("growth_stage_monitor")
        if wants_irrigation:
            selected.append("irrigation_planner")
        if wants_fertilizer:
            selected.append("fertilizer_advisor")
        if wants_soil:
            selected.append("soil_health")
        if wants_pest:
            selected.append("pest_disease_diagnostic")
        if wants_market:
            selected.append("market_intelligence")
        if wants_tasks:
            selected.append("task_scheduler")
        if wants_insurance:
            selected.append("crop_insurance_risk")

        selected = self._safe_list(selected)
        return selected or None

    async def _select_agents(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        strategy_selected = self._select_agents_by_strategy(context)
        if strategy_selected:
            return strategy_selected

        keyword_selected = self._select_agents_by_keywords(query)
        if keyword_selected:
            return keyword_selected

        payload_selected = self._select_agents_by_payload(context)
        if payload_selected:
            return payload_selected

        gemini_selected = await self._select_agents_with_gemini(query, context)
        gemini_selected = self._safe_list(gemini_selected)
        if gemini_selected:
            return gemini_selected

        return self._safe_list(["crop_selector", "farmer_coach"], max_items=2)

    def _get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available agents"""
        agents_info = {}
        
        # Crop Planning Agents
        agents_info.update({
            "crop_selector": {
                "name": "Crop Selector Agent",
                "description": "Helps select the best crops based on soil, weather, and market conditions",
                "category": "crop_planning",
                "tools": ["soil", "weather", "market", "crop", "web_scraping", "climate_prediction", "market_analysis"]
            },
            "seed_selection": {
                "name": "Seed Selection Agent", 
                "description": "Recommends the best seeds and varieties for selected crops",
                "category": "crop_planning",
                "tools": ["market", "genetic_database", "soil_suitability", "yield_prediction"]
            },
            "soil_health": {
                "name": "Soil Health Agent",
                "description": "Analyzes soil conditions and provides health recommendations",
                "category": "crop_planning", 
                "tools": ["soil", "crop", "soil_sensor", "amendment_recommendation", "lab_test_analyzer"]
            },
            "fertilizer_advisor": {
                "name": "Fertilizer Advisor Agent",
                "description": "Provides fertilizer recommendations based on soil analysis",
                "category": "crop_planning",
                "tools": ["soil", "fertilizer", "crop", "fertilizer_database", "weather_forecast", "plant_growth_simulation"]
            },
            "irrigation_planner": {
                "name": "Irrigation Planner Agent",
                "description": "Plans irrigation schedules based on weather and crop needs",
                "category": "crop_planning",
                "tools": ["weather", "irrigation", "crop", "evapotranspiration_model", "iot_soil_moisture", "weather_api"]
            },
            "pest_disease_diagnostic": {
                "name": "Pest & Disease Diagnostic Agent",
                "description": "Diagnoses pest and disease issues and provides treatment plans",
                "category": "crop_planning",
                "tools": ["pest_disease", "crop", "image_recognition", "voice_to_text", "disease_prediction"]
            },
            "weather_watcher": {
                "name": "Weather Watcher Agent",
                "description": "Monitors weather conditions and provides forecasts",
                "category": "crop_planning",
                "tools": ["weather", "crop", "weather_monitoring", "alert_system"]
            },
            "growth_stage_monitor": {
                "name": "Growth Stage Monitor Agent",
                "description": "Tracks crop growth stages and provides care recommendations",
                "category": "crop_planning",
                "tools": ["crop", "satellite_image_processing", "drone_image_processing", "growth_stage_prediction"]
            }
        })
        
        # Farm Operations Agents
        agents_info.update({
            "task_scheduler": {
                "name": "Task Scheduler Agent",
                "description": "Schedules farm tasks and operations efficiently",
                "category": "farm_operations",
                "tools": ["task_prioritization", "real_time_tracking", "weather_api"]
            },
            "machinery_equipment": {
                "name": "Machinery & Equipment Agent",
                "description": "Manages machinery and equipment recommendations",
                "category": "farm_operations",
                "tools": ["maintenance_tracker", "predictive_maintenance"]
            },
            "farm_layout_mapping": {
                "name": "Farm Layout Mapping Agent",
                "description": "Helps design and optimize farm layout",
                "category": "farm_operations",
                "tools": ["field_mapping"]
            }
        })
        
        # Analytics Agents
        agents_info.update({
            "yield_predictor": {
                "name": "Yield Predictor Agent",
                "description": "Predicts crop yields based on various factors",
                "category": "analytics",
                "tools": ["yield_model", "weather", "crop", "soil"]
            },
            "profit_optimization": {
                "name": "Profit Optimization Agent",
                "description": "Optimizes farm profitability through various strategies",
                "category": "analytics",
                "tools": ["profit_optimization", "market", "crop"]
            },
            "carbon_sustainability": {
                "name": "Carbon Sustainability Agent",
                "description": "Helps with carbon footprint and sustainability practices",
                "category": "analytics",
                "tools": ["carbon_sustainability"]
            }
        })
        
        # Supply Chain Agents
        agents_info.update({
            "market_intelligence": {
                "name": "Market Intelligence Agent",
                "description": "Provides market insights and price trends",
                "category": "supply_chain",
                "tools": ["market", "crop", "market_intelligence"]
            },
            "logistics_storage": {
                "name": "Logistics & Storage Agent",
                "description": "Manages logistics and storage recommendations",
                "category": "supply_chain",
                "tools": ["logistics", "market", "weather"]
            },
            "input_procurement": {
                "name": "Input Procurement Agent",
                "description": "Helps with procurement of farm inputs",
                "category": "supply_chain",
                "tools": ["procurement", "market"]
            },
            "crop_insurance_risk": {
                "name": "Crop Insurance & Risk Agent",
                "description": "Provides risk assessment and insurance recommendations",
                "category": "supply_chain",
                "tools": ["insurance_risk", "weather", "market"]
            }
        })
        
        # Support Agents
        agents_info.update({
            "farmer_coach": {
                "name": "Farmer Coach Agent",
                "description": "Provides coaching and educational support to farmers",
                "category": "support",
                "tools": ["farmer_coach"]
            },
            "compliance_certification": {
                "name": "Compliance & Certification Agent",
                "description": "Helps with regulatory compliance and certifications",
                "category": "support",
                "tools": ["compliance_cert"]
            },
            "community_engagement": {
                "name": "Community Engagement Agent",
                "description": "Facilitates community engagement and knowledge sharing",
                "category": "support",
                "tools": ["community"]
            }
        })
        
        return agents_info
    
    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> SuperAgentResponse:
        """
        Main method to process user queries
        Uses Gemini to determine which agents to call and synthesizes responses
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(
                "Processing query",
                extra={
                    "query_preview": query[:100],
                    "session_id": session_id,
                    "context_keys": list(context.keys()) if context else [],
                    "timestamp": start_time.isoformat()
                }
            )
            
            # Handle simple greetings/small talk intelligently
            greeting_response = create_simple_greeting_response(query)
            if greeting_response:
                execution_time = (datetime.now() - start_time).total_seconds()
                return SuperAgentResponse(
                    query=query,
                    success=True,
                    response={"answer": greeting_response},
                    natural_language=greeting_response,
                    agent_responses=[],
                    execution_time=execution_time,
                    session_id=session_id
                )
            
            
            # Step 1: Determine which agents to call (hybrid rules + Gemini fallback)
            self.logger.debug("Starting agent selection")
            agent_selection = await self._select_agents(query, context)
            self.logger.info(
                "Agent selection completed",
                extra={
                    "selected_agents": agent_selection,
                    "agent_count": len(agent_selection)
                }
            )
            
            # Step 2: Execute selected agents
            self.logger.debug("Starting agent execution")
            agent_responses = await self._execute_agents(agent_selection, query, context)
            
            # Log agent execution results
            successful_agents = [r.agent_name for r in agent_responses if r.success]
            failed_agents = [r.agent_name for r in agent_responses if not r.success]
            
            self.logger.info(
                "Agent execution completed",
                extra={
                    "successful_agents": successful_agents,
                    "failed_agents": failed_agents,
                    "total_execution_time": sum(r.execution_time for r in agent_responses)
                }
            )
            
            # Step 3: Synthesize final response
            self.logger.debug("Starting response synthesis")
            final_response: Dict[str, Any] = await self._synthesize_response(query, agent_responses, context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                "Query processing completed successfully",
                extra={
                    "total_execution_time": execution_time,
                    "response_size": len(json.dumps(final_response, ensure_ascii=False)) if isinstance(final_response, dict) else len(str(final_response)),
                    "agents_used": len(agent_responses)
                }
            )
            
            # Format as natural language
            agent_names = [r.agent_name for r in agent_responses if r.success]
            natural_language = format_response_as_natural_language(
                query=query,
                response_data=final_response,
                agent_names=agent_names,
                context=context
            )
            
            return SuperAgentResponse(
                query=query,
                success=True,
                response=final_response,
                natural_language=natural_language,
                agent_responses=agent_responses,
                execution_time=execution_time,
                session_id=session_id
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(
                "Error processing query",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": execution_time,
                    "query_preview": query[:100]
                },
                exc_info=True
            )
            
            error_message = f"I apologize, but I encountered an error while processing your query: {str(e)}"
            
            return SuperAgentResponse(
                query=query,
                success=False,
                response={"answer": error_message},
                natural_language=error_message,
                execution_time=execution_time,
                session_id=session_id
            )
    
    async def _select_agents_with_gemini(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Use Gemini to determine which agents should handle the query
        """
        # Create agent information for Gemini
        agents_info_text = self._format_agents_for_gemini()
        
        prompt = f"""
You are an AI coordinator for FarmXpert, an agricultural expert system. Your job is to analyze a farmer's query and determine which specialized agents should handle it.

Available Agents:
{agents_info_text}

Farmer's Query: "{query}"

Context: {context or "No additional context provided"}

Based on the query, select the most relevant agents (1-5 agents maximum) that should be called to provide a comprehensive answer. Consider:
1. The main topic/domain of the query
2. What information the farmer needs
3. Which agents can provide the most relevant expertise
4. Agent dependencies (some agents work better together)

Respond with a JSON array of agent names (use the exact agent keys from the list above):
["agent1", "agent2", "agent3"]

Only include agents that are directly relevant to answering the query. If the query is very specific, you might only need 1-2 agents. If it's complex, you might need 3-5 agents.

IMPORTANT: If a query is about a specific sub-domain like 'seeds', 'irrigation', 'pests', or 'fertilizer', MUST select the corresponding specialized agent (e.g., 'seed_selection', 'irrigation_planner', 'pest_disease_diagnostic') instead of the general 'crop_selector'.
"""
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "agent_selection"})
            
            # Parse the JSON response
            self.logger.info(f"Gemini routing response: {response}")
            agent_list = self._parse_agent_selection(response)
            self.logger.info(f"Parsed agent list: {agent_list}")
            
            # Validate that selected agents exist
            valid_agents = [agent for agent in agent_list if agent in self.available_agents]
            
            if not valid_agents:
                # Fallback to a default set of agents
                valid_agents = ["crop_selector", "farmer_coach"]
            
            self.logger.info(f"Selected agents: {valid_agents}")
            return valid_agents
            
        except Exception as e:
            self.logger.error(f"Error in agent selection: {e}")
            # Fallback to default agents
            return ["crop_selector", "farmer_coach"]
    
    def _format_agents_for_gemini(self) -> str:
        """Format agent information for Gemini prompt"""
        formatted_agents = []
        
        for agent_key, agent_info in self.available_agents.items():
            tools_str = ", ".join(agent_info.get("tools", [])) if agent_info.get("tools") else "None"
            formatted_agents.append(
                f"- {agent_key}: {agent_info['name']} - {agent_info['description']} (Tools: {tools_str})"
            )
        
        return "\n".join(formatted_agents)
    
    def _parse_agent_selection(self, response: str) -> List[str]:
        """Parse agent selection from Gemini response"""
        try:
            # Try to extract JSON from the response
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                # Try to find JSON array in the response
                start = response.find('[')
                end = response.rfind(']') + 1
                json_str = response[start:end]
            
            agent_list = json.loads(json_str)
            
            if isinstance(agent_list, list):
                return agent_list
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error parsing agent selection: {e}")
            return []
    
    async def _execute_agents(
        self, 
        agent_names: List[str], 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Execute the selected agents and collect their responses
        """
        agent_responses = []
        
        # Execute agents in parallel for better performance
        tasks = []
        for agent_name in agent_names:
            task = asyncio.create_task(self._execute_single_agent(agent_name, query, context))
            tasks.append(task)
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_responses.append(AgentResponse(
                    agent_name=agent_names[i],
                    success=False,
                    data={},
                    error=str(result)
                ))
            else:
                agent_responses.append(result)
        
        return agent_responses
    
    async def _execute_single_agent(
        self, 
        agent_name: str, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute a single agent with tools and context
        """
        start_time = datetime.now()
        
        try:
            self.logger.debug(f"Executing agent: {agent_name}")
            
            # Create agent instance from registry
            agent = self.agent_registry.create_agent(agent_name)
            
            # Prepare inputs with tools and context
            agent_tools = self._get_agent_tools(agent_name)
            inputs = {
                "query": query,
                "context": context or {},
                "tools": agent_tools,
                "session_id": context.get("session_id") if context else None
            }
            
            self.logger.debug(
                f"Agent {agent_name} inputs prepared",
                extra={
                    "tools_available": list(agent_tools.keys()),
                    "context_keys": list(context.keys()) if context else []
                }
            )
            
            # Execute the agent with timeout
            try:
                result = await asyncio.wait_for(agent.handle(inputs), timeout=30.0)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Agent {agent_name} execution timed out after 30 seconds")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"Agent {agent_name} executed successfully",
                extra={
                    "execution_time": execution_time,
                    "result_keys": list(result.keys()) if isinstance(result, dict) else "non_dict_result"
                }
            )
            
            return AgentResponse(
                agent_name=agent_name,
                success=True,
                data=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(
                f"Error executing agent {agent_name}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": execution_time
                },
                exc_info=True
            )
            
            return AgentResponse(
                agent_name=agent_name,
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
    
    def _get_agent_tools(self, agent_name: str) -> Dict[str, Any]:
        """Get tools available to a specific agent"""
        agent_info = self.available_agents.get(agent_name, {})
        agent_tools = agent_info.get("tools", [])
        
        available_tools = {}
        for tool_name in agent_tools:
            if tool_name in self.tools:
                available_tools[tool_name] = self.tools[tool_name]
        
        return available_tools
    
    async def _synthesize_response(
        self, 
        query: str, 
        agent_responses: List[AgentResponse], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize a comprehensive response from multiple agent responses
        """
        # Low-LLM mode: deterministic SOP assembly to reduce quota usage and avoid long, random outputs.
        if getattr(settings, "low_llm_mode", False):
            return self._build_sop_from_agents(query, agent_responses)

        # Prepare agent responses for Gemini
        responses_text = self._format_agent_responses_for_synthesis(agent_responses)
        
        # SOP concise JSON schema
        sop_schema = {
            "answer": "string (one or two sentences, concise)",
            "recommendations": ["up to 3 bullet points"],
            "warnings": ["0-2 short items"],
            "next_steps": ["1-3 concrete actions"],
            "meta": {"agents_used": "list", "confidence": "0.0-1.0"}
        }

        # Determine language for response
        locale = context.get('locale', 'en-IN') if context else 'en-IN'
        language_instruction = ""
        if locale and locale.lower() not in ('en', 'en-us', 'en-in', 'none'):
             language_instruction = f"- IMPORTANT: Translate the 'answer', 'recommendations', 'warnings', and 'next_steps' into the language for locale '{locale}'."

        prompt = f"""
You are FarmXpert SuperAgent, an expert agricultural advisor. Synthesize a comprehensive, natural language response.

Original Query: "{query}"

Agent Responses (data from specialized farming agents):
{responses_text}

Generate a detailed, conversational response like a ChatGPT would - informative, helpful, and natural.

Output STRICTLY a single JSON object with this structure:
{sop_schema}

Rules:
- The 'answer' field MUST be a detailed, paragraph-form response (3-5 sentences minimum) that:
  * Directly addresses the user's query conversationally
  * Synthesizes insights from all agent responses
  * Provides specific, actionable information
  * Sounds natural and helpful, like talking to an expert farmer advisor
  * Do NOT use generic phrases like "Here's the recommended action plan based on your inputs"
- 'recommendations' should be specific, actionable tips (not generic placeholders)
- 'warnings' should be relevant alerts if any issues were detected
- 'next_steps' should be concrete actions the farmer can take
- Use meta.agents_used as the list of agent keys; meta.confidence as a number (0.0-1.0)
{language_instruction}
"""
        
        try:
            response = await gemini_service.generate_response(
                prompt,
                {"task": "response_synthesis", "format": "json", "concise": True}
            )
            parsed = gemini_service._parse_json_response(response)
            if isinstance(parsed, dict) and parsed.get("answer"):
                return parsed
            return self._build_sop_from_agents(query, agent_responses)
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {e}")
            return self._build_sop_from_agents(query, agent_responses)

    def _build_sop_from_agents(self, query: str, agent_responses: List[AgentResponse]) -> Dict[str, Any]:
        agents_used = [r.agent_name for r in agent_responses if r.success]

        recommendations: List[str] = []
        warnings: List[str] = []
        next_steps: List[str] = []

        def add_list(dst: List[str], items: Any, limit: int):
            if len(dst) >= limit:
                return
            if isinstance(items, str) and items.strip():
                dst.append(items.strip())
                return
            if isinstance(items, list):
                for x in items:
                    if len(dst) >= limit:
                        break
                    if isinstance(x, dict):
                        dst.append(json.dumps(x, ensure_ascii=False))
                    elif x is not None:
                        s = str(x).strip()
                        if s:
                            dst.append(s)

        for r in agent_responses:
            if not (r.success and isinstance(r.data, dict)):
                continue
            add_list(recommendations, r.data.get("recommendations"), 3)
            add_list(warnings, r.data.get("warnings"), 2)
            add_list(next_steps, r.data.get("next_steps"), 3)

        if not next_steps:
            next_steps = ["Share location + crop + growth stage for more precise advice."]

        answer: str = ""
        if agents_used:
            for r in agent_responses:
                if not (r.success and isinstance(r.data, dict)):
                    continue
                candidate = r.data.get("response")
                if isinstance(candidate, str) and candidate.strip():
                    answer = candidate.strip()
                    break
            if not answer:
                answer = "Response ready."
        else:
            answer = "Please provide crop and location details for a precise recommendation."

        if not recommendations:
            recommendations = ["Provide crop name and current growth stage."]

        return {
            "answer": answer,
            "recommendations": recommendations[:3],
            "warnings": warnings[:2],
            "next_steps": next_steps[:3],
            "meta": {
                "agents_used": agents_used,
                "confidence": 0.6 if agents_used else 0.4,
            },
        }
    
    def _format_agent_responses_for_synthesis(self, agent_responses: List[AgentResponse]) -> str:
        """Format agent responses for synthesis prompt"""
        formatted_responses = []
        
        for response in agent_responses:
            if response.success:
                agent_info = self.available_agents.get(response.agent_name, {})
                agent_name = agent_info.get("name", response.agent_name)
                
                formatted_responses.append(
                    f"**{agent_name}:**\n"
                    f"Response: {json.dumps(response.data, indent=2)}\n"
                    f"Execution Time: {response.execution_time:.2f}s\n"
                )
            else:
                formatted_responses.append(
                    f"**{response.agent_name}:**\n"
                    f"Error: {response.error}\n"
                )
        
        return "\n".join(formatted_responses)
    
    def _fallback_response_synthesis(self, agent_responses: List[AgentResponse]) -> str:
        """Fallback response synthesis when Gemini fails"""
        successful_responses = [r for r in agent_responses if r.success]
        
        if not successful_responses:
            return "I apologize, but I encountered issues while processing your query. Please try rephrasing your question or contact support for assistance."
        
        response_parts = []
        response_parts.append("Based on the analysis from our agricultural experts, here's what I found:\n")
        
        for response in successful_responses:
            agent_info = self.available_agents.get(response.agent_name, {})
            agent_name = agent_info.get("name", response.agent_name)
            
            response_parts.append(f"**{agent_name}:**")
            if isinstance(response.data, dict):
                for key, value in response.data.items():
                    response_parts.append(f"- {key}: {value}")
            else:
                response_parts.append(f"- {response.data}")
            response_parts.append("")
        
        return "\n".join(response_parts)


# Global instance
super_agent = SuperAgent()
