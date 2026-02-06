from datetime import datetime, timedelta
from typing import List, Optional

import logging

from ..models.weather_models import WeatherSnapshot
from ..models.output_models import WeatherAlertOutput, AlertAction
from ..constants.thresholds import (
    HEAT_STRESS_TEMP,
    COLD_STRESS_TEMP,
    HEAVY_RAIN_MM,
    HIGH_WIND_KMH,
    ALERT_COOLDOWN_MINUTES
)

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Deterministic rule engine for Weather Watcher
    """

    def __init__(self, last_alerts: dict):
        """
        last_alerts format:
        {
            "HEAT": datetime,
            "RAIN": datetime,
            "WIND": datetime
        }
        """
        self.last_alerts = last_alerts

    # ---------------- PUBLIC ---------------- #

    def evaluate(self, weather: WeatherSnapshot) -> List[WeatherAlertOutput]:
        alerts = []

        heat_alert = self._heat_rule(weather)
        if heat_alert:
            alerts.append(heat_alert)

        rain_alert = self._rain_rule(weather)
        if rain_alert:
            alerts.append(rain_alert)

        wind_alert = self._wind_rule(weather)
        if wind_alert:
            alerts.append(wind_alert)

        return alerts

    # ---------------- RULES ---------------- #

    def _heat_rule(self, weather: WeatherSnapshot) -> Optional[WeatherAlertOutput]:
        if weather.max_temperature < HEAT_STRESS_TEMP:
            return None

        if not self._cooldown_passed("HEAT"):
            return None

        logger.warning("Heat stress rule triggered")

        self.last_alerts["HEAT"] = datetime.utcnow()

        return WeatherAlertOutput(
            alert_type="HEAT_STRESS",
            severity="HIGH",
            confidence=0.85,
            message="High temperature may cause heat stress to crops.",
            actions=[
                AlertAction(action="Avoid mid-day field work"),
                AlertAction(action="Ensure sufficient irrigation")
            ],
            valid_till=datetime.utcnow() + timedelta(hours=12),
            generated_at=datetime.utcnow()
        )

    def _rain_rule(self, weather: WeatherSnapshot) -> Optional[WeatherAlertOutput]:
        if weather.rainfall_mm < HEAVY_RAIN_MM:
            return None

        if not self._cooldown_passed("RAIN"):
            return None

        logger.warning("Heavy rain rule triggered")

        self.last_alerts["RAIN"] = datetime.utcnow()

        return WeatherAlertOutput(
            alert_type="HEAVY_RAIN",
            severity="HIGH",
            confidence=0.88,
            message="Heavy rainfall expected. Field operations may be affected.",
            actions=[
                AlertAction(action="Stop irrigation"),
                AlertAction(action="Avoid pesticide spraying")
            ],
            valid_till=datetime.utcnow() + timedelta(hours=6),
            generated_at=datetime.utcnow()
        )

    def _wind_rule(self, weather: WeatherSnapshot) -> Optional[WeatherAlertOutput]:
        if weather.wind_speed < HIGH_WIND_KMH:
            return None

        if not self._cooldown_passed("WIND"):
            return None

        logger.warning("High wind rule triggered")

        self.last_alerts["WIND"] = datetime.utcnow()

        return WeatherAlertOutput(
            alert_type="HIGH_WIND",
            severity="MEDIUM",
            confidence=0.80,
            message="Strong winds detected. Spraying may be unsafe.",
            actions=[
                AlertAction(action="Postpone spraying operations")
            ],
            valid_till=datetime.utcnow() + timedelta(hours=4),
            generated_at=datetime.utcnow()
        )

    # ---------------- UTILS ---------------- #

    def _cooldown_passed(self, alert_type: str) -> bool:
        last_time = self.last_alerts.get(alert_type)

        if not last_time:
            return True

        return datetime.utcnow() - last_time > timedelta(
            minutes=ALERT_COOLDOWN_MINUTES
        )
