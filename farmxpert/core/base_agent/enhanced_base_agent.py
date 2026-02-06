"""
Enhanced Base Agent for FarmXpert
Extends existing agents with LLM capabilities while maintaining compatibility
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from farmxpert.core.base_agent.base_agent import BaseAgent
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.gemini_service import gemini_service


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentPriority(Enum):
    """Agent execution priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EnhancedAgentContext:
    """Enhanced context information for agent execution"""
    session_id: str
    user_id: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[float] = None
    farm_size_unit: str = "hectares"
    preferred_language: str = "en"
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    farm_id: Optional[str] = None
    db_session: Optional[Any] = None


@dataclass
class EnhancedAgentInput:
    """Enhanced input data for agent processing"""
    query: str
    context: EnhancedAgentContext
    additional_data: Dict[str, Any] = field(default_factory=dict)
    priority: AgentPriority = AgentPriority.NORMAL
    timeout: int = 30  # seconds


@dataclass
class EnhancedAgentOutput:
    """Enhanced output data from agent processing"""
    success: bool
    response: str
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    confidence: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedBaseAgent(BaseAgent):
    """
    Enhanced base class for FarmXpert agents
    Adds LLM capabilities while maintaining compatibility with existing agents
    """
    
    def __init__(
        self,
        name: str = None,
        description: str = None,
        use_llm: bool = True,
        max_retries: int = 3,
        temperature: float = 0.6
    ):
        # Use provided values or fall back to class attributes
        self.name = name or getattr(self, 'name', 'enhanced_agent')
        self.description = description or getattr(self, 'description', 'Enhanced AI Agent')
        
        super().__init__()
        
        # Enhanced capabilities
        self.use_llm = use_llm
        self.max_retries = max_retries
        self.temperature = temperature
        self.status = AgentStatus.IDLE
        
        # Enhanced logger
        self.logger = get_logger(f"enhanced_agent.{self.name}")
        
        # Agent-specific configuration
        self.config = self._load_agent_config()
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent-specific configuration"""
        return {
            "max_tokens": 2000,
            "system_prompt": self._get_system_prompt(),
            "examples": self._get_examples(),
            "tools": self._get_tools(),
            "use_llm": self.use_llm
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.name}, a specialized AI agent for {self.description}.

Your role is to provide expert, accurate, and actionable advice to farmers.
Always consider the context, farm conditions, and user preferences when making recommendations.
Provide responses in clear, practical language suitable for farmers of all experience levels."""
    
    def _get_examples(self) -> List[Dict[str, str]]:
        """Get example conversations for this agent"""
        return []
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools/functions available to this agent"""
        return []
    
    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced handle method that can use LLM when needed
        Maintains compatibility with existing agent interface
        """
        if self.use_llm and self._should_use_llm(inputs):
            return await self._handle_with_llm(inputs)
        else:
            return await self._handle_traditional(inputs)
    
    def _should_use_llm(self, inputs: Dict[str, Any]) -> bool:
        """Determine if LLM should be used for this request"""
        # Use LLM for complex queries or when explicitly requested
        query = inputs.get('query', '')
        use_llm_flag = inputs.get('use_llm', False)
        
        # Prefer LLM more often; only bypass for very short queries
        if len(query) < 8:
            return False
        
        # Complex queries benefit from LLM
        complex_keywords = ['analyze', 'recommend', 'explain', 'compare', 'why', 'how', 'best', 'suggest', 'plan']
        if any(keyword in query.lower() for keyword in complex_keywords):
            return True
        
        return use_llm_flag
    
    async def _handle_with_llm(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request using LLM capabilities"""
        start_time = datetime.now()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"Processing with LLM: {inputs.get('query', '')[:100]}...")
            
            # Prepare context and prompt
            context = self._prepare_context(inputs)
            prompt = self._build_prompt(inputs, context)
            
            # Get LLM response
            response = await self._get_llm_response(prompt, inputs)
            
            # Parse and validate response
            parsed_response = self._parse_response(response)
            
            # Create output
            output = {
                "agent": self.name,
                "success": True,
                "response": parsed_response.get("response", ""),
                "recommendations": parsed_response.get("recommendations", []),
                "warnings": parsed_response.get("warnings", []),
                "insights": parsed_response.get("insights", []),
                "data": parsed_response.get("data", {}),
                "confidence": parsed_response.get("confidence", 0.8),
                "metadata": {
                    "method": "llm",
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "model": "gemini-pro"
                }
            }
            
            self.status = AgentStatus.COMPLETED
            self.logger.info("LLM processing completed successfully")
            
            return output
            
        except Exception as e:
            self.logger.error(f"LLM processing failed: {str(e)}")
            self.status = AgentStatus.FAILED
            
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request using traditional agent logic"""
        self.logger.info("Using traditional agent logic")
        
        # This should be implemented by subclasses
        # For now, return a basic response
        return {
            "agent": self.name,
            "success": True,
            "response": f"Traditional {self.name} response",
            "data": inputs,
            "metadata": {"method": "traditional"}
        }
    
    def _prepare_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for LLM processing"""
        context = {
            "user_query": inputs.get("query", ""),
            "farm_location": inputs.get("location", ""),
            "season": inputs.get("season", ""),
            "soil_data": inputs.get("soil", {}),
            "additional_data": inputs
        }
        
        # Add any other relevant context from inputs
        for key, value in inputs.items():
            if key not in ["query", "location", "season", "soil"]:
                context[key] = value
        
        return context
    
    def _build_prompt(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build the complete prompt for LLM"""
        system_prompt = self.config["system_prompt"]
        examples = self.config["examples"]
        tools = self.config["tools"]
        
        # Build context string
        context_str = self._format_context(context)
        
        # Build examples string
        examples_str = self._format_examples(examples)
        
        # Build tools string
        tools_str = self._format_tools(tools)
        
        # Build complete prompt
        prompt = f"""System: {system_prompt}

{tools_str}

{examples_str}

Context: {context_str}

User Query: {inputs.get('query', '')}

Please provide a comprehensive response in the following JSON format:
{{
    "response": "Main response text",
    "recommendations": ["recommendation1", "recommendation2"],
    "warnings": ["warning1", "warning2"],
    "insights": ["insight1", "insight2"],
    "data": {{"key": "value"}},
    "confidence": 0.85
}}

Response:"""
        
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt"""
        context_parts = []
        
        if context.get("farm_location"):
            context_parts.append(f"Farm Location: {context['farm_location']}")
        
        if context.get("season"):
            context_parts.append(f"Season: {context['season']}")
        
        if context.get("soil_data"):
            soil = context["soil_data"]
            if isinstance(soil, dict) and soil:
                soil_str = ", ".join([f"{k}: {v}" for k, v in soil.items()])
                context_parts.append(f"Soil Data: {soil_str}")
        
        if context.get("additional_data"):
            additional = context["additional_data"]
            if isinstance(additional, dict) and additional:
                for key, value in additional.items():
                    if key not in ["query", "location", "season", "soil"]:
                        context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts) if context_parts else "No specific context provided"
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> str:
        """Format examples for prompt"""
        if not examples:
            return ""
        
        examples_str = "Examples:\n"
        for i, example in enumerate(examples, 1):
            examples_str += f"Example {i}:\n"
            examples_str += f"Input: {example.get('input', '')}\n"
            examples_str += f"Output: {example.get('output', '')}\n\n"
        
        return examples_str
    
    def _format_tools(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools for prompt"""
        if not tools:
            return ""
        
        tools_str = "Available Tools:\n"
        for tool in tools:
            tools_str += f"- {tool.get('name', '')}: {tool.get('description', '')}\n"
        
        return tools_str
    
    async def _get_llm_response(self, prompt: str, inputs: Dict[str, Any]) -> str:
        """Get response from LLM with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = await gemini_service.generate_response(prompt, {"agent": self.name})
                return response
                
            except Exception as e:
                self.logger.warning(f"LLM request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                
                # Validate required fields
                if "response" not in parsed:
                    parsed["response"] = response
                
                return parsed
            else:
                # Fallback to treating entire response as text
                return {
                    "response": response,
                    "recommendations": [],
                    "warnings": [],
                    "insights": [],
                    "data": {},
                    "confidence": 0.7
                }
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {str(e)}")
            return {
                "response": response,
                "recommendations": [],
                "warnings": [],
                "insights": [],
                "data": {},
                "confidence": 0.6
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "use_llm": self.use_llm,
            "enhanced": True
        }
    
    async def reset(self):
        """Reset agent to idle state"""
        self.status = AgentStatus.IDLE
        self.logger.info("Agent reset to idle state")
    
    async def cancel(self):
        """Cancel current processing"""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.CANCELLED
            self.logger.info("Agent processing cancelled")
    
    def enable_llm(self):
        """Enable LLM capabilities"""
        self.use_llm = True
        self.logger.info("LLM capabilities enabled")
    
    def disable_llm(self):
        """Disable LLM capabilities"""
        self.use_llm = False
        self.logger.info("LLM capabilities disabled")
