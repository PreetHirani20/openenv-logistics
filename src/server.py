from fastapi import FastAPI, HTTPException, Query
from .models import LogisticsAction, Observation, StepResponse
from .environment import LogisticsEnv
from .grader import LogisticsGrader

app = FastAPI(
    title="OpenEnv Global Logistics Dispatcher",
    description="Enterprise-grade Logistics Engine for Meta OpenEnv Hackathon"
)

env = LogisticsEnv(seed=42)
grader = LogisticsGrader()

@app.get("/")
async def root():
    return {"message": "Autonomous Logistics Engine Online."}

@app.post("/reset", response_model=Observation)
async def reset_env(task: str = "medium"):
    return env.reset(task_name=task)

@app.get("/state")
async def get_state():
    return env.state()

@app.post("/step", response_model=StepResponse)
async def step_env(action: LogisticsAction):
    try:
        return env.step(action)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks")
async def get_tasks():
    # BULLETPROOF: Perfectly matches openenv.yaml
    return {
        "tasks": ["easy", "medium", "hard"],
        "action_schema": LogisticsAction.model_json_schema()
    }

@app.get("/grade")
async def get_grade():
    state = env.state()
    state["carbon_footprint_kg"] = getattr(env, 'carbon_footprint', 0.0)
    score = grader.evaluate(state)
    # Defense-in-depth: enforce open interval at the HTTP boundary
    score = round(max(0.001, min(0.999, score)), 4)
    return {"score": score}