from gymnasium.utils.env_checker import check_env
from footy_env_rl import FootyGymEnv

def verify():
    env = FootyGymEnv()
    print("Checking environment...")
    check_env(env)
    print("Environment check passed!")

if __name__ == "__main__":
    verify()
