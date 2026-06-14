import pygame
from typing import Dict, Any, List, Tuple
from code.world import World

class SimulationGraphics:
    def __init__(self, cols: int, rows: int, params: Dict[str, Any]):
        pygame.init()
        pygame.display.set_caption("Artificial Life Simulation Dashboard")
        self.cell_size = 30
        self.grid_width_pixels = cols * self.cell_size
        self.grid_height_pixels = rows * self.cell_size
        self.screen_width = self.grid_width_pixels + 500
        self.screen_height = max(self.grid_height_pixels, 1020)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        
        self.font_title = pygame.font.SysFont("Outfit", 24, bold=True)
        self.font_header = pygame.font.SysFont("Outfit", 18, bold=True)
        self.font_body = pygame.font.SysFont("Courier New", 14)
        self.font_bold = pygame.font.SysFont("Courier New", 14, bold=True)
        self.max_history_len = 200

    def render(self, tick: int, world: World, params: Dict[str, Any], fps: float, 
               history_prey: List[int], history_predator: List[int], history_food: List[int], 
               extinct: bool):
        self.screen.fill((18, 18, 18))
        self._draw_grid(world)
        self._draw_sidebar(tick, world, params, fps, history_prey, history_predator, history_food)
        if extinct:
            self._draw_extinction_banner()
        pygame.display.flip()

    def _draw_grid(self, world: World):
        self._draw_grid_boundaries(world)
        self._draw_world_agents(world)
        pygame.draw.line(self.screen, (44, 44, 46), (self.grid_width_pixels, 0), (self.grid_width_pixels, self.screen_height), 2)

    def _draw_grid_boundaries(self, world: World):
        for y in range(world.rows):
            for x in range(world.cols):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)

    def _draw_world_agents(self, world: World):
        for y in range(world.rows):
            for x in range(world.cols):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                val = world.grid[y][x]
                if val == 1:
                    self._draw_predator_agent(rect)
                elif val == 2:
                    self._draw_food_agent(rect, x, y, world)
                elif val == 3:
                    self._draw_prey_agent(rect, x, y, world)

    def _draw_predator_agent(self, rect: pygame.Rect):
        pygame.draw.ellipse(self.screen, (255, 59, 48), rect.inflate(-4, -4))

    def _draw_food_agent(self, rect: pygame.Rect, x: int, y: int, world: World):
        food_instance = next((f for f in world.food_list if f.x == x and f.y == y), None)
        green_val = min(255, 100 + (food_instance.ticks_unstepped * 10) if food_instance else 100)
        pygame.draw.rect(self.screen, (52, green_val, 89), rect.inflate(-6, -6))

    def _draw_prey_agent(self, rect: pygame.Rect, x: int, y: int, world: World):
        prey_instance = next((p for p in world.prey_list if p.x == x and p.y == y), None)
        pygame.draw.ellipse(self.screen, (10, 132, 255), rect.inflate(-4, -4))
        if prey_instance:
            cx = x * self.cell_size + self.cell_size // 2
            cy = y * self.cell_size + self.cell_size // 2
            if prey_instance.orientation == 0:
                end_pos = (cx, cy - self.cell_size // 3)
            elif prey_instance.orientation == 1:
                end_pos = (cx + self.cell_size // 3, cy)
            elif prey_instance.orientation == 2:
                end_pos = (cx, cy + self.cell_size // 3)
            else:
                end_pos = (cx - self.cell_size // 3, cy)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, cy), end_pos, 2)

    def _draw_sidebar(self, tick: int, world: World, params: Dict[str, Any], fps: float,
                      history_prey: List[int], history_predator: List[int], history_food: List[int]):
        rx_offset = self.grid_width_pixels + 20
        ry_offset = 20
        
        title_surf = self.font_title.render("ALIFE SIMULATION DASHBOARD", True, (255, 255, 255))
        self.screen.blit(title_surf, (rx_offset, ry_offset))
        ry_offset += 40
        
        ry_offset = self._draw_stats_monitor(ry_offset, rx_offset, tick, world, params, fps)
        ry_offset = self._draw_fitness_breakdown(ry_offset, rx_offset, world)
        ry_offset = self._draw_moving_averages(ry_offset, rx_offset, world)
        ry_offset = self._draw_historical_trends(ry_offset, rx_offset, history_prey, history_predator, history_food)
        ry_offset = self._draw_hall_of_fame(ry_offset, rx_offset, world, params)
        self._draw_mortality_stats(ry_offset, rx_offset, world)

    def _draw_stats_monitor(self, ry: int, rx: int, tick: int, world: World, params: Dict[str, Any], fps: float) -> int:
        pygame.draw.line(self.screen, (44, 44, 46), (rx, ry), (self.screen_width - 20, ry), 1)
        ry += 10
        self.screen.blit(self.font_header.render("[STATS MONITOR]", True, (142, 142, 147)), (rx, ry))
        ry += 25
        
        headcounts_str = f"Tick: {tick:<8} FPS Limit: {fps:.1f}"
        self.screen.blit(self.font_body.render(headcounts_str, True, (255, 255, 255)), (rx, ry))
        ry += 20
        
        pop_str = f"{params['PREY_NAME']}s: {len(world.prey_list):<6} {params['PREDATOR_NAME']}s: {len(world.predator_list):<6} Food: {len(world.food_list)}"
        self.screen.blit(self.font_body.render(pop_str, True, (255, 255, 255)), (rx, ry))
        return ry + 30

    def _draw_fitness_breakdown(self, ry: int, rx: int, world: World) -> int:
        pygame.draw.line(self.screen, (44, 44, 46), (rx, ry), (self.screen_width - 20, ry), 1)
        ry += 10
        self.screen.blit(self.font_header.render("[FITNESS BREAKDOWN (AGE)]", True, (142, 142, 147)), (rx, ry))
        ry += 25
        
        if world.prey_list:
            ages = sorted([p.age for p in world.prey_list])
            worst_age = ages[0]
            median_age = ages[len(ages) // 2]
            elite_age = ages[-1]
        else:
            worst_age = median_age = elite_age = 0
            
        self.screen.blit(self.font_body.render(f"Elite Score (Max Age): {elite_age} Ticks", True, (10, 132, 255)), (rx, ry))
        ry += 20
        self.screen.blit(self.font_body.render(f"Median Score: {median_age} Ticks", True, (255, 255, 255)), (rx, ry))
        ry += 20
        self.screen.blit(self.font_body.render(f"Worst Score: {worst_age} Ticks", True, (255, 59, 48)), (rx, ry))
        return ry + 30

    def _draw_moving_averages(self, ry: int, rx: int, world: World) -> int:
        pygame.draw.line(self.screen, (44, 44, 46), (rx, ry), (self.screen_width - 20, ry), 1)
        ry += 10
        self.screen.blit(self.font_header.render("[GLOBAL TRAITS MOVING AVERAGE]", True, (142, 142, 147)), (rx, ry))
        ry += 25
        
        if world.prey_list:
            avg_energy = sum(p.energy for p in world.prey_list) / len(world.prey_list)
            avg_intel = sum(p.get_intelligence() for p in world.prey_list) / len(world.prey_list)
            avg_eff = sum(p.get_efficiency() for p in world.prey_list) / len(world.prey_list)
        else:
            avg_energy = avg_intel = avg_eff = 0
            
        self.screen.blit(self.font_body.render(f"Avg Energy: {avg_energy:.1f}", True, (255, 255, 255)), (rx, ry))
        ry += 20
        self.screen.blit(self.font_body.render(f"Avg Intelligence: {avg_intel:.1f} / 100", True, (255, 255, 255)), (rx, ry))
        ry += 20
        self.screen.blit(self.font_body.render(f"Avg Efficiency: {avg_eff:.1f} / 100", True, (255, 255, 255)), (rx, ry))
        return ry + 35

    def _draw_historical_trends(self, ry: int, rx: int, history_prey: List[int], history_predator: List[int], history_food: List[int]) -> int:
        pygame.draw.line(self.screen, (44, 44, 46), (rx, ry), (self.screen_width - 20, ry), 1)
        ry += 10
        self.screen.blit(self.font_header.render("[POPULATION HISTORICAL TRENDS]", True, (142, 142, 147)), (rx, ry))
        ry += 25
        
        graph_width = 400
        graph_height = 120
        graph_x = rx
        graph_y = ry
        
        pygame.draw.rect(self.screen, (28, 28, 30), (graph_x, graph_y, graph_width, graph_height))
        pygame.draw.rect(self.screen, (44, 44, 46), (graph_x, graph_y, graph_width, graph_height), 1)
        
        if len(history_prey) > 1:
            max_val = max(max(history_prey), max(history_predator), max(history_food), 10)
            
            points_prey = self._get_trend_points(history_prey, max_val, graph_x, graph_y, graph_width, graph_height)
            points_pred = self._get_trend_points(history_predator, max_val, graph_x, graph_y, graph_width, graph_height)
            points_food = self._get_trend_points(history_food, max_val, graph_x, graph_y, graph_width, graph_height)
            
            pygame.draw.lines(self.screen, (10, 132, 255), False, points_prey, 2)
            pygame.draw.lines(self.screen, (255, 59, 48), False, points_pred, 2)
            pygame.draw.lines(self.screen, (52, 199, 89), False, points_food, 2)
            
        return ry + graph_height + 25

    def _get_trend_points(self, history: List[int], max_val: int, graph_x: int, graph_y: int, graph_width: int, graph_height: int) -> List[Tuple[int, int]]:
        points = []
        for i, val in enumerate(history):
            x_p = graph_x + (i / (self.max_history_len - 1)) * graph_width
            y_p = graph_y + graph_height - (val / max_val) * graph_height
            points.append((int(x_p), int(y_p)))
        return points

    def _draw_hall_of_fame(self, ry: int, rx: int, world: World, params: Dict[str, Any]) -> int:
        pygame.draw.line(self.screen, (44, 44, 46), (rx, ry), (self.screen_width - 20, ry), 1)
        ry += 10
        self.screen.blit(self.font_header.render("[HALL OF FAME & REPRODUCTION]", True, (255, 214, 10)), (rx, ry))
        ry += 25
        
        ry = self._draw_best_prey_fame(ry, rx, world, params)
        ry = self._draw_best_predator_fame(ry, rx, world, params)
        ry = self._draw_best_mating_fame(ry, rx, world)
        return ry

    def _draw_best_prey_fame(self, ry: int, rx: int, world: World, params: Dict[str, Any]) -> int:
        prey_title = f"Best {params['PREY_NAME']} Ever:"
        self.screen.blit(self.font_bold.render(prey_title, True, (10, 132, 255)), (rx, ry))
        ry += 18
        if world.best_prey_ever:
            bp = world.best_prey_ever
            bp_str = f"ID: {bp['id']:<4} Age: {bp['age']:<3} Food: {bp['food_eaten']:<3} Kids: {bp['offspring']:<3} Fit: {bp['fitness']:.1f}"
            self.screen.blit(self.font_body.render(bp_str, True, (255, 255, 255)), (rx, ry))
            ry += 15
            bp_traits = f"      Intel: {bp['intelligence']:.1f}/100  Eff: {bp['efficiency']:.1f}/100"
            self.screen.blit(self.font_body.render(bp_traits, True, (255, 255, 255)), (rx, ry))
        else:
            self.screen.blit(self.font_body.render("  No records yet.", True, (142, 142, 147)), (rx, ry))
        return ry + 25

    def _draw_best_predator_fame(self, ry: int, rx: int, world: World, params: Dict[str, Any]) -> int:
        pred_title = f"Best {params['PREDATOR_NAME']} Ever:"
        self.screen.blit(self.font_bold.render(pred_title, True, (255, 59, 48)), (rx, ry))
        ry += 18
        if world.best_predator_ever:
            bpr = world.best_predator_ever
            bpr_str = f"ID: {bpr['id']:<4} Age: {bpr['age']:<3} Catches: {bpr['catches']:<3} Eff: {bpr['tracking_efficiency']:.1f}%"
            self.screen.blit(self.font_body.render(bpr_str, True, (255, 255, 255)), (rx, ry))
        else:
            self.screen.blit(self.font_body.render("  No records yet.", True, (142, 142, 147)), (rx, ry))
        return ry + 25

    def _draw_best_mating_fame(self, ry: int, rx: int, world: World) -> int:
        mating_title = "Best Mating Pair & Offspring:"
        self.screen.blit(self.font_bold.render(mating_title, True, (191, 90, 242)), (rx, ry))
        ry += 18
        if world.best_mating_pair_ever:
            bm = world.best_mating_pair_ever
            p1_str = f"  Parent 1: ID {bm['parent1']['id']:<3} (Age: {bm['parent1']['age']:<3} Fit: {bm['parent1']['fitness']:.1f})"
            p2_str = f"  Parent 2: ID {bm['parent2']['id']:<3} (Age: {bm['parent2']['age']:<3} Fit: {bm['parent2']['fitness']:.1f})"
            ch_str = f"  Produced: ID {bm['child']['id']:<3} (Intel: {bm['child']['intelligence']:.1f} Eff: {bm['child']['efficiency']:.1f})"
            self.screen.blit(self.font_body.render(p1_str, True, (255, 255, 255)), (rx, ry))
            ry += 15
            self.screen.blit(self.font_body.render(p2_str, True, (255, 255, 255)), (rx, ry))
            ry += 15
            self.screen.blit(self.font_body.render(ch_str, True, (255, 255, 255)), (rx, ry))
        else:
            self.screen.blit(self.font_body.render("  No mating events yet.", True, (142, 142, 147)), (rx, ry))
        return ry + 25

    def _draw_mortality_stats(self, ry: int, rx: int, world: World):
        pygame.draw.line(self.screen, (44, 44, 46), (rx, ry), (self.screen_width - 20, ry), 1)
        ry += 10
        self.screen.blit(self.font_header.render("[MORTALITY STATISTICS]", True, (255, 105, 97)), (rx, ry))
        ry += 25
        
        total_deaths = sum(world.death_causes.values())
        if total_deaths > 0:
            starv_pct = (world.death_causes["Starvation"] / total_deaths) * 100.0
            oldage_pct = (world.death_causes["Old Age"] / total_deaths) * 100.0
            pred_pct = (world.death_causes["Predation"] / total_deaths) * 100.0
        else:
            starv_pct = oldage_pct = pred_pct = 0.0
            
        self.screen.blit(self.font_body.render(f"Total Deaths: {total_deaths}", True, (255, 255, 255)), (rx, ry))
        ry += 20
        self.screen.blit(self.font_body.render(f"Starvation:  {world.death_causes['Starvation']:<5} ({starv_pct:.1f}%)", True, (255, 255, 255)), (rx, ry))
        ry += 18
        self.screen.blit(self.font_body.render(f"Old Age:     {world.death_causes['Old Age']:<5} ({oldage_pct:.1f}%)", True, (255, 255, 255)), (rx, ry))
        ry += 18
        self.screen.blit(self.font_body.render(f"Predation:   {world.death_causes['Predation']:<5} ({pred_pct:.1f}%)", True, (255, 255, 255)), (rx, ry))

    def _draw_extinction_banner(self):
        banner_rect = pygame.Rect(self.grid_width_pixels // 2 - 175, self.grid_height_pixels // 2 - 40, 350, 80)
        pygame.draw.rect(self.screen, (30, 30, 30), banner_rect)
        pygame.draw.rect(self.screen, (255, 59, 48), banner_rect, 2)
        
        extinct_text1 = self.font_header.render("ZIZOID EXTINCTION HIT", True, (255, 59, 48))
        extinct_text2 = self.font_body.render("Press ESC to Close Window", True, (255, 255, 255))
        
        self.screen.blit(extinct_text1, (self.grid_width_pixels // 2 - extinct_text1.get_width() // 2, self.grid_height_pixels // 2 - 25))
        self.screen.blit(extinct_text2, (self.grid_width_pixels // 2 - extinct_text2.get_width() // 2, self.grid_height_pixels // 2 + 5))

    def close(self):
        pygame.quit()
