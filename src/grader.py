import json
from typing import Dict, Any

class LogisticsGrader:
    def evaluate(self, env_state: Dict[str, Any]) -> float:
        """Returns a strict float between 0.0 and 1.0 per OpenEnv specs."""
        shipments = env_state.get("shipments", [])
        total_shipments = len(shipments)
        
        if total_shipments == 0:
            return 0.0
            
        delivered = [s for s in shipments if s.get("status") == "delivered"]
        spoiled = [s for s in shipments if s.get("status") == "spoiled"]
        
        # 1. Base Score (Max 0.7 for just getting things delivered)
        base_score = (len(delivered) / total_shipments) * 0.7
        
        # 2. Heavy Penalty for Spoilage
        spoilage_penalty = (len(spoiled) / total_shipments) * 0.4
        
        # 3. Efficiency Bonus (Max 0.3 for saving money and carbon)
        budget = env_state.get("budget", 0.0)
        carbon = env_state.get("carbon_footprint_kg", 0.0)
        
        # Dynamic targets based on the number of shipments
        target_budget = 8000.0 * total_shipments
        target_carbon = 350.0 * total_shipments
        
        cost_efficiency = min(1.0, target_budget / max(1, budget)) if budget > 0 else 0.0
        carbon_efficiency = min(1.0, target_carbon / max(1, carbon)) if carbon > 0 else 0.0
        
        efficiency_bonus = (cost_efficiency * 0.15) + (carbon_efficiency * 0.15)
        
        # Calculate final score and strictly clamp between 0.0 and 1.0
        final_score = base_score + efficiency_bonus - spoilage_penalty
        return max(0.0, min(1.0, round(final_score, 4)))