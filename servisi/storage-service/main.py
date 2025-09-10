from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import engine, get_db
from models import Base, Sensor, SensorData
from schemas import (
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
    db: Session = Depends(get_db)
):
    sensors = db.query(Sensor).offset(skip).limit(limit).all()
    return sensors


@app.get("/sensors/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: str, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


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


@app.get("/data", response_model=List[SensorDataResponse])
def get_sensor_data(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    limit: int = Query(100, description="Maximum number of results"),
    skip: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    
    query = db.query(SensorData)
    
   
    if sensor_id:
        query = query.filter(SensorData.sensor_id == sensor_id)
    
   
    query = query.order_by(SensorData.timestamp.desc())
    
    
    data = query.offset(skip).limit(limit).all()
    
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=True
    )

    