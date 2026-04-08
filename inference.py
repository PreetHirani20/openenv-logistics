import os
import requests
import json
import time
from openai import OpenAI

# --- 1. STRICT CHECKLIST COMPLIANCE ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN") 

api_key = HF_TOKEN or os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")

# --- 2. FIX: ADDED 15-SECOND TIMEOUT TO PREVENT HANGING ---
client = OpenAI(
    api_key=api_key,
    base_url=API_BASE_URL,
    timeout=15.0 
)

API_URL = os.getenv("API_URL", "http://localhost:7860")

def get_action_from_llm(observation, max_retries=3):
    prompt = f"""
    You are a Master Logistics AI.
    Goal: Deliver all cargo at the lowest Cost and Carbon Footprint WITHOUT spoilage.
    
    SITUATION:
    {json.dumps(observation, indent=2)}
    
    STRATEGY:
    1. CONSOLIDATION IS KING: If 2+ shipments are at the same node and `is_consolidated` is false, your FIRST action MUST be "consolidate" for a 40% discount.
    2. SAVE THE FOOD: Perishables MUST use fast 'supports_reefer': true routes (usually Air).
    3. CRUSH THE CARBON: Standard cargo does not spoil. ALWAYS put standard cargo on the cheapest, lowest-carbon routes (Ocean).
    
    Return ONLY a JSON object. Do not include markdown formatting or backticks:
    {{
        "thought_process": "Why you chose this action.",
        "action_type": "dispatch_leg" | "consolidate" | "wait",
        "shipment_ids": ["ID1", "ID2"],
        "target_edge_id": "LANE-XYZ"
    }}
    """
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content.strip()
            
            # --- THE FIX: AGGRESSIVE MARKDOWN STRIPPING ---
            if raw_content.startswith("```"):
                raw_content = raw_content.strip("` \n")
                if raw_content.lower().startswith("json"):
                    raw_content = raw_content[4:].strip()
            
            return json.loads(raw_content)
            
        except Exception as e:
            time.sleep(1) 
            
    return {
        "thought_process": "Fallback due to API error.",
        "action_type": "wait",
        "shipment_ids": [],
        "target_edge_id": ""
    }

def run_task(task_name):
    print(f"START task={task_name}", flush=True)
    
    try:
        # FIX: Added 10-second timeout to FastAPI requests
        resp = requests.post(f"{API_URL}/reset?task={task_name}", timeout=10.0)
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"END task={task_name} score=0.0", flush=True)
        return
        
    done = False
    step_count = 0
    MAX_STEPS = 100 # FIX: Hard cutoff to absolutely prevent infinite loops
    
    while not done and step_count < MAX_STEPS:
        action = get_action_from_llm(obs)
        
        print(f"STEP step={step_count} action={action.get('action_type')}", flush=True)
        
        try:
            # FIX: Added 10-second timeout
            step_resp = requests.post(f"{API_URL}/step", json=action, timeout=10.0)
            step_resp.raise_for_status()
            data = step_resp.json()
            obs = data['observation']
            done = data['done']
        except Exception as e:
            break 
            
        step_count += 1
        # FIX: The time.sleep(4) has been completely removed. Go as fast as the API allows.

    try:
        # FIX: Added 10-second timeout
        grade_resp = requests.get(f"{API_URL}/grade", timeout=10.0).json()
        score = grade_resp.get('score', 0.0)
    except Exception:
        score = 0.0

    print(f"END task={task_name} score={score}", flush=True)

if __name__ == "__main__":
    # Wait for the FastAPI server to boot up before firing the first task
    for _ in range(15):
        try:
            requests.get(API_URL, timeout=2.0)
            break # Server is awake!
        except requests.exceptions.ConnectionError:
            time.sleep(1) # Wait 1 second and check again
            
    # Now run the evaluation safely
    for task in ["easy", "medium", "hard"]:
        run_task(task)