import aiohttp
from typing import Optional, Dict
from datetime import datetime
from models import SensorData

class StorageClient:
    """Klijent za komunikaciju sa Storage servisom"""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
    
    async def check_sensor_exists(self, sensor_id: str) -> bool:
        """Provjeri postoji li senzor u storage servisu"""
        try:
            url = f"{self.base_url}/sensors/{sensor_id}"
            async with self.session.get(url) as response:
                return response.status == 200
        except aiohttp.ClientError as e:
            print(f"Error checking sensor {sensor_id}: {e}")
            raise
    
    async def store_data(self, data: SensorData) -> Dict:
        """Pošalji podatke na storage servis"""
        storage_data = {
            "sensor_id": data.sensor_id,
            "temperature": data.temperature,
            "aqi": data.aqi,
            "timestamp": datetime.fromtimestamp(data.timestamp).isoformat() if data.timestamp else None
        }
        
        try:
            url = f"{self.base_url}/data"
            async with self.session.post(url, json=storage_data) as response:
                if response.status not in [200, 201]:
                    text = await response.text()
                    raise Exception(f"Storage returned {response.status}: {text}")
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error storing data: {e}")
            raise
    
    async def check_health(self) -> bool:
        """Provjeri health storage servisa"""
        try:
            url = f"{self.base_url}/health"
            async with self.session.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except:
            return False

class DataValidator:
    """Validator za dodatne provjere podataka"""
    
    @staticmethod
    def validate_data_consistency(data: SensorData) -> bool:
        """Provjeri konzistentnost podataka"""
        # Provjeri da li su temperatura i AQI u logičnoj korelaciji
        # Npr. visoka temperatura ljeti može biti povezana s višim AQI
        if data.temperature == 0 and data.aqi == 0:
            # Možda je greška u očitanju
            return False
        
        # Provjeri timestamp
        if data.timestamp:
            current_time = datetime.utcnow().timestamp()
            # Podatak ne smije biti iz budućnosti
            if data.timestamp > current_time:
                return False
            # Podatak ne smije biti stariji od 24h
            if current_time - data.timestamp > 86400:
                return False
        
        if data.temperature < -20 or data.temperature > 50:
            return False

        if data.aqi < 0 or data.aqi > 300:
            return False

        return True