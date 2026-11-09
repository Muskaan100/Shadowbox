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

# Pre-synthesize sounds if mixer is available
if SOUND_AVAILABLE:
    try:
        _sounds["punch"] = _build_punch_sound()
        _sounds["kiai"] = _build_kiai_sound()
        _sounds["shield"] = _build_shield_sound()
        _sounds["laser"] = _build_laser_sound()
        _sounds["start"] = _build_start_sound()
        _sounds["chimes"] = _build_combo_chimes()
    except Exception as e:
        print(f"[Sound FX Error] Pre-rendering waveforms failed: {e}")
        SOUND_AVAILABLE = False

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
