# 🌍 Global Logistics Dispatcher (OpenEnv)

[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-1.0-blue.svg)]()
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

> A stochastic, multi-modal supply chain simulator designed to test frontier LLMs on real-world freight consolidation, cold-chain management, and carbon-cost tradeoffs.

---

## 🚀 The Problem: Real-World Utility

Most AI benchmarks test simple logic puzzles or static Q&A. In the real enterprise world, AI agents are being deployed to manage supply chains—a domain defined by **Pareto tradeoffs**.

**Global Logistics Dispatcher** models the actual daily challenges of a freight forwarder. To succeed, an LLM agent must navigate:

1. **The Cold Chain:** Perishable cargo decays daily. It must be routed through specific, expensive `supports_reefer` lanes.
2. **Consolidation Economics:** Grouping cargo at the same node yields a massive 40% cost discount, forcing the AI to weigh the cost of "waiting" against the discount of "consolidating."
3. **The Carbon vs. Cost Dilemma:** Air freight saves perishable food but destroys the sustainability index. Ocean freight is cheap and green but slow.
4. **Stochastic Chaos:** A daily 15% probability of global disruptions (Port Strikes, Fuel Surcharges) forces the AI to dynamically reroute cargo mid-transit.

---

## 🧠 Environment Design & Mechanics

### Observation Space

At each step, the environment provides the agent with the current state of the world, including active shipments, dynamic local routing options (edges), and active global alerts.
```json
{
  "current_day": 2,
  "active_shipments": [
    {
      "id": "PERISH-BOM-01",
      "weight_kg": 500.0,
      "commodity": "perishable",
      "status": "warehoused",
      "current_node": "INBOM",
      "days_until_deadline": 10,
      "shelf_life_days_remaining": 8,
      "is_consolidated": false
    }
  ],
  "local_edges": {
    "INBOM": [
      {
        "edge_id": "LANE-002",
        "mode": "air",
        "cost_per_kg": 5.0,
        "transit_days": 1,
        "supports_reefer": true
      }
    ]
  },
  "global_alerts": ["SEVERE: Global port congestion expected."]
}
```

### Action Space

The agent responds with a strictly typed JSON object mapping to one of three core logistics actions:
```json
{
  "thought_process": "Brief explanation of the strategy.",
  "action_type": "dispatch_leg",
  "shipment_ids": ["PERISH-BOM-01"],
  "target_edge_id": "LANE-002"
}
```

---

## 📈 Task Difficulty & Progression

The environment exposes 3 strict tasks via `reset(task_name="...")` to evaluate agent scaling:

| Level | Task | Description |
|-------|------|-------------|
| 🟢 | `easy` | Route standard cargo globally without perishability constraints. Tests basic pathfinding and cost optimization. |
| 🟡 | `medium` | Manage a mix of standard and perishable cargo. Tests the agent's ability to prioritize the cold-chain and utilize multi-modal transport. |
| 🔴 | `hard` | Optimize consolidation and cold-chain routing amidst multiple active shipments and a high probability of severe port strikes/chaos. Tests dynamic rerouting and failure recovery. |

---

## ⚖️ Evaluation & Grader (0.0 to 1.0)

The environment features a deterministic mathematical grader that returns a strict `0.0` to `1.0` score based on the OpenEnv spec.

| Component | Weight | Description |
|-----------|--------|-------------|
| **Base Score** | Up to `0.7` | Awarded for successfully delivering shipments before their deadlines. |
| **Spoilage Penalty** | `-0.5` | Massive deduction if the AI fails to use reefer-lanes and cargo perishes. |
| **Efficiency Bonus** | Up to `0.3` | Evaluates the Pareto frontier of the run. Agents earn fractions of this bonus by beating algorithmic benchmarks for Target Budget and Target Carbon Footprint. |

---

## 🛠️ Setup & Reproducibility

### 1. Local Installation

Clone the repository and install the dependencies:
```bash
git clone https://github.com/PreetHirani20/global-logistics-dispatcher.git
cd global-logistics-dispatcher
pip install -r requirements.txt
```

### 2. Run the OpenEnv Server

Launch the FastAPI environment physics engine:
```bash
uvicorn src.server:app --host 0.0.0.0 --port 8000
```

### 3. Run the Baseline Agent

In a separate terminal, run the baseline inference script. This script uses the OpenAI-compatible client to run all 3 OpenEnv tasks sequentially.
```bash
export OPENAI_API_KEY="your_api_key_here"
export API_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
export MODEL_NAME="gemini-2.5-flash"
python inference.py
```

### 4. Docker & Hugging Face Spaces Deployment

The environment is fully containerized and ready for HF Spaces validation.
```bash
docker build -t openenv-logistics .
docker run -p 8000:8000 openenv-logistics
```

---

## 👤 Author & License

**Author:** Preet &nbsp;|&nbsp; **License:** [MIT](LICENSE)