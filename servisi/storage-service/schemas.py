from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SensorCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=24)
    name: Optional[str] = None


class SensorOut(BaseModel):
    id:str
    name: Optional[str] = None


class SensorDataIn(BaseModel):
    sensor_id: str
    temperature: float
    aqi: float
    timestamp: Optional[datetime] = None

class SensorDataOut(BaseModel):
    id: int
    sensor_id : str
    temperature : float
    aqi: float
    timestamp: datetime