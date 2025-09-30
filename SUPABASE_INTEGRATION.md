# Supabase Integration Guide for CrewAI

This guide provides instructions for integrating Supabase with your CrewAI project for database connectivity during Render deployment.

## Prerequisites

- A Supabase account and project (https://supabase.com)
- Supabase project URL and API key
- CrewAI project set up

## Installation

The `supabase` package has been added to the project dependencies in `pyproject.toml`. It will be automatically installed during the Render build process.

## Environment Variables

Add the following environment variables to your `.env` file or Render dashboard:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

You can find these values in your Supabase project dashboard under Settings > API.

## Basic Implementation

Here's how to integrate Supabase into your CrewAI project:

### 1. Create a Supabase Client Module

Create a new file `src/my_project/supabase_client.py`:

```python
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
```

### 2. Using Supabase in Your CrewAI Project

Update your `src/my_project/main.py` to use Supabase:

```python
#!/usr/bin/env python
import sys
from my_project.crew import MyProjectCrew
from my_project.supabase_client import SupabaseManager

def run():
    """
    Run the crew with Supabase integration.
    """
    # Initialize Supabase
    db = SupabaseManager()
    
    # Example: Log crew execution start
    db.insert_data("crew_logs", {
        "event": "crew_start",
        "status": "running"
    })
    
    # Run your crew
    inputs = {
        'topic': 'AI Agents'
    }
    
    try:
        result = MyProjectCrew().crew().kickoff(inputs=inputs)
        
        # Log successful completion
        db.insert_data("crew_logs", {
            "event": "crew_complete",
            "status": "success",
            "result": str(result)
        })
        
        return result
    except Exception as e:
        # Log errors
        db.insert_data("crew_logs", {
            "event": "crew_error",
            "status": "failed",
            "error": str(e)
        })
        raise

if __name__ == "__main__":
    run()
```

### 3. Schema Setup in Supabase

Create the necessary tables in your Supabase project. Here's an example SQL for a crew logs table:

```sql
CREATE TABLE crew_logs (
    id BIGSERIAL PRIMARY KEY,
    event TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Enable Row Level Security
ALTER TABLE crew_logs ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (adjust based on your needs)
CREATE POLICY "Enable all access for authenticated users" ON crew_logs
    FOR ALL
    USING (true)
    WITH CHECK (true);
```

### 4. Using Supabase with CrewAI Tools

You can also create custom tools that interact with Supabase:

```python
from crewai_tools import tool
from my_project.supabase_client import SupabaseManager

@tool("Store Data Tool")
def store_data_tool(table: str, data: dict) -> str:
    """
    Store data in Supabase database.
    Args:
        table: The table name
        data: Dictionary of data to store
    """
    db = SupabaseManager()
    result = db.insert_data(table, data)
    return f"Data stored successfully: {result}"

@tool("Query Data Tool")
def query_data_tool(table: str, filters: dict = None) -> str:
    """
    Query data from Supabase database.
    Args:
        table: The table name
        filters: Optional filters as dictionary
    """
    db = SupabaseManager()
    result = db.query_data(table, filters)
    return f"Query results: {result}"
```

## Deployment on Render

### 1. Set Environment Variables

In your Render dashboard:
1. Go to your service
2. Navigate to "Environment" tab
3. Add the following environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

### 2. Build Configuration

Render will automatically install the `supabase` dependency from `pyproject.toml` during the build process.

### 3. Verify Installation

The build logs should show:
```
Installing dependencies from pyproject.toml...
✓ supabase>=2.0.0 installed successfully
```

## Best Practices

1. **Security**: Never commit your `.env` file. Use environment variables for sensitive data.
2. **Connection Pooling**: Supabase handles connection pooling automatically.
3. **Error Handling**: Always wrap database operations in try-except blocks.
4. **Rate Limits**: Be aware of Supabase rate limits on your plan.
5. **Row Level Security**: Configure RLS policies in Supabase for data security.

## Troubleshooting

### Issue: "No module named 'supabase'"
**Solution**: Ensure `supabase>=2.0.0` is in your `pyproject.toml` dependencies.

### Issue: "Invalid API key"
**Solution**: Verify that `SUPABASE_KEY` and `SUPABASE_URL` are correctly set in your environment.

### Issue: "Table does not exist"
**Solution**: Create the required tables in your Supabase dashboard using the SQL editor.

## Additional Resources

- [Supabase Python Documentation](https://supabase.com/docs/reference/python/introduction)
- [Supabase Dashboard](https://app.supabase.com/)
- [CrewAI Documentation](https://docs.crewai.com/)

## Example Use Cases

1. **Logging Agent Activities**: Track all agent decisions and actions
2. **Storing Results**: Save crew execution results for analysis
3. **User Management**: Manage users and permissions
4. **Data Persistence**: Store and retrieve task-related data
5. **Analytics**: Query and analyze crew performance metrics

---

**Note**: This integration assumes you have the `supabase` package available (>=2.0.0), which has been added to the project's `pyproject.toml` file.
