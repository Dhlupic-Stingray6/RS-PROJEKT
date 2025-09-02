import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import statistics
from models import SensorStats

class StorageClient:
    """Klijent za komunikaciju sa Storage servisom"""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
    
    async def get_sensors(self) -> List[Dict]:
        """Dohvati sve senzore"""
        try:
            async with self.session.get(f"{self.base_url}/sensors") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            print(f"Error fetching sensors: {e}")
            return []
    
    async def get_sensor_data(self, sensor_id: str, limit: int = 100) -> List[Dict]:
        """Dohvati podatke za senzor"""
        try:
            async with self.session.get(
                f"{self.base_url}/data",
                params={"sensor_id": sensor_id, "limit": limit}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            print(f"Error fetching data for {sensor_id}: {e}")
            return []
    
    async def check_health(self) -> bool:
        """Provjeri health storage servisa"""
        try:
            async with self.session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                return resp.status == 200
        except:
            return False

class StatisticsCalculator:
    """Kalkulator za statističke podatke"""
    
    @staticmethod
    def calculate(sensor_id: str, data_points: List[Dict]) -> Optional[SensorStats]:
        """Izračunaj statistiku iz podataka"""
        if not data_points:
            return None
        
        temperatures = []
        aqis = []
        timestamps = []
        
        for point in data_points:
            if "temperature" in point:
                temperatures.append(point["temperature"])
            if "aqi" in point:
                aqis.append(point["aqi"])
            if "timestamp" in point:
                ts = point["timestamp"]
                if isinstance(ts, str):
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                elif isinstance(ts, (int, float)):
                    timestamps.append(datetime.fromtimestamp(ts))
        
        if not temperatures or not aqis:
            return None
        
        period_start = min(timestamps) if timestamps else datetime.utcnow()
        period_end = max(timestamps) if timestamps else datetime.utcnow()
        
        return SensorStats(
            sensor_id=sensor_id,
            period_start=period_start,
            period_end=period_end,
            data_points=len(data_points),
            temperature_min=min(temperatures),
            temperature_max=max(temperatures),
            temperature_avg=round(statistics.mean(temperatures), 2),
            temperature_std=round(statistics.stdev(temperatures), 2) if len(temperatures) > 1 else None,
            aqi_min=min(aqis),
            aqi_max=max(aqis),
            aqi_avg=round(statistics.mean(aqis), 2),
            aqi_std=round(statistics.stdev(aqis), 2) if len(aqis) > 1 else None
        )
    
    @staticmethod
    def analyze_trend(stats: SensorStats) -> str:
        """Analiziraj trend temperature"""
        if not stats.temperature_std:
            return "stable"
        if stats.temperature_std > 3:
            return "variable"
        if stats.temperature_std < 1:
            return "stable"
        return "moderate"
    
    @staticmethod
    def classify_aqi(aqi: float) -> str:
        """Klasificiraj kvalitetu zraka"""
        if aqi < 50:
            return "good"
        elif aqi < 100:
            return "moderate"
        elif aqi < 200:
            return "unhealthy"
        else:
            return "hazardous"
