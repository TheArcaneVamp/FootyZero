import math
import numpy as np
from config import TACKLE_RANGE, PITCH_WIDTH, PITCH_LENGTH

class TacticalHeuristics:
    @staticmethod
    def get_actions(team, opponents, ball, tactics, is_team1):
        depth, width, aggression, directness = tactics
        actions = []
        ball_pos = ball.pos
        
        # Identify the closest player to the ball to be the "chaser"
        dists = [math.sqrt((p.pos[0]-ball_pos[0])**2 + (p.pos[1]-ball_pos[1])**2) for p in team]
        chaser_idx = np.argmin(dists)
        
        for i, p in enumerate(team):
            # Base home positions based on role and depth
            if p.role == 'D': base_y = 25
            elif p.role == 'M': base_y = 57
            else: base_y = 89
            
            y_shift = depth * 25
            target_home_y = base_y + y_shift
            
            spacing = 15 + (width + 1) * 15 
            if i == 0: target_home_x = 37 - spacing
            elif i == 1: target_home_x = 37
            else: target_home_x = 37 + spacing
            
            # Ensure home positions stay on pitch with a margin
            world_home_y = np.clip(target_home_y if is_team1 else PITCH_LENGTH - target_home_y, 10, PITCH_LENGTH - 10)
            world_home_x = np.clip(target_home_x, 10, PITCH_WIDTH - 10)
            
            if ball.possessor == p:
                target_y = PITCH_LENGTH if is_team1 else 0
                dist_to_goal = abs(p.pos[1] - target_y)
                if dist_to_goal < 30: 
                    actions.append(('SHOOT', None))
                else:
                    # Carrier movement: decision between direct run or pass
                    if directness > (np.random.random() * 2 - 1.2): 
                        actions.append(('MOVE', (37 - p.pos[0], target_y - p.pos[1])))
                    else:
                        teammates = [t for t in team if t != p]
                        # Look for forward teammates
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
                # Defensive/Off-ball movement
                if i == chaser_idx:
                    if ball.possessor is None:
                        # If ball is loose, chaser must go exactly to the ball to prevent deadlocks
                        weight = 1.0
                    else:
                        # Chaser is more ball-focused
                        weight = np.clip(((aggression+1.0)/2.0)*0.4 + (max(0,1-(dists[i]/60.0)))*0.6, 0.5, 1.0)
                else: 
                    weight = 0.1 
                
                # Check for tackle - ONLY stop to tackle if it's actually possible
                can_tackle = (dists[i] <= TACKLE_RANGE and 
                             ball.possessor in opponents and 
                             p.tackle_cooldown == 0 and 
                             ball.possessor.possession_frames == 0)
                
                if can_tackle: 
                    actions.append(('TACKLE', ball.possessor))
                else:
                    # Target position interpolation between home and ball
                    tx = (1-weight)*world_home_x + weight*ball_pos[0]
                    ty = (1-weight)*world_home_y + weight*ball_pos[1]
                    
                    # Teammate repulsion (gentle separation)
                    repel_dx, repel_dy = 0, 0
                    if i != chaser_idx:
                        for j, other in enumerate(team):
                            if i != j:
                                dx, dy = p.pos[0]-other.pos[0], p.pos[1]-other.pos[1]
                                d = math.sqrt(dx**2 + dy**2)
                                if d < 12:
                                    strength = 3.0
                                    factor = strength / (d + 0.1)
                                    repel_dx += dx * factor
                                    repel_dy += dy * factor
                    
                    move_x = tx + repel_dx - p.pos[0]
                    move_y = ty + repel_dy - p.pos[1]
                    
                    # Normalize large movements
                    move_mag = math.sqrt(move_x**2 + move_y**2)
                    if move_mag > 30:
                        move_x = (move_x / move_mag) * 30
                        move_y = (move_y / move_mag) * 30

                    actions.append(('MOVE', (move_x, move_y)))
        return actions
