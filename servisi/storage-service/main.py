from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db import engine, get_db
from models import Base, Sensor, SensorData
from schemas import SensorCreate, SensorOut, SensorDataIn, SensorDataOut
from typing import List



app = FastAPI(title="storage-service", version="0.1.0")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status" : "ok"}




@app.post("/sensors", response_model=SensorOut, status_code=201)
async def create_sensor(payload: SensorCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.get(Sensor, payload.id)
    if exists:
        raise HTTPException(status_code=400, detail="Senzor vec postoji")
    s = Sensor(id=payload.id, name=payload.name)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return SensorOut.model_validate(s.__dict__)


@app.get("/sensors/{sensor_id}", response_model=SensorOut)
async def get_sensor(sensor_id: str, db: AsyncSession= Depends(get_db)):
    s = await db.get(Sensor, sensor_id)
    if not s: 
        raise HTTPException(status_code=404, detail="Sensor ne postoji")
    return SensorOut.model_validate(s.__dict__)



@app.post("/data", response_model=SensorDataOut, status_code=201)
async def write_data(payload: SensorDataIn, db: AsyncSession= Depends(get_db)):
    s = await db.get(Sensor, payload.sensor_id)

    if not s:
        raise HTTPException(status_code=404, detail="Senzor ne postoji")
    

    sd = SensorData(
        sensor_id= payload.sensor_id, 
        temperature= payload.temperature,
        aqi = payload.aqi,
        timestamp = payload.timestamp,
    )

    db.add(sd)
    await db.commit()
    await db.refresh(sd)


    return SensorDataOut(
        id= sd.id, 
        sensor_id=sd.sensor_id,
        temperature=sd.temperature,
        aqi=sd.aqi,
        timestamp=sd.timestamp,
    )


@app.get("/data", response_model=List[SensorDataOut])
async def read_data(sensor_id: str = Query(...), limit: int = Query(100, ge=1, le= 1000), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(SensorData)
        .where(SensorData.sensor_id == sensor_id)
        .order_by(desc(SensorData.timestamp))
        .limit(limit)
        )
    
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
    return [
        SensorDataOut(
            id=r.id, sensor_id=r.sensor_id, temperature=r.temperature, aqi=r.aqi, timestamp=r.timestamp
        )
        for r in rows
    ]

