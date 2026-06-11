"""
food.py

Passive resource management for Food (Cacao).
Tracks nutritional value and compounding growth mechanics over time.
"""

class Food:
    def __init__(self, x: int, y: int, base_value: float = 40.0):
        """
        Initializes a Food resource at specific coordinates.
        :param x: X-coordinate (column index)
        :param y: Y-coordinate (row index)
        :param base_value: Base energy value of food
        """
        self.x = x
        self.y = y
        self.base_value = base_value
        self.ticks_unstepped = 5  # Food starts fully sprouted at tick 0

    def get_nutrition(self) -> float:
        """
        Calculates and returns the current nutritional value of this food instance.
        If it has been unstepped for more than 5 ticks, nutrition compounds linearly.
        """
        if self.ticks_unstepped <= 5:
            return self.base_value
        
        # Compounding formula: Base Value * (1 + 0.5 * (Ticks Unstepped - 5))
        compounding_factor = 1.0 + 0.25 * (self.ticks_unstepped - 5)
        return self.base_value * compounding_factor

    def step(self):
        """
        Increments the unstepped tick count representing food aging/compounding.
        """
        self.ticks_unstepped += 1
