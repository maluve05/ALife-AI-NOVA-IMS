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
        
        for y in range(world.rows):
            for x in range(world.cols):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)
                
                val = world.grid[y][x]
                if val == 1:
                    pygame.draw.ellipse(self.screen, (255, 59, 48), rect.inflate(-4, -4))
                elif val == 2:
                    food_instance = next((f for f in world.food_list if f.x == x and f.y == y), None)
                    green_val = min(255, 100 + (food_instance.ticks_unstepped * 10) if food_instance else 100)
                    pygame.draw.rect(self.screen, (52, green_val, 89), rect.inflate(-6, -6))
                elif val == 3:
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
                        
        pygame.draw.line(self.screen, (44, 44, 46), (self.grid_width_pixels, 0), (self.grid_width_pixels, self.screen_height), 2)
        
        rx_offset = self.grid_width_pixels + 20
        ry_offset = 20
        
        title_surf = self.font_title.render("ALIFE SIMULATION DASHBOARD", True, (255, 255, 255))
        self.screen.blit(title_surf, (rx_offset, ry_offset))
        ry_offset += 40
        
        pygame.draw.line(self.screen, (44, 44, 46), (rx_offset, ry_offset), (self.screen_width - 20, ry_offset), 1)
        ry_offset += 10
        self.screen.blit(self.font_header.render("[STATS MONITOR]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        headcounts_str = f"Tick: {tick:<8} FPS Limit: {fps:.1f}"
        self.screen.blit(self.font_body.render(headcounts_str, True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        
        pop_str = f"{params['PREY_NAME']}s: {len(world.prey_list):<6} {params['PREDATOR_NAME']}s: {len(world.predator_list):<6} Food: {len(world.food_list)}"
        self.screen.blit(self.font_body.render(pop_str, True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 30
        
        pygame.draw.line(self.screen, (44, 44, 46), (rx_offset, ry_offset), (self.screen_width - 20, ry_offset), 1)
        ry_offset += 10
        self.screen.blit(self.font_header.render("[FITNESS BREAKDOWN (AGE)]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        if world.prey_list:
            ages = sorted([p.age for p in world.prey_list])
            worst_age = ages[0]
            median_age = ages[len(ages) // 2]
            elite_age = ages[-1]
            avg_energy = sum(p.energy for p in world.prey_list) / len(world.prey_list)
            avg_intel = sum(p.get_intelligence() for p in world.prey_list) / len(world.prey_list)
            avg_eff = sum(p.get_efficiency() for p in world.prey_list) / len(world.prey_list)
        else:
            worst_age = median_age = elite_age = 0
            avg_energy = avg_intel = avg_eff = 0
            
        self.screen.blit(self.font_body.render(f"Elite Score (Max Age): {elite_age} Ticks", True, (10, 132, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        self.screen.blit(self.font_body.render(f"Median Score: {median_age} Ticks", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        self.screen.blit(self.font_body.render(f"Worst Score: {worst_age} Ticks", True, (255, 59, 48)), (rx_offset, ry_offset))
        ry_offset += 30
        
        pygame.draw.line(self.screen, (44, 44, 46), (rx_offset, ry_offset), (self.screen_width - 20, ry_offset), 1)
        ry_offset += 10
        self.screen.blit(self.font_header.render("[GLOBAL TRAITS MOVING AVERAGE]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        self.screen.blit(self.font_body.render(f"Avg Energy: {avg_energy:.1f}", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        self.screen.blit(self.font_body.render(f"Avg Intelligence: {avg_intel:.1f} / 100", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        self.screen.blit(self.font_body.render(f"Avg Efficiency: {avg_eff:.1f} / 100", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 35
        
        pygame.draw.line(self.screen, (44, 44, 46), (rx_offset, ry_offset), (self.screen_width - 20, ry_offset), 1)
        ry_offset += 10
        self.screen.blit(self.font_header.render("[POPULATION HISTORICAL TRENDS]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        graph_width = 400
        graph_height = 120
        graph_x = rx_offset
        graph_y = ry_offset
        
        pygame.draw.rect(self.screen, (28, 28, 30), (graph_x, graph_y, graph_width, graph_height))
        pygame.draw.rect(self.screen, (44, 44, 46), (graph_x, graph_y, graph_width, graph_height), 1)
        
        if len(history_prey) > 1:
            max_val = max(max(history_prey), max(history_predator), max(history_food), 10)
            
            def get_point(i: int, val: int) -> Tuple[int, int]:
                x_p = graph_x + (i / (self.max_history_len - 1)) * graph_width
                y_p = graph_y + graph_height - (val / max_val) * graph_height
                return int(x_p), int(y_p)
                
            points_prey = [get_point(i, v) for i, v in enumerate(history_prey)]
            points_pred = [get_point(i, v) for i, v in enumerate(history_predator)]
            points_food = [get_point(i, v) for i, v in enumerate(history_food)]
            
            pygame.draw.lines(self.screen, (10, 132, 255), False, points_prey, 2)
            pygame.draw.lines(self.screen, (255, 59, 48), False, points_pred, 2)
            pygame.draw.lines(self.screen, (52, 199, 89), False, points_food, 2)

        ry_offset += graph_height + 25
        
        pygame.draw.line(self.screen, (44, 44, 46), (rx_offset, ry_offset), (self.screen_width - 20, ry_offset), 1)
        ry_offset += 10
        self.screen.blit(self.font_header.render("[HALL OF FAME & REPRODUCTION]", True, (255, 214, 10)), (rx_offset, ry_offset))
        ry_offset += 25
        
        prey_title = f"Best {params['PREY_NAME']} Ever:"
        self.screen.blit(self.font_bold.render(prey_title, True, (10, 132, 255)), (rx_offset, ry_offset))
        ry_offset += 18
        if world.best_prey_ever:
            bp = world.best_prey_ever
            bp_str = f"ID: {bp['id']:<4} Age: {bp['age']:<3} Food: {bp['food_eaten']:<3} Kids: {bp['offspring']:<3} Fit: {bp['fitness']:.1f}"
            self.screen.blit(self.font_body.render(bp_str, True, (255, 255, 255)), (rx_offset, ry_offset))
            ry_offset += 15
            bp_traits = f"      Intel: {bp['intelligence']:.1f}/100  Eff: {bp['efficiency']:.1f}/100"
            self.screen.blit(self.font_body.render(bp_traits, True, (255, 255, 255)), (rx_offset, ry_offset))
        else:
            self.screen.blit(self.font_body.render("  No records yet.", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        pred_title = f"Best {params['PREDATOR_NAME']} Ever:"
        self.screen.blit(self.font_bold.render(pred_title, True, (255, 59, 48)), (rx_offset, ry_offset))
        ry_offset += 18
        if world.best_predator_ever:
            bpr = world.best_predator_ever
            bpr_str = f"ID: {bpr['id']:<4} Age: {bpr['age']:<3} Catches: {bpr['catches']:<3} Eff: {bpr['tracking_efficiency']:.1f}%"
            self.screen.blit(self.font_body.render(bpr_str, True, (255, 255, 255)), (rx_offset, ry_offset))
        else:
            self.screen.blit(self.font_body.render("  No records yet.", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        mating_title = "Best Mating Pair & Offspring:"
        self.screen.blit(self.font_bold.render(mating_title, True, (191, 90, 242)), (rx_offset, ry_offset))
        ry_offset += 18
        if world.best_mating_pair_ever:
            bm = world.best_mating_pair_ever
            p1_str = f"  Parent 1: ID {bm['parent1']['id']:<3} (Age: {bm['parent1']['age']:<3} Fit: {bm['parent1']['fitness']:.1f})"
            p2_str = f"  Parent 2: ID {bm['parent2']['id']:<3} (Age: {bm['parent2']['age']:<3} Fit: {bm['parent2']['fitness']:.1f})"
            ch_str = f"  Produced: ID {bm['child']['id']:<3} (Intel: {bm['child']['intelligence']:.1f} Eff: {bm['child']['efficiency']:.1f})"
            self.screen.blit(self.font_body.render(p1_str, True, (255, 255, 255)), (rx_offset, ry_offset))
            ry_offset += 15
            self.screen.blit(self.font_body.render(p2_str, True, (255, 255, 255)), (rx_offset, ry_offset))
            ry_offset += 15
            self.screen.blit(self.font_body.render(ch_str, True, (255, 255, 255)), (rx_offset, ry_offset))
        else:
            self.screen.blit(self.font_body.render("  No mating events yet.", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        pygame.draw.line(self.screen, (44, 44, 46), (rx_offset, ry_offset), (self.screen_width - 20, ry_offset), 1)
        ry_offset += 10
        self.screen.blit(self.font_header.render("[MORTALITY STATISTICS]", True, (255, 105, 97)), (rx_offset, ry_offset))
        ry_offset += 25
        
        total_deaths = sum(world.death_causes.values())
        if total_deaths > 0:
            starv_pct = (world.death_causes["Starvation"] / total_deaths) * 100.0
            oldage_pct = (world.death_causes["Old Age"] / total_deaths) * 100.0
            pred_pct = (world.death_causes["Predation"] / total_deaths) * 100.0
        else:
            starv_pct = oldage_pct = pred_pct = 0.0
            
        self.screen.blit(self.font_body.render(f"Total Deaths: {total_deaths}", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        self.screen.blit(self.font_body.render(f"Starvation:  {world.death_causes['Starvation']:<5} ({starv_pct:.1f}%)", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 18
        self.screen.blit(self.font_body.render(f"Old Age:     {world.death_causes['Old Age']:<5} ({oldage_pct:.1f}%)", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 18
        self.screen.blit(self.font_body.render(f"Predation:   {world.death_causes['Predation']:<5} ({pred_pct:.1f}%)", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 25
        
        if extinct:
            banner_rect = pygame.Rect(self.grid_width_pixels // 2 - 175, self.grid_height_pixels // 2 - 40, 350, 80)
            pygame.draw.rect(self.screen, (30, 30, 30), banner_rect)
            pygame.draw.rect(self.screen, (255, 59, 48), banner_rect, 2)
            
            extinct_text1 = self.font_header.render("ZIZOID EXTINCTION HIT", True, (255, 59, 48))
            extinct_text2 = self.font_body.render("Press ESC to Close Window", True, (255, 255, 255))
            
            self.screen.blit(extinct_text1, (self.grid_width_pixels // 2 - extinct_text1.get_width() // 2, self.grid_height_pixels // 2 - 25))
            self.screen.blit(extinct_text2, (self.grid_width_pixels // 2 - extinct_text2.get_width() // 2, self.grid_height_pixels // 2 + 5))

    def close(self):
        pygame.quit()
