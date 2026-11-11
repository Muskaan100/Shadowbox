import time
import numpy as np
import pytest
from hand_tracker import BladeTrail, HandData, HandTracker

def test_blade_trail():
    trail = BladeTrail(max_points=5, max_age=0.2)
    now = time.time()
    trail.add_point(100, 100, now)
    trail.add_point(150, 150, now + 0.05)
    
    assert len(trail.points) == 2
    assert trail.velocity > 0
    segs = trail.get_segments()
    assert len(segs) == 1

    # After aging past max_age
    trail.clean(now + 0.3)
    assert len(trail.points) == 0

def test_hand_data():
    hand = HandData("Right")
    assert not hand.is_present
    
    class DummyLM:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    # Create 21 dummy landmarks
    landmarks = [DummyLM(0.5, 0.5) for _ in range(21)]
    landmarks[8] = DummyLM(0.6, 0.4)  # Index tip
    
    now = time.time()
    hand.update(landmarks, 1000, 800, 0.95, now)
    
    assert hand.is_present
    assert hand.index_tip == (600.0, 320.0)
    assert hand.confidence == 0.95

    # Mark absent
    hand.mark_absent(now + 0.3)
    assert not hand.is_present

def test_hand_tracker_init_and_process():
    tracker = HandTracker()
    assert tracker.detector is not None

    # Process empty/black frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    left, right = tracker.process_frame(dummy_frame, 640, 480)
    assert not left.is_present
    assert not right.is_present
    assert not tracker.any_hand_present
