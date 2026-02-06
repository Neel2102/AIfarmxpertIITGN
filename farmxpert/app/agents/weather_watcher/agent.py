"""
Weather Watcher Agent
Core logic for weather monitoring and alert generation
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .services.weather_service import WeatherService
from .services.rule_engine import RuleEngine
from .services.llm_service import LLMService
from .models.weather_models import WeatherSnapshot
from .models.output_models import WeatherAlertOutput, AlertAction
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response
from farmxpert.app.shared.exceptions import WeatherServiceException, LLMServiceException


class WeatherWatcherAgent:
    """Weather monitoring and alert generation agent"""
    
    @staticmethod
    def analyze_weather(location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze weather conditions for a given location
        
        Args:
            location: Dictionary containing latitude and longitude
            
        Returns:
            Dictionary with weather analysis results and alerts
        """
        try:
            logger.info(f"🌦️ Analyzing weather for location: {location}")
            
            # Extract coordinates
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            
            if not latitude or not longitude:
                return create_error_response(
                    "INVALID_LOCATION",
                    "Latitude and longitude are required",
                    {"location": location}
                )
            
            # Get current weather
            weather = WeatherService.get_weather(latitude, longitude)
            
            if not weather:
                return create_error_response(
                    "WEATHER_FETCH_FAILED",
                    "Failed to fetch weather data",
                    {"coordinates": {"lat": latitude, "lon": longitude}}
                )
            
            # Generate alerts using rule engine
            alerts = RuleEngine(last_alerts={}).evaluate(weather)
            
            # Prepare response data
            response_data = {
                "location": location,
                "weather": weather.model_dump(),
                "alerts": [alert.model_dump() for alert in alerts],
                "alert_count": len(alerts),
                "analysis_summary": f"Weather analyzed for coordinates ({latitude}, {longitude})"
            }
            
            # Add LLM explanation for alerts if any
            if alerts:
                try:
                    explanation = LLMService.explain_alert(alerts[0])
                    response_data["llm_explanation"] = explanation
                except Exception as e:
                    logger.warning(f"LLM explanation failed: {e}")
                    response_data["llm_explanation"] = "Unable to generate explanation"
            
            return create_success_response(
                response_data,
                message=f"Weather analysis completed for coordinates ({latitude}, {longitude})",
                metadata={
                    "temperature": weather.temperature,
                    "condition": weather.weather_condition,
                    "alert_count": len(alerts)
                }
            )
            
        except WeatherServiceException as e:
            logger.error(f"Weather service error: {e.message}")
            return create_error_response(
                e.error_code or "WEATHER_ERROR",
                e.message,
                e.details
            )
        except Exception as e:
            logger.error(f"Unexpected error in weather analysis: {e}")
            return create_error_response(
                "UNEXPECTED_ERROR",
                f"Unexpected error: {str(e)}",
                {"location": location}
            )
    
    @staticmethod
    def get_weather_alerts(location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get weather alerts for a location
        
        Args:
            location: Dictionary containing latitude and longitude
            
        Returns:
            Dictionary with weather alerts
        """
        try:
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            
            if not latitude or not longitude:
                return create_error_response(
                    "INVALID_LOCATION",
                    "Latitude and longitude are required"
                )
            
            # Get weather data
            weather = WeatherService.get_weather(latitude, longitude)
            
            if not weather:
                return create_error_response(
                    "WEATHER_FETCH_FAILED",
                    "Failed to fetch weather data"
                )
            
            # Generate alerts
            alerts = RuleEngine(last_alerts={}).evaluate(weather)
            
            return create_success_response(
                {
                    "location": location,
                    "alerts": [alert.model_dump() for alert in alerts],
                    "alert_count": len(alerts)
                },
                message=f"Generated {len(alerts)} weather alerts"
            )
            
        except Exception as e:
            logger.error(f"Error getting weather alerts: {e}")
            return create_error_response(
                "ALERT_GENERATION_FAILED",
                f"Failed to generate alerts: {str(e)}"
            )
