from fastapi import FastAPI, HTTPException
from models import SensorData
import asyncio




app = FastAPI()


@app.post("/ingest")
async def ingest(data: SensorData):
    return {"status": "received", "sensor": data.sensor_id}