import json

def get_replay_html(history, title="FootyZero Replay"):
    data_json = json.dumps(history)
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ background: #1a1a1a; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; flex-direction: column; align-items: center; margin: 0; padding: 20px; }}
        .header {{ display: flex; justify-content: space-between; width: 500px; margin-bottom: 10px; }}
        .score-board {{ background: #333; padding: 10px 20px; border-radius: 8px; font-size: 28px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
        .team-a {{ color: #ff5252; }}
        .team-b {{ color: #448aff; }}
        canvas {{ background: #2e7d32; border: 4px solid #fff; border-radius: 4px; box-shadow: 0 0 30px rgba(0,0,0,0.5); }}
        .controls {{ margin-top: 15px; color: #aaa; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="score-board"><span class="team-a">Agent A</span> <span id="s1">0</span> - <span id="s2">0</span> <span class="team-b">Agent B</span></div>
    </div>
    <canvas id="pitch" width="370" height="570"></canvas>
    <div class="controls">Step: <span id="step">0</span> / {len(history)} | Replay Mode</div>

    <script>
        const data = {data_json};
        const canvas = document.getElementById('pitch');
        const ctx = canvas.getContext('2d');
        let frameIdx = 0;

        function draw() {{
            if (frameIdx >= data.length) frameIdx = 0;
            const state = data[frameIdx];
            
            // Draw Pitch
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = "rgba(255,255,255,0.4)";
            ctx.lineWidth = 2;
            ctx.strokeRect(0, 0, canvas.width, canvas.height);
            
            // Halfway Line & Center Circle
            ctx.beginPath(); ctx.moveTo(0, 285); ctx.lineTo(370, 285); ctx.stroke();
            ctx.beginPath(); ctx.arc(185, 285, 45, 0, Math.PI*2); ctx.stroke();
            
            // Goals
            ctx.strokeStyle = "white";
            ctx.lineWidth = 4;
            ctx.strokeRect(32*5, 0, 10*5, 10);
            ctx.strokeRect(32*5, canvas.height-10, 10*5, 10);

            // Team 1 (Red)
            ctx.fillStyle = "#ff5252";
            ctx.shadowBlur = 10; ctx.shadowColor = "#ff5252";
            state.team1.forEach(p => {{ ctx.beginPath(); ctx.arc(p[0]*5, p[1]*5, 8, 0, Math.PI*2); ctx.fill(); }});
            
            // Team 2 (Blue)
            ctx.fillStyle = "#448aff";
            ctx.shadowColor = "#448aff";
            state.team2.forEach(p => {{ ctx.beginPath(); ctx.arc(p[0]*5, p[1]*5, 8, 0, Math.PI*2); ctx.fill(); }});
            
            // Ball
            ctx.fillStyle = "white";
            ctx.shadowBlur = 15; ctx.shadowColor = "white";
            ctx.beginPath(); ctx.arc(state.ball[0]*5, state.ball[1]*5, 5, 0, Math.PI*2); ctx.fill();
            ctx.shadowBlur = 0;
            
            // Update Text
            document.getElementById('s1').innerText = state.score[0];
            document.getElementById('s2').innerText = state.score[1];
            document.getElementById('step').innerText = state.step || frameIdx;

            frameIdx++;
            setTimeout(() => requestAnimationFrame(draw), 50);
        }}
        draw();
    </script>
</body>
</html>
"""

def get_broadcast_html(history):
    data_json = json.dumps(history)
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>FootyZero Premiere Broadcast</title>
    <style>
        body {{ background: #0a0a0b; color: #eee; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; gap: 40px; }}
        .sidebar {{ width: 300px; display: flex; flex-direction: column; gap: 20px; }}
        .card {{ background: #161618; padding: 20px; border-radius: 12px; border: 1px solid #2a2a2e; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .card-title {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; font-weight: bold; }}
        .stat-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }}
        .team-a {{ color: #ff5252; }}
        .team-b {{ color: #448aff; }}
        canvas {{ background: #1b4d1d; border: 10px solid #161618; border-radius: 16px; box-shadow: 0 30px 100px rgba(0,0,0,0.8); }}
        .score-main {{ font-size: 48px; font-weight: 900; margin-bottom: 20px; letter-spacing: -2px; text-align: center; }}
        .timer {{ font-family: monospace; font-size: 20px; color: #ffd740; text-align: center; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="card">
            <div class="card-title">Broadcast Info</div>
            <div class="stat-row"><span>Type</span> <span style="color:#ffd740">Full Match Replay</span></div>
            <div class="stat-row"><span>Duration</span> <span>{len(history)} Steps</span></div>
            <div class="stat-row"><span>Speed</span> <span>1.0x (Natural)</span></div>
        </div>
        <div class="card">
            <div class="card-title">Match Context</div>
            <div class="stat-row"><span>Agent A</span> <span class="team-a">PPO Trained</span></div>
            <div class="stat-row"><span>Agent B</span> <span class="team-b">PPO Trained</span></div>
        </div>
        <div style="font-size: 10px; color: #444; text-align: center;">FOOTYZERO PREMIERE ENGINE v2.0</div>
    </div>

    <div>
        <div class="score-main">
            <span class="team-a" id="score-a">0</span><span style="color:#222; margin: 0 20px;">-</span><span class="team-b" id="score-b">0</span>
        </div>
        <div id="full-time" style="display:none; text-align:center; color:#ffd740; font-weight:bold; margin-bottom:10px; letter-spacing:2px;">FULL TIME</div>
        <canvas id="pitch" width="370" height="570"></canvas>
        <div class="timer" id="clock">00:00</div>
    </div>

    <script>
        const matchData = {data_json};
        const canvas = document.getElementById('pitch');
        const ctx = canvas.getContext('2d');
        let frameIdx = 0;
        let lastTimestamp = 0;
        const interval = 100; // 10 FPS
        let isPaused = false;

        function play(timestamp) {{
            if (isPaused) return;

            if (frameIdx >= matchData.length) {{
                isPaused = true;
                setTimeout(() => {{ 
                    frameIdx = 0; 
                    isPaused = false;
                    lastTimestamp = performance.now();
                    requestAnimationFrame(play);
                }}, 3000);
                return;
            }}

            if (!lastTimestamp) lastTimestamp = timestamp;
            const progress = timestamp - lastTimestamp;

            if (progress >= interval) {{
                lastTimestamp = timestamp - (progress % interval);
                const frame = matchData[frameIdx];
                draw(frame);
                
                document.getElementById('score-a').innerText = frame.score[0];
                document.getElementById('score-b').innerText = frame.score[1];
                const ts = Math.floor(frameIdx / 10);
                document.getElementById('clock').innerText = 
                    String(Math.floor(ts/60)).padStart(2,'0') + ":" + 
                    String(ts%60).padStart(2,'0');
                
                if (frameIdx === matchData.length - 1) {{
                    document.getElementById('full-time').style.display = 'block';
                }} else {{
                    document.getElementById('full-time').style.display = 'none';
                }}
                
                frameIdx++;
            }}
            requestAnimationFrame(play);
        }}

        function draw(state) {{
            ctx.clearRect(0, 0, 370, 570);
            for(let i=0; i<10; i++) {{
                ctx.fillStyle = i % 2 === 0 ? "#1b4d1d" : "#1e5420";
                ctx.fillRect(0, i * 57, 370, 57);
            }}
            ctx.strokeStyle = "rgba(255,255,255,0.15)"; ctx.lineWidth = 2;
            ctx.strokeRect(5, 5, 360, 560);
            ctx.beginPath(); ctx.moveTo(5, 285); ctx.lineTo(365, 285); ctx.stroke();
            ctx.beginPath(); ctx.arc(185, 285, 45, 0, Math.PI*2); ctx.stroke();
            ctx.strokeStyle = "white"; ctx.lineWidth = 4;
            ctx.strokeRect(160, 0, 50, 6); ctx.strokeRect(160, 564, 50, 6);

            state.team1.forEach(p => {{ ctx.fillStyle = "#ff5252"; ctx.beginPath(); ctx.arc(p[0]*5, p[1]*5, 9, 0, Math.PI*2); ctx.fill(); }});
            state.team2.forEach(p => {{ ctx.fillStyle = "#448aff"; ctx.beginPath(); ctx.arc(p[0]*5, p[1]*5, 9, 0, Math.PI*2); ctx.fill(); }});
            
            ctx.fillStyle = "white"; ctx.shadowBlur = 10; ctx.shadowColor = "white";
            ctx.beginPath(); ctx.arc(state.ball[0]*5, state.ball[1]*5, 5, 0, Math.PI*2); ctx.fill();
            ctx.shadowBlur = 0;
            if (state.possession > 0) {{
                ctx.strokeStyle = state.possession === 1 ? "#ff5252" : "#448aff";
                ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(state.ball[0]*5, state.ball[1]*5, 11, 0, Math.PI*2); ctx.stroke();
            }}
        }}
        requestAnimationFrame(play);
    </script>
</body>
</html>
"""
