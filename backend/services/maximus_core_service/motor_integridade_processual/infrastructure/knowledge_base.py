"""Knowledge base for precedents and principles."""

from typing import List, Optional

class KnowledgeBase:
    """Stores ethical precedents and principles."""
    
    def __init__(self):
        self.precedents: List[dict] = []
        self.principles: List[dict] = []
    
    def store_precedent(self, case: dict) -> None:
        """Store a decision as precedent."""
        self.precedents.append(case)
    
    def find_similar(self, query: str) -> List[dict]:
        """Find similar past cases."""
        # Simplified: return all for now
        return self.precedents[:10]
    
    def get_principle(self, name: str) -> Optional[dict]:
        """Retrieve a principle by name."""
        for p in self.principles:
            if p.get("name") == name:
                return p
        return None
