"""
Artificial Life Simulation Core Package
"""

try:
    from Alife_Simulation.code.ANNprey import ANNPrey
    from Alife_Simulation.code.food import Food
    from Alife_Simulation.code.predator import Predator
    from Alife_Simulation.code.prey import Prey
    from Alife_Simulation.code.world import World
    from Alife_Simulation.code.graphics import SimulationGraphics
except ImportError:
    try:
        from code.ANNprey import ANNPrey
        from code.food import Food
        from code.predator import Predator
        from code.prey import Prey
        from code.world import World
        from code.graphics import SimulationGraphics
    except ImportError:
        from .ANNprey import ANNPrey
        from .food import Food
        from .predator import Predator
        from .prey import Prey
        from .world import World
        from .graphics import SimulationGraphics

__all__ = [
    "ANNPrey",
    "Food",
    "Predator",
    "Prey",
    "World",
    "SimulationGraphics",
]
