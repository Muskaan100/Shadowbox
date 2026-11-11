# 🕹️ SHADOWBOX: Dual-Game AR Arcade

> **Zero-Controller, Real-Time Computer Vision Arcade Games for Laptop Webcams**  
> Built with **Python**, **OpenCV**, **MediaPipe**, **NumPy**, and **Pygame**.  
> Runs at **50–60 FPS entirely offline on local CPU / Integrated Graphics**.

---

## 🌟 The Arcade Experience

**Shadowbox** features two complete, controller-free AR arcade games operated entirely through your physical body and natural hand motions:

```
                                  ┌─────────────────────────────┐
                                  │    04_arcade_launcher.py    │
                                  │   (Arcade Selection Hub)    │
                                  └──────────────┬──────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
        ┌───────────────────────────────┐                 ┌───────────────────────────────┐
        │       1. SHADOW-BOXER         │                 │       2. FRUIT NINJA AR       │
        │    02_shadow_boxer_game.py    │                 │    03_fruit_ninja_game.py     │
        ├───────────────────────────────┤                 ├───────────────────────────────┤
        │ • Skeletal Pose Tracking      │                 │ • Dual Hand Landmark Tracking │
        │ • 33 BlazePose Keypoints      │                 │ • 21 Hand Joints (Fingertips) │
        │ • Microphone Acoustic Kiai    │                 │ • Continuous Swept Slicing    │
        │ • Mecha Mini-Boss Waves       │                 │ • Sliced Halves & Splatters   │
        │ • Kinetic Laser Ducking       │                 │ • Bombs, Combos, Slow-Mo      │
        └───────────────────────────────┘                 └───────────────────────────────┘
```

---

## 🍉 Game 2: Fruit Ninja AR (New Game Mode)

**Fruit Ninja AR** brings the legendary fruit-slicing gameplay to your webcam without needing a touchscreen, mouse, or controller. Stand in front of your camera, raise your hands, and slice flying fruits out of the air with glowing laser blade streaks!

### ⚡ Core Fruit Ninja Features:
- **Dual-Hand Tracking:** Independently tracks both left and right hands using Google MediaPipe HandLandmarker Tasks API.
  - Left Hand: **Electric Cyan Katana Blade**
  - Right Hand: **Flaming Amber/Ruby Katana Blade**
- **Continuous Swept Segment Anti-Tunneling:** Mathematical line-segment Euclidean projection checks slices between consecutive frames, guaranteeing fast ninja swipes never tunnel through targets.
- **Physical Fruit Halves & Splatters:** Slicing cleanly splits fruits into two spinning halves that fly outward with opposing velocities and gravitational acceleration, accompanied by juicy droplet particles and cutting board decals.
- **Three Distinct Game Modes:**
  - 🍉 **Classic Mode:** 60-second timer, 3 lives (missed fruits cost a life), bombs included.
  - 🍊 **Zen Mode:** Relaxed slicing with NO bombs, no life penalties, pure combo meditation.
  - 🌟 **Arcade Mode:** 60-second high-density fruit frenzy with special powers and non-lethal bomb penalties (-25 points).
- **Special Objects & Hazards:**
  - 💣 **Classic Iron Bombs:** Distinct cartoon bomb with burning spark fuse. Slicing causes an explosive shockwave, screen flash, and violent screen shake!
  - 🌟 **Golden Bonus Fruit:** Glowing metallic gold fruit worth +30 points and fireworks.
  - ❄️ **Frozen Slow-Mo Fruit:** Freezes the arena, decelerating physics to $0.45\times$ speed for 4.5 seconds with frosty trails.
- **Dynamic Combo System:** Slicing multiple fruits in a single swipe triggers ascending musical chord arpeggios (2x to 7x) and bonus combo points.
- **Interactive Menu Targets:** Physically slice the floating watermelon, orange, golden fruit, or bomb on the Main Menu to pick your game mode!
- **Persistent High Scores:** Local JSON records (`fruit_ninja_high_score.json`) save personal records across all game modes.

---

## 🥊 Game 1: Shadow-Boxer (AR Boxing)

A multimodal kinetic combat game fusing skeletal pose tracking and acoustic voice recognition:
- **Skeletal Pose Tracking:** Tracks 33 joints using MediaPipe Pose Landmarker Lite.
- **Multimodal "KIAI" Battle Cry:** Shouting or grunting while throwing a punch activates a **5x Critical Strike** with dynamic golden explosions.
- **Sonic Clap Forcefield:** Clapping your hands together projects an electric forcefield that parries incoming lasers.
- **Armored Mini-Bosses:** Face off against *MECHA-BRUTE* and *CYBER-TITAN* with multi-segmented health bars and spiked shields.
- **Workout Analytics:** Tracks punch count, peak velocity, dodges, and estimated calories burned.

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.9 – 3.11
- Laptop webcam and microphone
- Windows, macOS, or Linux

### 2. Install Dependencies
```bash
# Clone the repository
git clone https://github.com/Noobi-Programmer/Shadowbox.git
cd Shadowbox

# Install required packages
pip install opencv-python mediapipe numpy pygame sounddevice pytest pillow
```

### 3. Launch the Games

* **Launch the Unified Arcade Portal (Recommended):**
  ```bash
  python 04_arcade_launcher.py
  ```
  *(Press `1` for Boxing, `2` for Fruit Ninja, or `Q` to quit)*

* **Or Launch Fruit Ninja directly:**
  ```bash
  python 03_fruit_ninja_game.py
  ```
  *(Optional: Add `--fullscreen` for borderless fullscreen)*

* **Or Launch Shadow-Boxer directly:**
  ```bash
  python 02_shadow_boxer_game.py
  ```

* **Test your camera & MediaPipe skeleton detection:**
  ```bash
  python 01_test_skeleton.py
  ```

---

## 🎮 Fruit Ninja In-Game Controls & Shortcuts

| Action | Physical Gesture / Key |
|---|---|
| **Slice Fruits & Menus** | Swipe left or right hand in front of webcam |
| **Select Mode (Menu)** | Physically slice the floating labeled fruit target |
| **Quick Start Mode** | Press `1` (Classic), `2` (Zen), `3` (Arcade), or `SPACE` |
| **Pause / Resume** | Press `P` |
| **Restart Match** | Press `R` |
| **Toggle Camera Blend** | Press `B` (Cycles between Dojo Wood and AR Webcam overlay) |
| **Toggle Audio Mute** | Press `M` |
| **Return to Menu / Quit** | Press `ESC` or `Q` |

---

## ⚡ Performance & Benchmarks

Benchmarked on local CPU / Integrated Graphics (no dedicated GPU required):

| Pipeline Stage | Measured Latency | Measured Throughput |
|---|---|---|
| **MediaPipe Hand Landmarker** ($384 \times 288$ stream) | **17.9 ms** | **55.9 FPS** |
| **Physics & Particle Simulation** (195 entities) | **0.095 ms** | **10,500+ FPS** |
| **Engine Simulation & Slicing Loop** | **0.07 ms** | **14,000+ FPS** |
| **Camera Buffer Conversion** | **0.057 ms** | **17,000+ FPS** |

Detailed benchmark methodology is recorded in [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md).

---

## 🧪 Testing Suite

Run the automated test suite covering swept collision, physics, MediaPipe hand tracking, and launcher integration:

```bash
pytest tests/ -v
```

All 10 tests run in $< 5$ seconds. Detailed test cases and results are recorded in [TEST_REPORT.md](TEST_REPORT.md).

---

## 📜 Asset Credits & Licenses

All assets are 100% free, open-source, CC0 (Public Domain), or procedurally generated:
- **Audio & Particle FX:** Kenney (Kenney.nl) — CC0 1.0 Universal
- **Retro Fruit Sprites:** Belohlavek (OpenGameArt.org) — CC0 1.0 Universal
- **High-Res Fruit & Splatter Sprites:** Procedural generator (`generate_fruit_ninja_assets.py`)
- **Procedural Audio Synthesizer:** Pure NumPy DSP (`fruit_sound_fx.py`)
- **ML Models:** Google MediaPipe (`hand_landmarker.task`, `pose_landmarker_lite.task`) — Apache 2.0

Complete attribution and source links are documented in [ASSET_CREDITS.md](ASSET_CREDITS.md).
