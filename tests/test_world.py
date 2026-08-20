import unittest
import random
from Alife_Simulation.code.world import World
from Alife_Simulation.code.prey import Prey
from Alife_Simulation.code.predator import Predator
from Alife_Simulation.code.food import Food

class TestWorld(unittest.TestCase):
    def setUp(self):
        self.params = {
            "INITIAL_ENERGY_PREY": 150,
            "MUTATION_RATE": 0.05,
            "P_REPRODUCTION": 0.75,
            "INITIAL_PREY_COUNT": 20,
            "INITIAL_PREDATOR_COUNT": 3,
            "MAX_PREY_POPULATION": 100,
            "ENERGY_FROM_CONSUMING_FOOD": 60,
            "ENERGY_FROM_PREDATOR_CATCH": 10,
            "ENERGY_REPRODUCTION_COST": 3,
            "GENERATIONAL_DECAY": 1,
            "FRAME_RATE_LIMIT": 1.0,
            "LOGGING_INTERVAL": 15,
            "GRID_WIDTH": 20,
            "GRID_HEIGHT": 20,
            "PREY_NAME": "Zizoid",
            "PREDATOR_NAME": "Wsiloid"
        }
        self.world = World(20, 20, self.params)

    def test_initialization(self):
        self.assertEqual(self.world.cols, 20)
        self.assertEqual(self.world.rows, 20)
        self.assertEqual(len(self.world.predator_list), 3)
        self.assertEqual(len(self.world.prey_list), 20)
        self.assertGreater(len(self.world.food_list), 0)

    def test_grid_sync_values(self):
        self.world.sync_grid()
        for p in self.world.prey_list:
            self.assertEqual(self.world.grid[p.y][p.x], 3)
        for pred in self.world.predator_list:
            self.assertEqual(self.world.grid[pred.y][pred.x], 1)
        for f in self.world.food_list:
            self.assertEqual(self.world.grid[f.y][f.x], 2)

    def test_crossover_strategies(self):
        p1 = Prey(1, "Parent1", 0, 0, [1.0] * 712)
        p2 = Prey(2, "Parent2", 1, 1, [-1.0] * 712)
        
        # Test individual strategy execution
        for strategy in [1, 2, 3]:
            child_chromo = self.world._perform_crossover_strategy(p1, p2, strategy, 712)
            self.assertEqual(len(child_chromo), 712)
            # Should have elements from both parents
            self.assertTrue(any(g == 1.0 for g in child_chromo))
            self.assertTrue(any(g == -1.0 for g in child_chromo))

    def test_mutation_clamping(self):
        chromo = [0.0] * 712
        mutated = self.world._mutate_chromosome(chromo, mut_rate=1.0, length=712)
        # Weights should be clamped between -2.0 and 2.0
        for w in mutated[:710]:
            self.assertGreaterEqual(w, -2.0)
            self.assertLessEqual(w, 2.0)
        # Base traits should be clamped between 5.0 and 100.0
        for trait in mutated[710:]:
            self.assertGreaterEqual(trait, 5.0)
            self.assertLessEqual(trait, 100.0)

    def test_find_nearest_empty_cell(self):
        empty_pos = self.world.find_nearest_empty_cell(0, 0)
        if empty_pos:
            ex, ey = empty_pos
            self.assertEqual(self.world.grid[ey][ex], 0)

    def test_simulation_step_update(self):
        prey_count_start = len(self.world.prey_list)
        # Run 5 world steps
        for _ in range(5):
            self.world.update()
            
        # Ensure agents are still tracked or death causes recorded
        total_deaths = sum(self.world.death_causes.values())
        self.assertTrue(len(self.world.prey_list) > 0 or total_deaths > 0)

if __name__ == "__main__":
    unittest.main()
