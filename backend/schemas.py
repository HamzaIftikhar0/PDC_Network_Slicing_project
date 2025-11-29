"""
Pydantic schemas for request/response validation
Validates all incoming data and defines API response formats
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from config import config

# ===================== SIMULATION SCHEMAS =====================

class SimulationCreateRequest(BaseModel):
    """Request schema for creating a new simulation"""
    traffic_volume: int = Field(..., ge=config.MIN_TRAFFIC_VOLUME, le=config.MAX_TRAFFIC_VOLUME)
    duration: int = Field(..., ge=config.MIN_DURATION, le=config.MAX_DURATION)
    pattern: str = Field(..., description="Traffic pattern type")
    
    @validator('pattern')
    def validate_pattern(cls, v):
        if v not in config.VALID_PATTERNS:
            raise ValueError(f"Pattern must be one of {config.VALID_PATTERNS}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "traffic_volume": 5000,
                "duration": 120,
                "pattern": "wave"
            }
        }

class SimulationResponse(BaseModel):
    """Response schema for simulation info"""
    id: int
    simulation_id: str
    traffic_volume: int
    duration: int
    pattern: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    total_traffic_generated: int
    total_packets_processed: int
    total_packets_dropped: int
    
    class Config:
        from_attributes = True

class SimulationHistoryResponse(BaseModel):
    """Response for simulation history list"""
    simulations: List[SimulationResponse]
    total_count: int
    
    class Config:
        from_attributes = True

# ===================== METRICS SCHEMAS =====================

class MetricsCreateRequest(BaseModel):
    """Request schema for saving metrics"""
    simulation_id: str
    total_packets_processed: int
    total_packets_dropped: int
    success_rate: float
    embb_latency: float
    urllc_latency: float
    mmtc_latency: float
    embb_throughput: float
    urllc_reliability: float
    mmtc_devices: int
    
    @validator('success_rate', 'embb_latency', 'urllc_latency', 'mmtc_latency', 'embb_throughput', 'urllc_reliability')
    def validate_float_range(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Must be a number")
        return float(v)
    
    class Config:
        schema_extra = {
            "example": {
                "simulation_id": "sim_abc123",
                "total_packets_processed": 5000,
                "total_packets_dropped": 50,
                "success_rate": 99.0,
                "embb_latency": 45.5,
                "urllc_latency": 5.2,
                "mmtc_latency": 250.0,
                "embb_throughput": 800.0,
                "urllc_reliability": 99.95,
                "mmtc_devices": 1000
            }
        }

class MetricsResponse(BaseModel):
    """Response schema for metrics"""
    id: int
    simulation_id: str
    timestamp: datetime
    total_packets_processed: int
    total_packets_dropped: int
    success_rate: float
    embb_latency: float
    urllc_latency: float
    mmtc_latency: float
    embb_throughput: float
    urllc_reliability: float
    mmtc_devices: int
    
    class Config:
        from_attributes = True

class MetricsHistoryResponse(BaseModel):
    """Response for metrics history"""
    metrics: List[MetricsResponse]
    total_count: int
    
    class Config:
        from_attributes = True

# ===================== SLICE METRICS SCHEMAS =====================

class SliceMetricsCreateRequest(BaseModel):
    """Request schema for slice metrics"""
    simulation_id: str
    slice_type: str = Field(..., description="embb, urllc, or mmtc")
    latency_avg: float
    latency_min: float
    latency_max: float
    throughput_avg: float
    drop_rate: float
    qos_compliance: float
    queue_length: int
    packets_processed: int = 0
    packets_dropped: int = 0
    
    @validator('slice_type')
    def validate_slice_type(cls, v):
        valid_slices = ["embb", "urllc", "mmtc"]
        if v not in valid_slices:
            raise ValueError(f"Slice type must be one of {valid_slices}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "simulation_id": "sim_abc123",
                "slice_type": "embb",
                "latency_avg": 45.5,
                "latency_min": 20.0,
                "latency_max": 80.0,
                "throughput_avg": 800.0,
                "drop_rate": 0.5,
                "qos_compliance": 98.5,
                "queue_length": 150,
                "packets_processed": 5000,
                "packets_dropped": 25
            }
        }

class SliceMetricsResponse(BaseModel):
    """Response schema for slice metrics"""
    id: int
    simulation_id: str
    slice_type: str
    timestamp: datetime
    latency_avg: float
    latency_min: float
    latency_max: float
    throughput_avg: float
    drop_rate: float
    qos_compliance: float
    queue_length: int
    packets_processed: int
    packets_dropped: int
    
    class Config:
        from_attributes = True

class SliceMetricsHistoryResponse(BaseModel):
    """Response for slice metrics history"""
    slice_metrics: List[SliceMetricsResponse]
    total_count: int
    
    class Config:
        from_attributes = True

# ===================== EXPORT SCHEMAS =====================

class ExportRequest(BaseModel):
    """Request schema for exporting data"""
    simulation_id: str
    format: str = Field(..., description="csv, json, or pdf")
    include_metrics: bool = True
    include_slice_metrics: bool = True
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ["csv", "json", "pdf"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of {valid_formats}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "simulation_id": "sim_abc123",
                "format": "csv",
                "include_metrics": True,
                "include_slice_metrics": True
            }
        }

class ExportResponse(BaseModel):
    """Response schema for export"""
    success: bool
    message: str
    file_name: Optional[str] = None
    download_url: Optional[str] = None

# ===================== ERROR SCHEMAS =====================

class ErrorResponse(BaseModel):
    """Response schema for errors"""
    success: bool = False
    error: str
    detail: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """Response schema for health check"""
    status: str
    database_connected: bool
    timestamp: datetime
    version: str = config.APP_VERSION