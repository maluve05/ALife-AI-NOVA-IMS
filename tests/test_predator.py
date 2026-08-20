import unittest
from Alife_Simulation.code.predator import Predator

class TestPredator(unittest.TestCase):
    def setUp(self):
        self.pred = Predator(id_val=1, name="Wsiloid_1", x=10, y=10)

    def test_initialization(self):
        self.assertEqual(self.pred.id, 1)
        self.assertEqual(self.pred.name, "Wsiloid_1")
        self.assertEqual(self.pred.x, 10)
        self.assertEqual(self.pred.y, 10)
        self.assertEqual(self.pred.age, 0)
        self.assertEqual(self.pred.energy, 100.0)
        self.assertEqual(self.pred.tracking_efficiency, 50.0)
        self.assertEqual(self.pred.catches, 0)
        self.assertFalse(self.pred.chase_state)

    def test_adjacent_prey_chasing(self):
        # 3 is prey
        grid = [[0] * 20 for _ in range(20)]
        grid[10][11] = 3  # Prey adjacent right (dx=+1, dy=0)
        
        dx, dy = self.pred.get_action_step(grid)
        self.assertTrue(self.pred.chase_state)
        self.assertEqual(dx, 1)
        self.assertEqual(dy, 0)

    def test_valid_empty_move(self):
        grid = [[0] * 20 for _ in range(20)]
        dx, dy = self.pred.get_action_step(grid)
        self.assertFalse(self.pred.chase_state)
        self.assertIn(dx, [-1, 0, 1])
        self.assertIn(dy, [-1, 0, 1])

    def test_failed_chase_penalty(self):
        initial_energy = self.pred.energy
        params = {"GENERATIONAL_DECAY": 2.0}
        self.pred.apply_failed_chase_penalty(params)
        self.assertLess(self.pred.energy, initial_energy)

    def test_fitness(self):
        self.pred.catches = 3
        self.pred.age = 45
        fit = self.pred.get_fitness()
        # 3 * 100 + 45 = 345
        self.assertEqual(fit, 345.0)

if __name__ == "__main__":
    unittest.main()
