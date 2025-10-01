# Example Crew instantiation with SupabaseStorage as external_memory
from dotenv import load_dotenv
import os
from src.crewai.crew import Crew
from src.crewai.agent import Agent
from src.crewai.task import Task
from src.crewai.supabase_storage import SupabaseStorage
from src.crewai.process import Process

# Load environment variables
load_dotenv()

# Initialize SupabaseStorage
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Instantiate SupabaseStorage for external memory
supabase_storage = SupabaseStorage(
    supabase_url=supabase_url,
    supabase_key=supabase_key
)

# Define an example agent
researcher = Agent(
    role='Senior Research Analyst',
    goal='Uncover cutting-edge developments in AI',
    backstory="""You are a senior research analyst with expertise in 
    identifying emerging trends and breakthrough developments in artificial intelligence.""",
    verbose=True
)

# Define an example task
research_task = Task(
    description="""Conduct a comprehensive analysis of the latest AI developments 
    and provide key insights about emerging trends.""",
    expected_output="A detailed report on current AI trends and breakthroughs",
    agent=researcher
)

# Create a Crew with SupabaseStorage wired as external_memory
crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    process=Process.sequential,
    external_memory=supabase_storage,  # Wire up SupabaseStorage as external memory
    verbose=True,
    memory=True  # Enable memory functionality
)

# Example execution
if __name__ == "__main__":
    print("Starting Crew with SupabaseStorage as external memory...")
    result = crew.kickoff()
    print("\nCrew execution completed!")
    print(f"Result: {result}")
