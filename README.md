# 🥊 Shadow-Boxer: Multimodal Kinetic & Acoustic AR Boxer

> **Hackathon Track:** Beginners Track — *The Exploration Arena*  
> **Key Special Awards Targeted:** *Most Creative ML Use*, *Over-Engineered Masterpiece*, *Built in a Cave with a Box of Scraps*

---

## 🌟 Overview
**Shadow-Boxer** is a zero-controller, real-time Human-Computer Interface (HCI) and Augmented Reality (AR) boxing game that fuses **Computer Vision (Skeletal Pose Tracking)** and **Acoustic DSP (Non-Verbal Battle Cry Recognition)** into a seamless multimodal combat engine.

Using **Google MediaPipe BlazePose** and real-time **RMS audio energy extraction**, it runs at **30–60 FPS directly on local CPU / Integrated Graphics** without requiring an external GPU, specialized hardware, or cloud APIs.

```
 [Webcam 640x480 @ 60 FPS]          [Laptop Microphone Stream]
             │                                   │
             ▼                                   ▼
[Google MediaPipe PoseLandmarker]     [Real-Time RMS Acoustic DSP]
  (Extracts 33 Skeletal Joints)         (Kiai / Battle Cry Energy)
             │                                   │
      ┌──────┴──────┐                            │
      ▼             ▼                            │
 [Wrists 15/16]  [Head Ducking]                  │
  Punch Vectors   Laser Dodges                   │
      │             │                            │
      └──────┬──────┘                            │
             ▼                                   ▼
        ┌─────────────────────────────────────────────┐
        │       MULTIMODAL AR GAME ARBITER            │
        │ - Standard Punch: +10 pts * Combo           │
        │ - Punch + Shout: 5x KIAI CRITICAL (+50 pts) │
        │ - Dynamic Screen Shake & Golden Explosions  │
        │ - Laser Dodge Hazard & Workout Analytics    │
        └─────────────────────────────────────────────┘
```

---

## ⚡ Features
- **Authentic Professional Boxing Gloves (Reference Match):** Redesigned from scratch to match professional 2D boxing gloves — rounded convex striking surface, curved ergonomic thumb with safety webbing, thick padded wrist cuff with velcro strap, double vertical stitch detailing, rolled bottom hem, soft leather specular highlights, and natural first-person forward perspective.
- **Pure Punch-Only Audio (Zero Background Noise):** Complete audio silence during normal gameplay with zero ambient humming, loops, or movement sounds. Sound plays **only** upon successful physical impact against a target circle.
- **Realistic Heavy Bag Impact Audio Bank:** 4 procedurally synthesized physical punch variations modeling leather slap transients (980–1400 Hz), foam compression mid-thud (165 $\to$ 58 Hz), and deep chest-thumping sub-bass (46–58 Hz) with analog soft-clipping tape saturation.
- **Physical Punch Animations & First-Person Perspective:** Dynamic biomechanical extension, perspective zoom (+22% scale as fists punch toward the camera), fist pronation (inward rotation), and snappy 80ms impact spring recoil on target connection.
- **Enlarged Detected Hand Tracking Anchors:** High-visibility luminous wrist tracking indicators coupled with forward-projected first-person gloves.
- **Full-Screen Arcade Gameplay:** Launches natively in borderless full-screen (`cv2.WINDOW_FULLSCREEN`) with dynamic responsive UI scaling across all monitor resolutions and aspect ratios. Toggle anytime with `F`!
- **High-Performance Low-Latency CPU Pipeline:** MediaPipe pose estimation runs on an optimized downsampled stream paired with Exponential Moving Average (EMA) sub-pixel smoothing, delivering steady 45–60 FPS and zero perceptible lag even on modest laptops!
- **Continuous Swept Collision Detection:** Mathematical line-segment sweeping prevents fast punches from tunneling through targets, making punch registration forgiving, natural, and responsive.
- **Mechanical Mini-Boss Waves:** Multi-hit armored bosses (*MECHA-BRUTE* and *CYBER-TITAN*) emerge with rotating spiked energy shields, floating segmented health bars, audio alarms, and huge point bounties.
- **Glowing Power-Up Orbs:** Dynamic power-ups spawn throughout the match with live HUD countdown bars:
  - 🔥 **Double Damage (2X DMG):** Punches inflict 2x damage on mini-bosses.
  - ❄️ **Slow Motion (SLOW-MO):** Decelerates lasers and hazards.
  - 🌟 **Score Multiplier (3X SCORE):** Triples all earned points.
  - ⚡ **Rapid Fury (FURY):** Expands glove hitboxes by +55% with blazing glove fire.
  - 🛡️ **Titanium Shield (SHIELD):** Auto-deflects hazards with total immunity.
- **Multimodal "KIAI" Battle Cry:** Shouting or grunting while throwing a punch triggers a **5x Critical Power Strike** with dynamic screen shake, booming audio, and blazing golden particle bursts!
- **Multimodal "Clap" Sonic Forcefield:** Clapping your hands together (dual-wrist proximity + acoustic transient spike) projects a glowing **Cyan Electric Forcefield** with electric zap audio that parries laser hazards for **+75 Parry Points**!
- **Physical Dodge Hazard:** Full-body kinetic engagement — players can physically squat/duck under sweeping laser beams or deflect them with the Sonic Shield.
- **Pause & Resume Controls:** Press `P` anytime to pause the action with a sleek translucent HUD card.
- **Hardware Haptic Integration Ready:** Includes plug-and-play serial stubs to drive ₹200 Arduino vibration motors and LED strips on punches, Kiai strikes, and shield parries.
- **Workout Analytics:** Post-match summary calculates score, punch count, mini-bosses defeated, power-ups collected, Kiai power strikes, laser deflections, peak velocity, dodges, and estimated calories burned.
- **100% Offline & Private:** Zero GPU needed; runs on consumer CPU with TensorFlow Lite XNNPACK delegates.

---

## 🚀 Quickstart

### 1. Requirements
- Python 3.9+
- Laptop webcam

### 2. Install Dependencies
```bash
pip install opencv-python mediapipe numpy pygame
```

### 3. Run the Game
* **Step 1: Test your webcam & skeleton detection**
  ```bash
  python 01_test_skeleton.py
  ```
  *(Press `Q` to exit)*

* **Step 2: Launch the full AR Boxing Game!**
  ```bash
  python 02_shadow_boxer_game.py
  ```
  *(Press `SPACE` to start, hit targets, duck lasers, `R` to restart, `Q` to exit)*

---

## 🛠️ Architecture & Hardware Optimization
- **Model:** `pose_landmarker_lite.task` (~5.7 MB)
- **Runtime:** TensorFlow Lite XNNPACK CPU delegate
- **Resolution:** Frame scaled to $640 \times 480$ for low memory bandwidth and steady 60 FPS on integrated Intel UHD/Iris or AMD Radeon graphics.
