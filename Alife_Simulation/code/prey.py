"""
prey.py

State representation, attribute calculations, relative locomotion,
mating logic, and high-level pathfinding (A*) for Prey (Zizoids / Midges).
"""
import math
import random
from typing import List, Tuple, Dict, Any, Optional
from code.ANNprey import ANNPrey

class Prey:
    def __init__(self, id_val: int, name: str, x: int, y: int, chromosome: Optional[List[float]] = None):
        """
        Initializes a Prey agent.
        :param id_val: Unique identifier
        :param name: Display name
        :param x: Initial column index
        :param y: Initial row index
        :param chromosome: 712-element genetic vector (710 neural + 2 base traits)
        """
        self.id = id_val
        self.name = name
        self.x = x
        self.y = y
        self.orientation = random.randint(0, 3)  # 0: North, 1: East, 2: South, 3: West
        self.age = 0
        self.gestation_timer = 0
        self.is_pregnant = False
        self.last_jumped = False  # Track alternate jump steps for velocity 1.5
        
        # Statistics for fitness evaluation
        self.total_food_eaten = 0
        self.successful_offspring = 0
        
        # Initialize chromosome: 710 ANN parameters + 2 base parameters (efficiency, intelligence)
        if chromosome is None:
            # Random initial chromosome in range [-1.0, 1.0]
            self.chromosome = [random.uniform(-1.0, 1.0) for _ in range(712)]
            # Map genes 710 and 711 to reasonable starting ranges [10.0, 30.0]
            self.chromosome[710] = random.uniform(10.0, 30.0)  # base_efficiency
            self.chromosome[711] = random.uniform(10.0, 30.0)  # base_intelligence
        else:
            self.chromosome = list(chromosome)
            if len(self.chromosome) < 712:
                # Pad to 712 elements
                self.chromosome += [random.uniform(-1.0, 1.0)] * (712 - len(self.chromosome))
        
        # Instantiate the neural brain
        self.ann = ANNPrey()
        self.ann.set_weights_from_chromosome(self.chromosome[:710])
        
        # Set base energy from global default (will be overwritten by world/simulation parameters)
        self.energy = 100.0

    @property
    def base_efficiency(self) -> float:
        return self.chromosome[710]

    @property
    def base_intelligence(self) -> float:
        return self.chromosome[711]

    def get_life_expectancy(self, params: Dict[str, Any]) -> float:
        """
        Predictive lifespan calculation based on configuration environment values.
        LE = INITIAL_ENERGY_PREY * (1 + INITIAL_PREY_COUNT / (INITIAL_PREDATOR_COUNT + 1))
        """
        init_energy = params.get("INITIAL_ENERGY_PREY", 100.0)
        prey_count = params.get("INITIAL_PREY_COUNT", 75)
        predator_count = params.get("INITIAL_PREDATOR_COUNT", 25)
        return init_energy * (1.0 + prey_count / (predator_count + 1.0))

    def get_gaussian_scaling(self, le: float) -> float:
        """
        Computes the Gaussian scaling factor peaking at mid-life (Age = LE/2).
        Uses sigma = LE / 4.
        """
        mu = le / 2.0
        sigma = le / 4.0
        if sigma <= 0.0:
            return 1.0
        # Normalization cancels out, yields a scaling factor bounded between [0.13, 1.0] over [0, LE]
        exponent = -0.5 * ((self.age - mu) / sigma) ** 2
        return math.exp(exponent)

    def get_max_energy(self, params: Dict[str, Any]) -> float:
        """Calculates current max energy capacity using Gaussian curve over lifespan."""
        le = self.get_life_expectancy(params)
        scale = self.get_gaussian_scaling(le)
        base_max_energy = params.get("INITIAL_ENERGY_PREY", 100.0)
        # Apply a floor of 50% of base_max_energy to protect young/old individuals from instant starvation
        return base_max_energy * max(0.50, scale)

    def get_reproduction_probability(self, params: Dict[str, Any]) -> float:
        """Calculates current reproduction probability capacity using Gaussian curve."""
        le = self.get_life_expectancy(params)
        scale = self.get_gaussian_scaling(le)
        base_rep_prob = params.get("P_REPRODUCTION", 0.50)
        return base_rep_prob * scale

    def get_efficiency(self) -> float:
        """Logarithmic scaling for efficiency growth: min(100, Base + 15 * ln(Age + 1))"""
        growth_constant = 15.0
        return min(100.0, self.base_efficiency + growth_constant * math.log(self.age + 1.0))

    def get_intelligence(self) -> float:
        """Logarithmic scaling for intelligence growth: min(100, Base + 15 * ln(Age + 1))"""
        growth_constant = 15.0
        return min(100.0, self.base_intelligence + growth_constant * math.log(self.age + 1.0))

    def get_survival_probability(self, le: float) -> float:
        """Logarithmic decay for survival probability: max(0, 1.0 - K * ln(Age + 1))"""
        if le <= 1.0:
            return 0.0
        # Calculate K such that cumulative survival probability to age LE is approximately 50%.
        # Stirlings approximation for log(LE!) is LE * ln(LE) - LE.
        denom = le * (math.log(le) - 1.0)
        if denom > 0:
            k = 0.70 / denom
        else:
            k = 0.005
        return max(0.0, 1.0 - k * math.log(self.age + 1.0))

    def get_vision_radius(self, total_cells: int) -> int:
        """
        Determines the vision radius based on intelligence milestones.
        Milestones:
          - Radius 1 (baseline): Intel < 25
          - Radius 2: 25 <= Intel < 50
          - Radius 3: 50 <= Intel < 75
          - Radius 4: Intel >= 75
        """
        intel = self.get_intelligence()
        max_radius = max(1, int(total_cells ** 0.25))  # floor((Total Grid Cells)^0.25)
        
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
        """
        Multi-attribute fitness function:
        w1*Age + w2*Energy_Harvested + w3*Offspring + w4*Efficiency
        """
        return (w1 * self.age) + (w2 * self.total_food_eaten) + (w3 * self.successful_offspring) + (w4 * self.get_efficiency())

    def get_relative_cells(self, radius: int) -> List[Tuple[int, int]]:
        """
        Generates relative offsets (rx, ry) for concentric vision rings up to 'radius',
        rotated according to the agent's current orientation.
        """
        relative_offsets = []
        for d in range(1, radius + 1):
            ring = []
            # 1. Front row: Left to Right (rx from -d to d, ry = d)
            for rx in range(-d, d + 1):
                ring.append((rx, d))
            # 2. Right side: Front to Back (rx = d, ry from d-1 to -d)
            for ry in range(d - 1, -d - 1, -1):
                ring.append((d, ry))
            # 3. Back row: Right to Left (rx from d-1 to -d, ry = -d)
            for rx in range(d - 1, -d - 1, -1):
                ring.append((rx, -d))
            # 4. Left side: Back to Front (rx = -d, ry from -d+1 to d-1)
            for ry in range(-d + 1, d):
                ring.append((-d, ry))
            relative_offsets.extend(ring)
        return relative_offsets

    def get_absolute_coords(self, rx: int, ry: int) -> Tuple[int, int]:
        """
        Converts relative coordinates (rx: right-positive, ry: front-positive)
        to absolute coordinates based on current heading.
        0: North, 1: East, 2: South, 3: West
        """
        if self.orientation == 0:  # North
            dx = rx
            dy = -ry
        elif self.orientation == 1:  # East
            dx = ry
            dy = rx
        elif self.orientation == 2:  # South
            dx = -rx
            dy = ry
        else:  # West
            dx = -ry
            dy = -rx
        return self.x + dx, self.y + dy

    def get_vision_vector(self, grid: List[List[int]], total_cells: int) -> List[float]:
        """
        Builds the 81-neuron input vector.
        Inputs: 80 vision cells (padded/masked if radius < 4) + 1 hunger float.
        Empty = 0, Predator = 1, Food = 2, Prey = 3, Wall/Out-of-bounds = 4.
        """
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        
        radius = self.get_vision_radius(total_cells)
        
        # 1. Construct vision features
        vision_vector = []
        
        # Maximum vision vector is for radius 4 (80 cells)
        max_radius = 4
        
        # Collect actual cells up to max_radius
        for d in range(1, max_radius + 1):
            # Ring cells offset for this d
            ring_offsets = []
            for rx in range(-d, d + 1):
                ring_offsets.append((rx, d))
            for ry in range(d - 1, -d - 1, -1):
                ring_offsets.append((d, ry))
            for rx in range(d - 1, -d - 1, -1):
                ring_offsets.append((rx, -d))
            for ry in range(-d + 1, d):
                ring_offsets.append((-d, ry))
                
            for rx, ry in ring_offsets:
                if d <= radius:
                    # Within active intelligence radius: fetch absolute grid value
                    ax, ay = self.get_absolute_coords(rx, ry)
                    if 0 <= ax < cols and 0 <= ay < rows:
                        vision_vector.append(float(grid[ay][ax]))
                    else:
                        vision_vector.append(4.0)  # Wall/Out of bounds
                else:
                    # Beyond active radius: mask/zero-pad
                    vision_vector.append(0.0)
                    
        # 2. Construct hunger sensor
        # Normalized energy level [0.0, 1.0] (cap at 1.0 if energy exceeds max)
        hunger = self.energy / 100.0
        vision_vector.append(float(max(0.0, min(1.0, hunger))))
        
        return vision_vector

    def parse_action(self, action_idx: int) -> Tuple[int, int, int]:
        """
        Parses output neuron index to grid changes.
        Returns (dx, dy, d_orientation) relative to current orientation.
        """
        # Rel: rx (Right+), ry (Front+)
        rx, ry, d_orient = 0, 0, 0
        
        if action_idx == 0:    # Move Left Leg -> Moves Front-Right
            rx, ry = 1, 1
        elif action_idx == 1:  # Move Right Leg -> Moves Front-Left
            rx, ry = -1, 1
        elif action_idx == 2:  # Move Both Legs -> Moves Forward
            rx, ry = 0, 1
        elif action_idx == 3:  # Move Both Legs Back -> Moves Backward
            rx, ry = 0, -1
        elif action_idx == 4:  # Rotate 90 CW
            d_orient = 1
        elif action_idx == 5:  # Idle
            pass
            
        # Convert relative to orientation offset
        if rx == 0 and ry == 0:
            return 0, 0, d_orient
            
        # We need absolute offsets
        ax, ay = self.get_absolute_coords(rx, ry)
        dx = ax - self.x
        dy = ay - self.y
        return dx, dy, d_orient

    def pathfind_to_goal(self, start: Tuple[int, int], goals: List[Tuple[int, int]], grid: List[List[int]], radius: int) -> Optional[Tuple[int, int]]:
        """
        Standard A* pathfinding.
        Finds the shortest path to the closest goal cell from the start position.
        Returns the first step coordinate along that path, or None if unreachable.
        Obstacles: grid values that block Prey (e.g., walls, other agents).
        We treat Empty(0) and Food(2) as traversable.
        """
        if not goals:
            return None
            
        rows = len(grid)
        cols = len(grid[0])
        goals_set = set(goals)
        
        # Priority Queue elements: (f_score, (x, y))
        # Open set tracks current candidates
        open_set = {start}
        
        # Track path history
        came_from = {}
        
        # Cost scores
        g_score = {start: 0}
        
        def heuristic(p: Tuple[int, int]) -> float:
            # Manhattan distance to nearest goal
            return min(abs(p[0] - g[0]) + abs(p[1] - g[1]) for g in goals)
            
        f_score = {start: heuristic(start)}
        
        while open_set:
            # Get node in open_set with lowest f_score
            current = min(open_set, key=lambda p: f_score.get(p, float('inf')))
            
            if current in goals_set:
                # Reconstruct path
                path = []
                temp = current
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.reverse()
                return path[0] if path else None
                
            open_set.remove(current)
            cx, cy = current
            
            # Neighbors (orthogonal & diagonal)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = cx + dx, cy + dy
                    # Restrict A* search strictly to cells within the agent's visible radius
                    if max(abs(nx - start[0]), abs(ny - start[1])) <= radius:
                        if 0 <= nx < cols and 0 <= ny < rows:
                            # Traversable check: Empty (0) or Food (2)
                            if grid[ny][nx] == 0 or grid[ny][nx] == 2:
                                neighbor = (nx, ny)
                                # Diagonal movement has cost sqrt(2) approx 1.4, normal has cost 1
                                step_cost = 1.414 if (dx != 0 and dy != 0) else 1.0
                                tentative_g_score = g_score[current] + step_cost
                                
                                if tentative_g_score < g_score.get(neighbor, float('inf')):
                                    came_from[neighbor] = current
                                    g_score[neighbor] = tentative_g_score
                                    f_score[neighbor] = tentative_g_score + heuristic(neighbor)
                                    if neighbor not in open_set:
                                        open_set.add(neighbor)
        return None

    def get_action_step(self, grid: List[List[int]], total_cells: int) -> Tuple[int, int, int]:
        """
        Combines ANN execution and A* pathfinding.
        Returns absolute grid offsets (dx, dy, d_orientation).
        """
        rows = len(grid)
        cols = len(grid[0])
        
        # 1. Pathfinding awareness scan: check targets within intelligence radius
        radius = self.get_vision_radius(total_cells)
        
        # Locate food and predator coordinates in active vision radius
        food_targets = []
        predator_targets = []
        
        for ry in range(-radius, radius + 1):
            for rx in range(-radius, radius + 1):
                if rx == 0 and ry == 0:
                    continue
                ax, ay = self.get_absolute_coords(rx, ry)
                if 0 <= ax < cols and 0 <= ay < rows:
                    val = grid[ay][ax]
                    if val == 2:  # Food
                        food_targets.append((ax, ay))
                    elif val == 1:  # Predator
                        predator_targets.append((ax, ay))
                        
        # 2. Check pathfinding override
        # Target pathfind rule: Run pathfinding to find food if not threatened,
        # or pathfind to run away from predators if predators are in range.
        if radius > 1:
            if predator_targets:
                # RUN AWAY: Find adjacent empty cells, calculate A* steps away
                # To simplify: we find the empty adjacent cell that maximizes distance from predators
                best_step = None
                max_dist = -1.0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = self.x + dx, self.y + dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if grid[ny][nx] == 0:
                                # Distance to nearest predator
                                min_pred_dist = min(math.hypot(nx - px, ny - py) for px, py in predator_targets)
                                if min_pred_dist > max_dist:
                                    max_dist = min_pred_dist
                                    best_step = (dx, dy)
                if best_step:
                    # We rotate towards the move step and execute
                    dx, dy = best_step
                    return dx, dy, 0
            elif food_targets:
                # Move towards food using A*
                next_step = self.pathfind_to_goal((self.x, self.y), food_targets, grid, radius)
                if next_step:
                    dx = next_step[0] - self.x
                    dy = next_step[1] - self.y
                    return dx, dy, 0
                    
        # 3. Default back to ANN computation
        input_vec = self.get_vision_vector(grid, total_cells)
        output_probs = self.ann.compute(input_vec)
        
        # Action with highest probability
        action_idx = output_probs.index(max(output_probs))
        return self.parse_action(action_idx)
