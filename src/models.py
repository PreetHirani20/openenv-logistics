from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class TransportMode(str, Enum):
    OCEAN = "ocean"
    AIR = "air"
    RAIL = "rail"
    TRUCK = "truck"

class CommodityType(str, Enum):
    STANDARD = "standard"
    HAZMAT = "hazmat"
    PERISHABLE = "perishable"

class ShipmentStatus(str, Enum):
    WAREHOUSED = "warehoused"
    IN_TRANSIT = "in_transit"
    CUSTOMS_HOLD = "customs_hold"
    SPOILED = "spoiled"
    DELIVERED = "delivered"

class TransitNode(BaseModel):
    id: str
    name: str
    supported_modes: List[TransportMode]
    customs_clearance_days_avg: float

class Shipment(BaseModel):
    id: str
    origin_node: str
    destination_node: str
    weight_kg: float
    volume_cbm: float
    commodity: CommodityType
    status: ShipmentStatus
    current_node: str
    days_until_deadline: int
    shelf_life_days_remaining: Optional[int] = None
    is_consolidated: bool = False
    parent_container_id: Optional[str] = None

class CarrierEdge(BaseModel):
    edge_id: str
    source_node: str
    target_node: str
    mode: TransportMode
    carrier_name: str
    cost_per_kg: float
    transit_days: int
    capacity_kg_remaining: float
    supports_reefer: bool

class LogisticsAction(BaseModel):
    action_type: str
    shipment_ids: List[str]
    target_edge_id: Optional[str] = None

class Observation(BaseModel):
    current_day: int
    active_shipments: List[Shipment]
    local_edges: Dict[str, List[CarrierEdge]]
    global_alerts: List[str]
    total_budget_spent: float
    available_actions: List[str] = Field(default=["dispatch_leg", "consolidate", "wait"])

class StepResponse(BaseModel):
    # BULLETPROOF: Exactly 4 keys per OpenEnv Spec. Extra data moved to 'info'
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]