from typing import Dict, Any

# --- 1. Task Definitions ---
TASKS = {
    "easy_routing": {
        "description": "Route a single priority shipment before the deadline. Weather is clear.",
        "shipments": [
            {"id": "SHIP-E1", "origin": "JNPT", "destination": "LAX", "weight_kg": 1000.0, "priority": 3, "days_until_deadline": 15}
        ],
        "budget": 20000.0,
        "forced_event": "EVT-003" # Clear weather
    },
    "medium_cost_opt": {
        "description": "Route 3 shipments globally. Strict budget constraint.",
        "shipments": [
            {"id": "SHIP-M1", "origin": "FRA", "destination": "BOM", "weight_kg": 500.0, "priority": 1, "days_until_deadline": 25},
            {"id": "SHIP-M2", "origin": "LAX", "destination": "SGP", "weight_kg": 2000.0, "priority": 2, "days_until_deadline": 20},
            {"id": "SHIP-M3", "origin": "JNPT", "destination": "FRA", "weight_kg": 1000.0, "priority": 1, "days_until_deadline": 30}
        ],
        "budget": 30000.0,
        "forced_event": "EVT-003" # Clear weather
    },
    "hard_disruption": {
        "description": "Route critical shipments during a major ocean typhoon.",
        "shipments": [
            {"id": "SHIP-H1", "origin": "SGP", "destination": "LAX", "weight_kg": 1500.0, "priority": 3, "days_until_deadline": 8},
            {"id": "SHIP-H2", "origin": "BOM", "destination": "FRA", "weight_kg": 800.0, "priority": 2, "days_until_deadline": 12}
        ],
        "budget": 40000.0,
        "forced_event": "EVT-001" # Severe Typhoon (Forces agent to avoid Ocean freight)
    }
}

# --- 2. Deterministic Grader ---
class LogisticsGrader:
    @staticmethod
    def evaluate(state: Dict[str, Any], task_name: str) -> float:
        """
        Calculates a strict 0.0 to 1.0 score based on delivery success and budget management.
        """
        if task_name not in TASKS:
            return 0.0
            
        task_def = TASKS[task_name]
        shipments = state.get("shipments", [])
        total_budget = task_def["budget"]
        spent = state.get("budget_spent", 0.0)
        
        if not shipments:
            return 0.0

        # Calculate Delivery Success (70% of final score)
        delivered_count = sum(1 for s in shipments if s["status"] == "delivered")
        delivery_ratio = delivered_count / len(task_def["shipments"])
        
        # Calculate Budget Management (30% of final score)
        budget_score = 1.0
        if spent > total_budget:
            # If they go over budget, penalize them linearly
            overage = spent - total_budget
            penalty = overage / total_budget
            budget_score = max(0.0, 1.0 - penalty) # Floor at 0.0
            
        # Weighted Final Score
        final_score = (delivery_ratio * 0.7) + (budget_score * 0.3)
        
        return round(final_score, 2)