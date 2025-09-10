from sqlalchemy import Column,String, Float, DateTime, Integer
from datetime import datetime
from database import Base 



class Sensor(Base):
    __tablename__="sensors"

    id = Column(String, primary_key = True, index = True)
    name = Column(String, nullable=False)
    location = Column(String)
    created_at = Column(DateTime, default = datetime.utcnow)


class SensorData(Base):
    __tablename__="sensor_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(String, index=True, nullable=False)
    temperature = Column(Float, nullable=False)
    aqi = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


