from fastapi import FastAPI, HTTPException
from typing import Optional
import aiohttp
import os

from models import SensorData, IngestResponse, HealthResponse
from services import StorageClient, DataValidator

app = FastAPI(
    title="Collector Service",
    description="Async servis za prikupljanje podataka sa senzora",
    version="2.0.0"
)

# Konfiguracija
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8001")

# Globalne varijable
client_session: Optional[aiohttp.ClientSession] = None
storage_client: Optional[StorageClient] = None

@app.on_event("startup")
async def startup():
    global client_session, storage_client
    
    client_session = aiohttp.ClientSession()
    storage_client = StorageClient(STORAGE_SERVICE_URL, client_session)
    
    print(f"Collector Service started (port 8002)")
    print(f"Storage URL: {STORAGE_SERVICE_URL}")

@app.on_event("shutdown")
async def shutdown():
    global client_session
    
    if client_session:
        await client_session.close()
        print(" Collector Service stopped")

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    storage_connected = False
    
    if storage_client:
        storage_connected = await storage_client.check_health()
    
    return HealthResponse(
        status="healthy" if storage_connected else "degraded",
        service="collector",
        storage_connected=storage_connected,
        
    )

@app.post("/ingest", response_model=IngestResponse)
async def ingest(data: SensorData):
    """Glavni endpoint za primanje podataka sa senzora"""
    
    # Dodatna validacija
    if not DataValidator.validate_data_consistency(data):
        raise HTTPException(
            status_code=400,
            detail="Podaci nisu konzistentni ili su izvan dozvoljenog raspona"
        )
    
    # Provjeri postoji li senzor
    try:
        sensor_exists = await storage_client.check_sensor_exists(data.sensor_id)
        if not sensor_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Senzor {data.sensor_id} nije registriran. Prvo registrirajte senzor na storage servisu."
            )
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Storage servis nije dostupan: {str(e)}"
        )
    
    # Spremi podatke
    try:
        result = await storage_client.store_data(data)
        
        return IngestResponse(
            status="received and stored",
            sensor=data.sensor_id,
            data_id=result.get("id"),
            message="Podaci uspješno spremljeni"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Greška pri spremanju podataka: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint s informacijama o servisu"""
    return {
        "service": "Collector Service",
        "version": "2.0.0",
        "description": "Servis za prikupljanje podataka sa senzora",
        "endpoints": {
            "/health": "Health check",
            "/ingest": "Primanje podataka sa senzora",
            "/docs": "API dokumentacija"
        },
        "storage_url": STORAGE_SERVICE_URL
    }

@app.get("/stats")
async def get_stats():
    """Statistike o radu collector servisa"""
    
    return {
        "service": "Collector",
        "storage_connected": await storage_client.check_health() if storage_client else False,
        "configuration": {
            "storage_url": STORAGE_SERVICE_URL,
            "temperature_range": [-50, 100],
            "aqi_range": [0, 500],
            "max_data_age": "24 hours"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)


