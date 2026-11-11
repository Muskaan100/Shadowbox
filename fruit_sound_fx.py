"""
Fruit Ninja Audio Engine: High-fidelity procedural and hybrid audio synthesizer
Generates blade swooshes, juicy fruit slicing impacts, squelches, bomb explosions,
combos, countdowns, and game over sounds.
"""

import os
import math
import random
import numpy as np

SOUND_AVAILABLE = False
_sounds = {}
_swoosh_bank = []
_slice_bank = []
_splat_bank = []
_fuse_sound = None

try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(16)
    SOUND_AVAILABLE = True
except Exception as e:
    print(f"[Fruit Audio Warning] Could not initialize pygame.mixer: {e}")

def _to_sound(audio_mono, sample_rate=44100, volume=0.9):
    """Convert numpy 1D float array into pygame Sound."""
    if not SOUND_AVAILABLE:
        return None
    import pygame
    max_val = np.max(np.abs(audio_mono))
    if max_val > 0:
        audio_mono = audio_mono / max_val
    audio_int = (audio_mono * 32767 * volume).astype(np.int16)
    stereo = np.column_stack((audio_int, audio_int))
    return pygame.sndarray.make_sound(stereo)

# -----------------------------------------------------------------------------
# 1. PROCEDURAL SOUND SYNTHESIZERS
# -----------------------------------------------------------------------------

def synth_blade_swoosh(variation=0):
    """Fast, sharp aerodynamic katana blade slice through air."""
    sr = 44100
    dur = 0.18 + (variation * 0.02)
    t = np.linspace(0, dur, int(sr * dur), False)
    # Pitch sweep from high to low
    start_f = 2400 + variation * 300
    end_f = 280 + variation * 50
    freq_sweep = np.linspace(start_f, end_f, len(t))
    # Wind noise modulated with tone
    wind = np.random.uniform(-0.6, 0.6, len(t))
    tone = np.sin(2 * np.pi * freq_sweep * t)
    # Bell envelope
    env = np.sin(np.pi * (t / dur)) ** 2.2
    wave = np.tanh(1.8 * (0.6 * tone + 0.4 * wind) * env)
    return _to_sound(wave, volume=0.85)

def synth_fruit_slice(fruit_type="watermelon", variation=0):
    """Visceral fruit cutting sound combining blade cut transient + wet pulp squelch."""
    sr = 44100
    dur = 0.22 + (variation * 0.015)
    t = np.linspace(0, dur, int(sr * dur), False)
    
    # Base parameters per fruit
    if fruit_type == "watermelon":
        # Deep wet fleshy thwack
        body_freq = np.linspace(260, 65, len(t))
        crunch_burst = np.random.uniform(-0.7, 0.7, len(t)) * np.exp(-45 * t)
        sub_impulse = np.sin(2 * np.pi * 55 * t) * np.exp(-15 * t)
        wave = 0.45 * np.sin(2 * np.pi * body_freq * t) * np.exp(-18 * t) + 0.4 * crunch_burst + 0.5 * sub_impulse
    elif fruit_type == "apple":
        # Crisp snappy crack
        body_freq = np.linspace(1600, 400, len(t))
        crack = np.sin(2 * np.pi * body_freq * t) * np.exp(-120 * t)
        crunch = np.random.uniform(-0.8, 0.8, len(t)) * np.exp(-70 * t)
        wave = 0.6 * crack + 0.45 * crunch
    elif fruit_type == "coconut":
        # Hard hollow shell crack
        thud = np.sin(2 * np.pi * np.linspace(420, 110, len(t)) * t) * np.exp(-32 * t)
        crack = np.random.uniform(-0.9, 0.9, len(t)) * np.exp(-90 * t)
        wave = 0.7 * thud + 0.5 * crack
    else:
        # Citrus / soft pulp squishy burst
        body_freq = np.linspace(450, 120, len(t))
        wet = np.random.uniform(-0.55, 0.55, len(t)) * np.exp(-38 * t)
        tone = np.sin(2 * np.pi * body_freq * t) * np.exp(-25 * t)
        wave = 0.5 * tone + 0.5 * wet

    # Sharp blade edge transient for all cuts
    edge = np.sin(2 * np.pi * 3200 * t) * np.exp(-150 * t)
    full = np.tanh(1.9 * (wave + 0.35 * edge))
    return _to_sound(full, volume=0.95)

def synth_juice_splat():
    """Wet liquid droplet splatter."""
    sr = 44100
    dur = 0.16
    t = np.linspace(0, dur, int(sr * dur), False)
    freq = np.linspace(800, 150, len(t))
    bubbles = np.sin(2 * np.pi * freq * t + np.sin(2 * np.pi * 45 * t))
    env = np.exp(-22 * t)
    noise = np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-35 * t)
    wave = np.tanh(1.5 * (bubbles * 0.6 + noise * 0.4) * env)
    return _to_sound(wave, volume=0.8)

def synth_bomb_fuse():
    """Hissing burning rope fuse loop."""
    sr = 44100
    dur = 0.5
    t = np.linspace(0, dur, int(sr * dur), False)
    # High-pass crackle
    noise = np.random.uniform(-0.4, 0.4, len(t))
    sparks = np.where(np.random.rand(len(t)) > 0.985, np.random.uniform(-0.8, 0.8, len(t)), 0)
    wave = 0.5 * noise + 0.7 * sparks
    return _to_sound(wave, volume=0.55)

def synth_bomb_explosion():
    """Massive arcade bomb explosion with deep sub-bass shockwave."""
    sr = 44100
    dur = 1.1
    t = np.linspace(0, dur, int(sr * dur), False)
    sub = np.sin(2 * np.pi * np.linspace(110, 24, len(t)) * t) * np.exp(-3.5 * t)
    blast = np.random.uniform(-0.9, 0.9, len(t)) * np.exp(-4.2 * t)
    debris = np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-1.8 * t)
    wave = np.tanh(2.2 * (0.6 * sub + 0.7 * blast + 0.3 * debris))
    return _to_sound(wave, volume=1.0)

def synth_combo(multiplier=2):
    """Ascending cheerful musical chime arpeggio for combo slices."""
    sr = 44100
    dur = 0.45
    t = np.linspace(0, dur, int(sr * dur), False)
    # Base chord frequencies (C major pentatonic steps)
    base_freqs = [523.25, 659.25, 783.99, 1046.50, 1318.51]
    f1 = base_freqs[min(multiplier - 2, len(base_freqs) - 1)]
    f2 = f1 * 1.25  # Major third
    chime = (np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f2 * t)) * np.exp(-7.0 * t)
    return _to_sound(np.tanh(1.4 * chime), volume=0.9)

def synth_game_over():
    """Dramatic descending minor sting."""
    sr = 44100
    dur = 1.2
    t = np.linspace(0, dur, int(sr * dur), False)
    f = np.linspace(440, 110, len(t))
    drone = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * (f * 1.189) * t)) * np.exp(-2.2 * t)
    return _to_sound(np.tanh(1.6 * drone), volume=0.9)

def synth_countdown():
    """Crisp dojo strike bell for 3, 2, 1 countdown."""
    sr = 44100
    dur = 0.35
    t = np.linspace(0, dur, int(sr * dur), False)
    bell = (np.sin(2 * np.pi * 880 * t) + 0.4 * np.sin(2 * np.pi * 1760 * t)) * np.exp(-12 * t)
    return _to_sound(bell, volume=0.85)

# -----------------------------------------------------------------------------
# 2. AUDIO MANAGER & PLAYBACK
# -----------------------------------------------------------------------------

class FruitAudioManager:
    def __init__(self, asset_dir=None):
        self.asset_dir = asset_dir or os.path.join(os.path.dirname(__file__), "assets", "fruit_ninja", "audio")
        self.muted = False
        self.volume = 0.85
        self.sfx = {}
        self._load_and_synth()
        
    def _load_and_synth(self):
        # 1. Load CC0 Kenney files if present
        def load(rel):
            p = os.path.join(self.asset_dir, rel)
            if os.path.exists(p) and SOUND_AVAILABLE:
                try:
                    s = pygame.mixer.Sound(p)
                    s.set_volume(self.volume)
                    return s
                except Exception:
                    pass
            return None
            
        self.sfx["kenney_swoosh"] = load("kenney_swoosh.ogg")
        self.sfx["kenney_splat"] = load("kenney_splat.ogg")
        self.sfx["kenney_combo"] = load("kenney_combo.ogg")
        self.sfx["kenney_explosion"] = load("kenney_explosion.ogg")
        self.sfx["kenney_bonus"] = load("kenney_bonus.ogg")
        self.sfx["kenney_impact"] = load("kenney_slice_impact.ogg")
        
        # 2. Pre-generate procedural bank for rapid, zero-lag response
        self.swoosh_bank = [synth_blade_swoosh(i) for i in range(4)]
        self.slice_bank = {
            "watermelon": [synth_fruit_slice("watermelon", i) for i in range(3)],
            "apple": [synth_fruit_slice("apple", i) for i in range(3)],
            "coconut": [synth_fruit_slice("coconut", i) for i in range(3)],
            "orange": [synth_fruit_slice("orange", i) for i in range(3)],
            "default": [synth_fruit_slice("citrus", i) for i in range(3)]
        }
        self.splat_bank = [synth_juice_splat() for _ in range(3)]
        self.bomb_explosion = synth_bomb_explosion()
        self.countdown_snd = synth_countdown()
        self.game_over_snd = synth_game_over()
        self.combos = [synth_combo(m) for m in range(2, 8)]

    def play_swoosh(self):
        if self.muted or not SOUND_AVAILABLE:
            return
        # Random pick
        snd = random.choice(self.swoosh_bank)
        if snd:
            snd.play()

    def play_slice(self, fruit_type="watermelon"):
        if self.muted or not SOUND_AVAILABLE:
            return
        bank = self.slice_bank.get(fruit_type, self.slice_bank["default"])
        snd = random.choice(bank)
        if snd:
            snd.play()
        # Also play a subtle wet splat
        if random.random() > 0.4:
            sp = random.choice(self.splat_bank)
            if sp:
                sp.play()

    def play_bomb(self):
        if self.muted or not SOUND_AVAILABLE:
            return
        # Play both kenney explosion if available and procedural shockwave
        if self.sfx.get("kenney_explosion"):
            self.sfx["kenney_explosion"].play()
        if self.bomb_explosion:
            self.bomb_explosion.play()

    def play_combo(self, multiplier=2):
        if self.muted or not SOUND_AVAILABLE:
            return
        idx = max(0, min(multiplier - 2, len(self.combos) - 1))
        snd = self.combos[idx]
        if snd:
            snd.play()

    def play_bonus(self):
        if self.muted or not SOUND_AVAILABLE:
            return
        if self.sfx.get("kenney_bonus"):
            self.sfx["kenney_bonus"].play()
        elif self.combos[-1]:
            self.combos[-1].play()

    def play_countdown(self):
        if self.muted or not SOUND_AVAILABLE:
            return
        if self.countdown_snd:
            self.countdown_snd.play()

    def play_game_over(self):
        if self.muted or not SOUND_AVAILABLE:
            return
        if self.game_over_snd:
            self.game_over_snd.play()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

_manager = None
def get_audio_manager():
    global _manager
    if _manager is None:
        _manager = FruitAudioManager()
    return _manager

if __name__ == "__main__":
    import time
    am = get_audio_manager()
    print("Testing Fruit Ninja audio synthesis...")
    print("Playing swoosh...")
    am.play_swoosh()
    time.sleep(0.3)
    print("Playing watermelon slice...")
    am.play_slice("watermelon")
    time.sleep(0.4)
    print("Playing apple slice...")
    am.play_slice("apple")
    time.sleep(0.4)
    print("Playing combo x3...")
    am.play_combo(3)
    time.sleep(0.5)
    print("Playing bomb explosion...")
    am.play_bomb()
    time.sleep(1.0)
    print("Audio test finished successfully!")
