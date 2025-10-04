"""
📡 Real-Time Event Stream - WebSocket para eventos ao vivo

Integra com backend event_bus_service para streaming distribuído.

Features:
- WebSocket connection para eventos em tempo real
- Event filtering (por tipo, severidade, source)
- Auto-reconnect
- Event buffering
- Multiple subscribers
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tipos de eventos"""
    DETECTION = "detection"
    ALERT = "alert"
    POLICY_EXECUTION = "policy_execution"
    SYSTEM = "system"
    ENDPOINT_STATUS = "endpoint_status"
    THREAT_INTEL = "threat_intel"


@dataclass
class Event:
    """
    Evento em tempo real
    """
    id: str
    event_type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    tags: List[str] = field(default_factory=list)


class EventStream:
    """
    Stream de eventos em tempo real via WebSocket

    Features:
    - WebSocket connection
    - Event filtering
    - Callback registration
    - Auto-reconnect
    - Buffering
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        auto_reconnect: bool = True,
        buffer_size: int = 1000,
    ):
        """
        Args:
            backend_url: URL do event_bus_service WebSocket
            auto_reconnect: Se True, reconecta automaticamente
            buffer_size: Tamanho do buffer de eventos
        """
        self.backend_url = backend_url or "ws://localhost:8004"
        self.auto_reconnect = auto_reconnect
        self.buffer_size = buffer_size

        # WebSocket connection
        self.ws: Optional[Any] = None
        self.connected = False

        # Event buffer
        self.event_buffer: List[Event] = []

        # Callbacks registrados
        self.callbacks: Dict[EventType, List[Callable[[Event], None]]] = {}

        # Filters
        self.event_type_filter: Set[EventType] = set()
        self.severity_filter: Set[str] = set()
        self.source_filter: Set[str] = set()

        # Stats
        self.events_received = 0
        self.last_event_time: Optional[datetime] = None

    async def connect(self) -> bool:
        """
        Conecta ao WebSocket backend

        Returns:
            True se conectado
        """
        try:
            import websockets

            self.ws = await websockets.connect(
                f"{self.backend_url}/ws/events",
                ping_interval=30,
                ping_timeout=10,
            )

            self.connected = True
            logger.info(f"Connected to event stream: {self.backend_url}")

            # Start listening
            asyncio.create_task(self._listen())

            return True

        except Exception as e:
            logger.error(f"Failed to connect to event stream: {e}")
            self.connected = False

            if self.auto_reconnect:
                asyncio.create_task(self._reconnect())

            return False

    async def disconnect(self) -> None:
        """Desconecta do WebSocket"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.info("Disconnected from event stream")

    async def _listen(self) -> None:
        """
        Loop principal de escuta de eventos
        """
        try:
            async for message in self.ws:
                try:
                    # Parse evento
                    event_data = json.loads(message)
                    event = self._parse_event(event_data)

                    # Filter
                    if not self._should_process_event(event):
                        continue

                    # Buffer
                    self._buffer_event(event)

                    # Stats
                    self.events_received += 1
                    self.last_event_time = datetime.now()

                    # Call callbacks
                    await self._dispatch_event(event)

                except Exception as e:
                    logger.error(f"Error processing event: {e}")

        except Exception as e:
            logger.error(f"Event stream connection lost: {e}")
            self.connected = False

            if self.auto_reconnect:
                await self._reconnect()

    def _parse_event(self, data: Dict[str, Any]) -> Event:
        """
        Parse de evento JSON para Event object

        Args:
            data: Dict do JSON

        Returns:
            Event object
        """
        event_type_str = data.get("type", "system")

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            event_type = EventType.SYSTEM

        timestamp_str = data.get("timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()

        return Event(
            id=data.get("id", ""),
            event_type=event_type,
            timestamp=timestamp,
            source=data.get("source", "unknown"),
            data=data.get("data", {}),
            severity=data.get("severity", "info"),
            tags=data.get("tags", []),
        )

    def _should_process_event(self, event: Event) -> bool:
        """
        Verifica se evento deve ser processado (filtros)

        Args:
            event: Event object

        Returns:
            True se deve processar
        """
        # Event type filter
        if self.event_type_filter and event.event_type not in self.event_type_filter:
            return False

        # Severity filter
        if self.severity_filter and event.severity not in self.severity_filter:
            return False

        # Source filter
        if self.source_filter and event.source not in self.source_filter:
            return False

        return True

    def _buffer_event(self, event: Event) -> None:
        """
        Adiciona evento ao buffer (FIFO)

        Args:
            event: Event object
        """
        self.event_buffer.append(event)

        # Mantém buffer size
        if len(self.event_buffer) > self.buffer_size:
            self.event_buffer.pop(0)

    async def _dispatch_event(self, event: Event) -> None:
        """
        Dispatch evento para callbacks registrados

        Args:
            event: Event object
        """
        # Global callbacks (all events)
        global_callbacks = self.callbacks.get(None, [])

        for callback in global_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        # Type-specific callbacks
        type_callbacks = self.callbacks.get(event.event_type, [])

        for callback in type_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def _reconnect(self) -> None:
        """
        Tenta reconectar com backoff exponencial
        """
        delay = 1

        while not self.connected and self.auto_reconnect:
            logger.info(f"Attempting to reconnect in {delay}s...")
            await asyncio.sleep(delay)

            if await self.connect():
                break

            # Exponential backoff
            delay = min(delay * 2, 60)

    def subscribe(
        self,
        callback: Callable[[Event], None],
        event_type: Optional[EventType] = None,
    ) -> None:
        """
        Registra callback para eventos

        Args:
            callback: Função que recebe Event
            event_type: Tipo específico ou None para todos
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []

        self.callbacks[event_type].append(callback)
        logger.info(f"Callback registered for {event_type}")

    def unsubscribe(
        self,
        callback: Callable[[Event], None],
        event_type: Optional[EventType] = None,
    ) -> None:
        """
        Remove callback

        Args:
            callback: Callback para remover
            event_type: Tipo específico ou None
        """
        if event_type in self.callbacks:
            try:
                self.callbacks[event_type].remove(callback)
            except ValueError:
                pass

    def set_filter(
        self,
        event_types: Optional[List[EventType]] = None,
        severities: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
    ) -> None:
        """
        Configura filtros de eventos

        Args:
            event_types: Lista de tipos para aceitar
            severities: Lista de severidades para aceitar
            sources: Lista de sources para aceitar
        """
        if event_types:
            self.event_type_filter = set(event_types)

        if severities:
            self.severity_filter = set(severities)

        if sources:
            self.source_filter = set(sources)

        logger.info(
            f"Filters set: types={len(self.event_type_filter)}, "
            f"severities={len(self.severity_filter)}, "
            f"sources={len(self.source_filter)}"
        )

    def clear_filters(self) -> None:
        """Limpa todos os filtros"""
        self.event_type_filter.clear()
        self.severity_filter.clear()
        self.source_filter.clear()

    def get_buffered_events(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Retorna eventos do buffer

        Args:
            event_type: Filtrar por tipo
            limit: Máximo de eventos

        Returns:
            Lista de Event
        """
        events = self.event_buffer

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Mais recentes primeiro
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    async def publish(self, event: Event) -> bool:
        """
        Publica evento no stream (se conectado)

        Args:
            event: Event object

        Returns:
            True se publicado
        """
        if not self.connected or not self.ws:
            logger.warning("Cannot publish event: not connected")
            return False

        try:
            event_json = json.dumps({
                "id": event.id,
                "type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "data": event.data,
                "severity": event.severity,
                "tags": event.tags,
            })

            await self.ws.send(event_json)
            return True

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do stream

        Returns:
            Dict com stats
        """
        return {
            "connected": self.connected,
            "events_received": self.events_received,
            "buffer_size": len(self.event_buffer),
            "last_event_time": self.last_event_time.isoformat() if self.last_event_time else None,
            "active_callbacks": sum(len(cbs) for cbs in self.callbacks.values()),
        }


# Convenience function para uso síncrono
def create_event_stream(backend_url: Optional[str] = None) -> EventStream:
    """
    Cria EventStream e conecta

    Args:
        backend_url: URL do backend WebSocket

    Returns:
        EventStream conectado
    """
    stream = EventStream(backend_url=backend_url)

    # Run connect in asyncio
    async def _connect():
        await stream.connect()

    asyncio.run(_connect())

    return stream
