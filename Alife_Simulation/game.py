"""
game.py

The Director.
Entry point of the application. Manages high-level execution loops, Pygame initialization,
user interaction, logging, serialization/loading, and the graphics dashboard.
"""
import os
import sys
import json
import csv
import pygame
import random
from typing import Dict, Any, List

# Add the parent directory to sys.path at index 0 to override built-in code module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code.world import World
from code.prey import Prey
from code.predator import Predator
from code.food import Food

# Global default parameter configurations
DEFAULT_PARAMETERS: Dict[str, Any] = {
    "INITIAL_ENERGY_PREY": 100,
    "MUTATION_RATE": 0.05,
    "P_REPRODUCTION": 0.50,
    "INITIAL_PREY_COUNT": 75,
    "INITIAL_PREDATOR_COUNT": 25,
    "MAX_PREY_POPULATION": 300,
    "ENERGY_FROM_CONSUMING_FOOD": 40,
    "ENERGY_FROM_PREDATOR_CATCH": 10,
    "ENERGY_REPRODUCTION_COST": 3,
    "GENERATIONAL_DECAY": 1,
    "FRAME_RATE_LIMIT": 1.0,
    "LOGGING_INTERVAL": 15,
    "GRID_WIDTH": 15,
    "GRID_HEIGHT": 20,
    "PREY_NAME": "Zizoid",
    "PREDATOR_NAME": "Wsiloid"
}

def boot_menu() -> Tuple[World, Dict[str, Any], int]:
    """
    Runs the blocking CLI configuration handshake in the console before starting Pygame.
    Returns (World instance, parameters dict, current_tick_offset)
    """
    print("============================================================")
    print("       ARTIFICIAL LIFE ENVIRONMENT SIMULATION ENGINE")
    print("============================================================")
    print("[1] Load Previous Simulation State (.json)")
    print("[2] Run Default Simulation Configuration")
    print("[3] Modify Parameters & Create New Simulation")
    print("============================================================")
    
    while True:
        try:
            choice = input("Select boot option (1-3): ").strip()
            if choice == "1":
                # Option 1: Load state
                file_path = input("Enter JSON state file path (e.g. simulation_state.json): ").strip()
                if not os.path.exists(file_path):
                    print(f"Error: File '{file_path}' not found. Try again.")
                    continue
                with open(file_path, 'r') as f:
                    state_data = json.load(f)
                
                params = state_data.get("parameters", DEFAULT_PARAMETERS.copy())
                cols = params.get("GRID_WIDTH", 15)
                rows = params.get("GRID_HEIGHT", 20)
                
                # Reconstruct world
                world = World(cols, rows, params)
                world.prey_list.clear()
                world.predator_list.clear()
                world.food_list.clear()
                
                # Re-load Prey
                world.next_prey_id = state_data.get("next_prey_id", 1)
                for p_data in state_data.get("prey", []):
                    p = Prey(p_data["id"], p_data["name"], p_data["x"], p_data["y"], p_data["chromosome"])
                    p.energy = p_data["energy"]
                    p.age = p_data["age"]
                    p.gestation_timer = p_data.get("gestation_timer", 0)
                    p.is_pregnant = p_data.get("is_pregnant", False)
                    p.last_jumped = p_data.get("last_jumped", False)
                    p.total_food_eaten = p_data.get("total_food_eaten", 0)
                    p.successful_offspring = p_data.get("successful_offspring", 0)
                    world.prey_list.append(p)
                    
                # Re-load Predators
                world.next_predator_id = state_data.get("next_predator_id", 1)
                for pred_data in state_data.get("predators", []):
                    pred = Predator(pred_data["id"], pred_data["name"], pred_data["x"], pred_data["y"])
                    pred.energy = pred_data["energy"]
                    pred.age = pred_data["age"]
                    pred.tracking_efficiency = pred_data.get("tracking_efficiency", 50.0)
                    pred.last_jumped = pred_data.get("last_jumped", False)
                    pred.chase_state = pred_data.get("chase_state", False)
                    world.predator_list.append(pred)
                    
                # Re-load Food
                for f_data in state_data.get("food", []):
                    f_obj = Food(f_data["x"], f_data["y"], params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                    f_obj.ticks_unstepped = f_data.get("ticks_unstepped", 3)
                    world.food_list.append(f_obj)
                    
                world.sync_grid()
                tick_offset = state_data.get("current_tick", 0)
                print(f"Simulation successfully loaded from '{file_path}' (resuming at tick {tick_offset}).")
                return world, params, tick_offset
                
            elif choice == "2":
                # Option 2: Default configuration
                print("Starting default simulation (15x20 grid, 75 Zizoids, 25 Wsiloids)...")
                params = DEFAULT_PARAMETERS.copy()
                world = World(15, 20, params)
                return world, params, 0
                
            elif choice == "3":
                # Option 3: Modify Parameters
                params = DEFAULT_PARAMETERS.copy()
                print("\n--- Custom Parameter Handshake ---")
                
                # Grid sizing validation gate
                while True:
                    try:
                        width = int(input("Enter Grid Width (default 15): ") or "15")
                        height = int(input("Enter Grid Height (default 20): ") or "20")
                        total_cells = width * height
                        if total_cells < 300:
                            print(f"Error: Grid yields {total_cells} cells. Minimum 300 cells is required. Re-enter.")
                            continue
                        params["GRID_WIDTH"] = width
                        params["GRID_HEIGHT"] = height
                        break
                    except ValueError:
                        print("Invalid input. Please enter integers.")
                
                # Custom entity naming
                params["PREY_NAME"] = input("Enter name for Prey (default: Zizoid): ").strip() or "Zizoid"
                params["PREDATOR_NAME"] = input("Enter name for Predator (default: Wsiloid): ").strip() or "Wsiloid"
                
                # Attribute tweaks
                try:
                    params["INITIAL_ENERGY_PREY"] = float(input("Enter starting Prey energy (default 100): ") or "100")
                    params["ENERGY_FROM_CONSUMING_FOOD"] = float(input("Enter Food energy value (default 40): ") or "40")
                    params["MUTATION_RATE"] = float(input("Enter Mutation Rate (0.0 to 1.0, default 0.05): ") or "0.05")
                    params["FRAME_RATE_LIMIT"] = float(input("Enter initial speed in FPS (default 1.0): ") or "1.0")
                except ValueError:
                    print("Invalid value entered. Reverting parameters to baseline defaults.")
                
                # Custom ratio input
                ratio_str = input("Enter starting Predator-to-Prey ratio (default 1:3): ").strip() or "1:3"
                try:
                    parts = ratio_str.split(':')
                    ratio_pred = int(parts[0])
                    ratio_prey = int(parts[1])
                    if ratio_pred <= 0 or ratio_prey <= 0:
                        raise ValueError()
                except (ValueError, IndexError):
                    print("Invalid ratio format. Reverting to default 1:3.")
                    ratio_pred, ratio_prey = 1, 3
                
                # Capacity limits
                total_cells = params["GRID_WIDTH"] * params["GRID_HEIGHT"]
                max_agents = total_cells // 3
                
                # Compute count using ratio
                total_ratio_units = ratio_pred + ratio_prey
                unit_count = max_agents // total_ratio_units
                pred_count = unit_count * ratio_pred
                prey_count = unit_count * ratio_prey
                
                # Fallback if unit count is zero
                if pred_count == 0 or prey_count == 0:
                    print("Ratio scale too large for grid capacity. Reverting to default 1:3 counts.")
                    pred_count = max_agents // 4
                    prey_count = pred_count * 3
                    ratio_pred, ratio_prey = 1, 3
                
                params["INITIAL_PREY_COUNT"] = prey_count
                params["INITIAL_PREDATOR_COUNT"] = pred_count
                
                print(f"Calculated starting population (ratio {ratio_pred}:{ratio_prey}): {prey_count} {params['PREY_NAME']}s, {pred_count} {params['PREDATOR_NAME']}s.")
                
                world = World(params["GRID_WIDTH"], params["GRID_HEIGHT"], params)
                return world, params, 0
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
        except Exception as e:
            print(f"Error handling menu setup: {e}. Try again.")

def save_state_to_json(world: World, params: Dict[str, Any], tick: int, file_path: str = "simulation_state.json"):
    """Serializes the complete simulation state to JSON to enable exact resume loading."""
    state = {
        "current_tick": tick,
        "next_prey_id": world.next_prey_id,
        "next_predator_id": world.next_predator_id,
        "parameters": params,
        "prey": [
            {
                "id": p.id,
                "name": p.name,
                "x": p.x,
                "y": p.y,
                "energy": p.energy,
                "age": p.age,
                "gestation_timer": p.gestation_timer,
                "is_pregnant": p.is_pregnant,
                "last_jumped": p.last_jumped,
                "total_food_eaten": p.total_food_eaten,
                "successful_offspring": p.successful_offspring,
                "chromosome": p.chromosome
            } for p in world.prey_list
        ],
        "predators": [
            {
                "id": pred.id,
                "name": pred.name,
                "x": pred.x,
                "y": pred.y,
                "energy": pred.energy,
                "age": pred.age,
                "tracking_efficiency": pred.tracking_efficiency,
                "last_jumped": pred.last_jumped,
                "chase_state": pred.chase_state
            } for pred in world.predator_list
        ],
        "food": [
            {
                "x": f.x,
                "y": f.y,
                "ticks_unstepped": f.ticks_unstepped
            } for f in world.food_list
        ]
    }
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)

def log_to_csv(tick: int, world: World, params: Dict[str, Any], file_path: str = "simulation_1.csv"):
    """
    Appends simulation state logs, population records, and elite Zizoid chromosomes to simulation_1.csv.
    """
    file_exists = os.path.exists(file_path)
    
    # Calculate averages
    avg_energy = sum(p.energy for p in world.prey_list) / max(1, len(world.prey_list))
    avg_intel = sum(p.get_intelligence() for p in world.prey_list) / max(1, len(world.prey_list))
    avg_eff = sum(p.get_efficiency() for p in world.prey_list) / max(1, len(world.prey_list))
    
    # Find elite chromosome
    elite_chromo = []
    if world.prey_list:
        elite = max(world.prey_list, key=lambda p: p.age)
        elite_chromo = elite.chromosome
        
    row = [
        tick,
        len(world.prey_list),
        len(world.predator_list),
        len(world.food_list),
        round(avg_energy, 2),
        round(avg_intel, 2),
        round(avg_eff, 2),
        json.dumps(elite_chromo)  # Serialize chromosome cleanly
    ]
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header
            writer.writerow([
                "Tick", "PreyCount", "PredatorCount", "FoodCount", 
                "AvgEnergy", "AvgIntelligence", "AvgEfficiency", "EliteChromosome"
            ])
        writer.writerow(row)

def main():
    # 1. Run Boot sequence configuration CLI
    world, params, tick = boot_menu()
    
    # 2. Pygame Screen initialization
    pygame.init()
    pygame.display.set_caption("Artificial Life Simulation Dashboard")
    
    # Screen details
    cell_size = 30
    grid_width_pixels = world.cols * cell_size
    grid_height_pixels = world.rows * cell_size
    
    # Total screen width is Left Panel (grid) + Right Panel (dashboard)
    screen_width = grid_width_pixels + 450
    screen_height = max(grid_height_pixels, 600)
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    
    # Setup fonts
    font_title = pygame.font.SysFont("Outfit", 24, bold=True)
    font_header = pygame.font.SysFont("Outfit", 18, bold=True)
    font_body = pygame.font.SysFont("Courier New", 14)
    font_bold = pygame.font.SysFont("Courier New", 14, bold=True)
    
    # Population history for graphing
    history_prey: List[int] = []
    history_predator: List[int] = []
    history_food: List[int] = []
    max_history_len = 200
    
    running = True
    fps = params.get("FRAME_RATE_LIMIT", 1.0)
    paused = False
    extinct = False
    
    print(f"\nSimulation graphics loaded successfully! Window resolution: {screen_width}x{screen_height} px.")
    print("Controls:")
    print("  [SPACE] - Pause/Play simulation execution.")
    print("  [UP Arrow] - Speed up simulation frame rate.")
    print("  [DOWN Arrow] - Slow down simulation frame rate.")
    print("  [S] - Save current simulation state immediately.")
    print("  [ESC] - Quit simulation.")
    
    # Main simulation loop
    while running:
        # Handle keyboard/mouse clock velocity scaling & commands
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    print("Simulation Paused." if paused else "Simulation Resumed.")
                elif event.key == pygame.K_UP:
                    fps = min(60.0, fps + 1.0)
                    print(f"Speed increased to {fps} FPS/TPS.")
                elif event.key == pygame.K_DOWN:
                    fps = max(0.2, fps - 0.2)
                    print(f"Speed decreased to {fps} FPS/TPS.")
                elif event.key == pygame.K_s:
                    save_state_to_json(world, params, tick)
                    print(f"Simulation state checkpoint saved at tick {tick}.")
                    
        # Check Extinction termination gate
        if len(world.prey_list) == 0 and not extinct:
            extinct = True
            print("\n============================================================")
            print("             ZIZOID EXTINCTION CONSTRAINTS HIT!")
            print("============================================================")
            print(f"Final Tick Duration: {tick} Epochs")
            print("Shutting down simulation environment updates.")
            print("============================================================")

        if not paused and not extinct:
                
            # Perform simulation stage tick
            world.update()
            tick += 1
            
            # Record historical parameters
            history_prey.append(len(world.prey_list))
            history_predator.append(len(world.predator_list))
            history_food.append(len(world.food_list))
            if len(history_prey) > max_history_len:
                history_prey.pop(0)
                history_predator.pop(0)
                history_food.pop(0)
                
            # Logging interval trigger
            if tick % params.get("LOGGING_INTERVAL", 15) == 0:
                log_to_csv(tick, world, params)
                save_state_to_json(world, params, tick)

        # -------------------------------------------------------------
        # DRAWING ROUTINES
        # -------------------------------------------------------------
        # 1. Clear Screen (Charcoal black background)
        screen.fill((18, 18, 18))
        
        # 2. Render Left Panel (Environment Grid)
        for y in range(world.rows):
            for x in range(world.cols):
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, (30, 30, 30), rect, 1)  # Grid border
                
                val = world.grid[y][x]
                if val == 1:  # Predator ( Crimson Red )
                    pygame.draw.ellipse(screen, (255, 59, 48), rect.inflate(-4, -4))
                elif val == 2:  # Food ( Forest Green compounding )
                    # Find food instance to get ticks_unstepped
                    food_instance = next((f for f in world.food_list if f.x == x and f.y == y), None)
                    green_val = min(255, 100 + (food_instance.ticks_unstepped * 10) if food_instance else 100)
                    pygame.draw.rect(screen, (52, green_val, 89), rect.inflate(-6, -6))
                elif val == 3:  # Prey ( Electric Blue with direction arrow )
                    prey_instance = next((p for p in world.prey_list if p.x == x and p.y == y), None)
                    pygame.draw.ellipse(screen, (10, 132, 255), rect.inflate(-4, -4))
                    if prey_instance:
                        # Draw orient arrow: line from center to edge
                        cx = x * cell_size + cell_size // 2
                        cy = y * cell_size + cell_size // 2
                        if prey_instance.orientation == 0:    # North
                            end_pos = (cx, cy - cell_size // 3)
                        elif prey_instance.orientation == 1:  # East
                            end_pos = (cx + cell_size // 3, cy)
                        elif prey_instance.orientation == 2:  # South
                            end_pos = (cx, cy + cell_size // 3)
                        else:                                  # West
                            end_pos = (cx - cell_size // 3, cy)
                        pygame.draw.line(screen, (255, 255, 255), (cx, cy), end_pos, 2)
                        
        # Draw Panel separator line
        pygame.draw.line(screen, (44, 44, 46), (grid_width_pixels, 0), (grid_width_pixels, screen_height), 2)
        
        # 3. Render Right Panel (Real-Time Simulation Dashboard)
        rx_offset = grid_width_pixels + 20
        ry_offset = 20
        
        # Dashboard Title
        title_surf = font_title.render("ALIFE SIMULATION DASHBOARD", True, (255, 255, 255))
        screen.blit(title_surf, (rx_offset, ry_offset))
        ry_offset += 40
        
        # [STATS MONITOR]
        pygame.draw.line(screen, (44, 44, 46), (rx_offset, ry_offset), (screen_width - 20, ry_offset), 1)
        ry_offset += 10
        screen.blit(font_header.render("[STATS MONITOR]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        # Print active headcounts
        headcounts_str = f"Tick: {tick:<8} FPS Limit: {fps:.1f}"
        screen.blit(font_body.render(headcounts_str, True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        
        pop_str = f"{params['PREY_NAME']}s: {len(world.prey_list):<6} {params['PREDATOR_NAME']}s: {len(world.predator_list):<6} Food: {len(world.food_list)}"
        screen.blit(font_body.render(pop_str, True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 30
        
        # [FITNESS BREAKDOWN]
        pygame.draw.line(screen, (44, 44, 46), (rx_offset, ry_offset), (screen_width - 20, ry_offset), 1)
        ry_offset += 10
        screen.blit(font_header.render("[FITNESS BREAKDOWN (AGE)]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        # Rank by age/lifespan
        if world.prey_list:
            ages = sorted([p.age for p in world.prey_list])
            worst_age = ages[0]
            median_age = ages[len(ages) // 2]
            elite_age = ages[-1]
            
            # Rank average traits
            avg_energy = sum(p.energy for p in world.prey_list) / len(world.prey_list)
            avg_intel = sum(p.get_intelligence() for p in world.prey_list) / len(world.prey_list)
            avg_eff = sum(p.get_efficiency() for p in world.prey_list) / len(world.prey_list)
        else:
            worst_age = median_age = elite_age = 0
            avg_energy = avg_intel = avg_eff = 0
            
        screen.blit(font_body.render(f"Elite Score (Max Age): {elite_age} Ticks", True, (10, 132, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        screen.blit(font_body.render(f"Median Score: {median_age} Ticks", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        screen.blit(font_body.render(f"Worst Score: {worst_age} Ticks", True, (255, 59, 48)), (rx_offset, ry_offset))
        ry_offset += 30
        
        # [GLOBAL TRAITS MONITOR]
        pygame.draw.line(screen, (44, 44, 46), (rx_offset, ry_offset), (screen_width - 20, ry_offset), 1)
        ry_offset += 10
        screen.blit(font_header.render("[GLOBAL TRAITS MOVING AVERAGE]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        screen.blit(font_body.render(f"Avg Energy: {avg_energy:.1f}", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        screen.blit(font_body.render(f"Avg Intelligence: {avg_intel:.1f} / 100", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 20
        screen.blit(font_body.render(f"Avg Efficiency: {avg_eff:.1f} / 100", True, (255, 255, 255)), (rx_offset, ry_offset))
        ry_offset += 35
        
        # [POPULATION GRAPH]
        pygame.draw.line(screen, (44, 44, 46), (rx_offset, ry_offset), (screen_width - 20, ry_offset), 1)
        ry_offset += 10
        screen.blit(font_header.render("[POPULATION HISTORICAL TRENDS]", True, (142, 142, 147)), (rx_offset, ry_offset))
        ry_offset += 25
        
        # Draw dynamic pop line graph
        graph_width = 400
        graph_height = 120
        graph_x = rx_offset
        graph_y = ry_offset
        
        # Draw background container for graph
        pygame.draw.rect(screen, (28, 28, 30), (graph_x, graph_y, graph_width, graph_height))
        pygame.draw.rect(screen, (44, 44, 46), (graph_x, graph_y, graph_width, graph_height), 1)
        
        # Plot coordinates
        if len(history_prey) > 1:
            max_val = max(max(history_prey), max(history_predator), max(history_food), 10)
            
            # Map index i and value v to pixel coordinates
            def get_point(i: int, val: int) -> Tuple[int, int]:
                x_p = graph_x + (i / (max_history_len - 1)) * graph_width
                y_p = graph_y + graph_height - (val / max_val) * graph_height
                return int(x_p), int(y_p)
                
            points_prey = [get_point(i, v) for i, v in enumerate(history_prey)]
            points_pred = [get_point(i, v) for i, v in enumerate(history_predator)]
            points_food = [get_point(i, v) for i, v in enumerate(history_food)]
            
            # Draw lines
            pygame.draw.lines(screen, (10, 132, 255), False, points_prey, 2)
            pygame.draw.lines(screen, (255, 59, 48), False, points_pred, 2)
            pygame.draw.lines(screen, (52, 199, 89), False, points_food, 2)

        if extinct:
            # Draw overlay banner
            banner_rect = pygame.Rect(grid_width_pixels // 2 - 175, grid_height_pixels // 2 - 40, 350, 80)
            pygame.draw.rect(screen, (30, 30, 30), banner_rect)
            pygame.draw.rect(screen, (255, 59, 48), banner_rect, 2)
            
            extinct_text1 = font_header.render("ZIZOID EXTINCTION HIT", True, (255, 59, 48))
            extinct_text2 = font_body.render("Press ESC to Close Window", True, (255, 255, 255))
            
            screen.blit(extinct_text1, (grid_width_pixels // 2 - extinct_text1.get_width() // 2, grid_height_pixels // 2 - 25))
            screen.blit(extinct_text2, (grid_width_pixels // 2 - extinct_text2.get_width() // 2, grid_height_pixels // 2 + 5))
            
        pygame.display.flip()
        
        # Frame limit clock check
        clock.tick(int(fps))
        
    pygame.quit()
    
    # 4. Display Final Summary Audit of Simulation run
    print("\n============================================================")
    print("             SIMULATION SHUTDOWN COMPLETE")
    print("============================================================")
    print(f"Elapsed Time steps: {tick}")
    print(f"Metrics logged to 'simulation_1.csv'.")
    print("============================================================")

if __name__ == "__main__":
    main()
