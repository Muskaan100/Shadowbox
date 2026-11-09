import numpy as np

# -----------------------------------------------------------------------------
# SHADOW-BOXER HIGH-FIDELITY PROCEDURAL BOXING AUDIO SYNTHESIZER
# Generates realistic heavy boxing punch impacts, leather slaps, sub-bass thuds,
# air whooshes, critical hits, and arcade cues purely in memory with ZERO external files!
# -----------------------------------------------------------------------------

SOUND_AVAILABLE = False
_sounds = {}
_punch_bank = []
_last_sfx_time = {}

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(16)  # High polyphony for simultaneous punch & ambience
    SOUND_AVAILABLE = True
except Exception as e:
    print(f"[Sound FX Warning] Could not initialize pygame.mixer: {e}. Running in silent mode.")

def _to_sound(audio_mono, sample_rate=44100, volume=0.9):
    """Normalize and convert 1D float numpy array into 16-bit stereo pygame Sound."""
    import pygame
    max_val = np.max(np.abs(audio_mono))
    if max_val > 0:
        audio_mono = audio_mono / max_val
    audio_int = (audio_mono * 32767 * volume).astype(np.int16)
    stereo = np.column_stack((audio_int, audio_int))
    return pygame.sndarray.make_sound(stereo)

# -----------------------------------------------------------------------------
# 1. REALISTIC BOXING PUNCH IMPACT BANK (Heavy Bag / Glove Impact Physics)
# Physical Model:
# - Initial Transient: 0-15ms snappy leather-on-leather crack (800-1600 Hz)
# - Mid Body Thud: 15-70ms resonant compression pitch sweep (180 -> 75 Hz)
# - Sub-Bass Impulse: 30-140ms deep 45-60 Hz chest-thumping visceral boom
# - Soft-clipping saturation (np.tanh) for natural acoustic compression
# -----------------------------------------------------------------------------
def _build_realistic_punch(variation=0):
    sr = 44100
    dur = 0.14 + (variation * 0.015)
    t = np.linspace(0, dur, int(sr * dur), False)
    
    # Variation parameters
    crack_freqs = [1450, 1200, 1600, 1350]
    sub_freqs = [56, 48, 62, 52]
    mid_starts = [220, 195, 240, 210]
    mid_ends = [80, 72, 88, 75]
    
    cf = crack_freqs[variation % 4]
    sf = sub_freqs[variation % 4]
    ms = mid_starts[variation % 4]
    me = mid_ends[variation % 4]
    
    # 1. Leather crack transient (initial snap)
    crack = np.sin(2 * np.pi * cf * t) * np.exp(-95 * t)
    noise_burst = np.random.uniform(-0.55, 0.55, len(t)) * np.exp(-110 * t)
    
    # 2. Resonant mid-body punch (downward pitch compression)
    body_pitch = np.linspace(ms, me, len(t))
    body_tone = np.sin(2 * np.pi * body_pitch * t) * np.exp(-22 * t)
    
    # 3. Visceral Sub-bass thump (physical weight)
    sub_bass = np.sin(2 * np.pi * sf * t) * np.exp(-13 * t)
    
    # 4. Analog tape saturation / soft clipping
    raw = 0.35 * crack + 0.28 * noise_burst + 0.45 * body_tone + 0.75 * sub_bass
    wave = np.tanh(1.85 * raw)
    return _to_sound(wave, volume=0.88)

def _build_critical_punch():
    """Heavy explosive impact for KIAI / Battle Cry power punches."""
    sr = 44100
    dur = 0.38
    t = np.linspace(0, dur, int(sr * dur), False)
    # Violent leather whip crack + massive 38Hz sub-bass shockwave
    whip = np.sin(2 * np.pi * 1850 * t) * np.exp(-110 * t)
    distortion = np.clip(np.random.normal(0, 0.75, len(t)), -0.9, 0.9) * np.exp(-40 * t)
    sub_boom = np.sin(2 * np.pi * np.linspace(110, 36, len(t)) * t) * np.exp(-6.5 * t)
    wave = np.tanh(2.2 * (0.45 * whip + 0.35 * distortion + 0.9 * sub_boom))
    return _to_sound(wave, volume=0.98)

def _build_target_destroy_sound():
    """Satisfying impact pop when a target is smashed and cleared."""
    sr = 44100
    dur = 0.20
    t = np.linspace(0, dur, int(sr * dur), False)
    thud = np.sin(2 * np.pi * np.linspace(190, 55, len(t)) * t) * np.exp(-19 * t)
    shatter_freq = np.linspace(1750, 280, len(t))
    shatter_tone = np.sin(2 * np.pi * shatter_freq * t) * np.exp(-30 * t)
    shatter_noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-26 * t)
    wave = np.tanh(1.7 * (0.6 * thud + 0.35 * shatter_tone + 0.3 * shatter_noise))
    return _to_sound(wave, volume=0.85)

def _build_whoosh_sound():
    """Air displacement swoosh sound for missed fast punches."""
    sr = 44100
    dur = 0.17
    t = np.linspace(0, dur, int(sr * dur), False)
    # Bandpass swept resonant noise
    noise = np.random.uniform(-0.45, 0.45, len(t))
    center_freq = 190 + 340 * np.sin(np.pi * t / dur)
    modulator = np.sin(2 * np.pi * center_freq * t)
    env = np.sin(np.pi * t / dur) ** 1.8
    wave = noise * modulator * env
    return _to_sound(wave, volume=0.55)

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
    freq = 550 + 250 * np.sin(2 * np.pi * 12 * t)
    saw = 2 * (t * freq - np.floor(0.5 + t * freq))
    env = np.clip(1.5 * np.sin(np.pi * t / duration), 0, 1)
    return _to_sound(saw * env * 0.6)

def _build_combo_chimes():
    sr = 44100
    duration = 0.16
    t = np.linspace(0, duration, int(sr * duration), False)
    env = np.exp(-11 * t)
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
    bell = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1760 * t)) * np.exp(-4 * t)
    return _to_sound(bell)

def _build_powerup_sound():
    sr = 44100
    duration = 0.38
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = np.linspace(400, 1200, len(t))
    tone = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(4 * np.pi * freq * t)
    sparkle = 0.3 * np.sin(2 * np.pi * 2400 * t) * np.sin(2 * np.pi * 32 * t)
    env = np.clip(1.0 - t / duration, 0, 1) ** 0.8
    return _to_sound((tone + sparkle) * env)

def _build_boss_spawn_sound():
    sr = 44100
    duration = 0.85
    t = np.linspace(0, duration, int(sr * duration), False)
    base_freq = 95 - 25 * (t / duration)
    vibrato = 12 * np.sin(2 * np.pi * 6.5 * t)
    horn = np.sin(2 * np.pi * (base_freq + vibrato) * t)
    horn += 0.5 * np.sin(4 * np.pi * (base_freq + vibrato) * t)
    env = np.minimum(t * 12.0, 1.0) * np.exp(-1.8 * t)
    return _to_sound(horn * env * 0.9)

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
    duration = 0.95
    t = np.linspace(0, duration, int(sr * duration), False)
    boom = np.sin(2 * np.pi * np.linspace(140, 25, len(t)) * t) * np.exp(-3.2 * t)
    noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-4.5 * t)
    chord = (np.sin(2 * np.pi * 523.25 * t) + np.sin(2 * np.pi * 659.25 * t) + np.sin(2 * np.pi * 783.99 * t)) / 3.0
    chord_env = np.clip((t - 0.15) * 4.0, 0, 1) * np.exp(-2.2 * (t - 0.15))
    chord_env[t < 0.15] = 0
    return _to_sound((0.6 * boom + 0.4 * noise + 0.7 * chord * chord_env))

# Pre-synthesize sound bank if mixer is available
if SOUND_AVAILABLE:
    try:
        # Build 4 realistic punch variations
        _punch_bank = [_build_realistic_punch(i) for i in range(4)]
        _sounds["punch"] = _punch_bank[0]
        _sounds["critical"] = _build_critical_punch()
        _sounds["destroy"] = _build_target_destroy_sound()
        _sounds["whoosh"] = _build_whoosh_sound()
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
    except Exception:
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
    """Play procedural sound effect asynchronously with rate limiting & volume balancing."""
    if not SOUND_AVAILABLE:
        return
    import time
    import random
    now = time.time()
    
    # Rate limit punch sounds (min 60ms gap) to prevent audio blowout on rapid hits
    if name in ("punch", "whoosh"):
        last_t = _last_sfx_time.get(name, 0.0)
        if (now - last_t) < 0.065:
            return
        _last_sfx_time[name] = now

    try:
        if name == "punch":
            # Select random variation from the 4 realistic punch bank
            if _punch_bank:
                snd = random.choice(_punch_bank)
                vol = random.uniform(0.85, 1.0)
                snd.set_volume(vol)
                snd.play()
            elif "punch" in _sounds:
                _sounds["punch"].play()
        elif name == "combo":
            chimes = _sounds.get("chimes", [])
            if chimes:
                idx = min(len(chimes) - 1, max(0, combo_idx - 1))
                chimes[idx].play()
        elif name in _sounds:
            _sounds[name].play()
    except Exception:
        pass
