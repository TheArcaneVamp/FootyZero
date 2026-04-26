import pygame
import math
from config import PITCH_WIDTH, PITCH_LENGTH, GOAL_WIDTH_START, GOAL_WIDTH_END

class FootyRenderer:
    def __init__(self, width=518, height=798):
        pygame.init()
        self.width = width
        self.height = height
        self.scale = width / PITCH_WIDTH
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("FootyZero Premiere")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 48, bold=True)
        
        # Colors
        self.COLOR_PITCH = (34, 139, 34)
        self.COLOR_PITCH_DARK = (30, 120, 30)
        self.COLOR_LINES = (255, 255, 255, 180)
        self.COLOR_BALL = (255, 255, 255)
        self.COLOR_TEAM1 = (255, 82, 82)
        self.COLOR_TEAM2 = (68, 138, 255)

    def draw_pitch(self):
        # Draw grass stripes
        stripe_h = self.height / 10
        for i in range(10):
            color = self.COLOR_PITCH if i % 2 == 0 else self.COLOR_PITCH_DARK
            pygame.draw.rect(self.screen, color, (0, i * stripe_h, self.width, stripe_h))
        
        # Draw boundary lines
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, self.width, self.height), 2)
        
        # Halfway line
        pygame.draw.line(self.screen, (255, 255, 255), (0, self.height/2), (self.width, self.height/2), 2)
        
        # Center circle
        pygame.draw.circle(self.screen, (255, 255, 255), (int(self.width/2), int(self.height/2)), int(9.15 * self.scale), 2)
        pygame.draw.circle(self.screen, (255, 255, 255), (int(self.width/2), int(self.height/2)), 3)

        # Goals
        pygame.draw.rect(self.screen, (255, 255, 255), (GOAL_WIDTH_START * self.scale, 0, (GOAL_WIDTH_END - GOAL_WIDTH_START) * self.scale, 10))
        pygame.draw.rect(self.screen, (255, 255, 255), (GOAL_WIDTH_START * self.scale, self.height - 10, (GOAL_WIDTH_END - GOAL_WIDTH_START) * self.scale, 10))

    def render(self, state, fps=12):
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

        self.screen.fill(self.COLOR_PITCH)
        self.draw_pitch()
        
        # Draw Team 1 (Red)
        for pos in state['team1_pos']:
            px, py = pos[0] * self.scale, pos[1] * self.scale
            pygame.draw.circle(self.screen, self.COLOR_TEAM1, (int(px), int(py)), int(1.5 * self.scale))
            pygame.draw.circle(self.screen, (0, 0, 0), (int(px), int(py)), int(1.5 * self.scale), 1)

        # Draw Team 2 (Blue)
        for pos in state['team2_pos']:
            px, py = pos[0] * self.scale, pos[1] * self.scale
            pygame.draw.circle(self.screen, self.COLOR_TEAM2, (int(px), int(py)), int(1.5 * self.scale))
            pygame.draw.circle(self.screen, (0, 0, 0), (int(px), int(py)), int(1.5 * self.scale), 1)

        # Draw Ball
        bx, by = state['ball_pos'][0] * self.scale, state['ball_pos'][1] * self.scale
        pygame.draw.circle(self.screen, self.COLOR_BALL, (int(bx), int(by)), int(0.8 * self.scale))
        pygame.draw.circle(self.screen, (0, 0, 0), (int(bx), int(by)), int(0.8 * self.scale), 1)
        
        # Possession Highlight
        if state['possession'] > 0:
            color = self.COLOR_TEAM1 if state['possession'] == 1 else self.COLOR_TEAM2
            pygame.draw.circle(self.screen, color, (int(bx), int(by)), int(1.8 * self.scale), 2)

        # Scoreboard
        score_text = f"{state['score'][0]} - {state['score'][1]}"
        score_surf = self.large_font.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 20))
        
        # Timer
        mins = state['time'] // 600
        secs = (state['time'] // 10) % 60
        timer_text = f"{mins:02d}:{secs:02d}"
        timer_surf = self.font.render(timer_text, True, (255, 215, 0))
        self.screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 80))

        pygame.display.flip()
        if fps > 0:
            self.clock.tick(fps)
        return True

    def close(self):
        pygame.quit()
