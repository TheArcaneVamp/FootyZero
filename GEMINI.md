# FootyZero - Instructional Context

This document provides essential context and instructions for working with the FootyZero codebase. FootyZero is a high-fidelity 2D football simulation environment designed for Reinforcement Learning (RL) self-play training.

## Project Overview

- **Core Goal:** Train two teams of 3 players (Defender, Midfielder, Forward) to play football using Reinforcement Learning (PPO).
- **Primary Technologies:** Python, [Gymnasium](https://gymnasium.farama.org/), [Stable Baselines3](https://stable-baselines3.readthedocs.io/), NumPy, and Pygame for visualization.
- **Architecture:**
    - `FootballEnv`: The core physics and rules engine (`football_env.py`).
    - `FootyGymEnv`: A Gymnasium-compliant wrapper (`footy_env_rl.py`).
    - `TacticalHeuristics`: Static logic that translates high-level tactical shifts into heuristic movements (`tactics.py`).
    - `FootyRenderer`: Native Pygame rendering engine (`renderer.py`).
    - `Player` & `Ball`: Entity classes defining physical attributes and capabilities (`Player.py`, `Ball.py`).
    - `config.py`: Centralized configuration for pitch dimensions, physics, and match rules.

## Technical Specifications

- **Pitch Dimensions:** 74 (Width) x 114 (Length).
- **Match Structure:** 2000 total steps (1000 per half).
- **Action Space:** `Box(-1, 1, (4,))` representing high-level tactical shifts:
    1. **Depth:** Defensive line height (Low to High).
    2. **Width:** Team horizontal spacing (Narrow to Wide).
    3. **Aggression:** Weight of ball-chasing vs. holding position.
    4. **Directness:** Preference for long balls/shots vs. short passing.
- **Observation Space:** `Box(-1, 1, (17,))` including ball position/velocity, player positions, and possession status.

## Key Workflows

### 1. Training Agents
Train agents using self-play PPO. The script alternates training between Team 1 and Team 2.
```bash
python3 train_ppo.py --epochs 25 --timesteps 200000
```
- **Models:** Saved by default as `ppo_footy_team1` and `ppo_footy_team2`.

### 2. Running & Watching Matches
Use `run_match.py` to test models with native Pygame visualization.
```bash
# Watch match at 24 FPS
python3 run_match.py

# Debug Mode (Console output only, max speed)
python3 run_match.py --debug
```

## Development Conventions

- **Physics-First:** Always refer to `config.py` for physical constants (FRICTION, PACE, KICK_POWER).
- **Tactical Logic:** Heuristic logic for movement and action selection is centralized in `tactics.py`. Avoid adding low-level movement logic to the RL environment wrapper.
- **Reward Shaping:** Rewards are biased towards goals (50.0) but also include proximity to goal and possession incentives.
- **Visualization:** Native Pygame renderer is used for evaluations. Training remains headless for maximum performance.

## File Map

- `football_env.py`: Core physics and match rules.
- `footy_env_rl.py`: Gymnasium environment wrapper.
- `tactics.py`: Tactical heuristic controller.
- `Player.py` / `Ball.py`: Physical entities.
- `run_match.py`: Unified entry point for simulation and evaluation.
- `renderer.py`: Native Pygame rendering engine.
- `config.py`: Centralized physical constants.
