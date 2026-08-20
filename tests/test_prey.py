import unittest
import math
from Alife_Simulation.code.prey import Prey

class TestPrey(unittest.TestCase):
    def setUp(self):
        self.prey = Prey(prey_id=1, name="Zizoid_1", x=5, y=5)
        self.params = {
            "INITIAL_ENERGY_PREY": 150.0,
            "INITIAL_PREY_COUNT": 60,
            "INITIAL_PREDATOR_COUNT": 5,
            "P_REPRODUCTION": 0.75
        }

    def test_initialization_defaults(self):
        self.assertEqual(self.prey.id, 1)
        self.assertEqual(self.prey.name, "Zizoid_1")
        self.assertEqual(self.prey.x, 5)
        self.assertEqual(self.prey.y, 5)
        self.assertEqual(len(self.prey.chromosome), 712)
        self.assertEqual(self.prey.age, 0)
        self.assertEqual(self.prey.energy, 100.0)
        self.assertFalse(self.prey.is_pregnant)

    def test_custom_chromosome_padding(self):
        custom_chromo = [0.5] * 700
        p = Prey(prey_id=2, name="Zizoid_2", x=0, y=0, chromosome=custom_chromo)
        self.assertEqual(len(p.chromosome), 712)

    def test_traits_bounds(self):
        self.prey.chromosome[710] = 25.0  # Base efficiency
        self.prey.chromosome[711] = 30.0  # Base intelligence
        
        self.assertEqual(self.prey.base_efficiency, 25.0)
        self.assertEqual(self.prey.base_intelligence, 30.0)
        
        # Growth with age
        self.prey.age = 10
        eff = self.prey.get_efficiency()
        intel = self.prey.get_intelligence()
        self.assertGreater(eff, 25.0)
        self.assertGreater(intel, 30.0)
        self.assertLessEqual(eff, 100.0)
        self.assertLessEqual(intel, 100.0)

    def test_life_expectancy(self):
        le = Prey.get_life_expectancy(self.params)
        # 0.03125 * 150 * (1 + 60 / 6) = 4.6875 * 11 = 51.5625
        self.assertAlmostEqual(le, 51.5625, places=2)

    def test_gaussian_scaling(self):
        le = 50.0
        self.prey.age = 25  # Exactly mean age
        scale_at_mean = self.prey.get_gaussian_scaling(le)
        self.assertAlmostEqual(scale_at_mean, 1.0, places=4)
        
        self.prey.age = 0
        scale_at_young = self.prey.get_gaussian_scaling(le)
        self.assertLess(scale_at_young, 1.0)

    def test_survival_probability(self):
        le = 50.0
        self.prey.age = 0
        p_young = self.prey.get_survival_probability(le)
        self.assertAlmostEqual(p_young, 1.0, places=4)
        
        self.prey.age = 100
        p_old = self.prey.get_survival_probability(le)
        self.assertLess(p_old, p_young)

    def test_vision_radius_scaling(self):
        total_cells = 400
        self.prey.chromosome[711] = 10.0
        self.prey.age = 0
        self.assertEqual(self.prey.get_vision_radius(total_cells), 1)
        
        self.prey.chromosome[711] = 40.0
        self.assertEqual(self.prey.get_vision_radius(total_cells), 2)
        
        self.prey.chromosome[711] = 60.0
        self.assertEqual(self.prey.get_vision_radius(total_cells), 3)
        
        self.prey.chromosome[711] = 85.0
        self.assertEqual(self.prey.get_vision_radius(total_cells), 4)

    def test_vision_vector_shape(self):
        grid = [[0] * 20 for _ in range(25)]
        grid[5][6] = 2  # food nearby
        v_vector = self.prey.get_vision_vector(grid, 500)
        # Rings 1 (8), 2 (16), 3 (24), 4 (32) = 80 cells + 1 hunger = 81 inputs
        self.assertEqual(len(v_vector), 81)
        self.assertTrue(all(0.0 <= val <= 1.0 for val in v_vector))

    def test_action_step_parsing(self):
        self.prey.orientation = 0  # North
        # Action 0: (1, 1) relative
        dx, dy, d_orient = self.prey.parse_action(0)
        self.assertEqual(dx, 1)
        self.assertEqual(dy, -1)
        self.assertEqual(d_orient, 0)
        
        # Action 4: Turn
        dx, dy, d_orient = self.prey.parse_action(4)
        self.assertEqual(dx, 0)
        self.assertEqual(dy, 0)
        self.assertEqual(d_orient, 1)

    def test_fitness_calculation(self):
        self.prey.age = 10
        self.prey.total_food_eaten = 5
        self.prey.successful_offspring = 2
        fit = self.prey.get_fitness()
        # 1.0 * 10 + 1.5 * 5 + 5.0 * 2 + 0.5 * eff
        expected = 10.0 + 7.5 + 10.0 + 0.5 * self.prey.get_efficiency()
        self.assertAlmostEqual(fit, expected, places=3)

if __name__ == "__main__":
    unittest.main()
