import os
import sys
import json
import csv
import random
import argparse
from typing import Dict, Any, List, Tuple, Optional

# Ensure parent directory and current directory are on sys.path for flexible importing
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from Alife_Simulation.code.world import World
    from Alife_Simulation.code.prey import Prey
    from Alife_Simulation.code.predator import Predator
    from Alife_Simulation.code.food import Food
    from Alife_Simulation.code.graphics import SimulationGraphics
except ImportError:
    try:
        from code.world import World
        from code.prey import Prey
        from code.predator import Predator
        from code.food import Food
        from code.graphics import SimulationGraphics
    except ImportError:
        from .code.world import World
        from .code.prey import Prey
        from .code.predator import Predator
        from .code.food import Food
        from .code.graphics import SimulationGraphics

DEFAULT_PARAMETERS: Dict[str, Any] = {
    "INITIAL_ENERGY_PREY": 150,
    "MUTATION_RATE": 0.05,
    "P_REPRODUCTION": 0.75,
    "INITIAL_PREY_COUNT": 60,
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

def load_state_from_json(file_path: str) -> Tuple[World, Dict[str, Any], int]:
    """Load a world state and configuration from a JSON snapshot file."""
    with open(file_path, 'r') as f:
        state_data = json.load(f)
    
    params = state_data.get("parameters", DEFAULT_PARAMETERS.copy())
    cols = params.get("GRID_WIDTH", 20)
    rows = params.get("GRID_HEIGHT", 25)
    
    world = World(cols, rows, params)
    world.prey_list.clear()
    world.predator_list.clear()
    world.food_list.clear()
    
    world.best_prey_ever = state_data.get("best_prey_ever", None)
    world.best_predator_ever = state_data.get("best_predator_ever", None)
    world.best_mating_pair_ever = state_data.get("best_mating_pair_ever", None)
    world.death_causes = state_data.get("death_causes", {"Starvation": 0, "Old Age": 0, "Predation": 0})
    
    _parse_prey_state(world, state_data.get("prey", []))
    _parse_predator_state(world, state_data.get("predators", []))
    _parse_food_state(world, state_data.get("food", []), params)
    
    world.sync_grid()
    tick_offset = state_data.get("current_tick", 0)
    print(f"Simulation successfully loaded from '{file_path}' (resuming at tick {tick_offset}).")
    return world, params, tick_offset

def _parse_prey_state(world: World, prey_data: List[Dict[str, Any]]):
    for p_data in prey_data:
        p = Prey(p_data["id"], p_data["name"], p_data["x"], p_data["y"], p_data.get("chromosome"))
        p.energy = p_data["energy"]
        p.age = p_data["age"]
        p.gestation_timer = p_data.get("gestation_timer", 0)
        p.is_pregnant = p_data.get("is_pregnant", False)
        p.last_jumped = p_data.get("last_jumped", False)
        p.total_food_eaten = p_data.get("total_food_eaten", 0)
        p.successful_offspring = p_data.get("successful_offspring", 0)
        world.prey_list.append(p)

def _parse_predator_state(world: World, predator_data: List[Dict[str, Any]]):
    for pred_data in predator_data:
        pred = Predator(pred_data["id"], pred_data["name"], pred_data["x"], pred_data["y"])
        pred.energy = pred_data["energy"]
        pred.age = pred_data["age"]
        pred.tracking_efficiency = pred_data.get("tracking_efficiency", 50.0)
        pred.last_jumped = pred_data.get("last_jumped", False)
        pred.chase_state = pred_data.get("chase_state", False)
        pred.catches = pred_data.get("catches", 0)
        world.predator_list.append(pred)

def _parse_food_state(world: World, food_data: List[Dict[str, Any]], params: Dict[str, Any]):
    for f_data in food_data:
        f_obj = Food(f_data["x"], f_data["y"], params.get("ENERGY_FROM_CONSUMING_FOOD", 60.0))
        f_obj.ticks_unstepped = f_data.get("ticks_unstepped", 10)
        world.food_list.append(f_obj)

def _configure_custom_simulation() -> Tuple[World, Dict[str, Any], int]:
    params = DEFAULT_PARAMETERS.copy()
    print("\n--- Custom Parameter Handshake ---")
    
    _prompt_grid_dimensions(params)
    
    params["PREY_NAME"] = input("Enter name for Prey (default: Zizoid): ").strip() or "Zizoid"
    params["PREDATOR_NAME"] = input("Enter name for Predator (default: Wsiloid): ").strip() or "Wsiloid"
    _prompt_simulation_parameters(params)
    
    total_cells = params["GRID_WIDTH"] * params["GRID_HEIGHT"]
    max_agents = total_cells // 3
    _prompt_agent_populations(params, max_agents)
            
    world = World(params["GRID_WIDTH"], params["GRID_HEIGHT"], params)
    return world, params, 0

def _prompt_grid_dimensions(params: Dict[str, Any]):
    while True:
        try:
            width = int(input("Enter Grid Width (default 20): ") or "20")
            height = int(input("Enter Grid Height (default 25): ") or "25")
            total_cells = width * height
            if total_cells < 300:
                print(f"Error: Grid yields {total_cells} cells. Minimum 300 cells is required. Re-enter.")
                continue
            params["GRID_WIDTH"] = width
            params["GRID_HEIGHT"] = height
            break
        except ValueError:
            print("Invalid input. Please enter integers.")

def _prompt_simulation_parameters(params: Dict[str, Any]):
    try:
        params["INITIAL_ENERGY_PREY"] = float(input("Enter starting Prey (Zizoid) energy (default 150): ") or "150")
        params["MUTATION_RATE"] = float(input("Enter Mutation Rate (0.0 to 1.0, default 0.05): ") or "0.05")
        params["P_REPRODUCTION"] = float(input("Enter Prob(reproduction) (0.0 to 1.0, default 0.75): ") or "0.75")
        params["ENERGY_FROM_PREDATOR_CATCH"] = float(input("Enter Predator catch energy reward (default 10): ") or "10")
        params["ENERGY_REPRODUCTION_COST"] = float(input("Enter energy cost factor spent on reproduction (default 3): ") or "3")
        params["MAX_PREY_POPULATION"] = int(input("Enter maximum number of Prey (default 300): ") or "300")
        params["ENERGY_FROM_CONSUMING_FOOD"] = float(input("Enter Food energy value (default 60): ") or "60")
        params["FRAME_RATE_LIMIT"] = float(input("Enter initial speed in FPS (default 1.0): ") or "1.0")
    except ValueError:
        print("Invalid value entered. Reverting attributes to defaults.")

def _prompt_agent_populations(params: Dict[str, Any], max_agents: int):
    print(f"Starting Populations configuration (Note: Predators + Prey <= {max_agents} agents total):")
    while True:
        try:
            prey_count = int(input(f"Enter initial number of {params['PREY_NAME']}s (default {params['INITIAL_PREY_COUNT']}): ") or str(params['INITIAL_PREY_COUNT']))
            pred_count = int(input(f"Enter initial number of {params['PREDATOR_NAME']}s (default {params['INITIAL_PREDATOR_COUNT']}): ") or str(params['INITIAL_PREDATOR_COUNT']))
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
                return load_state_from_json(file_path)
            elif choice == "2":
                params = DEFAULT_PARAMETERS.copy()
                print(f"Starting default simulation ({params['GRID_WIDTH']}x{params['GRID_HEIGHT']} grid, {params['INITIAL_PREY_COUNT']} {params['PREY_NAME']}s, {params['INITIAL_PREDATOR_COUNT']} {params['PREDATOR_NAME']}s)...")
                world = World(params["GRID_WIDTH"], params["GRID_HEIGHT"], params)
                return world, params, 0
            elif choice == "3":
                return _configure_custom_simulation()
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting boot menu.")
            sys.exit(0)
        except Exception as e:
            print(f"Error handling menu setup: {e}. Try again.")

def save_state_to_json(world: World, params: Dict[str, Any], tick: int, file_path: str = "simulation_state.json"):
    """Save the complete world state, agents, and parameters into a JSON file."""
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
    # Ensure directory exists if file_path includes directories
    target_dir = os.path.dirname(file_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)

def log_to_csv(tick: int, world: World, params: Dict[str, Any], file_path: str = "simulation_1.csv"):
    """Append current step metrics to CSV log file."""
    file_exists = os.path.exists(file_path)
    target_dir = os.path.dirname(file_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
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

def _handle_events(fps: float, paused: bool, world: World, params: Dict[str, Any], tick: int,
                   json_path: str = "simulation_state.json") -> Tuple[bool, bool, float]:
    import pygame
    running = True
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
                save_state_to_json(world, params, tick, json_path)
                print(f"Simulation state checkpoint saved at tick {tick} to '{json_path}'.")
    return running, paused, fps

def run_headless_simulation(world: World, params: Dict[str, Any], start_tick: int = 0,
                            max_ticks: int = 1000, csv_path: str = "simulation_1.csv",
                            json_path: str = "simulation_state.json", log_interval: Optional[int] = None) -> int:
    """Execute simulation without GUI for batch or automated experiments."""
    interval = log_interval or params.get("LOGGING_INTERVAL", 15)
    tick = start_tick
    target_tick = start_tick + max_ticks
    
    print(f"\n[Headless Mode] Starting simulation from tick {tick} to {target_tick}...")
    print(f"Grid: {world.cols}x{world.rows} | Initial Prey: {len(world.prey_list)} | Initial Predators: {len(world.predator_list)} | Food: {len(world.food_list)}")
    
    # Initial log
    log_to_csv(tick, world, params, csv_path)
    
    while tick < target_tick:
        if len(world.prey_list) == 0:
            print(f"\n[Extinction] All {params['PREY_NAME']}s extinct at tick {tick}.")
            break
            
        world.update()
        tick += 1
        
        if tick % interval == 0:
            log_to_csv(tick, world, params, csv_path)
            save_state_to_json(world, params, tick, json_path)
            avg_fit = sum(p.get_fitness() for p in world.prey_list) / max(1, len(world.prey_list))
            print(f"Tick {tick:5d} | Prey: {len(world.prey_list):3d} | Predators: {len(world.predator_list):2d} | Food: {len(world.food_list):3d} | AvgFit: {avg_fit:6.1f}")

    # Final state checkpoint & log
    log_to_csv(tick, world, params, csv_path)
    save_state_to_json(world, params, tick, json_path)
    _print_shutdown_summary(tick, csv_path)
    return tick

def run_gui_simulation(world: World, params: Dict[str, Any], start_tick: int = 0,
                       max_ticks: Optional[int] = None, csv_path: str = "simulation_1.csv",
                       json_path: str = "simulation_state.json"):
    """Execute simulation with interactive Pygame GUI dashboard."""
    import pygame
    graphics, history_prey, history_predator, history_food, max_history_len = _initialize_simulation_components(world, params)
    
    clock = pygame.time.Clock()
    running = True
    fps = params.get("FRAME_RATE_LIMIT", 1.0)
    paused = False
    extinct = False
    tick = start_tick
    target_tick = (start_tick + max_ticks) if max_ticks else None
    
    while running:
        running, paused, fps = _handle_events(fps, paused, world, params, tick, json_path)
        if not running:
            break
            
        extinct = _handle_extinction_check(world, tick, extinct, params)
            
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
                log_to_csv(tick, world, params, csv_path)
                save_state_to_json(world, params, tick, json_path)
                
            if target_tick and tick >= target_tick:
                print(f"\nTarget tick count of {target_tick} reached.")
                break
                
        graphics.render(tick, world, params, fps, history_prey, history_predator, history_food, extinct)
        clock.tick(max(1, int(fps)))
        
    graphics.close()
    _print_shutdown_summary(tick, csv_path)

def _initialize_simulation_components(world: World, params: Dict[str, Any]) -> Tuple[SimulationGraphics, List[int], List[int], List[int], int]:
    graphics = SimulationGraphics(world.cols, world.rows, params)
    history_prey: List[int] = []
    history_predator: List[int] = []
    history_food: List[int] = []
    max_history_len = 200
    
    print(f"\nSimulation graphics loaded successfully! Window resolution: {graphics.screen_width}x{graphics.screen_height} px.")
    print("Controls:")
    print("  [SPACE] - Pause/Play simulation execution.")
    print("  [UP Arrow] - Speed up simulation frame rate.")
    print("  [DOWN Arrow] - Slow down simulation frame rate.")
    print("  [S] - Save current simulation state immediately.")
    print("  [ESC] - Quit simulation.")
    
    return graphics, history_prey, history_predator, history_food, max_history_len

def _handle_extinction_check(world: World, tick: int, extinct: bool, params: Dict[str, Any]) -> bool:
    if len(world.prey_list) == 0 and not extinct:
        prey_name = params.get("PREY_NAME", "Zizoid")
        print("\n============================================================")
        print(f"             {prey_name.upper()} EXTINCTION CONSTRAINTS HIT!")
        print("============================================================")
        print(f"Final Tick Duration: {tick} Epochs")
        print("Shutting down simulation environment updates.")
        print("============================================================")
        return True
    return extinct

def _print_shutdown_summary(tick: int, csv_path: str = "simulation_1.csv"):
    print("\n============================================================")
    print("             SIMULATION SHUTDOWN COMPLETE")
    print("============================================================")
    print(f"Elapsed Time steps: {tick}")
    print(f"Metrics logged to '{csv_path}'.")
    print("============================================================")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Artificial Life & ANN Ecosystem Simulation Engine (NOVA IMS)"
    )
    parser.add_argument("--headless", "-H", action="store_true", help="Run simulation in headless mode (no Pygame window)")
    parser.add_argument("--ticks", "-t", type=int, default=None, help="Maximum number of ticks to simulate")
    parser.add_argument("--load", "-l", type=str, default=None, help="Load simulation state from JSON checkpoint")
    parser.add_argument("--config", "-c", type=str, default=None, help="Load simulation parameters from JSON config file")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Set random seed for deterministic execution")
    parser.add_argument("--csv", type=str, default="simulation_1.csv", help="Path to output CSV log file")
    parser.add_argument("--json", type=str, default="simulation_state.json", help="Path to output JSON checkpoint file")
    parser.add_argument("--fps", type=float, default=None, help="Target FPS limit for GUI mode")
    parser.add_argument("--grid-width", type=int, default=None, help="Override grid width")
    parser.add_argument("--grid-height", type=int, default=None, help="Override grid height")
    parser.add_argument("--prey-count", type=int, default=None, help="Override starting Prey population")
    parser.add_argument("--predator-count", type=int, default=None, help="Override starting Predator population")
    parser.add_argument("--mutation-rate", type=float, default=None, help="Override mutation rate (0.0 - 1.0)")
    parser.add_argument("--log-interval", type=int, default=None, help="Metrics logging interval in ticks")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Random seed set to {args.seed}.")

    # Parameter loading & overrides
    params = DEFAULT_PARAMETERS.copy()
    
    if args.config:
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                custom_cfg = json.load(f)
                params.update(custom_cfg)
            print(f"Configuration overrides loaded from '{args.config}'.")
        else:
            print(f"Warning: Config file '{args.config}' not found. Using defaults.")
            
    if args.grid_width:
        params["GRID_WIDTH"] = args.grid_width
    if args.grid_height:
        params["GRID_HEIGHT"] = args.grid_height
    if args.prey_count:
        params["INITIAL_PREY_COUNT"] = args.prey_count
    if args.predator_count:
        params["INITIAL_PREDATOR_COUNT"] = args.predator_count
    if args.mutation_rate is not None:
        params["MUTATION_RATE"] = args.mutation_rate
    if args.fps is not None:
        params["FRAME_RATE_LIMIT"] = args.fps
    if args.log_interval:
        params["LOGGING_INTERVAL"] = args.log_interval

    # Initialization
    if args.load:
        world, params, start_tick = load_state_from_json(args.load)
    elif args.headless or any([args.ticks, args.config, args.grid_width, args.grid_height, args.prey_count]):
        world = World(params["GRID_WIDTH"], params["GRID_HEIGHT"], params)
        start_tick = 0
    else:
        # Default interactive menu
        world, params, start_tick = boot_menu()

    # Execution Mode
    if args.headless:
        ticks_to_run = args.ticks if args.ticks is not None else 500
        run_headless_simulation(
            world=world,
            params=params,
            start_tick=start_tick,
            max_ticks=ticks_to_run,
            csv_path=args.csv,
            json_path=args.json,
            log_interval=args.log_interval
        )
    else:
        run_gui_simulation(
            world=world,
            params=params,
            start_tick=start_tick,
            max_ticks=args.ticks,
            csv_path=args.csv,
            json_path=args.json
        )

if __name__ == "__main__":
    main()
