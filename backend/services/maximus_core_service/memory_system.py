"""Maximus Core Service - Memory System.

This module implements the long-term and short-term memory capabilities of the
Maximus AI. It is responsible for storing, retrieving, and managing various
types of information, including past interactions, learned knowledge, and
contextual data.

The memory system utilizes a vector database for efficient semantic search and
retrieval, allowing Maximus to access relevant information quickly and accurately.
It also incorporates mechanisms for updating and consolidating memories to ensure
the knowledge base remains current and coherent.
"""

from datetime import datetime
from typing import Any


class MemorySystem:
    """Manages the long-term and short-term memory of Maximus AI.

    This includes storing past interactions, learned knowledge, and contextual data,
    using a vector database for efficient retrieval.
    """

    def __init__(self, vector_db_client: Any):
        """Initializes the MemorySystem with a vector database client.

        Args:
            vector_db_client (Any): An initialized client for interacting with the vector database.
        """
        self.vector_db_client = vector_db_client
        self.short_term_memory: list[dict[str, Any]] = []  # Stores recent interactions

    async def store_interaction(self, prompt: str, response: dict[str, Any], confidence: float):
        """Stores a user interaction in both short-term and long-term memory.

        Args:
            prompt (str): The user's input prompt.
            response (Dict[str, Any]): The AI's response.
            confidence (float): The confidence score of the AI's response.
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "confidence": confidence,
        }
        self.short_term_memory.append(interaction)
        if len(self.short_term_memory) > 10:  # Keep only the last 10 interactions
            self.short_term_memory.pop(0)

        # Store in long-term memory (vector DB)
        await self.vector_db_client.add_document(
            content=f"User: {prompt}\nMaximus: {response.get('final_response', '')}",
            metadata={
                "type": "interaction",
                "timestamp": interaction["timestamp"],
                "confidence": confidence,
            },
        )
        print(f"[MemorySystem] Stored interaction: {prompt}")

    async def retrieve_recent_interactions(self, limit: int = 5) -> list[dict[str, Any]]:
        """Retrieves the most recent interactions from short-term memory.

        Args:
            limit (int): The maximum number of recent interactions to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of recent interaction dictionaries.
        """
        return self.short_term_memory[-limit:]

    async def search_long_term_memory(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Searches the long-term memory (vector DB) for relevant information.

        Args:
            query (str): The search query.
            top_k (int): The number of top relevant documents to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of relevant documents from the vector database.
        """
        print(f"[MemorySystem] Searching long-term memory for: {query}")
        results = await self.vector_db_client.query_documents(query, top_k=top_k)
        return results

    async def update_knowledge(
        self,
        document_id: str,
        new_content: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Updates an existing knowledge document in long-term memory.

        Args:
            document_id (str): The ID of the document to update.
            new_content (str): The new content for the document.
            metadata (Optional[Dict[str, Any]]): Optional new metadata for the document.
        """
        await self.vector_db_client.update_document(document_id, new_content, metadata)
        print(f"[MemorySystem] Updated knowledge document: {document_id}")

    async def forget_knowledge(self, document_id: str):
        """Removes a knowledge document from long-term memory.

        Args:
            document_id (str): The ID of the document to remove.
        """
        await self.vector_db_client.delete_document(document_id)
        print(f"[MemorySystem] Forgot knowledge document: {document_id}")
