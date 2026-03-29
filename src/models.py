from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# --- 1. Advanced Enums ---
class TransportMode(str, Enum):
    OCEAN = "ocean"
    AIR = "air"
    RAIL = "rail"
    TRUCK = "truck"

class CommodityType(str, Enum):
    STANDARD = "standard"        # Electronics, textiles
    HAZMAT = "hazmat"          # Chemicals, batteries (requires special carrier)
    PERISHABLE = "perishable"    # Food, pharmaceuticals (requires Reefer, has shelf-life)

class ShipmentStatus(str, Enum):
    WAREHOUSED = "warehoused"
    IN_TRANSIT = "in_transit"
    CUSTOMS_HOLD = "customs_hold"
    SPOILED = "spoiled"          # Failed state for perishables
    DELIVERED = "delivered"

# --- 2. Node Graph & Logistics Entities ---
class TransitNode(BaseModel):
    id: str = Field(description="UN/LOCODE, e.g., INBOM for Mumbai, USLAX for LA")
    name: str
    supported_modes: List[TransportMode]
    customs_clearance_days_avg: float

class Shipment(BaseModel):
    id: str
    origin_node: str
    destination_node: str
    weight_kg: float
    volume_cbm: float = Field(description="Cubic meters, used for container consolidation")
    commodity: CommodityType
    status: ShipmentStatus
    current_node: str
    days_until_deadline: int
    shelf_life_days_remaining: Optional[int] = Field(
        default=None, 
        description="If this reaches 0 before delivery, cargo spoils."
    )
    is_consolidated: bool = False
    parent_container_id: Optional[str] = None

class CarrierEdge(BaseModel):
    """Represents a specific travel lane between two nodes."""
    edge_id: str
    source_node: str
    target_node: str
    mode: TransportMode
    carrier_name: str
    cost_per_kg: float
    transit_days: int
    capacity_kg_remaining: float = Field(description="Agents must compete for space")
    supports_reefer: bool = Field(description="Required for perishable goods")

# --- 3. Complex Action Space ---
class LogisticsAction(BaseModel):
    """The agent can now do complex operational commands."""
    action_type: str = Field(
        description="Must be: 'dispatch_leg', 'consolidate', 'clear_customs', or 'wait'"
    )
    shipment_ids: List[str] = Field(
        description="List of shipments to act upon. Pass multiple to consolidate."
    )
    target_edge_id: Optional[str] = Field(
        default=None, 
        description="Required for 'dispatch_leg'. Must be a valid edge connected to current node."
    )

# --- 4. OpenEnv Specs ---
class Observation(BaseModel):
    current_day: int
    active_shipments: List[Shipment]
    local_edges: Dict[str, List[CarrierEdge]]
    global_alerts: List[str]
    total_budget_spent: float
    available_actions: List[str] = Field(default=["dispatch_leg", "consolidate", "wait"])

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]
    carbon_footprint_kg: float = 0.0

