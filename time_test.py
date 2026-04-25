import time
from footy_env_rl import FootyGymEnv
import numpy as np

def time_match():
    env = FootyGymEnv()
    obs, _ = env.reset()
    
    start_time = time.time()
    
    steps = 500
    for _ in range(steps):
        # Sample random tactical actions
        action = env.action_space.sample()
        obs, reward, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            break
            
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Match (500 steps) completed in: {total_time:.4f} seconds")
    print(f"Steps per second: {steps / total_time:.2f}")

if __name__ == "__main__":
    time_match()
