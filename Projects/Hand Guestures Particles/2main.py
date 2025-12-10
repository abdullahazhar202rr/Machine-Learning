# 2main.py — Fixed, Clean & Rock-Solid Version
# (All features from the previous beautiful rewrite + bug fixes)

import os
import sys
import math
import time
import random
import collections
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame
import cv2
import mediapipe as mp
from PIL import Image

# ============================= CONFIG =============================
class Config:
    WINDOW = (1200, 800)
    FPS_TARGET = 60

    NUM_PARTICLES = 80
    PHOTO_FOLDER = "photos"
    THUMB_SIZE = 90

    MIN_SPREAD = 50
    MAX_SPREAD = 500
    COLLAPSE_SPREAD = 15

    SPRING_WEAK = 0.018
    SPRING_STRONG = 0.20
    DAMPING = 0.84
    JITTER_OPEN = 1.4
    JITTER_CLOSED = 0.06

    ZOOM_MIN = 0.4
    ZOOM_MAX = 3.5
    ZOOM_SMOOTH = 0.15

    PINCH_SELECT_DIST = 80
    PINCH_HOLD_TIME = 0.25
    SLAP_VELOCITY = 2200
    SLAP_COOLDOWN = 0.4

    CAM_W, CAM_H = 640, 480
    CAM_INDEX = 0

    SHOW_DEBUG = False          # toggle with F1
    TRAIL_LENGTH = 12
    GLOW_INTENSITY = 80

CONFIG = Config()
# ==================================================================

pygame.init()
screen = pygame.display.set_mode(CONFIG.WINDOW, pygame.RESIZABLE)
pygame.display.set_caption("Gesture Photo Cloud • Pinch • Drag • Slap • Zoom")
clock = pygame.time.Clock()

font_small = pygame.font.SysFont("Arial", 18)
font_big   = pygame.font.SysFont("Arial", 28, bold=True)

# --------------------- Photo Loading ---------------------
def load_photos(folder: str, size: int) -> List[pygame.Surface]:
    photos = []
    if not os.path.isdir(folder):
        print(f"[Warning] Folder '{folder}' not found → using colored circles.")
        return photos
    for file in os.listdir(folder):
        if file.lower().split(".")[-1] in {"png","jpg","jpeg","webp","bmp","gif"}:
            path = os.path.join(folder, file)
            try:
                img = Image.open(path).convert("RGBA")
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                surf = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
                photos.append(surf)
            except Exception as e:
                print(f"Skipped {path}: {e}")
    random.shuffle(photos)
    print(f"[Info] Loaded {len(photos)} photos")
    return photos

photos = load_photos(CONFIG.PHOTO_FOLDER, CONFIG.THUMB_SIZE)

# --------------------- Mediapipe ---------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)

cap = cv2.VideoCapture(CONFIG.CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG.CAM_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG.CAM_H)

# --------------------- Helpers ---------------------
def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def norm_to_screen(nx: float, ny: float) -> Tuple[float, float]:
    return nx * CONFIG.WINDOW[0], ny * CONFIG.WINDOW[1]

# --------------------- Hand Data ---------------------
@dataclass
class HandData:
    palm: pygame.math.Vector2
    pinch_point: pygame.math.Vector2
    pinch_ratio: float
    thumb_tip: pygame.math.Vector2
    index_tip: pygame.math.Vector2
    fingers_up: int

def analyze_hand(landmarks) -> HandData:
    lm = landmarks

    # Palm center
    palm_x = sum(lm[i].x for i in [0,5,9,13,17]) / 5
    palm_y = sum(lm[i].y for i in [0,5,9,13,17]) / 5
    palm = pygame.math.Vector2(norm_to_screen(palm_x, palm_y))

    # Finger count
    tips = [4,8,12,16,20]
    up = 0
    for i, tip in enumerate(tips):
        pip = [2,6,10,14,18][i-1 if i>0 else 0]
        if i == 0:  # thumb
            if lm[4].x < lm[2].x:
                up += 1
        elif lm[tip].y < lm[pip].y:
            up += 1

    # Pinch
    thumb = pygame.math.Vector2(norm_to_screen(lm[4].x, lm[4].y))
    index = pygame.math.Vector2(norm_to_screen(lm[8].x, lm[8].y))
    pinch_vec = thumb - index
    pinch_dist = pinch_vec.length()
    pinch_point = (thumb + index) / 2

    # Ratio
    xs = [l.x for l in lm]; ys = [l.y for l in lm]
    span = max(max(xs)-min(xs), max(ys)-min(ys))
    bbox_diag = max(span, 0.05) * max(CONFIG.WINDOW)
    pinch_ratio = pinch_dist / bbox_diag

    return HandData(palm, pinch_point, pinch_ratio, thumb, index, up)

def get_hands(frame_bgr) -> List[HandData]:
    rgb = cv2.cvtColor(cv2.flip(frame_bgr, 1), cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    if not results.multi_hand_landmarks:
        return []
    return [analyze_hand(hl.landmark) for hl in results.multi_hand_landmarks]

# --------------------- Particle ---------------------
class Particle:
    def __init__(self, idx: int):
        self.idx = idx
        self.base_img = random.choice(photos) if photos else None
        self.color = (random.randint(100,255), random.randint(100,255), random.randint(100,255)) if not self.base_img else None

        angle = random.random() * math.tau
        self.pos = pygame.math.Vector2(CONFIG.WINDOW[0]//2, CONFIG.WINDOW[1]//2) + \
                   pygame.math.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(20, 120)
        self.vel = pygame.math.Vector2(0, 0)
        self.trail = collections.deque(maxlen=CONFIG.TRAIL_LENGTH)
        self.scale = random.uniform(0.8, 1.3)
        self.angle = 0.0
        self.angular_vel = random.uniform(-2, 2)

    def update(self, attractor: pygame.math.Vector2, spread: float, dt: float,
               push: pygame.math.Vector2, spring: float, jitter: float,
               zoom: float, selected: bool = False):
        # FIXED: .xy is a property, not a method
        self.trail.append(self.pos.xy)

        if selected:
            jitter *= 0.05
            spring *= 0.15

        angle = (self.idx * 0.13 + time.time() * 0.3) * 1.1
        offset = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(0.7, 1.3)
        target = attractor + offset * spread * zoom

        force = (target - self.pos) * spring
        jitter_vec = pygame.math.Vector2(random.gauss(0,1), random.gauss(0,1)) * jitter
        self.vel += (force + jitter_vec + push) * dt
        self.vel *= CONFIG.DAMPING
        self.pos += self.vel * dt

        self.angular_vel += random.uniform(-0.4, 0.4)
        self.angular_vel *= 0.9
        self.angle += self.angular_vel * dt

    def draw(self, surf: pygame.Surface, selected: bool = False, extra_scale: float = 1.0):
        scale = self.scale * extra_scale * (2.2 if selected else 1.0)
        angle_deg = math.degrees(self.angle)

        if self.base_img:
            img = pygame.transform.rotozoom(self.base_img, angle_deg, scale)
            rect = img.get_rect(center=self.pos)

            if selected:
                glow = pygame.Surface((rect.w+60, rect.h+60), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (255,240,180,CONFIG.GLOW_INTENSITY), glow.get_rect())
                surf.blit(glow, glow.get_rect(center=rect.center), special_flags=pygame.BLEND_RGB_ADD)

            shadow = pygame.transform.rotozoom(self.base_img, 0, scale*1.15)
            shadow.fill((0,0,0,90), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(shadow, rect.move(10,10))

            surf.blit(img, rect)
        else:
            r = int(14 * scale)
            color = (*self.color, 255) if not selected else (255,255,180)
            pygame.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), r)
            if selected:
                pygame.draw.circle(surf, (255,255,200), (int(self.pos.x), int(self.pos.y)), r+12, 5)

        # Trail
        for i, (x, y) in enumerate(self.trail):
            alpha = int(140 * (i / len(self.trail)))
            pygame.draw.circle(surf, (255,255,255,alpha), (int(x), int(y)), 3)

# --------------------- App State ---------------------
class App:
    def __init__(self):
        self.particles = [Particle(i) for i in range(CONFIG.NUM_PARTICLES)]
        self.attractor = pygame.math.Vector2(*[x//2 for x in CONFIG.WINDOW])
        self.target_spread = CONFIG.MIN_SPREAD
        self.zoom = 1.0
        self.push = pygame.math.Vector2(0,0)

        self.selected: Optional[int] = None
        self.selected_scale = 1.0
        self.selected_hand: Optional[int] = None
        self.last_release = -10.0
        self.pinch_start = {}          # hand_idx → time

        self.hands: List[HandData] = []
        self.palm_hist = collections.deque(maxlen=10)

    def update_attractor(self):
        if self.hands:
            avg = sum((h.palm for h in self.hands), pygame.math.Vector2(0,0)) / len(self.hands)
            self.attractor += (avg - self.attractor) * 0.22

    def update_zoom(self):
        if len(self.hands) == 2 and self.hands[0].pinch_ratio < 0.45 and self.hands[1].pinch_ratio < 0.45:
            d = self.hands[0].pinch_point.distance_to(self.hands[1].pinch_point)
            target = lerp(CONFIG.ZOOM_MIN, CONFIG.ZOOM_MAX, d / 900)
        elif len(self.hands) == 1 and self.hands[0].pinch_ratio < 0.45:
            d = self.hands[0].thumb_tip.distance_to(self.hands[0].index_tip)
            target = lerp(CONFIG.ZOOM_MIN, CONFIG.ZOOM_MAX, d / 420)
        else:
            return
        self.zoom = lerp(self.zoom, target, CONFIG.ZOOM_SMOOTH)

    def try_select(self, t):
        if self.selected is not None or (t - self.last_release) < CONFIG.SLAP_COOLDOWN:
            return

        for i, h in enumerate(self.hands):
            if h.pinch_ratio > 0.45:
                self.pinch_start.pop(i, None)
                continue

            closest_i, closest_d = None, CONFIG.PINCH_SELECT_DIST
            for idx, p in enumerate(self.particles):
                d = h.pinch_point.distance_to(p.pos)
                if d < closest_d:
                    closest_d, closest_i = d, idx

            if closest_i is not None:
                if i not in self.pinch_start:
                    self.pinch_start[i] = t
                elif t - self.pinch_start[i] >= CONFIG.PINCH_HOLD_TIME:
                    self.selected = closest_i
                    self.selected_hand = i
                    self.selected_scale = 1.0
                    self.pinch_start.clear()
                    print(f"[Select] Particle {closest_i}")
                    return
            else:
                self.pinch_start.pop(i, None)

    def update_selection(self, t):
        if self.selected is None:
            return
        if self.selected_hand is None or self.selected_hand >= len(self.hands):
            self.selected = None
            return

        h = self.hands[self.selected_hand]
        p = self.particles[self.selected]

        # Follow palm
        p.pos += (h.palm - p.pos) * 0.38

        # Scale with pinch openness
        openness = max(0, 1 - h.pinch_ratio * 2)
        target = lerp(0.7, 3.2, openness)
        self.selected_scale = lerp(self.selected_scale, target, 0.25)
        p.scale = self.selected_scale

        # Slap detection
        self.palm_hist.append((h.palm, t))
        if len(self.palm_hist) >= 2:
            dp = self.palm_hist[-1][0] - self.palm_hist[-2][0]
            dt = max(0.001, self.palm_hist[-1][1] - self.palm_hist[-2][1])
            speed = dp.length() / dt
            if speed > CONFIG.SLAP_VELOCITY and h.pinch_ratio < 0.5:
                p.vel += dp.normalize() * 38
                print("[Slap] Released!")
                self.selected = None
                self.last_release = t
                self.selected_hand = None

    def get_physics(self):
        if not self.hands:
            spread = CONFIG.MIN_SPREAD
            spring = CONFIG.SPRING_WEAK
            jitter = 0.7
        else:
            openness = self.hands[0].fingers_up / 5.0
            spread = lerp(CONFIG.COLLAPSE_SPREAD, CONFIG.MAX_SPREAD, openness)
            spring = lerp(CONFIG.SPRING_STRONG, CONFIG.SPRING_WEAK, openness)
            jitter = lerp(CONFIG.JITTER_CLOSED, CONFIG.JITTER_OPEN, openness)
        self.target_spread = lerp(self.target_spread, spread, 0.18)
        return spring, jitter

    def draw_ui(self):
        lines = [
            "Open hand → Spread   |   Fist → Collapse   |   Pinch → Zoom / Grab",
            "Pinch near photo → hold ~0.3s → move hand → open/close pinch to scale → fast slap to throw!",
            f"Hands: {len(self.hands)}   Zoom: {self.zoom:.2f}x   Selected: {self.selected if self.selected else '—'}   FPS: {clock.get_fps():.1f}",
        ]
        for i, txt in enumerate(lines):
            color = (255, 240, 180) if i == 1 else (200, 230, 255)
            surf = font_small.render(txt, True, color)
            screen.blit(surf, (16, 16 + i*26))

        if CONFIG.SHOW_DEBUG:
            for h in self.hands:
                pygame.draw.circle(screen, (0,255,0), h.palm, 15, 3)
                pygame.draw.circle(screen, (255,80,80), h.pinch_point, 12, 3)

# --------------------- Main Loop ---------------------
app = App()
running = True

while running:
    dt = clock.tick(CONFIG.FPS_TARGET) / 1000.0
    now = time.time()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            elif e.key == pygame.K_SPACE:
                app.target_spread = CONFIG.MAX_SPREAD if app.target_spread < 200 else CONFIG.MIN_SPREAD
            elif e.key == pygame.K_F1:
                CONFIG.SHOW_DEBUG = not CONFIG.SHOW_DEBUG

    ret, frame = cap.read()
    app.hands = get_hands(frame) if ret else []

    app.update_attractor()
    app.update_zoom()
    app.try_select(now)
    app.update_selection(now)
    spring, jitter = app.get_physics()

    for i, p in enumerate(app.particles):
        p.update(app.attractor, app.target_spread, dt, app.push,
                 spring, jitter, app.zoom, selected=(i == app.selected))

    # ------- Render -------
    screen.fill((10, 14, 26))

    # Background rings
    for i in range(6):
        r = 80 + i*140 * app.zoom
        col = (60, 80, 120, 8-i)
        s = pygame.Surface(CONFIG.WINDOW, pygame.SRCALPHA)
        pygame.draw.circle(s, col, app.attractor, int(r), max(1, 5-i))
        screen.blit(s, (0,0), special_flags=pygame.BLEND_RGB_ADD)

    # Particles (depth sorted)
    for p in sorted(app.particles, key=lambda p: p.pos.y):
        idx = app.particles.index(p)
        extra = app.selected_scale if idx == app.selected else 1.0
        p.draw(screen, selected=(idx == app.selected), extra_scale=extra)

    app.draw_ui()
    pygame.display.flip()

# Cleanup
cap.release()
hands.close()
pygame.quit()
sys.exit()