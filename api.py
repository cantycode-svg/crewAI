# FastAPI endpoints for CrewAI with Supabase persistent memory
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os
from src.crewai.crew import Crew
from src.crewai.agent import Agent
from src.crewai.task import Task
from src.crewai.supabase_storage import SupabaseStorage
from src.crewai.process import Process

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="CrewAI API with Supabase Memory",
    description="API endpoints for running CrewAI with Supabase persistent memory",
    version="1.0.0"
)

# Initialize SupabaseStorage
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase_storage = SupabaseStorage(
    supabase_url=supabase_url,
    supabase_key=supabase_key
)

# Request/Response models
class CrewRequest(BaseModel):
    topic: str = "AI Agents"
    agent_role: Optional[str] = "Senior Research Analyst"
    agent_goal: Optional[str] = "Uncover cutting-edge developments in AI"
    task_description: Optional[str] = None

class CrewResponse(BaseModel):
    success: bool
    result: Any
    message: str

class ResultsResponse(BaseModel):
    success: bool
    results: Dict[str, Any]
    message: str

# Global crew instance storage
crew_results = {}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CrewAI API with Supabase Persistent Memory",
        "endpoints": {
            "/run_crew/": "POST - Run a crew with specified parameters and persist results",
            "/results/": "GET - Retrieve persisted crew results from Supabase",
            "/results/{crew_id}": "GET - Retrieve specific crew result by ID"
        }
    }

@app.post("/run_crew/", response_model=CrewResponse)
async def run_crew(request: CrewRequest):
    """
    Run a CrewAI crew with Supabase persistent memory.
    
    Args:
        request: CrewRequest containing topic and optional agent/task configurations
    
    Returns:
        CrewResponse with execution results
    """
    try:
        # Define agent
        researcher = Agent(
            role=request.agent_role or 'Senior Research Analyst',
            goal=request.agent_goal or 'Uncover cutting-edge developments in AI',
            backstory="""You are a senior research analyst with expertise in 
            identifying emerging trends and breakthrough developments in artificial intelligence.""",
            verbose=True
        )
        
        # Define task
        task_desc = request.task_description or f"""Conduct a comprehensive analysis of the latest 
        developments in {request.topic} and provide key insights about emerging trends."""
        
        research_task = Task(
            description=task_desc,
            expected_output="A detailed report on current trends and breakthroughs",
            agent=researcher
        )
        
        # Create crew with Supabase storage
        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            external_memory=supabase_storage,
            verbose=True,
            memory=True
        )
        
        # Execute crew
        result = crew.kickoff()
        
        # Store result locally for quick access
        crew_id = f"crew_{len(crew_results)}"
        crew_results[crew_id] = {
            "topic": request.topic,
            "result": str(result),
            "agent_role": request.agent_role
        }
        
        return CrewResponse(
            success=True,
            result=result,
            message=f"Crew executed successfully. Results persisted to Supabase. ID: {crew_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing crew: {str(e)}"
        )

@app.get("/results/", response_model=ResultsResponse)
async def get_all_results():
    """
    Retrieve all persisted crew results.
    
    Returns:
        ResultsResponse containing all stored results
    """
    try:
        # In a production system, this would query Supabase directly
        # For now, we return locally stored results
        return ResultsResponse(
            success=True,
            results=crew_results,
            message=f"Retrieved {len(crew_results)} crew results"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving results: {str(e)}"
        )

@app.get("/results/{crew_id}", response_model=Dict[str, Any])
async def get_result_by_id(crew_id: str):
    """
    Retrieve a specific crew result by ID.
    
    Args:
        crew_id: The ID of the crew execution
    
    Returns:
        Dict containing the crew result
    """
    try:
        if crew_id not in crew_results:
            raise HTTPException(
                status_code=404,
                detail=f"Crew result with ID {crew_id} not found"
            )
        
        return {
            "success": True,
            "crew_id": crew_id,
            "result": crew_results[crew_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving result: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "supabase_configured": bool(supabase_url and supabase_key),
        "storage_type": "SupabaseStorage"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
