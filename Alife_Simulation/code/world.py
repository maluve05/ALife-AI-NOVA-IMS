"""
world.py

The spatial stage manager and state arbiter.
Handles coordinates, grid cell occupancies, movement validations,
collisions, food sprouting, and mating/gestation execution.
"""
import random
import math
from typing import List, Tuple, Dict, Any, Optional
from code.prey import Prey
from code.predator import Predator
from code.food import Food

class World:
    def __init__(self, cols: int, rows: int, params: Dict[str, Any]):
        """
        Initializes the simulation stage.
        :param cols: Width of the grid matrix (default: 15)
        :param rows: Height of the grid matrix (default: 20)
        :param params: Simulation configurations
        """
        self.cols = cols
        self.rows = rows
        self.params = params
        self.total_cells = cols * rows
        
        # State tracking lists
        self.prey_list: List[Prey] = []
        self.predator_list: List[Predator] = []
        self.food_list: List[Food] = []
        
        # Grid array for cells state check: 0=Empty, 1=Predator, 2=Food, 3=Prey
        self.grid: List[List[int]] = [[0] * self.cols for _ in range(self.rows)]
        
        # Unstepped tracker for food regeneration
        self.unstepped_ticks: List[List[int]] = [[0] * self.cols for _ in range(self.rows)]
        
        # Next entity IDs
        self.next_prey_id = 1
        self.next_predator_id = 1
        
        # Perform initial placement of entities
        self.initialize_world()

    def get_cell_value(self, x: int, y: int) -> int:
        """Helper to get cell value safely."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.grid[y][x]
        return 4  # Wall

    def sync_grid(self):
        """Syncs the 2D grid matrix with coordinates of active entities."""
        # 1. Clear grid
        for y in range(self.rows):
            for x in range(self.cols):
                self.grid[y][x] = 0
                
        # 2. Draw Food
        for f in self.food_list:
            if 0 <= f.x < self.cols and 0 <= f.y < self.rows:
                self.grid[f.y][f.x] = 2
                
        # 3. Draw Prey (Prey overrides food if overlap occurs, which shouldn't under normal steps)
        for p in self.prey_list:
            if 0 <= p.x < self.cols and 0 <= p.y < self.rows:
                self.grid[p.y][p.x] = 3
                
        # 4. Draw Predators
        for pred in self.predator_list:
            if 0 <= pred.x < self.cols and 0 <= pred.y < self.rows:
                self.grid[pred.y][pred.x] = 1

    def initialize_world(self):
        """
        Runs initial placement engine satisfying counts, Sudoku layouts,
        and buffer constraints.
        """
        prey_count = self.params.get("INITIAL_PREY_COUNT", 75)
        predator_count = self.params.get("INITIAL_PREDATOR_COUNT", 25)
        
        # 1. Spawn Predators (Sudoku Unique Stride Layout)
        pred_coords = []
        for i in range(predator_count):
            # Deterministic modular stride spacing
            r = (i * 7) % self.rows
            c = (i * 11) % self.cols
            # Overlap resolution
            attempts = 0
            while (c, r) in pred_coords and attempts < self.total_cells:
                r = (r + 1) % self.rows
                c = (c + 1) % self.cols
                attempts += 1
            pred_coords.append((c, r))
            
            p_obj = Predator(
                id_val=self.next_predator_id,
                name=f"{self.params.get('PREDATOR_NAME', 'Wsiloid')}_{self.next_predator_id}",
                x=c,
                y=r
            )
            p_obj.energy = 100.0
            self.predator_list.append(p_obj)
            self.next_predator_id += 1

        # Sync grid temporarily to check spacing for prey
        self.sync_grid()

        # 2. Spawn Prey (1-cell safety buffer from any predator)
        prey_placed = 0
        attempts = 0
        max_attempts = 5000
        
        while prey_placed < prey_count and attempts < max_attempts:
            attempts += 1
            rx = random.randint(0, self.cols - 1)
            ry = random.randint(0, self.rows - 1)
            
            # Must spawn on empty cell
            if self.grid[ry][rx] != 0:
                continue
                
            # Check 1-cell buffer from any Predator coordinate
            near_predator = False
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = rx + dx, ry + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        if self.grid[ny][nx] == 1:  # Predator
                            near_predator = True
                            break
                if near_predator:
                    break
                    
            if near_predator:
                continue
                
            # Valid coordinate: spawn
            prey_obj = Prey(
                id_val=self.next_prey_id,
                name=f"{self.params.get('PREY_NAME', 'Zizoid')}_{self.next_prey_id}",
                x=rx,
                y=ry
            )
            prey_obj.energy = self.params.get("INITIAL_ENERGY_PREY", 100.0)
            self.prey_list.append(prey_obj)
            self.next_prey_id += 1
            prey_placed += 1
            
            # Sync grid to reflect newly placed prey
            self.sync_grid()

        # 3. Spawn Food (Floor Fill remaining empty cells)
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    f_obj = Food(x=x, y=y, base_value=self.params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                    self.food_list.append(f_obj)
                    
        # Final sync
        self.sync_grid()

    def find_nearest_empty_cell(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        Executes concentric spiral searches outward from coordinates (x, y)
        to find the absolute closest empty cell.
        """
        max_radius = max(self.cols, self.rows)
        for r in range(1, max_radius):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    # Only search perimeter of radius r
                    if abs(dx) == r or abs(dy) == r:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows:
                            if self.grid[ny][nx] == 0:
                                return nx, ny
                                
        # Global fallback: Scan row-by-row
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 0:
                    return c, r
        return None

    def execute_crossover(self, p1: Prey, p2: Prey) -> List[float]:
        """
        Combines Parent A and Parent B chromosomes using one of the three strategies.
        Selects strategy randomly.
        """
        strategy = random.choice([1, 2, 3])
        length = 712  # Total genome length
        child_chromo = [0.0] * length
        
        if strategy == 1:
            # 1. Single Point Split (A | B)
            pivot = random.randint(1, length - 2)
            child_chromo[:pivot] = p1.chromosome[:pivot]
            child_chromo[pivot:] = p2.chromosome[pivot:]
        elif strategy == 2:
            # 2. Reverse Single Point Split (B | A)
            pivot = random.randint(1, length - 2)
            child_chromo[:pivot] = p2.chromosome[:pivot]
            child_chromo[pivot:] = p1.chromosome[pivot:]
        else:
            # 3. Alternating Block Swap
            # Divide genome into 5 logical blocks:
            # - Block 1: hidden layer weights row 0-3 (4*81 = 324)
            # - Block 2: hidden layer weights row 4-7 (4*81 = 324)
            # - Block 3: hidden biases (8)
            # - Block 4: output layer weights (48)
            # - Block 5: output biases & base traits (6 + 2 = 8)
            block_boundaries = [0, 324, 648, 656, 704, 712]
            for b_idx in range(5):
                start = block_boundaries[b_idx]
                end = block_boundaries[b_idx + 1]
                # Alternate source
                if b_idx % 2 == 0:
                    child_chromo[start:end] = p1.chromosome[start:end]
                else:
                    child_chromo[start:end] = p2.chromosome[start:end]
                    
        # 4. Mutation Filter
        mut_rate = self.params.get("MUTATION_RATE", 0.05)
        for i in range(length):
            if random.random() < mut_rate:
                # Gaussian mutation: Weight_new = Weight_old + N(0, 0.1^2)
                noise = random.gauss(0.0, 0.1)
                child_chromo[i] += noise
                # Clamp weights & traits to reasonable bounds
                if i < 710:
                    child_chromo[i] = max(-2.0, min(2.0, child_chromo[i]))
                else:
                    # Trait genes (efficiency, intelligence) should stay in positive bounds
                    child_chromo[i] = max(5.0, min(100.0, child_chromo[i]))
                    
        return child_chromo

    def handle_prey_mating(self):
        """
        Scans all adjacent prey pairs. If visibility and joint probability match,
        initiates mating gestation and deducts energy cost.
        """
        # Set of already mated IDs in this tick to avoid multiple matings in one step
        mated_ids = set()
        
        for i, p1 in enumerate(self.prey_list):
            if p1.id in mated_ids or p1.energy <= 10.0 or p1.is_pregnant:
                continue
                
            # Scan 8-neighborhood for other mating candidates
            for p2 in self.prey_list[i + 1:]:
                if p2.id in mated_ids or p2.energy <= 10.0 or p2.is_pregnant:
                    continue
                    
                # Adjacency check
                dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if dist < 2.0:  # Orthogonal (1.0) or Diagonal (1.414)
                    # Visibility check: can they see each other?
                    # Visible if distance is within their active vision radius
                    r1 = p1.get_vision_radius(self.total_cells)
                    r2 = p2.get_vision_radius(self.total_cells)
                    if dist <= r1 and dist <= r2:
                        # Probability Threshold Check: rand(0, 100) < P(A) * P(B)
                        p_a = p1.get_reproduction_probability(self.params)
                        p_b = p2.get_reproduction_probability(self.params)
                        joint_prob = p_a * p_b * 100.0  # scale from probability product to percentage
                        
                        if random.uniform(0, 100) < joint_prob:
                            # Trigger Gestation
                            p1.is_pregnant = True
                            p1.gestation_timer = 2
                            p2.is_pregnant = True
                            p2.gestation_timer = 2
                            
                            # Mating cost (3 movements' energy)
                            cost1 = 3.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p1.get_efficiency() / 10.0))
                            cost2 = 3.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p2.get_efficiency() / 10.0))
                            p1.energy -= cost1
                            p2.energy -= cost2
                            
                            # Mark as mated
                            mated_ids.add(p1.id)
                            mated_ids.add(p2.id)
                            break  # p1 is now busy mating

    def update(self):
        """
        Executes one full simulation step (Time Step Unit).
        Orchestrates entity locomotion, interactions, state shifts, and resource growth.
        """
        le = Prey(0, "", 0, 0).get_life_expectancy(self.params)

        # -------------------------------------------------------------
        # A. Update Food Growth
        # -------------------------------------------------------------
        # Unstepped tracker increment: cells with no predator (1), food (2), or prey (3)
        # gets unstepped increment.
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    self.unstepped_ticks[y][x] += 1
                    # If empty cell unstepped for 3 ticks, sprout food
                    if self.unstepped_ticks[y][x] >= 3:
                        f_obj = Food(x=x, y=y, base_value=self.params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                        self.food_list.append(f_obj)
                        self.unstepped_ticks[y][x] = 0  # reset unstepped counter
                else:
                    self.unstepped_ticks[y][x] = 0

        # Increment age of existing food resources to compound nutrition
        for f in self.food_list:
            f.step()

        # Sync grid state before agent decisions
        self.sync_grid()

        # -------------------------------------------------------------
        # B. Prey Action & State Resolution
        # -------------------------------------------------------------
        prey_to_remove = []
        newly_born_prey = []

        for p in self.prey_list:
            # 1. Pregnancy/Gestation Check
            if p.is_pregnant:
                p.gestation_timer -= 1
                p.age += 1
                p.energy -= self.params.get("GENERATIONAL_DECAY", 1.0)
                
                # Check natural death roll
                p_surv = p.get_survival_probability(le)
                if random.random() > p_surv or p.energy <= 0.0:
                    prey_to_remove.append(p)
                    continue
                    
                if p.gestation_timer <= 0:
                    p.is_pregnant = False
                    p.successful_offspring += 1
                    
                    # Spawn child coordinate
                    spawn_pos = self.find_nearest_empty_cell(p.x, p.y)
                    if spawn_pos and len(self.prey_list) < self.params.get("MAX_PREY_POPULATION", 300):
                        cx, cy = spawn_pos
                        # Parents find closest mating partner or average parent.
                        # For simplicity, we find the closest adjacent prey to p.
                        parent2 = p
                        min_d = float('inf')
                        for other in self.prey_list:
                            if other != p:
                                d = math.hypot(p.x - other.x, p.y - other.y)
                                if d < min_d:
                                    min_d = d
                                    parent2 = other
                        
                        # Generate chromosome
                        child_chromo = self.execute_crossover(p, parent2)
                        child = Prey(
                            id_val=self.next_prey_id,
                            name=f"{self.params.get('PREY_NAME', 'Zizoid')}_{self.next_prey_id}",
                            x=cx,
                            y=cy,
                            chromosome=child_chromo
                        )
                        child.energy = self.params.get("INITIAL_ENERGY_PREY", 100.0)
                        newly_born_prey.append(child)
                        self.next_prey_id += 1
                continue  # Pregnant prey does not move

            # 2. Forced Rest State Check
            if p.energy <= 0.0:
                p.age += 1
                # Recover energy equivalent to 1 movement tick
                rec_val = 1.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p.get_efficiency() / 10.0))
                p.energy = min(p.get_max_energy(self.params), p.energy + rec_val)
                
                # Check natural death roll
                p_surv = p.get_survival_probability(le)
                if random.random() > p_surv:
                    prey_to_remove.append(p)
                continue

            # 3. Decision Loop (ANN + A* Pathfinding)
            dx, dy, d_orient = p.get_action_step(self.grid, self.total_cells)
            
            # Apply rotation
            p.orientation = (p.orientation + d_orient) % 4
            
            # Calculate target move
            nx = p.x + dx
            ny = p.y + dy
            
            # Resolve velocity 1.5 Jump cadence
            is_running = (abs(dx) > 1 or abs(dy) > 1 or (dx != 0 and dy != 0 and (abs(dx) + abs(dy)) > 1))
            # Determine step offset distance
            if dx != 0 or dy != 0:
                # Alternate jump cadence
                if p.last_jumped:
                    # Cannot jump this turn: step normally (limit movement to 1 cell)
                    p.last_jumped = False
                    # clamp dx, dy to 1 cell step
                    dx = max(-1, min(1, dx))
                    dy = max(-1, min(1, dy))
                    nx = p.x + dx
                    ny = p.y + dy
                else:
                    # Jump is executed
                    p.last_jumped = True
            
            # Check cell validity
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                # Cell state: 0=Empty, 2=Food
                # (Prey cannot step on cells occupied by other Prey or Predators)
                target_val = self.grid[ny][nx]
                if target_val == 0 or target_val == 2:
                    p.x = nx
                    p.y = ny
                    
                    # Consume Food
                    if target_val == 2:
                        # Find and consume the Food object
                        food_obj = None
                        for f in self.food_list:
                            if f.x == nx and f.y == ny:
                                food_obj = f
                                break
                        if food_obj:
                            p.energy = min(p.get_max_energy(self.params), p.energy + food_obj.get_nutrition())
                            p.total_food_eaten += 1
                            self.food_list.remove(food_obj)
                            self.unstepped_ticks[ny][nx] = 0
                            
            # Calculate and subtract energy movement costs
            efficiency = p.get_efficiency()
            base_cost = self.params.get("GENERATIONAL_DECAY", 1.0)
            
            # If idle (no movement step)
            if dx == 0 and dy == 0:
                # Rest recovery
                p.energy = min(p.get_max_energy(self.params), p.energy + 1.0)
            else:
                # Movement cost: E = Base Cost / Efficiency
                move_cost = base_cost / max(1.0, efficiency / 10.0)
                if is_running:
                    # Run cost: 1.5 * normal cost
                    move_cost *= 1.5
                p.energy -= move_cost
                
            # Deduct flat generational decay
            p.energy -= base_cost
            p.age += 1
            
            # Check natural death roll
            p_surv = p.get_survival_probability(le)
            if random.random() > p_surv or p.energy < 0.0:
                prey_to_remove.append(p)

        # Apply prey lists update
        for p in prey_to_remove:
            if p in self.prey_list:
                self.prey_list.remove(p)
                
        self.prey_list.extend(newly_born_prey)
        self.sync_grid()

        # -------------------------------------------------------------
        # C. Mating Handshake Engine
        # -------------------------------------------------------------
        self.handle_prey_mating()
        self.sync_grid()

        # -------------------------------------------------------------
        # D. Predator Action & Resolution (Chase catch combat tax)
        # -------------------------------------------------------------
        predators_to_remove = []
        
        for pred in self.predator_list:
            dx, dy = pred.get_action_step(self.grid)
            
            # Alternate jump cadence if chasing
            is_running = pred.chase_state
            if is_running:
                if pred.last_jumped:
                    # Cannot jump, clamp step
                    pred.last_jumped = False
                    dx = max(-1, min(1, dx))
                    dy = max(-1, min(1, dy))
                else:
                    pred.last_jumped = True
                    
            nx = pred.x + dx
            ny = pred.y + dy
            
            # Check validity
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                target_val = self.grid[ny][nx]
                
                # Check collision with Prey (Catch state)
                if target_val == 3:  # Prey occupied
                    # Find the Prey agent
                    target_prey = None
                    for p in self.prey_list:
                        if p.x == nx and p.y == ny:
                            target_prey = p
                            break
                            
                    if target_prey:
                        # Inflict Heavy Combat Tax: drops prey energy heavily
                        combat_tax = 50.0
                        target_prey.energy -= combat_tax
                        
                        if target_prey.energy <= 0.0:
                            # Catch kills Prey
                            if target_prey in self.prey_list:
                                self.prey_list.remove(target_prey)
                            # Predator attributes boost (10% boost to tracking efficiency)
                            pred.tracking_efficiency = min(100.0, pred.tracking_efficiency * 1.1)
                            pred.energy = min(150.0, pred.energy + self.params.get("ENERGY_FROM_PREDATOR_CATCH", 10.0))
                        else:
                            # Prey escapes: Prey attributes get permanent 25% boost
                            target_prey.chromosome[710] = min(100.0, target_prey.base_efficiency * 1.25)
                            target_prey.chromosome[711] = min(100.0, target_prey.base_intelligence * 1.25)
                            
                            # Predator efficiency penalty
                            pred.tracking_efficiency = max(10.0, pred.tracking_efficiency * 0.9)
                            
                            # Push prey to adjacent cell
                            escape_pos = self.find_nearest_empty_cell(target_prey.x, target_prey.y)
                            if escape_pos:
                                target_prey.x, target_prey.y = escape_pos
                                
                    # Predator steps into cell
                    pred.x = nx
                    pred.y = ny
                elif target_val == 0 or target_val == 2:
                    # Predator steps into Empty/Food
                    pred.x = nx
                    pred.y = ny
                    # Note: Predator does not eat Food, just steps on it
                    if target_val == 2:
                        # Food is crushed/exhausted: remove it
                        food_obj = None
                        for f in self.food_list:
                            if f.x == nx and f.y == ny:
                                food_obj = f
                                break
                        if food_obj:
                            self.food_list.remove(food_obj)
                            self.unstepped_ticks[ny][nx] = 0

            # Energy consumption for predator
            action_str = 'run' if is_running else ('idle' if (dx == 0 and dy == 0) else 'move')
            pred.apply_decay(self.params, action_str)
            pred.age += 1
            
            # Starvation condition
            if pred.energy <= 0.0:
                predators_to_remove.append(pred)

        # Clean dead predators
        for pred in predators_to_remove:
            if pred in self.predator_list:
                self.predator_list.remove(pred)

        # Environmental Stabilizer: Respawn predators if count drops to protect pressure
        min_predators = self.params.get("INITIAL_PREDATOR_COUNT", 25)
        while len(self.predator_list) < min_predators:
            # Respawn at random empty cell
            spawn_pos = self.find_nearest_empty_cell(random.randint(0, self.cols - 1), random.randint(0, self.rows - 1))
            if spawn_pos:
                cx, cy = spawn_pos
                p_obj = Predator(
                    id_val=self.next_predator_id,
                    name=f"{self.params.get('PREDATOR_NAME', 'Wsiloid')}_{self.next_predator_id}",
                    x=cx,
                    y=cy
                )
                p_obj.energy = 100.0
                p_obj.tracking_efficiency = 50.0
                self.predator_list.append(p_obj)
                self.next_predator_id += 1

        self.sync_grid()
