import unittest
import os
import tempfile
from Alife_Simulation.code.world import World
from Alife_Simulation.game import run_headless_simulation, DEFAULT_PARAMETERS

class TestHeadlessSimulation(unittest.TestCase):
    def setUp(self):
        self.params = DEFAULT_PARAMETERS.copy()
        self.params["GRID_WIDTH"] = 15
        self.params["GRID_HEIGHT"] = 20
        self.params["INITIAL_PREY_COUNT"] = 15
        self.params["INITIAL_PREDATOR_COUNT"] = 2
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_headless_execution_run(self):
        world = World(15, 20, self.params)
        csv_path = os.path.join(self.temp_dir.name, "headless_test.csv")
        json_path = os.path.join(self.temp_dir.name, "headless_test.json")
        
        final_tick = run_headless_simulation(
            world=world,
            params=self.params,
            start_tick=0,
            max_ticks=20,
            csv_path=csv_path,
            json_path=json_path,
            log_interval=5
        )
        
        self.assertGreaterEqual(final_tick, 1)
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(json_path))

if __name__ == "__main__":
    unittest.main()
