"""
Weather Watcher Router
API endpoints for weather monitoring agent
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .agent import WeatherWatcherAgent
from farmxpert.app.shared.utils import logger
from farmxpert.app.shared.exceptions import FarmXpertException

router = APIRouter()

@router.get("/")
async def weather_info():
    """Get weather watcher information"""
    return {
        "name": "Weather Watcher Agent",
        "description": "Monitors weather conditions and generates alerts",
        "version": "1.0.0",
        "capabilities": [
            "Current weather analysis",
            "Weather alert generation",
            "LLM-powered explanations",
            "Multi-source weather data"
        ]
    }

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_weather(request: Dict[str, Any]):
    """
    Analyze weather conditions for a location
    
    Args:
        request: Dictionary containing location and analysis options
        
    Returns:
        Weather analysis results with alerts and recommendations
    """
    try:
        logger.info(f"🌦️ Received weather analysis request")
        
        # Extract location from request
        location = request.get("location", {})
        
        if not location.get("latitude") or not location.get("longitude"):
            raise HTTPException(status_code=400, detail={
                "error": True,
                "error_code": "INVALID_LOCATION",
                "message": "Latitude and longitude are required"
            })
        
        # Call agent for analysis
        result = WeatherWatcherAgent.analyze_weather(location)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except FarmXpertException as e:
        logger.error(f"Weather analysis failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in weather analysis: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during weather analysis"
        })

@router.post("/alerts", response_model=Dict[str, Any])
async def get_weather_alerts(location: Dict[str, Any]):
    """
    Get weather alerts for a location
    
    Args:
        location: Dictionary containing latitude and longitude
        
    Returns:
        Weather alerts for the specified location
    """
    try:
        logger.info(f"🚨 Received weather alerts request")
        
        if not location.get("latitude") or not location.get("longitude"):
            raise HTTPException(status_code=400, detail={
                "error": True,
                "error_code": "INVALID_LOCATION",
                "message": "Latitude and longitude are required"
            })
        
        # Call agent for alerts
        result = WeatherWatcherAgent.get_weather_alerts(location)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except FarmXpertException as e:
        logger.error(f"Weather alerts failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in weather alerts: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during weather alerts generation"
        })

@router.get("/health")
async def weather_health():
    """Health check for weather watcher agent"""
    return {
        "status": "healthy",
        "agent": "weather_watcher",
        "timestamp": "2026-01-30T11:39:00Z",
        "services": {
            "weather_service": "active",
            "rule_engine": "active",
            "llm_service": "active"
        }
    }
