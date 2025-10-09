"""
Episodic Memory Buffer
Short-term to long-term memory consolidation system.
"""
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import logging
from .event import Event, EventType, Salience

logger = logging.getLogger(__name__)


class EpisodicBuffer:
    """
    Episodic memory buffer implementing STM → LTM consolidation.
    
    Architecture:
    - Short-Term Memory (STM): Recent events (last N)
    - Long-Term Memory (LTM): Consolidated important events
    - Consolidation: Move important events from STM to LTM
    
    Inspired by Atkinson-Shiffrin memory model.
    """
    
    def __init__(
        self,
        stm_capacity: int = 1000,
        consolidation_threshold: float = 0.6,
        consolidation_interval: int = 300  # seconds
    ):
        """
        Initialize episodic buffer.
        
        Args:
            stm_capacity: Maximum events in STM
            consolidation_threshold: Importance threshold for LTM
            consolidation_interval: Seconds between auto-consolidation
        """
        self.stm: deque = deque(maxlen=stm_capacity)
        self.ltm: List[Event] = []
        
        self.stm_capacity = stm_capacity
        self.consolidation_threshold = consolidation_threshold
        self.consolidation_interval = consolidation_interval
        
        self.last_consolidation = datetime.now()
        self.stats = {
            "total_events": 0,
            "stm_events": 0,
            "ltm_events": 0,
            "consolidations": 0,
            "discarded": 0
        }
        
        logger.info(f"EpisodicBuffer initialized: STM capacity={stm_capacity}, threshold={consolidation_threshold}")
    
    def add_event(self, event: Event) -> bool:
        """
        Add new event to short-term memory.
        
        Args:
            event: Event to add
            
        Returns:
            bool: True if added successfully
        """
        try:
            # Validate event
            if not isinstance(event, Event):
                raise TypeError("Must provide Event instance")
            
            # Check if buffer is full (will auto-discard oldest)
            if len(self.stm) >= self.stm_capacity:
                discarded = self.stm[0]
                logger.debug(f"STM full, discarding oldest: {discarded.id[:8]}")
                self.stats["discarded"] += 1
            
            # Add to STM
            self.stm.append(event)
            self.stats["total_events"] += 1
            self.stats["stm_events"] = len(self.stm)
            
            logger.debug(f"Event added to STM: {event.id[:8]} ({event.type.value})")
            
            # Auto-consolidate if interval elapsed
            if (datetime.now() - self.last_consolidation).total_seconds() > self.consolidation_interval:
                self.consolidate()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            return False
    
    def consolidate(self, force: bool = False) -> int:
        """
        Consolidate important events from STM to LTM.
        
        Args:
            force: If True, consolidate even if interval not reached
            
        Returns:
            int: Number of events consolidated
        """
        if not force:
            elapsed = (datetime.now() - self.last_consolidation).total_seconds()
            if elapsed < self.consolidation_interval:
                logger.debug(f"Consolidation skipped: {elapsed:.0f}s < {self.consolidation_interval}s")
                return 0
        
        consolidated_count = 0
        
        # Evaluate each STM event
        for event in list(self.stm):
            if event.consolidated:
                continue
                
            importance = event.calculate_importance()
            
            # Consolidate if important enough
            if importance >= self.consolidation_threshold:
                event.consolidated = True
                self.ltm.append(event)
                consolidated_count += 1
                logger.debug(f"Consolidated: {event.id[:8]} (importance={importance:.2f})")
        
        self.stats["consolidations"] += consolidated_count
        self.stats["ltm_events"] = len(self.ltm)
        self.last_consolidation = datetime.now()
        
        if consolidated_count > 0:
            logger.info(f"Consolidation complete: {consolidated_count} events moved to LTM")
        
        return consolidated_count
    
    def get_recent_events(self, limit: int = 10) -> List[Event]:
        """
        Get most recent events from STM.
        
        Args:
            limit: Maximum events to return
            
        Returns:
            List of recent events
        """
        return list(self.stm)[-limit:]
    
    def get_ltm_events(
        self,
        limit: Optional[int] = None,
        min_importance: Optional[float] = None
    ) -> List[Event]:
        """
        Get events from long-term memory.
        
        Args:
            limit: Maximum events to return
            min_importance: Filter by minimum importance
            
        Returns:
            List of LTM events
        """
        events = self.ltm
        
        # Filter by importance
        if min_importance is not None:
            events = [e for e in events if e.calculate_importance() >= min_importance]
        
        # Sort by timestamp (most recent first)
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            events = events[:limit]
        
        return events
    
    def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[EventType] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        include_stm: bool = True,
        include_ltm: bool = True
    ) -> List[Event]:
        """
        Query events with filters.
        
        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time
            event_type: Filter by event type
            tags: Filter by tags (any match)
            min_importance: Minimum importance score
            include_stm: Include STM events
            include_ltm: Include LTM events
            
        Returns:
            List of matching events
        """
        events = []
        
        if include_stm:
            events.extend(self.stm)
        if include_ltm:
            events.extend(self.ltm)
        
        # Apply filters
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        if event_type:
            events = [e for e in events if e.type == event_type]
        if tags:
            events = [e for e in events if any(tag in e.tags for tag in tags)]
        if min_importance is not None:
            events = [e for e in events if e.calculate_importance() >= min_importance]
        
        # Sort by timestamp
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        return events
    
    def clear_stm(self):
        """Clear short-term memory (emergency function)"""
        discarded = len(self.stm)
        self.stm.clear()
        self.stats["discarded"] += discarded
        self.stats["stm_events"] = 0
        logger.warning(f"STM cleared: {discarded} events discarded")
    
    def clear_ltm(self):
        """Clear long-term memory (emergency function)"""
        discarded = len(self.ltm)
        self.ltm.clear()
        self.stats["ltm_events"] = 0
        logger.warning(f"LTM cleared: {discarded} events discarded")
    
    def get_stats(self) -> Dict[str, any]:
        """Get memory statistics"""
        return {
            **self.stats,
            "stm_capacity": self.stm_capacity,
            "stm_usage": len(self.stm) / self.stm_capacity,
            "consolidation_threshold": self.consolidation_threshold,
            "last_consolidation": self.last_consolidation.isoformat()
        }
    
    def __repr__(self) -> str:
        return f"EpisodicBuffer(STM={len(self.stm)}/{self.stm_capacity}, LTM={len(self.ltm)})"
