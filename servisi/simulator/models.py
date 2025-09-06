from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Location(BaseModel):
    city: str
    latitude: float
    longitude: float
    base_temp: float  
    base_aqi: float  
    is_urban: bool    

class SensorConfig(BaseModel):
    sensor_id: str
    name: str
    location: Location
    active: bool = True

class SimulatorConfig(BaseModel):
    sensor_count: int = Field(5, ge=1, le=50)
    interval_seconds: int = Field(10, ge=1, le=3600)
    collector_url: str
    storage_url: str