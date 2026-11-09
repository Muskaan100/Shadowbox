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
- **Procedural 8-Bit Arcade Audio Synthesizer:** Real-time multi-channel audio synthesis (`sound_fx.py`) that mathematically generates leather punches, explosive sub-bass Kiai booms, electric shield deflections, ascending pentatonic combo chimes, and fight bells with **zero external audio files**!
- **Multimodal "KIAI" Battle Cry:** Shouting or grunting while throwing a punch triggers a **5x Critical Power Strike** with dynamic screen shake, booming audio, and blazing golden particle bursts!
- **Multimodal "Clap" Sonic Forcefield:** Clapping your hands together (dual-wrist proximity + acoustic transient spike) projects a glowing **Cyan Electric Forcefield** with electric zap audio that parries laser hazards for **+75 Parry Points**!
- **Oriented Arcade Boxing Gloves:** Forearm vector tracking ($\vec{V} = \text{Wrist} - \text{Elbow}$) dynamically rotates stylized boxing gloves (knuckle padding, thumb, velcro strap, speed trails) in the direction of your punch.
- **Physical Dodge Hazard:** Full-body kinetic engagement — players can either physically squat/duck under sweeping laser beams or deflect them with the Sonic Shield.
- **Punch Velocity Physics:** Measures wrist displacement $(\Delta d / \Delta t)$ per frame to compute simulated punch impact speed in km/h.
- **Dynamic Audio HUD:** Real-time microphone volume bar that turns into a flashing `"KIAI READY!"` state when your voice reaches battle energy.
- **Workout Analytics:** Post-match summary calculates score, punch count, Kiai power strikes, laser deflections, peak velocity, dodges, and estimated calories burned.
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
