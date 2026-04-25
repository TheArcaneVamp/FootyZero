import random, math
from typing import Tuple, List, Optional, Dict
from config import (
    PITCH_WIDTH, PITCH_LENGTH, KICK_POWER, 
    TACKLE_RANGE, POSSESSION_STICKY_FRAMES, TACKLE_COOLDOWN_FRAMES,
    PASS_NOISE_SCALE, SHOT_NOISE_SCALE, SHOT_TARGET_VARIANCE,
    GOAL_CENTER
)

class Player:
    ROLE_STATS: Dict[str, Dict[str, int]] = {
        'F': {'attack': 6, 'pace': 3, 'passing': 4, 'defence':3}, 
        'M': {'attack': 4, 'pace': 2, 'passing': 6, 'defence':4}, 
        'D': {'attack': 3, 'pace': 2, 'passing': 4, 'defence':7}
    }
    
    def __init__(self, pos: List[float], role: str):
        self.pos = pos
        self.role = role
        self.attack = self.ROLE_STATS[role]['attack']
        self.pace = self.ROLE_STATS[role]['pace']
        self.defence = self.ROLE_STATS[role]['defence']
        self.passing = self.ROLE_STATS[role]['passing']
        self.is_pressed = False
        self.tackle_cooldown = 0
        self.possession_frames = 0

    def tick(self) -> None:
        if self.tackle_cooldown > 0:
            self.tackle_cooldown -= 1
        if self.possession_frames > 0:
            self.possession_frames -= 1

    def Move(self, direction: Tuple[float, float]) -> List[float]:
        dx, dy = direction
        magnitude = math.sqrt(dx**2 + dy**2)
        
        if magnitude > 0:
            # If target is closer than pace, just move to target
            if magnitude < self.pace:
                step_x = dx
                step_y = dy
            else:
                # Normalize and move by pace
                step_x = (dx / magnitude) * self.pace
                step_y = (dy / magnitude) * self.pace
            
            new_pos_x = self.pos[0] + step_x
            new_pos_y = self.pos[1] + step_y
            
            # Clamp to pitch boundaries
            self.pos[0] = max(0, min(PITCH_WIDTH, new_pos_x))
            self.pos[1] = max(0, min(PITCH_LENGTH, new_pos_y))
            
        return self.pos

    def Pass(self, target: Tuple[float, float], ball: 'Ball') -> None:
        effective_passing = self.passing - (2 if self.is_pressed else 0)
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]
        
        noise = (10 - effective_passing) * PASS_NOISE_SCALE
        dx += random.gauss(0, noise)
        dy += random.gauss(0, noise)
        
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude > 0 and ball.possessor == self:
            # Normalize and multiply by kick power
            ball.vector = ((dx / magnitude) * KICK_POWER, (dy / magnitude) * KICK_POWER)
            ball.possessor = None

    def Shoot(self, ball: 'Ball', side: int) -> None:
        effective_shooting = self.attack - (2 if self.is_pressed else 0)
        target_x = random.gauss(GOAL_CENTER, SHOT_TARGET_VARIANCE)
        # Side 0: shoots towards y=114, Side 1: shoots towards y=0
        target_y = 114 if side == 0 else 0
        
        noise = (10 - effective_shooting) * SHOT_NOISE_SCALE
        dx = target_x - self.pos[0]
        dy = target_y - self.pos[1]
        dx += random.gauss(0, noise)
        dy += random.gauss(0, noise)
        
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude > 0 and (ball.possessor == self or ball.in_range(self)):
            # Normalize and multiply by kick power
            ball.vector = ((dx / magnitude) * KICK_POWER, (dy / magnitude) * KICK_POWER)
            ball.possessor = None

    def Tackle(self, opponent: 'Player', ball: 'Ball') -> bool:
        if self.tackle_cooldown > 0 or opponent.possession_frames > 0:
            return False

        dx = opponent.pos[0] - self.pos[0]
        dy = opponent.pos[1] - self.pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Simplified: check range to opponent
        if distance <= TACKLE_RANGE and ball.possessor == opponent:
            success_prob = self.defence / (self.defence + opponent.attack)
            if random.random() < success_prob:
                ball.possessor = self
                self.possession_frames = POSSESSION_STICKY_FRAMES
                opponent.tackle_cooldown = TACKLE_COOLDOWN_FRAMES
                return True
        return False

    def Press(self, target: 'Player') -> None:
        dx = target.pos[0] - self.pos[0]
        dy = target.pos[1] - self.pos[1]

        self.Move((dx, dy))

        dx = target.pos[0] - self.pos[0]
        dy = target.pos[1] - self.pos[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance <= 6:
            target.is_pressed = True

from Ball import Ball
