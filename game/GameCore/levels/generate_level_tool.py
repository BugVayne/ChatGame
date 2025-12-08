import json
import os
import random
import sys
import time

sys.path.append(os.getcwd())

from game.GameCore.levels.ai_level_generator import AdvancedLevelGenerator


def main():
    print("=== ADVANCED DUNGEON GENERATOR v2.4 (BELL CURVE MODE) ===")

    # 1. Setup Output Folder
    output_folder = "generated_levels"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    # 2. Gather Batch Inputs
    try:
        batch_size = int(input("How many levels to generate? (e.g., 20): ") or 20)
        start_id = int(input("Start numbering from ID? (e.g., 0): ") or 0)
    except ValueError:
        print("Invalid input using defaults.")
        batch_size = 20
        start_id = 0

    print(f"\nStarting Batch Generation of {batch_size} levels...")
    total_start_time = time.time()

    # 3. Batch Loop
    for i in range(batch_size):
        current_id = start_id + i

        # --- Randomize Configuration ---

        # A. Size: Pick randomly from presets
        size_presets = [(15, 10), (18, 10), (12, 8), (10, 8), (8, 10)]
        width, height = random.choice(size_presets)

        # B. Difficulty: BELL CURVE DISTRIBUTION
        # mu=5.5 (center), sigma=2.0 (spread)
        # Most results will be between 3 and 8. 1 and 10 will be rare.
        diff_val = random.gauss(4, 2.0)

        # Round and Clamp between 1 and 10
        difficulty = int(max(1, min(10, round(diff_val))))

        # 4. Run AI Generation
        ai = AdvancedLevelGenerator(width, height, difficulty)
        grid = ai.generate()
        raw_level_data = ai.convert_to_game_format(grid)

        # Inject difficulty into name for visibility in Viewer
        raw_level_data["name"] = f"Gen Level {current_id} (Diff {difficulty})"
        raw_level_data["difficulty"] = difficulty

        # 5. Save File
        formatted_output = {str(current_id): raw_level_data}

        filename = f"generated_level_{current_id}.json"
        full_path = os.path.join(output_folder, filename)

        with open(full_path, "w") as f:
            json.dump(formatted_output, f, indent=4)

        print(
            f"[Generated] ID: {current_id} | Size: {width}x{height} | Diff: {difficulty} -> Saved."
        )

    total_elapsed = time.time() - total_start_time
    print(f"\n[BATCH COMPLETE] Generated {batch_size} levels in {total_elapsed:.2f}s")
    print(f"Files saved to '{output_folder}/'")
    print("Run 'level_viewer.py' to inspect them.")


if __name__ == "__main__":
    main()
