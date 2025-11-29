"""
mMTC (Massive Machine-Type Communication) Slice Processor
Many devices, flexible timing, cost-effective
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
import logging
from datetime import datetime
from typing import Dict, List, Deque, Set
from collections import deque, defaultdict
import uvicorn
import numpy as np
from dataclasses import dataclass
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== PYDANTIC MODELS =====================

class ProcessPacketsRequest(BaseModel):
    """Request schema for processing packets"""
    packet_count: int = Field(..., ge=1, le=100000)

# ===================== DATACLASSES =====================

@dataclass
class QOSMetrics:
    """QoS metrics for mMTC"""
    latency: float
    active_devices: int
    success_rate: float

# ===================== DEVICE REGISTRY =====================

class DeviceRegistry:
    """Manages massive number of IoT devices"""
    
    def __init__(self, max_devices: int = 100000):
        self.devices: Dict[str, dict] = {}
        self.max_devices = max_devices
        self.device_last_seen: Dict[str, float] = {}
    
    def register_or_get_device(self, device_id: str) -> dict:
        """Register new device or get existing"""
        if device_id not in self.devices:
            if len(self.devices) >= self.max_devices:
                raise OverflowError(f"Max devices ({self.max_devices}) reached")
            
            self.devices[device_id] = {
                "id": device_id,
                "type": random.choice(["sensor", "actuator", "gateway"]),
                "registered_at": datetime.now().isoformat(),
                "packets_sent": 0,
                "status": "active"
            }
        
        self.device_last_seen[device_id] = datetime.now().timestamp()
        return self.devices[device_id]
    
    def get_active_devices(self) -> int:
        """Get count of active devices"""
        return len(self.devices)
    
    def get_device_count_by_type(self) -> Dict[str, int]:
        """Get device breakdown by type"""
        counts = defaultdict(int)
        for device in self.devices.values():
            counts[device["type"]] += 1
        return dict(counts)

# ===================== mMTC QoS ENGINE =====================

class MMTCQoSEngine:
    """QoS engine for massive machine-type communication"""
    
    CONFIG = {
        "max_latency": 1000,  # ms - relaxed
        "min_throughput": 10,  # Mbps
        "max_drop_rate": 2.0,  # % - allows higher drop
        "max_jitter": 200,  # ms
        "queue_size": 100000,  # Large queue for many devices
        "batch_processing": True,
        "batch_size": 1000,
        "device_limit": 100000,
        "aggregation_enabled": True,
    }
    
    def __init__(self):
        self.queue: Deque = deque(maxlen=self.CONFIG["queue_size"])
        self.device_registry = DeviceRegistry(self.CONFIG["device_limit"])
        self.processed_packets = 0
        self.dropped_packets = 0
        self.aggregated_packets = 0
        self.metrics_history: Deque = deque(maxlen=1000)
        self.qos_violations = 0
        self.resource_utilization = 0.0
        self.last_latency = 0
        self.device_distribution: Dict[str, int] = defaultdict(int)
        logger.info("mMTC QoS Engine initialized")
    
    def process_batch(self, packets: List[dict]) -> Dict:
        """Process large batch with device aggregation"""
        
        results = []
        batch_latencies = []
        batch_throughputs = []
        batch_drop_rates = []
        devices_contacted: Set[str] = set()
        
        # Aggregate packets by device if enabled
        if self.CONFIG["aggregation_enabled"]:
            packets = self._aggregate_packets_by_device(packets)
        
        for packet in packets:
            # Register device
            device_id = packet.get("device_id", f"device_{random.randint(0, 99999)}")
            try:
                device = self.device_registry.register_or_get_device(device_id)
                devices_contacted.add(device_id)
            except OverflowError:
                self.dropped_packets += 1
                logger.warning("Device limit reached")
                continue
            
            # Try to enqueue
            if len(self.queue) >= self.CONFIG["queue_size"]:
                self.dropped_packets += 1
                continue
            
            self.queue.append(packet)
            
            # Process with relaxed QoS
            latency = self._calculate_relaxed_latency()
            throughput = self._calculate_throughput(packet.get("size", 200))
            drop_rate = self._calculate_drop_rate()
            jitter = self._calculate_jitter(latency)
            utilization = len(self.queue) / self.CONFIG["queue_size"]
            
            # Flexible QoS compliance
            qos_satisfied = (
                latency <= self.CONFIG["max_latency"] and
                throughput >= self.CONFIG["min_throughput"] and
                drop_rate <= self.CONFIG["max_drop_rate"]
            )
            
            if not qos_satisfied:
                self.qos_violations += 1
            
            result = {
                "packet_id": packet.get("packet_id"),
                "device_id": device_id,
                "latency": latency,
                "throughput": throughput,
                "drop_rate": drop_rate,
                "jitter": jitter,
                "qos_satisfied": qos_satisfied,
                "device_type": device["type"],
                "resource_utilization": utilization
            }
            
            results.append(result)
            self.processed_packets += 1
            self.device_distribution[device["type"]] += 1
            
            batch_latencies.append(latency)
            batch_throughputs.append(throughput)
            batch_drop_rates.append(drop_rate)
            
            self.last_latency = latency
            self.resource_utilization = utilization
        
        batch_stats = {
            "slice_type": "mmtc",
            "packets_processed": len(results),
            "packets_dropped": self.dropped_packets,
            "packets_aggregated": self.aggregated_packets,
            "total_processed": self.processed_packets,
            "qos_violations": self.qos_violations,
            "queue_length": len(self.queue),
            "active_devices": self.device_registry.get_active_devices(),
            "devices_in_batch": len(devices_contacted),
            "device_distribution": self.device_distribution,
            "metrics": {
                "latency": {
                    "min": min(batch_latencies) if batch_latencies else 0,
                    "max": max(batch_latencies) if batch_latencies else 0,
                    "avg": np.mean(batch_latencies) if batch_latencies else 0,
                    "median": np.median(batch_latencies) if batch_latencies else 0,
                    "stdev": np.std(batch_latencies) if batch_latencies else 0,
                },
                "throughput": {
                    "min": min(batch_throughputs) if batch_throughputs else 0,
                    "max": max(batch_throughputs) if batch_throughputs else 0,
                    "avg": np.mean(batch_throughputs) if batch_throughputs else 0,
                },
                "drop_rate": {
                    "avg": np.mean(batch_drop_rates) if batch_drop_rates else 0,
                },
            },
            "success_rate": (
                (self.processed_packets - self.dropped_packets) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "qos_compliance_rate": (
                (self.processed_packets - self.qos_violations) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "detailed_results": results[:100]
        }
        
        self.metrics_history.append(batch_stats)
        logger.info(f"mMTC: Processed {len(results)} packets from {len(devices_contacted)} devices, Success Rate: {batch_stats['success_rate']:.2f}%")
        
        return batch_stats
    
    def _aggregate_packets_by_device(self, packets: List[dict]) -> List[dict]:
        """Aggregate multiple packets from same device"""
        device_packets = defaultdict(list)
        
        for packet in packets:
            device_id = packet.get("device_id", f"device_{random.randint(0, 99999)}")
            device_packets[device_id].append(packet)
        
        aggregated = []
        for device_id, device_packet_list in device_packets.items():
            if len(device_packet_list) > 1:
                # Combine packets
                combined = {
                    "packet_id": device_packet_list[0]["packet_id"],
                    "device_id": device_id,
                    "size": sum(p.get("size", 100) for p in device_packet_list),
                    "count": len(device_packet_list),
                    "aggregated": True
                }
                aggregated.append(combined)
                self.aggregated_packets += len(device_packet_list) - 1
            else:
                aggregated.append(device_packet_list[0])
        
        return aggregated
    
    def _calculate_relaxed_latency(self) -> float:
        """Calculate relaxed latency for mMTC"""
        base_latency = random.uniform(50, 300)
        queue_delay = (len(self.queue) / self.CONFIG["queue_size"]) * 400
        propagation = random.uniform(100, 500)
        
        total = base_latency + queue_delay + propagation
        return min(total, self.CONFIG["max_latency"] * 1.5)
    
    def _calculate_throughput(self, packet_size: int) -> float:
        """Calculate throughput for mMTC"""
        bandwidth = random.uniform(10, 100)
        transmission_time = (packet_size * 8) / (bandwidth * 1_000_000)
        total_time = (self.last_latency / 1000) + transmission_time
        throughput = (packet_size * 8) / (total_time * 1_000_000) if total_time > 0 else bandwidth
        return max(0, min(throughput, 150))
    
    def _calculate_drop_rate(self) -> float:
        """Calculate drop rate with higher tolerance"""
        base_rate = random.uniform(0.5, 1.5)
        utilization = len(self.queue) / self.CONFIG["queue_size"]
        adjusted_rate = base_rate * (1 + utilization * 3)
        return min(adjusted_rate, 5.0)
    
    def _calculate_jitter(self, current_latency: float) -> float:
        """Calculate jitter with relaxed tolerance"""
        if self.last_latency == 0:
            return 0
        jitter = abs(current_latency - self.last_latency)
        return min(jitter, 300)
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        if len(self.metrics_history) == 0:
            return {}
        
        recent_metrics = list(self.metrics_history)[-10:]
        device_breakdown = self.device_registry.get_device_count_by_type()
        
        return {
            "slice_type": "mmtc",
            "total_packets_processed": self.processed_packets,
            "total_packets_dropped": self.dropped_packets,
            "total_packets_aggregated": self.aggregated_packets,
            "queue_length": len(self.queue),
            "queue_capacity": self.CONFIG["queue_size"],
            "active_devices": self.device_registry.get_active_devices(),
            "max_devices": self.CONFIG["device_limit"],
            "device_breakdown": device_breakdown,
            "success_rate": (
                (self.processed_packets - self.dropped_packets) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "qos_violations": self.qos_violations,
            "recent_metrics": recent_metrics,
            "current_resource_utilization": self.resource_utilization
        }

# ===================== FASTAPI APP =====================

app = FastAPI(title="mMTC Slice Processor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qos_engine = MMTCQoSEngine()

# ===================== ENDPOINTS =====================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "slice": "mmtc",
        "timestamp": datetime.now().isoformat(),
        "queue_status": {
            "length": len(qos_engine.queue),
            "capacity": qos_engine.CONFIG["queue_size"],
            "utilization": len(qos_engine.queue) / qos_engine.CONFIG["queue_size"] * 100
        },
        "devices": {
            "active": qos_engine.device_registry.get_active_devices(),
            "max": qos_engine.CONFIG["device_limit"]
        }
    }

@app.post("/process")
async def process_packets(request: ProcessPacketsRequest):
    """Process massive batch of packets"""
    try:
        if request.packet_count <= 0 or request.packet_count > 100000:
            raise ValueError("Packet count must be between 1 and 100000")
        
        packets = [
            {
                "packet_id": f"mmtc_{i}",
                "device_id": f"device_{random.randint(0, 10000)}",
                "size": random.randint(100, 500)
            }
            for i in range(request.packet_count)
        ]
        
        result = qos_engine.process_batch(packets)
        return result
    except Exception as e:
        logger.error(f"Error processing packets: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Get slice statistics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "statistics": qos_engine.get_statistics()
    }

@app.get("/devices")
async def get_devices():
    """Get device registry statistics"""
    return {
        "active_devices": qos_engine.device_registry.get_active_devices(),
        "device_breakdown": qos_engine.device_registry.get_device_count_by_type(),
        "max_capacity": qos_engine.CONFIG["device_limit"]
    }

@app.get("/config")
async def get_config():
    """Get QoS configuration"""
    return {
        "slice_type": "mmtc",
        "config": qos_engine.CONFIG
    }

@app.post("/reset")
async def reset():
    """Reset slice state"""
    global qos_engine
    qos_engine = MMTCQoSEngine()
    return {"status": "reset", "slice": "mmtc"}

# ===================== RUN SERVER =====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8103, log_level="info")