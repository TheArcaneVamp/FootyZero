import json
from football_env import FootballEnv
from Player import Player
import random

def run_sim_and_save_json():
    # Setup teams
    team1 = [Player([20, 30], 'D'), Player([37, 57], 'M'), Player([54, 30], 'F')]
    team2 = [Player([20, 84], 'D'), Player([37, 57], 'M'), Player([54, 84], 'F')]
    env = FootballEnv(team1, team2)

    history = []
    
    for _ in range(300):
        t1_actions = []
        for p in team1:
            if env.ball.possessor == p:
                if p.pos[1] > 90:
                    t1_actions.append(('SHOOT', None))
                else:
                    t1_actions.append(('MOVE', (37 - p.pos[0], 114 - p.pos[1])))
            else:
                dx, dy = env.ball.pos[0] - p.pos[0], env.ball.pos[1] - p.pos[1]
                if env.ball.in_range(p) and env.ball.possessor in team2:
                    t1_actions.append(('TACKLE', env.ball.possessor))
                elif env.ball.in_range(p) and env.ball.possessor is None:
                    env.ball.possessor = p
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
                    env.ball.possessor = p
                    t2_actions.append(('MOVE', (dx, dy)))
                else:
                    t2_actions.append(('MOVE', (dx, dy)))

        env.step(t1_actions, t2_actions)
        
        # Save frame data
        frame = {
            "ball": list(env.ball.pos),
            "team1": [list(p.pos) for p in team1],
            "team2": [list(p.pos) for p in team2],
            "score": list(env.score)
        }
        history.append(frame)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>FootyZero Replay</title>
        <style>
            body {{ background: #222; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; }}
            canvas {{ background: #2e7d32; border: 5px solid #fff; border-radius: 5px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
            .stats {{ margin: 20px; font-size: 24px; }}
        </style>
    </head>
    <body>
        <div class="stats">Team Red <span id="s1">0</span> - <span id="s2">0</span> Team Blue</div>
        <canvas id="pitch" width="370" height="570"></canvas>
        <p>Step: <span id="step">0</span></p>

        <script>
            const data = {json.dumps(history)};
            const canvas = document.getElementById('pitch');
            const ctx = canvas.getContext('2d');
            let frame = 0;

            function draw() {{
                if (frame >= data.length) frame = 0;
                const state = data[frame];
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.strokeStyle = "rgba(255,255,255,0.5)";
                ctx.strokeRect(0, 0, canvas.width, canvas.height);
                ctx.beginPath();
                ctx.moveTo(0, canvas.height/2); ctx.lineTo(canvas.width, canvas.height/2);
                ctx.stroke();

                // Draw Goals
                ctx.strokeStyle = "white";
                ctx.lineWidth = 2;
                ctx.strokeRect(32*5, 0, 10*5, 10);
                ctx.strokeRect(32*5, canvas.height-10, 10*5, 10);

                // Draw Team 1 (Red)
                ctx.fillStyle = "#ff5252";
                state.team1.forEach(p => {{
                    ctx.beginPath(); ctx.arc(p[0]*5, p[1]*5, 8, 0, Math.PI*2); ctx.fill();
                }});

                // Draw Team 2 (Blue)
                ctx.fillStyle = "#448aff";
                state.team2.forEach(p => {{
                    ctx.beginPath(); ctx.arc(p[0]*5, p[1]*5, 8, 0, Math.PI*2); ctx.fill();
                }});

                // Draw Ball
                ctx.fillStyle = "white";
                ctx.beginPath(); ctx.arc(state.ball[0]*5, state.ball[1]*5, 4, 0, Math.PI*2); ctx.fill();
                ctx.strokeStyle = "black"; ctx.lineWidth = 1; ctx.stroke();

                document.getElementById('s1').innerText = state.score[0];
                document.getElementById('s2').innerText = state.score[1];
                document.getElementById('step').innerText = frame;

                frame++;
                setTimeout(() => requestAnimationFrame(draw), 50);
            }}
            draw();
        </script>
    </body>
    </html>
    """
    with open("replay.html", "w") as f:
        f.write(html_content)
    print("Replay updated: replay.html")

if __name__ == "__main__":
    run_sim_and_save_json()
