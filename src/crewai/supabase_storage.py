"""Supabase Storage adapter for CrewAI external memory."""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime
from supabase import create_client, Client


class SupabaseStorage:
    """Storage adapter that implements CrewAI Storage interface for Supabase.
    
    This adapter allows CrewAI to use Supabase as an external memory store,
    providing persistent storage for agent memories, task outputs, and other data.
    
    Attributes:
        client: Supabase client instance
        table_name: Name of the Supabase table to use for storage
    """

    def __init__(self, supabase_url: str, supabase_key: str, table_name: str = "crewai_memory"):
        """Initialize Supabase storage adapter.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            table_name: Name of table to store data (default: crewai_memory)
        """
        self.client: Client = create_client(supabase_url, supabase_key)
        self.table_name = table_name
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure the storage table exists with required schema.
        
        Note: This is a helper method. In practice, tables should be created
        via Supabase dashboard or migrations. This method just documents the schema.
        
        Required schema:
        - id: UUID primary key
        - key: text (indexed)
        - value: jsonb
        - metadata: jsonb
        - created_at: timestamp
        - updated_at: timestamp
        """
        pass  # Table should be created via Supabase migrations

    def save(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save data to Supabase storage.
        
        Args:
            key: Unique identifier for the data
            value: Data to store (will be JSON serialized)
            metadata: Optional metadata to store alongside the value
            
        Returns:
            Stored data record including id and timestamps
        """
        data = {
            "key": key,
            "value": json.dumps(value) if not isinstance(value, str) else value,
            "metadata": metadata or {},
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Try to update existing record first
        result = self.client.table(self.table_name).update(data).eq("key", key).execute()
        
        # If no record exists, insert new one
        if not result.data:
            data["created_at"] = datetime.utcnow().isoformat()
            result = self.client.table(self.table_name).insert(data).execute()
        
        return result.data[0] if result.data else {}

    def load(self, key: str) -> Optional[Any]:
        """Load data from Supabase storage.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            Stored value or None if not found
        """
        result = self.client.table(self.table_name).select("value").eq("key", key).execute()
        
        if result.data:
            value = result.data[0].get("value")
            try:
                return json.loads(value) if isinstance(value, str) else value
            except json.JSONDecodeError:
                return value
        return None

    def delete(self, key: str) -> bool:
        """Delete data from Supabase storage.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            True if deletion was successful, False otherwise
        """
        result = self.client.table(self.table_name).delete().eq("key", key).execute()
        return len(result.data) > 0

    def search(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for data in Supabase storage.
        
        Args:
            query: Dictionary of key-value pairs to match
            limit: Maximum number of results to return
            
        Returns:
            List of matching records
        """
        query_builder = self.client.table(self.table_name).select("*")
        
        for key, value in query.items():
            if key == "metadata":
                # Search in JSONB metadata field
                for meta_key, meta_value in value.items():
                    query_builder = query_builder.eq(f"metadata->{meta_key}", meta_value)
            else:
                query_builder = query_builder.eq(key, value)
        
        result = query_builder.limit(limit).execute()
        return result.data or []

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys in storage, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        query_builder = self.client.table(self.table_name).select("key")
        
        if prefix:
            query_builder = query_builder.like("key", f"{prefix}%")
        
        result = query_builder.execute()
        return [record["key"] for record in result.data] if result.data else []

    def clear(self) -> bool:
        """Clear all data from storage.
        
        Returns:
            True if successful, False otherwise
        """
        result = self.client.table(self.table_name).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return True


# Example usage:
# storage = SupabaseStorage(
#     supabase_url="https://your-project.supabase.co",
#     supabase_key="your-anon-key"
# )
# 
# # Save agent memory
# storage.save(
#     key="agent_memory_001",
#     value={"conversation": "User asked about weather"},
#     metadata={"agent_id": "agent_1", "timestamp": "2025-09-30"}
# )
# 
# # Load memory
# memory = storage.load("agent_memory_001")
# 
# # Search memories
# results = storage.search({"metadata": {"agent_id": "agent_1"}})
