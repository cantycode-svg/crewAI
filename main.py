from fastapi import FastAPI, Request
from pydantic import BaseModel
import os

def run_my_crew(inputs):
    return {"status": "success", "inputs": inputs}

app = FastAPI()

class CrewInput(BaseModel):
    input_data: dict

@app.get("/")
def healthcheck():
    return {"status": "ok", "message": "CrewAI FastAPI is live."}

@app.post("/run_crew/")
async def run_crew(input: CrewInput):
    result = run_my_crew(input.input_data)
    return {"result": result}
