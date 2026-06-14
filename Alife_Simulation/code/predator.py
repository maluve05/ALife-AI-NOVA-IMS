import random
from typing import List, Tuple, Any, Dict

class Predator:
    def __init__(self, id_val: int, name: str, x: int, y: int):
        self.id = id_val
        self.name = name
        self.x = x
        self.y = y
        self.age = 0
        self.energy = 100.0
        self.tracking_efficiency = 50.0
        self.last_jumped = False
        self.chase_state = False
        self.catches = 0

    def get_action_step(self, grid: List[List[int]]) -> Tuple[int, int]:
        rows = len(grid)
        cols = len(grid[0])
        
        prey_adjacent = self._find_adjacent_prey_moves(grid, rows, cols)
        if prey_adjacent:
            self.chase_state = True
            return random.choice(prey_adjacent)
            
        self.chase_state = False
        valid_moves = self._find_valid_moves(grid, rows, cols)
        if valid_moves:
            return random.choice(valid_moves)
        return 0, 0

    def _find_adjacent_prey_moves(self, grid: List[List[int]], rows: int, cols: int) -> List[Tuple[int, int]]:
        prey_adjacent = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    if grid[ny][nx] == 3:
                        prey_adjacent.append((dx, dy))
        return prey_adjacent

    def _find_valid_moves(self, grid: List[List[int]], rows: int, cols: int) -> List[Tuple[int, int]]:
        valid_moves = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    if grid[ny][nx] == 0 or grid[ny][nx] == 2:
                        valid_moves.append((dx, dy))
        return valid_moves

    def apply_failed_chase_penalty(self, params: Dict[str, Any]):
        base_cost = params.get("GENERATIONAL_DECAY", 1.0)
        cost = 1.5 * (base_cost / max(1.0, self.tracking_efficiency / 10.0))
        self.energy = max(0.0, self.energy - cost)

    def get_fitness(self) -> float:
        return self.catches * 100.0 + self.age
