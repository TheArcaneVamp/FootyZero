import math, random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict
from Player import Player
from Ball import Ball
from config import (
    PITCH_WIDTH, PITCH_LENGTH, GOAL_WIDTH_START, GOAL_WIDTH_END, GOAL_CENTER, BALL_RANGE
)

@dataclass
class GameState:
    score: List[int]
    ball_pos: List[float]
    ball_vector: Tuple[float, float]
    team1_pos: List[List[float]]
    team2_pos: List[List[float]]
    possession: int
    time: int

class FootballEnv:
    def __init__(self, team1: List[Player], team2: List[Player]):
        self.pitch_length = PITCH_LENGTH
        self.pitch_width = PITCH_WIDTH
        self.reset(team1, team2)

    def get_state(self) -> GameState:
        return GameState(
            score=list(self.score),
            ball_pos=list(self.ball.pos),
            ball_vector=self.ball.vector,
            team1_pos=[list(p.pos) for p in self.team1],
            team2_pos=[list(p.pos) for p in self.team2],
            possession=self.possession,
            time=self.time
        )

    def reset(self, team1: List[Player], team2: List[Player]):
        self.score = [0, 0]
        self.ball = Ball([PITCH_WIDTH / 2, PITCH_LENGTH / 2], (0, 0), None)
        self.team1 = team1
        self.team2 = team2
        self.time = 0
        self.half = 1 
        self.possession = 0
        
        # Explicitly clamp player coordinates
        for p in self.team1 + self.team2:
            p.pos[0] = max(0, min(PITCH_WIDTH, p.pos[0]))
            p.pos[1] = max(0, min(PITCH_LENGTH, p.pos[1]))

    def step(self, team1_actions: List[Tuple[str, Any]], team2_actions: List[Tuple[str, Any]]):
        # 0. Tick cooldowns
        for player in self.team1 + self.team2:
            player.tick()

        # 1. Reset 'is_pressed' status
        for player in self.team1 + self.team2:
            player.is_pressed = False

        # 2. Resolve all PRESS actions first
        for i, (action, params) in enumerate(team1_actions):
            if action == 'PRESS':
                self.team1[i].Press(params)
        
        for i, (action, params) in enumerate(team2_actions):
            if action == 'PRESS':
                self.team2[i].Press(params)

        # 3. Resolve other actions (MOVE, PASS, SHOOT, TACKLE)
        # Alternate team order based on time to remove bias while remaining deterministic
        if self.time % 2 == 0:
            order = [(self.team1, team1_actions, 1), (self.team2, team2_actions, 2)]
        else:
            order = [(self.team2, team2_actions, 2), (self.team1, team1_actions, 1)]

        for players, actions, team_id in order:
            for i, (action, params) in enumerate(actions):
                player = players[i]
                if action == 'MOVE':
                    player.Move(params)
                elif action == 'PASS':
                    player.Pass(params, self.ball)
                    self.ball.last_touch_team = team_id
                elif action == 'SHOOT':
                    # Team 1 shoots towards y=114 (side 0), Team 2 towards y=0 (side 1)
                    player.Shoot(self.ball, 0 if team_id == 1 else 1)
                    self.ball.last_touch_team = team_id
                elif action == 'TACKLE':
                    if player.Tackle(params, self.ball):
                        self.ball.last_touch_team = team_id

        # 4. Move the ball
        self.ball.Move()

        # 5. Loose Ball Retrieval
        if self.ball.possessor is None:
            # Use time-based deterministic ordering to remove team bias while remaining Gymnasium-compliant
            all_players = [(p, 1 if p in self.team1 else 2) for p in self.team1 + self.team2]
            # Deterministic rotation based on time
            shift = self.time % len(all_players)
            rotated_players = all_players[shift:] + all_players[:shift]
            
            for player, team_id in rotated_players:
                if self.ball.in_range(player):
                    self.ball.possessor = player
                    self.ball.last_touch_team = team_id
                    break

        # 6. Check for Goals, Saves, Posts, and OUT OF PLAY
        ball_x, ball_y = self.ball.pos
        
        # 6a. Out of play
        out_of_bounds = False
        if ball_x <= 0 or ball_x >= PITCH_WIDTH: out_of_bounds = True
        if (ball_y <= 0 or ball_y >= PITCH_LENGTH) and not (GOAL_WIDTH_START < ball_x < GOAL_WIDTH_END): 
            out_of_bounds = True
        
        if out_of_bounds:
            restart_team_id = 2 if self.ball.last_touch_team == 1 else 1
            restart_team = self.team1 if restart_team_id == 1 else self.team2
            
            self.ball.vector = (0, 0)
            self.ball.possessor = restart_team[1] 
            
            safe_x = max(2, min(PITCH_WIDTH - 2, ball_x))
            safe_y = max(2, min(PITCH_LENGTH - 2, ball_y))
            self.ball.possessor.pos = [safe_x, safe_y]
            self.ball.pos = [safe_x, safe_y]
            self.possession = restart_team_id
            
            # PUSH OTHERS AWAY and clamp
            for p in self.team1 + self.team2:
                if p != self.ball.possessor:
                    dx, dy = p.pos[0] - safe_x, p.pos[1] - safe_y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 12:
                        scale = 12 / (dist + 0.1)
                        p.pos[0] = max(0, min(PITCH_WIDTH, safe_x + dx * scale))
                        p.pos[1] = max(0, min(PITCH_LENGTH, safe_y + dy * scale))

        # 6b. Goal Area Handling
        elif ball_y <= 0 or ball_y >= PITCH_LENGTH:
            # Goalposts
            if abs(ball_x - GOAL_WIDTH_START) < 0.5 or abs(ball_x - GOAL_WIDTH_END) < 0.5:
                dx, dy = self.ball.vector
                self.ball.vector = (dx * 0.5, -dy * 0.7)
                self.ball.pos[1] = 1 if ball_y <= 0 else PITCH_LENGTH - 1
            elif GOAL_WIDTH_START < ball_x < GOAL_WIDTH_END:
                # Team 1 scores at y=114, Team 2 at y=0
                scoring_team = 0 if ball_y >= PITCH_LENGTH else 1
                dist_from_center = abs(ball_x - GOAL_CENTER)
                save_prob = 0.4 * math.exp(-(dist_from_center**2) / (2 * 3**2))
                
                if random.random() > save_prob:
                    self.score[scoring_team] += 1
                    self.ball.pos = [PITCH_WIDTH / 2, PITCH_LENGTH / 2]
                    self.ball.vector = (0, 0)
                    self.ball.possessor = None
                else:
                    # Save logic: target_team is the team that WAS NOT scoring (the defender)
                    # if ball_y >= PITCH_LENGTH, Team 1 was scoring, Team 2 is defending
                    defending_team = 1 if ball_y >= PITCH_LENGTH else 0
                    self.ball.vector = (random.uniform(-2, 2), -5 if defending_team == 1 else 5)
                    self.ball.possessor = None
            else:
                self.ball.vector = (0, 0)

        # 7. Update environment state
        self.time += 1
        if self.ball.possessor in self.team1:
            self.possession = 1
        elif self.ball.possessor in self.team2:
            self.possession = 2
        else:
            self.possession = 0

        return self.score, self.ball.pos, self.possession
