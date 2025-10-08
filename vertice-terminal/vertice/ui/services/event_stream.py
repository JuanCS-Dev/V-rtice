"""
Event Stream Client para Vértice TUI
UI/UX Blueprint v1.2 - WebSocket/SSE para dados em tempo real

Características:
- WebSocket com reconnection automática
- Subscribe/unsubscribe por tópicos
- Buffer de eventos
- Implementação completa
"""

import asyncio
import os
from typing import Callable, Dict, List, Optional, Any
from enum import Enum
import httpx
from textual.message import Message


class EventType(Enum):
    """Tipos de eventos do backend."""
    ALERT = "alert"
    METRIC = "metric"
    STATUS = "status"
    DECISION = "decision"
    LOG = "log"
    THREAT = "threat"


class Event(Message):
    """Mensagem de evento para Textual."""

    def __init__(self, event_type: EventType, data: Dict[str, Any], topic: str):
        super().__init__()
        self.event_type = event_type
        self.data = data
        self.topic = topic


class EventStreamClient:
    """
    Cliente de stream de eventos para comunicação tempo real com backend.

    Utiliza Server-Sent Events (SSE) para compatibilidade universal.
    WebSocket pode ser implementado futuramente se necessário.

    Example:
        client = EventStreamClient()
        await client.connect()
        client.subscribe("alerts", on_alert_callback)
        await client.start_listening()
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Inicializa cliente.

        Args:
            base_url: URL base do API Gateway (default: env VITE_API_GATEWAY_URL)
        """
        self.base_url = base_url or os.getenv("VITE_API_GATEWAY_URL", "http://localhost:8000")
        self.client: Optional[httpx.AsyncClient] = None
        self.is_connected = False
        self.is_listening = False

        # Subscribers por tópico
        self._subscribers: Dict[str, List[Callable]] = {}

        # Buffer de eventos
        self._event_buffer: List[Event] = []
        self._buffer_size = 1000

        # Reconnection
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._reconnect_delay = 2  # seconds

    async def connect(self) -> bool:
        """
        Conecta ao backend.

        Returns:
            bool: True se conectado com sucesso
        """
        try:
            if not self.client:
                self.client = httpx.AsyncClient(timeout=30.0)

            # Verifica health do backend
            response = await self.client.get(f"{self.base_url}/health")
            self.is_connected = response.status_code == 200

            if self.is_connected:
                self._reconnect_attempts = 0

            return self.is_connected

        except Exception:
            self.is_connected = False
            return False

    async def disconnect(self):
        """Desconecta do backend."""
        self.is_listening = False
        self.is_connected = False

        if self.client:
            await self.client.aclose()
            self.client = None

    async def _reconnect(self) -> bool:
        """
        Tenta reconectar automaticamente.

        Returns:
            bool: True se reconectou
        """
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            return False

        self._reconnect_attempts += 1

        await asyncio.sleep(self._reconnect_delay)

        return await self.connect()

    def subscribe(self, topic: str, callback: Callable[[Event], None]):
        """
        Inscreve callback para tópico específico.

        Args:
            topic: Nome do tópico (ex: "alerts", "metrics")
            callback: Função a ser chamada quando evento chegar
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []

        self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Optional[Callable] = None):
        """
        Cancela inscrição.

        Args:
            topic: Nome do tópico
            callback: Callback específico (None remove all)
        """
        if topic not in self._subscribers:
            return

        if callback:
            self._subscribers[topic].remove(callback)
        else:
            self._subscribers[topic] = []

    async def start_listening(self):
        """
        Inicia escuta de eventos (SSE).
        Executa em loop até disconnect.
        """
        self.is_listening = True

        while self.is_listening:
            if not self.is_connected:
                if not await self._reconnect():
                    break

            try:
                # SSE endpoint (simulado - backend precisa implementar)
                async with self.client.stream("GET", f"{self.base_url}/api/events/stream") as response:
                    if response.status_code != 200:
                        await asyncio.sleep(self._reconnect_delay)
                        continue

                    async for line in response.aiter_lines():
                        if not line or not self.is_listening:
                            continue

                        # Parse SSE format
                        if line.startswith("data: "):
                            data_str = line[6:]

                            try:
                                import json
                                event_data = json.loads(data_str)

                                # Cria evento
                                event = Event(
                                    event_type=EventType(event_data.get("type", "log")),
                                    data=event_data.get("data", {}),
                                    topic=event_data.get("topic", "general"),
                                )

                                # Adiciona ao buffer
                                self._add_to_buffer(event)

                                # Notifica subscribers
                                await self._notify_subscribers(event)

                            except (json.JSONDecodeError, ValueError):
                                continue

            except httpx.HTTPError:
                # Reconnect on error
                self.is_connected = False
                await asyncio.sleep(self._reconnect_delay)

            except Exception:
                break

    def _add_to_buffer(self, event: Event):
        """Adiciona evento ao buffer circular."""
        self._event_buffer.append(event)

        if len(self._event_buffer) > self._buffer_size:
            self._event_buffer.pop(0)

    async def _notify_subscribers(self, event: Event):
        """Notifica subscribers do tópico do evento."""
        if event.topic in self._subscribers:
            for callback in self._subscribers[event.topic]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception:
                    # Ignora erros em callbacks
                    pass

    def get_buffered_events(
        self,
        topic: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """
        Retorna eventos do buffer.

        Args:
            topic: Filtrar por tópico (None = all)
            limit: Número máximo de eventos

        Returns:
            Lista de eventos
        """
        events = self._event_buffer

        if topic:
            events = [e for e in events if e.topic == topic]

        if limit:
            events = events[-limit:]

        return events

    async def publish_event(
        self,
        topic: str,
        event_type: EventType,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publica evento para o backend (opcional).

        Args:
            topic: Tópico
            event_type: Tipo do evento
            data: Dados do evento

        Returns:
            bool: True se publicado com sucesso
        """
        if not self.is_connected or not self.client:
            return False

        try:
            payload = {
                "topic": topic,
                "type": event_type.value,
                "data": data,
            }

            response = await self.client.post(
                f"{self.base_url}/api/events/publish",
                json=payload,
            )

            return response.status_code == 200

        except Exception:
            return False


__all__ = ["EventStreamClient", "Event", "EventType"]
