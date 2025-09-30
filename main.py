from fastapi import FastAPI
from pydantic import BaseModel
from crewai import Agent, Task, Crew
import os

def run_my_crew(inputs):
    question = inputs.get('question', 'What can CrewAI do?')
    llm = Agent(
        role="AI Assistant",
        goal="Answer questions helpfully",
        backstory="A helpful multi-agent AI assistant using CrewAI.",
        verbose=True,
        allow_delegation=False,
        llm="openai",  # assumes OPENAI_API_KEY env var
    )
    task = Task(
        description=f"Answer the user's question: {question}",
        agent=llm,
    )
    crew = Crew(
        agents=[llm],
        tasks=[task],
        verbose=True,
    )
    result = crew.kickoff(inputs={"question": question})
    return result

app = FastAPI()

class CrewInput(BaseModel):
    input_data: dict

@app.get("/")
def healthcheck():
    return {"status": "ok", "message": "CrewAI FastAPI is live."}

@app.post("/run_crew/")
async def run_crew(input: CrewInput):
    try:
        result = run_my_crew(input.input_data)
        return {"result": result}
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "failed"
        }
