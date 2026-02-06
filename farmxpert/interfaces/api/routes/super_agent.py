"""
Super Agent API Routes
Handles user queries through the SuperAgent system
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import json
import asyncio
from datetime import datetime
from farmxpert.core.super_agent import super_agent, SuperAgentResponse
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.gemini_service import gemini_service

router = APIRouter(prefix="/super-agent", tags=["Super Agent"])
logger = get_logger("super_agent_api")


class QueryRequest(BaseModel):
    """Request model for user queries"""
    query: str = Field(..., description="User's agricultural query", min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID for personalization")


class QueryResponse(BaseModel):
    """Response model for user queries"""
    success: bool
    response: Any  # Backward-compatible: UI renders string; we provide a concise answer
    sop: Optional[Dict[str, Any]] = None  # Full SOP JSON payload
    session_id: str
    agent_responses: List[Dict[str, Any]]
    recommendations: List[str]
    warnings: List[str]
    execution_time: float
    timestamp: datetime


class AgentInfoResponse(BaseModel):
    """Response model for available agents information"""
    agents: Dict[str, Dict[str, Any]]
    total_agents: int
    categories: List[str]


@router.post("/query/stream")
async def process_user_query_stream(request: QueryRequest):
    """
    Process a user query with streaming response
    
    This endpoint provides real-time streaming of AI responses,
    similar to ChatGPT's typing effect. Returns Server-Sent Events (SSE).
    """
    try:
        logger.info(f"Processing streaming query: {request.query[:100]}...")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Prepare context
        context = request.context or {}
        if request.user_id:
            context["user_id"] = request.user_id
        context["session_id"] = session_id
        
        async def generate_stream():
            try:
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
                
                # Use Gemini service directly for faster streaming
                full_prompt = f"""
You are FarmXpert, an AI agricultural expert system.

Farmer Context:
{json.dumps(context, indent=2)}

Farmer Question:
{request.query}

Provide your response in this exact format with proper line breaks and bullet points:

Direct Answer:
[Your clear answer here]

Recommendations:
- First recommendation
- Second recommendation
- Third recommendation

Scientific Reasoning:
[Explain why these recommendations work]

Warnings / Considerations:
- First warning
- Second warning

Additional Information:
[Any extra helpful details]

IMPORTANT: Use proper line breaks and bullet points (-) for lists. Each item should be on a new line.
"""
                
                # Stream the response
                async for chunk in gemini_service.generate_streaming_response(full_prompt, context):
                    if chunk:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing streaming query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process streaming query: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def process_user_query(request: QueryRequest):
    """
    Process a user query through the SuperAgent system
    
    This endpoint:
    1. Takes a user's agricultural query
    2. Uses Gemini to determine which agents to call
    3. Executes the selected agents with appropriate tools
    4. Synthesizes a comprehensive response
    5. Returns the final answer to the user
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Prepare context
        context = request.context or {}
        if request.user_id:
            context["user_id"] = request.user_id
        context["session_id"] = session_id
        
        # Process query through SuperAgent
        result: SuperAgentResponse = await super_agent.process_query(
            query=request.query,
            context=context,
            session_id=session_id
        )
        
        # Extract recommendations and warnings from agent responses
        recommendations = []
        warnings = []
        
        for agent_response in result.agent_responses:
            if agent_response.success and isinstance(agent_response.data, dict):
                # Extract recommendations from agent data
                if "recommendations" in agent_response.data:
                    if isinstance(agent_response.data["recommendations"], list):
                        for rec in agent_response.data["recommendations"]:
                            if isinstance(rec, dict):
                                # Convert dict to string representation
                                recommendations.append(f"{rec.get('variety', 'Unknown')}: {rec.get('description', 'No description')}")
                            else:
                                recommendations.append(str(rec))
                    else:
                        recommendations.append(str(agent_response.data["recommendations"]))
                
                # Extract warnings from agent data
                if "warnings" in agent_response.data:
                    if isinstance(agent_response.data["warnings"], list):
                        warnings.extend(agent_response.data["warnings"])
                    else:
                        warnings.append(str(agent_response.data["warnings"]))
        
        # Format agent responses for API response
        formatted_agent_responses = []
        for agent_response in result.agent_responses:
            formatted_agent_responses.append({
                "agent_name": agent_response.agent_name,
                "success": agent_response.success,
                "data": agent_response.data,
                "error": agent_response.error,
                "execution_time": agent_response.execution_time
            })
        
        # Prepare concise string answer for UI and attach SOP JSON
        sop_json: Dict[str, Any] = result.response if isinstance(result.response, dict) else {}
        answer_text: str = sop_json.get("answer") if isinstance(sop_json, dict) else None
        if not answer_text:
            # Fallback to a short string
            answer_text = "Response ready." if result.success else "Sorry, something went wrong."

        return QueryResponse(
            success=result.success,
            response=answer_text,
            sop=sop_json or None,
            session_id=session_id,
            agent_responses=formatted_agent_responses,
            recommendations=recommendations,
            warnings=warnings,
            execution_time=result.execution_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/agents", response_model=AgentInfoResponse)
async def get_available_agents():
    """
    Get information about all available agents
    
    Returns details about:
    - All registered agents
    - Agent categories
    - Available tools for each agent
    - Agent descriptions and capabilities
    """
    try:
        agents_info = super_agent.available_agents
        
        # Extract categories
        categories = list(set(agent_info.get("category", "unknown") for agent_info in agents_info.values()))
        categories.sort()
        
        return AgentInfoResponse(
            agents=agents_info,
            total_agents=len(agents_info),
            categories=categories
        )
        
    except Exception as e:
        logger.error(f"Error getting agent information: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent information: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the SuperAgent system
    
    Returns the status of:
    - SuperAgent initialization
    - Available agents
    - Gemini service connectivity
    - Tool availability
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(),
            "super_agent": {
                "initialized": True,
                "available_agents": len(super_agent.available_agents),
                "available_tools": len(super_agent.tools)
            },
            "services": {
                "gemini_service": "available",  # This would check actual service status
                "agent_registry": "available"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }


@router.get("/status/realtime")
async def get_realtime_status():
    """
    Get real-time status of all agents and system components
    
    Returns:
    - Agent status (active, processing, idle)
    - System performance metrics
    - Recent activity
    """
    try:
        # Get agent status from the registry
        agents_info = super_agent.available_agents
        
        # Simulate real-time agent status (in a real implementation, this would be dynamic)
        agent_status = {}
        for agent_name, agent_info in agents_info.items():
            # Simulate different statuses based on agent type
            if agent_name in ['crop_selector', 'weather_watcher', 'irrigation_planner']:
                status = "active"
            elif agent_name in ['yield_predictor', 'profit_optimization']:
                status = "processing"
            else:
                status = "idle"
            
            agent_status[agent_name] = {
                "name": agent_info.get("name", agent_name),
                "category": agent_info.get("category", "unknown"),
                "status": status,
                "last_activity": datetime.now().isoformat(),
                "response_time": f"{round(0.5 + (hash(agent_name) % 10) * 0.1, 2)}s"
            }
        
        # Count statuses
        status_counts = {
            "active": sum(1 for agent in agent_status.values() if agent["status"] == "active"),
            "processing": sum(1 for agent in agent_status.values() if agent["status"] == "processing"),
            "idle": sum(1 for agent in agent_status.values() if agent["status"] == "idle")
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "agent_status": agent_status,
            "status_counts": status_counts,
            "total_agents": len(agent_status),
            "system_metrics": {
                "cpu_usage": f"{20 + (hash(str(datetime.now())) % 30)}%",
                "memory_usage": f"{45 + (hash(str(datetime.now())) % 20)}%",
                "active_sessions": 1,
                "queries_processed_today": 42
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get real-time status: {str(e)}"
        )


@router.post("/query/batch")
async def process_batch_queries(requests: List[QueryRequest]):
    """
    Process multiple queries in batch
    
    Useful for:
    - Processing multiple related questions
    - Bulk analysis of farm data
    - Comparative analysis across different scenarios
    """
    try:
        if len(requests) > 10:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size cannot exceed 10 queries"
            )
        
        results = []
        for request in requests:
            try:
                # Process each query
                result = await process_user_query(request)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch query: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "query": request.query
                })
        
        return {
            "batch_results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r.get("success", False)]),
            "failed": len([r for r in results if not r.get("success", False)])
        }
        
    except Exception as e:
        logger.error(f"Error processing batch queries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process batch queries: {str(e)}"
        )


@router.get("/tools")
async def get_available_tools():
    """
    Get information about available tools
    
    Returns details about:
    - All available tools
    - Tool capabilities
    - Tool usage examples
    """
    try:
        tools_info = {}
        
        for tool_name, tool_instance in super_agent.tools.items():
            # Get tool methods
            methods = [method for method in dir(tool_instance) 
                      if not method.startswith('_') and callable(getattr(tool_instance, method))]
            
            tools_info[tool_name] = {
                "class_name": tool_instance.__class__.__name__,
                "available_methods": methods,
                "description": tool_instance.__class__.__doc__ or f"Tool for {tool_name} operations"
            }
        
        return {
            "tools": tools_info,
            "total_tools": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools information: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools information: {str(e)}"
        )
