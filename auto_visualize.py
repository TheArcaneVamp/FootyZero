import os
import time
import subprocess

def auto_update():
    print("Auto-Visualizer started. Monitoring for model updates...")
    last_update = 0
    
    while True:
        # Check if new models were saved in root
        model_exists = os.path.exists("/home/dodo/ppo_footy_team1.zip")
        
        if model_exists:
            current_mtime = os.path.getmtime("/home/dodo/ppo_footy_team1.zip")
            if current_mtime > last_update:
                print(f"[{time.strftime('%H:%M:%S')}] New models found! Updating replay...")
                
                # Move models
                subprocess.run("mv /home/dodo/ppo_footy_team*.zip /home/dodo/projects/FootyZero/", shell=True)
                
                # Run visualizer
                subprocess.run("/home/dodo/projects/FootyZero/venv/bin/python3 /home/dodo/projects/FootyZero/visualize_ppo.py", shell=True, cwd="/home/dodo/projects/FootyZero")
                
                last_update = current_mtime
                print("Replay updated. Refresh your browser.")
        
        time.sleep(10)

if __name__ == "__main__":
    auto_update()
