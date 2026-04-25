# FootyZero

A realistic 2D football simulation environment designed for Reinforcement Learning (RL) self-play training.

## Project Overview

FootyZero provides a high-fidelity 2D football pitch (74x114 units) where two teams of three players (Defender, Midfielder, Forward) compete. The environment is built with Gymnasium compatibility, making it ideal for training agents using algorithms like PPO (Proximal Policy Optimization).

### Key Features

*   **Realistic Physics:** Includes ball friction, player pace, and tackle/possession mechanics.
*   **Tactical Heuristics:** Players use a mix of RL-driven tactical decisions (Depth, Width, Aggression, Directness) and automated movement logic.
*   **Gymnasium Integration:** Standard `obs, reward, terminated, truncated, info` loop with deterministic steps for reproducibility.
*   **Broadcast Engine:** High-quality HTML/JS visualization for match replays with scoreboards, timers, and "Full Time" overlays.
*   **Self-Play Ready:** Supports training one team against a saved policy of the other.

## Getting Started

### Installation

1.  Clone the repository.
2.  Set up a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install gymnasium stable-baselines3 torch numpy matplotlib
    ```

### Running the Simulation

*   **Train Agents:** `python3 train_ppo.py --timesteps 100000 --epochs 5`
*   **Record a Match:** `python3 record_match.py` (Generates `broadcast.html`)
*   **Live View:** Set `export_live=True` in `FootyGymEnv` to update `live_state.json` during execution.

## Controls & Logic

*   **Pitch Dimensions:** 74x114.
*   **Team 1:** Attacks toward Y=114 (Top).
*   **Team 2:** Attacks toward Y=0 (Bottom).
*   **Match Duration:** 2000 steps (1000 per half).
*   **Action Space:** Box(-1, 1, (4,)) representing tactical shifts:
    1.  **Depth:** Defensive line height.
    2.  **Width:** Team horizontal spacing.
    3.  **Aggression:** Weight of ball-chasing vs. holding position.
    4.  **Directness:** Preference for long balls/shots vs. short passing.

## Development Status

Current focus is on stabilizing agent behavior and eliminating simulation "stagnation" through refined possession mechanics and dampened repulsion forces.
