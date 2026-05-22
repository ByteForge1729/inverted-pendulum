import pygame
import numpy as np
import sys
from cart_pole_dynamics import rk4_step, L_VAL
from swing_up import swing_up_force, should_handoff
from mpc_controller import mpc_force, should_use_mpc, mpc_fallback_needed
import time


# ── initialise ────────────────────────────────────────────────
pygame.init()

WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Inverted Pendulum — Interactive")
clock = pygame.time.Clock()

# ── colours ───────────────────────────────────────────────────
BG        = ( 15,  15,  15)
TRACK     = ( 60,  60,  60)
CART_COL  = ( 93, 202, 165)
POLE_COL  = (175, 169, 236)
BOB_COL   = (240, 153, 123)
TRAIL_COL = (240, 153, 123)
TEXT_COL  = (200, 200, 200)
DIM_COL   = ( 80,  80,  80)
PHASE_COL = ( 83,  74, 183)
GRID_COL  = ( 35,  35,  35)
WHITE     = (255, 255, 255)
FORCE_COL = (240, 200,  80)

# ── layout ────────────────────────────────────────────────────
SPLIT     = 750
ANIM_W    = SPLIT
PHASE_W   = WIDTH - SPLIT
PHASE_PAD = 40

# ── coordinate transforms ─────────────────────────────────────
ORIGIN_X = ANIM_W  // 2
ORIGIN_Y = HEIGHT  // 2 + 50
SCALE    = 100
L        = L_VAL

def to_px(x_m, y_m):
    return (int(ORIGIN_X + x_m * SCALE),
            int(ORIGIN_Y - y_m * SCALE))

# phase portrait range (fixed around upright equilibrium)
TH_RANGE  = 60    # degrees either side
THD_RANGE = 400

def to_phase_px(th_deg, thd_deg):
    px = SPLIT + PHASE_PAD + int(
        (th_deg + TH_RANGE) / (2 * TH_RANGE)
        * (PHASE_W - 2 * PHASE_PAD)
    )
    py = PHASE_PAD + int(
        (1 - (thd_deg + THD_RANGE) / (2 * THD_RANGE))
        * (HEIGHT - 2 * PHASE_PAD)
    )
    return px, py

# ── font ──────────────────────────────────────────────────────
font_sm = pygame.font.SysFont('monospace', 14)
font_md = pygame.font.SysFont('monospace', 16)

def draw_text(surf, text, x, y, colour=TEXT_COL, small=False):
    f = font_sm if small else font_md
    surf.blit(f.render(text, True, colour), (x, y))

# ── simulation state ──────────────────────────────────────────
THETA_INIT = np.radians(5)
state      = np.array([0.0, 0.0, THETA_INIT, 0.0])
DT         = 1 / 50        # 50fps physics timestep
F_MAGNITUDE = 8.0          # Newtons applied per keypress
current_F   = 0.0
sim_time    = 0.0
mpc_on = False
swing_up_on = False

# ── trail + phase history asthetics ──────────────────────────────────────
trail        = []
phase_hist   = []
MAX_TRAIL    = 120
MAX_PHASE    = 800

# ── phase background (cached) asthetics ─────────────────────────────────
def build_phase_bg():
    surf = pygame.Surface((PHASE_W, HEIGHT))
    surf.fill((22, 22, 28))

    for th in np.linspace(-TH_RANGE, TH_RANGE, 7):
        x, _ = to_phase_px(th, -THD_RANGE)
        x -= SPLIT
        pygame.draw.line(surf, GRID_COL, (x, PHASE_PAD),
                         (x, HEIGHT - PHASE_PAD), 1)
        draw_text(surf, f"{int(th)}°", x - 14,
                  HEIGHT - PHASE_PAD + 4, colour=DIM_COL, small=True)

    for thd in np.linspace(-THD_RANGE, THD_RANGE, 7):
        _, y = to_phase_px(-TH_RANGE, thd)
        pygame.draw.line(surf, GRID_COL,
                         (PHASE_PAD, y), (PHASE_W - PHASE_PAD, y), 1)
        draw_text(surf, f"{int(thd)}", PHASE_PAD - 36, y - 7,
                  colour=DIM_COL, small=True)

    _, zero_y = to_phase_px(-TH_RANGE, 0)
    pygame.draw.line(surf, (60, 60, 60),
                     (PHASE_PAD, zero_y), (PHASE_W - PHASE_PAD, zero_y), 1)
    zero_x, _ = to_phase_px(0, -THD_RANGE)
    zero_x -= SPLIT
    pygame.draw.line(surf, (60, 60, 60),
                     (zero_x, PHASE_PAD), (zero_x, HEIGHT - PHASE_PAD), 1)

    draw_text(surf, "phase portrait",    PHASE_PAD, 10)
    draw_text(surf, "x: θ   y: θ̇",
              PHASE_PAD, HEIGHT - 18, colour=DIM_COL, small=True)
    return surf

phase_bg = build_phase_bg()

# ── force arrow - asthetics ────────────────────────────────────────────────
def draw_force_arrow(cx, cy, F):
    if abs(F) < 0.1:
        return
    direction = 1 if F > 0 else -1
    arrow_len = int(abs(F) * 8)
    tip_x     = cx + direction * (50 + arrow_len)
    pygame.draw.line(screen, FORCE_COL,
                     (cx + direction * 50, cy), (tip_x, cy), 3)
    # arrowhead
    pygame.draw.polygon(screen, FORCE_COL, [
        (tip_x + direction * 10, cy),
        (tip_x - direction * 6,  cy - 6),
        (tip_x - direction * 6,  cy + 6),
    ])

# ── main draw ─────────────────────────────────────────────────
def draw_scene(st, F, t):
    screen.fill(BG)
    x_m, xd_m, th_m, thd_m = st

    # divider
    pygame.draw.line(screen, (40,40,40), (SPLIT,0), (SPLIT,HEIGHT), 1)

    # ── LEFT - asthetics──────────────────────────────────────────────────
    pygame.draw.line(screen, TRACK,
                     (50, ORIGIN_Y), (ANIM_W-50, ORIGIN_Y), 3)

    cx, cy = to_px(x_m, 0)
    wheel_y = cy + 23
    pygame.draw.circle(screen, DIM_COL, (cx-20, wheel_y), 8)
    pygame.draw.circle(screen, DIM_COL, (cx+20, wheel_y), 8)

    cart_rect = pygame.Rect(cx-40, cy-15, 80, 30)
    pygame.draw.rect(screen, CART_COL, cart_rect, border_radius=6)

    # force arrow on cart
    draw_force_arrow(cx, cy, F)

    hinge_px = to_px(x_m, 0)
    tip_px   = to_px(x_m + L*np.sin(th_m), L*np.cos(th_m))
    pygame.draw.line(screen, POLE_COL, hinge_px, tip_px, 5)

    trail.append(tip_px)
    if len(trail) > MAX_TRAIL:
        trail.pop(0)
    for k in range(1, len(trail)):
        ratio  = k / MAX_TRAIL
        colour = (int(TRAIL_COL[0]*ratio),
                  int(TRAIL_COL[1]*ratio),
                  int(TRAIL_COL[2]*ratio))
        pygame.draw.line(screen, colour, trail[k-1], trail[k], 2)

    pygame.draw.circle(screen, BOB_COL, tip_px, 12)

    # telemetry
    draw_text(screen, f"t     = {t:.2f} s",              20, 20)
    draw_text(screen, f"x     = {x_m:.3f} m",            20, 42)
    draw_text(screen, f"θ     = {np.degrees(th_m):.1f}°",20, 64)
    draw_text(screen, f"θ̇     = {np.degrees(thd_m):.1f} °/s", 20, 86)
    draw_text(screen, f"F     = {F:.1f} N",
              20, 108, colour=FORCE_COL if abs(F)>0.1 else DIM_COL)

    mpc_colour = (93, 202, 165) if mpc_on else DIM_COL
    su_colour  = (240, 200,  80) if swing_up_on else DIM_COL
    draw_text(screen, f"M     MPC      {'ON ✓' if mpc_on else 'OFF'}", 20, HEIGHT-118, colour=mpc_colour)
    draw_text(screen, f"S     SWING-UP {'ON ✓' if swing_up_on else 'OFF'}", 20, HEIGHT-98, colour=su_colour)
    draw_text(screen, "← →  apply force", 20, HEIGHT-76, colour=DIM_COL)
    draw_text(screen, "R     reset",       20, HEIGHT-54, colour=DIM_COL)
    draw_text(screen, "Q     quit",        20, HEIGHT-32, colour=DIM_COL)

    su_colour = (240, 200, 80) if swing_up_on else DIM_COL
    draw_text(screen, f"S     SWING-UP {'ON ✓' if swing_up_on else 'OFF'}", 20, HEIGHT-98, colour=su_colour)

    draw_text(screen, "← →  apply force",  20, HEIGHT-76, colour=DIM_COL)
    draw_text(screen, "R     reset",        20, HEIGHT-54, colour=DIM_COL)
    draw_text(screen, "Q     quit",         20, HEIGHT-32, colour=DIM_COL)

    # ── RIGHT: phase portrait - asthetics ──────────────────────────────────
    screen.blit(phase_bg, (SPLIT, 0))

    if len(phase_hist) > 1:
        for k in range(1, len(phase_hist)):
            ratio = k / len(phase_hist)
            col   = (int(PHASE_COL[0]*ratio),
                     int(PHASE_COL[1]*ratio),
                     int(PHASE_COL[2]*ratio + 100*(1-ratio)))
            p1 = to_phase_px(*phase_hist[k-1])
            p2 = to_phase_px(*phase_hist[k])
            pygame.draw.line(screen, col, p1, p2, 2)

    dot = to_phase_px(np.degrees(th_m), np.degrees(thd_m))
    pygame.draw.circle(screen, WHITE,     dot, 6)
    pygame.draw.circle(screen, PHASE_COL, dot, 4)

    pygame.display.flip()

# ── main loop ─────────────────────────────────────────────────
while True:
    current_F = 0.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                state     = np.array([0.0, 0.0, THETA_INIT, 0.0])
                sim_time  = 0.0
                trail.clear()
                phase_hist.clear()
            if event.key == pygame.K_q:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_m:
                mpc_on = not mpc_on
                trail.clear()
                phase_hist.clear()
            if event.key == pygame.K_s:
                swing_up_on = not swing_up_on
                if swing_up_on:
                    mpc_on = False
                    state[3] += 0.05    # tiny kick to break perfect-rest deadlock
                trail.clear()
                phase_hist.clear()
            if event.key == pygame.K_m:
                mpc_on = not mpc_on
                if mpc_on:
                    swing_up_on = False
                    mpc_on = False
                trail.clear()
                phase_hist.clear()

    # held keys — checked every frame
    keys = pygame.key.get_pressed()
    if swing_up_on:
        # check if we're close enough to hand off to LQR
        if should_handoff(state):
            swing_up_on = False
            mpc_on      = True       # automatic handoff
        else:
            current_F = swing_up_force(state)

    if mpc_on:
        wrapped      = state.copy()
        wrapped[2]   = (state[2] + np.pi) % (2 * np.pi) - np.pi
        if mpc_fallback_needed(state):
            mpc_on      = False
            swing_up_on = True
            current_F   = 0.0
        else:
            _t = time.perf_counter()
            current_F = mpc_force(wrapped)
            _ms = (time.perf_counter() - _t) * 1000
            print(f"MPC solve time: {_ms:.1f} ms",flush=True, end='\r')
    elif not swing_up_on:
        if keys[pygame.K_RIGHT]: current_F =  F_MAGNITUDE
        if keys[pygame.K_LEFT]:  current_F = -F_MAGNITUDE

    # physics step
    state    = rk4_step(state, current_F, DT)
    sim_time += DT

    # phase history
    phase_hist.append((np.degrees(state[2]),
                       np.degrees(state[3])))
    if len(phase_hist) > MAX_PHASE:
        phase_hist.pop(0)

    draw_scene(state, current_F, sim_time)
    clock.tick(50)