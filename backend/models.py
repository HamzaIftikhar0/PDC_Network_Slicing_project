"""
SQLAlchemy database models
These define the structure of tables in MySQL
SQLAlchemy will auto-create these tables
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Create base class for all models
Base = declarative_base()

class Simulation(Base):
    """
    Simulation table - stores information about each simulation run
    """
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(50), unique=True, nullable=False, index=True)
    traffic_volume = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    pattern = Column(String(50), nullable=False)
    status = Column(String(20), default="initialized", nullable=False, index=True)
    
    # Timestamps
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Final results
    total_traffic_generated = Column(Integer, default=0)
    total_packets_processed = Column(Integer, default=0)
    total_packets_dropped = Column(Integer, default=0)
    
    # Relationships
    metrics = relationship("Metrics", back_populates="simulation", cascade="all, delete-orphan")
    slice_metrics = relationship("SliceMetrics", back_populates="simulation", cascade="all, delete-orphan")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_simulation_status', 'status'),
        Index('idx_simulation_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Simulation {self.simulation_id}>"

class Metrics(Base):
    """
    Metrics table - stores real-time metrics data during simulation
    Each simulation has many metric records (one per second)
    """
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(50), ForeignKey('simulations.simulation_id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Overall metrics
    total_packets_processed = Column(Integer, default=0)
    total_packets_dropped = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Per-slice metrics
    embb_latency = Column(Float, default=0.0)
    urllc_latency = Column(Float, default=0.0)
    mmtc_latency = Column(Float, default=0.0)
    
    embb_throughput = Column(Float, default=0.0)
    urllc_reliability = Column(Float, default=0.0)
    mmtc_devices = Column(Integer, default=0)
    
    # Relationship
    simulation = relationship("Simulation", back_populates="metrics")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_metrics_simulation_time', 'simulation_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Metrics {self.simulation_id} @ {self.timestamp}>"

class SliceMetrics(Base):
    """
    SliceMetrics table - detailed metrics for each network slice
    Stores eMBB, URLLC, mMTC specific metrics
    """
    __tablename__ = "slice_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(50), ForeignKey('simulations.simulation_id'), nullable=False, index=True)
    slice_type = Column(String(20), nullable=False, index=True)  # embb, urllc, mmtc
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Latency metrics (in ms)
    latency_avg = Column(Float, default=0.0)
    latency_min = Column(Float, default=0.0)
    latency_max = Column(Float, default=0.0)
    
    # Throughput metrics (in Mbps)
    throughput_avg = Column(Float, default=0.0)
    
    # Quality metrics
    drop_rate = Column(Float, default=0.0)
    qos_compliance = Column(Float, default=0.0)
    queue_length = Column(Integer, default=0)
    
    # Additional metrics
    packets_processed = Column(Integer, default=0)
    packets_dropped = Column(Integer, default=0)
    
    # Relationship
    simulation = relationship("Simulation", back_populates="slice_metrics")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_slice_metrics_sim_type', 'simulation_id', 'slice_type'),
        Index('idx_slice_metrics_time', 'slice_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SliceMetrics {self.slice_type} {self.simulation_id}>"