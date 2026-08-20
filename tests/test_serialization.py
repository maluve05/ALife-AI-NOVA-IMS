import unittest
import os
import tempfile
import json
import csv
from Alife_Simulation.code.world import World
from Alife_Simulation.game import save_state_to_json, load_state_from_json, log_to_csv, DEFAULT_PARAMETERS

class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.params = DEFAULT_PARAMETERS.copy()
        self.params["GRID_WIDTH"] = 15
        self.params["GRID_HEIGHT"] = 20
        self.params["INITIAL_PREY_COUNT"] = 10
        self.params["INITIAL_PREDATOR_COUNT"] = 2
        self.world = World(15, 20, self.params)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_json_save_and_load_roundtrip(self):
        json_path = os.path.join(self.temp_dir.name, "test_state.json")
        save_state_to_json(self.world, self.params, tick=42, file_path=json_path)
        
        self.assertTrue(os.path.exists(json_path))
        
        loaded_world, loaded_params, loaded_tick = load_state_from_json(json_path)
        
        self.assertEqual(loaded_tick, 42)
        self.assertEqual(len(loaded_world.prey_list), len(self.world.prey_list))
        self.assertEqual(len(loaded_world.predator_list), len(self.world.predator_list))
        self.assertEqual(len(loaded_world.food_list), len(self.world.food_list))
        
        # Verify first prey attributes
        p_orig = self.world.prey_list[0]
        p_loaded = loaded_world.prey_list[0]
        self.assertEqual(p_loaded.id, p_orig.id)
        self.assertEqual(p_loaded.x, p_orig.x)
        self.assertEqual(p_loaded.y, p_orig.y)
        self.assertEqual(len(p_loaded.chromosome), len(p_orig.chromosome))

    def test_csv_logging(self):
        csv_path = os.path.join(self.temp_dir.name, "test_log.csv")
        log_to_csv(15, self.world, self.params, file_path=csv_path)
        log_to_csv(30, self.world, self.params, file_path=csv_path)
        
        self.assertTrue(os.path.exists(csv_path))
        
        with open(csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        self.assertEqual(len(rows), 3)  # Header + 2 data rows
        self.assertEqual(rows[0][0], "Tick")
        self.assertEqual(rows[1][0], "15")
        self.assertEqual(rows[2][0], "30")

if __name__ == "__main__":
    unittest.main()
