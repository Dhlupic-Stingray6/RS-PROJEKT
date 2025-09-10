from fastapi import FastAPI, HTTPException
from typing import Dict, List
from datetime import datetime, timedelta
import asyncio
import aiohttp
import os

from models import SensorStats, AggregatedStats, TrendAnalysis, ProcessingStatus
from services import StorageClient, StatisticsCalculator

app = FastAPI(
    title="Processing Service",
    description="Servis za statističku obradu podataka senzora",
    version="2.0.0"
)

# Konfiguracija
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8001")
PROCESSING_INTERVAL = int(os.getenv("PROCESSING_INTERVAL", "60"))

# Globalne varijable
client_session: aiohttp.ClientSession = None
storage_client: StorageClient = None
processing_task = None
stats_cache: Dict[str, SensorStats] = {}
last_processing_time: datetime = None
next_processing_time: datetime = None

@app.on_event("startup")
async def startup_event():
    global client_session, storage_client, processing_task, next_processing_time
    
    client_session = aiohttp.ClientSession()
    storage_client = StorageClient(STORAGE_SERVICE_URL, client_session)
    
    # Pokreni background processing
    processing_task = asyncio.create_task(periodic_processing())
    next_processing_time = datetime.utcnow() + timedelta(seconds=PROCESSING_INTERVAL)
    
    print(f" Processing Service started (port 8003)")
    print(f" Interval: {PROCESSING_INTERVAL}s")

@app.on_event("shutdown")
async def shutdown_event():
    if processing_task:
        processing_task.cancel()
    if client_session:
        await client_session.close()

async def process_all_sensors():
    """Glavni processing logic"""
    global stats_cache, last_processing_time, next_processing_time
    
    sensors = await storage_client.get_sensors()
    if not sensors:
        return
    
    print(f" Processing {len(sensors)} sensors...")
    
    for sensor in sensors:
        sensor_id = sensor["id"]
        data = await storage_client.get_sensor_data(sensor_id)
        
        if data:
            stats = StatisticsCalculator.calculate(sensor_id, data)
            if stats:
                stats_cache[sensor_id] = stats
                print(f" {sensor_id}: {stats.data_points} points")
    
    last_processing_time = datetime.utcnow()
    next_processing_time = last_processing_time + timedelta(seconds=PROCESSING_INTERVAL)

async def periodic_processing():
    """Background task"""
    while True:
        try:
            await process_all_sensors()
        except Exception as e:
            print(f" Error: {e}")
        
        await asyncio.sleep(PROCESSING_INTERVAL)

# Endpoints
@app.get("/health")
async def health():
    storage_healthy = await storage_client.check_health() if storage_client else False
    
    return {
        "status": "healthy",
        "storage_connection": storage_healthy,
        "cached_sensors": len(stats_cache),
        "last_processing": last_processing_time,
        "next_processing": next_processing_time
    }

@app.get("/stats", response_model=List[SensorStats])
async def get_all_stats():
    if not stats_cache:
        raise HTTPException(404, "Nema statistika. Pričekajte processing...")
    return list(stats_cache.values())

@app.get("/stats/aggregated", response_model=AggregatedStats)
async def get_aggregated():
    if not stats_cache:
        raise HTTPException(404, "Nema podataka")
    
    all_temps = [s.temperature_avg for s in stats_cache.values()]
    all_aqis = [s.aqi_avg for s in stats_cache.values()]
    total_points = sum(s.data_points for s in stats_cache.values())
    
    return AggregatedStats(
        total_sensors=len(stats_cache),
        total_data_points=total_points,
        global_temp_avg=sum(all_temps) / len(all_temps) if all_temps else 0,
        global_aqi_avg=sum(all_aqis) / len(all_aqis) if all_aqis else 0,
        sensors=list(stats_cache.values())
    )


@app.get("/stats/{sensor_id}", response_model=SensorStats)
async def get_sensor_stats(sensor_id: str):
    if sensor_id not in stats_cache:
        raise HTTPException(404, f"Nema statistike za {sensor_id}")
    return stats_cache[sensor_id]

@app.post("/process", response_model=ProcessingStatus)
async def trigger_processing():
    await process_all_sensors()
    return ProcessingStatus(
        status="completed",
        processed_sensors=len(stats_cache),
        timestamp=datetime.utcnow(),
        next_run=next_processing_time
    )


@app.get("/trends/{sensor_id}", response_model=TrendAnalysis)
async def get_trend(sensor_id: str):
    if sensor_id not in stats_cache:
        raise HTTPException(404, f"Nema podataka za {sensor_id}")
    
    stats = stats_cache[sensor_id]
    trend = StatisticsCalculator.analyze_trend(stats)
    aqi_status = StatisticsCalculator.classify_aqi(stats.aqi_avg)
    
    recommendations = {
        "good": "Kvaliteta zraka je odlična.",
        "moderate": "Kvaliteta zraka je prihvatljiva.",
        "unhealthy": "Preporučuje se izbjegavanje aktivnosti vani.",
        "hazardous": "Opasno! Ostanite unutra."
    }
    
    return TrendAnalysis(
        sensor_id=sensor_id,
        temperature_trend=trend,
        aqi_status=aqi_status,
        recommendation=recommendations.get(aqi_status, ""),
        last_analysis=stats.last_updated
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=True)


