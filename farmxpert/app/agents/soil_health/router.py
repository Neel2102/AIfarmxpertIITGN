"""
Soil Health Agent Router
API endpoints for soil health analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
from farmxpert.app.agents.soil_health.services.soil_health_service import SoilHealthAnalysisService
from farmxpert.app.agents.soil_health.models.input_models import SoilHealthInput, QuickSoilCheckInput
from farmxpert.app.agents.soil_health.models.output_models import SoilHealthResponse
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response

router = APIRouter()

@router.get("/")
async def soil_health_info():
    """Get soil health agent information"""
    return {
        "name": "Soil Health Agent",
        "description": "Analyzes soil health parameters and provides recommendations",
        "version": "2.0.0",
        "architecture": "Optimized for FarmXpert modular monolith",
        "capabilities": [
            "Soil pH analysis",
            "Nutrient level assessment (N, P, K)",
            "Salinity detection",
            "Chemical and organic recommendations",
            "Health scoring",
            "Crop-specific analysis",
            "Location-aware recommendations"
        ],
        "models": {
            "input": ["SoilHealthInput", "QuickSoilCheckInput"],
            "output": ["SoilHealthAnalysis", "QuickSoilCheckResult"]
        },
        "services": ["SoilHealthAnalysisService"],
        "constraints": ["soil_constraints.py with crop-specific thresholds"],
        "endpoints": [
            "/agents/soil_health/analyze",
            "/agents/soil_health/quick_check"
        ]
    }

@router.post("/analyze")
async def analyze_soil(request: Dict[str, Any]):
    """
    Comprehensive soil health analysis
    
    Request format:
    {
        "location": {
            "latitude": 21.7051,
            "longitude": 72.9959,
            "district": "Ankleshwar",
            "state": "Gujarat"
        },
        "soil_data": {
            "pH": 6.5,
            "nitrogen": 50,
            "phosphorus": 20,
            "potassium": 100,
            "electrical_conductivity": 1.5,
            "moisture": 35.0,
            "temperature": 18.0
        },
        "crop_type": "cotton",
        "growth_stage": "vegetative"
    }
    """
    try:
        logger.info("🌱 Received comprehensive soil health analysis request")
        
        # Validate and parse input
        try:
            # Create location input
            from farmxpert.app.agents.soil_health.models.input_models import LocationInput, SoilSensorData
            from farmxpert.app.agents.soil_health.models.input_models import SoilHealthInput
            
            location_input = LocationInput(
                latitude=request["location"]["latitude"],
                longitude=request["location"]["longitude"],
                district=request["location"].get("district", "Unknown"),
                state=request["location"].get("state", "Unknown"),
                field_id=request.get("field_id")
            )
            
            # Create soil sensor data
            soil_data = request["soil_data"]
            soil_sensor_data = SoilSensorData(
                pH=soil_data["pH"],
                nitrogen=soil_data["nitrogen"],
                phosphorus=soil_data["phosphorus"],
                potassium=soil_data["potassium"],
                electrical_conductivity=soil_data["electrical_conductivity"],
                moisture=soil_data.get("moisture"),
                temperature=soil_data.get("temperature"),
                organic_matter=soil_data.get("organic_matter")
            )
            
            # Create soil health input
            soil_input = SoilHealthInput(
                location=location_input,
                soil_data=soil_sensor_data,
                crop_type=request.get("crop_type"),
                growth_stage=request.get("growth_stage"),
                triggered_at=datetime.now(),
                request_source=request.get("request_source", "api"),
                field_id=request.get("field_id")
            )
            
        except Exception as e:
            return create_error_response(
                "INVALID_INPUT",
                f"Invalid input format: {str(e)}",
                {"request": request}
            )
        
        # Perform analysis
        analysis = SoilHealthAnalysisService.analyze_soil_health(soil_input)
        
        return create_success_response(
            analysis.dict(),
            message="Comprehensive soil health analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Soil health analysis error: {e}")
        return create_error_response(
            "SOIL_HEALTH_ANALYSIS_ERROR",
            str(e),
            {"request": request}
        )

@router.post("/quick_check")
async def quick_soil_check(request: Dict[str, Any]):
    """
    Quick soil health check with minimal parameters
    
    Request format:
    {
        "pH": 6.5,
        "nitrogen": 50,
        "phosphorus": 20,
        "potassium": 100,
        "electrical_conductivity": 1.5,
        "moisture": 35.0,
        "temperature": 18.0
    }
    """
    try:
        logger.info("🌱 Received quick soil health check")
        
        # Validate and parse input
        try:
            quick_input = QuickSoilCheckInput(**request)
        except Exception as e:
            return create_error_response(
                "INVALID_INPUT",
                f"Invalid input format: {str(e)}",
                {"request": request}
            )
        
        # Perform quick check
        result = SoilHealthAnalysisService.quick_soil_check(quick_input)
        
        return create_success_response(
            result.dict(),
            message="Quick soil health check completed"
        )
        
    except Exception as e:
        logger.error(f"Quick soil check error: {e}")
        return create_error_response(
            "QUICK_SOIL_CHECK_ERROR",
            str(e),
            {"request": request}
        )

@router.get("/health")
async def soil_health_agent_health():
    """Health check for soil health agent"""
    return {
        "status": "healthy",
        "agent": "soil_health_agent",
        "version": "2.0.0",
        "timestamp": "2026-02-03T22:15:00Z",
        "architecture": "FarmXpert modular monolith optimized",
        "capabilities": [
            "soil_ph_analysis",
            "nutrient_assessment", 
            "salinity_detection",
            "recommendation_generation",
            "health_scoring",
            "crop_specific_analysis",
            "location_aware_recommendations"
        ],
        "parameters_monitored": [
            "pH", "nitrogen", "phosphorus", "potassium", 
            "electrical_conductivity", "moisture", "temperature"
        ],
        "supported_crops": [
            "cotton", "wheat", "rice", "maize", "default"
        ],
        "models_loaded": True,
        "constraints_loaded": True,
        "services_active": 1
    }
