"""
=============================================================================
SHADOWBOX: FRUIT NINJA ARCADIA (03_fruit_ninja_game.py)
A Full Webcam-Controlled Fruit Slicing Arcade Game Powered by MediaPipe Hands
=============================================================================
"""

import os
import sys
import time
import math
import json
import random
import numpy as np
import cv2
import pygame

from hand_tracker import HandTracker, BladeTrail
from fruit_physics import (
    FruitObject, SlicedHalf, JuiceParticle, JuiceSplatterDecal, 
    FloatingScore, WaveSpawner, swept_slice_collision
)
from fruit_sound_fx import get_audio_manager

# -----------------------------------------------------------------------------
# 1. CONSTANTS & SYSTEM CONFIGURATION
# -----------------------------------------------------------------------------

WINDOW_TITLE = "SHADOWBOX: Fruit Ninja AR Dojo"
SCREEN_W = 1280
SCREEN_H = 720
TARGET_FPS = 60

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "fruit_ninja_high_score.json")
ASSET_ROOT = os.path.join(os.path.dirname(__file__), "assets", "fruit_ninja")

# Splash color mappings (BGR)
SPLASH_COLORS = {
    "watermelon": (45, 45, 235),
    "apple": (35, 40, 230),
    "orange": (15, 140, 255),
    "banana": (35, 215, 255),
    "strawberry": (30, 35, 235),
    "kiwi": (50, 210, 80),
    "coconut": (240, 240, 250),
    "golden_fruit": (30, 210, 255),
    "frozen_fruit": (255, 230, 140),
    "bomb": (30, 30, 30)
}

SPLASH_DECAL_MAP = {
    "watermelon": "splash_red",
    "apple": "splash_red",
    "strawberry": "splash_red",
    "orange": "splash_orange",
    "banana": "splash_yellow",
    "kiwi": "splash_green",
    "golden_fruit": "splash_gold",
    "frozen_fruit": "splash_ice"
}

# -----------------------------------------------------------------------------
# 2. HIGH SCORE MANAGER
# -----------------------------------------------------------------------------

def load_high_scores():
    defaults = {"CLASSIC": 0, "ZEN": 0, "ARCADE": 0, "total_slices": 0}
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults

def save_high_scores(scores):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except Exception as e:
        print(f"[Score Error] Could not save high score: {e}")

# -----------------------------------------------------------------------------
# 3. SPRITE CACHE & ASSET LOADER
# -----------------------------------------------------------------------------

class SpriteCache:
    def __init__(self):
        self.fruits = {}
        self.halves = {}
        self.bombs = {}
        self.splatters = {}
        self.background = None
        self._load_all()

    def _load_all(self):
        # Background
        bg_path = os.path.join(ASSET_ROOT, "backgrounds", "dojo_cutting_board.png")
        if os.path.exists(bg_path):
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_W, SCREEN_H))
            
        # Fruits
        fruit_dir = os.path.join(ASSET_ROOT, "fruits")
        if os.path.exists(fruit_dir):
            for f in os.listdir(fruit_dir):
                if f.endswith(".png"):
                    key = os.path.splitext(f)[0]
                    img = pygame.image.load(os.path.join(fruit_dir, f)).convert_alpha()
                    self.fruits[key] = img

        # Halves
        half_dir = os.path.join(ASSET_ROOT, "sliced_fruits")
        if os.path.exists(half_dir):
            for f in os.listdir(half_dir):
                if f.endswith(".png"):
                    key = os.path.splitext(f)[0]
                    img = pygame.image.load(os.path.join(half_dir, f)).convert_alpha()
                    self.halves[key] = img

        # Bombs
        bomb_path = os.path.join(ASSET_ROOT, "bombs", "bomb.png")
        if os.path.exists(bomb_path):
            self.bombs["bomb"] = pygame.image.load(bomb_path).convert_alpha()

        # Splatters
        part_dir = os.path.join(ASSET_ROOT, "particles")
        if os.path.exists(part_dir):
            for f in os.listdir(part_dir):
                if f.startswith("splash_") and f.endswith(".png"):
                    key = os.path.splitext(f)[0]
                    self.splatters[key] = pygame.image.load(os.path.join(part_dir, f)).convert_alpha()

    def get_fruit_surface(self, fruit_type, radius):
        target_size = int(radius * 2.3)
        if fruit_type in self.fruits:
            orig = self.fruits[fruit_type]
            return pygame.transform.smoothscale(orig, (target_size, target_size))
        elif fruit_type == "bomb" and "bomb" in self.bombs:
            return pygame.transform.smoothscale(self.bombs["bomb"], (target_size, target_size))
        # Fallback circle surface
        surf = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
        color = SPLASH_COLORS.get(fruit_type, (200, 200, 200))
        pygame.draw.circle(surf, (color[2], color[1], color[0]), (target_size//2, target_size//2), int(radius))
        return surf

    def get_half_surface(self, fruit_type, side, radius):
        target_size = int(radius * 2.3)
        key = f"{fruit_type}_{side}"
        if key in self.halves:
            orig = self.halves[key]
            return pygame.transform.smoothscale(orig, (target_size, target_size))
        # Fallback semicircle
        surf = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
        color = SPLASH_COLORS.get(fruit_type, (200, 200, 200))
        rect = pygame.Rect(0, 0, target_size, target_size)
        start_angle = math.pi/2 if side == 'left' else -math.pi/2
        end_angle = 3*math.pi/2 if side == 'left' else math.pi/2
        pygame.draw.arc(surf, (color[2], color[1], color[0]), rect, start_angle, end_angle, int(radius))
        return surf

# -----------------------------------------------------------------------------
# 4. MAIN FRUIT NINJA GAME ENGINE
# -----------------------------------------------------------------------------

class FruitNinjaGame:
    def __init__(self, use_fullscreen=False):
        pygame.init()
        pygame.font.init()
        
        self.screen_w = SCREEN_W
        self.screen_h = SCREEN_H
        flags = pygame.DOUBLEBUF
        if use_fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("impact", 58)
        self.font_header = pygame.font.SysFont("trebuchetms", 36, bold=True)
        self.font_hud = pygame.font.SysFont("trebuchetms", 28, bold=True)
        self.font_small = pygame.font.SysFont("trebuchetms", 20)
        self.font_combo = pygame.font.SysFont("impact", 42)

        # Audio
        self.audio = get_audio_manager()

        # Sprites
        self.sprites = SpriteCache()

        # Camera & Hand Tracking
        self.cap = None
        self.tracker = None
        self.init_camera()
        self.init_tracker()

        # High Scores
        self.high_scores = load_high_scores()

        # Game State
        self.state = "MENU"  # "MENU", "CALIBRATION", "COUNTDOWN", "PLAYING", "PAUSED", "GAMEOVER"
        self.mode = "CLASSIC"  # "CLASSIC", "ZEN", "ARCADE"
        self.ar_blend_alpha = 0.35  # Opacity of camera feed overlay (0 = full dojo, 1 = full webcam)
        
        # Gameplay Session Stats
        self.score = 0
        self.lives = 3
        self.max_lives = 3
        self.time_remaining = 60.0
        self.total_sliced = 0
        self.total_missed = 0
        self.bombs_hit = 0
        self.max_combo = 0
        self.is_new_high_score = False

        # Collections
        self.active_fruits = []
        self.sliced_halves = []
        self.particles = []
        self.splatter_decals = []
        self.floating_scores = []

        # Systems
        self.spawner = WaveSpawner(self.screen_w, self.screen_h)
        self.screen_shake_time = 0.0
        self.shake_magnitude = 0.0
        self.flash_alpha = 0.0

        # Slow motion effect (frozen fruit)
        self.slow_mo_timer = 0.0
        self.time_scale = 1.0

        # Slicing combo accumulator (tracks slices in current swipe)
        self.current_swipe_slices = []
        self.last_slice_timestamp = 0.0

        # Menu Interactive Fruit Targets
        self.menu_targets = []
        self.init_menu_targets()

    def init_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 60)
            print("[Camera] Webcam initialized successfully at 640x480.")
        except Exception as e:
            print(f"[Camera Warning] Could not open webcam: {e}. Mouse fallback enabled.")
            self.cap = None

    def init_tracker(self):
        try:
            self.tracker = HandTracker()
            print("[Tracker] MediaPipe HandLandmarker initialized.")
        except Exception as e:
            print(f"[Tracker Error] Could not initialize HandTracker: {e}")
            self.tracker = None

    def release_camera(self):
        if self.cap:
            try:
                self.cap.release()
                print("[Camera] Webcam resources cleanly released.")
            except Exception:
                pass
            self.cap = None

    def init_menu_targets(self):
        """Interactive floating fruits on the Main Menu that player slices to select modes."""
        self.menu_targets = [
            FruitObject(1001, "watermelon", 0.25 * self.screen_w, 0.55 * self.screen_h, 0, 0, gravity=0, radius=65),
            FruitObject(1002, "orange", 0.50 * self.screen_w, 0.55 * self.screen_h, 0, 0, gravity=0, radius=65),
            FruitObject(1003, "golden_fruit", 0.75 * self.screen_w, 0.55 * self.screen_h, 0, 0, gravity=0, radius=65, special="golden"),
            FruitObject(1004, "bomb", 0.90 * self.screen_w, 0.82 * self.screen_h, 0, 0, gravity=0, radius=48, is_bomb=True)
        ]

    # -------------------------------------------------------------------------
    # STATE TRANSITIONS
    # -------------------------------------------------------------------------

    def start_game(self, mode="CLASSIC"):
        self.mode = mode
        self.score = 0
        self.total_sliced = 0
        self.total_missed = 0
        self.bombs_hit = 0
        self.max_combo = 0
        self.is_new_high_score = False
        self.lives = 3 if mode == "CLASSIC" else (99 if mode == "ZEN" else 3)
        self.time_remaining = 60.0 if mode in ["CLASSIC", "ARCADE"] else 90.0
        
        self.active_fruits.clear()
        self.sliced_halves.clear()
        self.particles.clear()
        self.floating_scores.clear()
        self.spawner = WaveSpawner(self.screen_w, self.screen_h)
        self.slow_mo_timer = 0.0
        self.time_scale = 1.0

        # Start with Countdown
        self.state = "COUNTDOWN"
        self.countdown_start = time.time()
        self.audio.play_countdown()

    def trigger_game_over(self):
        self.state = "GAMEOVER"
        self.audio.play_game_over()
        
        # Check high score
        current_best = self.high_scores.get(self.mode, 0)
        if self.score > current_best:
            self.high_scores[self.mode] = self.score
            self.is_new_high_score = True
        self.high_scores["total_slices"] = self.high_scores.get("total_slices", 0) + self.total_sliced
        save_high_scores(self.high_scores)

    # -------------------------------------------------------------------------
    # SLICE & EXPLOSION RESOLUTION
    # -------------------------------------------------------------------------

    def slice_fruit(self, fruit, contact_point=None, swipe_vector=None):
        if fruit.is_sliced:
            return
        fruit.is_sliced = True
        fruit.slice_time = time.time()
        cx, cy = fruit.x, fruit.y
        
        # 1. BOMB DETONATION
        if fruit.is_bomb:
            self.bombs_hit += 1
            self.audio.play_bomb()
            self.screen_shake_time = 0.5
            self.shake_magnitude = 22.0
            self.flash_alpha = 255.0
            
            # Spawn explosive sparks and smoke
            for _ in range(35):
                ang = random.uniform(0, 2*math.pi)
                spd = random.uniform(120, 600)
                vx = spd * math.cos(ang)
                vy = spd * math.sin(ang)
                color = random.choice([(255, 120, 20), (255, 220, 40), (200, 200, 200), (50, 50, 50)])
                self.particles.append(JuiceParticle(cx, cy, color, vx, vy, radius=random.uniform(4, 9), lifetime=random.uniform(0.5, 1.2), is_spark=True))
                
            if self.mode == "CLASSIC":
                self.lives = 0
                self.floating_scores.append(FloatingScore("BOMB! GAME OVER", cx, cy - 20, color=(255, 60, 60), scale=1.3))
                self.trigger_game_over()
            elif self.mode == "ARCADE":
                penalty = 25
                self.score = max(0, self.score - penalty)
                self.floating_scores.append(FloatingScore(f"-{penalty} BOMB PENALTY", cx, cy - 20, color=(255, 80, 80), scale=1.2))
                self.current_swipe_slices.clear()
            return

        # 2. NORMAL / SPECIAL FRUIT SLICE
        self.total_sliced += 1
        base_points = 30 if fruit.special == "golden" else 10
        self.score += base_points
        self.current_swipe_slices.append(fruit)
        self.last_slice_timestamp = time.time()
        
        # Sound
        self.audio.play_slice(fruit.fruit_type)
        
        # Floating point
        self.floating_scores.append(FloatingScore(f"+{base_points}", cx, cy - 15, color=(255, 235, 60) if fruit.special != "golden" else (255, 215, 0)))

        # Sliced halves trajectory
        split_speed = random.uniform(180, 320)
        h_left = SlicedHalf(fruit.fruit_type, cx - 12, cy, fruit.vx - split_speed, fruit.vy - 60, fruit.angle, -random.uniform(140, 260), 'left', fruit.special)
        h_right = SlicedHalf(fruit.fruit_type, cx + 12, cy, fruit.vx + split_speed, fruit.vy - 60, fruit.angle, random.uniform(140, 260), 'right', fruit.special)
        self.sliced_halves.extend([h_left, h_right])

        # Juice droplets & pulp particles
        splash_rgb = SPLASH_COLORS.get(fruit.fruit_type, (220, 40, 40))
        for _ in range(random.randint(16, 26)):
            ang = random.uniform(0, 2*math.pi)
            spd = random.uniform(80, 450)
            pvx = fruit.vx * 0.3 + spd * math.cos(ang)
            pvy = fruit.vy * 0.3 + spd * math.sin(ang)
            self.particles.append(JuiceParticle(cx, cy, splash_rgb, pvx, pvy, radius=random.uniform(3, 7), lifetime=random.uniform(0.4, 0.9)))

        # Splatter decal on cutting board
        decal_name = SPLASH_DECAL_MAP.get(fruit.fruit_type, "splash_red")
        self.splatter_decals.append(JuiceSplatterDecal(cx, cy, decal_name))
        if len(self.splatter_decals) > 18:
            self.splatter_decals.pop(0)

        # Special fruit powers
        if fruit.special == "golden":
            self.audio.play_bonus()
            for _ in range(30):
                ang = random.uniform(0, 2*math.pi)
                spd = random.uniform(150, 450)
                self.particles.append(JuiceParticle(cx, cy, (255, 215, 0), spd * math.cos(ang), spd * math.sin(ang), radius=random.uniform(4, 8), lifetime=1.0, is_spark=True))
        elif fruit.special == "frozen":
            self.slow_mo_timer = 4.5
            self.floating_scores.append(FloatingScore("FREEZE! SLOW-MO", cx, cy - 45, color=(140, 220, 255), scale=1.3))

    def evaluate_combo(self):
        """Evaluates multi-fruit slices performed in a single swipe."""
        now = time.time()
        if self.current_swipe_slices and (now - self.last_slice_timestamp) > 0.32:
            num_sliced = len(self.current_swipe_slices)
            if num_sliced >= 2:
                combo_bonus = num_sliced * (num_sliced - 1) * 2
                self.score += combo_bonus
                if num_sliced > self.max_combo:
                    self.max_combo = num_sliced
                self.audio.play_combo(num_sliced)
                
                # Floating combo text
                avg_x = sum(f.x for f in self.current_swipe_slices) / num_sliced
                avg_y = sum(f.y for f in self.current_swipe_slices) / num_sliced
                label = f"{num_sliced}x COMBO! +{combo_bonus}"
                color = (255, 120, 40) if num_sliced >= 4 else (255, 215, 0)
                self.floating_scores.append(FloatingScore(label, avg_x, avg_y - 45, color=color, duration=1.2, scale=1.4))
            self.current_swipe_slices.clear()

    # -------------------------------------------------------------------------
    # MAIN LOOP & UPDATE LOGIC
    # -------------------------------------------------------------------------

    def run(self):
        prev_time = time.perf_counter()
        running = True
        
        while running:
            # Timing & Delta-time
            curr_time = time.perf_counter()
            dt = max(1e-4, min(0.066, curr_time - prev_time))
            prev_time = curr_time

            # Slow-mo scaling
            if self.slow_mo_timer > 0:
                self.slow_mo_timer -= dt
                self.time_scale = 0.45
            else:
                self.time_scale = 1.0
            sim_dt = dt * self.time_scale

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        if self.state == "MENU":
                            running = False
                        else:
                            self.state = "MENU"
                    elif event.key == pygame.K_p:
                        if self.state == "PLAYING":
                            self.state = "PAUSED"
                        elif self.state == "PAUSED":
                            self.state = "PLAYING"
                    elif event.key == pygame.K_r:
                        if self.state in ["PLAYING", "GAMEOVER", "PAUSED"]:
                            self.start_game(self.mode)
                    elif event.key == pygame.K_m:
                        self.audio.toggle_mute()
                    elif event.key == pygame.K_b:
                        # Cycle AR background blend
                        self.ar_blend_alpha = (self.ar_blend_alpha + 0.3) % 1.0
                    elif event.key == pygame.K_1 and self.state == "MENU":
                        self.start_game("CLASSIC")
                    elif event.key == pygame.K_2 and self.state == "MENU":
                        self.start_game("ZEN")
                    elif event.key == pygame.K_3 and self.state == "MENU":
                        self.start_game("ARCADE")
                    elif event.key == pygame.K_SPACE:
                        if self.state == "MENU":
                            self.start_game("CLASSIC")
                        elif self.state == "GAMEOVER":
                            self.state = "MENU"

            # 2. Camera Frame Capture & Hand Tracking
            camera_surface = None
            active_slices = []
            
            if self.cap and self.cap.isOpened():
                ret, raw_frame = self.cap.read()
                if ret:
                    # Mirror webcam frame horizontally
                    flipped_bgr = cv2.flip(raw_frame, 1)
                    
                    # Process hands via MediaPipe
                    if self.tracker:
                        self.tracker.process_frame(flipped_bgr, self.screen_w, self.screen_h)
                        active_slices = self.tracker.get_active_slices(min_velocity=120.0)
                        
                    # Play swoosh audio on high velocity swipe
                    if self.tracker and self.tracker.any_hand_present:
                        for h in [self.tracker.left_hand, self.tracker.right_hand]:
                            if h.trail.velocity > 450.0 and random.random() < 0.25:
                                self.audio.play_swoosh()
                                
                    # Convert camera frame for Pygame background
                    rgb_small = cv2.cvtColor(cv2.resize(flipped_bgr, (self.screen_w, self.screen_h)), cv2.COLOR_BGR2RGB)
                    camera_surface = pygame.image.frombuffer(rgb_small.tobytes(), (self.screen_w, self.screen_h), 'RGB')

            # Mouse fallback for testing
            m_buttons = pygame.mouse.get_pressed()
            if m_buttons[0]:
                mx, my = pygame.mouse.get_pos()
                pmx, pmy = getattr(self, "prev_mouse", (mx, my))
                dist = math.hypot(mx - pmx, my - pmy)
                if dist > 6.0:
                    active_slices.append((( (pmx, pmy), (mx, my) ), "Mouse"))
                self.prev_mouse = (mx, my)
            else:
                self.prev_mouse = pygame.mouse.get_pos()

            # 3. State-Specific Updates
            if self.state == "MENU":
                self.update_menu(active_slices, dt)
            elif self.state == "COUNTDOWN":
                self.update_countdown(dt)
            elif self.state == "PLAYING":
                self.update_playing(active_slices, sim_dt, dt)
            elif self.state == "GAMEOVER":
                self.update_gameover(active_slices, dt)

            # 4. Rendering
            self.render(camera_surface)
            self.clock.tick(TARGET_FPS)

        self.release_camera()
        pygame.quit()

    # -------------------------------------------------------------------------
    # STATE UPDATE SUBROUTINES
    # -------------------------------------------------------------------------

    def update_menu(self, active_slices, dt):
        for target in self.menu_targets:
            target.angle = (target.angle + 40.0 * dt) % 360.0
            
            # Check slice collision
            for (p1, p2), _ in active_slices:
                hit, contact = swept_slice_collision(p1, p2, (target.x, target.y), target.radius, blade_radius=20.0)
                if hit:
                    self.slice_fruit(target, contact)
                    if target.fruit_type == "watermelon":
                        self.start_game("CLASSIC")
                    elif target.fruit_type == "orange":
                        self.start_game("ZEN")
                    elif target.fruit_type == "golden_fruit":
                        self.start_game("ARCADE")
                    elif target.is_bomb:
                        # Exit
                        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update_countdown(self, dt):
        elapsed = time.time() - self.countdown_start
        if elapsed >= 3.0:
            self.state = "PLAYING"

    def update_playing(self, active_slices, sim_dt, raw_dt):
        # Countdown game timer (for Classic & Arcade)
        if self.mode != "ZEN":
            self.time_remaining -= raw_dt
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.trigger_game_over()
                return

        # Screen shake
        if self.screen_shake_time > 0:
            self.screen_shake_time -= raw_dt

        # White flash fade
        if self.flash_alpha > 0:
            self.flash_alpha = max(0.0, self.flash_alpha - raw_dt * 450.0)

        # Spawning new waves
        new_fruits = self.spawner.get_wave(mode=self.mode, dt=sim_dt)
        self.active_fruits.extend(new_fruits)

        # Update fruits
        surviving_fruits = []
        for fruit in self.active_fruits:
            fruit.update(sim_dt)
            
            # Slicing collision check
            sliced_this_frame = False
            for (p1, p2), _ in active_slices:
                hit, contact = swept_slice_collision(p1, p2, (fruit.x, fruit.y), fruit.radius, blade_radius=22.0)
                if hit:
                    self.slice_fruit(fruit, contact)
                    sliced_this_frame = True
                    break
                    
            if not sliced_this_frame:
                if fruit.is_offscreen(self.screen_w, self.screen_h):
                    # Missed fruit penalty (Classic mode only, bombs do not penalize on drop)
                    if not fruit.is_bomb and self.mode == "CLASSIC":
                        self.lives -= 1
                        self.total_missed += 1
                        self.floating_scores.append(FloatingScore("MISS! -1 LIFE", fruit.x, self.screen_h - 40, color=(255, 70, 70)))
                        if self.lives <= 0:
                            self.trigger_game_over()
                else:
                    surviving_fruits.append(fruit)

        self.active_fruits = surviving_fruits

        # Evaluate combos
        self.evaluate_combo()

        # Update sliced halves
        self.sliced_halves = [h for h in self.sliced_halves if not h.is_dead(self.screen_h)]
        for h in self.sliced_halves:
            h.update(sim_dt)

        # Update particles
        self.particles = [p for p in self.particles if not p.is_dead()]
        for p in self.particles:
            p.update(sim_dt)

        # Update splatter decals
        self.splatter_decals = [d for d in self.splatter_decals if not d.is_dead()]
        for d in self.splatter_decals:
            d.update(raw_dt)

        # Update floating scores
        self.floating_scores = [f for f in self.floating_scores if not f.is_dead()]
        for f in self.floating_scores:
            f.update(raw_dt)

    def update_gameover(self, active_slices, dt):
        # Update lingering particles and halves
        for h in self.sliced_halves:
            h.update(dt)
        for p in self.particles:
            p.update(dt)

    # -------------------------------------------------------------------------
    # RENDERING ENGINE
    # -------------------------------------------------------------------------

    def render(self, camera_surface):
        # Screen shake offset
        shake_x, shake_y = 0, 0
        if self.screen_shake_time > 0:
            shake_x = int(random.uniform(-self.shake_magnitude, self.shake_magnitude))
            shake_y = int(random.uniform(-self.shake_magnitude, self.shake_magnitude))

        render_surf = pygame.Surface((self.screen_w, self.screen_h))

        # 1. Background (Cutting board + Webcam AR blend)
        if self.sprites.background:
            render_surf.blit(self.sprites.background, (0, 0))
        else:
            render_surf.fill((35, 25, 20))

        if camera_surface and self.ar_blend_alpha > 0.05:
            cam_copy = camera_surface.copy()
            cam_copy.set_alpha(int(self.ar_blend_alpha * 255))
            render_surf.blit(cam_copy, (0, 0))

        # 2. Splatter Decals
        for decal in self.splatter_decals:
            if decal.splash_type in self.sprites.splatters:
                orig = self.sprites.splatters[decal.splash_type]
                alpha = int(decal.alpha * 200)
                if alpha > 0:
                    rot = pygame.transform.rotate(orig, decal.angle)
                    rot.set_alpha(alpha)
                    r = rot.get_rect(center=(decal.x, decal.y))
                    render_surf.blit(rot, r)

        # 3. Active Fruits & Bombs
        if self.state in ["PLAYING", "PAUSED", "COUNTDOWN"]:
            for fruit in self.active_fruits:
                surf = self.sprites.get_fruit_surface(fruit.fruit_type, fruit.radius)
                rot = pygame.transform.rotate(surf, fruit.angle)
                r = rot.get_rect(center=(int(fruit.x), int(fruit.y)))
                render_surf.blit(rot, r)
                
                # Special Fruit Aura
                if fruit.special == "golden":
                    pygame.draw.circle(render_surf, (255, 230, 40), (int(fruit.x), int(fruit.y)), int(fruit.radius + 6), 3)
                elif fruit.special == "frozen":
                    pygame.draw.circle(render_surf, (140, 220, 255), (int(fruit.x), int(fruit.y)), int(fruit.radius + 6), 3)

        # 4. Sliced Fruit Halves
        for half in self.sliced_halves:
            surf = self.sprites.get_half_surface(half.fruit_type, half.side, 48.0)
            if half.alpha < 255:
                surf.set_alpha(half.alpha)
            rot = pygame.transform.rotate(surf, half.angle)
            r = rot.get_rect(center=(int(half.x), int(half.y)))
            render_surf.blit(rot, r)

        # 5. Particles (Droplets, Sparks)
        for p in self.particles:
            alpha = int(p.alpha * 255)
            if alpha > 0:
                color = (p.color[2], p.color[1], p.color[0])  # BGR to RGB
                if p.is_spark:
                    pygame.draw.circle(render_surf, (255, 255, 255), (int(p.x), int(p.y)), max(1, int(p.radius * 0.6)))
                    pygame.draw.circle(render_surf, color, (int(p.x), int(p.y)), int(p.radius), 2)
                else:
                    p_surf = pygame.Surface((int(p.radius*2), int(p.radius*2)), pygame.SRCALPHA)
                    pygame.draw.circle(p_surf, (*color, alpha), (int(p.radius), int(p.radius)), int(p.radius))
                    render_surf.blit(p_surf, (int(p.x - p.radius), int(p.y - p.radius)))

        # 6. Blade Trails (Katana Ribbon Effect)
        if self.tracker:
            for hand in [self.tracker.left_hand, self.tracker.right_hand]:
                segs = hand.trail.get_segments()
                b, g, r = hand.trail.color
                for (x1, y1), (x2, y2), alpha in segs:
                    width = max(2, int(16 * alpha))
                    # Outer neon glow
                    pygame.draw.line(render_surf, (r, g, b), (int(x1), int(y1)), (int(x2), int(y2)), width)
                    # White core
                    pygame.draw.line(render_surf, (255, 255, 255), (int(x1), int(y1)), (int(x2), int(y2)), max(2, width//3))

                # Hand Reticle / Slicing Point
                if hand.is_present and hand.index_tip:
                    ix, iy = int(hand.index_tip[0]), int(hand.index_tip[1])
                    pygame.draw.circle(render_surf, (r, g, b), (ix, iy), 14, 2)
                    pygame.draw.circle(render_surf, (255, 255, 255), (ix, iy), 5)
                    # Label
                    lbl = self.font_small.render(hand.label[0], True, (255, 255, 255))
                    render_surf.blit(lbl, (ix - 5, iy - 28))

        # 7. Floating Scores
        for fs in self.floating_scores:
            txt = self.font_header.render(fs.text, True, fs.color)
            txt.set_alpha(int(fs.alpha * 255))
            render_surf.blit(txt, (int(fs.x - txt.get_width()//2), int(fs.y)))

        # 8. HUD & Overlays
        if self.state == "PLAYING":
            self.draw_hud(render_surf)
        elif self.state == "MENU":
            self.draw_menu(render_surf)
        elif self.state == "COUNTDOWN":
            self.draw_countdown(render_surf)
        elif self.state == "PAUSED":
            self.draw_hud(render_surf)
            self.draw_pause(render_surf)
        elif self.state == "GAMEOVER":
            self.draw_gameover(render_surf)

        # 9. Bomb Flash
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.screen_w, self.screen_h))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(int(self.flash_alpha))
            render_surf.blit(flash_surf, (0, 0))

        # 10. Hand Warning Banner (if no hand detected)
        if self.tracker and not self.tracker.any_hand_present and self.tracker.seconds_since_last_hand > 1.2:
            self.draw_hand_warning(render_surf)

        # Final Blit with Screen Shake
        self.screen.fill((0, 0, 0))
        self.screen.blit(render_surf, (shake_x, shake_y))
        pygame.display.flip()

    # -------------------------------------------------------------------------
    # HUD & UI SUBROUTINES
    # -------------------------------------------------------------------------

    def draw_hud(self, surf):
        # Top banner panel
        hud_bg = pygame.Surface((self.screen_w, 75), pygame.SRCALPHA)
        hud_bg.fill((10, 10, 15, 170))
        surf.blit(hud_bg, (0, 0))

        # Score Counter
        score_lbl = self.font_hud.render(f"SCORE: {self.score}", True, (255, 220, 40))
        surf.blit(score_lbl, (30, 20))

        # High Score
        high_lbl = self.font_small.render(f"BEST: {self.high_scores.get(self.mode, 0)}", True, (190, 190, 190))
        surf.blit(high_lbl, (32, 50))

        # Mode Badge
        mode_surf = self.font_hud.render(f"[{self.mode} MODE]", True, (80, 220, 255))
        surf.blit(mode_surf, (self.screen_w//2 - mode_surf.get_width()//2, 22))

        # Timer (Classic / Arcade)
        if self.mode != "ZEN":
            time_col = (255, 80, 80) if self.time_remaining <= 10.0 else (255, 255, 255)
            time_lbl = self.font_hud.render(f"TIME: {int(self.time_remaining)}s", True, time_col)
            surf.blit(time_lbl, (self.screen_w - 320, 22))

        # Lives (Hearts & X's)
        if self.mode == "CLASSIC":
            lives_x = self.screen_w - 140
            for i in range(self.max_lives):
                col = (255, 45, 45) if i < self.lives else (70, 70, 70)
                # Draw heart / cross indicator
                if i < self.lives:
                    pygame.draw.circle(surf, col, (lives_x + i * 36, 36), 11)
                else:
                    # Red X for lost life
                    lx = lives_x + i * 36
                    pygame.draw.line(surf, (220, 30, 30), (lx - 9, 27), (lx + 9, 45), 3)
                    pygame.draw.line(surf, (220, 30, 30), (lx + 9, 27), (lx - 9, 45), 3)

        # Slow-mo indicator
        if self.slow_mo_timer > 0:
            freeze_lbl = self.font_header.render(f"FROZEN SLOW-MO ({self.slow_mo_timer:.1f}s)", True, (130, 230, 255))
            surf.blit(freeze_lbl, (self.screen_w//2 - freeze_lbl.get_width()//2, 85))

    def draw_menu(self, surf):
        # Title Header
        title = self.font_title.render("SHADOWBOX: FRUIT NINJA", True, (255, 215, 0))
        surf.blit(title, (self.screen_w//2 - title.get_width()//2, 55))

        sub = self.font_small.render("WEBCAM GESTURE-POWERED FRUIT SLICING ARCADE", True, (200, 220, 240))
        surf.blit(sub, (self.screen_w//2 - sub.get_width()//2, 125))

        instruction = self.font_header.render("SLICE A FRUIT TO CHOOSE YOUR MODE!", True, (255, 255, 255))
        surf.blit(instruction, (self.screen_w//2 - instruction.get_width()//2, 175))

        # Draw Menu Targets
        labels = [
            ("CLASSIC", "3 Lives - Bombs - 60s", (45, 195, 35)),
            ("ZEN", "No Bombs - Pure Slicing", (255, 160, 20)),
            ("ARCADE", "Frenzy - Powers - Bombs", (255, 215, 0)),
            ("EXIT", "Slice Bomb to Quit", (220, 60, 60))
        ]
        for target, (name, desc, col) in zip(self.menu_targets, labels):
            surf_f = self.sprites.get_fruit_surface(target.fruit_type, target.radius)
            rot = pygame.transform.rotate(surf_f, target.angle)
            r = rot.get_rect(center=(int(target.x), int(target.y)))
            surf.blit(rot, r)

            name_t = self.font_header.render(name, True, col)
            surf.blit(name_t, (int(target.x - name_t.get_width()//2), int(target.y + target.radius + 15)))
            
            desc_t = self.font_small.render(desc, True, (200, 200, 200))
            surf.blit(desc_t, (int(target.x - desc_t.get_width()//2), int(target.y + target.radius + 50)))

        # Keyboard fallback hints at bottom
        hint = self.font_small.render("Keyboard shortcuts: [1] Classic  [2] Zen  [3] Arcade  [SPACE] Quick Start  [B] Toggle Camera Blend  [M] Mute  [ESC] Quit", True, (160, 160, 170))
        surf.blit(hint, (self.screen_w//2 - hint.get_width()//2, self.screen_h - 45))

    def draw_countdown(self, surf):
        elapsed = time.time() - self.countdown_start
        step = int(3 - elapsed)
        text = str(step + 1) if step >= 0 else "SLICE!"
        scale = 1.0 + (elapsed % 1.0) * 0.35
        
        num_font = pygame.font.SysFont("impact", int(110 * scale))
        num_surf = num_font.render(text, True, (255, 220, 40))
        surf.blit(num_surf, (self.screen_w//2 - num_surf.get_width()//2, self.screen_h//2 - num_surf.get_height()//2))

    def draw_pause(self, surf):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 190))
        surf.blit(overlay, (0, 0))

        p_txt = self.font_title.render("GAME PAUSED", True, (255, 255, 255))
        surf.blit(p_txt, (self.screen_w//2 - p_txt.get_width()//2, self.screen_h//2 - 90))

        sub = self.font_header.render("Press 'P' to Resume | 'R' to Restart | 'ESC' for Menu", True, (200, 220, 255))
        surf.blit(sub, (self.screen_w//2 - sub.get_width()//2, self.screen_h//2 + 10))

    def draw_gameover(self, surf):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((15, 10, 12, 215))
        surf.blit(overlay, (0, 0))

        # Title
        t_col = (255, 215, 0) if self.is_new_high_score else (255, 70, 70)
        t_text = "NEW HIGH SCORE!" if self.is_new_high_score else "GAME OVER"
        title = self.font_title.render(t_text, True, t_col)
        surf.blit(title, (self.screen_w//2 - title.get_width()//2, 90))

        # Stats Card
        stats_box = pygame.Surface((600, 310), pygame.SRCALPHA)
        stats_box.fill((25, 25, 35, 220))
        pygame.draw.rect(stats_box, (80, 80, 110), stats_box.get_rect(), 2, border_radius=12)
        surf.blit(stats_box, (self.screen_w//2 - 300, 180))

        bx = self.screen_w//2 - 250
        by = 210
        total_swipes = self.total_sliced + self.total_missed
        acc = int((self.total_sliced / max(1, total_swipes)) * 100)

        lines = [
            (f"FINAL SCORE:", f"{self.score}", (255, 225, 40)),
            (f"MODE RECORD:", f"{self.high_scores.get(self.mode, 0)}", (180, 230, 255)),
            (f"FRUITS SLICED:", f"{self.total_sliced}", (255, 255, 255)),
            (f"MAX COMBO:", f"{self.max_combo}x COMBO", (255, 140, 40)),
            (f"ACCURACY:", f"{acc}%", (140, 255, 140)),
            (f"BOMBS HIT:", f"{self.bombs_hit}", (255, 80, 80))
        ]

        for lbl, val, col in lines:
            t1 = self.font_small.render(lbl, True, (200, 200, 200))
            t2 = self.font_hud.render(val, True, col)
            surf.blit(t1, (bx, by))
            surf.blit(t2, (bx + 320, by - 4))
            by += 44

        restart_t = self.font_header.render("Press SPACE or 'R' to Play Again | 'ESC' for Menu", True, (255, 255, 255))
        surf.blit(restart_t, (self.screen_w//2 - restart_t.get_width()//2, 530))

    def draw_hand_warning(self, surf):
        warn_box = pygame.Surface((480, 52), pygame.SRCALPHA)
        warn_box.fill((220, 40, 30, 210))
        pygame.draw.rect(warn_box, (255, 255, 255), warn_box.get_rect(), 2, border_radius=8)
        
        warn_t = self.font_small.render("PLEASE RAISE HAND IN FRONT OF WEBCAM TO SLICE", True, (255, 255, 255))
        warn_box.blit(warn_t, (warn_box.get_width()//2 - warn_t.get_width()//2, 14))
        
        surf.blit(warn_box, (self.screen_w//2 - 240, self.screen_h - 75))

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------

def main():
    use_fullscreen = "--fullscreen" in sys.argv or "-f" in sys.argv
    game = FruitNinjaGame(use_fullscreen=use_fullscreen)
    game.run()

if __name__ == "__main__":
    main()
