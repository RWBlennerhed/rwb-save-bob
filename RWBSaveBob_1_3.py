import pygame
import random
import math
import os
import sys

# ------------------------------------------------------------
# Android helpers for Pydroid / Android
# ------------------------------------------------------------
def hide_android_keyboard():
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        Context = autoclass('android.content.Context')
        input_manager = activity.getSystemService(Context.INPUT_METHOD_SERVICE)
        window = activity.getWindow()
        view = window.getDecorView()
        input_manager.hideSoftInputFromWindow(view.getWindowToken(), 0)
    except:
        pass

def vibrate_android(milliseconds=140):
    try:
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        Build_VERSION = autoclass('android.os.Build$VERSION')
        VibrationEffect = autoclass('android.os.VibrationEffect')

        activity = PythonActivity.mActivity
        vibrator = cast('android.os.Vibrator', activity.getSystemService(Context.VIBRATOR_SERVICE))

        if vibrator:
            if Build_VERSION.SDK_INT >= 26:
                effect = VibrationEffect.createOneShot(milliseconds, VibrationEffect.DEFAULT_AMPLITUDE)
                vibrator.vibrate(effect)
            else:
                vibrator.vibrate(milliseconds)
    except:
        pass

# ------------------------------------------------------------
# Save Bob v1.3
# Idea & design: (c) Robert William Blennerhed 2026
# Developed in collaboration with ChatGPT
# RWB Tech Lab
# ------------------------------------------------------------

pygame.init()
pygame.font.init()
hide_android_keyboard()

# ------------------------------------------------------------
# SCREEN
# ------------------------------------------------------------
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Save Bob v1.3")
clock = pygame.time.Clock()

# ------------------------------------------------------------
# COLORS
# ------------------------------------------------------------
BG_TOP = (18, 24, 42)
BG_BOTTOM = (42, 58, 90)
WHITE = (245, 245, 245)
BLACK = (0, 0, 0)
RED = (220, 70, 70)
DARK_RED = (120, 10, 10)
GREEN = (60, 220, 120)
DARK_GREEN = (30, 140, 70)
YELLOW = (240, 220, 80)
RING = (75, 95, 135)
DARK_GRAY = (70, 78, 95)
PANEL_BG = (18, 24, 36)
PANEL_BORDER = (180, 190, 215)
SOFT_TEXT = (210, 220, 235)
BTN_GREEN = (70, 230, 130)
BTN_GREEN_PRESSED = (40, 180, 95)

# ------------------------------------------------------------
# FONTS
# ------------------------------------------------------------
font_small = pygame.font.SysFont(None, max(34, SCREEN_W // 34))
font_medium = pygame.font.SysFont(None, max(50, SCREEN_W // 24))
font_big = pygame.font.SysFont(None, max(76, SCREEN_W // 14))
font_huge = pygame.font.SysFont(None, max(96, SCREEN_W // 11))

# ------------------------------------------------------------
# GAME GEOMETRY
# ------------------------------------------------------------
CENTER_X = SCREEN_W // 2
CENTER_Y = SCREEN_H // 2
BOB_RADIUS = min(SCREEN_W, SCREEN_H) // 9
ARROW_LENGTH = max(56, min(SCREEN_W, SCREEN_H) // 12)
ARROW_WIDTH = max(16, min(SCREEN_W, SCREEN_H) // 55)
ARROW_SPEED = max(12, min(SCREEN_W, SCREEN_H) // 68)
DEADLY_ARROW_SPEED = ARROW_SPEED * 1.18

# ------------------------------------------------------------
# LEVEL DATA
# ------------------------------------------------------------
LEVELS = {
    1: {"total": 10, "deadly": 1},
    2: {"total": 15, "deadly": 2},
    3: {"total": 20, "deadly": 3},
    4: {"total": 25, "deadly": 4},
    5: {"total": 30, "deadly": 5},
}
MAX_LEVEL = 5

# ------------------------------------------------------------
# TIMING
# ------------------------------------------------------------
LOSE_DELAY_MS = 1600
IMPLODE_TIME_MS = 850
SHAKE_TIME_MS = 420
WARNING_TIME_MS = 320

# ------------------------------------------------------------
# RED ARROW HINT FLASH - v1.3
# ------------------------------------------------------------
SHOW_RED_ARROWS = True
RED_ARROW_FLASH_MS = 1
RED_ARROW_FLASH_COUNT = 1
RED_ARROW_FLASH_GAP_MS = 5

# ------------------------------------------------------------
# IMAGE LOADING
# ------------------------------------------------------------
def load_and_scale_image(filename, size):
    if os.path.exists(filename):
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.smoothscale(img, (size, size))
    return None

bob_angry_img = load_and_scale_image("bob_angry.png", BOB_RADIUS * 2)
bob_happy_img = load_and_scale_image("bob_happy.png", BOB_RADIUS * 2)

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def normalize(vx, vy):
    d = math.hypot(vx, vy)
    if d == 0:
        return 0, 0
    return vx / d, vy / d

def draw_text(surface, text, font, color, x, y, center=True):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)

def draw_vertical_gradient(surface, ox=0, oy=0):
    for y in range(SCREEN_H):
        t = y / max(1, SCREEN_H - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (ox, y + oy), (SCREEN_W + ox, y + oy))

def draw_fallback_bob(surface, x, y, radius, angry=True):
    color = (165, 80, 220) if angry else (190, 110, 240)
    pygame.draw.circle(surface, color, (int(x), int(y)), int(radius))

    eye_y = y - radius * 0.20
    eye_dx = radius * 0.32
    eye_r = max(5, int(radius * 0.10))

    pygame.draw.circle(surface, WHITE, (int(x - eye_dx), int(eye_y)), eye_r)
    pygame.draw.circle(surface, WHITE, (int(x + eye_dx), int(eye_y)), eye_r)
    pygame.draw.circle(surface, BLACK, (int(x - eye_dx), int(eye_y)), max(2, eye_r // 2))
    pygame.draw.circle(surface, BLACK, (int(x + eye_dx), int(eye_y)), max(2, eye_r // 2))

    if angry:
        pygame.draw.line(surface, BLACK,
                         (int(x - eye_dx - eye_r), int(eye_y - eye_r - 6)),
                         (int(x - eye_dx + eye_r), int(eye_y - eye_r)), 3)
        pygame.draw.line(surface, BLACK,
                         (int(x + eye_dx - eye_r), int(eye_y - eye_r)),
                         (int(x + eye_dx + eye_r), int(eye_y - eye_r - 6)), 3)
        rect = pygame.Rect(int(x - radius * 0.28), int(y + radius * 0.08),
                           int(radius * 0.56), int(radius * 0.24))
        pygame.draw.arc(surface, BLACK, rect, math.radians(15), math.radians(165), 3)
    else:
        rect = pygame.Rect(int(x - radius * 0.30), int(y - radius * 0.02),
                           int(radius * 0.60), int(radius * 0.36))
        pygame.draw.arc(surface, BLACK, rect, math.radians(15), math.radians(165), 3)

def draw_bob(surface, angry=True, scale=1.0, x=None, y=None):
    r = max(8, int(BOB_RADIUS * scale))
    if x is None:
        x = CENTER_X
    if y is None:
        y = CENTER_Y

    if angry and bob_angry_img:
        img = pygame.transform.smoothscale(bob_angry_img, (r * 2, r * 2))
        rect = img.get_rect(center=(x, y))
        surface.blit(img, rect)
    elif (not angry) and bob_happy_img:
        img = pygame.transform.smoothscale(bob_happy_img, (r * 2, r * 2))
        rect = img.get_rect(center=(x, y))
        surface.blit(img, rect)
    else:
        draw_fallback_bob(surface, x, y, r, angry=angry)

def heart_size_for_level(level):
    base = 26
    return max(10, base - (level - 1) * 3)

def draw_heart(surface, x, y, size, filled=True):
    if filled:
        color = GREEN
        outline = DARK_GREEN
    else:
        color = (70, 90, 80)
        outline = (40, 55, 45)

    r = size // 3
    left_center = (x - r, y - r // 2)
    right_center = (x + r, y - r // 2)
    bottom = (x, y + size // 2)

    pygame.draw.circle(surface, color, left_center, r)
    pygame.draw.circle(surface, color, right_center, r)

    points = [
        (x - size // 2, y - r // 3),
        (x + size // 2, y - r // 3),
        bottom,
    ]
    pygame.draw.polygon(surface, color, points)

    pygame.draw.circle(surface, outline, left_center, r, 2)
    pygame.draw.circle(surface, outline, right_center, r, 2)
    pygame.draw.polygon(surface, outline, points, 2)

# ------------------------------------------------------------
# GLOBAL GAME STATE HELPERS FOR ARROW METHODS
# ------------------------------------------------------------
safe_total = 0
deadly_total = 0
safe_cleared = 0
deadly_cleared = 0
arrows = []

def remaining_safe_arrows():
    return [a for a in arrows if a.active and not a.deadly]

def deadly_phase_open():
    return len(remaining_safe_arrows()) == 0

# ------------------------------------------------------------
# ARROW CLASS
# ------------------------------------------------------------
class Arrow:
    def __init__(self, angle_deg, dist_from_center, deadly=False):
        self.angle = math.radians(angle_deg)
        self.cx = CENTER_X + math.cos(self.angle) * dist_from_center
        self.cy = CENTER_Y + math.sin(self.angle) * dist_from_center

        to_bob_x = CENTER_X - self.cx
        to_bob_y = CENTER_Y - self.cy
        self.dir_x, self.dir_y = normalize(to_bob_x, to_bob_y)

        self.deadly = deadly
        self.active = True
        self.flying = False
        self.attacking_bob = False
        self.warning = False
        self.warning_until = 0
        self.vel_x = 0.0
        self.vel_y = 0.0

        # Red arrow hint flash - v1.3
        self.hint_flash = False
        self.hint_flash_until = 0
        self.hint_flashes_left = RED_ARROW_FLASH_COUNT if deadly else 0
        self.next_hint_flash_at = pygame.time.get_ticks() + random.randint(600, 1600)

    def get_tip(self):
        return (
            self.cx + self.dir_x * ARROW_LENGTH,
            self.cy + self.dir_y * ARROW_LENGTH
        )

    def get_body_points(self):
        px = -self.dir_y
        py = self.dir_x

        tip_x, tip_y = self.get_tip()
        tail_x, tail_y = self.cx, self.cy

        shaft_len = ARROW_LENGTH * 0.58
        shaft_front_x = tail_x + self.dir_x * shaft_len
        shaft_front_y = tail_y + self.dir_y * shaft_len

        half_w = ARROW_WIDTH * 0.36
        head_w = ARROW_WIDTH * 0.95

        tail_left = (tail_x + px * half_w, tail_y + py * half_w)
        tail_right = (tail_x - px * half_w, tail_y - py * half_w)
        front_left = (shaft_front_x + px * half_w, shaft_front_y + py * half_w)
        front_right = (shaft_front_x - px * half_w, shaft_front_y - py * half_w)
        head_left = (shaft_front_x + px * head_w, shaft_front_y + py * head_w)
        head_right = (shaft_front_x - px * head_w, shaft_front_y - py * head_w)

        return [tail_left, front_left, head_left, (tip_x, tip_y), head_right, front_right, tail_right]

    def draw(self, surface, ox=0, oy=0):
        local_ox = ox
        local_oy = oy
        fill_color = WHITE
        outline_color = DARK_GRAY

        if self.warning or self.hint_flash:
            fill_color = RED
            outline_color = DARK_RED

        if self.warning:
            local_ox += random.randint(-4, 4)
            local_oy += random.randint(-4, 4)

        pts = []
        for p in self.get_body_points():
            pts.append((p[0] + local_ox, p[1] + local_oy))

        pygame.draw.polygon(surface, fill_color, pts)
        pygame.draw.polygon(surface, outline_color, pts, 2)

    def contains_point(self, px, py):
        if self.warning:
            hit_radius = ARROW_LENGTH * 1.05
        elif self.deadly:
            hit_radius = ARROW_LENGTH * 0.95
        else:
            hit_radius = ARROW_LENGTH * 0.78
        return distance(px, py, self.cx, self.cy) <= hit_radius

    def launch_outward(self):
        away_x = self.cx - CENTER_X
        away_y = self.cy - CENTER_Y
        nx, ny = normalize(away_x, away_y)
        self.dir_x = nx
        self.dir_y = ny
        self.vel_x = nx * ARROW_SPEED
        self.vel_y = ny * ARROW_SPEED
        self.flying = True
        self.attacking_bob = False
        self.warning = False
        self.warning_until = 0
        self.hint_flash = False

    def force_safe_outward(self):
        self.attacking_bob = False
        self.warning = False
        self.warning_until = 0
        self.hint_flash = False
        self.launch_outward()

    def launch_into_bob(self):
        to_bob_x = CENTER_X - self.cx
        to_bob_y = CENTER_Y - self.cy
        nx, ny = normalize(to_bob_x, to_bob_y)
        self.dir_x = nx
        self.dir_y = ny
        self.vel_x = nx * DEADLY_ARROW_SPEED
        self.vel_y = ny * DEADLY_ARROW_SPEED
        self.flying = True
        self.attacking_bob = True
        self.warning = False
        self.warning_until = 0
        self.hint_flash = False

    def start_warning(self):
        self.warning = True
        self.warning_until = pygame.time.get_ticks() + WARNING_TIME_MS
        self.flying = False
        self.attacking_bob = False
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.hint_flash = False

    def update_warning(self):
        if self.warning and pygame.time.get_ticks() >= self.warning_until:
            self.warning = False
            if deadly_phase_open():
                self.force_safe_outward()
            else:
                self.launch_into_bob()

    def update_hint_flash(self):
           if not SHOW_RED_ARROWS:
               return

           if not self.deadly:
               return

           if self.flying or self.warning or not self.active:
              self.hint_flash = False
              return

           if self.hint_flashes_left <= 0:
              self.hint_flash = False
              return

           now = pygame.time.get_ticks()

           if self.hint_flash and now >= self.hint_flash_until:
              self.hint_flash = False
              self.next_hint_flash_at = now + RED_ARROW_FLASH_GAP_MS

           elif (not self.hint_flash) and now >= self.next_hint_flash_at:
              self.hint_flash = True
              self.hint_flash_until = now + RED_ARROW_FLASH_MS
              self.hint_flashes_left -= 1

    def update(self):
        self.update_hint_flash()

        if self.warning:
            self.update_warning()
        elif self.flying:
            self.cx += self.vel_x
            self.cy += self.vel_y

    def is_offscreen(self):
        margin = 170
        return (
            self.cx < -margin or self.cx > SCREEN_W + margin or
            self.cy < -margin or self.cy > SCREEN_H + margin
        )

# ------------------------------------------------------------
# REMAINING GAME STATE
# ------------------------------------------------------------
level = 1
score = 0
best_level = 1

state = "play"
state_timer = 0
message = ""

shake_until = 0
flash_until = 0
level_score = 0

next_button_rect = None
button_pressed_visual = False

# ------------------------------------------------------------
# GAME FUNCTIONS
# ------------------------------------------------------------
def get_level_info(level_number):
    return LEVELS.get(level_number, LEVELS[MAX_LEVEL])

def remaining_active_arrows():
    return [a for a in arrows if a.active]

def start_shake_and_flash():
    global shake_until, flash_until
    now = pygame.time.get_ticks()
    shake_until = now + SHAKE_TIME_MS
    flash_until = now + 180

def trigger_loss(reason):
    global state, state_timer, message
    state = "lose"
    state_timer = pygame.time.get_ticks()
    message = reason
    start_shake_and_flash()

def trigger_win():
    global state, state_timer, message, score, best_level, level_score
    state = "win"
    state_timer = pygame.time.get_ticks()
    level_score = safe_total + deadly_total
    score += level_score
    message = "Bob is saved!"
    best_level = max(best_level, level)

def create_level(level_number):
    global arrows, safe_cleared, safe_total, deadly_cleared, deadly_total
    global next_button_rect, button_pressed_visual

    arrows = []
    safe_cleared = 0
    deadly_cleared = 0
    next_button_rect = None
    button_pressed_visual = False

    info = get_level_info(level_number)
    total_arrows = info["total"]
    deadly_count = info["deadly"]
    safe_total = total_arrows - deadly_count
    deadly_total = deadly_count

    angles = []
    tries = 0
    min_gap = max(8, int(360 / (total_arrows + 4)))

    while len(angles) < total_arrows and tries < 4000:
        tries += 1
        a = random.randint(0, 359)
        ok = True
        for old in angles:
            diff = abs((a - old + 180) % 360 - 180)
            if diff < min_gap:
                ok = False
                break
        if ok:
            angles.append(a)

    if len(angles) < total_arrows:
        step = 360 / total_arrows
        angles = [int(i * step) for i in range(total_arrows)]

    deadly_indices = set(random.sample(range(total_arrows), deadly_count))

    base_dist = BOB_RADIUS + 100
    max_dist = min(SCREEN_W, SCREEN_H) // 2 - 70

    for i, angle in enumerate(angles):
        dist_from_center = random.randint(base_dist, max_dist)
        arrows.append(Arrow(angle, dist_from_center, deadly=(i in deadly_indices)))

def draw_hearts(surface, ox=0, oy=0):
    size = heart_size_for_level(level)
    gap = size + 6
    per_row = max(6, SCREEN_W // gap - 1)
    start_x = 22 + size // 2 + ox
    start_y = 26 + size // 2 + oy

    total_hearts = safe_total + deadly_total
    filled_hearts = safe_cleared + deadly_cleared

    for i in range(total_hearts):
        row = i // per_row
        col = i % per_row
        x = start_x + col * gap
        y = start_y + row * (size + 8)
        filled = i < filled_hearts
        draw_heart(surface, x, y, size, filled=filled)

def draw_win_panel(surface, pressed=False):
    global next_button_rect

    panel_w = int(SCREEN_W * 0.78)
    panel_h = int(SCREEN_H * 0.62)
    panel_x = (SCREEN_W - panel_w) // 2
    panel_y = (SCREEN_H - panel_h) // 2

    shadow = pygame.Surface((panel_w + 16, panel_h + 16), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 90))
    surface.blit(shadow, (panel_x + 8, panel_y + 10))

    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(surface, PANEL_BG, panel, border_radius=24)
    pygame.draw.rect(surface, PANEL_BORDER, panel, 3, border_radius=24)

    draw_text(surface, f"LEVEL {level} CLEARED!", font_big, GREEN, SCREEN_W // 2, panel_y + 70)

    draw_bob(surface, angry=False, scale=0.75, x=SCREEN_W // 2, y=panel_y + 220)

    if safe_cleared == safe_total and deadly_cleared == deadly_total:
        glow = 170 + int(85 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.008)))
        glow_color = (glow // 3, glow, glow // 3)

        for offset in (6, 4, 2):
            draw_text(surface, "PERFECT CLEAR!", font_medium, glow_color,
                      SCREEN_W // 2, panel_y + 320 + offset)

        draw_text(surface, "PERFECT CLEAR!", font_medium, GREEN,
                  SCREEN_W // 2, panel_y + 320)

    stats_y = panel_y + 370
    gap = 50

    draw_text(surface, f"Safe arrows: {safe_cleared}/{safe_total}", font_medium, SOFT_TEXT, SCREEN_W // 2, stats_y)
    draw_text(surface, f"Deadly arrows: {deadly_cleared}/{deadly_total}", font_medium, SOFT_TEXT, SCREEN_W // 2, stats_y + gap)
    draw_text(surface, f"Level score: {level_score}", font_medium, YELLOW, SCREEN_W // 2, stats_y + gap * 2)
    draw_text(surface, f"Total score: {score}", font_medium, WHITE, SCREEN_W // 2, stats_y + gap * 3)

    btn_w = 300
    btn_h = 86
    btn_x = SCREEN_W // 2 - btn_w // 2
    btn_y = panel_y + panel_h - 118
    next_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    btn_color = BTN_GREEN_PRESSED if pressed else BTN_GREEN
    pygame.draw.rect(surface, btn_color, next_button_rect, border_radius=16)
    pygame.draw.rect(surface, DARK_GREEN, next_button_rect, 3, border_radius=16)
    draw_text(surface, "NEXT LEVEL", font_medium, BLACK, SCREEN_W // 2, btn_y + btn_h // 2)

# ------------------------------------------------------------
# START FIRST LEVEL
# ------------------------------------------------------------
create_level(level)

# ------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------
running = True
while running:
    now = pygame.time.get_ticks()
    clock.tick(60)
    hide_android_keyboard()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            hide_android_keyboard()
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                level = 1
                score = 0
                best_level = 1
                state = "play"
                message = ""
                create_level(level)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            hide_android_keyboard()
            mx, my = event.pos

            if state == "play":
                clicked = None
                for a in arrows:
                    if a.active and not a.flying and not a.warning and a.contains_point(mx, my):
                        clicked = a
                        break

                if clicked:
                    if clicked.deadly:
                        if deadly_phase_open():
                            clicked.force_safe_outward()
                            deadly_cleared += 1
                        else:
                            vibrate_android(140)
                            clicked.start_warning()
                    else:
                        clicked.launch_outward()
                        safe_cleared += 1

            elif state == "win":
                if next_button_rect and next_button_rect.collidepoint(mx, my):
                    button_pressed_visual = True
                    if level >= MAX_LEVEL:
                        state = "complete"
                    else:
                        level += 1
                        create_level(level)
                        state = "play"
                        message = ""

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------
    if state == "play":
        for a in arrows:
            if not a.active:
                continue

            a.update()

            if deadly_phase_open() and (a.attacking_bob or a.warning):
                a.force_safe_outward()

            if a.attacking_bob:
                if distance(a.cx, a.cy, CENTER_X, CENTER_Y) <= BOB_RADIUS * 0.32:
                    a.active = False
                    trigger_loss("Wrong arrow hit Bob!")
            elif a.flying:
                if a.is_offscreen():
                    a.active = False

        if len(remaining_active_arrows()) == 0 and state == "play":
            deadly_cleared = deadly_total
            trigger_win()

    elif state == "lose":
        if now - state_timer >= LOSE_DELAY_MS:
            create_level(level)
            state = "play"
            message = ""

    elif state == "complete":
        pass

    # --------------------------------------------------------
    # SHAKE OFFSET
    # --------------------------------------------------------
    ox = 0
    oy = 0
    if now < shake_until:
        ox = random.randint(-10, 10)
        oy = random.randint(-8, 8)

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------
    draw_vertical_gradient(screen, ox, oy)

    pygame.draw.circle(screen, (35, 45, 80), (CENTER_X + ox, CENTER_Y + oy), BOB_RADIUS + 55)
    pygame.draw.circle(screen, RING, (CENTER_X + ox, CENTER_Y + oy), BOB_RADIUS + 28, 6)

    for a in arrows:
        if a.active:
            a.draw(screen, ox, oy)

    if state == "lose":
        elapsed = now - state_timer
        t = min(1.0, elapsed / IMPLODE_TIME_MS)
        bob_scale = max(0.03, 1.0 - t)

        for i in range(4):
            rr = int((BOB_RADIUS + 18) * (1.0 - t) + i * 9)
            if rr > 4:
                pygame.draw.circle(screen, (130, 40, 40), (CENTER_X + ox, CENTER_Y + oy), rr, 3)

        draw_bob(screen, angry=True, scale=bob_scale, x=CENTER_X + ox, y=CENTER_Y + oy)
    elif state == "play":
        draw_bob(screen, angry=True, scale=1.0, x=CENTER_X + ox, y=CENTER_Y + oy)
    else:
        draw_bob(screen, angry=False, scale=1.0, x=CENTER_X + ox, y=CENTER_Y + oy)

    draw_hearts(screen, ox, oy)

    draw_text(screen, f"Level: {level}", font_medium, WHITE, 20 + ox, 118 + oy, center=False)
    draw_text(screen, f"Score: {score}", font_medium, WHITE, 20 + ox, 180 + oy, center=False)
    draw_text(screen, f"Best: {best_level}", font_medium, YELLOW, 20 + ox, 242 + oy, center=False)

    if state == "play":
        draw_text(screen, "Tap white arrows", font_medium, WHITE, SCREEN_W // 2 + ox, 48 + oy)
        draw_text(screen, "but avoid the wrong one - be careful", font_medium, WHITE, SCREEN_W // 2 + ox, 95 + oy)

    draw_text(screen, "ESC = Quit   R = Restart", font_small, WHITE, SCREEN_W // 2 + ox, SCREEN_H - 34 + oy)

    if state == "win":
        draw_win_panel(screen, pressed=button_pressed_visual)

    elif state == "lose":
        draw_text(screen, "BOB IMPLODED!", font_huge, RED, SCREEN_W // 2 + ox, SCREEN_H // 2 - BOB_RADIUS - 90 + oy)
        draw_text(screen, message, font_medium, WHITE, SCREEN_W // 2 + ox, SCREEN_H // 2 + BOB_RADIUS + 78 + oy)

    elif state == "complete":
        draw_text(screen, "SAVE BOB COMPLETE!", font_huge, GREEN, SCREEN_W // 2 + ox, SCREEN_H // 2 - BOB_RADIUS - 95 + oy)
        draw_text(screen, "Happy Bob survived every level", font_medium, WHITE, SCREEN_W // 2 + ox, SCREEN_H // 2 + BOB_RADIUS + 40 + oy)
        draw_text(screen, f"Total score: {score}", font_medium, YELLOW, SCREEN_W // 2 + ox, SCREEN_H // 2 + BOB_RADIUS + 95 + oy)
        draw_text(screen, "Press R to play again", font_medium, WHITE, SCREEN_W // 2 + ox, SCREEN_H // 2 + BOB_RADIUS + 150 + oy)

    if now < flash_until:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 55))
        screen.blit(overlay, (0, 0))

    pygame.display.flip()

pygame.quit()
sys.exit()