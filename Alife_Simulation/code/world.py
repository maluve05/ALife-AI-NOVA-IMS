import random
import math
from typing import List, Tuple, Dict, Any, Optional
try:
    from Alife_Simulation.code.prey import Prey
    from Alife_Simulation.code.predator import Predator
    from Alife_Simulation.code.food import Food
except ImportError:
    try:
        from code.prey import Prey
        from code.predator import Predator
        from code.food import Food
    except ImportError:
        from .prey import Prey
        from .predator import Predator
        from .food import Food

class World:
    def __init__(self, cols: int, rows: int, params: Dict[str, Any]):
        self.cols = cols
        self.rows = rows
        self.params = params
        self.total_cells = cols * rows
        
        self.prey_list: List[Prey] = []
        self.predator_list: List[Predator] = []
        self.food_list: List[Food] = []
        
        self.grid: List[List[int]] = [[0] * self.cols for _ in range(self.rows)]
        self.unstepped_ticks: List[List[int]] = [[0] * self.cols for _ in range(self.rows)]
        
        self.next_prey_id = 1
        self.next_predator_id = 1
        
        self.best_prey_ever = None
        self.best_predator_ever = None
        self.best_mating_pair_ever = None
        
        self.death_causes = {
            "Starvation": 0,
            "Old Age": 0,
            "Predation": 0
        }
        
        self.initialize_world()

    def get_cell_value(self, x: int, y: int) -> int:
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.grid[y][x]
        return 4

    def sync_grid(self):
        for y in range(self.rows):
            for x in range(self.cols):
                self.grid[y][x] = 0
                
        for f in self.food_list:
            if 0 <= f.x < self.cols and 0 <= f.y < self.rows:
                self.grid[f.y][f.x] = 2
                
        for p in self.prey_list:
            if 0 <= p.x < self.cols and 0 <= p.y < self.rows:
                self.grid[p.y][p.x] = 3
                
        for pred in self.predator_list:
            if 0 <= pred.x < self.cols and 0 <= pred.y < self.rows:
                self.grid[pred.y][pred.x] = 1

    def initialize_world(self):
        self._spawn_initial_predators()
        self.sync_grid()
        self._spawn_initial_prey()
        self._spawn_initial_food()
        self.sync_grid()

    def _spawn_initial_predators(self):
        predator_count = self.params.get("INITIAL_PREDATOR_COUNT", 5)
        pred_coords = []
        for i in range(predator_count):
            c, r = self._get_non_overlapping_predator_coords(i, pred_coords)
            pred_coords.append((c, r))
            self._spawn_single_predator(c, r)

    def _get_non_overlapping_predator_coords(self, index: int, pred_coords: List[Tuple[int, int]]) -> Tuple[int, int]:
        r = (index * 7) % self.rows
        c = (index * 11) % self.cols
        attempts = 0
        while (c, r) in pred_coords and attempts < self.total_cells:
            r = (r + 1) % self.rows
            c = (c + 1) % self.cols
            attempts += 1
        return c, r

    def _spawn_single_predator(self, x: int, y: int):
        p_obj = Predator(
            id_val=self.next_predator_id,
            name=f"{self.params.get('PREDATOR_NAME', 'Wsiloid')}_{self.next_predator_id}",
            x=x,
            y=y
        )
        p_obj.energy = 100.0
        self.predator_list.append(p_obj)
        self.next_predator_id += 1

    def _spawn_initial_prey(self):
        prey_count = self.params.get("INITIAL_PREY_COUNT", 30)
        prey_placed = 0
        attempts = 0
        max_attempts = 5000
        
        while prey_placed < prey_count and attempts < max_attempts:
            attempts += 1
            rx = random.randint(0, self.cols - 1)
            ry = random.randint(0, self.rows - 1)
            
            if self.grid[ry][rx] != 0:
                continue
                
            if self._is_near_predator(rx, ry):
                continue
                
            self._spawn_single_prey(rx, ry)
            prey_placed += 1
            self.sync_grid()

    def _is_near_predator(self, x: int, y: int) -> bool:
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny][nx] == 1:
                        return True
        return False

    def _spawn_single_prey(self, x: int, y: int):
        prey_obj = Prey(
            prey_id=self.next_prey_id,
            name=f"{self.params.get('PREY_NAME', 'Zizoid')}_{self.next_prey_id}",
            x=x,
            y=y
        )
        prey_obj.energy = self.params.get("INITIAL_ENERGY_PREY", 100.0)
        self.prey_list.append(prey_obj)
        self.next_prey_id += 1

    def _spawn_initial_food(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    f_obj = Food(x=x, y=y, base_value=self.params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                    self.food_list.append(f_obj)

    def find_nearest_empty_cell(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        max_radius = max(self.cols, self.rows)
        for r in range(1, max_radius):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if abs(dx) == r or abs(dy) == r:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows:
                            if self.grid[ny][nx] == 0:
                                return nx, ny
                                
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 0:
                    return c, r
        return None

    def execute_crossover(self, p1: Prey, p2: Prey) -> List[float]:
        strategy = random.choice([1, 2, 3])
        length = 712
        child_chromo = self._perform_crossover_strategy(p1, p2, strategy, length)
        mut_rate = self.params.get("MUTATION_RATE", 0.05)
        return self._mutate_chromosome(child_chromo, mut_rate, length)

    def _perform_crossover_strategy(self, p1: Prey, p2: Prey, strategy: int, length: int) -> List[float]:
        child_chromo = [0.0] * length
        if strategy == 1:
            pivot = random.randint(1, length - 2)
            child_chromo[:pivot] = p1.chromosome[:pivot]
            child_chromo[pivot:] = p2.chromosome[pivot:]
        elif strategy == 2:
            pivot = random.randint(1, length - 2)
            child_chromo[:pivot] = p2.chromosome[:pivot]
            child_chromo[pivot:] = p1.chromosome[pivot:]
        else:
            block_boundaries = [0, 324, 648, 656, 704, 712]
            for b_idx in range(5):
                start = block_boundaries[b_idx]
                end = block_boundaries[b_idx + 1]
                if b_idx % 2 == 0:
                    child_chromo[start:end] = p1.chromosome[start:end]
                else:
                    child_chromo[start:end] = p2.chromosome[start:end]
        return child_chromo

    def _mutate_chromosome(self, chromosome: List[float], mut_rate: float, length: int) -> List[float]:
        for i in range(length):
            if random.random() < mut_rate:
                noise = random.gauss(0.0, 0.1)
                chromosome[i] += noise
                if i < 710:
                    chromosome[i] = max(-2.0, min(2.0, chromosome[i]))
                else:
                    chromosome[i] = max(5.0, min(100.0, chromosome[i]))
        return chromosome

    def handle_prey_mating(self):
        mated_ids = set()
        for i, p1 in enumerate(self.prey_list):
            if not self._can_mate(p1, mated_ids):
                continue
                
            for p2 in self.prey_list[i + 1:]:
                if not self._can_mate(p2, mated_ids):
                    continue
                    
                if self._process_mating_pair(p1, p2):
                    mated_ids.add(p1.id)
                    mated_ids.add(p2.id)
                    break

    def _can_mate(self, p: Prey, mated_ids: set) -> bool:
        return not (p.id in mated_ids or p.energy <= 10.0 or p.is_pregnant)

    def _process_mating_pair(self, p1: Prey, p2: Prey) -> bool:
        dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
        if dist < 2.0:
            r1 = p1.get_vision_radius(self.total_cells)
            r2 = p2.get_vision_radius(self.total_cells)
            if dist <= r1 and dist <= r2:
                p_a = p1.get_reproduction_probability(self.params)
                p_b = p2.get_reproduction_probability(self.params)
                joint_prob = p_a * p_b * 100.0
                
                if random.uniform(0, 100) < joint_prob:
                    p1.is_pregnant = True
                    p1.gestation_timer = 2
                    p2.is_pregnant = True
                    p2.gestation_timer = 2
                    
                    cost1 = 6.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p1.get_efficiency() / 10.0))
                    cost2 = 6.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p2.get_efficiency() / 10.0))
                    p1.energy -= cost1
                    p2.energy -= cost2
                    return True
        return False

    def _update_food_growth(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    self.unstepped_ticks[y][x] += 1
                    if self.unstepped_ticks[y][x] >= 10:
                        f_obj = Food(x=x, y=y, base_value=self.params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                        self.food_list.append(f_obj)
                        self.unstepped_ticks[y][x] = 0
                else:
                    self.unstepped_ticks[y][x] = 0
                    
        for f in self.food_list:
            f.step()

    def _update_prey_agents(self, le: float):
        prey_to_remove: List[Prey] = []
        newly_born_prey: List[Prey] = []
        
        for p in self.prey_list:
            if p.is_pregnant:
                self._process_pregnant_prey(p, le, prey_to_remove, newly_born_prey)
            elif p.energy <= 0.0:
                p.age += 1
                rec_val = 1.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p.get_efficiency() / 10.0))
                p.energy = min(p.get_max_energy(self.params), p.energy + rec_val)
                if random.random() > p.get_survival_probability(le):
                    self.death_causes["Old Age"] += 1
                    prey_to_remove.append(p)
            else:
                self._process_active_prey(p, le, prey_to_remove)

        for p in prey_to_remove:
            if p in self.prey_list:
                self.prey_list.remove(p)
                
        self.prey_list.extend(newly_born_prey)

    def _process_pregnant_prey(self, p: Prey, le: float, prey_to_remove: List[Prey], newly_born_prey: List[Prey]):
        p.gestation_timer -= 1
        p.age += 1
        p.energy -= 2.0 * self.params.get("GENERATIONAL_DECAY", 1.0)
        
        if p.energy <= 0.0:
            self.death_causes["Starvation"] += 1
            prey_to_remove.append(p)
            return
            
        if random.random() > p.get_survival_probability(le):
            self.death_causes["Old Age"] += 1
            prey_to_remove.append(p)
            return
            
        if p.gestation_timer <= 0:
            p.is_pregnant = False
            p.successful_offspring += 1
            self._spawn_prey_offspring(p, newly_born_prey)

    def _spawn_prey_offspring(self, p: Prey, newly_born_prey: List[Prey]):
        spawn_pos = self.find_nearest_empty_cell(p.x, p.y)
        if not spawn_pos or len(self.prey_list) >= self.params.get("MAX_PREY_POPULATION", 300):
            return
            
        cx, cy = spawn_pos
        parent2 = p
        best_fitness = -1.0
        for other in self.prey_list:
            if other != p:
                d = math.hypot(p.x - other.x, p.y - other.y)
                if d <= 10.0:
                    fit = other.get_fitness()
                    if fit > best_fitness:
                        best_fitness = fit
                        parent2 = other
                        
        child_chromo = self.execute_crossover(p, parent2)
        child = Prey(
            prey_id=self.next_prey_id,
            name=f"{self.params.get('PREY_NAME', 'Zizoid')}_{self.next_prey_id}",
            x=cx,
            y=cy,
            chromosome=child_chromo
        )
        child.energy = self.params.get("INITIAL_ENERGY_PREY", 100.0)
        
        self._record_best_mating(p, parent2, child)
        newly_born_prey.append(child)
        self.next_prey_id += 1
        self.grid[cy][cx] = 3

    def _get_prey_record_dict(self, p: Prey) -> Dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "energy": p.energy,
            "food_eaten": p.total_food_eaten,
            "offspring": p.successful_offspring,
            "fitness": p.get_fitness(),
            "intelligence": p.get_intelligence(),
            "efficiency": p.get_efficiency()
        }

    def _record_best_mating(self, p1: Prey, p2: Prey, child: Prey):
        mating_fit = p1.get_fitness() + p2.get_fitness()
        if self.best_mating_pair_ever is None or mating_fit > self.best_mating_pair_ever["mating_fitness"]:
            self.best_mating_pair_ever = {
                "mating_fitness": mating_fit,
                "parent1": self._get_prey_record_dict(p1),
                "parent2": self._get_prey_record_dict(p2),
                "child": {
                    "id": child.id,
                    "name": child.name,
                    "energy": child.energy,
                    "intelligence": child.get_intelligence(),
                    "efficiency": child.get_efficiency(),
                    "fitness": child.get_fitness()
                }
            }

    def _process_active_prey(self, p: Prey, le: float, prey_to_remove: List[Prey]):
        dx, dy, d_orient = p.get_action_step(self.grid, self.total_cells)
        p.orientation = (p.orientation + d_orient) % 4
        
        is_running = (abs(dx) > 1 or abs(dy) > 1 or (dx != 0 and dy != 0 and (abs(dx) + abs(dy)) > 1))
        dx, dy = self._handle_prey_movement(p, dx, dy)
        
        self._apply_prey_energy_decay_and_age(p, is_running, dx, dy)
        self._check_prey_survival(p, le, prey_to_remove)

    def _handle_prey_movement(self, p: Prey, dx: int, dy: int) -> Tuple[int, int]:
        nx, ny = p.x + dx, p.y + dy
        if dx != 0 or dy != 0:
            if p.last_jumped:
                p.last_jumped = False
                dx, dy = max(-1, min(1, dx)), max(-1, min(1, dy))
                nx, ny = p.x + dx, p.y + dy
            else:
                p.last_jumped = True
                
        if 0 <= nx < self.cols and 0 <= ny < self.rows:
            target_val = self.grid[ny][nx]
            if target_val in (0, 2):
                self.grid[p.y][p.x] = 0
                p.x, p.y = nx, ny
                self.grid[ny][nx] = 3
                if target_val == 2:
                    self._prey_eat_food(p, nx, ny)
        return dx, dy

    def _apply_prey_energy_decay_and_age(self, p: Prey, is_running: bool, dx: int, dy: int):
        efficiency = p.get_efficiency()
        base_cost = self.params.get("GENERATIONAL_DECAY", 1.0)
        move_cost = base_cost / max(1.0, efficiency / 10.0)
        if is_running:
            move_cost *= 1.5
            
        p.energy -= 2.0 * (move_cost if (dx != 0 or dy != 0) else 0.0) + 2.0 * base_cost
        p.age += 1

    def _check_prey_survival(self, p: Prey, le: float, prey_to_remove: List[Prey]):
        if p.energy < 0.0:
            self.death_causes["Starvation"] += 1
            prey_to_remove.append(p)
        elif random.random() > p.get_survival_probability(le):
            self.death_causes["Old Age"] += 1
            prey_to_remove.append(p)

    def _prey_eat_food(self, p: Prey, x: int, y: int):
        food_obj = next((f for f in self.food_list if f.x == x and f.y == y), None)
        if food_obj:
            p.energy = min(p.get_max_energy(self.params), p.energy + food_obj.get_nutrition())
            p.total_food_eaten += 1
            self.food_list.remove(food_obj)
            self.unstepped_ticks[y][x] = 0

    def _update_predator_agents(self):
        for pred in self.predator_list:
            self._process_predator(pred)
        self._replenish_predators()

    def _process_predator(self, pred: Predator):
        dx, dy = pred.get_action_step(self.grid)
        if pred.chase_state:
            if pred.last_jumped:
                pred.last_jumped = False
                dx, dy = max(-1, min(1, dx)), max(-1, min(1, dy))
            else:
                pred.last_jumped = True
                
        nx, ny = pred.x + dx, pred.y + dy
        if 0 <= nx < self.cols and 0 <= ny < self.rows:
            target_val = self.grid[ny][nx]
            if target_val == 3:
                self._predator_hunt_prey(pred, nx, ny)
            elif target_val in (0, 2):
                self.grid[pred.y][pred.x] = 0
                pred.x, pred.y = nx, ny
                self.grid[ny][nx] = 1
                if target_val == 2:
                    self._predator_destroy_food(nx, ny)
        pred.age += 1

    def _predator_hunt_prey(self, pred: Predator, nx: int, ny: int):
        target_prey = next((p for p in self.prey_list if p.x == nx and p.y == ny), None)
        if target_prey:
            target_prey.energy -= 50.0
            if target_prey.energy <= 0.0:
                self._handle_successful_hunt(pred, target_prey)
            else:
                self._handle_escaped_hunt(pred, target_prey)
                    
        self.grid[pred.y][pred.x] = 0
        pred.x, pred.y = nx, ny
        self.grid[ny][nx] = 1

    def _handle_successful_hunt(self, pred: Predator, target_prey: Prey):
        self.grid[target_prey.y][target_prey.x] = 0
        if target_prey in self.prey_list:
            self.prey_list.remove(target_prey)
        pred.tracking_efficiency = min(100.0, pred.tracking_efficiency * 1.1)
        pred.energy = min(150.0, pred.energy + self.params.get("ENERGY_FROM_PREDATOR_CATCH", 10.0))
        pred.catches += 1
        self.death_causes["Predation"] += 1

    def _handle_escaped_hunt(self, pred: Predator, target_prey: Prey):
        target_prey.chromosome[710] = min(100.0, target_prey.base_efficiency * 1.25)
        target_prey.chromosome[711] = min(100.0, target_prey.base_intelligence * 1.25)
        pred.tracking_efficiency = max(10.0, pred.tracking_efficiency * 0.9)
        pred.apply_failed_chase_penalty(self.params)
        
        escape_pos = self.find_nearest_empty_cell(target_prey.x, target_prey.y)
        if escape_pos:
            self.grid[target_prey.y][target_prey.x] = 0
            target_prey.x, target_prey.y = escape_pos
            self.grid[escape_pos[1]][escape_pos[0]] = 3

    def _predator_destroy_food(self, x: int, y: int):
        food_obj = next((f for f in self.food_list if f.x == x and f.y == y), None)
        if food_obj:
            self.food_list.remove(food_obj)
            self.unstepped_ticks[y][x] = 0

    def _replenish_predators(self):
        min_predators = self.params.get("INITIAL_PREDATOR_COUNT", 25)
        while len(self.predator_list) < min_predators:
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
                self.grid[cy][cx] = 1

    def update(self):
        le = Prey.get_life_expectancy(self.params)
        self._update_food_growth()
        self.sync_grid()
        self._update_prey_agents(le)
        self.sync_grid()
        self.handle_prey_mating()
        self.sync_grid()
        self._update_predator_agents()
        self.sync_grid()
        self.update_historical_records()

    def update_historical_records(self):
        self._update_best_prey_record()
        self._update_best_predator_record()

    def _update_best_prey_record(self):
        for p in self.prey_list:
            fit = p.get_fitness()
            if (self.best_prey_ever is None or 
                fit > self.best_prey_ever["fitness"] or 
                p.id == self.best_prey_ever["id"]):
                self.best_prey_ever = self._get_prey_record_dict(p)
                self.best_prey_ever["fitness"] = fit

    def _update_best_predator_record(self):
        for pred in self.predator_list:
            fit = pred.get_fitness()
            if (self.best_predator_ever is None or 
                fit > self.best_predator_ever["fitness"] or 
                pred.id == self.best_predator_ever["id"]):
                self.best_predator_ever = {
                    "id": pred.id,
                    "name": pred.name,
                    "age": pred.age,
                    "energy": pred.energy,
                    "catches": pred.catches,
                    "tracking_efficiency": pred.tracking_efficiency,
                    "fitness": fit
                }
