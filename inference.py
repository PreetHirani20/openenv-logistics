import os
import requests
import json
import time
from openai import OpenAI

# --- 1. STRICT CHECKLIST COMPLIANCE: ENVIRONMENT VARIABLES ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN") # CRITICAL: No default value here per checklist

# Hackathon uses HF_TOKEN, but we keep a local fallback so you can still test it
api_key = HF_TOKEN or os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")

# --- 2. STRICT CHECKLIST COMPLIANCE: OPENAI CLIENT ---
client = OpenAI(
    api_key=api_key,
    base_url=API_BASE_URL,
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
    
    Return ONLY a JSON object:
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
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            time.sleep(3)
            
    return {
        "thought_process": "Fallback due to API error.",
        "action_type": "wait",
        "shipment_ids": [],
        "target_edge_id": ""
    }

def run_task(task_name):
    # --- 3. STRICT CHECKLIST COMPLIANCE: START LOG ---
    print(f"START task={task_name}")
    
    try:
        resp = requests.post(f"{API_URL}/reset?task={task_name}")
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"END task={task_name} score=0.0")
        return
        
    done = False
    step_count = 0
    
    while not done:
        action = get_action_from_llm(obs)
        
        # --- 4. STRICT CHECKLIST COMPLIANCE: STEP LOG ---
        print(f"STEP step={step_count} action={action.get('action_type')}")
        
        try:
            step_resp = requests.post(f"{API_URL}/step", json=action)
            step_resp.raise_for_status()
            data = step_resp.json()
            obs = data['observation']
            done = data['done']
        except Exception as e:
            break 
            
        step_count += 1
        time.sleep(4)

    try:
        grade_resp = requests.get(f"{API_URL}/grade").json()
        score = grade_resp.get('score', 0.0)
    except Exception:
        score = 0.0

    # --- 5. STRICT CHECKLIST COMPLIANCE: END LOG ---
    print(f"END task={task_name} score={score}")

if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_task(task)