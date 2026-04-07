import os
import requests
import json
import time
from openai import OpenAI

# --- OPENENV REQUIRED VARIABLES ---
# The hackathon validator will inject these variables automatically.
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini") # Standard OpenAI model
API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")

# If the grader provides a custom base URL (like an enterprise proxy), use it.
# Otherwise, default to standard OpenAI API.
API_BASE_URL = os.getenv("API_BASE_URL") 

if API_BASE_URL:
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
else:
    client = OpenAI(api_key=API_KEY)

API_URL = os.getenv("API_URL", "http://localhost:7860")

# ... (The rest of your functions stay exactly the same)

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
            print(f"⚠️ LLM or Parsing Error (Attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(3) # Wait before retrying
            
    # If all retries fail, return a safe fallback action so the script DOES NOT crash
    print("🚨 All retries failed. Returning safe fallback action.")
    return {
        "thought_process": "Fallback due to API error.",
        "action_type": "wait",
        "shipment_ids": [],
        "target_edge_id": ""
    }

def run_task(task_name):
    print(f"\n🚀 Starting Task: {task_name.upper()}...")
    try:
        resp = requests.post(f"{API_URL}/reset?task={task_name}")
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"❌ Failed to reset environment for {task_name}: {e}")
        return # Skip this task, but don't crash the script
        
    done = False
    
    while not done:
        action = get_action_from_llm(obs)
        time.sleep(4)
        print(f"[{task_name.upper()}] Day {obs.get('current_day', '?')} | Action: {action.get('action_type')} for {action.get('shipment_ids')}")
        
        try:
            step_resp = requests.post(f"{API_URL}/step", json=action)
            step_resp.raise_for_status()
            data = step_resp.json()
            obs = data['observation']
            done = data['done']
        except Exception as e:
            print(f"❌ Network/Environment error during step: {e}")
            break # Exit the loop safely without crashing the script
            
        time.sleep(4) # Rate limit protection

    try:
        grade_resp = requests.get(f"{API_URL}/grade").json()
        print(f"🏁 Final Score for {task_name.upper()}: {grade_resp.get('score', 0.0)} / 1.0")
    except Exception as e:
        print(f"❌ Failed to fetch grade: {e}")

if __name__ == "__main__":
    # OpenEnv requires testing on all 3 difficulties
    for task in ["easy", "medium", "hard"]:
        run_task(task)