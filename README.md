# 🥊 Shadow-Boxer: Full-Body Kinetic Controller & AR Boxer

> **Hackathon Track:** Beginners Track — *The Exploration Arena*  
> **Key Special Awards Targeted:** *Built in a Cave with a Box of Scraps*, *Most Creative ML Use*, *People's Choice*

---

## 🌟 Overview
**Shadow-Boxer** is a zero-controller, real-time Human-Computer Interface (HCI) and Augmented Reality (AR) boxing game that turns any standard laptop webcam into a full-body motion controller. 

Using **Google MediaPipe BlazePose**, it tracks skeletal landmarks at **30–60 FPS directly on local CPU / Integrated Graphics** without requiring an external GPU, specialized sensors, or cloud APIs.

```
       [Webcam 640x480 @ 30-60 FPS]
                   │
                   ▼
     [Google MediaPipe PoseLandmarker]
       (Extracts 33 Skeletal Joints)
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
  [Wrists (15, 16)]    [Nose (0) & Head]
  Punch Collision,     Dodge / Ducking
  Velocity & Combo     Laser Sweeps
         │                   │
         └─────────┬─────────┘
                   ▼
       [AR Game Engine (OpenCV)]
    - Floating Hitboxes & Neon Pads
    - Particle Spark Explosions
    - Real-Time Punch Velocity (km/h)
    - Dynamic Combo Multiplier
    - Post-Round Workout Analytics
```

---

## ⚡ Features
- **Zero-Latency Kinetic Controls:** Left hand (Cyan) and Right hand (Red) punch recognition with glowing AR boxing gloves.
- **Physical Dodge Mechanic:** Full-body kinetic engagement — players must physically squat/duck under sweeping laser beams to avoid penalties.
- **Punch Velocity Physics:** Measures wrist displacement $(\Delta d / \Delta t)$ per frame to compute simulated punch impact speed in km/h.
- **Particle System:** Procedural particle spark bursts trigger upon every successful target punch.
- **Workout Analytics:** Post-match summary calculates score, punch count, peak velocity, dodges, and estimated calories burned.
- **100% Offline & Private:** Video frames never leave your local machine.

---

## 🚀 Quickstart

### 1. Requirements
- Python 3.9+
- Laptop webcam

### 2. Install Dependencies
```bash
pip install opencv-python mediapipe numpy
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
