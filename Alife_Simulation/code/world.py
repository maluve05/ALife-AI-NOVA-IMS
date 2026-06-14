import random
import math
from typing import List, Tuple, Dict, Any, Optional
from code.prey import Prey
from code.predator import Predator
from code.food import Food

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
        prey_count = self.params.get("INITIAL_PREY_COUNT", 30)
        predator_count = self.params.get("INITIAL_PREDATOR_COUNT", 5)
        
        pred_coords = []
        for i in range(predator_count):
            r = (i * 7) % self.rows
            c = (i * 11) % self.cols
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

        self.sync_grid()

        prey_placed = 0
        attempts = 0
        max_attempts = 5000
        
        while prey_placed < prey_count and attempts < max_attempts:
            attempts += 1
            rx = random.randint(0, self.cols - 1)
            ry = random.randint(0, self.rows - 1)
            
            if self.grid[ry][rx] != 0:
                continue
                
            near_predator = False
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = rx + dx, ry + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        if self.grid[ny][nx] == 1:
                            near_predator = True
                            break
                if near_predator:
                    break
                    
            if near_predator:
                continue
                
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
            
            self.sync_grid()

        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    f_obj = Food(x=x, y=y, base_value=self.params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                    self.food_list.append(f_obj)
                    
        self.sync_grid()

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
                    
        mut_rate = self.params.get("MUTATION_RATE", 0.05)
        for i in range(length):
            if random.random() < mut_rate:
                noise = random.gauss(0.0, 0.1)
                child_chromo[i] += noise
                if i < 710:
                    child_chromo[i] = max(-2.0, min(2.0, child_chromo[i]))
                else:
                    child_chromo[i] = max(5.0, min(100.0, child_chromo[i]))
                    
        return child_chromo

    def handle_prey_mating(self):
        mated_ids = set()
        for i, p1 in enumerate(self.prey_list):
            if p1.id in mated_ids or p1.energy <= 10.0 or p1.is_pregnant:
                continue
                
            for p2 in self.prey_list[i + 1:]:
                if p2.id in mated_ids or p2.energy <= 10.0 or p2.is_pregnant:
                    continue
                    
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
                            
                            mated_ids.add(p1.id)
                            mated_ids.add(p2.id)
                            break

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
        prey_to_remove = []
        newly_born_prey = []
        
        for p in self.prey_list:
            if p.is_pregnant:
                p.gestation_timer -= 1
                p.age += 1
                p.energy -= 2.0 * self.params.get("GENERATIONAL_DECAY", 1.0)
                
                p_surv = p.get_survival_probability(le)
                if p.energy <= 0.0:
                    self.death_causes["Starvation"] += 1
                    prey_to_remove.append(p)
                    continue
                elif random.random() > p_surv:
                    self.death_causes["Old Age"] += 1
                    prey_to_remove.append(p)
                    continue
                    
                if p.gestation_timer <= 0:
                    p.is_pregnant = False
                    p.successful_offspring += 1
                    
                    spawn_pos = self.find_nearest_empty_cell(p.x, p.y)
                    if spawn_pos and len(self.prey_list) < self.params.get("MAX_PREY_POPULATION", 300):
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
                            id_val=self.next_prey_id,
                            name=f"{self.params.get('PREY_NAME', 'Zizoid')}_{self.next_prey_id}",
                            x=cx,
                            y=cy,
                            chromosome=child_chromo
                        )
                        child.energy = self.params.get("INITIAL_ENERGY_PREY", 100.0)
                        
                        mating_fit = p.get_fitness() + parent2.get_fitness()
                        if self.best_mating_pair_ever is None or mating_fit > self.best_mating_pair_ever["mating_fitness"]:
                            self.best_mating_pair_ever = {
                                "mating_fitness": mating_fit,
                                "parent1": {
                                    "id": p.id,
                                    "name": p.name,
                                    "age": p.age,
                                    "energy": p.energy,
                                    "food_eaten": p.total_food_eaten,
                                    "offspring": p.successful_offspring,
                                    "fitness": p.get_fitness(),
                                    "intelligence": p.get_intelligence(),
                                    "efficiency": p.get_efficiency()
                                },
                                "parent2": {
                                    "id": parent2.id,
                                    "name": parent2.name,
                                    "age": parent2.age,
                                    "energy": parent2.energy,
                                    "food_eaten": parent2.total_food_eaten,
                                    "offspring": parent2.successful_offspring,
                                    "fitness": parent2.get_fitness(),
                                    "intelligence": parent2.get_intelligence(),
                                    "efficiency": parent2.get_efficiency()
                                },
                                "child": {
                                    "id": child.id,
                                    "name": child.name,
                                    "energy": child.energy,
                                    "intelligence": child.get_intelligence(),
                                    "efficiency": child.get_efficiency(),
                                    "fitness": child.get_fitness()
                                }
                            }
                            
                        newly_born_prey.append(child)
                        self.next_prey_id += 1
                        self.grid[cy][cx] = 3
                continue

            if p.energy <= 0.0:
                p.age += 1
                rec_val = 1.0 * (self.params.get("GENERATIONAL_DECAY", 1.0) / max(1.0, p.get_efficiency() / 10.0))
                p.energy = min(p.get_max_energy(self.params), p.energy + rec_val)
                
                p_surv = p.get_survival_probability(le)
                if random.random() > p_surv:
                    self.death_causes["Old Age"] += 1
                    prey_to_remove.append(p)
                continue

            dx, dy, d_orient = p.get_action_step(self.grid, self.total_cells)
            
            p.orientation = (p.orientation + d_orient) % 4
            
            nx = p.x + dx
            ny = p.y + dy
            
            is_running = (abs(dx) > 1 or abs(dy) > 1 or (dx != 0 and dy != 0 and (abs(dx) + abs(dy)) > 1))
            if dx != 0 or dy != 0:
                if p.last_jumped:
                    p.last_jumped = False
                    dx = max(-1, min(1, dx))
                    dy = max(-1, min(1, dy))
                    nx = p.x + dx
                    ny = p.y + dy
                else:
                    p.last_jumped = True
            
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                target_val = self.grid[ny][nx]
                if target_val == 0 or target_val == 2:
                    self.grid[p.y][p.x] = 0
                    p.x = nx
                    p.y = ny
                    self.grid[ny][nx] = 3
                    
                    if target_val == 2:
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
                            
            efficiency = p.get_efficiency()
            base_cost = self.params.get("GENERATIONAL_DECAY", 1.0)
            
            if dx != 0 or dy != 0:
                move_cost = base_cost / max(1.0, efficiency / 10.0)
                if is_running:
                    move_cost *= 1.5
                p.energy -= 2.0 * move_cost
                
            p.energy -= 2.0 * base_cost
            p.age += 1
            
            p_surv = p.get_survival_probability(le)
            if p.energy < 0.0:
                self.death_causes["Starvation"] += 1
                prey_to_remove.append(p)
            elif random.random() > p_surv:
                self.death_causes["Old Age"] += 1
                prey_to_remove.append(p)

        for p in prey_to_remove:
            if p in self.prey_list:
                self.prey_list.remove(p)
                
        self.prey_list.extend(newly_born_prey)

    def _update_predator_agents(self):
        for pred in self.predator_list:
            dx, dy = pred.get_action_step(self.grid)
            
            is_running = pred.chase_state
            if is_running:
                if pred.last_jumped:
                    pred.last_jumped = False
                    dx = max(-1, min(1, dx))
                    dy = max(-1, min(1, dy))
                else:
                    pred.last_jumped = True
                    
            nx = pred.x + dx
            ny = pred.y + dy
            
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                target_val = self.grid[ny][nx]
                
                if target_val == 3:
                    target_prey = None
                    for p in self.prey_list:
                        if p.x == nx and p.y == ny:
                            target_prey = p
                            break
                            
                    if target_prey:
                        combat_tax = 50.0
                        target_prey.energy -= combat_tax
                        
                        if target_prey.energy <= 0.0:
                            self.grid[target_prey.y][target_prey.x] = 0
                            if target_prey in self.prey_list:
                                self.prey_list.remove(target_prey)
                            pred.tracking_efficiency = min(100.0, pred.tracking_efficiency * 1.1)
                            pred.energy = min(150.0, pred.energy + self.params.get("ENERGY_FROM_PREDATOR_CATCH", 10.0))
                            pred.catches += 1
                            self.death_causes["Predation"] += 1
                        else:
                            target_prey.chromosome[710] = min(100.0, target_prey.base_efficiency * 1.25)
                            target_prey.chromosome[711] = min(100.0, target_prey.base_intelligence * 1.25)
                            
                            pred.tracking_efficiency = max(10.0, pred.tracking_efficiency * 0.9)
                            pred.apply_failed_chase_penalty(self.params)
                            
                            escape_pos = self.find_nearest_empty_cell(target_prey.x, target_prey.y)
                            if escape_pos:
                                self.grid[target_prey.y][target_prey.x] = 0
                                target_prey.x, target_prey.y = escape_pos
                                self.grid[escape_pos[1]][escape_pos[0]] = 3
                                
                    self.grid[pred.y][pred.x] = 0
                    pred.x = nx
                    pred.y = ny
                    self.grid[ny][nx] = 1
                elif target_val == 0 or target_val == 2:
                    self.grid[pred.y][pred.x] = 0
                    pred.x = nx
                    pred.y = ny
                    self.grid[ny][nx] = 1
                    if target_val == 2:
                        food_obj = None
                        for f in self.food_list:
                            if f.x == nx and f.y == ny:
                                food_obj = f
                                break
                        if food_obj:
                            self.food_list.remove(food_obj)
                            self.unstepped_ticks[ny][nx] = 0

            pred.age += 1

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
        for p in self.prey_list:
            fit = p.get_fitness()
            if (self.best_prey_ever is None or 
                fit > self.best_prey_ever["fitness"] or 
                p.id == self.best_prey_ever["id"]):
                self.best_prey_ever = {
                    "id": p.id,
                    "name": p.name,
                    "age": p.age,
                    "energy": p.energy,
                    "food_eaten": p.total_food_eaten,
                    "offspring": p.successful_offspring,
                    "fitness": fit,
                    "intelligence": p.get_intelligence(),
                    "efficiency": p.get_efficiency()
                }
        
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
