import aiohttp
import random
import math
from datetime import datetime
from typing import List, Dict, Optional
from models import Location, SensorConfig

class WeatherSimulator:
    """Simulacija vremenskih uvjeta"""
    
    @staticmethod
    def get_time_factor() -> float:
        """Faktor vremena u danu (jutro hladno, popodne toplo)"""
        hour = datetime.now().hour
        # Sinusni val za temperaturu tijekom dana
        return math.sin((hour - 6) * math.pi / 12) * 5 if 6 <= hour <= 18 else -2
    
    @staticmethod
    def get_seasonal_factor() -> float:
        """Sezonski faktor za temperaturu"""
        month = datetime.now().month
        season_factors = {
            12: -10, 1: -12, 2: -8,   # Zima
            3: -2, 4: 5, 5: 10,        # Proljeće
            6: 15, 7: 20, 8: 18,       # Ljeto
            9: 10, 10: 5, 11: 0        # Jesen
        }
        return season_factors.get(month, 0)
    
    @staticmethod
    def get_random_variation() -> float:
        """Nasumična varijacija"""
        return random.gauss(0, 1.5)

class DataGenerator:
    """Generator realističnih podataka za senzore"""
    
    def __init__(self):
        self.sensor_states = {}  
    
    def generate_temperature(self, sensor: SensorConfig) -> float:
        """Generiraj realističnu temperaturu"""
        base = sensor.location.base_temp
        time_factor = WeatherSimulator.get_time_factor()
        seasonal = WeatherSimulator.get_seasonal_factor()
        variation = WeatherSimulator.get_random_variation()
        
        
        if sensor.sensor_id in self.sensor_states:
            last_temp = self.sensor_states[sensor.sensor_id].get('temperature', base)
            
            new_temp = 0.8 * last_temp + 0.2 * (base + time_factor + seasonal + variation)
        else:
            new_temp = base + time_factor + seasonal + variation
        
       
        if sensor.location.is_urban:
            new_temp += 1.5
        
       
        return round(max(-20, min(45, new_temp)), 2)
    
    def generate_aqi(self, sensor: SensorConfig) -> float:
        """Generiraj realistični AQI"""
        base = sensor.location.base_aqi
        hour = datetime.now().hour
        
        
        traffic_factor = 0
        if 7 <= hour <= 9 or 16 <= hour <= 19: 
            traffic_factor = 30 if sensor.location.is_urban else 10
        elif 10 <= hour <= 16:
            traffic_factor = 15 if sensor.location.is_urban else 5
        
        
        random_event = random.random()
        if random_event < 0.05:  
            traffic_factor += random.uniform(20, 50)
        
        variation = random.gauss(0, 5)
        
        
        if sensor.sensor_id in self.sensor_states:
            last_aqi = self.sensor_states[sensor.sensor_id].get('aqi', base)
            new_aqi = 0.7 * last_aqi + 0.3 * (base + traffic_factor + variation)
        else:
            new_aqi = base + traffic_factor + variation
        
        return round(max(0, min(300, new_aqi)), 2)
    
    def generate_data(self, sensor: SensorConfig) -> Dict:
        """Generiraj podatke za senzor"""
        temp = self.generate_temperature(sensor)
        aqi = self.generate_aqi(sensor)
        
        # Save state
        self.sensor_states[sensor.sensor_id] = {
            'temperature': temp,
            'aqi': aqi,
            'timestamp': datetime.utcnow()
        }
        
        return {
            'sensor_id': sensor.sensor_id,
            'temperature': temp,
            'aqi': aqi,
            'timestamp': datetime.utcnow().timestamp()
        }

class SensorRegistrar:
    """Registracija senzora u Storage servisu"""
    
    @staticmethod
    async def register_sensor(
        session: aiohttp.ClientSession,
        storage_url: str,
        sensor: SensorConfig
    ) -> bool:
        """Registriraj senzor u storage servisu"""
        payload = {
            'id': sensor.sensor_id,
            'name': sensor.name,
            'location': sensor.location.city
        }
        
        try:
            async with session.post(f"{storage_url}/sensors", json=payload) as resp:
                if resp.status in [200, 201]:
                    print(f" Registered: {sensor.sensor_id} ({sensor.location.city})")
                    return True
                elif resp.status == 400:
                    print(f"ℹ Already exists: {sensor.sensor_id}")
                    return True
                else:
                    print(f" Failed to register {sensor.sensor_id}: {resp.status}")
                    return False
        except Exception as e:
            print(f" Error registering {sensor.sensor_id}: {e}")
            return False
