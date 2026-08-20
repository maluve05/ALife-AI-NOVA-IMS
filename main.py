#!/usr/bin/env python3
"""
Main Entry Point for the Artificial Life & Ecosystem Simulation Engine
NOVA IMS - Master / Course Project in Artificial Life & AI
"""
import sys
import os

# Ensure the Alife_Simulation folder and root are on Python's path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from Alife_Simulation.game import main

if __name__ == "__main__":
    main()
