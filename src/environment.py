import json
import os
import random
from typing import Dict, Any, List
from .models import (
    Observation, LogisticsAction, StepResponse, Shipment, 
    ShipmentStatus, CarrierEdge, TransportMode, CommodityType
)

class LogisticsEnv:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(self.seed)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(base_dir, "data", "graph.json")
        
        with open(self.data_path, "r") as f:
            graph_data = json.load(f)
            self.nodes = graph_data["nodes"]
            self.edges = graph_data["edges"]
            
        self.current_day = 0
        self.budget_spent = 0.0
        self.carbon_footprint = 0.0
        self.active_shipments: List[Shipment] = []
        self.global_alerts: List[str] = []

    def _get_local_edges(self, node_id: str) -> List[CarrierEdge]:
        return [
            CarrierEdge(
                edge_id=e["edge_id"],
                source_node=e["source"],
                target_node=e["target"],
                mode=TransportMode(e["mode"]),
                carrier_name=e["carrier"],
                cost_per_kg=e["cost_per_kg"],
                transit_days=e["transit_days"],
                capacity_kg_remaining=e["capacity_kg"],
                supports_reefer=e["supports_reefer"]
            )
            for e in self.edges if e["source"] == node_id
        ]

    def _trigger_chaos(self):
        """Randomly injects global disruptions to challenge the AI."""
        chaos_events = [
            "Fuel Surcharge: +20% cost for all Air routes.",
            "Port Strike: Ocean transit delayed by 7 days.",
            "Customs Crackdown: +2 days for all international legs."
        ]
        if random.random() < 0.15: # 15% chance of disruption per day
            event = random.choice(chaos_events)
            if event not in self.global_alerts:
                self.global_alerts.append(event)

    def _apply_daily_physics(self, days: int):
        """Calculates holding costs and shelf-life decay over time."""
        for _ in range(days):
            self.current_day += 1
            self._trigger_chaos()
            for s in self.active_shipments:
                if s.status in [ShipmentStatus.WAREHOUSED, ShipmentStatus.CUSTOMS_HOLD]:
                    # Holding cost: $10 per CBM per day
                    self.budget_spent += (s.volume_cbm * 10.0)
                
                if s.shelf_life_days_remaining is not None and s.status != ShipmentStatus.DELIVERED:
                    s.shelf_life_days_remaining -= 1
                    if s.shelf_life_days_remaining <= 0:
                        s.status = ShipmentStatus.SPOILED

    def reset(self, task_name: str = "medium") -> Observation:
        """Spawns different scenarios based on the OpenEnv task difficulty."""
        self.current_day = 0
        self.budget_spent = 0.0
        self.carbon_footprint = 0.0
        self.active_shipments = []
        self.global_alerts = ["System Online. Monitoring global transit lanes."]
        
        # --- TASK 1: EASY ---
        if task_name == "easy":
            self.active_shipments = [
                Shipment(
                    id="EASY-STD-01", origin_node="INBOM", destination_node="USLAX",
                    weight_kg=1000.0, volume_cbm=5.0, commodity=CommodityType.STANDARD,
                    status=ShipmentStatus.WAREHOUSED, current_node="INBOM", 
                    days_until_deadline=40 # Lots of time, no spoilage
                )
            ]
            
        # --- TASK 3: HARD ---
        elif task_name == "hard":
            self.global_alerts.append("SEVERE: Global port congestion expected.")
            self.active_shipments = [
                Shipment(
                    id="HARD-PERISH-01", origin_node="INBOM", destination_node="USLAX",
                    weight_kg=500.0, volume_cbm=2.5, commodity=CommodityType.PERISHABLE,
                    status=ShipmentStatus.WAREHOUSED, current_node="INBOM", 
                    days_until_deadline=12, shelf_life_days_remaining=8 # Very tight!
                ),
                Shipment(
                    id="HARD-PERISH-02", origin_node="SGSIN", destination_node="NLRTM",
                    weight_kg=800.0, volume_cbm=4.0, commodity=CommodityType.PERISHABLE,
                    status=ShipmentStatus.WAREHOUSED, current_node="SGSIN", 
                    days_until_deadline=25, shelf_life_days_remaining=15
                ),
                Shipment(
                    id="HARD-STD-03", origin_node="INBOM", destination_node="NLRTM",
                    weight_kg=3000.0, volume_cbm=15.0, commodity=CommodityType.STANDARD,
                    status=ShipmentStatus.WAREHOUSED, current_node="INBOM", 
                    days_until_deadline=35
                )
            ]
            
        # --- TASK 2: MEDIUM (Default) ---
        else: 
            self.active_shipments = [
                Shipment(
                    id="MED-PERISH-01", origin_node="INBOM", destination_node="USLAX",
                    weight_kg=500.0, volume_cbm=2.5, commodity=CommodityType.PERISHABLE,
                    status=ShipmentStatus.WAREHOUSED, current_node="INBOM", 
                    days_until_deadline=12, shelf_life_days_remaining=10
                ),
                Shipment(
                    id="MED-STD-02", origin_node="INBOM", destination_node="USLAX",
                    weight_kg=2000.0, volume_cbm=10.0, commodity=CommodityType.STANDARD,
                    status=ShipmentStatus.WAREHOUSED, current_node="INBOM", 
                    days_until_deadline=30
                )
            ]
            
        return self._get_observation()

    def _get_observation(self) -> Observation:
        edges_map = {}
        for s in self.active_shipments:
            if s.status not in [ShipmentStatus.DELIVERED, ShipmentStatus.SPOILED]:
                edges_map[s.current_node] = self._get_local_edges(s.current_node)

        return Observation(
            current_day=self.current_day,
            active_shipments=self.active_shipments,
            local_edges=edges_map,
            global_alerts=self.global_alerts,
            total_budget_spent=self.budget_spent
        )
    
    def state(self) -> Dict[str, Any]:
        """Returns the raw internal state of the world for the Grader."""
        return {
            "day": self.current_day,
            "budget": self.budget_spent,
            "carbon_footprint_kg": self.carbon_footprint,
            "shipments": [s.model_dump() for s in self.active_shipments]
        }

    def step(self, action: LogisticsAction) -> StepResponse:
        reward = 0.0
        info = {"logs": []}

        # --- PROCESS ACTIONS ---
        if action.action_type == "dispatch_leg":
            edge_data = next((e for e in self.edges if e["edge_id"] == action.target_edge_id), None)
            
            for sid in action.shipment_ids:
                shipment = next((s for s in self.active_shipments if s.id == sid), None)
                if not shipment or not edge_data or shipment.current_node != edge_data["source"]:
                    reward -= 2.0
                    continue

                # Advanced Multipliers from Chaos
                cost_mult = 1.0
                time_add = 0
                for alert in self.global_alerts:
                    if "Fuel" in alert and edge_data["mode"] == "air": cost_mult = 1.2
                    if "Strike" in alert and edge_data["mode"] == "ocean": time_add = 7

                # Reefer Check
                if shipment.commodity == CommodityType.PERISHABLE and not edge_data["supports_reefer"]:
                    shipment.status = ShipmentStatus.SPOILED
                    reward -= 10.0
                    continue

                # Execution
                discount = 0.6 if shipment.is_consolidated else 1.0
                total_cost = (shipment.weight_kg * edge_data["cost_per_kg"] * cost_mult) * discount
                self.budget_spent += total_cost
                
                # Carbon: Air is 10x worse than Sea
                carbon_factor = 0.5 if edge_data["mode"] == "air" else 0.05
                self.carbon_footprint += (shipment.weight_kg * carbon_factor)

                shipment.current_node = edge_data["target"]
                self._apply_daily_physics(edge_data["transit_days"] + time_add)

                if shipment.current_node == shipment.destination_node:
                    shipment.status = ShipmentStatus.DELIVERED
                    reward += 20.0 if self.current_day <= shipment.days_until_deadline else 5.0

        elif action.action_type == "consolidate":
            targets = [s for s in self.active_shipments if s.id in action.shipment_ids]
            if len(targets) >= 2 and len(set(s.current_node for s in targets)) == 1:
                for s in targets: s.is_consolidated = True
                reward += 2.0
            else:
                reward -= 1.0

        elif action.action_type == "wait":
            self._apply_daily_physics(1)
            reward -= 0.5

        done = all(s.status in [ShipmentStatus.DELIVERED, ShipmentStatus.SPOILED] for s in self.active_shipments)
        
        return StepResponse(
            observation=self._get_observation(),
            reward=reward,
            done=done,
            info=info,
            carbon_footprint_kg=self.carbon_footprint
        )