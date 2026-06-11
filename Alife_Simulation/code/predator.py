"""
predator.py

State representation and heuristic state machine logic for Predators (Wsiloids / Mites).
Has no brain or genetic array. Executes an erratic random walk unless triggered
by proximity chase reflex steps.
"""
import random
import math
from typing import List, Tuple, Optional, Any, Dict

class Predator:
    def __init__(self, id_val: int, name: str, x: int, y: int):
        """
        Initializes a Predator agent.
        :param id_val: Unique identifier
        :param name: Display name
        :param x: Initial column index
        :param y: Initial row index
        """
        self.id = id_val
        self.name = name
        self.x = x
        self.y = y
        self.age = 0
        self.energy = 100.0
        self.tracking_efficiency = 50.0  # Base efficiency coefficient (10.0 to 100.0)
        self.last_jumped = False  # Momentum alternation for chase speed 1.5
        self.chase_state = False  # True when in immediate pursuit

    def get_action_step(self, grid: List[List[int]]) -> Tuple[int, int]:
        """
        Heuristic targeting logic:
        1. Proximity Chase Exception: Scan immediate 8-neighborhood. If any cell contains
           a Prey (value 3), enter Chase State and take a reflex step straight toward it.
        2. Search: If no Prey is adjacent, execute an erratic pseudo-random grid step.
        Returns relative grid offset (dx, dy).
        """
        rows = len(grid)
        cols = len(grid[0])
        
        # Scan 8-neighborhood for Prey (value 3)
        prey_adjacent = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    if grid[ny][nx] == 3:  # Prey
                        prey_adjacent.append((dx, dy))
                        
        if prey_adjacent:
            # Proximity Chase trigger
            self.chase_state = True
            # Choose one of the adjacent prey cells to step towards
            dx, dy = random.choice(prey_adjacent)
            return dx, dy
        else:
            # Idle or Search (erratic pseudo-random step)
            self.chase_state = False
            # Search mode: random step into empty (0) or food (2) cells
            valid_moves = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = self.x + dx, self.y + dy
                    if 0 <= nx < cols and 0 <= ny < rows:
                        # Wsiloid can step onto Empty (0) or Food (2)
                        # (If it steps on Prey (3), it triggers a Catch, handled by world update)
                        if grid[ny][nx] == 0 or grid[ny][nx] == 2:
                            valid_moves.append((dx, dy))
            
            if valid_moves:
                return random.choice(valid_moves)
            return 0, 0  # Stay in place if completely blocked

    def apply_decay(self, params: Dict[str, Any], action_type: str):
        """
        Deducts energy based on action type and tracking efficiency.
        Action types: 'idle', 'move', 'run'
        """
        base_cost = params.get("GENERATIONAL_DECAY", 1.0)
        
        if action_type == 'idle':
            # Idle / Rest: Gain +1 movement's equivalent energy
            self.energy += 1.0
        elif action_type == 'move':
            # Normal movement: E = Base / Efficiency
            cost = base_cost / max(1.0, self.tracking_efficiency / 10.0)
            self.energy -= cost
        elif action_type == 'run':
            # Run/Chase movement: E = 1.5 * (Base / Efficiency)
            cost = 1.5 * (base_cost / max(1.0, self.tracking_efficiency / 10.0))
            self.energy -= cost

        # Flat generational decay is added
        self.energy -= base_cost
        if self.energy < 0.0:
            self.energy = 0.0
