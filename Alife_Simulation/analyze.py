#!/usr/bin/env python3
"""
Telemetry Data Analysis & Visualization Script
Processes simulation logs (e.g. simulation_1.csv) to compute evolutionary metrics,
population dynamics, and trait convergence over time.
"""

import os
import sys
import csv
import json
import argparse
from typing import List, Dict, Any, Optional

def parse_simulation_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load and parse the simulation CSV telemetry log."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Telemetry log '{file_path}' does not exist.")
        
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                record = {
                    "Tick": int(row["Tick"]),
                    "PreyCount": int(row["PreyCount"]),
                    "PredatorCount": int(row["PredatorCount"]),
                    "FoodCount": int(row["FoodCount"]),
                    "AvgEnergy": float(row["AvgEnergy"]),
                    "AvgIntelligence": float(row["AvgIntelligence"]),
                    "AvgEfficiency": float(row["AvgEfficiency"]),
                    "EliteChromosome": json.loads(row["EliteChromosome"]) if row.get("EliteChromosome") else []
                }
                records.append(record)
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                continue
    return records

def print_terminal_summary(records: List[Dict[str, Any]], source_file: str):
    """Print clean terminal report of simulation statistics."""
    if not records:
        print(f"No valid records found in {source_file}.")
        return

    first = records[0]
    last = records[-1]
    total_ticks = last["Tick"] - first["Tick"] + 1

    prey_counts = [r["PreyCount"] for r in records]
    pred_counts = [r["PredatorCount"] for r in records]
    food_counts = [r["FoodCount"] for r in records]
    energies = [r["AvgEnergy"] for r in records]
    intelligences = [r["AvgIntelligence"] for r in records]
    efficiencies = [r["AvgEfficiency"] for r in records]

    print("\n" + "=" * 65)
    print(f"       ALIFE SIMULATION TELEMETRY SUMMARY REPORT")
    print(f"       Source File: {os.path.basename(source_file)}")
    print("=" * 65)
    print(f"  * Total Time Horizon:     {total_ticks} Ticks (from tick {first['Tick']} to {last['Tick']})")
    print(f"  * Data Snapshots Logged:  {len(records)} checkpoints")
    print("-" * 65)
    print("  POPULATION DYNAMICS:")
    print(f"    - Prey Count:         Start: {first['PreyCount']:3d} | End: {last['PreyCount']:3d} | Peak: {max(prey_counts):3d} | Min: {min(prey_counts):3d} | Mean: {sum(prey_counts)/len(prey_counts):.1f}")
    print(f"    - Predator Count:     Start: {first['PredatorCount']:3d} | End: {last['PredatorCount']:3d} | Peak: {max(pred_counts):3d} | Min: {min(pred_counts):3d} | Mean: {sum(pred_counts)/len(pred_counts):.1f}")
    print(f"    - Food Availability:  Start: {first['FoodCount']:3d} | End: {last['FoodCount']:3d} | Peak: {max(food_counts):3d} | Min: {min(food_counts):3d} | Mean: {sum(food_counts)/len(food_counts):.1f}")
    print("-" * 65)
    print("  EVOLUTIONARY TRAIT PROGRESSION:")
    print(f"    - Avg Intelligence:   Start: {first['AvgIntelligence']:5.2f}  ==>  End: {last['AvgIntelligence']:5.2f} (Delta: {last['AvgIntelligence'] - first['AvgIntelligence']:+5.2f})")
    print(f"    - Avg Efficiency:     Start: {first['AvgEfficiency']:5.2f}  ==>  End: {last['AvgEfficiency']:5.2f} (Delta: {last['AvgEfficiency'] - first['AvgEfficiency']:+5.2f})")
    print(f"    - Avg Energy Level:   Start: {first['AvgEnergy']:5.2f}  ==>  End: {last['AvgEnergy']:5.2f} (Delta: {last['AvgEnergy'] - first['AvgEnergy']:+5.2f})")
    print("-" * 65)
    
    if last["EliteChromosome"] and len(last["EliteChromosome"]) >= 712:
        elite_eff = last["EliteChromosome"][710]
        elite_intel = last["EliteChromosome"][711]
        print("  FINAL ELITE AGENT GENOME:")
        print(f"    - Base Efficiency:    {elite_eff:.2f} / 100.0")
        print(f"    - Base Intelligence:  {elite_intel:.2f} / 100.0")
        print(f"    - ANN Weights Count:  {len(last['EliteChromosome'][:710])} genes")
    print("=" * 65 + "\n")

def generate_plots(records: List[Dict[str, Any]], output_plot_path: Optional[str] = None):
    """Generate a multi-panel visual analytics plot using Matplotlib if installed."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[Notice] 'matplotlib' is not installed. To generate visual charts, install it via: pip install matplotlib")
        return

    ticks = [r["Tick"] for r in records]
    prey = [r["PreyCount"] for r in records]
    pred = [r["PredatorCount"] for r in records]
    food = [r["FoodCount"] for r in records]
    energy = [r["AvgEnergy"] for r in records]
    intel = [r["AvgIntelligence"] for r in records]
    eff = [r["AvgEfficiency"] for r in records]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Artificial Life Ecosystem Simulation Telemetry", fontsize=16, fontweight='bold')

    # Panel 1: Population Dynamics
    axes[0, 0].plot(ticks, prey, label="Prey (Zizoid)", color="#0a84ff", linewidth=2)
    axes[0, 0].plot(ticks, pred, label="Predators (Wsiloid)", color="#ff3b30", linewidth=2)
    axes[0, 0].plot(ticks, food, label="Food Resources", color="#34c759", linestyle="--", alpha=0.7)
    axes[0, 0].set_title("Ecosystem Population Dynamics", fontweight='bold')
    axes[0, 0].set_xlabel("Ticks")
    axes[0, 0].set_ylabel("Agent Count")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Panel 2: Energy Dynamics
    axes[0, 1].plot(ticks, energy, color="#ff9500", linewidth=2)
    axes[0, 1].set_title("Prey Average Energy Level", fontweight='bold')
    axes[0, 1].set_xlabel("Ticks")
    axes[0, 1].set_ylabel("Mean Energy")
    axes[0, 1].grid(True, alpha=0.3)

    # Panel 3: Evolutionary Traits
    axes[1, 0].plot(ticks, intel, label="Avg Intelligence", color="#af52de", linewidth=2)
    axes[1, 0].plot(ticks, eff, label="Avg Efficiency", color="#5856d6", linewidth=2)
    axes[1, 0].set_title("Trait Evolution Over Generations", fontweight='bold')
    axes[1, 0].set_xlabel("Ticks")
    axes[1, 0].set_ylabel("Score (0 - 100)")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Panel 4: Phase Portrait (Prey vs Predator)
    axes[1, 1].scatter(prey, pred, c=ticks, cmap="viridis", s=15, alpha=0.8)
    axes[1, 1].set_title("Phase Portrait: Prey vs. Predator Density", fontweight='bold')
    axes[1, 1].set_xlabel("Prey Population")
    axes[1, 1].set_ylabel("Predator Population")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if output_plot_path:
        plt.savefig(output_plot_path, dpi=300)
        print(f"Telemetry visual analytics plot saved to '{output_plot_path}'.")
    else:
        plt.show()

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze and visualize ALife simulation telemetry")
    parser.add_argument("--csv", "-f", type=str, default="simulation_1.csv", help="Path to simulation CSV file")
    parser.add_argument("--plot", "-p", type=str, default=None, help="Path to save output plot PNG (e.g. results.png)")
    parser.add_argument("--no-plot", action="store_true", help="Skip matplotlib visual plotting")
    parser.add_argument("--export-json", type=str, default=None, help="Export computed metrics to a JSON file")
    return parser.parse_args()

def main():
    args = parse_args()
    try:
        records = parse_simulation_csv(args.csv)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print_terminal_summary(records, args.csv)

    if args.export_json and records:
        summary_data = {
            "source_file": args.csv,
            "total_records": len(records),
            "start_tick": records[0]["Tick"],
            "end_tick": records[-1]["Tick"],
            "final_prey_count": records[-1]["PreyCount"],
            "final_predator_count": records[-1]["PredatorCount"],
            "final_food_count": records[-1]["FoodCount"],
            "final_avg_intelligence": records[-1]["AvgIntelligence"],
            "final_avg_efficiency": records[-1]["AvgEfficiency"],
            "final_avg_energy": records[-1]["AvgEnergy"]
        }
        with open(args.export_json, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"Exported metrics JSON to '{args.export_json}'.")

    if not args.no_plot and args.plot:
        generate_plots(records, args.plot)

if __name__ == "__main__":
    main()
