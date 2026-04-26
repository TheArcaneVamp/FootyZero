# Pitch Dimensions
PITCH_WIDTH = 74
PITCH_LENGTH = 114

# Physics
FRICTION = 0.9
BALL_RANGE = 3
KICK_POWER = 15.0 # Default kick power for passes and shots

# Goal Dimensions
GOAL_WIDTH_START = 32
GOAL_WIDTH_END = 42
GOAL_CENTER = 37

# Tackle Settings
TACKLE_RANGE = 4
TACKLE_SUCCESS_BASE = 0.5 # Can be adjusted or used as a base
POSSESSION_STICKY_FRAMES = 10
TACKLE_COOLDOWN_FRAMES = 20

# Match Structure
HALF_TIME_STEPS = 1000
TOTAL_STEPS = 2000

# Starting Positions (y < 57 is bottom half, y > 57 is top half)
# Team 1 always attacks y=114 (Top), Team 2 always attacks y=0 (Bottom)
POS_T1_KICKOFF = [[32, 50], [37, 57], [42, 50]]
POS_T2_DEFENDING = [[20, 94], [37, 85], [54, 94]]

POS_T2_KICKOFF = [[32, 64], [37, 57], [42, 64]]
POS_T1_DEFENDING = [[20, 20], [37, 29], [54, 20]]

# Noise parameters
PASS_NOISE_SCALE = 0.3
SHOT_NOISE_SCALE = 0.3
SHOT_TARGET_VARIANCE = 3.5
