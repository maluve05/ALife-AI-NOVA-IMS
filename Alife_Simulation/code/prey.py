import math
import random
from typing import List, Tuple, Dict, Any, Optional
from code.ANNprey import ANNPrey

class Prey:
    def __init__(self, id_val: int, name: str, x: int, y: int, chromosome: Optional[List[float]] = None):
        self.id = id_val
        self.name = name
        self.x = x
        self.y = y
        self.orientation = random.randint(0, 3)
        self.age = 0
        self.gestation_timer = 0
        self.is_pregnant = False
        self.last_jumped = False
        self.total_food_eaten = 0
        self.successful_offspring = 0
        
        if chromosome is None:
            self.chromosome = [random.uniform(-0.3, 0.3) for _ in range(710)]
            self.chromosome.append(random.uniform(10.0, 30.0))
            self.chromosome.append(random.uniform(10.0, 30.0))
        else:
            self.chromosome = list(chromosome)
            if len(self.chromosome) < 712:
                self.chromosome += [random.uniform(-1.0, 1.0)] * (712 - len(self.chromosome))
        
        self.ann = ANNPrey()
        self.ann.set_weights_from_chromosome(self.chromosome[:710])
        self.energy = 100.0

    @property
    def base_efficiency(self) -> float:
        return self.chromosome[710]

    @property
    def base_intelligence(self) -> float:
        return self.chromosome[711]

    @staticmethod
    def get_life_expectancy(params: Dict[str, Any]) -> float:
        init_energy = params.get("INITIAL_ENERGY_PREY", 100.0)
        prey_count = params.get("INITIAL_PREY_COUNT", 30)
        predator_count = params.get("INITIAL_PREDATOR_COUNT", 5)
        return init_energy * (1.0 + prey_count / (predator_count + 1.0))

    def get_gaussian_scaling(self, le: float) -> float:
        mu = le / 2.0
        sigma = le / 4.0
        if sigma <= 0.0:
            return 1.0
        exponent = -0.5 * ((self.age - mu) / sigma) ** 2
        return math.exp(exponent)

    def get_max_energy(self, params: Dict[str, Any]) -> float:
        le = self.get_life_expectancy(params)
        scale = self.get_gaussian_scaling(le)
        base_max_energy = params.get("INITIAL_ENERGY_PREY", 100.0)
        return base_max_energy * max(0.50, scale)

    def get_reproduction_probability(self, params: Dict[str, Any]) -> float:
        le = self.get_life_expectancy(params)
        scale = self.get_gaussian_scaling(le)
        base_rep_prob = params.get("P_REPRODUCTION", 0.50)
        return base_rep_prob * scale

    def get_efficiency(self) -> float:
        growth_constant = 15.0
        return min(100.0, self.base_efficiency + growth_constant * math.log(self.age + 1.0))

    def get_intelligence(self) -> float:
        growth_constant = 15.0
        return min(100.0, self.base_intelligence + growth_constant * math.log(self.age + 1.0))

    def get_survival_probability(self, le: float) -> float:
        if le <= 1.0:
            return 0.0
        denom = le * (math.log(le) - 1.0)
        if denom > 0:
            k = 0.70 / denom
        else:
            k = 0.005
        return max(0.0, 1.0 - k * math.log(self.age + 1.0))

    def get_vision_radius(self, total_cells: int) -> int:
        intel = self.get_intelligence()
        max_radius = max(1, int(total_cells ** 0.25))
        if intel < 25.0:
            radius = 1
        elif intel < 50.0:
            radius = 2
        elif intel < 75.0:
            radius = 3
        else:
            radius = 4
        return min(radius, max_radius)

    def get_fitness(self, w1=1.0, w2=1.5, w3=5.0, w4=0.5) -> float:
        return (w1 * self.age) + (w2 * self.total_food_eaten) + (w3 * self.successful_offspring) + (w4 * self.get_efficiency())

    def get_absolute_coords(self, rx: int, ry: int) -> Tuple[int, int]:
        if self.orientation == 0:
            dx = rx
            dy = -ry
        elif self.orientation == 1:
            dx = ry
            dy = rx
        elif self.orientation == 2:
            dx = -rx
            dy = ry
        else:
            dx = -ry
            dy = -rx
        return self.x + dx, self.y + dy

    def get_vision_vector(self, grid: List[List[int]], total_cells: int) -> List[float]:
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        radius = self.get_vision_radius(total_cells)
        vision_vector = []
        for d in range(1, 5):
            ring = []
            for rx in range(-d, d + 1): ring.append((rx, d))
            for ry in range(d - 1, -d - 1, -1): ring.append((d, ry))
            for rx in range(d - 1, -d - 1, -1): ring.append((rx, -d))
            for ry in range(-d + 1, d): ring.append((-d, ry))
            
            for rx, ry in ring:
                if d <= radius:
                    ax, ay = self.get_absolute_coords(rx, ry)
                    if 0 <= ax < cols and 0 <= ay < rows:
                        vision_vector.append(float(grid[ay][ax]) / 4.0)
                    else:
                        vision_vector.append(1.0)
                else:
                    vision_vector.append(0.0)
                    
        hunger = self.energy / 100.0
        vision_vector.append(float(max(0.0, min(1.0, hunger))))
        return vision_vector

    def parse_action(self, action_idx: int) -> Tuple[int, int, int]:
        rx, ry, d_orient = 0, 0, 0
        if action_idx == 0:
            rx, ry = 1, 1
        elif action_idx == 1:
            rx, ry = -1, 1
        elif action_idx == 2:
            rx, ry = 0, 1
        elif action_idx == 3:
            rx, ry = 0, -1
        elif action_idx == 4:
            d_orient = 1
        elif action_idx == 5:
            pass
            
        if rx == 0 and ry == 0:
            return 0, 0, d_orient
            
        ax, ay = self.get_absolute_coords(rx, ry)
        dx = ax - self.x
        dy = ay - self.y
        return dx, dy, d_orient

    def get_action_step(self, grid: List[List[int]], total_cells: int) -> Tuple[int, int, int]:
        input_vec = self.get_vision_vector(grid, total_cells)
        output_probs = self.ann.compute(input_vec)
        action_idx = random.choices(range(len(output_probs)), weights=output_probs, k=1)[0]
        return self.parse_action(action_idx)
