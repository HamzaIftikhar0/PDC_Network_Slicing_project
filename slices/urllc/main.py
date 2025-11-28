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
import heapq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLLCPriorityQueue:
    """Priority-based queue for ultra-reliable packets"""
    
    def __init__(self, max_size: int = 5000):
        self.heap = []
        self.max_size = max_size
        self.counter = 0
    
    def push(self, packet: dict):
        if len(self.heap) >= self.max_size:
            raise OverflowError("Queue full")
        
        # Priority: higher value = higher priority
        # Use counter to maintain FIFO for same priority
        priority = -packet.get("priority", 5)  # Negate for max-heap
        heapq.heappush(self.heap, (priority, self.counter, packet))
        self.counter += 1
    
    def pop(self):
        if not self.heap:
            return None
        _, _, packet = heapq.heappop(self.heap)
        return packet
    
    def __len__(self):
        return len(self.heap)

class URLLCQoSEngine:
    """Ultra-Reliable Low-Latency QoS engine"""
    
    CONFIG = {
        "max_latency": 10,  # ms - ultra strict
        "min_throughput": 50,  # Mbps
        "max_drop_rate": 0.001,  # 0.001% - ultra reliable
        "max_jitter": 5,  # ms
        "queue_size": 5000,
        "priority_levels": 10,
        "retry_policy": "aggressive",
        "redundancy_enabled": True,
    }
    
    def __init__(self):
        self.priority_queue = URLLCPriorityQueue(self.CONFIG["queue_size"])
        self.processed_packets = 0
        self.dropped_packets = 0
        self.retransmitted_packets = 0
        self.metrics_history: Deque = deque(maxlen=1000)
        self.qos_violations = 0
        self.resource_utilization = 0.0
        self.last_latency = 0
        self.redundancy_cache = {}
    
    def enqueue_packet(self, packet: dict, with_redundancy: bool = True) -> bool:
        """Enqueue with optional redundancy for reliability"""
        try:
            self.priority_queue.push(packet)
            
            # Store for redundancy
            if with_redundancy and self.CONFIG["redundancy_enabled"]:
                packet_id = packet.get("packet_id")
                if packet_id:
                    self.redundancy_cache[packet_id] = packet
            
            return True
        except OverflowError:
            self.dropped_packets += 1
            logger.warning("URLLC queue full - critical packet dropped")
            return False
    
    def process_batch(self, packets: List[dict]) -> Dict:
        """Process with ultra-low latency guarantees"""
        
        results = []
        batch_latencies = []
        batch_throughputs = []
        batch_drop_rates = []
        
        for packet in packets:
            if not self.enqueue_packet(packet):
                continue
            
            # Pop and process
            queued_packet = self.priority_queue.pop()
            if not queued_packet:
                continue
            
            # Ultra-low latency calculation
            latency = self._calculate_ultra_low_latency()
            throughput = self._calculate_throughput(queued_packet.get("size", 100))
            drop_rate = self._calculate_ultra_reliable_drop_rate()
            jitter = self._calculate_jitter(latency)
            utilization = len(self.priority_queue) / self.CONFIG["queue_size"]
            
            # Aggressive QoS check
            qos_satisfied = (
                latency <= self.CONFIG["max_latency"] and
                throughput >= self.CONFIG["min_throughput"] and
                drop_rate <= self.CONFIG["max_drop_rate"] and
                jitter <= self.CONFIG["max_jitter"]
            )
            
            # If QoS violated, trigger retransmission
            if not qos_satisfied and self.CONFIG["retry_policy"] == "aggressive":
                self._handle_retransmission(queued_packet)
                self.retransmitted_packets += 1
            
            if not qos_satisfied:
                self.qos_violations += 1
            
            result = {
                "packet_id": queued_packet.get("packet_id"),
                "latency": latency,
                "throughput": throughput,
                "drop_rate": drop_rate,
                "jitter": jitter,
                "qos_satisfied": qos_satisfied,
                "priority": queued_packet.get("priority", 8),
                "resource_utilization": utilization,
                "retransmitted": not qos_satisfied
            }
            
            results.append(result)
            self.processed_packets += 1
            
            batch_latencies.append(latency)
            batch_throughputs.append(throughput)
            batch_drop_rates.append(drop_rate)
            
            self.last_latency = latency
            self.resource_utilization = utilization
        
        batch_stats = {
            "slice_type": "urllc",
            "packets_processed": len(results),
            "packets_dropped": self.dropped_packets,
            "packets_retransmitted": self.retransmitted_packets,
            "total_processed": self.processed_packets,
            "qos_violations": self.qos_violations,
            "queue_length": len(self.priority_queue),
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
            "reliability_index": (
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
        return batch_stats
    
    def _calculate_ultra_low_latency(self) -> float:
        """Calculate ultra-low latency (1-10ms range)"""
        # Prioritize: minimal processing + minimal queueing
        base_latency = random.uniform(0.5, 3)  # Minimal
        
        queue_delay = (len(self.priority_queue) / self.CONFIG["queue_size"]) * 4
        
        propagation = random.uniform(2, 6)
        
        total = base_latency + queue_delay + propagation
        return min(total, self.CONFIG["max_latency"] * 1.5)
    
    def _calculate_throughput(self, packet_size: int) -> float:
        """Calculate throughput for URLLC"""
        bandwidth = random.uniform(50, 150)
        transmission_time = (packet_size * 8) / (bandwidth * 1_000_000)
        total_time = (self.last_latency / 1000) + transmission_time
        throughput = (packet_size * 8) / (total_time * 1_000_000) if total_time > 0 else bandwidth
        return max(0, min(throughput, 200))
    
    def _calculate_ultra_reliable_drop_rate(self) -> float:
        """Calculate ultra-low drop rate"""
        # Almost zero drop rate - rely on redundancy if needed
        base_rate = random.uniform(0.0001, 0.0005)
        
        utilization = len(self.priority_queue) / self.CONFIG["queue_size"]
        adjusted_rate = base_rate * (1 + utilization)
        
        return min(adjusted_rate, 0.002)
    
    def _calculate_jitter(self, current_latency: float) -> float:
        """Calculate minimal jitter"""
        if self.last_latency == 0:
            return 0
        jitter = abs(current_latency - self.last_latency)
        return min(jitter, 10)
    
    def _handle_retransmission(self, packet: dict):
        """Handle packet retransmission for failed QoS"""
        packet_id = packet.get("packet_id")
        if packet_id and packet_id in self.redundancy_cache:
            try:
                self.priority_queue.push(self.redundancy_cache[packet_id])
            except OverflowError:
                logger.error(f"Cannot retransmit packet {packet_id} - queue full")
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        if len(self.metrics_history) == 0:
            return {}
        
        recent_metrics = list(self.metrics_history)[-10:]
        
        return {
            "slice_type": "urllc",
            "total_packets_processed": self.processed_packets,
            "total_packets_dropped": self.dropped_packets,
            "total_packets_retransmitted": self.retransmitted_packets,
            "queue_length": len(self.priority_queue),
            "queue_capacity": self.CONFIG["queue_size"],
            "reliability_index": (
                (self.processed_packets - self.dropped_packets) / self.processed_packets * 100
                if self.processed_packets > 0 else 0
            ),
            "qos_violations": self.qos_violations,
            "recent_metrics": recent_metrics,
            "current_resource_utilization": self.resource_utilization,
            "redundancy_cache_size": len(self.redundancy_cache)
        }

app = FastAPI(title="URLLC Slice Processor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qos_engine = URLLCQoSEngine()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "slice": "urllc",
        "timestamp": datetime.now().isoformat(),
        "queue_status": {
            "length": len(qos_engine.priority_queue),
            "capacity": qos_engine.CONFIG["queue_size"],
            "utilization": len(qos_engine.priority_queue) / qos_engine.CONFIG["queue_size"] * 100
        }
    }

@app.post("/process")
async def process_packets(packet_count: int = 100):
    """Process ultra-reliable packets"""
    try:
        if packet_count <= 0 or packet_count > 5000:
            raise ValueError("Packet count must be between 1 and 5000")
        
        packets = [
            {
                "packet_id": f"urllc_{i}",
                "size": random.randint(50, 300),
                "priority": random.randint(8, 10)
            }
            for i in range(packet_count)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8102, log_level="info")