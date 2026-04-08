import json
from typing import Dict, Any

class LogisticsGrader:
    def evaluate(self, env_state: Dict[str, Any]) -> float:
        """
        Returns a float STRICTLY between 0.0 and 1.0 (exclusive).
        Per Phase 2 spec: score must be in open interval (0, 1).
        """
        shipments = env_state.get("shipments", [])
        total_shipments = len(shipments)

        # Guard: no shipments → return minimum non-zero score
        if total_shipments == 0:
            return 0.001

        delivered = [s for s in shipments if s.get("status") == "delivered"]
        spoiled   = [s for s in shipments if s.get("status") == "spoiled"]

        # 1. Base Score: max 0.65 (not 0.7) — prevents hitting 1.0 when
        #    all shipments are delivered AND efficiency bonus is maxed.
        base_score = (len(delivered) / total_shipments) * 0.65

        # 2. Spoilage Penalty: max 0.4
        spoilage_penalty = (len(spoiled) / total_shipments) * 0.4

        # 3. Efficiency Bonus: max 0.25 (not 0.3) — keeps ceiling at 0.90
        budget = env_state.get("budget", 0.0)
        carbon = env_state.get("carbon_footprint_kg", 0.0)

        target_budget = 8000.0 * total_shipments
        target_carbon = 350.0  * total_shipments

        # If budget/carbon is 0 (nothing dispatched), give a tiny partial score
        # instead of 0.0 — this also prevents a 0.0 return on an all-wait episode.
        cost_efficiency   = min(0.95, target_budget / max(1, budget)) if budget > 0 else 0.05
        carbon_efficiency = min(0.95, target_carbon / max(1, carbon)) if carbon > 0 else 0.05

        efficiency_bonus = (cost_efficiency * 0.125) + (carbon_efficiency * 0.125)

        raw_score = base_score + efficiency_bonus - spoilage_penalty

        # HARD CLAMP to open interval (0.001, 0.999) — grader requirement
        return round(max(0.001, min(0.999, raw_score)), 4)