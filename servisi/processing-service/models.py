from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SensorStats(BaseModel):
    sensor_id: str
    period_start: datetime
    period_end: datetime
    data_points: int = Field(..., ge=0)
    temperature_min: float
    temperature_max: float
    temperature_avg: float
    temperature_std: Optional[float] = None
    aqi_min: float = Field(..., ge=0, le=500)
    aqi_max: float = Field(..., ge=0, le=500)
    aqi_avg: float = Field(..., ge=0, le=500)
    aqi_std: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AggregatedStats(BaseModel):
    total_sensors: int = Field(..., ge=0)
    total_data_points: int = Field(..., ge=0)
    global_temp_avg: float
    global_aqi_avg: float = Field(..., ge=0, le=500)
    sensors: List[SensorStats]
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

class TrendAnalysis(BaseModel):
    sensor_id: str
    temperature_trend: str = Field(..., pattern="^(stable|increasing|decreasing|variable)$")
    aqi_status: str = Field(..., pattern="^(good|moderate|unhealthy|hazardous)$")
    recommendation: str
    last_analysis: datetime

class ProcessingStatus(BaseModel):
    status: str
    processed_sensors: int
    timestamp: datetime
    next_run: Optional[datetime] = None