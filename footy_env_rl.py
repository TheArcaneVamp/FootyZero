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
from dataclasses import asdict

from tactics import TacticalHeuristics

class FootyGymEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 12}

    def __init__(self, opponent_policy=None, render_mode=None, max_steps=None):
        super(FootyGymEnv, self).__init__()
        self.action_space = spaces.Box(low=-1, high=1, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-1, high=1, shape=(17,), dtype=np.float32)
        self.env = None
        self.max_steps = max_steps or TOTAL_STEPS
        self.half_time_steps = self.max_steps // 2
        self.current_step = 0
        self.opponent_policy = opponent_policy
        self.training_team1 = True 
        self.match_count = 0
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

        # Rendering
        self.render_mode = render_mode
        self.renderer = None

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
        
        if self.render_mode == "human":
            self.render()

        return self.get_observation(is_team1=self.training_team1), {}

    def _apply_kickoff(self, starting_team_id):
        # Preserve match time and half during kickoff resets
        curr_time = 0
        curr_half = 1
        if self.env is not None:
            curr_time = self.env.time
            curr_half = self.env.half

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
        
        # Restore state
        self.env.time = curr_time
        self.env.half = curr_half
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

    def step(self, action):
        if self.training_team1:
            t1_tactics = action
            if self.opponent_policy:
                obs2 = self.get_observation(is_team1=False)
                t2_tactics, _ = self.opponent_policy.predict(obs2, deterministic=True)
            else: t2_tactics = np.zeros(4)
        else:
            t2_tactics = action
            if self.opponent_policy:
                obs1 = self.get_observation(is_team1=True)
                t1_tactics, _ = self.opponent_policy.predict(obs1, deterministic=True)
            else: t1_tactics = np.zeros(4)

        # Tactical Smoothing
        t1_tactics = self.last_t1_tactics * self.smoothing + t1_tactics * (1 - self.smoothing)
        t2_tactics = self.last_t2_tactics * self.smoothing + t2_tactics * (1 - self.smoothing)
        self.last_t1_tactics, self.last_t2_tactics = t1_tactics, t2_tactics

        # Get heuristic actions from the TacticalHeuristics class
        t1_actions = TacticalHeuristics.get_actions(self.env.team1, self.env.team2, self.env.ball, t1_tactics, is_team1=True)
        t2_actions = TacticalHeuristics.get_actions(self.env.team2, self.env.team1, self.env.ball, t2_tactics, is_team1=False)
        
        old_score, old_possession = list(self.env.score), self.env.possession
        self.env.step(t1_actions, t2_actions)
        self.current_step += 1
        
        # 1. Handle Goals (Kickoffs)
        if old_score != self.env.score:
            kickoff_team = 2 if self.env.score[0] > old_score[0] else 1
            current_score = list(self.env.score)
            self._apply_kickoff(kickoff_team)
            self.env.score = current_score
            if self.current_step > self.half_time_steps: self.env.half = 2

        # 2. Handle Half-Time Transition
        if self.current_step == self.half_time_steps:
            second_half_starter = 2 if self.first_half_starter == 1 else 1
            current_score = list(self.env.score)
            self._apply_kickoff(second_half_starter)
            self.env.score = current_score
            self.env.half = 2
            
        ball_x, ball_y = self.env.ball.pos
        reward = 0
        
        if self.training_team1:
            # Goal Rewards
            reward += (self.env.score[0] - old_score[0]) * 50.0  # Goal scored by my team
            reward -= (self.env.score[1] - old_score[1]) * 50.0  # Goal conceded by my team (changed from 40 to 50)

            # Defensive Positioning Reward (when out of possession)
            if self.env.possession != 1: # If Team 1 does not have possession
                for p in self.env.team1:
                    # Reward for being between ball and own goal (y=0 for Team 1's goal)
                    if p.pos[1] < ball_y: # Player is behind the ball (closer to own goal)
                        reward += 0.01

            # Forward Progress Reward (when in possession)
            if self.env.possession == 1: # If Team 1 has possession
                # Reward for moving the ball further into opponent's half (y=114)
                reward += (ball_y / PITCH_LENGTH) * 0.1 # Max 0.1 reward when at opponent's goal line
        else: # training_team2
            # Goal Rewards
            reward += (self.env.score[1] - old_score[1]) * 50.0  # Goal scored by my team
            reward -= (self.env.score[0] - old_score[0]) * 50.0  # Goal conceded by my team

            # Defensive Positioning Reward (when out of possession)
            if self.env.possession != 2: # If Team 2 does not have possession
                for p in self.env.team2:
                    # Reward for being between ball and own goal (y=114 for Team 2's goal)
                    if p.pos[1] > ball_y: # Player is behind the ball (closer to own goal)
                        reward += 0.01

            # Forward Progress Reward (when in possession)
            if self.env.possession == 2: # If Team 2 has possession
                # Reward for moving the ball further into opponent's half (y=0)
                reward += (1.0 - (ball_y / PITCH_LENGTH)) * 0.1 # Max 0.1 reward when at opponent's goal line
        
        terminated = self.current_step >= self.max_steps
        return self.get_observation(is_team1=self.training_team1), reward, terminated, False, {}

    def render(self):
        if self.render_mode == "human":
            if self.renderer is None:
                from renderer import FootyRenderer
                self.renderer = FootyRenderer()
            
            state = asdict(self.env.get_state())
            state['match_count'] = self.match_count
            state['training_team'] = 1 if self.training_team1 else 2
            
            if not self.renderer.render(state, fps=self.metadata["render_fps"]):
                self.close()

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None
