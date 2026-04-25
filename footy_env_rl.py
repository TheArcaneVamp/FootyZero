import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
import random
from football_env import FootballEnv
from Player import Player
from Ball import Ball
from config import (
    PITCH_WIDTH, PITCH_LENGTH, HALF_TIME_STEPS, TOTAL_STEPS,
    POS_T1_KICKOFF, POS_T2_DEFENDING, POS_T2_KICKOFF, POS_T1_DEFENDING
)
import json
import time
from dataclasses import asdict

class FootyGymEnv(gym.Env):
    def __init__(self, opponent_policy=None, export_live=False):
        super(FootyGymEnv, self).__init__()
        self.action_space = spaces.Box(low=-1, high=1, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-1, high=1, shape=(17,), dtype=np.float32)
        self.env = None
        self.max_steps = TOTAL_STEPS
        self.current_step = 0
        self.opponent_policy = opponent_policy
        self.training_team1 = True 
        self.match_count = 0
        self.export_live = export_live
        self.first_half_starter = 1 # 1 or 2
        
        # Statistics
        self.stats = {
            "team1_wins": 0, "team2_wins": 0, "draws": 0,
            "team1_goals": 0, "team2_goals": 0
        }
        
        # Tactical Smoothing (EMA)
        self.last_t1_tactics = np.zeros(4)
        self.last_t2_tactics = np.zeros(4)
        self.smoothing = 0.5 

        # Live Visualization Settings
        self.last_export_time = 0
        self.export_interval = 0.05

    def reset(self, seed=None, options=None):
        if self.env is not None:
            self.stats["team1_goals"] += self.env.score[0]
            self.stats["team2_goals"] += self.env.score[1]
            if self.env.score[0] > self.env.score[1]: self.stats["team1_wins"] += 1
            elif self.env.score[1] > self.env.score[0]: self.stats["team2_wins"] += 1
            else: self.stats["draws"] += 1

        super().reset(seed=seed)
        self.match_count += 1
        self.current_step = 0
        self.first_half_starter = 1 if random.random() < 0.5 else 2
        
        self._apply_kickoff(self.first_half_starter)
        
        self.last_t1_tactics = np.zeros(4)
        self.last_t2_tactics = np.zeros(4)
        return self.get_observation(is_team1=self.training_team1), {}

    def _apply_kickoff(self, starting_team_id):
        # Reset tactical smoothing to prevent biased drift across restarts
        self.last_t1_tactics = np.zeros(4)
        self.last_t2_tactics = np.zeros(4)
        
        if starting_team_id == 1:
            team1 = [Player(list(p), role) for p, role in zip(POS_T1_KICKOFF, ['D', 'M', 'F'])]
            team2 = [Player(list(p), role) for p, role in zip(POS_T2_DEFENDING, ['D', 'M', 'F'])]
            if self.env is None:
                self.env = FootballEnv(team1, team2)
            else:
                self.env.reset(team1, team2)
            self.env.ball.possessor = self.env.team1[1] 
            self.env.possession = 1
        else:
            team1 = [Player(list(p), role) for p, role in zip(POS_T1_DEFENDING, ['D', 'M', 'F'])]
            team2 = [Player(list(p), role) for p, role in zip(POS_T2_KICKOFF, ['D', 'M', 'F'])]
            if self.env is None:
                self.env = FootballEnv(team1, team2)
            else:
                self.env.reset(team1, team2)
            self.env.ball.possessor = self.env.team2[1]
            self.env.possession = 2
            
        self.env.ball.pos = list(self.env.ball.possessor.pos)
        self.env.ball.vector = (0, 0)

    def get_observation(self, is_team1):
        ball_pos = list(self.env.ball.pos)
        ball_vec = list(self.env.ball.vector)
        my_players = self.env.team1 if is_team1 else self.env.team2
        opp_players = self.env.team2 if is_team1 else self.env.team1
        
        half_width = PITCH_WIDTH / 2
        half_length = PITCH_LENGTH / 2

        if not is_team1:
            ball_pos[1] = PITCH_LENGTH - ball_pos[1]
            ball_vec[1] = -ball_vec[1]
        
        obs = [
            (ball_pos[0]/half_width)-1.0, 
            (ball_pos[1]/half_length)-1.0, 
            np.clip(ball_vec[0]/15.0,-1,1), 
            np.clip(ball_vec[1]/15.0,-1,1)
        ]
        
        for p in my_players:
            y = p.pos[1] if is_team1 else PITCH_LENGTH - p.pos[1]
            obs.extend([(p.pos[0]/half_width)-1.0, (y/half_length)-1.0])
        for p in opp_players:
            y = p.pos[1] if is_team1 else PITCH_LENGTH - p.pos[1]
            obs.extend([(p.pos[0]/half_width)-1.0, (y/half_length)-1.0])
            
        if self.env.possession == 0: pos_val = -1.0
        elif (is_team1 and self.env.possession == 1) or (not is_team1 and self.env.possession == 2): pos_val = 0.0
        else: pos_val = 1.0
        obs.append(pos_val)
        return np.array(obs, dtype=np.float32)

    def _export_live_state(self):
        if not self.export_live:
            return
            
        now = time.time()
        if now - self.last_export_time < self.export_interval: return
        self.last_export_time = now
        
        game_state = self.env.get_state()
        state = {
            "match": self.match_count,
            "training_team": 1 if self.training_team1 else 2,
            "stats": self.stats,
            **asdict(game_state)
        }
        try:
            with open("/home/dodo/projects/FootyZero/live_state.json", "w") as f:
                json.dump(state, f)
        except: pass

    def step(self, action):
        if self.training_team1:
            t1_action = action
            if self.opponent_policy:
                obs2 = self.get_observation(is_team1=False)
                t2_action, _ = self.opponent_policy.predict(obs2, deterministic=True)
            else: t2_action = np.zeros(4)
        else:
            t2_action = action
            if self.opponent_policy:
                obs1 = self.get_observation(is_team1=True)
                t1_action, _ = self.opponent_policy.predict(obs1, deterministic=True)
            else: t1_action = np.zeros(4)

        # Tactical Smoothing
        t1_action = self.last_t1_tactics * self.smoothing + t1_action * (1 - self.smoothing)
        t2_action = self.last_t2_tactics * self.smoothing + t2_action * (1 - self.smoothing)
        self.last_t1_tactics, self.last_t2_tactics = t1_action, t2_action

        t1_moves = self._get_heuristic_actions(self.env.team1, self.env.team2, t1_action, is_team1=True)
        t2_moves = self._get_heuristic_actions(self.env.team2, self.env.team1, t2_action, is_team1=False)
        
        old_score, old_possession = list(self.env.score), self.env.possession
        self.env.step(t1_moves, t2_moves)
        self.current_step += 1
        
        # 1. Handle Goals (Kickoffs)
        if old_score != self.env.score:
            # If team 1 scored (score[0] increased), team 2 kicks off
            kickoff_team = 2 if self.env.score[0] > old_score[0] else 1
            current_score = list(self.env.score)
            self._apply_kickoff(kickoff_team)
            self.env.score = current_score
            # Ensure the half stays consistent during post-goal reset
            if self.current_step > HALF_TIME_STEPS: self.env.half = 2

        # 2. Handle Half-Time Transition
        if self.current_step == HALF_TIME_STEPS:
            second_half_starter = 2 if self.first_half_starter == 1 else 1
            current_score = list(self.env.score)
            self._apply_kickoff(second_half_starter)
            self.env.score = current_score
            self.env.half = 2
            
        self._export_live_state()
        
        ball_x, ball_y = self.env.ball.pos
        if self.training_team1:
            dist_to_goal = math.sqrt((ball_x - 37)**2 + (ball_y - 114)**2)
            reward = (self.env.score[0] - old_score[0]) * 50.0 - (self.env.score[1] - old_score[1]) * 40.0
            reward += (1.0 - min(1.0, dist_to_goal / 120.0)) * 0.5
            if old_possession != 1 and self.env.possession == 1: reward += 0.2
            if self.env.possession == 1: 
                reward += 0.01 # Very small reward for holding ball
                if ball_x < 5 or ball_x > 69: reward -= 0.01
        else:
            dist_to_goal = math.sqrt((ball_x - 37)**2 + (ball_y - 0)**2)
            reward = (self.env.score[1] - old_score[1]) * 50.0 - (self.env.score[0] - old_score[0]) * 40.0
            reward += (1.0 - min(1.0, dist_to_goal / 120.0)) * 0.5
            if old_possession != 2 and self.env.possession == 2: reward += 0.2
            if self.env.possession == 2: 
                reward += 0.01
                if ball_x < 5 or ball_x > 69: reward -= 0.01
        
        terminated = self.current_step >= self.max_steps
        return self.get_observation(is_team1=self.training_team1), reward, terminated, False, {}

    def _get_heuristic_actions(self, team, opponents, tactics, is_team1):
        depth, width, aggression, directness = tactics
        actions = []
        ball_pos = self.env.ball.pos
        dists = [math.sqrt((p.pos[0]-ball_pos[0])**2 + (p.pos[1]-ball_pos[1])**2) for p in team]
        chaser_idx = np.argmin(dists)
        
        from config import TACKLE_RANGE
        
        for i, p in enumerate(team):
            if p.role == 'D': base_y = 25
            elif p.role == 'M': base_y = 57
            else: base_y = 89
            
            y_shift = depth * 25
            target_home_y = base_y + y_shift
            
            spacing = 15 + (width + 1) * 15 
            if i == 0: target_home_x = 37 - spacing
            elif i == 1: target_home_x = 37
            else: target_home_x = 37 + spacing
            
            world_home_y = target_home_y if is_team1 else PITCH_LENGTH - target_home_y
            world_home_x = np.clip(target_home_x, 5, PITCH_WIDTH - 5)
            
            if self.env.ball.possessor == p:
                target_y = PITCH_LENGTH if is_team1 else 0
                dist_to_goal = abs(p.pos[1] - target_y)
                if dist_to_goal < 30: 
                    actions.append(('SHOOT', None))
                else:
                    # Direct move vs pass logic
                    if directness > (random.random() * 2 - 1.2): 
                        actions.append(('MOVE', (37 - p.pos[0], target_y - p.pos[1])))
                    else:
                        teammates = [t for t in team if t != p]
                        best_tm = None
                        for tm in teammates:
                            if (is_team1 and tm.pos[1] > p.pos[1]) or (not is_team1 and tm.pos[1] < p.pos[1]):
                                best_tm = tm
                                break
                        if best_tm: 
                            actions.append(('PASS', best_tm.pos))
                        else: 
                            actions.append(('MOVE', (37 - p.pos[0], target_y - p.pos[1])))
            else:
                # Calculate movement vector
                if i == chaser_idx:
                    # Chaser is more aggressive
                    weight = np.clip(((aggression+1.0)/2.0)*0.4 + (max(0,1-(dists[i]/40.0)))*0.6, 0.3, 1.0)
                else: 
                    weight = 0.1 
                
                # Check for tackle
                if dists[i] <= TACKLE_RANGE and self.env.ball.possessor in opponents: 
                    actions.append(('TACKLE', self.env.ball.possessor))
                else:
                    # Target position
                    tx = (1-weight)*world_home_x + weight*ball_pos[0]
                    ty = (1-weight)*world_home_y + weight*ball_pos[1]
                    
                    # Apply gentle repel from teammates
                    repel_dx, repel_dy = 0, 0
                    for j, other in enumerate(team):
                        if i != j:
                            dx, dy = p.pos[0]-other.pos[0], p.pos[1]-other.pos[1]
                            d = math.sqrt(dx**2 + dy**2)
                            if d < 10:
                                # Chaser is less affected by repel to ensure ball retrieval
                                strength = 1.5 if i == chaser_idx else 3.0
                                factor = strength / (d + 0.5)
                                repel_dx += dx * factor
                                repel_dy += dy * factor
                    
                    # Cap the total movement vector to prevent "teleportation" jitter
                    move_x = tx + repel_dx - p.pos[0]
                    move_y = ty + repel_dy - p.pos[1]
                    
                    # Ensure moves aren't extreme
                    move_mag = math.sqrt(move_x**2 + move_y**2)
                    if move_mag > 30:
                        move_x = (move_x / move_mag) * 30
                        move_y = (move_y / move_mag) * 30

                    actions.append(('MOVE', (move_x, move_y)))
        return actions
