import asyncio
import aiohttp
import os
from typing import List, Dict, Optional
from datetime import datetime

from models import Location, SensorConfig, SimulatorConfig
from services import DataGenerator, SensorRegistrar

# Hrvatske lokacije za simulaciju
CROATIAN_LOCATIONS = [
    Location(city="Zagreb-Maksimir", latitude=45.8240, longitude=16.0170, base_temp=11, base_aqi=30, is_urban=True),
    Location(city="Zagreb-Sljeme", latitude=45.9089, longitude=15.9667, base_temp=7, base_aqi=20, is_urban=False),
    Location(city="Split", latitude=43.5081, longitude=16.4402, base_temp=16, base_aqi=35, is_urban=True),
    Location(city="Rijeka", latitude=45.3271, longitude=14.4422, base_temp=14, base_aqi=40, is_urban=True),
    Location(city="Osijek", latitude=45.5550, longitude=18.6955, base_temp=11, base_aqi=38, is_urban=True),
    Location(city="Zadar", latitude=44.1194, longitude=15.2314, base_temp=15, base_aqi=30, is_urban=False),
    Location(city="Pula", latitude=44.8666, longitude=13.8496, base_temp=14, base_aqi=32, is_urban=False),
    Location(city="Varaždin", latitude=46.3044, longitude=16.3378, base_temp=10, base_aqi=35, is_urban=False),
    Location(city="Dubrovnik", latitude=42.6507, longitude=18.0944, base_temp=17, base_aqi=25, is_urban=False),
    Location(city="Karlovac", latitude=45.4929, longitude=15.5553, base_temp=11, base_aqi=33, is_urban=False),
]

class Simulator:
    def __init__(self, config: SimulatorConfig):
        self.config = config
        self.sensors: List[SensorConfig] = []
        self.data_generator = DataGenerator()
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = True
        self.stats = {
            'sent': 0,
            'failed': 0,
            'start_time': datetime.utcnow()
        }
    
    def create_sensors(self):
        """Stvori konfiguracije senzora"""
        for i in range(self.config.sensor_count):
            location = CROATIAN_LOCATIONS[i % len(CROATIAN_LOCATIONS)]
            sensor = SensorConfig(
                sensor_id=f"SIM-{i+1:03d}",
                name=f"Simulator {location.city}",
                location=location
            )
            self.sensors.append(sensor)
    
    async def setup(self):
        """Inicijalizacija"""
        self.session = aiohttp.ClientSession()
        self.create_sensors()
        
        # Registriraj senzore
        print(f" Registering {len(self.sensors)} sensors...")
        for sensor in self.sensors:
            await SensorRegistrar.register_sensor(
                self.session,
                self.config.storage_url,
                sensor
            )
    
    async def send_data(self, data: Dict) -> bool:
        """Pošalji podatke na Collector servis"""
        try:
            async with self.session.post(
                f"{self.config.collector_url}/ingest",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    self.stats['sent'] += 1
                    return True
                else:
                    self.stats['failed'] += 1
                    return False
        except Exception as e:
            self.stats['failed'] += 1
            print(f" Error sending data: {e}")
            return False
    
    async def simulate_sensor(self, sensor: SensorConfig):
        """Simuliraj jedan senzor"""
        data = self.data_generator.generate_data(sensor)
        success = await self.send_data(data)
        
        if success:
            print(f" {sensor.sensor_id}: T={data['temperature']}°C, AQI={data['aqi']}")
        
        return success
    
    async def run(self):
        """Glavna petlja simulacije"""
        await self.setup()
        
        print(f"\n Starting simulation")
        print(f"Sensors: {self.config.sensor_count}")
        print(f" Interval: {self.config.interval_seconds}s")
        print("-" * 50)
        
        while self.running:
            
            tasks = [self.simulate_sensor(sensor) for sensor in self.sensors]
            results = await asyncio.gather(*tasks)
            
            success_count = sum(1 for r in results if r)
            print(f" Sent: {success_count}/{len(self.sensors)} | Total: {self.stats['sent']}")
            
            await asyncio.sleep(self.config.interval_seconds)
    
    async def stop(self):
        """Zaustavi simulaciju"""
        self.running = False
        if self.session:
            await self.session.close()
        
        
        runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        print(f"\n statistika:")
        print(f"  Runtime: {runtime:.1f}s")
        print(f"  Sent: {self.stats['sent']}")
        print(f"  Failed: {self.stats['failed']}")
        print(f"  Rate: {self.stats['sent']/runtime:.2f} msg/s")

async def main():
    config = SimulatorConfig(
        sensor_count=int(os.getenv("SENSOR_COUNT", "5")),
        interval_seconds=int(os.getenv("INTERVAL_SECONDS", "10")),
        collector_url=os.getenv("COLLECTOR_URL", "http://localhost:8002"),
        storage_url=os.getenv("STORAGE_URL", "http://localhost:8001")
    )
    
    simulator = Simulator(config)
    
    try:
        await simulator.run()
    except KeyboardInterrupt:
        print("\n Stopping simulation...")
        await simulator.stop()

if __name__ == "__main__":
    asyncio.run(main())