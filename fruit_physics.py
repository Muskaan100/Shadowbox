"""
Fruit Ninja Physics & Object Engine
Mathematical continuous swept collision, parabolic launch trajectories,
fruit splitting dynamics, and particle simulations.
"""

import math
import random
import time
import numpy as np

def dist_point_to_segment(px, py, x1, y1, x2, y2):
    """
    Compute minimum Euclidean distance from point (px, py) to line segment (x1, y1)-(x2, y2).
    Prevents tunneling during fast swipes.
    """
    dx = x2 - x1
    dy = y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-6:
        return math.hypot(px - x1, py - y1), (x1, y1)
    
    # Projection factor t clamped between 0.0 and 1.0
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y), (proj_x, proj_y)

def swept_slice_collision(prev_pos, curr_pos, target_pos, target_radius, blade_radius=18.0):
    """
    Determines if swept blade segment intersects fruit circle.
    Returns (hit: bool, contact_point: tuple)
    """
    if prev_pos is None or curr_pos is None:
        return False, None
    x1, y1 = prev_pos
    x2, y2 = curr_pos
    tx, ty = target_pos
    dist, contact = dist_point_to_segment(tx, ty, x1, y1, x2, y2)
    hit = dist <= (target_radius + blade_radius)
    return hit, contact

class FruitObject:
    """Represents a flying whole fruit or bomb hazard."""
    def __init__(self, obj_id, fruit_type, x, y, vx, vy, gravity=980.0, radius=52.0, is_bomb=False, special=None):
        self.id = obj_id
        self.fruit_type = fruit_type  # 'watermelon', 'apple', 'orange', 'banana', 'strawberry', 'kiwi', 'coconut', 'bomb'
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.gravity = float(gravity)
        self.radius = float(radius)
        self.is_bomb = is_bomb
        self.special = special  # 'golden', 'frozen', None
        
        self.angle = random.uniform(0.0, 360.0)
        self.angular_velocity = random.uniform(-180.0, 180.0)  # degrees/sec
        
        self.is_sliced = False
        self.slice_angle = 0.0
        self.slice_time = 0.0
        self.missed = False
        self.spawn_time = time.time()
        self.lifetime = 0.0

    def update(self, dt):
        """Delta-time based Newtonian physics update."""
        self.x += self.vx * dt
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.angular_velocity * dt) % 360.0
        self.lifetime += dt

    def is_offscreen(self, screen_w, screen_h):
        """Check if fallen off the bottom or outside bounds after reaching apex."""
        # Only considered dead if moving downward and below bottom screen margin
        return self.vy > 0 and self.y > (screen_h + self.radius + 60)

class SlicedHalf:
    """Sliced fruit half thrown outward with angular torque."""
    def __init__(self, fruit_type, x, y, vx, vy, angle, angular_velocity, side='left', special=None):
        self.fruit_type = fruit_type
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.angle = float(angle)
        self.angular_velocity = float(angular_velocity)
        self.side = side  # 'left' or 'right'
        self.special = special
        self.gravity = 1100.0
        self.alpha = 255
        self.lifetime = 0.0

    def update(self, dt):
        self.x += self.vx * dt
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.angular_velocity * dt) % 360.0
        self.lifetime += dt
        if self.lifetime > 1.2:
            self.alpha = max(0, int(255 * (1.0 - (self.lifetime - 1.2) / 0.6)))

    def is_dead(self, screen_h):
        return self.y > (screen_h + 100) or self.alpha <= 0

class JuiceParticle:
    """Juice droplets, seeds, sparks, and smoke particles."""
    def __init__(self, x, y, color, vx, vy, radius=4.0, lifetime=0.75, gravity=750.0, is_spark=False):
        self.x = float(x)
        self.y = float(y)
        self.color = color  # (B, G, R)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = float(radius)
        self.max_life = float(lifetime)
        self.life = float(lifetime)
        self.gravity = float(gravity)
        self.is_spark = is_spark

    def update(self, dt):
        self.x += self.vx * dt
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        self.life -= dt

    @property
    def alpha(self):
        return max(0.0, min(1.0, self.life / self.max_life))

    def is_dead(self):
        return self.life <= 0

class JuiceSplatterDecal:
    """Persistent juice splash mark on the dojo cutting board."""
    def __init__(self, x, y, splash_type, max_duration=7.0):
        self.x = int(x)
        self.y = int(y)
        self.splash_type = splash_type  # 'splash_red', 'splash_orange', etc.
        self.angle = random.uniform(0, 360)
        self.scale = random.uniform(0.65, 1.05)
        self.duration = max_duration
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    @property
    def alpha(self):
        if self.age < (self.duration - 2.0):
            return 1.0
        return max(0.0, 1.0 - (self.age - (self.duration - 2.0)) / 2.0)

    def is_dead(self):
        return self.age >= self.duration

class FloatingScore:
    """Floating points/combo banner that drifts up and fades."""
    def __init__(self, text, x, y, color=(255, 235, 60), duration=0.9, scale=1.0):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.vy = -75.0  # Drift upward
        self.duration = duration
        self.life = duration
        self.scale = scale

    def update(self, dt):
        self.y += self.vy * dt
        self.life -= dt

    @property
    def alpha(self):
        return max(0.0, min(1.0, self.life / self.duration))

    def is_dead(self):
        return self.life <= 0

# -----------------------------------------------------------------------------
# WAVE SPAWN GENERATOR
# -----------------------------------------------------------------------------

FRUIT_TYPES = ["watermelon", "apple", "orange", "banana", "strawberry", "kiwi", "coconut"]

class WaveSpawner:
    def __init__(self, screen_w=1280, screen_h=720):
        self.w = screen_w
        self.h = screen_h
        self.next_obj_id = 1
        self.time_to_next_wave = 1.0
        self.wave_counter = 0

    def get_wave(self, mode="CLASSIC", dt=0.016):
        """
        Calculates when to launch a new wave of fruits and bombs.
        Returns list of new FruitObject instances.
        """
        self.time_to_next_wave -= dt
        if self.time_to_next_wave > 0:
            return []
            
        self.wave_counter += 1
        spawned = []
        
        # Difficulty scaling
        if mode == "CLASSIC":
            wave_size = random.choices([1, 2, 3, 4], weights=[0.25, 0.45, 0.20, 0.10])[0]
            self.time_to_next_wave = random.uniform(1.8, 3.2)
            bomb_chance = 0.28 if self.wave_counter > 2 else 0.0
        elif mode == "ARCADE":
            wave_size = random.choices([2, 3, 4, 5], weights=[0.2, 0.4, 0.3, 0.1])[0]
            self.time_to_next_wave = random.uniform(1.2, 2.4)
            bomb_chance = 0.35
        else:  # ZEN
            wave_size = random.choices([1, 2, 3], weights=[0.4, 0.45, 0.15])[0]
            self.time_to_next_wave = random.uniform(2.2, 3.8)
            bomb_chance = 0.0  # Zen has NO bombs

        for _ in range(wave_size):
            obj = self._spawn_single(bomb_chance=bomb_chance, mode=mode)
            spawned.append(obj)
            
        return spawned

    def _spawn_single(self, bomb_chance=0.25, mode="CLASSIC"):
        obj_id = self.next_obj_id
        self.next_obj_id += 1
        
        # Determine object type
        is_bomb = (random.random() < bomb_chance)
        special = None
        
        if is_bomb:
            fruit_type = "bomb"
            radius = 48.0
        else:
            # Special fruit check (Golden or Frozen)
            r_spec = random.random()
            if r_spec < 0.05:
                fruit_type = "golden_fruit"
                special = "golden"
                radius = 54.0
            elif r_spec < 0.10 and mode in ["CLASSIC", "ARCADE"]:
                fruit_type = "frozen_fruit"
                special = "frozen"
                radius = 54.0
            else:
                fruit_type = random.choice(FRUIT_TYPES)
                radius = 52.0 if fruit_type == "watermelon" else (42.0 if fruit_type in ["strawberry", "kiwi"] else 48.0)

        # Launch physics: varied positions along bottom screen
        # Fruits arc inward towards center zone (0.35 * w to 0.65 * w)
        spawn_x = random.uniform(0.12 * self.w, 0.88 * self.w)
        spawn_y = self.h + radius + 15
        
        target_center_x = random.uniform(0.35 * self.w, 0.65 * self.w)
        target_apex_y = random.uniform(0.18 * self.h, 0.40 * self.h)
        
        gravity = 980.0
        # Time to reach apex: vy = -sqrt(2 * g * delta_y)
        delta_y = spawn_y - target_apex_y
        vy = -math.sqrt(2.0 * gravity * delta_y)
        t_apex = abs(vy) / gravity
        
        # Horizontal velocity to reach target_center_x at apex
        vx = (target_center_x - spawn_x) / t_apex
        # Add slight natural jitter
        vx += random.uniform(-35.0, 35.0)

        return FruitObject(
            obj_id=obj_id,
            fruit_type=fruit_type,
            x=spawn_x,
            y=spawn_y,
            vx=vx,
            vy=vy,
            gravity=gravity,
            radius=radius,
            is_bomb=is_bomb,
            special=special
        )
