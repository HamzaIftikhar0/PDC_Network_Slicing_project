from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uvicorn
import aiohttp
from enum import Enum
import uuid
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimulationStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"

class Simulation:
    def __init__(self, simulation_id: str, config: dict):
        self.simulation_id = simulation_id
        self.config = config
        self.status = SimulationStatus.INITIALIZED
        self.start_time = None
        self.end_time = None
        self.total_traffic_generated = 0
        self.total_packets_processed = 0
        self.total_packets_dropped = 0
        self.slice_metrics = {"embb": {}, "urllc": {}, "mmtc": {}}
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

class SimulationManager:
    def __init__(self):
        self.simulations: Dict[str, Simulation] = {}
        self.active_tasks = set()
    
    async def create_simulation(self, config: dict) -> Simulation:
        sim_id = f"sim_{uuid.uuid4().hex[:12]}"
        simulation = Simulation(sim_id, config)
        self.simulations[sim_id] = simulation
        logger.info(f"Created simulation: {sim_id}")
        return simulation
    
    async def get_simulation(self, sim_id: str) -> Optional[Simulation]:
        return self.simulations.get(sim_id)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
    
    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        self.active_connections[simulation_id].append(websocket)
        logger.info(f"Client connected to {simulation_id}")
    
    async def disconnect(self, websocket: WebSocket, simulation_id: str):
        if websocket in self.active_connections.get(simulation_id, []):
            self.active_connections[simulation_id].remove(websocket)
    
    async def broadcast_to_simulation(self, simulation_id: str, message: dict):
        disconnected = []
        connections = self.active_connections.get(simulation_id, [])[:]
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Send error: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            await self.disconnect(conn, simulation_id)

sim_manager = SimulationManager()
conn_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend starting")
    yield
    logger.info("Backend shutting down")

app = FastAPI(title="5G Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/simulation/create")
async def create_simulation(config: dict):
    try:
        if not config.get("traffic_volume") or not config.get("duration"):
            raise ValueError("traffic_volume and duration required")
        
        simulation = await sim_manager.create_simulation(config)
        return {"simulation_id": simulation.simulation_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/{simulation_id}/start")
async def start_simulation(simulation_id: str):
    try:
        simulation = await sim_manager.get_simulation(simulation_id)
        if not simulation:
            raise HTTPException(status_code=404, detail="Not found")
        
        simulation.status = SimulationStatus.RUNNING
        simulation.start_time = datetime.now()
        
        task = asyncio.create_task(run_simulation_loop(simulation_id))
        sim_manager.active_tasks.add(task)
        task.add_done_callback(sim_manager.active_tasks.discard)
        
        return {"simulation_id": simulation_id, "status": "started"}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

@app.post("/simulation/{simulation_id}/stop")
async def stop_simulation(simulation_id: str):
    simulation = await sim_manager.get_simulation(simulation_id)
    if simulation:
        simulation.status = SimulationStatus.STOPPED
        simulation.end_time = datetime.now()
    return {"status": "stopped"}

@app.websocket("/ws/metrics/{simulation_id}")
async def websocket_metrics(websocket: WebSocket, simulation_id: str):
    await conn_manager.connect(websocket, simulation_id)
    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        await conn_manager.disconnect(websocket, simulation_id)

async def run_simulation_loop(simulation_id: str):
    """Main simulation loop"""
    try:
        simulation = await sim_manager.get_simulation(simulation_id)
        if not simulation:
            return
        
        duration = simulation.config.get("duration", 60)
        traffic_volume = simulation.config.get("traffic_volume", 1000)
        
        end_time = datetime.now() + timedelta(seconds=duration)
        
        async with aiohttp.ClientSession() as session:
            while datetime.now() < end_time and simulation.status == SimulationStatus.RUNNING:
                try:
                    # Traffic per cycle
                    traffic_per_cycle = int(traffic_volume / duration)
                    simulation.total_traffic_generated += traffic_per_cycle
                    
                    # Get metrics from all slices in parallel
                    tasks = [
                        process_slice_traffic(session, "embb", 8101, traffic_per_cycle // 3),
                        process_slice_traffic(session, "urllc", 8102, traffic_per_cycle // 3),
                        process_slice_traffic(session, "mmtc", 8103, traffic_per_cycle // 3)
                    ]
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Error: {result}")
                            continue
                        
                        if result:
                            slice_type = result.get("slice_type")
                            
                            # Update totals
                            simulation.total_packets_processed += result.get("packets_processed", 0)
                            simulation.total_packets_dropped += result.get("packets_dropped", 0)
                            
                            # Store slice metrics
                            simulation.slice_metrics[slice_type] = result
                    
                    # Send to frontend
                    metrics_data = {
                        "type": "metrics_update",
                        "data": {
                            "timestamp": datetime.now().isoformat(),
                            "total_traffic_generated": simulation.total_traffic_generated,
                            "total_packets_processed": simulation.total_packets_processed,
                            "total_packets_dropped": simulation.total_packets_dropped,
                            "slice_metrics": simulation.slice_metrics
                        }
                    }
                    
                    await conn_manager.broadcast_to_simulation(simulation_id, metrics_data)
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Loop error: {e}")
                    await asyncio.sleep(1)
        
        simulation.status = SimulationStatus.COMPLETED
        simulation.end_time = datetime.now()
        logger.info(f"Simulation {simulation_id} completed")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")

async def process_slice_traffic(session, slice_type: str, port: int, packet_count: int):
    """Get metrics from slice"""
    try:
        url = f"http://localhost:{port}/process"
        async with session.post(url, json={"packet_count": packet_count}, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["slice_type"] = slice_type
                return data
    except Exception as e:
        logger.error(f"Error from {slice_type}: {e}")
    return None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")