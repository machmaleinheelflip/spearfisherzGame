import pygame
import random
import sys
import math
import asyncio

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


# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spearfisherz")
    # load_face_image()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)
    big_font = pygame.font.SysFont("consolas", 48, bold=True)
    med_font = pygame.font.SysFont("consolas", 28)
    small_font = pygame.font.SysFont("consolas", 14)

    def reset_game():
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
        dt = clock.tick(FPS)
        dt_sec = dt / 1000.0
        now = pygame.time.get_ticks()

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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

        if g["state"] == "playing":
            # --- Fin animation ---
            g["fin_timer"] += dt * 0.005
            fin_offset = math.sin(g["fin_timer"] * 4) * 3

            # Save previous position for movement detection
            g["prev_px"] = g["px"]
            g["prev_py"] = g["py"]

            # --- Player movement ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                g["py"] = max(SURFACE_Y - 5, g["py"] - PLAYER_SPEED)  # allow going to surface
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                g["py"] = min(SCREEN_HEIGHT - PLAYER_BODY_H - 5, g["py"] + PLAYER_SPEED)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                g["px"] = max(5, g["px"] - PLAYER_SPEED)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                g["px"] = min(SCREEN_WIDTH // 2, g["px"] + PLAYER_SPEED)

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
                g["breath_damage_accum"] += dt_sec
                while g["breath_damage_accum"] >= BREATH_DAMAGE_INTERVAL:
                    g["breath_damage_accum"] -= BREATH_DAMAGE_INTERVAL
                    g["lives"] -= 1
                    if g["lives"] <= 0:
                        g["state"] = "gameover"
                        break

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
            lives_txt = font.render(f"Lives: {g['lives']}", True, WHITE)
            score_txt = font.render(f"Score: {g['score']}", True, YELLOW)
            screen.blit(lives_txt, (10, 10))
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

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
