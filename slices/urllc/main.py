"""
URLLC (Ultra-Reliable Low-Latency Communication) Slice Processor
Extreme low latency, ultra-high reliability
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
from pydantic import BaseModel, Field

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
    """QoS metrics for URLLC"""
    latency: float
    reliability: float
    packets_retransmitted: int

# ===================== URLLC QoS ENGINE =====================

class URLLCQoSEngine:
    """QoS enforcement engine for URLLC slice"""
    
    CONFIG = {
        "max_latency": 10,  # Strict latency requirement (ms)
        "min_reliability": 99.99,  # 4 nines reliability
        "max_drop_rate": 0.01,  # 0.01% maximum drop
        "queue_size": 5000,  # Smaller queue for faster processing
        "priority_levels": 10,
        "preemption_enabled": True,  # Can preempt lower priority traffic
    }
    
    def __init__(self):
        self.queue: Deque = deque(maxlen=self.CONFIG["queue_size"])
        self.priority_queue: Dict[int, Deque] = {i: deque() for i in range(self.CONFIG["priority_levels"])}
        self.processed_packets = 0
        self.dropped_packets = 0
        self.retransmitted_packets = 0
        self.metrics_history: Deque = deque(maxlen=1000)
        self.qos_violations = 0
        self.resource_utilization = 0.0
        self.last_latency = 0
        logger.info("URLLC QoS Engine initialized")
    
    def enqueue_packet(self, packet: dict) -> bool:
        """Enqueue packet with strict priority handling"""
        priority = packet.get("priority", 5)
        
        if len(self.queue) >= self.CONFIG["queue_size"]:
            # Try to preempt lower priority packets
            if self.CONFIG["preemption_enabled"] and priority >= 8:
                self._preempt_lower_priority_packet()
            else:
                self.dropped_packets += 1
                logger.warning("URLLC queue full - dropping packet")
                return False
        
        self.priority_queue[priority].append(packet)
        self.queue.append(packet)
        return True
    
    def _preempt_lower_priority_packet(self):
        """Remove lowest priority packet to make room"""
        for priority in range(self.CONFIG["priority_levels"]):
            if self.priority_queue[priority]:
                self.priority_queue[priority].popleft()
                self.dropped_packets += 1
                logger.info(f"Preempted priority {priority} packet for higher priority")
                return
    
    def process_batch(self, packets: List[dict]) -> Dict:
        """Process batch with ultra-low latency"""
        
        results = []
        batch_latencies = []
        
        packets_to_process = min(len(packets), len(self.queue) + len(packets))
        
        for packet in packets[:packets_to_process]:
            if not self.enqueue_packet(packet):
                continue
            
            # Ultra-low latency calculation
            latency = self._calculate_ultra_low_latency()
            reliability = self._calculate_reliability()
            retransmitted = self._check_retransmission_needed(latency)
            
            if retransmitted:
                self.retransmitted_packets += 1
            
            # Strict QoS compliance
            qos_satisfied = (
                latency <= self.CONFIG["max_latency"] and
                reliability >= self.CONFIG["min_reliability"] and
                not retransmitted
            )
            
            if not qos_satisfied:
                self.qos_violations += 1
            
            result = {
                "packet_id": packet.get("packet_id"),
                "latency": latency,
                "reliability_index": reliability,
                "packets_retransmitted": int(retransmitted),
                "qos_satisfied": qos_satisfied,
                "priority": packet.get("priority", 5),
            }
            
            results.append(result)
            self.processed_packets += 1
            batch_latencies.append(latency)
            self.last_latency = latency
        
        # Calculate batch statistics
        batch_stats = {
            "slice_type": "urllc",
            "packets_processed": len(results),
            "packets_dropped": self.dropped_packets,
            "packets_retransmitted": self.retransmitted_packets,
            "total_processed": self.processed_packets,
            "qos_violations": self.qos_violations,
            "queue_length": len(self.queue),
            "metrics": {
                "latency": {
                    "min": min(batch_latencies) if batch_latencies else 0,
                    "max": max(batch_latencies) if batch_latencies else 0,
                    "avg": np.mean(batch_latencies) if batch_latencies else 0,
                    "median": np.median(batch_latencies) if batch_latencies else 0,
                },
                "reliability": self._calculate_average_reliability(),
            },
            "success_rate": (
                (self.processed_packets - self.dropped_packets) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "reliability_index": self._calculate_average_reliability(),
            "detailed_results": results[:100]
        }
        
        self.metrics_history.append(batch_stats)
        logger.info(f"URLLC: Processed {len(results)} packets, Reliability: {batch_stats['reliability_index']:.4f}%")
        
        return batch_stats
    
    def _calculate_ultra_low_latency(self) -> float:
        """Calculate ultra-low latency for URLLC"""
        # Prioritized transmission
        transmission = random.uniform(0.5, 2)
        
        # Minimal propagation delay
        propagation = random.uniform(0.1, 1)
        
        # Minimal queueing (prioritized)
        queue_delay = (len(self.queue) / self.CONFIG["queue_size"]) * 3
        
        total = transmission + propagation + queue_delay
        return min(total, self.CONFIG["max_latency"] * 1.5)
    
    def _calculate_reliability(self) -> float:
        """Calculate packet reliability percentage"""
        base_reliability = 99.95 + random.uniform(-0.05, 0.05)
        
        # Decrease with queue utilization
        utilization = len(self.queue) / self.CONFIG["queue_size"]
        adjusted_reliability = base_reliability * (1 - utilization * 0.1)
        
        return max(99.0, min(99.99, adjusted_reliability))
    
    def _check_retransmission_needed(self, latency: float) -> bool:
        """Check if packet needs retransmission"""
        # 0.5% chance of requiring retransmission
        if random.random() < 0.005:
            return True
        
        # If latency exceeds threshold significantly, mark for retransmission
        if latency > self.CONFIG["max_latency"] * 1.3:
            return True
        
        return False
    
    def _calculate_average_reliability(self) -> float:
        """Calculate average reliability from history"""
        if len(self.metrics_history) == 0:
            return 99.99
        
        recent = list(self.metrics_history)[-5:]
        reliability_values = [m["metrics"]["reliability"] for m in recent if "reliability" in m["metrics"]]
        
        return np.mean(reliability_values) if reliability_values else 99.99
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        if len(self.metrics_history) == 0:
            return {}
        
        recent_metrics = list(self.metrics_history)[-10:]
        
        return {
            "slice_type": "urllc",
            "total_packets_processed": self.processed_packets,
            "total_packets_dropped": self.dropped_packets,
            "total_retransmitted": self.retransmitted_packets,
            "queue_length": len(self.queue),
            "queue_capacity": self.CONFIG["queue_size"],
            "success_rate": (
                (self.processed_packets - self.dropped_packets) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "reliability_index": self._calculate_average_reliability(),
            "qos_violations": self.qos_violations,
            "recent_metrics": recent_metrics,
            "current_resource_utilization": self.resource_utilization
        }

# ===================== FASTAPI APP =====================

app = FastAPI(title="URLLC Slice Processor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qos_engine = URLLCQoSEngine()

# ===================== ENDPOINTS =====================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "slice": "urllc",
        "timestamp": datetime.now().isoformat(),
        "queue_status": {
            "length": len(qos_engine.queue),
            "capacity": qos_engine.CONFIG["queue_size"],
            "utilization": len(qos_engine.queue) / qos_engine.CONFIG["queue_size"] * 100
        },
        "reliability": qos_engine._calculate_average_reliability()
    }

@app.post("/process")
async def process_packets(request: ProcessPacketsRequest):
    """Process packet batch with ultra-low latency"""
    try:
        if request.packet_count <= 0 or request.packet_count > 10000:
            raise ValueError("Packet count must be between 1 and 10000")
        
        # Generate dummy packets for processing
        packets = [
            {
                "packet_id": f"urllc_{i}",
                "size": random.randint(50, 300),
                "priority": random.randint(8, 10)
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
        "slice_type": "urllc",
        "config": qos_engine.CONFIG
    }

@app.post("/reset")
async def reset():
    """Reset slice state"""
    global qos_engine
    qos_engine = URLLCQoSEngine()
    return {"status": "reset", "slice": "urllc"}

# ===================== RUN SERVER =====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8102, log_level="info")