"""
5G Network Slice Simulator - Backend API
Main application file with all endpoints
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, Query
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
import csv
import json
from io import StringIO, BytesIO

# Import database and models
from database import get_db, init_db, test_db_connection, SessionLocal
from models import Simulation as SimulationModel, Metrics as MetricsModel, SliceMetrics as SliceMetricsModel
from schemas import (
    SimulationCreateRequest, SimulationResponse, SimulationHistoryResponse,
    MetricsCreateRequest, MetricsResponse, MetricsHistoryResponse,
    SliceMetricsCreateRequest, SliceMetricsResponse, SliceMetricsHistoryResponse,
    ExportRequest, ExportResponse, ErrorResponse, HealthCheckResponse
)
from config import config
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== ENUMS =====================

class SimulationStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"

# ===================== IN-MEMORY CLASSES =====================

class Simulation:
    """In-memory simulation object"""
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
    """Manages active simulations"""
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
    """Manages WebSocket connections"""
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

# ===================== INITIALIZE MANAGERS =====================

sim_manager = SimulationManager()
conn_manager = ConnectionManager()

# ===================== LIFESPAN EVENT =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Backend starting...")
    
    # Initialize database on startup
    db_ready = init_db()
    if db_ready:
        logger.info("Database initialized successfully")
    else:
        logger.error("Failed to initialize database")
    
    # Test database connection
    if test_db_connection():
        logger.info("Database connection verified")
    else:
        logger.warning("Database connection failed")
    
    yield
    
    logger.info("Backend shutting down")

# ===================== FASTAPI APP SETUP =====================

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_CREDENTIALS,
    allow_methods=config.CORS_METHODS,
    allow_headers=config.CORS_HEADERS
)

# ===================== HEALTH CHECK ENDPOINTS =====================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """Check if backend is healthy"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_connected = True
    except:
        db_connected = False
    
    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        timestamp=datetime.now()
    )

# ===================== SIMULATION ENDPOINTS =====================

@app.post("/simulation/create", response_model=SimulationResponse)
async def create_simulation(
    request: SimulationCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new simulation"""
    try:
        logger.info(f"Creating simulation with config: {request.dict()}")
        
        # Create in-memory simulation
        config_dict = request.dict()
        simulation = await sim_manager.create_simulation(config_dict)
        
        # Save to database
        db_simulation = SimulationModel(
            simulation_id=simulation.simulation_id,
            traffic_volume=request.traffic_volume,
            duration=request.duration,
            pattern=request.pattern,
            status=SimulationStatus.INITIALIZED.value,
            created_at=datetime.now()
        )
        db.add(db_simulation)
        db.commit()
        db.refresh(db_simulation)
        
        logger.info(f"Simulation {simulation.simulation_id} created successfully")
        
        return SimulationResponse.from_orm(db_simulation)
    
    except Exception as e:
        logger.error(f"Error creating simulation: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/{simulation_id}/start", response_model=SimulationResponse)
async def start_simulation(
    simulation_id: str,
    db: Session = Depends(get_db)
):
    """Start a simulation"""
    try:
        simulation = await sim_manager.get_simulation(simulation_id)
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        simulation.status = SimulationStatus.RUNNING
        simulation.start_time = datetime.now()
        
        # Update in database
        db_sim = db.query(SimulationModel).filter_by(simulation_id=simulation_id).first()
        if db_sim:
            db_sim.status = SimulationStatus.RUNNING.value
            db_sim.start_time = datetime.now()
            db.commit()
        
        # Start simulation task
        task = asyncio.create_task(run_simulation_loop(simulation_id, db))
        sim_manager.active_tasks.add(task)
        task.add_done_callback(sim_manager.active_tasks.discard)
        
        logger.info(f"Simulation {simulation_id} started")
        return SimulationResponse.from_orm(db_sim)
    
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise

@app.post("/simulation/{simulation_id}/stop", response_model=SimulationResponse)
async def stop_simulation(
    simulation_id: str,
    db: Session = Depends(get_db)
):
    """Stop a running simulation"""
    try:
        simulation = await sim_manager.get_simulation(simulation_id)
        if simulation:
            simulation.status = SimulationStatus.STOPPED
            simulation.end_time = datetime.now()
        
        # Update in database
        db_sim = db.query(SimulationModel).filter_by(simulation_id=simulation_id).first()
        if db_sim:
            db_sim.status = SimulationStatus.STOPPED.value
            db_sim.end_time = datetime.now()
            db_sim.total_packets_processed = simulation.total_packets_processed
            db_sim.total_packets_dropped = simulation.total_packets_dropped
            db_sim.total_traffic_generated = simulation.total_traffic_generated
            db.commit()
        
        logger.info(f"Simulation {simulation_id} stopped")
        return SimulationResponse.from_orm(db_sim)
    
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/simulation/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: str,
    db: Session = Depends(get_db)
):
    """Get simulation details"""
    try:
        db_sim = db.query(SimulationModel).filter_by(simulation_id=simulation_id).first()
        if not db_sim:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return SimulationResponse.from_orm(db_sim)
    
    except Exception as e:
        logger.error(f"Error fetching simulation: {e}")
        raise

@app.get("/simulations/history", response_model=SimulationHistoryResponse)
async def get_simulation_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get simulation history with pagination"""
    try:
        query = db.query(SimulationModel).order_by(desc(SimulationModel.created_at))
        
        if status:
            query = query.filter_by(status=status)
        
        total_count = query.count()
        simulations = query.limit(limit).offset(offset).all()
        
        return SimulationHistoryResponse(
            simulations=[SimulationResponse.from_orm(sim) for sim in simulations],
            total_count=total_count
        )
    
    except Exception as e:
        logger.error(f"Error fetching simulation history: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ===================== METRICS ENDPOINTS =====================

@app.post("/metrics/save", response_model=MetricsResponse)
async def save_metrics(
    request: MetricsCreateRequest,
    db: Session = Depends(get_db)
):
    """Save metrics to database"""
    try:
        db_metrics = MetricsModel(
            simulation_id=request.simulation_id,
            timestamp=datetime.now(),
            total_packets_processed=request.total_packets_processed,
            total_packets_dropped=request.total_packets_dropped,
            success_rate=request.success_rate,
            embb_latency=request.embb_latency,
            urllc_latency=request.urllc_latency,
            mmtc_latency=request.mmtc_latency,
            embb_throughput=request.embb_throughput,
            urllc_reliability=request.urllc_reliability,
            mmtc_devices=request.mmtc_devices
        )
        db.add(db_metrics)
        db.commit()
        db.refresh(db_metrics)
        
        return MetricsResponse.from_orm(db_metrics)
    
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/metrics/{simulation_id}", response_model=MetricsHistoryResponse)
async def get_simulation_metrics(
    simulation_id: str,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get metrics history for a simulation"""
    try:
        query = db.query(MetricsModel).filter_by(simulation_id=simulation_id).order_by(MetricsModel.timestamp)
        
        total_count = query.count()
        metrics = query.limit(limit).offset(offset).all()
        
        return MetricsHistoryResponse(
            metrics=[MetricsResponse.from_orm(m) for m in metrics],
            total_count=total_count
        )
    
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ===================== SLICE METRICS ENDPOINTS =====================

@app.post("/slice-metrics/save", response_model=SliceMetricsResponse)
async def save_slice_metrics(
    request: SliceMetricsCreateRequest,
    db: Session = Depends(get_db)
):
    """Save slice metrics to database"""
    try:
        db_slice_metrics = SliceMetricsModel(
            simulation_id=request.simulation_id,
            slice_type=request.slice_type,
            timestamp=datetime.now(),
            latency_avg=request.latency_avg,
            latency_min=request.latency_min,
            latency_max=request.latency_max,
            throughput_avg=request.throughput_avg,
            drop_rate=request.drop_rate,
            qos_compliance=request.qos_compliance,
            queue_length=request.queue_length,
            packets_processed=request.packets_processed,
            packets_dropped=request.packets_dropped
        )
        db.add(db_slice_metrics)
        db.commit()
        db.refresh(db_slice_metrics)
        
        return SliceMetricsResponse.from_orm(db_slice_metrics)
    
    except Exception as e:
        logger.error(f"Error saving slice metrics: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/slice-metrics/{simulation_id}/{slice_type}", response_model=SliceMetricsHistoryResponse)
async def get_slice_metrics(
    simulation_id: str,
    slice_type: str,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get slice metrics history"""
    try:
        query = db.query(SliceMetricsModel).filter(
            and_(
                SliceMetricsModel.simulation_id == simulation_id,
                SliceMetricsModel.slice_type == slice_type
            )
        ).order_by(SliceMetricsModel.timestamp)
        
        total_count = query.count()
        metrics = query.limit(limit).offset(offset).all()
        
        return SliceMetricsHistoryResponse(
            slice_metrics=[SliceMetricsResponse.from_orm(m) for m in metrics],
            total_count=total_count
        )
    
    except Exception as e:
        logger.error(f"Error fetching slice metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ===================== EXPORT ENDPOINTS =====================

@app.post("/export", response_model=ExportResponse)
async def export_simulation(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export simulation data"""
    try:
        # Get simulation
        sim = db.query(SimulationModel).filter_by(simulation_id=request.simulation_id).first()
        if not sim:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        if request.format == "csv":
            return await export_as_csv(request.simulation_id, db)
        elif request.format == "json":
            return await export_as_json(request.simulation_id, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
    
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=400, detail=str(e))

async def export_as_csv(simulation_id: str, db: Session):
    """Export data as CSV"""
    try:
        output = StringIO()
        
        # Get metrics
        metrics = db.query(MetricsModel).filter_by(simulation_id=simulation_id).all()
        
        if metrics:
            writer = csv.DictWriter(output, fieldnames=[
                'timestamp', 'total_packets_processed', 'total_packets_dropped',
                'success_rate', 'embb_latency', 'urllc_latency', 'mmtc_latency'
            ])
            writer.writeheader()
            
            for metric in metrics:
                writer.writerow({
                    'timestamp': metric.timestamp.isoformat(),
                    'total_packets_processed': metric.total_packets_processed,
                    'total_packets_dropped': metric.total_packets_dropped,
                    'success_rate': metric.success_rate,
                    'embb_latency': metric.embb_latency,
                    'urllc_latency': metric.urllc_latency,
                    'mmtc_latency': metric.mmtc_latency
                })
        
        return ExportResponse(
            success=True,
            message="Export successful",
            file_name=f"{simulation_id}_export.csv"
        )
    
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return ExportResponse(success=False, message=str(e))

async def export_as_json(simulation_id: str, db: Session):
    """Export data as JSON"""
    try:
        sim = db.query(SimulationModel).filter_by(simulation_id=simulation_id).first()
        metrics = db.query(MetricsModel).filter_by(simulation_id=simulation_id).all()
        
        data = {
            "simulation": {
                "simulation_id": sim.simulation_id,
                "traffic_volume": sim.traffic_volume,
                "duration": sim.duration,
                "pattern": sim.pattern,
                "status": sim.status,
                "start_time": sim.start_time.isoformat() if sim.start_time else None,
                "end_time": sim.end_time.isoformat() if sim.end_time else None,
            },
            "metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "total_packets_processed": m.total_packets_processed,
                    "total_packets_dropped": m.total_packets_dropped,
                    "success_rate": m.success_rate,
                } for m in metrics
            ]
        }
        
        return ExportResponse(
            success=True,
            message="Export successful",
            file_name=f"{simulation_id}_export.json"
        )
    
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        return ExportResponse(success=False, message=str(e))

# ===================== WEBSOCKET ENDPOINT =====================

@app.websocket("/ws/metrics/{simulation_id}")
async def websocket_metrics(websocket: WebSocket, simulation_id: str):
    """WebSocket for real-time metrics updates"""
    await conn_manager.connect(websocket, simulation_id)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await conn_manager.disconnect(websocket, simulation_id)

# ===================== SIMULATION LOOP =====================

async def run_simulation_loop(simulation_id: str, db: Session):
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
                    
                    # Get metrics from all slices
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
                            simulation.total_packets_processed += result.get("packets_processed", 0)
                            simulation.total_packets_dropped += result.get("packets_dropped", 0)
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
        
        # Update in database
        db_sim = db.query(SimulationModel).filter_by(simulation_id=simulation_id).first()
        if db_sim:
            db_sim.status = SimulationStatus.COMPLETED.value
            db_sim.end_time = datetime.now()
            db_sim.total_packets_processed = simulation.total_packets_processed
            db_sim.total_packets_dropped = simulation.total_packets_dropped
            db_sim.total_traffic_generated = simulation.total_traffic_generated
            db.commit()
        
        logger.info(f"Simulation {simulation_id} completed")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")

async def process_slice_traffic(session, slice_type: str, port: int, packet_count: int):
    """Get metrics from slice"""
    try:
        # Generate packets for this slice
        packets = [
            {
                "packet_id": f"{slice_type}_{i}",
                "size": 100 + i % 200,
                "priority": 5 + i % 5
            }
            for i in range(packet_count)
        ]
        
        url = f"http://localhost:{port}/process"
        async with session.post(
            url, 
            json={"packet_count": packet_count, "packets": packets},  # Send actual packets
            timeout=aiohttp.ClientTimeout(total=3)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["slice_type"] = slice_type
                return data
    except Exception as e:
        logger.error(f"Error from {slice_type}: {e}")
    return None
# ===================== RUN SERVER =====================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        log_level=config.LOG_LEVEL.lower()
    )