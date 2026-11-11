import os
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from importlib.machinery import SourceFileLoader

def test_arcade_launcher_init():
    mod = SourceFileLoader("arcade_launcher", "04_arcade_launcher.py").load_module()
    launcher = mod.ArcadeLauncher()
    assert launcher.card_boxer is not None
    assert launcher.card_fruit is not None
    assert os.path.exists(mod.BOXER_SCRIPT)
    assert os.path.exists(mod.FRUIT_SCRIPT)
    pygame.quit()
