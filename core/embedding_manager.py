"""Embedding manager for Core memory system."""

import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import numpy as np

try:
    import openai
except ImportError:
    openai = None

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class EmbeddingManager:
    """Manages embeddings for calendar events and other data."""

    def __init__(self, vector_db_path: str = "core/memory.db"):
        """
        Initialize the embedding manager.

        Args:
            vector_db_path: Path to the vector database
        """
        self.vector_db_path = vector_db_path
        self.client = None
        self.collection = None

        # Initialize vector database
        self._init_vector_db()

        # OpenAI client for embeddings
        self.openai_client = None
        # Only create a real client if both library and API key are available and not under pytest
        if (
            openai is not None
            and "openai" in globals()
            and os.environ.get("PYTEST_CURRENT_TEST") is None
        ):
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                except Exception:
                    self.openai_client = None

    def _init_vector_db(self):
        """Initialize the vector database."""
        if not chromadb:
            print("Warning: ChromaDB not available. Using simple JSON storage.")
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=os.path.dirname(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False),
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="calendar_events",
                metadata={"description": "Calendar events with embeddings"},
            )
        except Exception as e:
            print(f"Warning: Could not initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    def extract_event_data(self, events: List[Any]) -> List[Dict]:
        """
        Extract relevant data from calendar events.

        Args:
            events: List of calendar events (EKEvent objects)

        Returns:
            List of dictionaries containing event data
        """
        event_data = []

        for event in events:
            # Extract basic event information
            event_dict = {
                "title": getattr(event, "title", "") or "",
                "description": getattr(event, "notes", "") or "",
                "location": getattr(event, "location", "") or "",
                "start_date": getattr(event, "startDate", ""),
                "end_date": getattr(event, "endDate", ""),
                "duration": self._calculate_duration(event),
                "attendees": self._extract_attendees(event),
                "is_recurring": getattr(event, "recurrenceRules", []) != [],
                "recurrence_pattern": self._extract_recurrence_pattern(event),
                "created_date": datetime.now().isoformat(),
            }

            # Create text representation for embedding
            event_dict["text_for_embedding"] = self._create_embedding_text(event_dict)

            event_data.append(event_dict)

        return event_data

    def _calculate_duration(self, event) -> int:
        """Calculate event duration in minutes."""
        try:
            start = getattr(event, "startDate", None)
            end = getattr(event, "endDate", None)
            if start and end:
                duration = end - start
                return int(duration.total_seconds() / 60)
        except:
            pass
        return 60  # Default duration

    def _extract_attendees(self, event) -> List[str]:
        """Extract attendee names from event."""
        try:
            attendees = getattr(event, "attendees", [])
            return [
                getattr(attendee, "name", "")
                for attendee in attendees
                if hasattr(attendee, "name")
            ]
        except:
            return []

    def _extract_recurrence_pattern(self, event) -> str:
        """Extract recurrence pattern from event."""
        try:
            rules = getattr(event, "recurrenceRules", [])
            if rules:
                return str(rules[0]) if rules else ""
        except:
            pass
        return ""

    def _create_embedding_text(self, event_dict: Dict) -> str:
        """Create text representation for embedding."""
        parts = []

        if event_dict["title"]:
            parts.append(f"Title: {event_dict['title']}")

        if event_dict["description"]:
            parts.append(f"Description: {event_dict['description']}")

        if event_dict["location"]:
            parts.append(f"Location: {event_dict['location']}")

        if event_dict["attendees"]:
            attendees_str = ", ".join(event_dict["attendees"])
            parts.append(f"Attendees: {attendees_str}")

        if event_dict["is_recurring"]:
            parts.append("Recurring event")
            if event_dict["recurrence_pattern"]:
                parts.append(f"Pattern: {event_dict['recurrence_pattern']}")

        duration = event_dict.get("duration", 0)
        if duration:
            parts.append(f"Duration: {duration} minutes")

        return " | ".join(parts)

    def create_embeddings(self, event_data: List[Dict]) -> List[List[float]]:
        """
        Create embeddings for event data.

        Args:
            event_data: List of event dictionaries

        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            print("Warning: OpenAI client not available. Using random embeddings.")
            return [np.random.rand(1536).tolist() for _ in event_data]

        embeddings = []

        for event in event_data:
            try:
                text = event["text_for_embedding"]
                if not text.strip():
                    # Use title as fallback
                    text = event.get("title", "calendar event")

                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small", input=text
                )

                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(
                    f"Warning: Could not create embedding for event {event.get('title', 'unknown')}: {e}"
                )
                # Fallback to random embedding
                embeddings.append(np.random.rand(1536).tolist())

        return embeddings

    def store_embeddings(
        self, embeddings: List[List[float]], metadata: List[Dict]
    ) -> bool:
        """
        Store embeddings in the vector database.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not self.collection:
            print("Warning: No vector database available. Storing in JSON file.")
            return self._store_in_json(embeddings, metadata)

        try:
            # Prepare data for ChromaDB
            ids = [
                f"event_{i}_{datetime.now().timestamp()}"
                for i in range(len(embeddings))
            ]
            documents = [meta.get("text_for_embedding", "") for meta in metadata]

            # Add embeddings to collection
            self.collection.add(
                embeddings=embeddings, documents=documents, metadatas=metadata, ids=ids
            )

            return True
        except Exception as e:
            print(f"Error storing embeddings: {e}")
            return False

    def _store_in_json(
        self, embeddings: List[List[float]], metadata: List[Dict]
    ) -> bool:
        """Store embeddings in JSON file as fallback."""
        try:
            data = {
                "embeddings": embeddings,
                "metadata": metadata,
                "created": datetime.now().isoformat(),
            }

            json_path = self.vector_db_path.replace(".db", ".json")
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error storing in JSON: {e}")
            return False

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar events using semantic similarity.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of similar events with metadata
        """
        if not self.openai_client:
            print("Warning: OpenAI client not available. Returning empty results.")
            return []

        try:
            # Create embedding for query
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=query
            )
            query_embedding = response.data[0].embedding

            if self.collection:
                # Search in ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding], n_results=top_k
                )

                # Format results
                similar_events = []
                for i in range(len(results["ids"][0])):
                    event_data = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": (
                            results["distances"][0][i]
                            if "distances" in results
                            else None
                        ),
                        "document": results["documents"][0][i],
                    }
                    similar_events.append(event_data)

                return similar_events
            else:
                # Fallback to JSON search
                return self._search_in_json(query_embedding, top_k)

        except Exception as e:
            print(f"Error searching similar events: {e}")
            return []

    def _search_in_json(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """Search in JSON file as fallback."""
        try:
            json_path = self.vector_db_path.replace(".db", ".json")
            if not os.path.exists(json_path):
                return []

            with open(json_path, "r") as f:
                data = json.load(f)

            embeddings = data.get("embeddings", [])
            metadata = data.get("metadata", [])

            # Calculate similarities
            similarities = []
            for i, embedding in enumerate(embeddings):
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                similarities.append((similarity, i))

            # Sort by similarity and return top_k
            similarities.sort(reverse=True)
            results = []

            for similarity, idx in similarities[:top_k]:
                if idx < len(metadata):
                    results.append(
                        {"metadata": metadata[idx], "similarity": float(similarity)}
                    )

            return results

        except Exception as e:
            print(f"Error searching in JSON: {e}")
            return []

    def update_event_embedding(self, event_id: str, event_data: Dict) -> bool:
        """
        Update embedding for a specific event.

        Args:
            event_id: ID of the event to update
            event_data: New event data

        Returns:
            True if successful, False otherwise
        """
        # For now, we'll delete and re-add the event
        # In a production system, you'd want more efficient updates
        return self.delete_event_embedding(event_id) and self.add_event_embedding(
            event_data
        )

    def delete_event_embedding(self, event_id: str) -> bool:
        """
        Delete embedding for a specific event.

        Args:
            event_id: ID of the event to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.collection:
            return True  # Nothing to delete in JSON fallback

        try:
            # Find and delete the event
            results = self.collection.get(where={"event_id": event_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            return True
        except Exception as e:
            print(f"Error deleting event embedding: {e}")
            return False

    def add_event_embedding(self, event_data: Dict) -> bool:
        """
        Add embedding for a new event.

        Args:
            event_data: Event data dictionary

        Returns:
            True if successful, False otherwise
        """
        # Create embedding
        embeddings = self.create_embeddings([event_data])
        if not embeddings:
            return False

        # Store embedding
        return self.store_embeddings(embeddings, [event_data])

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the embedding database.

        Returns:
            Dictionary with statistics
        """
        if self.collection:
            try:
                count = self.collection.count()
                return {
                    "total_events": count,
                    "storage_type": "chromadb",
                    "database_path": self.vector_db_path,
                }
            except Exception as e:
                print(f"Error getting stats: {e}")
                return {"error": str(e)}
        else:
            # Check JSON file
            json_path = self.vector_db_path.replace(".db", ".json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r") as f:
                        data = json.load(f)
                    return {
                        "total_events": len(data.get("embeddings", [])),
                        "storage_type": "json",
                        "database_path": json_path,
                    }
                except Exception as e:
                    return {"error": str(e)}
            else:
                return {
                    "total_events": 0,
                    "storage_type": "none",
                    "database_path": self.vector_db_path,
                }
