from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AlertAction(BaseModel):
    action: str
    reason: Optional[str] = None


class WeatherAlertOutput(BaseModel):
    alert_type: str                # HEAT, RAIN, WIND
    severity: str                  # LOW, MEDIUM, HIGH
    confidence: float              # 0.0 – 1.0
    message: str
    actions: List[AlertAction]
    valid_till: Optional[datetime]
    generated_at: datetime
