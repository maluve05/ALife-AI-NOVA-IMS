# Telemetry Data Analysis & Schema Guide

This document defines the data schemas for simulation logging and checkpointing, and provides recipes for data analytics.

---

## 1. CSV Telemetry Log Schema (`simulation_1.csv`)

Telemetry metrics are appended periodically (governed by `LOGGING_INTERVAL`, default every 15 ticks).

| Column Name | Data Type | Description |
|---|---|---|
| `Tick` | Integer | Epoch / simulation time-step index. |
| `PreyCount` | Integer | Total active Prey population in the environment. |
| `PredatorCount` | Integer | Total active Predator population in the environment. |
| `FoodCount` | Integer | Total food entities available on the grid. |
| `AvgEnergy` | Float | Mean energy reserve across all alive Prey agents. |
| `AvgIntelligence` | Float | Mean effective intelligence ($0 - 100$) across alive Prey. |
| `AvgEfficiency` | Float | Mean effective metabolic efficiency ($0 - 100$) across alive Prey. |
| `EliteChromosome` | JSON String | Array of 712 floats representing the genome of the highest-age agent. |

---

## 2. JSON State Checkpoint Schema (`simulation_state.json`)

Contains full snapshot data to restore the simulation world seamlessly:

```json
{
  "current_tick": 450,
  "next_prey_id": 892,
  "next_predator_id": 26,
  "parameters": {
    "GRID_WIDTH": 20,
    "GRID_HEIGHT": 25,
    "INITIAL_ENERGY_PREY": 150,
    "MUTATION_RATE": 0.05,
    ...
  },
  "best_prey_ever": {
    "id": 142,
    "name": "Zizoid_142",
    "age": 128,
    "energy": 94.2,
    "food_eaten": 35,
    "offspring": 8,
    "fitness": 215.5,
    "intelligence": 78.4,
    "efficiency": 82.1
  },
  "best_predator_ever": {
    "id": 4,
    "name": "Wsiloid_4",
    "age": 210,
    "energy": 120.0,
    "catches": 18,
    "tracking_efficiency": 85.2,
    "fitness": 2010.0
  },
  "best_mating_pair_ever": {
    "mating_fitness": 412.0,
    "parent1": { ... },
    "parent2": { ... },
    "child": { ... }
  },
  "death_causes": {
    "Starvation": 420,
    "Old Age": 312,
    "Predation": 156
  },
  "prey": [
    {
      "id": 1,
      "name": "Zizoid_1",
      "x": 12,
      "y": 8,
      "energy": 142.5,
      "age": 45,
      "gestation_timer": 0,
      "is_pregnant": false,
      "last_jumped": false,
      "total_food_eaten": 12,
      "successful_offspring": 3,
      "chromosome": [ ... 712 floats ... ]
    }
  ],
  "predators": [ ... ],
  "food": [ ... ]
}
```

---

## 3. Data Processing with Python & Pandas

Example Python snippet to load telemetry and compute summary metrics:

```python
import pandas as pd
import json

# Read CSV log
df = pd.read_csv("simulation_1.csv")

# Compute rolling average population
df["Prey_MA"] = df["PreyCount"].rolling(window=5).mean()

# Extract elite base traits
df["Elite_Efficiency"] = df["EliteChromosome"].apply(
    lambda s: json.loads(s)[710] if pd.notnull(s) and len(json.loads(s)) >= 712 else None
)
df["Elite_Intelligence"] = df["EliteChromosome"].apply(
    lambda s: json.loads(s)[711] if pd.notnull(s) and len(json.loads(s)) >= 712 else None
)

print(df[["Tick", "PreyCount", "PredatorCount", "AvgIntelligence", "Elite_Intelligence"]].tail(10))
```

---

## 4. Generating Visual Reports

Run the included `analyze.py` script:

```bash
python Alife_Simulation/analyze.py --csv simulation_1.csv --plot analytics_summary.png --export-json run_metrics.json
```
