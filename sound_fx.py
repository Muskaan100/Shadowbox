import numpy as np

# -----------------------------------------------------------------------------
# SHADOW-BOXER HIGH-FIDELITY PROCEDURAL BOXING AUDIO SYNTHESIZER
# Generates realistic heavy boxing punch impacts, leather slaps, and sub-bass thuds
# purely in memory with ZERO external files!
# -----------------------------------------------------------------------------

SOUND_AVAILABLE = False
_sounds = {}
_punch_bank = []
_last_sfx_time = {}

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(8)
    SOUND_AVAILABLE = True
except Exception as e:
    print(f"[Sound FX Warning] Could not initialize pygame.mixer: {e}. Running in silent mode.")

def _to_sound(audio_mono, sample_rate=44100, volume=0.92):
    """Normalize and convert 1D float numpy array into 16-bit stereo pygame Sound."""
    import pygame
    max_val = np.max(np.abs(audio_mono))
    if max_val > 0:
        audio_mono = audio_mono / max_val
    audio_int = (audio_mono * 32767 * volume).astype(np.int16)
    stereo = np.column_stack((audio_int, audio_int))
    return pygame.sndarray.make_sound(stereo)

# -----------------------------------------------------------------------------
# REALISTIC BOXING PUNCH IMPACT BANK (Heavy Bag / Padded Glove Impact Physics)
# Physical Model:
# - Initial Transient: 0-12ms snappy leather-on-leather crack (980-1400 Hz)
# - Mid-Body Thud: 15-65ms resonant compression pitch sweep (165 -> 58 Hz)
# - Sub-Bass Impulse: 20-130ms deep 46-58 Hz chest-thumping visceral boom
# - Soft-clipping saturation (np.tanh) for natural acoustic compression
# -----------------------------------------------------------------------------
def _build_realistic_punch(variation=0):
    sr = 44100
    dur = 0.15 + (variation * 0.015)
    t = np.linspace(0, dur, int(sr * dur), False)
    
    # 4 distinct impact profiles
    crack_freqs = [1250, 1100, 1400, 980]
    sub_freqs = [52, 46, 58, 48]
    mid_starts = [190, 175, 210, 165]
    mid_ends = [65, 58, 72, 60]
    
    cf = crack_freqs[variation % 4]
    sf = sub_freqs[variation % 4]
    ms = mid_starts[variation % 4]
    me = mid_ends[variation % 4]
    
    # 1. Leather crack transient (initial contact snap)
    crack = np.sin(2 * np.pi * cf * t) * np.exp(-110 * t)
    noise_burst = np.random.uniform(-0.45, 0.45, len(t)) * np.exp(-130 * t)
    
    # 2. Resonant mid-body punch (foam compression thud)
    body_pitch = np.linspace(ms, me, len(t))
    body_tone = np.sin(2 * np.pi * body_pitch * t) * np.exp(-24 * t)
    
    # 3. Visceral sub-bass thump (heavy bag impulse)
    sub_bass = np.sin(2 * np.pi * sf * t) * np.exp(-12 * t)
    
    # 4. Soft saturation for authentic analog punchiness
    raw = 0.28 * crack + 0.22 * noise_burst + 0.48 * body_tone + 0.85 * sub_bass
    wave = np.tanh(1.75 * raw)
    return _to_sound(wave, volume=0.92)

def _build_critical_punch():
    """Heavy explosive impact for KIAI / Battle Cry power punches."""
    sr = 44100
    dur = 0.35
    t = np.linspace(0, dur, int(sr * dur), False)
    crack = np.sin(2 * np.pi * 1600 * t) * np.exp(-120 * t)
    noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-80 * t)
    sub = np.sin(2 * np.pi * np.linspace(95, 38, len(t)) * t) * np.exp(-7.5 * t)
    wave = np.tanh(2.1 * (0.35 * crack + 0.25 * noise + 1.0 * sub))
    return _to_sound(wave, volume=0.98)

def _build_boss_hit_sound():
    sr = 44100
    duration = 0.20
    t = np.linspace(0, duration, int(sr * duration), False)
    bass = np.sin(2 * np.pi * np.linspace(160, 42, len(t)) * t)
    metal = np.sin(2 * np.pi * 780 * t) * np.exp(-22 * t)
    crunch = np.clip(np.random.normal(0, 0.75, len(t)), -0.9, 0.9)
    env = np.exp(-11 * t)
    return _to_sound(np.tanh(1.8 * (0.5 * bass + 0.35 * metal + 0.45 * crunch) * env))

def _build_boss_defeat_sound():
    sr = 44100
    duration = 0.90
    t = np.linspace(0, duration, int(sr * duration), False)
    boom = np.sin(2 * np.pi * np.linspace(140, 25, len(t)) * t) * np.exp(-3.2 * t)
    noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-4.5 * t)
    chord = (np.sin(2 * np.pi * 523.25 * t) + np.sin(2 * np.pi * 659.25 * t) + np.sin(2 * np.pi * 783.99 * t)) / 3.0
    chord_env = np.clip((t - 0.15) * 4.0, 0, 1) * np.exp(-2.2 * (t - 0.15))
    chord_env[t < 0.15] = 0
    return _to_sound((0.6 * boom + 0.4 * noise + 0.7 * chord * chord_env))

def _build_powerup_sound():
    sr = 44100
    duration = 0.35
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = np.linspace(400, 1200, len(t))
    tone = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(4 * np.pi * freq * t)
    sparkle = 0.3 * np.sin(2 * np.pi * 2400 * t) * np.sin(2 * np.pi * 32 * t)
    env = np.clip(1.0 - t / duration, 0, 1) ** 0.8
    return _to_sound((tone + sparkle) * env)

# Pre-synthesize sound bank if mixer is available
if SOUND_AVAILABLE:
    try:
        # Build 4 realistic punch variations
        _punch_bank = [_build_realistic_punch(i) for i in range(4)]
        _sounds["punch"] = _punch_bank[0]
        _sounds["critical"] = _build_critical_punch()
        _sounds["boss_hit"] = _build_boss_hit_sound()
        _sounds["boss_defeat"] = _build_boss_defeat_sound()
        _sounds["powerup"] = _build_powerup_sound()
    except Exception as e:
        print(f"[Sound FX Error] Pre-rendering waveforms failed: {e}")
        SOUND_AVAILABLE = False

# -----------------------------------------------------------------------------
# HARDWARE HAPTIC FEEDBACK (Arduino Serial Integration Stub)
# -----------------------------------------------------------------------------
_arduino_serial = None
HAPTIC_ENABLED = False

def init_haptic(port=None, baudrate=115200):
    """Attempt connection to Arduino microcontroller for haptic motor feedback."""
    global _arduino_serial, HAPTIC_ENABLED
    try:
        import serial
        if port:
            _arduino_serial = serial.Serial(port, baudrate, timeout=0.05)
            HAPTIC_ENABLED = True
            print(f"[Haptic] Connected to Arduino on {port}!")
    except Exception:
        HAPTIC_ENABLED = False

def trigger_haptic(event_name="punch"):
    """Send vibration pulse command to Arduino."""
    if HAPTIC_ENABLED and _arduino_serial:
        try:
            cmd = {"punch": b'P', "kiai": b'K', "shield": b'S', "boss": b'B', "powerup": b'U'}.get(event_name, b'P')
            _arduino_serial.write(cmd)
        except Exception:
            pass

def play_sfx(name, combo_idx=0):
    """Play procedural sound effect asynchronously with rate limiting & volume balancing.
    Silence is guaranteed for any unmapped or disabled audio event."""
    if not SOUND_AVAILABLE:
        return
    import time
    import random
    now = time.time()
    
    # Rate limit punch sounds (min 80ms gap) to prevent duplicate triggers
    if name in ("punch", "critical"):
        last_t = _last_sfx_time.get("punch", 0.0)
        if (now - last_t) < 0.080:
            return
        _last_sfx_time["punch"] = now

    try:
        if name == "punch":
            if _punch_bank:
                snd = random.choice(_punch_bank)
                snd.set_volume(0.92)
                snd.play()
            elif "punch" in _sounds:
                _sounds["punch"].play()
        elif name in _sounds:
            _sounds[name].play()
    except Exception:
        pass
