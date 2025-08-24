from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .database import engine, get_db
from .models import Base, Sensor, SensorData
from .schemas import (
    SensorCreate,SensorResponse,
    SensorDataResponse, SensorDataCreate
)

app = FastAPI(
    title="Storage Service", 
    description="Servis za spremanje podataka o senzorima", 
    version="1.0.1")

@app.on_event("startup")
def on_startup():
    print("Kreiranje tablica...")
    Base.metadata.create_all(bind=engine)
    print("Tablice kreirane")    


@app.get("/health")
def health():
    return {"status" : "ok"}




@app.post("/sensors", response_model=SensorResponse)
def create_sensor(
     sensor: SensorCreate, 
     db: Session = Depends(get_db)
):
    db_sensor = db.query(Sensor).filter(Sensor.id == sensor.id).first()
    if db_sensor:
        raise HTTPException(status_code=400, detail="Senzor vec postoji")
    
    
    db_sensor = Sensor(**sensor.dict())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


@app.get("/sensors", response_model=List[SensorResponse])
def list_sensors(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)  # <-- Svaki endpoint koji koristi DB treba dependency
):
    sensors = db.query(Sensor).offset(skip).limit(limit).all()
    return sensors



@app.post("/data", response_model=SensorDataResponse)
def create_sensor_data(
    data: SensorDataCreate, 
    db: Session = Depends(get_db)
):
    # Verify sensor exists
    sensor = db.query(Sensor).filter(Sensor.id == data.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    # Create data entry
    db_data = SensorData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


