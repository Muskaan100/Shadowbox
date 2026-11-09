import numpy as np

# -----------------------------------------------------------------------------
# SHADOW-BOXER PROCEDURAL 8-BIT ARCADE SOUND SYNTHESIZER
# Generates all retro sound effects purely from mathematical waveforms (sine,
# frequency sweeps, noise, envelopes) in memory with ZERO external files!
# -----------------------------------------------------------------------------

SOUND_AVAILABLE = False
_sounds = {}

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SOUND_AVAILABLE = True
except Exception as e:
    print(f"[Sound FX Warning] Could not initialize pygame.mixer: {e}. Running in silent mode.")

def _to_sound(audio_mono, sample_rate=44100):
    """Normalize and convert 1D float numpy array into 16-bit stereo pygame Sound."""
    import pygame
    max_val = np.max(np.abs(audio_mono))
    if max_val > 0:
        audio_mono = audio_mono / max_val
    audio_int = (audio_mono * 32767 * 0.85).astype(np.int16)
    stereo = np.column_stack((audio_int, audio_int))
    return pygame.sndarray.make_sound(stereo)

def _build_punch_sound():
    sr = 44100
    duration = 0.11
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = np.linspace(340, 65, len(t))
    tone = np.sin(2 * np.pi * freq * t)
    noise = np.random.uniform(-0.4, 0.4, len(t))
    env = np.exp(-14 * t)
    return _to_sound((0.65 * tone + 0.35 * noise) * env)

def _build_kiai_sound():
    sr = 44100
    duration = 0.42
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = np.linspace(180, 35, len(t))
    bass_sub = np.sin(2 * np.pi * freq * t)
    distorted_noise = np.clip(np.random.normal(0, 0.6, len(t)), -0.8, 0.8)
    env = np.exp(-5.5 * t)
    return _to_sound((0.6 * bass_sub + 0.4 * distorted_noise) * env)

def _build_shield_sound():
    sr = 44100
    duration = 0.32
    t = np.linspace(0, duration, int(sr * duration), False)
    # FM Synthesis for metallic forcefield zap
    carrier = 900 * np.exp(-3 * t)
    modulator = 180 * np.sin(2 * np.pi * 35 * t)
    tone = np.sin(2 * np.pi * (carrier + modulator) * t)
    sparkle = np.sin(2 * np.pi * 1800 * t) * np.exp(-18 * t)
    env = np.exp(-7 * t)
    return _to_sound((0.7 * tone + 0.3 * sparkle) * env)

def _build_laser_sound():
    sr = 44100
    duration = 0.55
    t = np.linspace(0, duration, int(sr * duration), False)
    # Modulated siren
    freq = 550 + 250 * np.sin(2 * np.pi * 12 * t)
    saw = 2 * (t * freq - np.floor(0.5 + t * freq))
    env = np.clip(1.5 * np.sin(np.pi * t / duration), 0, 1)
    return _to_sound(saw * env * 0.6)

def _build_combo_chimes():
    sr = 44100
    duration = 0.16
    t = np.linspace(0, duration, int(sr * duration), False)
    env = np.exp(-11 * t)
    # Pentatonic notes: C5, D5, E5, G5, A5, C6
    pitches = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50]
    chimes = []
    for p in pitches:
        tone = np.sin(2 * np.pi * p * t) + 0.3 * np.sin(2 * np.pi * (p * 2) * t)
        chimes.append(_to_sound(tone * env))
    return chimes

def _build_start_sound():
    sr = 44100
    duration = 0.45
    t = np.linspace(0, duration, int(sr * duration), False)
    # Boxing fight bell (two-tone chime)
    bell = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1760 * t)) * np.exp(-4 * t)
    return _to_sound(bell)

def _build_powerup_sound():
    sr = 44100
    duration = 0.38
    t = np.linspace(0, duration, int(sr * duration), False)
    # Rising magical arpeggio sweep
    freq = np.linspace(400, 1200, len(t))
    tone = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(4 * np.pi * freq * t)
    sparkle = 0.3 * np.sin(2 * np.pi * 2400 * t) * np.sin(2 * np.pi * 32 * t)
    env = np.clip(1.0 - t / duration, 0, 1) ** 0.8
    return _to_sound((tone + sparkle) * env)

def _build_boss_spawn_sound():
    sr = 44100
    duration = 0.85
    t = np.linspace(0, duration, int(sr * duration), False)
    # Deep ominous cyber warhorn / klaxon
    base_freq = 95 - 25 * (t / duration)
    vibrato = 12 * np.sin(2 * np.pi * 6.5 * t)
    horn = np.sin(2 * np.pi * (base_freq + vibrato) * t)
    horn += 0.5 * np.sin(4 * np.pi * (base_freq + vibrato) * t)
    env = np.minimum(t * 12.0, 1.0) * np.exp(-1.8 * t)
    return _to_sound(horn * env * 0.9)

def _build_boss_hit_sound():
    sr = 44100
    duration = 0.18
    t = np.linspace(0, duration, int(sr * duration), False)
    # Heavy metallic crunch
    bass = np.sin(2 * np.pi * np.linspace(160, 40, len(t)) * t)
    metal = np.sin(2 * np.pi * 780 * t) * np.exp(-25 * t)
    crunch = np.clip(np.random.normal(0, 0.7, len(t)), -0.9, 0.9)
    env = np.exp(-12 * t)
    return _to_sound((0.5 * bass + 0.3 * metal + 0.4 * crunch) * env)

def _build_boss_defeat_sound():
    sr = 44100
    duration = 0.95
    t = np.linspace(0, duration, int(sr * duration), False)
    # Dramatic explosion transitioning into high triumph chord
    boom = np.sin(2 * np.pi * np.linspace(140, 25, len(t)) * t) * np.exp(-3.2 * t)
    noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-4.5 * t)
    # Triumph chord (Major triad)
    chord = (np.sin(2 * np.pi * 523.25 * t) + np.sin(2 * np.pi * 659.25 * t) + np.sin(2 * np.pi * 783.99 * t)) / 3.0
    chord_env = np.clip((t - 0.15) * 4.0, 0, 1) * np.exp(-2.2 * (t - 0.15))
    chord_env[t < 0.15] = 0
    return _to_sound((0.6 * boom + 0.4 * noise + 0.7 * chord * chord_env))

# Pre-synthesize sounds if mixer is available
if SOUND_AVAILABLE:
    try:
        _sounds["punch"] = _build_punch_sound()
        _sounds["kiai"] = _build_kiai_sound()
        _sounds["shield"] = _build_shield_sound()
        _sounds["laser"] = _build_laser_sound()
        _sounds["start"] = _build_start_sound()
        _sounds["chimes"] = _build_combo_chimes()
        _sounds["powerup"] = _build_powerup_sound()
        _sounds["boss_spawn"] = _build_boss_spawn_sound()
        _sounds["boss_hit"] = _build_boss_hit_sound()
        _sounds["boss_defeat"] = _build_boss_defeat_sound()
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
    except Exception as e:
        # Gracefully handle when Arduino is not plugged in
        HAPTIC_ENABLED = False

def trigger_haptic(event_name="punch"):
    """Send vibration pulse command ('P'=Punch, 'K'=Kiai, 'S'=Shield, 'B'=Boss) to Arduino."""
    if HAPTIC_ENABLED and _arduino_serial:
        try:
            cmd = {"punch": b'P', "kiai": b'K', "shield": b'S', "boss": b'B', "powerup": b'U'}.get(event_name, b'P')
            _arduino_serial.write(cmd)
        except Exception:
            pass

def play_sfx(name, combo_idx=0):
    """Play a procedural sound effect asynchronously."""
    if not SOUND_AVAILABLE:
        return
    try:
        if name == "combo":
            chimes = _sounds.get("chimes", [])
            if chimes:
                idx = min(len(chimes) - 1, max(0, combo_idx - 1))
                chimes[idx].play()
        elif name in _sounds:
            _sounds[name].play()
    except Exception:
        pass
