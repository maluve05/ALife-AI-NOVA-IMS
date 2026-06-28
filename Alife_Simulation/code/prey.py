import math
import random
from typing import List, Tuple, Dict, Any, Optional
from code.ANNprey import ANNPrey

class Prey:
    def __init__(self, prey_id: int, name: str, x: int, y: int, chromosome: Optional[List[float]] = None):
        self.id = prey_id
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
                padding_length = 712 - len(self.chromosome)
                self.chromosome += [random.uniform(-1.0, 1.0)] * padding_length
        
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
    def get_life_expectancy(parameters: Dict[str, Any]) -> float:
        initial_energy = parameters.get("INITIAL_ENERGY_PREY", 100.0)
        prey_count = parameters.get("INITIAL_PREY_COUNT", 30)
        predator_count = parameters.get("INITIAL_PREDATOR_COUNT", 5)
        return 0.03125 * initial_energy * (1.0 + prey_count / (predator_count + 1.0))

    def get_gaussian_scaling(self, life_expectancy: float) -> float:
        mean_age = life_expectancy / 2.0
        standard_deviation = life_expectancy / 4.0
        if standard_deviation <= 0.0:
            return 1.0
        exponent = -0.5 * ((self.age - mean_age) / standard_deviation) ** 2
        return math.exp(exponent)

    def get_max_energy(self, parameters: Dict[str, Any]) -> float:
        life_expectancy = self.get_life_expectancy(parameters)
        gaussian_scale = self.get_gaussian_scaling(life_expectancy)
        base_max_energy = parameters.get("INITIAL_ENERGY_PREY", 100.0)
        return base_max_energy * max(0.50, gaussian_scale)

    def get_reproduction_probability(self, parameters: Dict[str, Any]) -> float:
        life_expectancy = self.get_life_expectancy(parameters)
        gaussian_scale = self.get_gaussian_scaling(life_expectancy)
        base_reproduction_probability = parameters.get("P_REPRODUCTION", 0.50)
        return base_reproduction_probability * gaussian_scale

    def get_efficiency(self) -> float:
        growth_constant = 15.0
        return min(100.0, self.base_efficiency + growth_constant * math.log(self.age + 1.0))

    def get_intelligence(self) -> float:
        growth_constant = 15.0
        return min(100.0, self.base_intelligence + growth_constant * math.log(self.age + 1.0))

    def get_survival_probability(self, life_expectancy: float) -> float:
        if life_expectancy <= 1.0:
            return 0.0
        denominator = life_expectancy * (math.log(life_expectancy) - 1.0)
        if denominator > 0:
            decay_constant = 0.70 / denominator
        else:
            decay_constant = 0.005
        return max(0.0, 1.0 - decay_constant * math.log(self.age + 1.0))

    def get_vision_radius(self, total_cells: int) -> int:
        intelligence = self.get_intelligence()
        max_radius = max(1, int(total_cells ** 0.25))
        if intelligence < 25.0:
            radius = 1
        elif intelligence < 50.0:
            radius = 2
        elif intelligence < 75.0:
            radius = 3
        else:
            radius = 4
        return min(radius, max_radius)

    def get_fitness(self, weight_age=1.0, weight_food=1.5, weight_offspring=5.0, weight_efficiency=0.5) -> float:
        return (weight_age * self.age) + (weight_food * self.total_food_eaten) + (weight_offspring * self.successful_offspring) + (weight_efficiency * self.get_efficiency())

    def get_absolute_coords(self, relative_x: int, relative_y: int) -> Tuple[int, int]:
        if self.orientation == 0:
            offset_x = relative_x
            offset_y = -relative_y
        elif self.orientation == 1:
            offset_x = relative_y
            offset_y = relative_x
        elif self.orientation == 2:
            offset_x = -relative_x
            offset_y = relative_y
        else:
            offset_x = -relative_y
            offset_y = -relative_x
        return self.x + offset_x, self.y + offset_y

    def get_vision_vector(self, grid: List[List[int]], total_cells: int) -> List[float]:
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        radius = self.get_vision_radius(total_cells)
        
        vision_vector = self._get_vision_signal(grid, radius, rows, cols)
        
        hunger = self.energy / 100.0
        vision_vector.append(float(max(0.0, min(1.0, hunger))))
        return vision_vector

    def _get_ring_coords(self, distance_radius: int) -> List[Tuple[int, int]]:
        ring = []
        for relative_x in range(-distance_radius, distance_radius + 1):
            ring.append((relative_x, distance_radius))
        for relative_y in range(distance_radius - 1, -distance_radius - 1, -1):
            ring.append((distance_radius, relative_y))
        for relative_x in range(distance_radius - 1, -distance_radius - 1, -1):
            ring.append((relative_x, -distance_radius))
        for relative_y in range(-distance_radius + 1, distance_radius):
            ring.append((-distance_radius, relative_y))
        return ring

    def _get_vision_signal(self, grid: List[List[int]], radius: int, rows: int, cols: int) -> List[float]:
        vision_vector = []
        for distance_radius in range(1, 5):
            ring = self._get_ring_coords(distance_radius)
            for relative_x, relative_y in ring:
                if distance_radius <= radius:
                    absolute_x, absolute_y = self.get_absolute_coords(relative_x, relative_y)
                    if 0 <= absolute_x < cols and 0 <= absolute_y < rows:
                        vision_vector.append(float(grid[absolute_y][absolute_x]) / 4.0)
                    else:
                        vision_vector.append(1.0)
                else:
                    vision_vector.append(0.0)
        return vision_vector

    def parse_action(self, action_index: int) -> Tuple[int, int, int]:
        relative_x, relative_y, orientation_change = 0, 0, 0
        if action_index == 0:
            relative_x, relative_y = 1, 1
        elif action_index == 1:
            relative_x, relative_y = -1, 1
        elif action_index == 2:
            relative_x, relative_y = 0, 1
        elif action_index == 3:
            relative_x, relative_y = 0, -1
        elif action_index == 4:
            orientation_change = 1
        elif action_index == 5:
            pass
            
        if relative_x == 0 and relative_y == 0:
            return 0, 0, orientation_change
            
        absolute_x, absolute_y = self.get_absolute_coords(relative_x, relative_y)
        step_x = absolute_x - self.x
        step_y = absolute_y - self.y
        return step_x, step_y, orientation_change

    def get_action_step(self, grid: List[List[int]], total_cells: int) -> Tuple[int, int, int]:
        input_vector = self.get_vision_vector(grid, total_cells)
        output_probabilities = self.ann.compute(input_vector)
        action_index = random.choices(range(len(output_probabilities)), weights=output_probabilities, k=1)[0]
        return self.parse_action(action_index)
