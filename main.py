# Force redeploy - accepts any JSON payload
from fastapi import FastAPI, HTTPException
from typing import Any, Dict
import os
from dotenv import load_dotenv

# Import the SupabaseManager from the crewai package
try:
    from src.crewai.supabase_client import SupabaseManager
except ImportError:
    from crewai.supabase_client import SupabaseManager

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="CrewAI Supabase Integration", version="1.0.0")

# Initialize Supabase manager
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase_manager = SupabaseManager(url=supabase_url, key=supabase_key)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CrewAI Supabase Integration API",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/run_crew/")
async def run_crew(payload: Dict[str, Any]):
    """
    Execute crew run and store results in Supabase.
    Accepts any JSON payload without validation.
    
    Args:
        payload: Dictionary containing any JSON data
    
    Returns:
        Success response with inserted data ID
    """
    try:
        # Insert data into Supabase 'results' table
        response = supabase_manager.insert_data('results', payload)
        
        return {
            "success": True,
            "message": "Data stored successfully in Supabase",
            "data": response
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store data: {str(e)}"
        )

@app.get("/results/{table_name}")
async def get_results(table_name: str):
    """
    Retrieve all results from Supabase by table name.
    
    Args:
        table_name: Name of the table to retrieve results from
    
    Returns:
        List of results from the specified table
    """
    try:
        response = supabase_manager.query_data(table_name, filters={})
        
        return {
            "success": True,
            "table_name": table_name,
            "results": response
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve data: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
