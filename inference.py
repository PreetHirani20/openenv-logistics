import os
import requests
import json
import time
from openai import OpenAI

# --- OPENENV REQUIRED VARIABLES ---
# The hackathon validator will inject these variables automatically.
# We set defaults here so you can still test it locally with Gemini.
API_BASE_URL = os.getenv("API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_GEMINI_API_KEY_HERE") # Put your key here for local testing

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)

API_URL = "http://localhost:8000"

def get_action_from_llm(observation):
    prompt = f"""
    You are a Master Logistics AI.
    Goal: Deliver all cargo at the lowest Cost and Carbon Footprint WITHOUT spoilage.
    
    SITUATION:
    {json.dumps(observation, indent=2)}
    
    STRATEGY:
    1. CONSOLIDATION IS KING: If 2+ shipments are at the same node and `is_consolidated` is false, your FIRST action MUST be "consolidate" for a 40% discount.
    2. SAVE THE FOOD: Perishables MUST use fast 'supports_reefer': true routes (usually Air).
    3. CRUSH THE CARBON: Standard cargo does not spoil. ALWAYS put standard cargo on the cheapest, lowest-carbon routes (Ocean).
    
    Return ONLY a JSON object:
    {{
        "thought_process": "Why you chose this action.",
        "action_type": "dispatch_leg" | "consolidate" | "wait",
        "shipment_ids": ["ID1", "ID2"],
        "target_edge_id": "LANE-XYZ"
    }}
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def run_task(task_name):
    print(f"\n🚀 Starting Task: {task_name.upper()}...")
    resp = requests.post(f"{API_URL}/reset?task={task_name}")
    obs = resp.json()
    done = False
    
    while not done:
        action = get_action_from_llm(obs)
        print(f"[{task_name.upper()}] Day {obs['current_day']} | Action: {action['action_type']} for {action.get('shipment_ids')}")
        
        step_resp = requests.post(f"{API_URL}/step", json=action)
        if step_resp.status_code != 200:
            break
            
        data = step_resp.json()
        obs = data['observation']
        done = data['done']
        time.sleep(4) # Rate limit protection

    grade_resp = requests.get(f"{API_URL}/grade").json()
    print(f"🏁 Final Score for {task_name.upper()}: {grade_resp.get('score', 0.0)} / 1.0")

if __name__ == "__main__":
    # OpenEnv requires testing on all 3 difficulties
    for task in ["easy", "medium", "hard"]:
        run_task(task)