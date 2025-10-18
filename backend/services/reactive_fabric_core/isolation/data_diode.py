"""
Data Diode Implementation - Unidirectional Communication Enforcer
Simulates hardware data diode behavior in software for L2→L1 communication
"""

import hashlib
import json
import logging
import queue
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Thread, Lock
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

class DiodeDirection(Enum):
    """Allowed data flow directions"""
    L2_TO_L1 = "layer2_to_layer1"  # Only allowed direction
    L1_TO_L2 = "layer1_to_layer2"  # BLOCKED
    L3_TO_L2 = "layer3_to_layer2"  # Allowed through DMZ
    L2_TO_L3 = "layer2_to_layer3"  # BLOCKED

@dataclass
class DiodePacket:
    """Data packet that crosses the diode"""
    id: str
    source_layer: str
    destination_layer: str
    payload: Dict[str, Any]
    timestamp: datetime
    signature: str
    integrity_hash: str

@dataclass
class DiodeStats:
    """Statistics for diode operations"""
    packets_transmitted: int = 0
    packets_dropped: int = 0
    bytes_transmitted: int = 0
    violations_blocked: int = 0
    last_transmission: Optional[datetime] = None
    uptime_seconds: float = 0

class DataDiode:
    """
    Software Data Diode - Enforces unidirectional communication
    Critical for preventing containment breaches from L3 (Sacrifice Island)
    """

    def __init__(self,
                 direction: DiodeDirection = DiodeDirection.L2_TO_L1,
                 buffer_size: int = 10000,
                 transmission_rate_limit: int = 1000,  # packets/second
                 enable_integrity_check: bool = True):
        """
        Initialize Data Diode

        Args:
            direction: Allowed transmission direction
            buffer_size: Size of transmission buffer
            transmission_rate_limit: Max packets per second
            enable_integrity_check: Verify packet integrity
        """
        self.direction = direction
        self.buffer_size = buffer_size
        self.rate_limit = transmission_rate_limit
        self.integrity_check = enable_integrity_check

        # Transmission buffer - unidirectional queue
        self._tx_buffer = queue.Queue(maxsize=buffer_size)
        self._rx_handler: Optional[Callable] = None

        # Statistics
        self._stats = DiodeStats()
        self._stats_lock = Lock()

        # Control
        self._running = False
        self._tx_thread: Optional[Thread] = None
        self._start_time = time.time()

        # Audit log
        self._audit_log: List[Dict] = []
        self._audit_file = Path("/var/log/reactive_fabric/data_diode.log")

    def start(self):
        """Start the data diode transmission"""
        if self._running:
            logger.warning("Data diode already running")
            return

        self._running = True
        self._start_time = time.time()

        # Start transmission thread
        self._tx_thread = Thread(target=self._transmission_loop, daemon=True)
        self._tx_thread.start()

        logger.info(f"Data Diode started: {self.direction.value}")
        self._audit_event("DIODE_START", {"direction": self.direction.value})

    def stop(self):
        """Stop the data diode"""
        self._running = False
        if self._tx_thread:
            self._tx_thread.join(timeout=5)

        logger.info("Data Diode stopped")
        self._audit_event("DIODE_STOP", {"stats": self.get_stats()})

    def transmit(self, data: Dict[str, Any], source: str, destination: str) -> bool:
        """
        Attempt to transmit data through the diode

        Args:
            data: Payload to transmit
            source: Source layer identifier
            destination: Destination layer identifier

        Returns:
            True if packet was queued, False if blocked
        """
        # Validate direction
        if not self._validate_direction(source, destination):
            self._record_violation(source, destination)
            return False

        # Create packet
        packet = self._create_packet(data, source, destination)

        try:
            # Queue for transmission (non-blocking)
            self._tx_buffer.put_nowait(packet)
            return True
        except queue.Full:
            logger.warning(f"Diode buffer full, packet dropped: {packet.id}")
            with self._stats_lock:
                self._stats.packets_dropped += 1
            return False

    def _validate_direction(self, source: str, destination: str) -> bool:
        """
        Validate if transmission direction is allowed

        CRITICAL: This is the core security enforcement
        """
        # Parse layers
        src_layer = self._parse_layer(source)
        dst_layer = self._parse_layer(destination)

        # Only allow specific directions
        if src_layer == "L2" and dst_layer == "L1":
            return self.direction == DiodeDirection.L2_TO_L1
        elif src_layer == "L3" and dst_layer == "L2":
            return self.direction == DiodeDirection.L3_TO_L2

        # Block all other directions
        logger.error(f"BLOCKED: Invalid direction {source} -> {destination}")
        return False

    def _parse_layer(self, identifier: str) -> str:
        """Extract layer from identifier"""
        if "layer1" in identifier.lower() or "l1" in identifier.lower():
            return "L1"
        elif "layer2" in identifier.lower() or "l2" in identifier.lower():
            return "L2"
        elif "layer3" in identifier.lower() or "l3" in identifier.lower():
            return "L3"
        else:
            return "UNKNOWN"

    def _create_packet(self, data: Dict, source: str, destination: str) -> DiodePacket:
        """Create a diode packet with integrity protection"""
        packet_id = hashlib.sha256(
            f"{time.time()}{source}{destination}".encode()
        ).hexdigest()[:16]

        payload_json = json.dumps(data, sort_keys=True)
        integrity_hash = hashlib.sha256(payload_json.encode()).hexdigest()

        signature = hashlib.sha512(
            f"{packet_id}{integrity_hash}{self.direction.value}".encode()
        ).hexdigest()

        return DiodePacket(
            id=packet_id,
            source_layer=source,
            destination_layer=destination,
            payload=data,
            timestamp=datetime.now(),
            signature=signature,
            integrity_hash=integrity_hash
        )

    def _transmission_loop(self):
        """Main transmission loop - runs in separate thread"""
        last_tx_time = time.time()
        tx_count = 0

        while self._running:
            try:
                # Rate limiting
                current_time = time.time()
                if current_time - last_tx_time >= 1.0:
                    tx_count = 0
                    last_tx_time = current_time

                if tx_count >= self.rate_limit:
                    time.sleep(0.001)  # Rate limit reached
                    continue

                # Get packet from buffer (timeout prevents hanging)
                try:
                    packet = self._tx_buffer.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Verify integrity if enabled
                if self.integrity_check:
                    if not self._verify_packet_integrity(packet):
                        logger.error(f"Packet integrity check failed: {packet.id}")
                        with self._stats_lock:
                            self._stats.packets_dropped += 1
                        continue

                # Transmit to handler
                if self._rx_handler:
                    try:
                        self._rx_handler(packet)
                        with self._stats_lock:
                            self._stats.packets_transmitted += 1
                            self._stats.bytes_transmitted += len(json.dumps(packet.payload))
                            self._stats.last_transmission = datetime.now()
                        tx_count += 1
                    except Exception as e:
                        logger.error(f"RX handler error: {e}")

            except Exception as e:
                logger.error(f"Transmission loop error: {e}")

    def _verify_packet_integrity(self, packet: DiodePacket) -> bool:
        """Verify packet hasn't been tampered with"""
        payload_json = json.dumps(packet.payload, sort_keys=True)
        expected_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        return packet.integrity_hash == expected_hash

    def _record_violation(self, source: str, destination: str):
        """Record attempted violation of diode direction"""
        with self._stats_lock:
            self._stats.violations_blocked += 1

        violation = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "destination": destination,
            "direction": f"{source} -> {destination}",
            "action": "BLOCKED",
            "reason": "Invalid transmission direction"
        }

        self._audit_event("DIRECTION_VIOLATION", violation)
        logger.critical(f"SECURITY VIOLATION: {violation}")

    def _audit_event(self, event_type: str, details: Dict):
        """Record audit event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "diode_id": id(self),
            "direction": self.direction.value,
            "details": details
        }

        self._audit_log.append(event)

        # Write to audit file
        try:
            self._audit_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def set_rx_handler(self, handler: Callable[[DiodePacket], None]):
        """Set the receiver handler for transmitted packets"""
        self._rx_handler = handler

    def get_stats(self) -> Dict:
        """Get diode statistics"""
        with self._stats_lock:
            return {
                "packets_transmitted": self._stats.packets_transmitted,
                "packets_dropped": self._stats.packets_dropped,
                "bytes_transmitted": self._stats.bytes_transmitted,
                "violations_blocked": self._stats.violations_blocked,
                "last_transmission": self._stats.last_transmission.isoformat() if self._stats.last_transmission else None,
                "uptime_seconds": time.time() - self._start_time,
                "buffer_usage": self._tx_buffer.qsize(),
                "buffer_capacity": self.buffer_size
            }

    def emergency_flush(self):
        """Emergency flush of transmission buffer"""
        flushed = 0
        while not self._tx_buffer.empty():
            try:
                self._tx_buffer.get_nowait()
                flushed += 1
            except queue.Empty:
                break

        logger.warning(f"Emergency flush: {flushed} packets dropped")
        self._audit_event("EMERGENCY_FLUSH", {"packets_flushed": flushed})
        return flushed