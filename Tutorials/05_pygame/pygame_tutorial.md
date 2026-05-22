# Pygame — real-time interactive graphics

**What this library does in one sentence:** Pygame gives you a window, a pixel buffer, and an event queue — the three things you need to draw something that moves in real time and responds to a keyboard.

For this project, pygame is the thing that lets us *feel* the cart-pole: push it with arrow keys, watch the pole swing, see the phase portrait trace out live. Matplotlib makes static plots; pygame makes the simulator playable.

---

## 1. Pygame vs matplotlib

| | matplotlib | pygame |
|--|------------|--------|
| use case | analysis, finished plots | live interaction |
| time model | call `show()`, get a picture | run a loop forever, redraw every frame |
| input | none | keyboard, mouse, joystick |
| frame rate | irrelevant | 50–60 fps target |
| typical line of code | `plt.plot(t, y)` | `pygame.draw.line(screen, RED, (10,10), (50,50), 3)` |

Use matplotlib for *thinking about* the simulation; use pygame for *driving* the simulation.

---

## 2. The game loop pattern

Every pygame program looks like this:

```python
while True:                      # forever, until the user quits
    for event in pygame.event.get():    # 1. handle input
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    # 2. update state (physics, etc.)
    state = rk4_step(state, F, DT)

    # 3. draw the new state
    screen.fill(BG)
    draw_scene(state)
    pygame.display.flip()        # 4. show what we drew

    clock.tick(50)               # 5. cap to 50 fps
```

The five steps — **events, update, draw, flip, tick** — appear in every loop. The physics goes in step 2; the rendering in step 3.

---

## 3. Initialisation

Before drawing anything you have to start pygame, open a window, and create a clock.

### `pygame.init()`

Starts every pygame subsystem (video, font, audio, etc.). Call it once at the top of your program.

```python
import pygame
pygame.init()
```

### `pygame.display.set_mode((width, height))`

Opens a window and returns the `Surface` you draw onto.

| Parameter | Meaning |
|-----------|---------|
| `(w, h)`  | Window size in pixels. |
| `flags`   | (optional) e.g. `pygame.FULLSCREEN`, `pygame.RESIZABLE`. |

```python
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
```

`screen` is the **back buffer** — drawing on it doesn't show anything until you call `pygame.display.flip()`.

### `pygame.display.set_caption(title)`

Sets the window title bar.

```python
pygame.display.set_caption("Inverted Pendulum — Interactive")
```

### `pygame.time.Clock()`

Returns a clock object used to throttle the loop to a target frame rate.

```python
clock = pygame.time.Clock()
# inside the loop:
clock.tick(50)        # sleeps just enough to hit 50 fps
```

Without `clock.tick(...)`, the loop runs as fast as your CPU allows — pegging a core to 100% and making the physics integrator take wildly variable steps. **Always cap the frame rate.**

---

## 4. The coordinate system — pygame vs physics

Pygame uses **screen coordinates**:

- origin `(0, 0)` is the **top-left**
- x increases to the **right**
- y increases **downward**
- units are pixels

Physics uses the opposite convention: origin at some chosen point, y *upward*, units in metres. The two don't match — you must convert.

The standard pattern is a `to_px(x_m, y_m)` helper:

```python
ORIGIN_X = WIDTH  // 2       # cart-track centred horizontally
ORIGIN_Y = HEIGHT // 2 + 50  # slightly below middle, leaves room above for the pole
SCALE    = 200               # pixels per metre

def to_px(x_m, y_m):
    return (int(ORIGIN_X + x_m * SCALE),
            int(ORIGIN_Y - y_m * SCALE))    # note the MINUS — flips y
```

Every draw call uses `to_px(x, y)` to convert the physics-space coordinates of the cart, hinge, and bob into pixel positions. The minus sign on `y_m * SCALE` is what flips physics-up to screen-down.

---

## 5. Drawing primitives

Every `pygame.draw.*` function follows the pattern `(surface, color, ...geometry..., width)`.

### `pygame.draw.line(surface, color, start, end, width)`

Draw a straight line.

| Parameter  | Meaning |
|------------|---------|
| `surface`  | What to draw on (usually `screen`). |
| `color`    | `(r, g, b)` tuple, 0–255 each. |
| `start`    | `(x, y)` pixel tuple. |
| `end`      | `(x, y)` pixel tuple. |
| `width`    | Line thickness in pixels. |

```python
pygame.draw.line(screen, (60, 60, 60), (50, ORIGIN_Y), (WIDTH-50, ORIGIN_Y), 3)
```

This is how the track and the pole are drawn.

### `pygame.draw.circle(surface, color, center, radius)`

Draw a filled circle.

| Parameter  | Meaning |
|------------|---------|
| `surface`  | Target. |
| `color`    | RGB tuple. |
| `center`   | `(x, y)` pixel tuple. |
| `radius`   | Radius in pixels. |
| `width`    | (optional) Outline thickness; `0` (default) = filled. |

```python
pygame.draw.circle(screen, (240, 153, 123), tip_px, 12)   # the pendulum bob
```

### `pygame.draw.rect(surface, color, rect, border_radius=0)`

Draw a filled rectangle. The `rect` argument is a `pygame.Rect` (see below).

| Parameter       | Meaning |
|-----------------|---------|
| `surface`       | Target. |
| `color`         | RGB tuple. |
| `rect`          | A `pygame.Rect` or `(x, y, w, h)` tuple. |
| `border_radius` | (optional) Corner rounding in pixels. |

```python
cart_rect = pygame.Rect(cx - 40, cy - 15, 80, 30)
pygame.draw.rect(screen, (93, 202, 165), cart_rect, border_radius=6)
```

### `pygame.Rect(x, y, w, h)`

A rectangle object. Defined by its **top-left** corner `(x, y)` and `(w, h)`. Used by `draw.rect`, collision tests, blit positions.

### `surface.fill(color)`

Paint the whole surface a single colour. Called once per frame on `screen` to clear the previous frame.

```python
screen.fill((15, 15, 15))   # dark grey background
```

### `pygame.display.flip()` — the double-buffer swap

You've been drawing to a hidden **back buffer**. `flip()` swaps it with what's on screen, making your drawing visible all at once. Without `flip()`, nothing appears.

Why double-buffered? If we drew directly to the visible buffer, you'd see the screen update piece by piece (lines appearing one by one) — flicker. Double buffering shows the whole frame atomically.

```python
pygame.display.flip()
```

Call this **once per frame**, after all drawing is done.

---

## 6. Surfaces and `blit`

A `Surface` is a 2-D pixel buffer. `screen` is one. You can also make your own.

### `pygame.Surface((w, h))`

Allocate a new off-screen surface to draw on.

```python
phase_surf = pygame.Surface((PHASE_W, HEIGHT))
phase_surf.fill((22, 22, 28))
# ... draw gridlines, labels, etc. on phase_surf ...
```

### `surface.blit(source, (x, y))`

Copy `source` onto `surface` at pixel position `(x, y)`.

```python
screen.blit(phase_surf, (SPLIT, 0))    # paste phase panel onto screen
```

### Why cache static backgrounds

The phase-portrait grid (axes, tick labels, zero lines) is **the same every frame**. Drawing it every frame is wasteful — for a complex grid it's tens of `draw.line` calls plus font rendering.

The trick:

1. Build the grid **once** on its own `Surface` (`build_phase_bg()`).
2. Every frame, `blit` that pre-rendered surface — one fast copy.
3. Only the *dynamic* part (current phase dot, trail) is drawn live.

You'll see this pattern in [Day_1/Output.py](../../Day_1/Output.py) at the `build_phase_bg()` function.

---

## 7. Event handling

Pygame collects input into an **event queue**. You drain it every frame.

### `pygame.event.get()`

Returns the list of events that happened since the last call. Loop over them:

```python
for event in pygame.event.get():
    if event.type == pygame.QUIT:
        pygame.quit(); sys.exit()
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_r:
            state[:] = INITIAL_STATE        # reset
        if event.key == pygame.K_q:
            pygame.quit(); sys.exit()
```

### `event.type` — what kind of event

| Constant            | Meaning |
|---------------------|---------|
| `pygame.QUIT`       | Window close button clicked. |
| `pygame.KEYDOWN`    | A key was *just pressed* (fires once per press). |
| `pygame.KEYUP`      | A key was *just released*. |
| `pygame.MOUSEBUTTONDOWN` / `MOUSEMOTION` | Mouse events (not used here). |

### `event.key` — which key

Inside `KEYDOWN`/`KEYUP` handlers, `event.key` tells you which key. The constants we use:

| Constant | Key |
|----------|-----|
| `K_LEFT`, `K_RIGHT`, `K_UP`, `K_DOWN` | Arrow keys. |
| `K_SPACE` | Spacebar. |
| `K_r`     | The R key (reset). |
| `K_q`     | The Q key (quit). |
| `K_ESCAPE` | Escape. |

### `pygame.key.get_pressed()` — held keys

A different API for keys that are *currently held down* (as opposed to just-pressed). Returns a sequence indexed by key constant:

```python
keys = pygame.key.get_pressed()
if keys[pygame.K_RIGHT]: current_F =  F_MAGNITUDE
if keys[pygame.K_LEFT]:  current_F = -F_MAGNITUDE
```

### `KEYDOWN` vs `get_pressed()` — when to use which

| Want…                                 | Use            |
|---------------------------------------|----------------|
| One action per press (jump, reset, quit)  | `KEYDOWN` in the event loop. |
| Continuous response while held (force, movement) | `pygame.key.get_pressed()`. |

For the cart-pole: **R and Q are `KEYDOWN`** (one press → one reset); **arrow keys are `get_pressed()`** (force applied as long as you hold the key).

---

## 8. Fonts and text

Drawing text takes three steps: pick a font, render text to a surface, blit the surface.

### `pygame.font.SysFont(name, size)`

Load a system font.

| Parameter | Meaning |
|-----------|---------|
| `name`    | Font name (`'monospace'`, `'Arial'`) or `None` for default. |
| `size`    | Pixel height. |

```python
font_sm = pygame.font.SysFont('monospace', 14)
font_md = pygame.font.SysFont('monospace', 16)
```

### `font.render(text, antialias, color)`

Render a string into a `Surface`.

| Parameter   | Meaning |
|-------------|---------|
| `text`      | The string. |
| `antialias` | `True` for smooth edges (almost always what you want). |
| `color`     | RGB tuple. |

```python
text_surf = font_md.render(f"t = {sim_time:.2f} s", True, (200, 200, 200))
screen.blit(text_surf, (20, 20))
```

The pattern is `render → blit` every frame for the live telemetry (time, angle, force).

---

## 9. Colours — the project palette

Pygame colours are `(r, g, b)` tuples with each channel 0–255.

```python
BG        = ( 15,  15,  15)    # near-black background
TRACK     = ( 60,  60,  60)    # cart rail
CART_COL  = ( 93, 202, 165)    # mint green
POLE_COL  = (175, 169, 236)    # lilac
BOB_COL   = (240, 153, 123)    # peach
PHASE_COL = ( 83,  74, 183)    # deep blue (phase-portrait trail)
TEXT_COL  = (200, 200, 200)    # off-white
FORCE_COL = (240, 200,  80)    # gold (force arrow)
```

Keep colour constants at the top of the file — never hard-code RGB tuples inside draw calls.

---

## 10. The physics loop pattern

The whole point: drive an ODE integrator from inside the game loop.

```python
DT          = 1 / 50         # physics step = 1 frame
state       = np.array([0.0, 0.0, np.radians(5), 0.0])
current_F   = 0.0
sim_time    = 0.0

while True:
    current_F = 0.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                state[:] = [0.0, 0.0, np.radians(5), 0.0]
                sim_time = 0.0
            if event.key == pygame.K_q:
                pygame.quit(); sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]: current_F =  F_MAGNITUDE
    if keys[pygame.K_LEFT]:  current_F = -F_MAGNITUDE

    state    = rk4_step(state, current_F, DT)   # one physics step per frame
    sim_time += DT

    draw_scene(state, current_F, sim_time)
    clock.tick(50)
```

`DT = 1/50` matches `clock.tick(50)` — one RK4 step per displayed frame. For faster pole dynamics you'd take *multiple* sub-steps per frame (e.g. 4 RK4 steps of `DT/4` each), then draw once. That decouples physics accuracy from visual frame rate.

---

## Quick reference — every pygame function used in this project

| Call | Purpose |
|------|---------|
| `pygame.init()`                              | Start pygame subsystems. |
| `pygame.display.set_mode((w, h))`            | Open a window, get a back-buffer surface. |
| `pygame.display.set_caption(s)`              | Window title. |
| `pygame.display.flip()`                      | Swap back and front buffers — make drawing visible. |
| `pygame.time.Clock()`                        | Frame-rate limiter. |
| `clock.tick(fps)`                            | Sleep just enough to hit `fps`. |
| `pygame.Surface((w, h))`                     | Create an off-screen drawing surface. |
| `surface.fill(color)`                        | Paint the whole surface. |
| `surface.blit(source, (x, y))`               | Copy `source` onto `surface` at `(x, y)`. |
| `pygame.draw.line(s, c, p1, p2, w)`          | Line. |
| `pygame.draw.circle(s, c, center, r)`        | Filled circle. |
| `pygame.draw.rect(s, c, rect, border_radius=…)` | Filled rectangle. |
| `pygame.draw.polygon(s, c, pts)`             | Filled polygon (used for the force arrowhead). |
| `pygame.Rect(x, y, w, h)`                    | Rectangle object. |
| `pygame.event.get()`                         | Drain the input event queue. |
| `event.type` constants: `QUIT`, `KEYDOWN`, `KEYUP` | Event kind. |
| `event.key` constants: `K_LEFT`, `K_RIGHT`, `K_SPACE`, `K_r`, `K_q` | Which key. |
| `pygame.key.get_pressed()`                   | Snapshot of held keys (one-per-press → use `KEYDOWN`). |
| `pygame.font.SysFont(name, size)`            | Load a font. |
| `font.render(text, antialias, color)`        | Render text to a surface. |
| `pygame.quit()`                              | Tear down pygame (paired with `sys.exit()`). |
