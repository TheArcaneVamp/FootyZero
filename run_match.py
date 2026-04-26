import argparse
import time
import math
import numpy as np
from footy_env_rl import FootyGymEnv
from stable_baselines3 import PPO

def run_match(args):
    print(f"Initializing FootyZero Match Runner...")
    
    # Set render mode: "human" to watch, None for headless debug
    render_mode = "human" if not args.debug else None
    
    env = FootyGymEnv(render_mode=render_mode, max_steps=args.steps)
    
    # Attempt to load models
    model1, model2 = None, None
    try:
        model1 = PPO.load(args.model1)
        print(f"Team 1 Model Loaded: {args.model1}")
    except:
        print(f"Team 1 Model not found at {args.model1}, using random actions.")
        
    try:
        model2 = PPO.load(args.model2)
        print(f"Team 2 Model Loaded: {args.model2}")
    except:
        print(f"Team 2 Model not found at {args.model2}, using random actions.")

    env.opponent_policy = model2
    env.training_team1 = True
    obs, _ = env.reset()
    
    start_time = time.time()
    print(f"Simulating match for {args.steps} steps...")
    
    try:
        for i in range(args.steps):
            # Determine action
            if model1:
                action, _ = model1.predict(obs, deterministic=True)
            else:
                action = env.action_space.sample()

            old_score = list(env.env.score)
            obs, reward, terminated, truncated, _ = env.step(action)

            # Trigger native rendering
            if render_mode == "human":
                env.render()

            # Logging for debug mode or goals
            if args.debug and (i % 200 == 0 or env.env.score != old_score):
                elapsed = time.time() - start_time
                ball_pos = env.env.ball.pos
                print(f"Step {i:4} | Score: {env.env.score} | Ball: [{ball_pos[0]:.2f}, {ball_pos[1]:.2f}] | FPS: {i/(elapsed+0.001):.1f}")

            if terminated or truncated:
                print(f"Match ended at step {i}")
                break
    except KeyboardInterrupt:
        print("\nMatch interrupted by user.")
    finally:
        env.close()

    print(f"Final Score: {env.env.score}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FootyZero Match Runner")
    parser.add_argument("--steps", type=int, default=2500, help="Maximum steps to simulate.")
    parser.add_argument("--model1", type=str, default="ppo_footy_team1", help="Path to Team 1 model.")
    parser.add_argument("--model2", type=str, default="ppo_footy_team2", help="Path to Team 2 model.")
    parser.add_argument("--debug", action="store_true", help="Enable high-speed headless mode with console logging.")
    
    args = parser.parse_args()
    run_match(args)
