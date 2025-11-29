"""
eMBB (Enhanced Mobile Broadband) Slice Processor
High throughput, moderate latency tolerance
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
import logging
from datetime import datetime
from typing import Dict, List, Deque
from collections import deque
import uvicorn
import numpy as np
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== PYDANTIC MODELS =====================

class ProcessPacketsRequest(BaseModel):
    """Request schema for processing packets"""
    packet_count: int = Field(..., ge=1, le=10000)

# ===================== DATACLASSES =====================

@dataclass
class QOSMetrics:
    """QoS metrics for eMBB"""
    latency: float
    throughput: float
    drop_rate: float
    jitter: float
    resource_utilization: float

# ===================== eMBB QoS ENGINE =====================

class EMBBQoSEngine:
    """QoS enforcement engine for eMBB slice"""
    
    CONFIG = {
        "max_latency": 200,  # ms
        "min_throughput": 100,  # Mbps
        "max_drop_rate": 0.5,  # %
        "max_jitter": 50,  # ms
        "target_utilization": 0.75,
        "queue_size": 10000,
        "priority_levels": 10,
    }
    
    def __init__(self):
        self.queue: Deque = deque(maxlen=self.CONFIG["queue_size"])
        self.processed_packets = 0
        self.dropped_packets = 0
        self.metrics_history: Deque = deque(maxlen=1000)
        self.qos_violations = 0
        self.resource_utilization = 0.0
        self.last_latency = 0
        self.latency_jitter = 0
        logger.info("eMBB QoS Engine initialized")
    
    def enqueue_packet(self, packet: dict) -> bool:
        """Enqueue packet with priority handling"""
        if len(self.queue) >= self.CONFIG["queue_size"]:
            self.dropped_packets += 1
            logger.warning("eMBB queue full - dropping packet")
            return False
        
        self.queue.append(packet)
        return True
    
    def process_batch(self, packets: List[dict]) -> Dict:
        """Process batch of packets with QoS metrics"""
        
        results = []
        batch_latencies = []
        batch_throughputs = []
        batch_drop_rates = []
        
        packets_to_process = min(len(packets), len(self.queue) + len(packets))
        
        for i, packet in enumerate(packets[:packets_to_process]):
            if not self.enqueue_packet(packet):
                continue
            
            # Calculate realistic metrics
            latency = self._calculate_latency()
            throughput = self._calculate_throughput(packet.get("size", 1000))
            drop_rate = self._calculate_drop_rate()
            jitter = self._calculate_jitter(latency)
            utilization = len(self.queue) / self.CONFIG["queue_size"]
            
            # Check QoS compliance
            qos_satisfied = (
                latency <= self.CONFIG["max_latency"] and
                throughput >= self.CONFIG["min_throughput"] and
                drop_rate <= self.CONFIG["max_drop_rate"] and
                jitter <= self.CONFIG["max_jitter"]
            )
            
            if not qos_satisfied:
                self.qos_violations += 1
            
            result = {
                "packet_id": packet.get("packet_id"),
                "latency": latency,
                "throughput": throughput,
                "drop_rate": drop_rate,
                "jitter": jitter,
                "qos_satisfied": qos_satisfied,
                "priority": packet.get("priority", 5),
                "resource_utilization": utilization
            }
            
            results.append(result)
            self.processed_packets += 1
            
            batch_latencies.append(latency)
            batch_throughputs.append(throughput)
            batch_drop_rates.append(drop_rate)
            
            self.last_latency = latency
            self.latency_jitter = jitter
            self.resource_utilization = utilization
        
        # Calculate batch statistics
        batch_stats = {
            "slice_type": "embb",
            "packets_processed": len(results),
            "packets_dropped": self.dropped_packets,
            "total_processed": self.processed_packets,
            "qos_violations": self.qos_violations,
            "queue_length": len(self.queue),
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
                "jitter": self.latency_jitter,
                "resource_utilization": self.resource_utilization,
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
        logger.info(f"eMBB: Processed {len(results)} packets, Success Rate: {batch_stats['success_rate']:.2f}%")
        
        return batch_stats
    
    def _calculate_latency(self) -> float:
        """Calculate realistic latency for eMBB"""
        # Base processing latency
        base_latency = random.uniform(20, 100)
        
        # Add queueing delay
        queue_delay = (len(self.queue) / self.CONFIG["queue_size"]) * 80
        
        # Add network propagation
        propagation = random.uniform(5, 30)
        
        total = base_latency + queue_delay + propagation
        return min(total, self.CONFIG["max_latency"] * 1.2)
    
    def _calculate_throughput(self, packet_size: int) -> float:
        """Calculate realistic throughput based on Shannon's theorem"""
        # Simulated bandwidth: 500-1000 Mbps for eMBB
        bandwidth = random.uniform(500, 1000)
        
        # Packet transmission time
        transmission_time = (packet_size * 8) / (bandwidth * 1_000_000)
        
        # Throughput calculation
        total_time = (self.last_latency / 1000) + transmission_time
        throughput = (packet_size * 8) / (total_time * 1_000_000) if total_time > 0 else bandwidth
        
        return max(0, min(throughput, 1000))
    
    def _calculate_drop_rate(self) -> float:
        """Calculate packet drop rate"""
        base_rate = random.uniform(0.01, 0.3)
        
        # Increase drop rate with queue utilization
        utilization = len(self.queue) / self.CONFIG["queue_size"]
        adjusted_rate = base_rate * (1 + utilization * 2)
        
        return min(adjusted_rate, self.CONFIG["max_drop_rate"] * 2)
    
    def _calculate_jitter(self, current_latency: float) -> float:
        """Calculate latency variation (jitter)"""
        if self.last_latency == 0:
            return 0
        
        jitter = abs(current_latency - self.last_latency)
        return min(jitter, self.CONFIG["max_jitter"] * 2)
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        if len(self.metrics_history) == 0:
            return {}
        
        recent_metrics = list(self.metrics_history)[-10:]
        
        return {
            "slice_type": "embb",
            "total_packets_processed": self.processed_packets,
            "total_packets_dropped": self.dropped_packets,
            "queue_length": len(self.queue),
            "queue_capacity": self.CONFIG["queue_size"],
            "success_rate": (
                (self.processed_packets - self.dropped_packets) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "qos_violations": self.qos_violations,
            "recent_metrics": recent_metrics,
            "current_resource_utilization": self.resource_utilization
        }

# ===================== FASTAPI APP =====================

app = FastAPI(title="eMBB Slice Processor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qos_engine = EMBBQoSEngine()

# ===================== ENDPOINTS =====================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "slice": "embb",
        "timestamp": datetime.now().isoformat(),
        "queue_status": {
            "length": len(qos_engine.queue),
            "capacity": qos_engine.CONFIG["queue_size"],
            "utilization": len(qos_engine.queue) / qos_engine.CONFIG["queue_size"] * 100
        }
    }

@app.post("/process")
async def process_packets(request: ProcessPacketsRequest):
    """Process packet batch"""
    try:
        if request.packet_count <= 0 or request.packet_count > 10000:
            raise ValueError("Packet count must be between 1 and 10000")
        
        # Generate dummy packets for processing
        packets = [
            {
                "packet_id": f"embb_{i}",
                "size": random.randint(500, 2000),
                "priority": random.randint(3, 6)
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

@app.get("/config")
async def get_config():
    """Get QoS configuration"""
    return {
        "slice_type": "embb",
        "config": qos_engine.CONFIG
    }

@app.post("/reset")
async def reset():
    """Reset slice state"""
    global qos_engine
    qos_engine = EMBBQoSEngine()
    return {"status": "reset", "slice": "embb"}

# ===================== RUN SERVER =====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8101, log_level="info")