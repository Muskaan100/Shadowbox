import cv2
import time
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# -----------------------------------------------------------------------------
# SHADOW-BOXER: STEP 1 - SKELETON & CAMERA TEST
# Runs 100% locally on CPU / Integrated Graphics using Google MediaPipe
# -----------------------------------------------------------------------------

# Path to the downloaded model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_lite.task")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Make sure pose_landmarker_lite.task is in the same folder.")

# 1. Initialize MediaPipe PoseLandmarker
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
detector = vision.PoseLandmarker.create_from_options(options)

# Pre-extract skeletal connections
CONNECTIONS = [(c.start, c.end) for c in vision.PoseLandmarksConnections.POSE_LANDMARKS]

# 2. Open Laptop Webcam
cap = cv2.VideoCapture(0)

# Set resolution to 640x480 for ultra-fast, smooth performance on laptops
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("\n" + "="*50)
print("  SHADOW-BOXER SKELETON TEST RUNNING!")
print("  - Stand back so the webcam can see your upper body.")
print("  - Press 'q' on your keyboard to quit.")
print("="*50 + "\n")

prev_time = time.time()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Warning: Camera frame could not be read.")
        break

    # Flip horizontally for a natural mirror view
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # MediaPipe requires RGB format
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # Detect body landmarks
    result = detector.detect(mp_image)

    # Draw skeleton if a person is detected
    if result.pose_landmarks and len(result.pose_landmarks) > 0:
        landmarks = result.pose_landmarks[0]
        pts = {}

        # Convert normalized coordinates (0 to 1) into pixel coordinates
        for idx, lm in enumerate(landmarks):
            px, py = int(lm.x * w), int(lm.y * h)
            pts[idx] = (px, py)

        # Draw bone connections (Neon Cyan lines)
        for start_idx, end_idx in CONNECTIONS:
            if start_idx in pts and end_idx in pts:
                cv2.line(frame, pts[start_idx], pts[end_idx], (255, 255, 0), 2)

        # Draw glowing joints
        for idx, (px, py) in pts.items():
            # Highlight wrists (15: Left Wrist, 16: Right Wrist) with glowing boxing gloves
            if idx == 15:
                cv2.circle(frame, (px, py), 28, (255, 200, 0), -1)  # Left hand Cyan
                cv2.circle(frame, (px, py), 34, (255, 255, 255), 2)
            elif idx == 16:
                cv2.circle(frame, (px, py), 28, (0, 80, 255), -1)   # Right hand Orange/Red
                cv2.circle(frame, (px, py), 34, (255, 255, 255), 2)
            elif idx == 0:
                # Keep face clear without distracting nose dots
                pass
            else:
                cv2.circle(frame, (px, py), 3, (0, 255, 255), -1)

        # Display detected wrist coordinates
        if 15 in pts and 16 in pts:
            cv2.putText(frame, f"L Wrist: {pts[15]}", (10, h - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(frame, f"R Wrist: {pts[16]}", (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Calculate and display FPS (Frames Per Second)
    curr_time = time.time()
    fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30
    prev_time = curr_time

    cv2.putText(frame, f"FPS: {int(fps)} (Local CPU)", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "Press 'Q' to Exit", (w - 180, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    cv2.imshow("Shadow-Boxer: Skeleton Test (Press Q to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()
