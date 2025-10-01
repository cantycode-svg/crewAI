from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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


class CrewRunPayload(BaseModel):
    """Payload model for crew run results"""
    crew_name: str
    status: str
    result: Dict[str, Any]
    metadata: Dict[str, Any] = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CrewAI Supabase Integration API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/run_crew/")
async def run_crew(payload: CrewRunPayload):
    """
    Execute crew run and store results in Supabase.
    
    Args:
        payload: CrewRunPayload containing crew execution data
    
    Returns:
        Success response with inserted data ID
    """
    try:
        # Prepare data for Supabase insertion
        data_to_insert = {
            "crew_name": payload.crew_name,
            "status": payload.status,
            "result": payload.result,
            "metadata": payload.metadata,
        }
        
        # Insert data into Supabase 'results' table
        response = supabase_manager.insert_data('results', data_to_insert)
        
        return {
            "success": True,
            "message": "Crew results stored successfully",
            "data": response
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store crew results: {str(e)}"
        )


@app.get("/results/{crew_name}")
async def get_results(crew_name: str):
    """
    Retrieve crew results from Supabase by crew name.
    
    Args:
        crew_name: Name of the crew to retrieve results for
    
    Returns:
        List of results for the specified crew
    """
    try:
        response = supabase_manager.query_data(
            'results',
            filters={'crew_name': crew_name}
        )
        
        return {
            "success": True,
            "crew_name": crew_name,
            "results": response
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve crew results: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
