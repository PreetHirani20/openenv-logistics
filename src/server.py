from fastapi import FastAPI, HTTPException, Query
from .models import LogisticsAction, Observation, StepResponse
from .environment import LogisticsEnv
from .grader import LogisticsGrader

app = FastAPI(
    title="OpenEnv Global Logistics Dispatcher (Advanced)",
    description="Enterprise-grade Logistics Engine for Meta OpenEnv Hackathon"
)

# Initialize the environment
env = LogisticsEnv(seed=42)

@app.get("/")
async def root():
    return {"message": "Autonomous Logistics Engine Online."}

# Update the reset endpoint to accept an optional task string
@app.post("/reset", response_model=Observation)
async def reset_env(task: str = "medium"):
    """Resets the world and spawns cargo based on task difficulty."""
    return env.reset(task_name=task)

@app.get("/state")
async def get_state():
    return env.state()

@app.post("/step", response_model=StepResponse)
async def step_env(action: LogisticsAction):
    """Executes complex multi-leg logistics commands."""
    try:
        return env.step(action)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks")
async def get_tasks():
    # We will build the task-specific logic for the graph later, 
    # for now, we return the baseline graph task.
    return {
        "tasks": ["global_graph_routing"],
        "action_schema": LogisticsAction.model_json_schema()
    }

grader = LogisticsGrader()

# Update the grade endpoint to return the strict 0.0 - 1.0 float
@app.get("/grade")
async def get_grade():
    """Returns the official OpenEnv 0.0 to 1.0 performance score."""
    state = env.state()
    state["carbon_footprint_kg"] = getattr(env, 'carbon_footprint', 0.0)
    
    score = grader.evaluate(state)
    return {"score": score}