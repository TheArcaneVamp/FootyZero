import random
from football_env import FootballEnv
from Player import Player

def run_test():
    # Initialize players for Team 1 (attacking Side 114)
    team1 = [
        Player([20, 30], 'D'),
        Player([37, 57], 'M'),
        Player([54, 30], 'F')
    ]

    # Initialize players for Team 2 (attacking Side 0)
    team2 = [
        Player([20, 84], 'D'),
        Player([37, 57], 'M'),
        Player([54, 84], 'F')
    ]

    env = FootballEnv(team1, team2)
    
    print("Starting Football Simulation Test with Chase AI...")
    print(f"Initial Score: {env.score}")

    for step in range(1, 301): # Increased steps to see more action
        t1_actions = []
        for p in team1:
            if env.ball.possessor == p:
                # If I have the ball, move toward the goal and shoot if close
                if p.pos[1] > 90:
                    t1_actions.append(('SHOOT', None))
                else:
                    t1_actions.append(('MOVE', (37 - p.pos[0], 114 - p.pos[1])))
            else:
                # If I don't have the ball, chase it and try to tackle
                dx, dy = env.ball.pos[0] - p.pos[0], env.ball.pos[1] - p.pos[1]
                if env.ball.in_range(p) and env.ball.possessor in team2:
                    t1_actions.append(('TACKLE', env.ball.possessor))
                elif env.ball.in_range(p) and env.ball.possessor is None:
                    env.ball.possessor = p # Simple pick-up
                    t1_actions.append(('MOVE', (dx, dy)))
                else:
                    t1_actions.append(('MOVE', (dx, dy)))

        t2_actions = []
        for p in team2:
            if env.ball.possessor == p:
                if p.pos[1] < 24:
                    t2_actions.append(('SHOOT', None))
                else:
                    t2_actions.append(('MOVE', (37 - p.pos[0], 0 - p.pos[1])))
            else:
                dx, dy = env.ball.pos[0] - p.pos[0], env.ball.pos[1] - p.pos[1]
                if env.ball.in_range(p) and env.ball.possessor in team1:
                    t2_actions.append(('TACKLE', env.ball.possessor))
                elif env.ball.in_range(p) and env.ball.possessor is None:
                    env.ball.possessor = p # Simple pick-up
                    t2_actions.append(('MOVE', (dx, dy)))
                else:
                    t2_actions.append(('MOVE', (dx, dy)))

        old_score = list(env.score)
        score, ball_pos, possession = env.step(t1_actions, t2_actions)

        # Log significant events
        if env.score != old_score:
            print(f"Step {step:3} | GOAL! Score: {score} | Possession: Team {possession}")
        elif step % 50 == 0:
            print(f"Step {step:3} | Score: {score} | Ball: [{ball_pos[0]:.1f}, {ball_pos[1]:.1f}] | Possession: Team {possession}")

    print("\nSimulation Finished.")
    print(f"Final Score: Team 1: {env.score[0]} | Team 2: {env.score[1]}")

if __name__ == "__main__":
    run_test()
