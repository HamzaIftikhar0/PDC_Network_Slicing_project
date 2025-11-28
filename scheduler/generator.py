from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import uvicorn
from dataclasses import dataclass, asdict
import numpy as np
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Packet:
    packet_id: str
    slice_type: str
    size: int
    priority: int
    src_ip: str
    dst_ip: str
    bandwidth_required: float
    latency_requirement: int
    packet_loss_tolerance: float
    timestamp: float

class TrafficPattern:
    """Defines traffic patterns for different scenarios"""
    
    PATTERNS = {
        "constant": lambda t: 1.0,
        "linear_increase": lambda t: min(1.0, t / 30.0),
        "burst": lambda t: 1.5 if (t % 10) < 2 else 0.7,
        "wave": lambda t: 1.0 + 0.5 * np.sin(2 * np.pi * t / 60),
    }
    
    @staticmethod
    def get_multiplier(pattern_name: str, elapsed_time: float) -> float:
        pattern_func = TrafficPattern.PATTERNS.get(pattern_name, TrafficPattern.PATTERNS["constant"])
        return max(0.1, pattern_func(elapsed_time))

class SliceProfile:
    """Defines characteristics for each network slice"""
    
    PROFILES = {
        "embb": {
            "name": "Enhanced Mobile Broadband",
            "description": "High throughput, moderate latency tolerance",
            "packet_size_range": (500, 2000),
            "priority_range": (3, 6),
            "bandwidth_range": (100, 1000),
            "latency_range": (50, 200),
            "loss_tolerance_range": (0.1, 1.0),
            "percentage": 0.40,  # 40% of traffic
        },
        "urllc": {
            "name": "Ultra-Reliable Low-Latency Communication",
            "description": "Low latency, extremely high reliability",
            "packet_size_range": (50, 300),
            "priority_range": (8, 10),
            "bandwidth_range": (10, 100),
            "latency_range": (1, 10),
            "loss_tolerance_range": (0.001, 0.01),
            "percentage": 0.30,  # 30% of traffic
        },
        "mmtc": {
            "name": "Massive Machine-Type Communication",
            "description": "Many devices, flexible timing",
            "packet_size_range": (100, 500),
            "priority_range": (1, 3),
            "bandwidth_range": (1, 50),
            "latency_range": (100, 1000),
            "loss_tolerance_range": (1.0, 5.0),
            "percentage": 0.30,  # 30% of traffic
        }
    }

class AdvancedTrafficGenerator:
    """Advanced traffic generator with realistic 5G characteristics"""
    
    def __init__(self):
        self.packet_counter = 0
        self.generation_history = deque(maxlen=1000)
        self.slice_stats = {
            "embb": {"generated": 0, "total_size": 0},
            "urllc": {"generated": 0, "total_size": 0},
            "mmtc": {"generated": 0, "total_size": 0}
        }
    
    def generate_traffic_batch(
        self, 
        total_volume: int, 
        pattern: str = "constant",
        elapsed_time: float = 0
    ) -> Dict[str, List[dict]]:
        """Generate realistic batch of packets across all slices"""
        
        pattern_multiplier = TrafficPattern.get_multiplier(pattern, elapsed_time)
        adjusted_volume = int(total_volume * pattern_multiplier)
        
        packets_by_slice = {}
        
        for slice_type, profile in SliceProfile.PROFILES.items():
            slice_volume = int(adjusted_volume * profile["percentage"])
            packets = self._generate_slice_packets(slice_type, profile, slice_volume)
            packets_by_slice[slice_type] = packets
            
            self.slice_stats[slice_type]["generated"] += len(packets)
            self.slice_stats[slice_type]["total_size"] += sum(p["size"] for p in packets)
        
        self.generation_history.append({
            "timestamp": datetime.now().isoformat(),
            "total_packets": adjusted_volume,
            "by_slice": {k: len(v) for k, v in packets_by_slice.items()}
        })
        
        return packets_by_slice
    
    def _generate_slice_packets(self, slice_type: str, profile: dict, volume: int) -> List[dict]:
        """Generate packets for specific slice type"""
        packets = []
        
        for i in range(volume):
            packet = self._create_packet(slice_type, profile)
            packets.append(asdict(packet))
            self.packet_counter += 1
        
        return packets
    
    def _create_packet(self, slice_type: str, profile: dict) -> Packet:
        """Create individual packet with realistic characteristics"""
        
        size = random.randint(*profile["packet_size_range"])
        priority = random.randint(*profile["priority_range"])
        bandwidth = random.uniform(*profile["bandwidth_range"])
        latency = random.randint(*profile["latency_range"])
        loss_tol = random.uniform(*profile["loss_tolerance_range"])
        
        # Generate realistic IP addresses
        src_octets = [random.randint(1, 254) for _ in range(4)]
        dst_octets = [random.randint(1, 254) for _ in range(4)]
        
        src_ip = f"192.168.{src_octets[2]}.{src_octets[3]}"
        dst_ip = f"10.{dst_octets[1]}.{dst_octets[2]}.{dst_octets[3]}"
        
        packet = Packet(
            packet_id=f"pkt_{self.packet_counter:09d}",
            slice_type=slice_type,
            size=size,
            priority=priority,
            src_ip=src_ip,
            dst_ip=dst_ip,
            bandwidth_required=bandwidth,
            latency_requirement=latency,
            packet_loss_tolerance=loss_tol,
            timestamp=datetime.now().timestamp()
        )
        
        return packet
    
    def get_statistics(self) -> Dict:
        """Get generation statistics"""
        total_packets = sum(s["generated"] for s in self.slice_stats.values())
        total_bytes = sum(s["total_size"] for s in self.slice_stats.values())
        
        return {
            "total_packets_generated": self.packet_counter,
            "total_packets_in_batch": total_packets,
            "total_bytes_generated": total_bytes,
            "slice_breakdown": {
                slice_type: {
                    "packets": stats["generated"],
                    "total_bytes": stats["total_size"],
                    "avg_packet_size": stats["total_size"] / stats["generated"] if stats["generated"] > 0 else 0
                }
                for slice_type, stats in self.slice_stats.items()
            },
            "generation_history_sample": list(self.generation_history)[-10:]
        }

app = FastAPI(title="5G Traffic Generator & Scheduler", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

traffic_generator = AdvancedTrafficGenerator()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "scheduler",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/generate")
async def generate_traffic(
    traffic_volume: int = 1000,
    pattern: str = "constant",
    elapsed_time: float = 0
):
    """Generate traffic batch and return packet distribution"""
    try:
        if traffic_volume <= 0:
            raise ValueError("Traffic volume must be positive")
        
        if traffic_volume > 100000:
            raise ValueError("Traffic volume exceeds maximum limit")
        
        packets_by_slice = traffic_generator.generate_traffic_batch(
            traffic_volume,
            pattern,
            elapsed_time
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "requested_volume": traffic_volume,
            "pattern": pattern,
            "generated_packets": {
                slice_type: len(packets)
                for slice_type, packets in packets_by_slice.items()
            },
            "packet_distribution": packets_by_slice,
            "statistics": traffic_generator.get_statistics()
        }
    except Exception as e:
        logger.error(f"Error generating traffic: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate/advanced")
async def generate_advanced_traffic(
    traffic_volume: int = 1000,
    pattern: str = "constant",
    slice_ratio: dict = None
):
    """Generate traffic with custom slice distribution"""
    try:
        if not slice_ratio:
            slice_ratio = {"embb": 0.4, "urllc": 0.3, "mmtc": 0.3}
        
        if abs(sum(slice_ratio.values()) - 1.0) > 0.01:
            raise ValueError("Slice ratios must sum to 1.0")
        
        packets_by_slice = {}
        
        for slice_type, ratio in slice_ratio.items():
            if slice_type not in SliceProfile.PROFILES:
                raise ValueError(f"Unknown slice type: {slice_type}")
            
            profile = SliceProfile.PROFILES[slice_type]
            slice_volume = int(traffic_volume * ratio)
            packets = traffic_generator._generate_slice_packets(slice_type, profile, slice_volume)
            packets_by_slice[slice_type] = packets
        
        return {
            "timestamp": datetime.now().isoformat(),
            "requested_volume": traffic_volume,
            "pattern": pattern,
            "custom_ratios": slice_ratio,
            "generated_packets": {k: len(v) for k, v in packets_by_slice.items()},
            "statistics": traffic_generator.get_statistics()
        }
    except Exception as e:
        logger.error(f"Error generating advanced traffic: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Get aggregated traffic generation statistics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "statistics": traffic_generator.get_statistics()
    }

@app.post("/reset")
async def reset_statistics():
    """Reset all statistics"""
    global traffic_generator
    traffic_generator = AdvancedTrafficGenerator()
    return {
        "status": "reset",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/profiles")
async def get_slice_profiles():
    """Get all slice profiles"""
    return {
        "profiles": {
            slice_type: {
                "name": profile["name"],
                "description": profile["description"],
                "percentage": profile["percentage"],
                "ranges": {
                    "packet_size": profile["packet_size_range"],
                    "priority": profile["priority_range"],
                    "bandwidth": profile["bandwidth_range"],
                    "latency": profile["latency_range"],
                    "loss_tolerance": profile["loss_tolerance_range"],
                }
            }
            for slice_type, profile in SliceProfile.PROFILES.items()
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )