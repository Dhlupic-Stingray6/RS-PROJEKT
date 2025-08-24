from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SensorCreate(BaseModel):
    id: str
    name: str
    location: Optional[str] = None

class SensorResponse(BaseModel):
    id: str 
    name: str
    location: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SensorDataCreate(BaseModel):
    sensor_id: str
    temperature: float
    aqi: float
    timestamp : Optional[datetime] = None


class SensorDataResponse(BaseModel):
    id: int
    sensor_id: str
    temperature: float
    aqi: float
    timestamp: datetime

    class Config:
        from_attributes = True
