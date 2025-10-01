import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseManager:
    """Manages Supabase database connections"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        self.client: Client = create_client(self.url, self.key)
    
    def get_client(self) -> Client:
        """Returns the Supabase client instance"""
        return self.client
    
    def insert_data(self, table: str, data: dict):
        """Insert data into a Supabase table"""
        try:
            response = self.client.table(table).insert(data).execute()
            return response
        except Exception as e:
            print(f"Error inserting data: {e}")
            raise
    
    def query_data(self, table: str, filters: dict = None):
        """Query data from a Supabase table"""
        try:
            query = self.client.table(table).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error querying data: {e}")
            raise
    
    def update_data(self, table: str, data: dict, filters: dict):
        """Update data in a Supabase table"""
        try:
            query = self.client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response
        except Exception as e:
            print(f"Error updating data: {e}")
            raise
    
    def delete_data(self, table: str, filters: dict):
        """Delete data from a Supabase table"""
        try:
            query = self.client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response
        except Exception as e:
            print(f"Error deleting data: {e}")
            raise
