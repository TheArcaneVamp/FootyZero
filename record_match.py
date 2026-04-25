import json
from footy_env_rl import FootyGymEnv
from stable_baselines3 import PPO
import numpy as np

from visualization_utils import get_broadcast_html

def record_and_embed_match():
    env = FootyGymEnv()
    try:
        model1 = PPO.load("fresh_team1")
        model2 = PPO.load("fresh_team2")
        print("Fresh models loaded successfully.")
    except Exception:
        try:
            model1 = PPO.load("ppo_footy_team1")
            model2 = PPO.load("ppo_footy_team2")
            print("Default models loaded successfully.")
        except Exception:
            print("No models found. Using random actions.")
            model1, model2 = None, None
    
    env.opponent_policy = model2
    env.training_team1 = True
    obs, _ = env.reset()
    history = []
    
    print("Simulating high-fidelity match...")
    for i in range(2500): # Allow up to 2500 steps, but stop on terminated
        if model1:
            action, _ = model1.predict(obs, deterministic=True)
        else:
            action = env.action_space.sample()
            
        # Record state BEFORE step to capture the "goal" frame
        history.append({
            "ball": [float(x) for x in env.env.ball.pos],
            "team1": [[float(x) for x in p.pos] for p in env.env.team1],
            "team2": [[float(x) for x in p.pos] for p in env.env.team2],
            "score": [int(x) for x in env.env.score],
            "possession": int(env.env.possession)
        })

        obs, reward, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            # Record final frame
            history.append({
                "ball": [float(x) for x in env.env.ball.pos],
                "team1": [[float(x) for x in p.pos] for p in env.env.team1],
                "team2": [[float(x) for x in p.pos] for p in env.env.team2],
                "score": [int(x) for x in env.env.score],
                "possession": int(env.env.possession)
            })
            break

    html_template = get_broadcast_html(history)
    with open("broadcast.html", "w") as f:
        f.write(html_template)
    print("Premiere Broadcast generated: broadcast.html")

if __name__ == "__main__":
    record_and_embed_match()
