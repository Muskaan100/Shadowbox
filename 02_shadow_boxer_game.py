import cv2
import time
import math
import random
import os
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# -----------------------------------------------------------------------------
# SHADOW-BOXER: AR ARCADE KINETIC BOXING GAME
# Features:
# 1. Real-time Pose tracking on local CPU (No GPU needed!)
# 2. Left & Right Punch Hitboxes with speed/velocity calculation
# 3. Particle spark explosion effects on impact
# 4. Laser Dodge Mechanic (Squat / Duck below the line!)
# 5. Combo streaks, dynamic HUD, and post-game workout stats
# -----------------------------------------------------------------------------

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_lite.task")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# 1. Initialize MediaPipe Detector
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
detector = vision.PoseLandmarker.create_from_options(options)

# 2. Camera Setup
cap = cv2.VideoCapture(0)
WIDTH = 640
HEIGHT = 480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# -----------------------------------------------------------------------------
# GAME STATE & VARIABLES
# -----------------------------------------------------------------------------
GAME_STATE = "WAITING"   # "WAITING", "PLAYING", "GAMEOVER"
GAME_DURATION = 60       # 60 seconds round
round_start_time = 0

score = 0
combo = 0
max_combo = 0
total_punches = 0
max_punch_speed = 0.0
dodges_completed = 0
last_hit_text = ""
last_hit_time = 0

# Wrist historical tracking for velocity calculation (pixels per second)
prev_wrist_l = None
prev_wrist_r = None
last_pose_time = time.time()

# Target data: (x, y, radius, hand_type: 'LEFT' or 'RIGHT', spawn_time)
target = None
TARGET_RADIUS = 45
GLOVE_RADIUS = 35

# Laser Dodge Hazard
laser_active = False
laser_y = 200
laser_start_time = 0
laser_duration = 3.5  # duration laser stays active
next_laser_time = time.time() + random.uniform(8, 14)
laser_dodged = False

# Particle System for Hit Explosions
particles = []

def spawn_target():
    """Spawn a new target on screen matching appropriate hand reach."""
    hand_type = random.choice(["LEFT", "RIGHT"])
    if hand_type == "LEFT":
        # Left side of screen (user's left)
        x = random.randint(80, int(WIDTH * 0.42))
    else:
        # Right side of screen
        x = random.randint(int(WIDTH * 0.58), WIDTH - 80)
    y = random.randint(120, HEIGHT - 140)
    return {"x": x, "y": y, "radius": TARGET_RADIUS, "hand": hand_type, "spawn_time": time.time()}

def create_explosion(x, y, color):
    """Create flying glowing particle sparks when target explodes."""
    for _ in range(16):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 12)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        size = random.randint(3, 7)
        life = random.randint(10, 20)  # frames to live
        particles.append({"x": x, "y": y, "vx": vx, "vy": vy, "size": size, "life": life, "max_life": life, "color": color})

def update_and_draw_particles(frame):
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        alpha = p["life"] / p["max_life"]
        radius = max(1, int(p["size"] * alpha))
        cv2.circle(frame, (int(p["x"]), int(p["y"])), radius, p["color"], -1)
        if p["life"] <= 0:
            particles.remove(p)

# Spawn initial target
target = spawn_target()

print("\n" + "="*55)
print("  SHADOW-BOXER ARCADE RUNNING!")
print("  - Press SPACEBAR to start playing!")
print("  - Hit Blue targets with LEFT hand, Red with RIGHT hand.")
print("  - DUCK under the red laser when WARNING appears!")
print("  - Press 'R' to Restart, 'Q' to Quit.")
print("="*55 + "\n")

prev_time = time.time()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Flip horizontally for intuitive mirror reflection
    frame = cv2.flip(frame, 1)
    current_time = time.time()
    dt = current_time - last_pose_time if (current_time - last_pose_time) > 0 else 0.033
    last_pose_time = current_time

    # FPS Calculation
    fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 30
    prev_time = current_time

    # MediaPipe Pose Detection
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    result = detector.detect(mp_image)

    wrist_l = None
    wrist_r = None
    nose = None
    speed_l = 0.0
    speed_r = 0.0

    if result.pose_landmarks and len(result.pose_landmarks) > 0:
        lms = result.pose_landmarks[0]
        # Nose: 0, Left Wrist: 15, Right Wrist: 16
        nose = (int(lms[0].x * WIDTH), int(lms[0].y * HEIGHT))
        wrist_l = (int(lms[15].x * WIDTH), int(lms[15].y * HEIGHT))
        wrist_r = (int(lms[16].x * WIDTH), int(lms[16].y * HEIGHT))

        # Calculate punch speed (pixels moved / dt converted to simulated km/h)
        if prev_wrist_l:
            dist_l = math.hypot(wrist_l[0] - prev_wrist_l[0], wrist_l[1] - prev_wrist_l[1])
            speed_l = (dist_l / dt) * 0.05  # simulation scale
        if prev_wrist_r:
            dist_r = math.hypot(wrist_r[0] - prev_wrist_r[0], wrist_r[1] - prev_wrist_r[1])
            speed_r = (dist_r / dt) * 0.05

        prev_wrist_l = wrist_l
        prev_wrist_r = wrist_r

        # Draw stylish arcade boxing gloves on wrists (significantly larger!)
        # Left Glove (Cyan / Neon Blue)
        cv2.circle(frame, wrist_l, GLOVE_RADIUS + 6, (255, 255, 255), 2)  # Outer glow ring
        cv2.circle(frame, wrist_l, GLOVE_RADIUS, (255, 210, 0), -1)        # Solid punch glove
        cv2.circle(frame, wrist_l, GLOVE_RADIUS - 10, (255, 240, 120), -1) # Inner highlight
        cv2.putText(frame, "L", (wrist_l[0] - 10, wrist_l[1] + 8),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (20, 20, 20), 2)

        # Right Glove (Flame Orange / Neon Red)
        cv2.circle(frame, wrist_r, GLOVE_RADIUS + 6, (255, 255, 255), 2)  # Outer glow ring
        cv2.circle(frame, wrist_r, GLOVE_RADIUS, (0, 80, 255), -1)         # Solid punch glove
        cv2.circle(frame, wrist_r, GLOVE_RADIUS - 10, (80, 160, 255), -1)  # Inner highlight
        cv2.putText(frame, "R", (wrist_r[0] - 10, wrist_r[1] + 8),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)

        # NOTE: The nose dot has been removed so your face remains completely clean!
        # (The code still tracks head coordinates in the background for laser ducking)

    # -------------------------------------------------------------------------
    # GAMEPLAY LOGIC
    # -------------------------------------------------------------------------
    if GAME_STATE == "WAITING":
        # Overlay translucent start banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (40, 100), (WIDTH - 40, 380), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        cv2.putText(frame, "SHADOW-BOXER", (WIDTH // 2 - 170, 160),
                    cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 255, 255), 2)
        cv2.putText(frame, "AI Kinetic Punching & Dodging", (WIDTH // 2 - 165, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.putText(frame, "HOW TO PLAY:", (80, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        cv2.putText(frame, "- Hit CYAN target with LEFT glove", (80, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)
        cv2.putText(frame, "- Hit RED target with RIGHT glove", (80, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 255), 1)
        cv2.putText(frame, "- SQUAT & DUCK under the Laser Beam!", (80, 335), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        cv2.putText(frame, "PRESS [SPACE] TO START", (WIDTH // 2 - 150, 370),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    elif GAME_STATE == "PLAYING":
        elapsed = current_time - round_start_time
        time_left = max(0, int(GAME_DURATION - elapsed))

        if time_left <= 0:
            GAME_STATE = "GAMEOVER"

        # 1. Update Laser Hazard (Every 10-14 seconds)
        if not laser_active and current_time >= next_laser_time:
            laser_active = True
            laser_start_time = current_time
            laser_dodged = False

        if laser_active:
            laser_elapsed = current_time - laser_start_time
            laser_y = 210  # Player must duck nose below Y=210

            # Flashing warning or deadly laser beam
            laser_color = (0, 0, 255) if int(current_time * 8) % 2 == 0 else (0, 255, 255)
            cv2.line(frame, (0, laser_y), (WIDTH, laser_y), laser_color, 4)
            cv2.putText(frame, "! DUCK UNDER LASER !", (WIDTH // 2 - 130, laser_y - 12),
                        cv2.FONT_HERSHEY_DUPLEX, 0.7, laser_color, 2)

            # Check if player ducked
            if nose and nose[1] > laser_y:
                laser_dodged = True
                cv2.putText(frame, "NICE DODGE!", (WIDTH // 2 - 60, laser_y + 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if laser_elapsed >= laser_duration:
                laser_active = False
                next_laser_time = current_time + random.uniform(10, 16)
                if laser_dodged:
                    score += 50
                    dodges_completed += 1
                    last_hit_text = "PERFECT DODGE! +50"
                    last_hit_time = current_time
                else:
                    score = max(0, score - 30)
                    combo = 0
                    last_hit_text = "LASER HIT! -30"
                    last_hit_time = current_time

        # 2. Draw & Check Target Punch
        if target:
            # Pulsing radius animation
            pulse = int(math.sin(current_time * 6) * 4)
            r = target["radius"] + pulse
            t_color = (255, 200, 0) if target["hand"] == "LEFT" else (0, 80, 255)
            label = "L" if target["hand"] == "LEFT" else "R"

            # Draw target pad
            cv2.circle(frame, (target["x"], target["y"]), r, t_color, 3)
            cv2.circle(frame, (target["x"], target["y"]), max(4, r - 12), t_color, -1)
            cv2.putText(frame, label, (target["x"] - 9, target["y"] + 8),
                        cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 2)

            # Collision Check
            hit = False
            hit_speed = 0.0

            if target["hand"] == "LEFT" and wrist_l:
                d = math.hypot(wrist_l[0] - target["x"], wrist_l[1] - target["y"])
                if d < (r + GLOVE_RADIUS - 5):
                    hit = True
                    hit_speed = speed_l
            elif target["hand"] == "RIGHT" and wrist_r:
                d = math.hypot(wrist_r[0] - target["x"], wrist_r[1] - target["y"])
                if d < (r + GLOVE_RADIUS - 5):
                    hit = True
                    hit_speed = speed_r

            if hit:
                create_explosion(target["x"], target["y"], t_color)
                total_punches += 1
                combo += 1
                if combo > max_combo:
                    max_combo = combo

                # Simulated speed in km/h
                kmh = min(45.0, max(12.0, hit_speed * 1.8 + random.uniform(2, 6)))
                if kmh > max_punch_speed:
                    max_punch_speed = kmh

                points = 10 * combo
                score += points
                last_hit_text = f"+{points} PUNCH! ({kmh:.1f} km/h)"
                last_hit_time = current_time

                # Spawn next target immediately
                target = spawn_target()

        # Draw flying particle sparks
        update_and_draw_particles(frame)

        # 3. HUD (Heads Up Display)
        # Top Header Bar
        cv2.rectangle(frame, (0, 0), (WIDTH, 48), (20, 20, 20), -1)
        cv2.putText(frame, f"SCORE: {score}", (15, 32), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"TIME: {time_left}s", (WIDTH // 2 - 50, 32), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
        combo_color = (0, 255, 0) if combo < 5 else (0, 165, 255)
        cv2.putText(frame, f"COMBO: x{combo}", (WIDTH - 160, 32), cv2.FONT_HERSHEY_DUPLEX, 0.7, combo_color, 2)

        # Floating Hit Impact Toast
        if current_time - last_hit_time < 1.2:
            cv2.putText(frame, last_hit_text, (WIDTH // 2 - 120, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

    elif GAME_STATE == "GAMEOVER":
        # Post-game summary card
        overlay = frame.copy()
        cv2.rectangle(overlay, (50, 60), (WIDTH - 50, 420), (15, 15, 15), -1)
        cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

        cv2.putText(frame, "ROUND FINISHED!", (WIDTH // 2 - 150, 110),
                    cv2.FONT_HERSHEY_DUPLEX, 0.95, (0, 255, 255), 2)

        # Workout Metrics
        cal_burned = total_punches * 0.18 + dodges_completed * 0.5
        stats = [
            f"FINAL SCORE: {score}",
            f"PUNCHES LANDED: {total_punches}",
            f"MAX COMBO: x{max_combo}",
            f"TOP PUNCH SPEED: {max_punch_speed:.1f} km/h",
            f"LASER DODGES: {dodges_completed}",
            f"EST. CALORIES BURNED: {cal_burned:.1f} kcal",
        ]

        y_offset = 160
        for s in stats:
            cv2.putText(frame, s, (90, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (230, 230, 230), 2)
            y_offset += 36

        cv2.putText(frame, "Press 'R' to Play Again  |  'Q' to Quit", (WIDTH // 2 - 180, 400),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Global footer: FPS & Controls
    cv2.putText(frame, f"FPS: {int(fps)} (CPU)", (10, HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 255, 100), 1)

    cv2.imshow("SHADOW-BOXER: Kinetic AR Punching Game", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == 32:  # SPACEBAR to start
        if GAME_STATE == "WAITING":
            GAME_STATE = "PLAYING"
            round_start_time = time.time()
            score = 0
            combo = 0
            total_punches = 0
            max_punch_speed = 0.0
            dodges_completed = 0
    elif key == ord('r'):  # Restart
        GAME_STATE = "PLAYING"
        round_start_time = time.time()
        score = 0
        combo = 0
        total_punches = 0
        max_punch_speed = 0.0
        dodges_completed = 0

cap.release()
cv2.destroyAllWindows()
detector.close()
