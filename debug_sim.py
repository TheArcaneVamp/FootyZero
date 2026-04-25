import numpy as np
import math
import time
from footy_env_rl import FootyGymEnv
from stable_baselines3 import PPO

def debug_sim():
    print("Initializing FootyGymEnv for 2000-step debug...")
    env = FootyGymEnv()
    
    try:
        model1 = PPO.load("fresh_team1")
        model2 = PPO.load("fresh_team2")
        print("Fresh models loaded successfully.")
    except Exception:
        print("Using random actions for debug.")
        model1, model2 = None, None
        
    env.opponent_policy = model2
    env.training_team1 = True
    obs, _ = env.reset()
    
    start_time = time.time()
    for i in range(1, 2001):
        if model1:
            action, _ = model1.predict(obs, deterministic=True)
        else:
            action = env.action_space.sample()
            
        try:
            obs, reward, terminated, truncated, info = env.step(action)
        except Exception as e:
            print(f"\nCRASH at step {i}: {e}")
            import traceback
            traceback.print_exc()
            break
            
        # Check for invalid values
        ball_pos = env.env.ball.pos
        if any(math.isnan(x) for x in ball_pos) or any(math.isinf(x) for x in ball_pos):
            print(f"\nINVALID BALL POSITION at step {i}: {ball_pos}")
            break
            
        for p_idx, p in enumerate(env.env.team1 + env.env.team2):
            if any(math.isnan(x) for x in p.pos) or any(math.isinf(x) for x in p.pos):
                print(f"\nINVALID PLAYER {p_idx} POSITION at step {i}: {p.pos}")
                break
        else:
            if i % 200 == 0:
                elapsed = time.time() - start_time
                print(f"Step {i:4} | Score: {env.env.score} | Ball: [{ball_pos[0]:.2f}, {ball_pos[1]:.2f}] | FPS: {i/elapsed:.1f}")
            
            if terminated or truncated:
                print(f"\nMatch terminated at step {i}")
                break
    else:
        print("\nSimulation reached 2000 steps without crashing.")
    
    print(f"Final Score: {env.env.score}")

if __name__ == "__main__":
    debug_sim()
