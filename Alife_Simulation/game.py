import os
import sys
import json
import csv
import pygame
import random
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code.world import World
from code.prey import Prey
from code.predator import Predator
from code.food import Food
from code.graphics import SimulationGraphics

DEFAULT_PARAMETERS: Dict[str, Any] = {
    "INITIAL_ENERGY_PREY": 150,
    "MUTATION_RATE": 0.05,
    "P_REPRODUCTION": 0.75,
    "INITIAL_PREY_COUNT": 30,
    "INITIAL_PREDATOR_COUNT": 5,
    "MAX_PREY_POPULATION": 300,
    "ENERGY_FROM_CONSUMING_FOOD": 60,
    "ENERGY_FROM_PREDATOR_CATCH": 10,
    "ENERGY_REPRODUCTION_COST": 3,
    "GENERATIONAL_DECAY": 1,
    "FRAME_RATE_LIMIT": 1.0,
    "LOGGING_INTERVAL": 15,
    "GRID_WIDTH": 20,
    "GRID_HEIGHT": 25,
    "PREY_NAME": "Zizoid",
    "PREDATOR_NAME": "Wsiloid"
}

def boot_menu() -> Tuple[World, Dict[str, Any], int]:
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
                file_path = input("Enter JSON state file path (e.g. simulation_state.json): ").strip()
                if not os.path.exists(file_path):
                    print(f"Error: File '{file_path}' not found. Try again.")
                    continue
                with open(file_path, 'r') as f:
                    state_data = json.load(f)
                
                params = state_data.get("parameters", DEFAULT_PARAMETERS.copy())
                cols = params.get("GRID_WIDTH", 15)
                rows = params.get("GRID_HEIGHT", 20)
                
                world = World(cols, rows, params)
                world.prey_list.clear()
                world.predator_list.clear()
                world.food_list.clear()
                
                world.best_prey_ever = state_data.get("best_prey_ever", None)
                world.best_predator_ever = state_data.get("best_predator_ever", None)
                world.best_mating_pair_ever = state_data.get("best_mating_pair_ever", None)
                world.death_causes = state_data.get("death_causes", {"Starvation": 0, "Old Age": 0, "Predation": 0})
                
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
                    
                world.next_predator_id = state_data.get("next_predator_id", 1)
                for pred_data in state_data.get("predators", []):
                    pred = Predator(pred_data["id"], pred_data["name"], pred_data["x"], pred_data["y"])
                    pred.energy = pred_data["energy"]
                    pred.age = pred_data["age"]
                    pred.tracking_efficiency = pred_data.get("tracking_efficiency", 50.0)
                    pred.last_jumped = pred_data.get("last_jumped", False)
                    pred.chase_state = pred_data.get("chase_state", False)
                    pred.catches = pred_data.get("catches", 0)
                    world.predator_list.append(pred)
                    
                for f_data in state_data.get("food", []):
                    f_obj = Food(f_data["x"], f_data["y"], params.get("ENERGY_FROM_CONSUMING_FOOD", 40.0))
                    f_obj.ticks_unstepped = f_data.get("ticks_unstepped", 10)
                    world.food_list.append(f_obj)
                    
                world.sync_grid()
                tick_offset = state_data.get("current_tick", 0)
                print(f"Simulation successfully loaded from '{file_path}' (resuming at tick {tick_offset}).")
                return world, params, tick_offset
                
            elif choice == "2":
                print("Starting default simulation (20x25 grid, 30 Zizoids, 5 Wsiloids)...")
                params = DEFAULT_PARAMETERS.copy()
                world = World(params["GRID_WIDTH"], params["GRID_HEIGHT"], params)
                return world, params, 0
                
            elif choice == "3":
                params = DEFAULT_PARAMETERS.copy()
                print("\n--- Custom Parameter Handshake ---")
                
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
                
                params["PREY_NAME"] = input("Enter name for Prey (default: Zizoid): ").strip() or "Zizoid"
                params["PREDATOR_NAME"] = input("Enter name for Predator (default: Wsiloid): ").strip() or "Wsiloid"
                
                try:
                    params["INITIAL_ENERGY_PREY"] = float(input("Enter starting Prey (Zizoid) energy (default 100): ") or "100")
                    params["MUTATION_RATE"] = float(input("Enter Mutation Rate (0.0 to 1.0, default 0.05): ") or "0.05")
                    params["P_REPRODUCTION"] = float(input("Enter Prob(reproduction) (0.0 to 1.0, default 0.50): ") or "0.50")
                    params["ENERGY_FROM_PREDATOR_CATCH"] = float(input("Enter Predator catch energy reward (default 10): ") or "10")
                    params["ENERGY_REPRODUCTION_COST"] = float(input("Enter energy cost factor spent on reproduction (default 3): ") or "3")
                    params["MAX_PREY_POPULATION"] = int(input("Enter maximum number of Prey (default 300): ") or "300")
                    params["ENERGY_FROM_CONSUMING_FOOD"] = float(input("Enter Food energy value (default 40): ") or "40")
                    params["FRAME_RATE_LIMIT"] = float(input("Enter initial speed in FPS (default 1.0): ") or "1.0")
                except ValueError:
                    print("Invalid value entered. Reverting attributes to defaults.")
                
                total_cells = params["GRID_WIDTH"] * params["GRID_HEIGHT"]
                max_agents = total_cells // 3
                print(f"Starting Populations configuration (Note: Predators + Prey <= {max_agents} agents total):")
                while True:
                    try:
                        prey_count = int(input(f"Enter initial number of {params['PREY_NAME']}s (default 30): ") or "30")
                        pred_count = int(input(f"Enter initial number of {params['PREDATOR_NAME']}s (default 5): ") or "5")
                        total_agents = prey_count + pred_count
                        if total_agents > max_agents:
                            print(f"Error: Total agents ({total_agents}) exceeds maximum capacity of {max_agents} for the grid. Re-enter.")
                            continue
                        if prey_count <= 0 or pred_count <= 0:
                            print("Error: Starting populations must be greater than zero. Re-enter.")
                            continue
                        params["INITIAL_PREY_COUNT"] = prey_count
                        params["INITIAL_PREDATOR_COUNT"] = pred_count
                        break
                    except ValueError:
                        print("Invalid input. Please enter integers.")
                
                world = World(params["GRID_WIDTH"], params["GRID_HEIGHT"], params)
                return world, params, 0
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
        except Exception as e:
            print(f"Error handling menu setup: {e}. Try again.")

def save_state_to_json(world: World, params: Dict[str, Any], tick: int, file_path: str = "simulation_state.json"):
    state = {
        "current_tick": tick,
        "next_prey_id": world.next_prey_id,
        "next_predator_id": world.next_predator_id,
        "parameters": params,
        "best_prey_ever": world.best_prey_ever,
        "best_predator_ever": world.best_predator_ever,
        "best_mating_pair_ever": world.best_mating_pair_ever,
        "death_causes": world.death_causes,
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
                "chase_state": pred.chase_state,
                "catches": pred.catches
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
    file_exists = os.path.exists(file_path)
    
    avg_energy = sum(p.energy for p in world.prey_list) / max(1, len(world.prey_list))
    avg_intel = sum(p.get_intelligence() for p in world.prey_list) / max(1, len(world.prey_list))
    avg_eff = sum(p.get_efficiency() for p in world.prey_list) / max(1, len(world.prey_list))
    
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
        json.dumps(elite_chromo)
    ]
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Tick", "PreyCount", "PredatorCount", "FoodCount", 
                "AvgEnergy", "AvgIntelligence", "AvgEfficiency", "EliteChromosome"
            ])
        writer.writerow(row)

def main():
    world, params, tick = boot_menu()
    
    graphics = SimulationGraphics(world.cols, world.rows, params)
    clock = pygame.time.Clock()
    
    history_prey: List[int] = []
    history_predator: List[int] = []
    history_food: List[int] = []
    max_history_len = 200
    
    running = True
    fps = params.get("FRAME_RATE_LIMIT", 1.0)
    paused = False
    extinct = False
    
    print(f"\nSimulation graphics loaded successfully! Window resolution: {graphics.screen_width}x{graphics.screen_height} px.")
    print("Controls:")
    print("  [SPACE] - Pause/Play simulation execution.")
    print("  [UP Arrow] - Speed up simulation frame rate.")
    print("  [DOWN Arrow] - Slow down simulation frame rate.")
    print("  [S] - Save current simulation state immediately.")
    print("  [ESC] - Quit simulation.")
    
    while running:
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
                    
        if len(world.prey_list) == 0 and not extinct:
            extinct = True
            print("\n============================================================")
            print("             ZIZOID EXTINCTION CONSTRAINTS HIT!")
            print("============================================================")
            print(f"Final Tick Duration: {tick} Epochs")
            print("Shutting down simulation environment updates.")
            print("============================================================")
            
        if not paused and not extinct:
            world.update()
            tick += 1
            
            history_prey.append(len(world.prey_list))
            history_predator.append(len(world.predator_list))
            history_food.append(len(world.food_list))
            if len(history_prey) > max_history_len:
                history_prey.pop(0)
                history_predator.pop(0)
                history_food.pop(0)
                
            if tick % params.get("LOGGING_INTERVAL", 15) == 0:
                log_to_csv(tick, world, params)
                save_state_to_json(world, params, tick)
                
        graphics.render(tick, world, params, fps, history_prey, history_predator, history_food, extinct)
        clock.tick(int(fps))
        
    graphics.close()
    
    print("\n============================================================")
    print("             SIMULATION SHUTDOWN COMPLETE")
    print("============================================================")
    print(f"Elapsed Time steps: {tick}")
    print(f"Metrics logged to 'simulation_1.csv'.")
    print("============================================================")

if __name__ == "__main__":
    main()
