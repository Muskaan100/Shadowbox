import os
import sys
import time
import pytest

# Use dummy video and audio drivers for headless test
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from fruit_ninja_game import FruitNinjaGame

def test_fruit_ninja_game_headless_lifecycle():
    # Instantiate game
    game = FruitNinjaGame(use_fullscreen=False)
    assert game.state == "MENU"
    
    # Start classic game
    game.start_game("CLASSIC")
    assert game.state == "COUNTDOWN"
    assert game.mode == "CLASSIC"
    assert game.lives == 3
    assert game.score == 0

    # Advance countdown
    game.countdown_start = time.time() - 4.0
    game.update_countdown(0.016)
    assert game.state == "PLAYING"

    # Spawn a wave manually
    game.spawner.time_to_next_wave = 0.0
    wave = game.spawner.get_wave(mode="CLASSIC", dt=0.016)
    game.active_fruits.extend(wave)
    assert len(game.active_fruits) > 0

    # Simulate slicing the first fruit
    target_fruit = game.active_fruits[0]
    initial_score = game.score
    game.slice_fruit(target_fruit)
    assert target_fruit.is_sliced is True
    assert game.total_sliced == 1
    assert game.score > initial_score
    assert len(game.sliced_halves) == 2
    assert len(game.particles) > 0

    # Simulate bomb hit in classic mode
    from fruit_physics import FruitObject
    bomb = FruitObject(999, "bomb", 500, 500, 0, 0, is_bomb=True)
    game.active_fruits.append(bomb)
    game.slice_fruit(bomb)
    assert game.bombs_hit == 1
    assert game.lives == 0
    assert game.state == "GAMEOVER"

    # Test game over and high scores
    assert game.high_scores["CLASSIC"] >= 0

    # Cleanup
    game.release_camera()
