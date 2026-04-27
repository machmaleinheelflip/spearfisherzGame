import pygame
import random
import sys
import math
import asyncio
import array

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

SURFACE_Y = 50
SEA_BOTTOM_Y = SCREEN_HEIGHT - 20

# Colors
SKY_BLUE = (135, 206, 235)
WATER_TOP = (0, 105, 148)
WATER_BOT = (0, 50, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
YELLOW = (255, 215, 0)
GRAY = (120, 120, 120)
DARK_GRAY = (80, 80, 80)
GREEN = (50, 200, 80)
ORANGE = (255, 140, 0)
SKIN = (255, 200, 150)
DARK_BLUE = (0, 30, 60)
SAND = (194, 178, 128)

# Player
PLAYER_SPEED = 4
PLAYER_BODY_W = 30
PLAYER_BODY_H = 14

# Spear
SPEAR_LENGTH = 120  # ~four times the player length
SPEAR_SPEED = 8
SPEAR_COOLDOWN = 600  # ms

# Breath
BREATH_MAX = 10.0       # seconds
BREATH_REFILL_RATE = 2.0 # seconds to refill per second on surface
BREATH_DAMAGE_INTERVAL = 1.0  # lose 1 life every second when out of breath

# Rocks
ROCK_SPEED = 3
ROCK_SPAWN_INTERVAL = 1200  # ms
MIN_ROCK_WIDTH = 30
MAX_ROCK_WIDTH = 60
MIN_ROCK_HEIGHT = 40
MAX_ROCK_HEIGHT = SCREEN_HEIGHT - SURFACE_Y - 30  # can reach almost to surface

# Fish types
FISH_TYPES = {
    "parrotfish": {"w": 24, "h": 12, "points": 1,
                   "body": (0, 180, 120), "fin": (0, 220, 160), "label": "Parrotfish"},
    "seabream":   {"w": 40, "h": 20, "points": 10,
                   "body": (200, 200, 210), "fin": (170, 170, 190), "label": "Sea Bream"},
    "grouper":    {"w": 34, "h": 18, "points": -20,
                   "body": (120, 80, 40), "fin": (90, 60, 30), "label": "Grouper"},
}

FISH_SPEED_BASE = 2
FISH_SPAWN_INTERVAL = 2200  # ms

SCROLL_SPEED = 2

# Sea bream scare settings
SCARE_DISTANCE = 150
SCARE_MOVE_THRESHOLD = 3  # player movement pixels to count as "moving a lot"
SCARE_FLEE_SPEED = 6

# Grouper attraction
GROUPER_ATTRACT_SPEED = 0.8

# Touch controls
JOYSTICK_CENTER = (120, SCREEN_HEIGHT - 120)
JOYSTICK_RADIUS = 60
FIRE_BUTTON_CENTER = (SCREEN_WIDTH - 90, SCREEN_HEIGHT - 120)
FIRE_BUTTON_RADIUS = 45

# ---------------------------------------------------------------------------
# Helper – draw pixel-art style shapes
# ---------------------------------------------------------------------------

# FACE_IMG = None

# def load_face_image():
#     global FACE_IMG
#     import os
#     path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "IMG_1382.jpg")
#     if os.path.exists(path):
#         img = pygame.image.load(path).convert_alpha()
#         FACE_IMG = pygame.transform.smoothscale(img, (36, 36))

def draw_player(surface, x, y, fin_offset=0):
    """Draw a small pixel-art spearfisher with animated fins."""
    # Body (wetsuit)
    pygame.draw.rect(surface, DARK_BLUE, (x, y, PLAYER_BODY_W, PLAYER_BODY_H))
    # Head
    pygame.draw.rect(surface, SKIN, (x + 26, y - 2, 12, 12))
    # Mask / goggles
    pygame.draw.rect(surface, (0, 180, 220), (x + 30, y, 8, 6))
    # Fins (animated)
    fin_y = y + 2 + int(fin_offset)
    pygame.draw.rect(surface, YELLOW, (x - 14, fin_y, 14, 10))
    # Speargun (same size as player body)
    gun_len = PLAYER_BODY_W
    pygame.draw.rect(surface, GRAY, (x + 32, y + 6, gun_len, 3))
    # Arm
    pygame.draw.rect(surface, SKIN, (x + 28, y + 8, 10, 4))


def draw_spear_shaft(surface, sx, sy, player_x, player_y):
    """Draw the shaft and the rope connecting it to the gun."""
    gun_tip_x = player_x + 32 + PLAYER_BODY_W
    gun_tip_y = player_y + 7
    pygame.draw.line(surface, (180, 160, 120), (gun_tip_x, gun_tip_y), (sx, sy + 1), 1)
    # Shaft
    pygame.draw.rect(surface, GRAY, (sx, sy, 20, 3))
    # Tip
    pygame.draw.polygon(surface, WHITE, [(sx + 20, sy - 2), (sx + 26, sy + 1), (sx + 20, sy + 5)])


def generate_rock_shape(w, h):
    """Return a list of polygon points for a rocky shape anchored at bottom."""
    cx = w // 2
    points = []
    # Bottom corners
    points.append((0, h))
    # Left side going up
    points.append((random.randint(0, w // 4), random.randint(h // 3, h * 2 // 3)))
    points.append((random.randint(w // 6, w // 3), random.randint(5, h // 3)))
    # Top
    points.append((random.randint(w // 3, w * 2 // 3), random.randint(0, h // 5)))
    # Right side going down
    points.append((random.randint(w * 2 // 3, w * 5 // 6), random.randint(5, h // 3)))
    points.append((random.randint(w * 3 // 4, w), random.randint(h // 3, h * 2 // 3)))
    points.append((w, h))
    return points


def draw_rock(surface, rock):
    """Draw a rock onto the main surface."""
    temp = pygame.Surface((rock["w"], rock["h"]), pygame.SRCALPHA)
    pygame.draw.polygon(temp, DARK_GRAY, rock["shape"])
    pygame.draw.polygon(temp, GRAY, rock["shape"], 2)
    surface.blit(temp, (rock["x"], rock["y"]))


def draw_fish(surface, x, y, fish_type):
    """Draw a pixel-art fish based on type."""
    info = FISH_TYPES[fish_type]
    w, h = info["w"], info["h"]
    body_color = info["body"]
    fin_color = info["fin"]
    # body
    pygame.draw.ellipse(surface, body_color, (x, y, w, h))
    # tail
    pygame.draw.polygon(surface, fin_color, [(x, y + h // 2),
                                              (x - 8, y),
                                              (x - 8, y + h)])
    # dorsal fin
    pygame.draw.polygon(surface, fin_color, [(x + w // 3, y),
                                              (x + w // 2, y - 5),
                                              (x + w * 2 // 3, y)])
    # eye
    pygame.draw.rect(surface, BLACK, (x + w - 8, y + 3, 3, 3))
    pygame.draw.rect(surface, WHITE, (x + w - 7, y + 3, 1, 1))

    # Grouper gets spots
    if fish_type == "grouper":
        for dx, dy in [(8, 6), (14, 10), (20, 5)]:
            pygame.draw.rect(surface, (80, 50, 20), (x + dx, y + dy, 3, 2))


def draw_bubbles(surface, bubbles):
    for b in bubbles:
        pygame.draw.circle(surface, (150, 210, 255), (int(b[0]), int(b[1])), b[2], 1)


def draw_breath_bar(surface, breath, max_breath, x, y, w, h):
    """Draw a breath bar."""
    ratio = max(0, breath / max_breath)
    # Background
    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h))
    # Fill
    color = (0, 180, 255) if ratio > 0.3 else RED
    pygame.draw.rect(surface, color, (x + 1, y + 1, int((w - 2) * ratio), h - 2))
    # Border
    pygame.draw.rect(surface, WHITE, (x, y, w, h), 1)


def draw_heart(surface, x, y, size=14):
    """Draw a pixel-art heart."""
    s = size
    # Two circles for top bumps
    pygame.draw.circle(surface, RED, (x + s // 4, y + s // 4), s // 4)
    pygame.draw.circle(surface, RED, (x + 3 * s // 4, y + s // 4), s // 4)
    # Triangle for bottom
    pygame.draw.polygon(surface, RED, [(x, y + s // 4), (x + s // 2, y + s), (x + s, y + s // 4)])

# ---------------------------------------------------------------------------
# Sound generation (simple synthesized retro sounds)
# ---------------------------------------------------------------------------

class _SilentSound:
    """Fallback when sound generation is not available (e.g. in browser)."""
    def play(self, *a, **kw): pass
    def stop(self, *a, **kw): pass
    def get_busy(self, *a, **kw): return False

class _SilentChannel:
    def play(self, *a, **kw): pass
    def get_busy(self, *a, **kw): return False

def _safe_sound(func):
    """Wrap a sound-creation function so it returns a silent stub on failure."""
    try:
        return func()
    except Exception:
        return _SilentSound()

def generate_sound(frequency=440, duration=0.2, volume=0.3, wave="square", fade_out=True):
    """Generate a simple retro sound using pure Python."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        if wave == "square":
            val = volume * (1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0)
        elif wave == "sine":
            val = volume * math.sin(2 * math.pi * frequency * t)
        elif wave == "noise":
            val = volume * random.uniform(-1, 1)
        elif wave == "saw":
            val = volume * (2 * ((frequency * t) % 1) - 1)
        else:
            val = volume * math.sin(2 * math.pi * frequency * t)
        if fade_out:
            val *= 1.0 - (i / n_samples)
        # Clamp and convert to 16-bit int
        val = max(-1.0, min(1.0, val))
        s = int(val * 32767)
        samples.append(s)
        samples.append(s)  # stereo: left and right
    buf = array.array('h', samples)
    return pygame.mixer.Sound(buffer=buf)

def create_fire_sound():
    s1 = generate_sound(800, 0.05, 0.3, "noise")
    s2 = generate_sound(400, 0.1, 0.2, "square")
    return s1  # short burst

def create_ouch_sound():
    return generate_sound(200, 0.3, 0.4, "saw")

def create_score_sound():
    """Quick ascending chime."""
    s = generate_sound(600, 0.1, 0.3, "square", fade_out=False)
    s2 = generate_sound(900, 0.15, 0.3, "square")
    return s2

def create_breath_sound():
    return generate_sound(100, 0.5, 0.3, "noise")

def create_theme_loop():
    """Generate a short retro underwater melody loop."""
    sample_rate = 44100
    notes = [261, 293, 329, 293, 261, 220, 261, 293]  # C D E D C A C D
    duration_per_note = 0.4
    all_samples = []
    for freq in notes:
        n_samples = int(sample_rate * duration_per_note)
        for i in range(n_samples):
            t = i / sample_rate
            vibrato = math.sin(2 * math.pi * 5 * t) * 3
            val = 0.15 * math.sin(2 * math.pi * (freq + vibrato) * t)
            val += 0.05 * math.sin(2 * math.pi * (freq * 2 + vibrato) * t)
            # Fade out last 20%
            fade_start = int(n_samples * 0.8)
            if i >= fade_start:
                val *= 1.0 - ((i - fade_start) / (n_samples - fade_start))
            val = max(-1.0, min(1.0, val))
            s = int(val * 32767)
            all_samples.append(s)
            all_samples.append(s)  # stereo
    buf = array.array('h', all_samples)
    return pygame.mixer.Sound(buffer=buf)

# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------

async def main():
    pygame.init()
    try:
        pygame.mixer.init(44100, -16, 2, 512)
    except Exception:
        pass
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spearfisherz")
    # load_face_image()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)
    big_font = pygame.font.SysFont("consolas", 48, bold=True)
    med_font = pygame.font.SysFont("consolas", 28)
    small_font = pygame.font.SysFont("consolas", 14)

    # Touch / joystick state
    touch_move = [0, 0]  # normalised dx, dy  (-1..1)
    touch_fire = False
    touch_joy_active = False  # is finger on joystick
    touch_joy_id = None
    touch_knob = list(JOYSTICK_CENTER)  # visual knob position

    # Load sounds (with browser fallback)
    snd_fire = _safe_sound(create_fire_sound)
    snd_ouch = _safe_sound(create_ouch_sound)
    snd_score = _safe_sound(create_score_sound)
    snd_breath = _safe_sound(create_breath_sound)
    snd_theme = _safe_sound(create_theme_loop)
    breath_sound_played = False

    def reset_game():
        nonlocal breath_sound_played
        breath_sound_played = False
        return {
            "px": 100,
            "py": SCREEN_HEIGHT // 2,
            "prev_px": 100,
            "prev_py": SCREEN_HEIGHT // 2,
            "lives": 3,
            "score": 0,
            "spear": None,  # dict: x, y, state ("out"/"returning"), caught_fish
            "rocks": [],
            "fishes": [],
            "bubbles": [],
            "last_rock_spawn": pygame.time.get_ticks(),
            "last_fish_spawn": pygame.time.get_ticks(),
            "last_spear_time": 0,
            "invincible_until": 0,
            "fin_timer": 0.0,
            "breath": BREATH_MAX,
            "breath_damage_accum": 0.0,
            "state": "menu",  # menu, playing, gameover
        }

    g = reset_game()
    
    # Start theme music
    try:
        snd_theme_channel = pygame.mixer.Channel(0)
    except Exception:
        snd_theme_channel = _SilentChannel()

    def spawn_rock():
        w = random.randint(MIN_ROCK_WIDTH, MAX_ROCK_WIDTH)
        h = random.randint(MIN_ROCK_HEIGHT, MAX_ROCK_HEIGHT)
        y = SEA_BOTTOM_Y - h  # anchored to bottom
        shape = generate_rock_shape(w, h)
        g["rocks"].append({"x": SCREEN_WIDTH + 10, "y": y, "w": w, "h": h, "shape": shape})

    def spawn_fish():
        fish_type = random.choices(
            ["parrotfish", "seabream", "grouper"],
            weights=[50, 30, 20],
            k=1
        )[0]
        info = FISH_TYPES[fish_type]
        y = random.randint(SURFACE_Y + 30, SCREEN_HEIGHT - info["h"] - 40)
        g["fishes"].append({"x": SCREEN_WIDTH + 10, "y": y, "type": fish_type})

    def add_bubble(x, y):
        g["bubbles"].append([x, y, random.randint(2, 5), random.uniform(-0.3, -1.0)])

    running = True
    while running:
        # Play theme loop
        if not snd_theme_channel.get_busy():
            snd_theme_channel.play(snd_theme)

        dt = clock.tick(FPS)
        dt_sec = dt / 1000.0
        now = pygame.time.get_ticks()

        # --- Events ---
        touch_fire = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Touch / mouse handling ---
            if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.FINGERDOWN:
                    tx = event.x * SCREEN_WIDTH
                    ty = event.y * SCREEN_HEIGHT
                    tid = event.finger_id
                else:
                    tx, ty = event.pos
                    tid = -1

                if g["state"] in ("menu", "gameover"):
                    # Tap anywhere acts as ENTER
                    if g["state"] == "menu":
                        g = reset_game()
                        g["state"] = "playing"
                    elif g["state"] == "gameover":
                        g = reset_game()
                        g["state"] = "playing"
                elif g["state"] == "playing":
                    # Check joystick area
                    jdx = tx - JOYSTICK_CENTER[0]
                    jdy = ty - JOYSTICK_CENTER[1]
                    if math.hypot(jdx, jdy) <= JOYSTICK_RADIUS * 1.5:
                        touch_joy_active = True
                        touch_joy_id = tid
                    # Check fire button
                    elif math.hypot(tx - FIRE_BUTTON_CENTER[0], ty - FIRE_BUTTON_CENTER[1]) <= FIRE_BUTTON_RADIUS * 1.3:
                        touch_fire = True

            if event.type in (pygame.FINGERMOTION, pygame.MOUSEMOTION):
                if event.type == pygame.FINGERMOTION:
                    tx = event.x * SCREEN_WIDTH
                    ty = event.y * SCREEN_HEIGHT
                    tid = event.finger_id
                else:
                    tx, ty = event.pos
                    tid = -1
                    if not pygame.mouse.get_pressed()[0]:
                        continue

                if touch_joy_active and tid == touch_joy_id:
                    jdx = tx - JOYSTICK_CENTER[0]
                    jdy = ty - JOYSTICK_CENTER[1]
                    dist = math.hypot(jdx, jdy)
                    if dist > JOYSTICK_RADIUS:
                        jdx = jdx / dist * JOYSTICK_RADIUS
                        jdy = jdy / dist * JOYSTICK_RADIUS
                    touch_move[0] = jdx / JOYSTICK_RADIUS
                    touch_move[1] = jdy / JOYSTICK_RADIUS
                    touch_knob[0] = JOYSTICK_CENTER[0] + jdx
                    touch_knob[1] = JOYSTICK_CENTER[1] + jdy

            if event.type in (pygame.FINGERUP, pygame.MOUSEBUTTONUP):
                if event.type == pygame.FINGERUP:
                    tid = event.finger_id
                else:
                    tid = -1
                if tid == touch_joy_id:
                    touch_joy_active = False
                    touch_joy_id = None
                    touch_move[0] = 0
                    touch_move[1] = 0
                    touch_knob[0] = JOYSTICK_CENTER[0]
                    touch_knob[1] = JOYSTICK_CENTER[1]

            if event.type == pygame.KEYDOWN:
                if g["state"] == "menu" and event.key == pygame.K_RETURN:
                    g = reset_game()
                    g["state"] = "playing"
                elif g["state"] == "gameover" and event.key == pygame.K_RETURN:
                    g = reset_game()
                    g["state"] = "playing"
                elif g["state"] == "playing" and event.key == pygame.K_SPACE:
                    if g["spear"] is None and now - g["last_spear_time"] > SPEAR_COOLDOWN:
                        gun_tip = g["px"] + 32 + PLAYER_BODY_W
                        g["spear"] = {
                            "x": gun_tip,
                            "y": g["py"] + 6,
                            "state": "out",
                            "caught_fish": None,
                            "origin_x": gun_tip,
                        }
                        g["last_spear_time"] = now
                        snd_fire.play()

        if g["state"] == "playing":
            # --- Fin animation ---
            g["fin_timer"] += dt * 0.005
            fin_offset = math.sin(g["fin_timer"] * 4) * 3

            # Save previous position for movement detection
            g["prev_px"] = g["px"]
            g["prev_py"] = g["py"]

            # --- Player movement ---
            keys = pygame.key.get_pressed()
            dx = 0
            dy = 0
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += 1
            # Merge touch input
            dx += touch_move[0]
            dy += touch_move[1]
            # Clamp
            dx = max(-1, min(1, dx))
            dy = max(-1, min(1, dy))
            g["py"] = max(SURFACE_Y - 5, min(SCREEN_HEIGHT - PLAYER_BODY_H - 5, g["py"] + dy * PLAYER_SPEED))
            g["px"] = max(5, min(SCREEN_WIDTH // 2, g["px"] + dx * PLAYER_SPEED))

            # Touch fire
            if touch_fire and g["spear"] is None and now - g["last_spear_time"] > SPEAR_COOLDOWN:
                gun_tip = g["px"] + 32 + PLAYER_BODY_W
                g["spear"] = {
                    "x": gun_tip,
                    "y": g["py"] + 6,
                    "state": "out",
                    "caught_fish": None,
                    "origin_x": gun_tip,
                }
                g["last_spear_time"] = now
                snd_fire.play()

            # Player movement magnitude this frame
            player_move = abs(g["px"] - g["prev_px"]) + abs(g["py"] - g["prev_py"])

            # --- Breath ---
            on_surface = g["py"] <= SURFACE_Y + 10
            if on_surface:
                g["breath"] = min(BREATH_MAX, g["breath"] + BREATH_REFILL_RATE * dt_sec)
                g["breath_damage_accum"] = 0.0
            else:
                g["breath"] -= dt_sec
            if g["breath"] <= 0:
                g["breath"] = 0
                if not breath_sound_played:
                    snd_breath.play()
                    breath_sound_played = True
                g["breath_damage_accum"] += dt_sec
                while g["breath_damage_accum"] >= BREATH_DAMAGE_INTERVAL:
                    g["breath_damage_accum"] -= BREATH_DAMAGE_INTERVAL
                    g["lives"] -= 1
                    if g["lives"] <= 0:
                        g["state"] = "gameover"
                        break

            if on_surface:
                breath_sound_played = False

            # --- Spawn ---
            if now - g["last_rock_spawn"] > ROCK_SPAWN_INTERVAL:
                spawn_rock()
                g["last_rock_spawn"] = now
            if now - g["last_fish_spawn"] > FISH_SPAWN_INTERVAL:
                spawn_fish()
                g["last_fish_spawn"] = now

            # Random bubbles from player
            if random.random() < 0.1:
                add_bubble(g["px"] + 15, g["py"])

            # --- Update spear (out then return) ---
            spear = g["spear"]
            if spear is not None:
                gun_tip_x = g["px"] + 32 + PLAYER_BODY_W
                if spear["state"] == "out":
                    spear["x"] += SPEAR_SPEED
                    # Max range: twice the player body length from gun tip
                    if spear["x"] >= spear["origin_x"] + SPEAR_LENGTH:
                        spear["state"] = "returning"
                elif spear["state"] == "returning":
                    spear["x"] -= SPEAR_SPEED
                    if spear["x"] <= gun_tip_x:
                        # Spear returned — process caught fish
                        if spear["caught_fish"] is not None:
                            pts = FISH_TYPES[spear["caught_fish"]["type"]]["points"]
                            g["score"] += pts
                            snd_score.play()
                            for _ in range(5):
                                add_bubble(gun_tip_x, g["py"] + 6)
                        g["spear"] = None
                # Move caught fish with spear
                if spear is not None and spear["caught_fish"] is not None:
                    spear["caught_fish"]["x"] = spear["x"] + 10
                    spear["caught_fish"]["y"] = spear["y"] - 4

            # --- Update rocks ---
            for r in g["rocks"]:
                r["x"] -= ROCK_SPEED
            g["rocks"] = [r for r in g["rocks"] if r["x"] + r["w"] > -10]

            # --- Update fishes (with behaviors) ---
            pcx = g["px"] + 20  # player center
            pcy = g["py"] + 7
            for f in g["fishes"]:
                ftype = f["type"]
                info = FISH_TYPES[ftype]
                fcx = f["x"] + info["w"] // 2
                fcy = f["y"] + info["h"] // 2
                dist = math.hypot(fcx - pcx, fcy - pcy)

                if ftype == "parrotfish":
                    # Slowly swims left, slight vertical wobble
                    f["x"] -= FISH_SPEED_BASE
                    f["y"] += math.sin(now * 0.003 + f["x"] * 0.1) * 0.5

                elif ftype == "seabream":
                    # If player is close and moving a lot, flee right quickly
                    if dist < SCARE_DISTANCE and player_move > SCARE_MOVE_THRESHOLD:
                        # Swim away from player fast
                        dx = fcx - pcx
                        dy = fcy - pcy
                        d = max(1, math.hypot(dx, dy))
                        f["x"] += dx / d * SCARE_FLEE_SPEED
                        f["y"] += dy / d * SCARE_FLEE_SPEED
                    else:
                        f["x"] -= FISH_SPEED_BASE

                elif ftype == "grouper":
                    # Slightly attracted to player
                    f["x"] -= FISH_SPEED_BASE * 0.7
                    dx = pcx - fcx
                    dy = pcy - fcy
                    d = max(1, math.hypot(dx, dy))
                    f["x"] += dx / d * GROUPER_ATTRACT_SPEED
                    f["y"] += dy / d * GROUPER_ATTRACT_SPEED

            g["fishes"] = [f for f in g["fishes"] if -50 < f["x"] < SCREEN_WIDTH + 100
                           and SURFACE_Y - 20 < f["y"] < SCREEN_HEIGHT + 20]

            # --- Update bubbles ---
            for b in g["bubbles"]:
                b[1] += b[3]
                b[0] += random.uniform(-0.3, 0.3)
            g["bubbles"] = [b for b in g["bubbles"] if b[1] > SURFACE_Y]

            # --- Collisions: spear ↔ fish ---
            if spear is not None and spear["state"] == "out" and spear["caught_fish"] is None:
                spear_rect = pygame.Rect(spear["x"], spear["y"], 26, 5)
                for f in g["fishes"][:]:
                    info = FISH_TYPES[f["type"]]
                    fish_rect = pygame.Rect(f["x"], f["y"], info["w"], info["h"])
                    if spear_rect.colliderect(fish_rect):
                        spear["caught_fish"] = f
                        spear["state"] = "returning"
                        g["fishes"].remove(f)
                        break

            # --- Collisions: player ↔ rock ---
            player_rect = pygame.Rect(g["px"], g["py"], 38, PLAYER_BODY_H)
            if now > g["invincible_until"]:
                for r in g["rocks"]:
                    rock_rect = pygame.Rect(r["x"] + 5, r["y"] + 5, r["w"] - 10, r["h"] - 10)
                    if player_rect.colliderect(rock_rect):
                        g["lives"] -= 1
                        g["invincible_until"] = now + 1500
                        snd_ouch.play()
                        if g["lives"] <= 0:
                            g["state"] = "gameover"
                        break
        else:
            fin_offset = 0

        # --- Draw ---
        # Sky
        screen.fill(SKY_BLUE)
        # Water
        pygame.draw.rect(screen, WATER_TOP, (0, SURFACE_Y, SCREEN_WIDTH, SCREEN_HEIGHT - SURFACE_Y))
        pygame.draw.rect(screen, WATER_BOT, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        # Sandy bottom
        pygame.draw.rect(screen, SAND, (0, SEA_BOTTOM_Y, SCREEN_WIDTH, SCREEN_HEIGHT - SEA_BOTTOM_Y))
        # Water surface line
        pygame.draw.line(screen, WHITE, (0, SURFACE_Y), (SCREEN_WIDTH, SURFACE_Y), 2)

        # Wave decorations on surface
        for wx in range(0, SCREEN_WIDTH, 30):
            offset = math.sin((now / 500) + wx * 0.1) * 4
            pygame.draw.arc(screen, WHITE,
                            (wx, SURFACE_Y - 6 + offset, 30, 12), 0, math.pi, 2)

        if g["state"] == "menu":
            title = big_font.render("SPEARFISHERZ", True, YELLOW)
            sub = med_font.render("Press ENTER to start", True, WHITE)
            ctrl = font.render("Arrow keys / WASD = move   SPACE = shoot", True, WHITE)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
            screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 260))
            screen.blit(ctrl, (SCREEN_WIDTH // 2 - ctrl.get_width() // 2, 320))
            # Decorative fish
            draw_fish(screen, 280, 420, "parrotfish")
            draw_fish(screen, 380, 440, "seabream")
            draw_fish(screen, 500, 430, "grouper")
            # Point legend
            screen.blit(small_font.render("Parrotfish +1   Sea Bream +10   Grouper -20", True, WHITE),
                        (SCREEN_WIDTH // 2 - 170, 490))

        elif g["state"] == "playing" or g["state"] == "gameover":
            # Rocks
            for r in g["rocks"]:
                draw_rock(screen, r)
            # Fishes
            for f in g["fishes"]:
                draw_fish(screen, f["x"], f["y"], f["type"])
            # Spear + rope + caught fish
            spear = g["spear"]
            if spear is not None:
                draw_spear_shaft(screen, spear["x"], spear["y"], g["px"], g["py"])
                if spear["caught_fish"] is not None:
                    cf = spear["caught_fish"]
                    draw_fish(screen, cf["x"], cf["y"], cf["type"])
            # Bubbles
            draw_bubbles(screen, g["bubbles"])
            # Player (blink when invincible)
            if g["state"] == "playing":
                if now > g["invincible_until"] or (now // 100) % 2 == 0:
                    draw_player(screen, g["px"], g["py"], fin_offset)

            # HUD
            for i in range(g["lives"]):
                draw_heart(screen, 10 + i * 22, 8, 18)
            score_txt = font.render(f"Score: {g['score']}", True, YELLOW)
            screen.blit(score_txt, (SCREEN_WIDTH - 160, 10))
            # Breath bar
            breath_label = small_font.render("Breath", True, WHITE)
            screen.blit(breath_label, (SCREEN_WIDTH - 160, 32))
            draw_breath_bar(screen, g["breath"], BREATH_MAX, SCREEN_WIDTH - 110, 30, 100, 14)

            if g["state"] == "gameover":
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 140))
                screen.blit(overlay, (0, 0))
                go_txt = big_font.render("GAME OVER", True, RED)
                sc_txt = med_font.render(f"Final Score: {g['score']}", True, YELLOW)
                re_txt = font.render("Press ENTER to restart", True, WHITE)
                screen.blit(go_txt, (SCREEN_WIDTH // 2 - go_txt.get_width() // 2, 200))
                screen.blit(sc_txt, (SCREEN_WIDTH // 2 - sc_txt.get_width() // 2, 270))
                screen.blit(re_txt, (SCREEN_WIDTH // 2 - re_txt.get_width() // 2, 330))

        # Draw touch controls (always on top, semi-transparent)
        if g["state"] == "playing":
            tc_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            # Joystick base
            pygame.draw.circle(tc_surf, (255, 255, 255, 40), JOYSTICK_CENTER, JOYSTICK_RADIUS)
            pygame.draw.circle(tc_surf, (255, 255, 255, 80), JOYSTICK_CENTER, JOYSTICK_RADIUS, 2)
            # Joystick knob
            pygame.draw.circle(tc_surf, (255, 255, 255, 120), (int(touch_knob[0]), int(touch_knob[1])), 22)
            # Fire button
            pygame.draw.circle(tc_surf, (255, 80, 80, 60), FIRE_BUTTON_CENTER, FIRE_BUTTON_RADIUS)
            pygame.draw.circle(tc_surf, (255, 80, 80, 120), FIRE_BUTTON_CENTER, FIRE_BUTTON_RADIUS, 3)
            # Label
            fire_lbl = small_font.render("FIRE", True, (255, 255, 255, 200))
            tc_surf.blit(fire_lbl, (FIRE_BUTTON_CENTER[0] - fire_lbl.get_width() // 2,
                                     FIRE_BUTTON_CENTER[1] - fire_lbl.get_height() // 2))
            screen.blit(tc_surf, (0, 0))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
