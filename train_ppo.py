import argparse
from stable_baselines3 import PPO
from footy_env_rl import FootyGymEnv
import numpy as np

def train_self_play(args):
    # Initialize the environment
    env = FootyGymEnv(export_live=args.export_live)
    
    # Initialize two agents (Load if exists, otherwise create new)
    try:
        model1 = PPO.load(args.save_path_t1, env=env)
        print(f"Loaded existing model for Team 1 from {args.save_path_t1}")
    except:
        model1 = PPO("MlpPolicy", env, verbose=0, learning_rate=3e-4)
        print("Starting training for Team 1 from scratch...")
        
    try:
        model2 = PPO.load(args.save_path_t2, env=env)
        print(f"Loaded existing model for Team 2 from {args.save_path_t2}")
    except:
        model2 = PPO("MlpPolicy", env, verbose=0, learning_rate=3e-4)
        print("Starting training for Team 2 from scratch...")
    
    total_rounds = args.epochs
    timesteps_per_round = args.timesteps
    
    print(f"Starting Self-Play Training: {total_rounds} rounds of {timesteps_per_round} timesteps each per team.")
    
    for r in range(total_rounds):
        # Round A: Team 1 learns to beat Team 2
        print(f"Round {r+1}/{total_rounds} - Team 1 Training...")
        env.training_team1 = True
        env.opponent_policy = model2
        model1.learn(total_timesteps=timesteps_per_round, reset_num_timesteps=False)
        
        # Round B: Team 2 learns to beat Team 1
        print(f"Round {r+1}/{total_rounds} - Team 2 Training...")
        env.training_team1 = False
        env.opponent_policy = model1
        model2.learn(total_timesteps=timesteps_per_round, reset_num_timesteps=False)
        
        if (r + 1) % args.save_freq == 0:
            print(f"Saving models at round {r+1}...")
            model1.save(args.save_path_t1)
            model2.save(args.save_path_t2)

    print("Training finished. Saving final models...")
    model1.save(args.save_path_t1)
    model2.save(args.save_path_t2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FootyZero agents using self-play PPO.")
    parser.add_argument("--epochs", type=int, default=25, help="Total number of self-play rounds.")
    parser.add_argument("--timesteps", type=int, default=200000, help="Timesteps per round for each team.")
    parser.add_argument("--save_path_t1", type=str, default="ppo_footy_team1", help="Path to save/load Team 1 model.")
    parser.add_argument("--save_path_t2", type=str, default="ppo_footy_team2", help="Path to save/load Team 2 model.")
    parser.add_argument("--save_freq", type=int, default=10, help="Frequency of saving models (in rounds).")
    parser.add_argument("--export_live", action="store_true", help="Whether to export live state for visualization.")
    
    args = parser.parse_args()
    train_self_play(args)
