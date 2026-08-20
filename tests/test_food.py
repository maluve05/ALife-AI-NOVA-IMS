import unittest
from Alife_Simulation.code.food import Food

class TestFood(unittest.TestCase):
    def setUp(self):
        self.food = Food(x=3, y=7, base_value=40.0)

    def test_initialization(self):
        self.assertEqual(self.food.x, 3)
        self.assertEqual(self.food.y, 7)
        self.assertEqual(self.food.base_value, 40.0)
        self.assertEqual(self.food.ticks_unstepped, 10)

    def test_nutrition_base(self):
        # When ticks_unstepped <= 10, nutrition equals base_value
        self.assertEqual(self.food.get_nutrition(), 40.0)

    def test_nutrition_growth_over_time(self):
        for _ in range(5):
            self.food.step()
        self.assertEqual(self.food.ticks_unstepped, 15)
        # 40 * (1 + 0.25 * (15 - 10)) = 40 * (1 + 1.25) = 40 * 2.25 = 90.0
        self.assertEqual(self.food.get_nutrition(), 90.0)

if __name__ == "__main__":
    unittest.main()
