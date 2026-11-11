"""
=============================================================================
SHADOWBOX ARCADE CABINET LAUNCHER (04_arcade_launcher.py)
Unified Multi-Game Selection Portal
=============================================================================
Select and play:
1. 🥊 SHADOW-BOXER: Kinetic & Acoustic AR Boxing (Pose Tracking + Voice Kiai)
2. 🍉 FRUIT NINJA: Hand Gesture Fruit Slicing (MediaPipe Hands + Blade Trails)
"""

import os
import sys
import time
import json
import subprocess
import pygame

WINDOW_TITLE = "SHADOWBOX: ARCADIA MULTI-GAME PORTAL"
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

BOXER_SCRIPT = os.path.join(os.path.dirname(__file__), "02_shadow_boxer_game.py")
FRUIT_SCRIPT = os.path.join(os.path.dirname(__file__), "03_fruit_ninja_game.py")
FRUIT_SCORES_FILE = os.path.join(os.path.dirname(__file__), "fruit_ninja_high_score.json")
BOXER_SCORES_FILE = os.path.join(os.path.dirname(__file__), "high_score.json")

def get_high_scores():
    fruit_best = 0
    boxer_best = 0
    if os.path.exists(FRUIT_SCORES_FILE):
        try:
            with open(FRUIT_SCORES_FILE, "r") as f:
                d = json.load(f)
                fruit_best = max(d.get("CLASSIC", 0), d.get("ARCADE", 0))
        except Exception:
            pass
    if os.path.exists(BOXER_SCORES_FILE):
        try:
            with open(BOXER_SCORES_FILE, "r") as f:
                d = json.load(f)
                boxer_best = d.get("high_score", 0)
        except Exception:
            pass
    return boxer_best, fruit_best

class ArcadeLauncher:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("impact", 64)
        self.font_sub = pygame.font.SysFont("trebuchetms", 22)
        self.font_card_title = pygame.font.SysFont("impact", 36)
        self.font_card_desc = pygame.font.SysFont("trebuchetms", 18)
        self.font_badge = pygame.font.SysFont("trebuchetms", 16, bold=True)
        self.font_btn = pygame.font.SysFont("impact", 26)

        # Card geometries
        card_w, card_h = 480, 420
        y_pos = 180
        self.card_boxer = pygame.Rect(110, y_pos, card_w, card_h)
        self.card_fruit = pygame.Rect(690, y_pos, card_w, card_h)
        
        self.selected_game = 0  # 0: None, 1: Boxer, 2: Fruit
        self.hovered_card = 0

    def launch_game(self, script_path):
        """Cleanly releases launcher resources and launches chosen game subprocess."""
        print(f"[Launcher] Handing off system resources to {os.path.basename(script_path)}...")
        
        # Display launching screen
        self.screen.fill((10, 10, 15))
        msg = self.font_card_title.render("INITIALIZING WEBCAM PIPELINE...", True, (255, 215, 0))
        self.screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H//2 - 20))
        pygame.display.flip()

        # Temporarily close pygame window to yield screen and audio resources
        pygame.display.quit()
        time.sleep(0.3)

        # Execute selected game in python environment
        cmd = [sys.executable, script_path]
        try:
            subprocess.run(cmd, check=False)
        except Exception as e:
            print(f"[Launcher Error] Failed to execute {script_path}: {e}")

        # Re-initialize launcher window on return
        time.sleep(0.3)
        pygame.display.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(WINDOW_TITLE)
        print("[Launcher] Returned to Arcade Launcher.")

    def run(self):
        running = True
        while running:
            boxer_best, fruit_best = get_high_scores()
            mouse_pos = pygame.mouse.get_pos()
            
            # Hover detection
            if self.card_boxer.collidepoint(mouse_pos):
                self.hovered_card = 1
            elif self.card_fruit.collidepoint(mouse_pos):
                self.hovered_card = 2
            else:
                self.hovered_card = 0

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                        running = False
                    elif event.key in [pygame.K_1, pygame.K_b]:
                        self.launch_game(BOXER_SCRIPT)
                    elif event.key in [pygame.K_2, pygame.K_f]:
                        self.launch_game(FRUIT_SCRIPT)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.hovered_card == 1:
                        self.launch_game(BOXER_SCRIPT)
                    elif self.hovered_card == 2:
                        self.launch_game(FRUIT_SCRIPT)

            # -----------------------------------------------------------------
            # RENDER
            # -----------------------------------------------------------------
            self.screen.fill((14, 16, 22))

            # Header Glow Title
            title = self.font_title.render("SHADOWBOX ARCADE", True, (255, 215, 0))
            self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 45))
            
            sub = self.font_sub.render("ZERO-CONTROLLER WEBCAM COMPUTER VISION ARCADE PORTAL", True, (180, 200, 220))
            self.screen.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 125))

            # -----------------------------------------------------------------
            # CARD 1: SHADOW-BOXER
            # -----------------------------------------------------------------
            b_border_col = (255, 60, 60) if self.hovered_card == 1 else (70, 75, 95)
            pygame.draw.rect(self.screen, (22, 24, 34), self.card_boxer, border_radius=16)
            pygame.draw.rect(self.screen, b_border_col, self.card_boxer, 3 if self.hovered_card == 1 else 1, border_radius=16)

            # Badge
            badge1 = self.font_badge.render("TRACK 1: BEGINNERS ARENA", True, (255, 100, 100))
            self.screen.blit(badge1, (self.card_boxer.x + 28, self.card_boxer.y + 24))

            # Title
            t1 = self.font_card_title.render("🥊 SHADOW-BOXER", True, (255, 255, 255))
            self.screen.blit(t1, (self.card_boxer.x + 28, self.card_boxer.y + 50))

            # Features list
            features_boxer = [
                "• Multimodal AR Boxing Combat",
                "• MediaPipe BlazePose Skeletal Tracking",
                "• Non-Verbal Acoustic 'KIAI' Battle Cry (5x DMG)",
                "• Dynamic Sonic Shield Laser Deflection",
                "• Mechanical Mini-Boss Waves & Health Bars",
                "• Dynamic Screen Shake & Procedural Punch Audio",
                f"• High Score Record: {boxer_best} pts"
            ]
            by = self.card_boxer.y + 110
            for line in features_boxer:
                col = (255, 215, 0) if "High Score" in line else (200, 205, 220)
                txt = self.font_card_desc.render(line, True, col)
                self.screen.blit(txt, (self.card_boxer.x + 28, by))
                by += 32

            # Play Button Box
            btn_boxer = pygame.Rect(self.card_boxer.x + 28, self.card_boxer.bottom - 68, self.card_boxer.w - 56, 46)
            btn_col = (220, 45, 45) if self.hovered_card == 1 else (45, 50, 70)
            pygame.draw.rect(self.screen, btn_col, btn_boxer, border_radius=8)
            btn1_t = self.font_btn.render("PLAY BOXING [PRESS 1]", True, (255, 255, 255))
            self.screen.blit(btn1_t, (btn_boxer.centerx - btn1_t.get_width()//2, btn_boxer.centery - btn1_t.get_height()//2))

            # -----------------------------------------------------------------
            # CARD 2: FRUIT NINJA
            # -----------------------------------------------------------------
            f_border_col = (40, 215, 60) if self.hovered_card == 2 else (70, 75, 95)
            pygame.draw.rect(self.screen, (22, 24, 34), self.card_fruit, border_radius=16)
            pygame.draw.rect(self.screen, f_border_col, self.card_fruit, 3 if self.hovered_card == 2 else 1, border_radius=16)

            # Badge
            badge2 = self.font_badge.render("NEW GAME MODE: HIGH PRECISION", True, (60, 220, 100))
            self.screen.blit(badge2, (self.card_fruit.x + 28, self.card_fruit.y + 24))

            # Title
            t2 = self.font_card_title.render("🍉 FRUIT NINJA AR", True, (255, 255, 255))
            self.screen.blit(t2, (self.card_fruit.x + 28, self.card_fruit.y + 50))

            # Features list
            features_fruit = [
                "• Natural Hand & Fingertip Slicing",
                "• MediaPipe HandLandmarker Dual-Hand Tracking",
                "• Continuous Swept Segment Anti-Tunneling",
                "• Sliced Fruit Halves & Dynamic Juice Splatters",
                "• Bombs with Screen Shake & White Flash",
                "• 3 Modes: Classic (60s), Zen, and Arcade",
                f"• High Score Record: {fruit_best} pts"
            ]
            fy = self.card_fruit.y + 110
            for line in features_fruit:
                col = (255, 215, 0) if "High Score" in line else (200, 205, 220)
                txt = self.font_card_desc.render(line, True, col)
                self.screen.blit(txt, (self.card_fruit.x + 28, fy))
                fy += 32

            # Play Button Box
            btn_fruit = pygame.Rect(self.card_fruit.x + 28, self.card_fruit.bottom - 68, self.card_fruit.w - 56, 46)
            btn_col2 = (35, 185, 55) if self.hovered_card == 2 else (45, 50, 70)
            pygame.draw.rect(self.screen, btn_col2, btn_fruit, border_radius=8)
            btn2_t = self.font_btn.render("PLAY FRUIT NINJA [PRESS 2]", True, (255, 255, 255))
            self.screen.blit(btn2_t, (btn_fruit.centerx - btn2_t.get_width()//2, btn_fruit.centery - btn2_t.get_height()//2))

            # Bottom instruction bar
            bar = self.font_sub.render("CLICK ANY GAME CARD OR PRESS [1] / [2] TO PLAY • [Q] QUIT", True, (150, 160, 180))
            self.screen.blit(bar, (SCREEN_W//2 - bar.get_width()//2, SCREEN_H - 60))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    launcher = ArcadeLauncher()
    launcher.run()
