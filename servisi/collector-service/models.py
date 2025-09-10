from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class SensorData(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50, description="ID senzora")
    temperature: float = Field(..., ge=-50, le=100, description="Temperatura u °C")
    aqi: float = Field(..., ge=0, le=500, description="Air Quality Index")
    timestamp: Optional[float] = Field(None, description="Unix timestamp")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v < -40 or v > 60:
            raise ValueError('Temperatura izvan realnog raspona za HR')
        return v

class IngestResponse(BaseModel):
    status: str
    sensor: str
    data_id: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str
    service: str
    storage_connected: bool
    