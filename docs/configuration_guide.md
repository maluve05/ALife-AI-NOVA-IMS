# Simulation Configuration & Parameter Guide

This document details all tunable simulation parameters, their biological/ecological implications, and preset configurations for scientific experimentation.

---

## 1. Parameters Reference Table

| Parameter | Type | Default | Description & Impact |
|---|---|---|---|
| `GRID_WIDTH` | Integer | `20` | Width of the 2D grid matrix in cells. (Total cells $\ge 300$). |
| `GRID_HEIGHT` | Integer | `25` | Height of the 2D grid matrix in cells. |
| `INITIAL_PREY_COUNT` | Integer | `60` | Starting population of Prey (`Zizoid`). |
| `INITIAL_PREDATOR_COUNT` | Integer | `5` | Starting population of Predators (`Wsiloid`). |
| `MAX_PREY_POPULATION` | Integer | `300` | Environmental carrying capacity ceiling for Prey. |
| `INITIAL_ENERGY_PREY` | Float | `150.0` | Initial energy endowment for Prey; directly scales life expectancy. |
| `ENERGY_FROM_CONSUMING_FOOD` | Float | `60.0` | Base nutritional caloric value gained from consuming food. |
| `ENERGY_FROM_PREDATOR_CATCH` | Float | `10.0` | Energy reward given to a Predator upon successful hunt. |
| `ENERGY_REPRODUCTION_COST` | Float | `3.0` | Multiplier for energy expenditure incurred during reproduction. |
| `MUTATION_RATE` | Float | `0.05` | Probability ($0.0 - 1.0$) of each gene mutating during reproduction. |
| `P_REPRODUCTION` | Float | `0.75` | Base probability ($0.0 - 1.0$) of mating when partners are in range. |
| `GENERATIONAL_DECAY` | Float | `1.0` | Base metabolic decay rate per tick. |
| `FRAME_RATE_LIMIT` | Float | `1.0` | Target simulation speed / frame rate limit in FPS/TPS. |
| `LOGGING_INTERVAL` | Integer | `15` | Checkpoint and CSV metrics recording frequency in ticks. |
| `PREY_NAME` | String | `"Zizoid"` | Display taxonomy name for Prey. |
| `PREDATOR_NAME` | String | `"Wsiloid"` | Display taxonomy name for Predator. |

---

## 2. Using Custom Configurations

You can pass configuration overrides via JSON files:

```bash
python main.py --config config_preset.json
```

Example `config_preset.json`:
```json
{
  "GRID_WIDTH": 30,
  "GRID_HEIGHT": 30,
  "INITIAL_PREY_COUNT": 80,
  "INITIAL_PREDATOR_COUNT": 8,
  "MUTATION_RATE": 0.08,
  "INITIAL_ENERGY_PREY": 180.0
}
```

---

## 3. Experimental Presets

### 3.1 Scenario: Rapid Evolution & Mutation Pressure
* **Goal**: Observe fast neuro-evolutionary adaptation and high trait variance.
* **Settings**:
  ```json
  {
    "MUTATION_RATE": 0.15,
    "P_REPRODUCTION": 0.85,
    "INITIAL_ENERGY_PREY": 200.0,
    "INITIAL_PREDATOR_COUNT": 6
  }
  ```

### 3.2 Scenario: High Predation Pressure & Evasion Selection
* **Goal**: Select for high intelligence, wide vision radius, and rapid diagonal sprinting.
* **Settings**:
  ```json
  {
    "INITIAL_PREDATOR_COUNT": 12,
    "ENERGY_FROM_PREDATOR_CATCH": 25.0,
    "MUTATION_RATE": 0.06,
    "MAX_PREY_POPULATION": 350
  }
  ```

### 3.3 Scenario: Resource Scarcity & Metabolic Efficiency
* **Goal**: Select for individuals with high base efficiency to minimize locomotion decay.
* **Settings**:
  ```json
  {
    "ENERGY_FROM_CONSUMING_FOOD": 30.0,
    "GENERATIONAL_DECAY": 1.5,
    "INITIAL_ENERGY_PREY": 100.0,
    "P_REPRODUCTION": 0.60
  }
  ```

### 3.4 Scenario: Stable Predator-Prey Equilibrium (Lotka-Volterra Cycles)
* **Goal**: Induce sustained periodic oscillations in population densities.
* **Settings**:
  ```json
  {
    "GRID_WIDTH": 25,
    "GRID_HEIGHT": 25,
    "INITIAL_PREY_COUNT": 70,
    "INITIAL_PREDATOR_COUNT": 5,
    "ENERGY_FROM_CONSUMING_FOOD": 50.0,
    "ENERGY_FROM_PREDATOR_CATCH": 15.0,
    "P_REPRODUCTION": 0.70
  }
  ```
