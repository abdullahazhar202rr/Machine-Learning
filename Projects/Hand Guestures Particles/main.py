"""
main.py
Gesture-controlled particle/photo cloud with:
 - one- or two-hand pinch-to-zoom
 - pinch-to-select particle, 3D move selected particle (position + scale)
 - quick 'slap' to release selected particle back to swarm
 - previous behaviors preserved (fist -> tight ball, open -> spread)

Dependencies:
    pip install pygame pillow mediapipe opencv-python
"""

import os
import sys
import random
import math
import time
import collections
import pygame
from PIL import Image
import cv2
import mediapipe as mp

# ---------------- Config ----------------
WINDOW_W, WINDOW_H = 1000, 700
NUM_PARTICLES = 80
THUMB_SIZE = 80
MAX_SPREAD = 420
MIN_SPREAD = 40
COLLAPSE_SPREAD = 12
SPRING_WEAK = 0.022
SPRING_STRONG = 0.18
DAMPING = 0.82
VEL_CLAMP = 3000.0
PHOTO_FOLDER = "photos"
CAPTURE_W, CAPTURE_H = 640, 480
CAMERA_INDEX = 0

# Zoom config
ZOOM_MIN = 0.45
ZOOM_MAX = 3.2
ZOOM_SMOOTH = 0.18
PINCH_THRESHOLD = 0.20

# Selection config
PINCH_SELECT_MAX_PIX = 60        # max pixel distance between pinch-point and particle center to select
PINCH_HOLD_TIME = 0.15          # seconds of continuous pinch to count as a selection
SLAP_VEL_THRESHOLD = 1800.0     # px/s approximate threshold for slap
SLAP_COOLDOWN = 0.35            # seconds after release before reselect allowed

# ----------------------------------------

pygame.init()
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Particle Cloud — Select & Pinch Zoom")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)

def load_photos(folder, thumb_size):
    if not os.path.isdir(folder):
        return []
    imgs = []
    for fname in os.listdir(folder):
        if fname.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            p = os.path.join(folder, fname)
            try:
                im = Image.open(p).convert("RGBA")
                im.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                mode = im.mode
                size = im.size
                data = im.tobytes()
                surf = pygame.image.fromstring(data, size, mode)
                imgs.append(surf)
            except Exception as e:
                print("Skipping", p, e)
    return imgs

photos = load_photos(PHOTO_FOLDER, THUMB_SIZE)

# Mediapipe
mp_hands = mp.solutions.hands
hands_sess = mp_hands.Hands(static_image_mode=False,
                            max_num_hands=2,
                            min_detection_confidence=0.6,
                            min_tracking_confidence=0.6)

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_H)

# Utility: analyze a single hand landmarks -> info dict
def analyze_hand_landmarks(landmarks):
    lm = landmarks
    ids_center = [0,5,9,13,17]
    cx = sum(lm[i].x for i in ids_center)/len(ids_center)
    cy = sum(lm[i].y for i in ids_center)/len(ids_center)

    # count extended fingers (index/middle/ring/pinky by tip vs pip)
    extended = 0
    tips = [8,12,16,20]
    pips = [6,10,14,18]
    for t,p in zip(tips,pips):
        try:
            if lm[t].y < lm[p].y:
                extended += 1
        except Exception:
            pass
    try:
        if lm[4].x > lm[3].x + 0.02:
            extended += 1
    except Exception:
        pass

    xs = [p.x for p in lm]; ys = [p.y for p in lm]
    span_x = max(xs)-min(xs); span_y = max(ys)-min(ys)
    span_norm = max(span_x, span_y)
    span_norm = max(0.02, min(span_norm, 0.55))
    span_norm = (span_norm - 0.02) / (0.55 - 0.02)

    # thumb tip (4) and index tip (8)
    try:
        tx,ty = lm[4].x, lm[4].y
        ixn,iyn = lm[8].x, lm[8].y
        tip_dist = math.hypot(tx-ixn, ty-iyn)
    except Exception:
        tip_dist = 1.0
        tx,ty,ixn,iyn = 0.0,0.0,0.0,0.0

    bbox_max = max(span_x, span_y, 1e-6)
    pinch_ratio = tip_dist / bbox_max
    pinch_point = ((tx+ixn)/2.0, (ty+iyn)/2.0)

    return {"cx":cx,"cy":cy,"extended":extended,"span_norm":span_norm,
            "pinch_ratio":pinch_ratio,"pinch_point":pinch_point,
            "thumb":(tx,ty),"index":(ixn,iyn)}

def get_hands_info(frame_bgr):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.flip(frame_rgb, 1)  # mirror
    results = hands_sess.process(frame_rgb)
    if not results.multi_hand_landmarks:
        return []
    out=[]
    for lm in results.multi_hand_landmarks:
        out.append(analyze_hand_landmarks(lm.landmark))
    return out

# Particles
class Particle:
    def __init__(self, idx):
        self.idx = idx
        self.angle = random.random()*math.tau
        self.radius = random.uniform(10,80)
        self.pos = pygame.math.Vector2(WINDOW_W//2 + math.cos(self.angle)*self.radius,
                                       WINDOW_H//2 + math.sin(self.angle)*self.radius)
        self.vel = pygame.math.Vector2(0,0)
        self.offset = random.uniform(0.85,1.25)
        self.base_image = None
        self.scale = 1.0  # local scale (for selected particle)
        if photos:
            self.base_image = random.choice(photos)
            s = random.uniform(0.85,1.15)
            w,h = self.base_image.get_size()
            new_w = max(4,int(w*s)); new_h = max(4,int(h*s))
            self.base_image = pygame.transform.smoothscale(self.base_image,(new_w,new_h))
        else:
            self.color=(random.randint(40,220),random.randint(40,220),random.randint(40,220))

    def update(self, attractor_pos, target_spread, dt, push_vector, spring_strength, jitter_scale, zoom):
        base_angle = (self.idx / max(1,NUM_PARTICLES)) * math.tau * self.offset
        r_scale = 0.55 + 0.9 * random.random()
        target = pygame.math.Vector2(attractor_pos.x + math.cos(base_angle) * target_spread * r_scale * zoom,
                                     attractor_pos.y + math.sin(base_angle) * target_spread * r_scale * zoom)
        displacement = target - self.pos
        force = displacement * spring_strength
        jitter = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1)) * jitter_scale
        self.vel += (force + jitter + push_vector) * dt
        if self.vel.length_squared() > VEL_CLAMP * VEL_CLAMP:
            self.vel.scale_to_length(VEL_CLAMP)
        self.vel *= DAMPING
        self.pos += self.vel * dt
        if not (math.isfinite(self.pos.x) and math.isfinite(self.pos.y)):
            self.pos.x = float(WINDOW_W//2); self.pos.y = float(WINDOW_H//2)

    def draw(self, surf, selected=False, sel_scale=1.0):
        try:
            px=float(self.pos.x); py=float(self.pos.y)
        except Exception:
            px,py=WINDOW_W//2, WINDOW_H//2
        if not (math.isfinite(px) and math.isfinite(py)):
            px,py=WINDOW_W//2, WINDOW_H//2
        ix,iy = int(px), int(py)
        if self.base_image:
            img = self.base_image
            if selected:
                # scale image visually for selected particle using sel_scale
                w,h = img.get_size()
                sw = max(2,int(w * sel_scale))
                sh = max(2,int(h * sel_scale))
                img2 = pygame.transform.smoothscale(img,(sw,sh))
                rect = img2.get_rect(center=(ix,iy))
                # shadow
                shadow_h = max(1, sh//3)
                shadow = pygame.Surface((max(1,sw),shadow_h), flags=pygame.SRCALPHA)
                pygame.draw.ellipse(shadow,(0,0,0,70),(0,0,max(1,sw),shadow_h))
                surf.blit(shadow,(rect.x, rect.y + int(sh*0.55)))
                surf.blit(img2, rect)
            else:
                w,h = img.get_size()
                rect = img.get_rect(center=(ix,iy))
                shadow_h = max(1,h//3)
                shadow = pygame.Surface((max(1,w),shadow_h), flags=pygame.SRCALPHA)
                pygame.draw.ellipse(shadow,(0,0,0,60),(0,0,max(1,w),shadow_h))
                surf.blit(shadow,(rect.x, rect.y + int(h*0.55)))
                surf.blit(img, rect)
        else:
            r = 8 + (self.idx % 6)
            r = max(1,int(r * (sel_scale if selected else 1.0)))
            pygame.draw.circle(surf, self.color, (ix,iy), r)

particles = [Particle(i) for i in range(NUM_PARTICLES)]

# State
expanded=False
target_spread = MIN_SPREAD
attractor = pygame.math.Vector2(WINDOW_W//2, WINDOW_H//2)
push_vel = pygame.math.Vector2(0,0)
push_decay = 0.92
hand_visible=False

# selection state
selected_idx = None
selected_since = None
last_release_time = -10.0
selected_hand_id = None  # index into hands_info for controlling hand
selected_hand_prev_pos = None
selected_hand_prev_time = None
selected_hand_prev_vel = pygame.math.Vector2(0,0)
selected_scale = 1.0

# zoom state
zoom = 1.0
last_pinch_distance = None

def draw_instructions(surface, hand_vis, hands_count, zoom_val, sel_idx):
    lines = [
        "Gestures: Open->Expand  |  Fist->Collapse  |  Pinch (one/two) -> Zoom/select",
        f"Hands visible: {hands_count}   |  Zoom: {zoom_val:.2f}   |  Selected: {sel_idx if sel_idx is not None else 'None'}",
        "Pinch near a particle to select it; move to drag; quick outward slap -> release"
    ]
    y=8
    for line in lines:
        txt = font.render(line, True, (240,240,240))
        surface.blit(txt,(10,y)); y+=18

def lerp(a,b,t): return a + (b-a)*t

# helpers for mapping normalized coords to window pixels
def norm_to_px(nx, ny): return nx * WINDOW_W, ny * WINDOW_H

# main loop
running=True
ext_count=None
span_norm=0.0
palm_position_hist = collections.deque(maxlen=6)  # history of palm positions for slap detection
while running:
    raw_dt_ms = clock.tick(60)
    dt = max(1.0, min(raw_dt_ms, 60.0)) / 16.0

    grabbed, frame = cap.read()
    hands_info = []
    if grabbed:
        hands_info = get_hands_info(frame)
        # update attractor depending on hands visible
        if len(hands_info) >= 2:
            # midpoint of palms
            mx = (hands_info[0]["cx"] + hands_info[1]["cx"]) / 2.0
            my = (hands_info[0]["cy"] + hands_info[1]["cy"]) / 2.0
            attractor_target_x = mx * WINDOW_W
            attractor_target_y = my * WINDOW_H
            attractor.x += (attractor_target_x - attractor.x) * 0.36
            attractor.y += (attractor_target_y - attractor.y) * 0.36
        elif len(hands_info) == 1:
            single = hands_info[0]
            attractor_target_x = single["cx"] * WINDOW_W
            attractor_target_y = single["cy"] * WINDOW_H
            attractor.x += (attractor_target_x - attractor.x) * 0.35
            attractor.y += (attractor_target_y - attractor.y) * 0.35

        # decide expand/collapse using first hand if present
        if len(hands_info) >= 1:
            ext_count = hands_info[0]["extended"]
            span_norm = hands_info[0]["span_norm"]
            if ext_count >= 4: expanded=True
            elif ext_count <= 1: expanded=False
            hand_visible = True
        else:
            hand_visible = False
    else:
        hand_visible=False

    # PINCH-TO-ZOOM (one- or two-hand)
    pinch_active = False
    desired_zoom = zoom
    if len(hands_info) >= 2:
        h0 = hands_info[0]; h1 = hands_info[1]
        pinch0 = (h0["pinch_ratio"] < PINCH_THRESHOLD)
        pinch1 = (h1["pinch_ratio"] < PINCH_THRESHOLD)
        if pinch0 and pinch1:
            pinch_active = True
            p0x,p0y = norm_to_px(*h0["pinch_point"])
            p1x,p1y = norm_to_px(*h1["pinch_point"])
            pinch_distance = math.hypot(p1x-p0x, p1y-p0y)
            diag = math.hypot(WINDOW_W, WINDOW_H)
            norm = pinch_distance / (diag * 0.9)
            desired_zoom = lerp(ZOOM_MIN, ZOOM_MAX, max(0.0, min(1.0, norm * 1.8)))
            last_pinch_distance = pinch_distance
    elif len(hands_info) == 1:
        h = hands_info[0]
        pinch0 = (h["pinch_ratio"] < PINCH_THRESHOLD)
        if pinch0:
            pinch_active = True
            # use thumb-index distance in pixels to map zoom
            tx,ty = h["thumb"]; ixn,iyn = h["index"]
            tx_px,ty_px = tx*WINDOW_W, ty*WINDOW_H
            ix_px,iy_px = ixn*WINDOW_W, iyn*WINDOW_H
            pinch_distance = math.hypot(tx_px-ix_px, ty_px-iy_px)
            diag = math.hypot(WINDOW_W, WINDOW_H)
            norm = pinch_distance / (diag * 0.5)
            desired_zoom = lerp(ZOOM_MIN, ZOOM_MAX, max(0.0, min(1.0, norm * 2.0)))
            last_pinch_distance = pinch_distance
    else:
        last_pinch_distance = None

    # smooth zoom update
    zoom += (desired_zoom - zoom) * ZOOM_SMOOTH
    zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom))

    # Selection logic:
    # If not currently selected:
    #  - if any hand pinch starts and that pinch-point is within PINCH_SELECT_MAX_PIX of a particle -> select that particle after PINCH_HOLD_TIME
    # If selected:
    #  - control selected particle with the selected hand's palm position + pinch distance -> scale (3D move)
    #  - if slap detected on controlling hand -> release (unselect) and send particle back to swarm
    current_time = time.time()

    # track palm positions for slap detection (we'll use the controlling hand only)
    # update history only for first hand if exists
    if len(hands_info) >= 1:
        palm_px = (hands_info[0]["cx"]*WINDOW_W, hands_info[0]["cy"]*WINDOW_H, current_time)
        palm_position_hist.append(palm_px)

    # selection initiation variables
    selecting_this_frame = False
    if selected_idx is None:
        # check every hand for pinch-start near particle
        for hid, h in enumerate(hands_info):
            if h["pinch_ratio"] < PINCH_THRESHOLD:
                pinch_px = norm_to_px(*h["pinch_point"])
                # find nearest particle to pinch point
                nearest = None; nearest_dist = 1e9
                for i,p in enumerate(particles):
                    d = math.hypot(p.pos.x - pinch_px[0], p.pos.y - pinch_px[1])
                    if d < nearest_dist:
                        nearest_dist = d; nearest = i
                if nearest is not None and nearest_dist <= PINCH_SELECT_MAX_PIX:
                    # user is pinching near this particle: require hold for PINCH_HOLD_TIME
                    # record start time in a simple attribute on hand info (we can use dict)
                    if "_pinch_start" not in h:
                        h["_pinch_start"] = current_time
                    else:
                        held = current_time - h["_pinch_start"]
                        if held >= PINCH_HOLD_TIME and (current_time - last_release_time) > SLAP_COOLDOWN:
                            # select
                            selected_idx = nearest
                            selected_since = current_time
                            selected_hand_id = hid
                            selected_hand_prev_pos = pygame.math.Vector2(h["cx"]*WINDOW_W, h["cy"]*WINDOW_H)
                            selected_hand_prev_time = current_time
                            selected_hand_prev_vel = pygame.math.Vector2(0,0)
                            selected_scale = 1.0
                            # hide others by just keeping selected_idx not None
                            selecting_this_frame = True
                            break
                else:
                    # pinch not near any particle -> reset pinch start (so user must re-pincht)
                    if "_pinch_start" in h: del h["_pinch_start"]
            else:
                if "_pinch_start" in h: del h["_pinch_start"]
    else:
        # control selected particle
        # determine controlling hand: prefer selected_hand_id if present, else pick first hand
        if selected_hand_id is None or selected_hand_id >= len(hands_info):
            controlling_hand = 0 if len(hands_info)>0 else None
            selected_hand_id = controlling_hand
        else:
            controlling_hand = selected_hand_id

        if controlling_hand is not None and len(hands_info) > controlling_hand:
            ch = hands_info[controlling_hand]
            # palm movement controls particle 2D position
            palm_px = pygame.math.Vector2(ch["cx"]*WINDOW_W, ch["cy"]*WINDOW_H)
            # compute palm velocity
            now = current_time
            if selected_hand_prev_pos is not None and selected_hand_prev_time is not None:
                dt_hand = max(1e-6, now - selected_hand_prev_time)
                vel = (palm_px - selected_hand_prev_pos) / dt_hand
                selected_hand_prev_vel = vel
                selected_hand_prev_pos = palm_px
                selected_hand_prev_time = now
            else:
                selected_hand_prev_pos = palm_px
                selected_hand_prev_time = now
                selected_hand_prev_vel = pygame.math.Vector2(0,0)

            # move selected particle smoothly toward palm
            # smaller smoothing so particle follows hand naturally
            target_pos = pygame.math.Vector2(palm_px.x, palm_px.y)
            particles[selected_idx].pos += (target_pos - particles[selected_idx].pos) * 0.36

            # pinch distance controls scale (z)
            try:
                tx,ty = ch["thumb"]; ix,iy = ch["index"]
                tx_px,ty_px = tx*WINDOW_W, ty*WINDOW_H
                ix_px,iy_px = ix*WINDOW_W, iy*WINDOW_H
                pinch_dist = math.hypot(tx_px-ix_px, ty_px-iy_px)
                # map pinch_dist to scale: small dist -> small scale, large dist -> big scale
                diag = math.hypot(WINDOW_W, WINDOW_H)
                s_norm = pinch_dist / (diag * 0.45)
                s_norm = max(0.0, min(1.0, s_norm))
                desired_scale = lerp(0.6, 2.6, s_norm)
            except Exception:
                desired_scale = 1.0
            # smooth scale
            selected_scale += (desired_scale - selected_scale) * 0.25
            particles[selected_idx].scale = selected_scale

            # detect slap: high outward velocity on controlling hand
            if selected_hand_prev_vel.length() > SLAP_VEL_THRESHOLD:
                # release particle: give it a push equal to that slap vector (so it flies away then returns)
                punch = selected_hand_prev_vel * 0.02
                particles[selected_idx].vel += punch
                # clear selection
                selected_idx = None
                selected_since = None
                selected_hand_id = None
                last_release_time = current_time
                selected_hand_prev_pos = None
                selected_hand_prev_time = None
                selected_hand_prev_vel = pygame.math.Vector2(0,0)

        else:
            # no controlling hand visible -> deselect
            selected_idx = None
            selected_since = None
            selected_hand_id = None
            selected_hand_prev_pos = None
            selected_hand_prev_time = None
            selected_hand_prev_vel = pygame.math.Vector2(0,0)

    # physics params (span/spring/jitter)
    if not hand_visible:
        desired_spread = MIN_SPREAD
        desired_spring = SPRING_WEAK
        jitter_scale = 0.9
    else:
        if not expanded:
            desired_spread = COLLAPSE_SPREAD
            desired_spring = SPRING_STRONG
            jitter_scale = 0.08
        else:
            # use first hand span_norm if available
            span = hands_info[0]["span_norm"] if len(hands_info)>0 else 0.5
            desired_spread = lerp(MIN_SPREAD, MAX_SPREAD, span)
            desired_spring = lerp(SPRING_STRONG, SPRING_WEAK, span)
            jitter_scale = lerp(0.15, 1.1, span)
    target_spread += (desired_spread - target_spread) * 0.28
    current_spring = desired_spring

    # events (keyboard)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running=False
            elif event.key == pygame.K_SPACE: expanded = not expanded
            elif event.key == pygame.K_RIGHT: push_vel.x += 4
            elif event.key == pygame.K_LEFT: push_vel.x -= 4
            elif event.key == pygame.K_UP: push_vel.y -= 3
            elif event.key == pygame.K_DOWN: push_vel.y += 3

    t = pygame.time.get_ticks() / 1000.0
    ambient = pygame.math.Vector2(math.cos(t*0.9)*4, math.sin(t*1.1)*4)
    push_vel *= push_decay
    push_vector = push_vel * 0.25

    # update particles: if a particle is selected we still update it with physics a little,
    # but drawing will show it specially and we override its position while dragging.
    for i,p in enumerate(particles):
        # if selected and we are actively moving it, skip the normal update to keep hand control smooth
        if selected_idx is not None and i == selected_idx:
            # give small physics to selected so it returns gracefully when released
            p.update(attractor + ambient, target_spread * 0.2, dt, push_vector, current_spring*0.2, jitter_scale*0.05, zoom)
        else:
            individual_target = target_spread * (0.85 + 0.3 * math.sin(p.idx * 0.37 + t * 1.2))
            p.update(attractor + ambient, individual_target, dt, push_vector, current_spring, jitter_scale, zoom)

    # draw
    screen.fill((18,22,28))
    center = pygame.math.Vector2(WINDOW_W//2, WINDOW_H//2)
    for i in range(1,6):
        alpha = int(8 * (6-i))
        r = int((i/6) * (WINDOW_W // 1.4))
        surf = pygame.Surface((WINDOW_W, WINDOW_H), flags=pygame.SRCALPHA)
        pygame.draw.circle(surf, (60,80,100,alpha), (int(center.x), int(center.y)), r)
        screen.blit(surf, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

    # draw either only selected particle (big) or all
    if selected_idx is not None:
        # draw selected last so it's on top
        for i,p in enumerate(sorted(particles, key=lambda q: q.pos.y)):
            if i == selected_idx:
                # skip now, draw later
                continue
            # draw tiny placeholders behind (optional: we can hide them completely)
            # draw them faintly
            p.draw(screen, selected=False, sel_scale=0.8)
        # draw the selected particle prominently
        particles[selected_idx].draw(screen, selected=True, sel_scale=particles[selected_idx].scale)
    else:
        for p in sorted(particles, key=lambda q: q.pos.y):
            p.draw(screen)

    # draw attractor
    pygame.draw.circle(screen, (200,200,255), (int(attractor.x), int(attractor.y)), 6, 2)

    draw_instructions(screen, hand_visible, len(hands_info), zoom, selected_idx)
    pygame.display.flip()

# cleanup
cap.release()
pygame.quit()
sys.exit()
