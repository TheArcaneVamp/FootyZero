import math
from typing import Tuple, List, Optional
from config import PITCH_WIDTH, PITCH_LENGTH, FRICTION, BALL_RANGE

class Ball:
    def __init__(self, pos: List[float], vector: Tuple[float, float], possessor: Optional['Player']):
        self.pos = pos
        self.vector = vector
        self.possessor = possessor
        self.last_touch_team: Optional[int] = None # 1 or 2
    
    def Move(self) -> List[float]:
        if self.possessor:
            self.pos = list(self.possessor.pos)
            self.vector = (0, 0)
            return self.pos

        dx, dy = self.vector
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude < 0.1:
            self.vector = (0, 0)
            return self.pos
        
        # Move the ball by the full vector amount
        new_x = self.pos[0] + dx
        new_y = self.pos[1] + dy
        
        # Clamp to pitch boundaries and check for collision
        self.pos[0] = max(0, min(PITCH_WIDTH, new_x))
        self.pos[1] = max(0, min(PITCH_LENGTH, new_y))

        # Fix the bounce/rolling logic at the boundaries
        # If the ball hits side boundaries (x=0, x=PITCH_WIDTH)
        if self.pos[0] <= 0 or self.pos[0] >= PITCH_WIDTH:
            # Bounce it by inverting x component and applying friction
            self.vector = (-dx * FRICTION, dy * FRICTION)
        elif self.pos[1] <= 0 or self.pos[1] >= PITCH_LENGTH:
            # Let environment handle end-line logic (goals, corners)
            pass
        else:
            # Apply friction/decay to the vector
            self.vector = (dx * FRICTION, dy * FRICTION)
        
        return self.pos

    def in_range(self, player: 'Player') -> bool:
        px, py = player.pos
        bx, by = self.pos
        distance = math.sqrt((bx - px)**2 + (by - py)**2)
        return distance <= BALL_RANGE

from Player import Player
