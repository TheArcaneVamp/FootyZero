import json
from footy_env_rl import FootyGymEnv
from stable_baselines3 import PPO
import numpy as np

from visualization_utils import get_replay_html

def visualize_multi_agent():
    env = FootyGymEnv()
    
    try:
        model1 = PPO.load("fresh_team1")
        model2 = PPO.load("fresh_team2")
        print("Fresh models loaded successfully.")
    except:
        print("Fresh models not found, attempting to load default models...")
        try:
            model1 = PPO.load("ppo_footy_team1")
            model2 = PPO.load("ppo_footy_team2")
            print("Default models loaded successfully.")
        except:
            print("No models found, using random actions.")
            model1, model2 = None, None
    
    # We use a single env.step(action) where the env handles the opponent internally
    env.opponent_policy = model2
    env.training_team1 = True
    
    obs, _ = env.reset()
    history = []
    
    for i in range(500):
        if model1:
            action1, _ = model1.predict(obs, deterministic=True)
        else:
            action1 = env.action_space.sample()

        obs, reward, terminated, truncated, _ = env.step(action1)

        frame = {
            "step": i,
            "ball": [float(x) for x in env.env.ball.pos],
            "team1": [[float(x) for x in p.pos] for p in env.env.team1],
            "team2": [[float(x) for x in p.pos] for p in env.env.team2],
            "score": [int(x) for x in env.env.score]
        }
        history.append(frame)
        if terminated or truncated: break

    html_content = get_replay_html(history, title="FootyZero Multi-Agent Replay")
    with open("multi_agent_replay.html", "w") as f:
        f.write(html_content)
    print("Multi-agent replay generated: multi_agent_replay.html")

if __name__ == "__main__":
    visualize_multi_agent()
