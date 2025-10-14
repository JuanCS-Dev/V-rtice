"""Human-in-the-loop queue management."""

from typing import List, Optional
from motor_integridade_processual.models.verdict import EthicalVerdict

class HITLQueue:
    """Manages cases escalated to human operators."""
    
    def __init__(self):
        self.queue: List[EthicalVerdict] = []
    
    def add_to_queue(self, verdict: EthicalVerdict) -> None:
        """Add case to HITL queue."""
        if verdict.requires_human_review:
            self.queue.append(verdict)
    
    def get_next(self) -> Optional[EthicalVerdict]:
        """Get next case from queue."""
        return self.queue.pop(0) if self.queue else None
    
    def queue_size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
