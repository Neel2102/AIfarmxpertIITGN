"""
Orchestrator Router
API endpoints for the central orchestrator.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from farmxpert.app.orchestrator.agent import OrchestratorAgent
from farmxpert.app.shared.utils import logger
from farmxpert.app.shared.exceptions import FarmXpertException, OrchestratorException

router = APIRouter()

@router.get("/")
async def orchestrator_info():
    """Get orchestrator information"""
    return {
        "name": "FarmXpert Orchestrator",
        "description": "Coordinates weather and growth agents using pluggable routing rules",
        "version": "2.0.0",
        "capabilities": [
            "Pluggable routing rules",
            "Multi-agent coordination",
            "Optional LLM summaries"
        ],
        "endpoints": [
            "/orchestrator/dispatch",
            "/orchestrator/chat",
            "/orchestrator/analyze"
        ]
    }

@router.post("/dispatch")
async def dispatch(request: Dict[str, Any]):
    """
    Dispatch request based on routing rules.

    Request options:
    - query: optional natural language query
    - location: {latitude, longitude}
    - crop_data: crop payload for growth analysis
    - strategy: "weather" | "growth" | "both" | "auto"
    - llm_summary: bool (optional)
    """
    try:
        logger.info("🧭 Received orchestrator dispatch request")
        result = await OrchestratorAgent.handle_request(request)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        return result
    except FarmXpertException as e:
        logger.error(f"Orchestrator dispatch failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in orchestrator dispatch: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during dispatch"
        })

@router.post("/chat")
async def conversational_chat(request: Dict[str, Any] = Body(...)):
    """
    Conversational entrypoint.
    Behaves like /dispatch but expects a 'query' field and defaults to auto routing.
    """
    try:
        logger.info("💬 Received orchestrator chat request")
        logger.info(f"Request body: {request}")
        request.setdefault("strategy", "auto")
        result = await OrchestratorAgent.handle_request(request)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        return result
    except FarmXpertException as e:
        logger.error(f"Orchestrator chat failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in orchestrator chat: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during chat processing"
        })

@router.post("/analyze")
async def analyze(request: Dict[str, Any]):
    """
    Comprehensive analysis; defaults to both agents.
    """
    try:
        logger.info("Received orchestrator analyze request")
        request.setdefault("strategy", "both")
        result = await OrchestratorAgent.handle_request(request)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        return result
    except FarmXpertException as e:
        logger.error(f"Orchestrator analyze failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in orchestrator analyze: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during analysis"
        })

@router.get("/health")
async def orchestrator_health():
    """Health check for orchestrator"""
    return {
        "status": "healthy",
        "agent": "orchestrator",
        "timestamp": "2026-02-03T00:00:00Z",
        "routing_rules": "active",
        "llm_summary": "optional",
        "coordinated_agents": {
            "weather_watcher": "active",
            "growth_stage_monitor": "active", 
            "irrigation_agent": "active",
            "fertilizer_agent": "active"
        },
        "capabilities": [
            "weather_analysis",
            "growth_monitoring", 
            "irrigation_recommendations",
            "fertilizer_recommendations",
            "comprehensive_farming_advice"
        ]
    }
