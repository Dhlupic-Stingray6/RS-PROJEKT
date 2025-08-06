from pydantic import BaseModel


class SensorData(BaseModel):
    sensor_id: str 
    timestamp: float
    temperature: float 
    aqi: float


    