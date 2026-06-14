class Food:
    def __init__(self, x: int, y: int, base_value: float = 40.0):
        self.x = x
        self.y = y
        self.base_value = base_value
        self.ticks_unstepped = 10

    def get_nutrition(self) -> float:
        if self.ticks_unstepped <= 10:
            return self.base_value
        return self.base_value * (1.0 + 0.25 * (self.ticks_unstepped - 10))

    def step(self):
        self.ticks_unstepped += 1
