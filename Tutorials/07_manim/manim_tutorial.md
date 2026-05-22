# Manim — mathematical animation engine

**What this library does in one sentence:** Manim renders Python code into a video — every line in your `Scene` becomes a polished, frame-by-frame animation of mathematical objects (dots, axes, equations, vectors) moving and transforming.

**Key distinction:** Manim is **not a simulator**. It does not compute physics. It plays back animations of objects whose positions you've already determined — either analytically or, more often for us, by running a simulation in NumPy first and saving the trajectory to `.npz`.

The workflow for this project is:

```
NumPy + SciPy  →  simulate  →  .npz file
                                  ↓
                           Manim loads, animates
```

---

## 1. Installation

```bash
pip install manim
```

System dependencies:

- **cairo** (graphics rendering) — usually bundled with manim on pip.
- **ffmpeg** (video encoding) — install separately:
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: download from ffmpeg.org and add to PATH
- **LaTeX** (only if you use `MathTex`) — `brew install mactex-no-gui` / `sudo apt install texlive-full`. Skip if you only use `Text`.

Test the install:

```bash
manim --version
```

---

## 2. Running a scene

A Manim file is a regular `.py` file containing one or more `Scene` subclasses. To render:

```bash
manim -pql scene.py SceneName
```

| Flag | Meaning |
|------|---------|
| `-p` | **Preview** — open the output in your default video player when done. |
| `-q` + letter | **Quality** — `l` (480p, fast), `m` (720p), `h` (1080p), `k` (4K). |
| `-ql` | Shorthand for `-q low`. Use `-qh` for final exports. |
| `-s`  | Save only the **last frame** as an image — quick for layout checks. |

**Output location:** Manim creates a `media/` folder next to your script:

```
media/
  videos/scene/{quality}/SceneName.mp4
  images/scene/SceneName.png      # if -s
```

For day-to-day work use `-pql` (preview, low quality, fast). Switch to `-qh` only when you're rendering the final version.

---

## 3. The `Scene` class pattern

Every animation lives inside a class that subclasses `Scene` and overrides `construct(self)`:

```python
from manim import *

class HelloScene(Scene):
    def construct(self):
        title = Text("hello, manim", font_size=48)
        self.play(FadeIn(title))
        self.wait(1)
        self.play(FadeOut(title))
```

Inside `construct`:

| Call | Meaning |
|------|---------|
| `self.add(mob)`    | Put `mob` on the scene **instantly** (no animation). |
| `self.play(anim)`  | Run an animation. Blocks until it finishes (default 1 s). |
| `self.wait(t)`     | Hold the current frame for `t` seconds. |
| `self.remove(mob)` | Remove `mob` from the scene. |

The animations themselves are objects: `FadeIn(mob)`, `Create(mob)`, `Transform(a, b)`, etc.

---

## 4. Core Mobjects (mathematical objects)

A **Mobject** is anything that can appear on screen. They share a position, colour, and stroke/fill.

### Geometric primitives

```python
Dot(point=ORIGIN, color=WHITE, radius=0.08)
Line(start, end, color=WHITE, stroke_width=4)
Rectangle(width=2, height=1, color=WHITE)
Square(side_length=2)
Circle(radius=1, color=WHITE)
Arrow(start, end, color=WHITE, buff=0.25)
```

Positions are 3-D arrays like `np.array([1, 2, 0])` — Manim's coordinate system is 3-D but for 2-D scenes you keep `z = 0`. There are also shorthand constants: `ORIGIN`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `UL`, `UR`, etc.

### Text and equations

```python
Text("hello", font_size=36, color=WHITE)
MathTex(r"\theta(t) = \theta_0 \cos(\omega t)")        # needs LaTeX installed
```

`Text` is plain text (TrueType). `MathTex` uses LaTeX — you can paste any equation from your sympy derivation.

### Grouping — `VGroup(*mobjects)`

Bundle multiple objects so you can move/scale/fade them together.

```python
cart_assembly = VGroup(cart_rect, left_wheel, right_wheel)
self.play(cart_assembly.animate.shift(2 * RIGHT))     # all three move together
```

---

## 5. Axes and plotting

`Axes` is the workhorse for plotting numerical data.

```python
axes = Axes(
    x_range=[0, 5, 1],        # [min, max, tick_step]
    y_range=[-1, 1, 0.5],
    x_length=8,               # how wide on screen, in manim units
    y_length=4,               # how tall on screen
    axis_config={"color": GREY},
)
```

### Plotting a function

```python
curve = axes.plot(lambda x: np.sin(2*x), color=BLUE)
self.play(Create(curve))
```

### Plotting pre-computed arrays — `plot_line_graph` (key for us)

This is **the** method you'll use for cart-pole data: hand it the `t` and `theta` arrays from your `.npz` file.

```python
data = axes.plot_line_graph(
    x_values=t_array,
    y_values=theta_array,
    line_color=YELLOW,
    add_vertex_dots=False,
)
self.play(Create(data))
```

### Labels and coordinate transforms

```python
axes.get_graph_label(curve, label="sin(2x)")           # text near the curve
point = axes.coords_to_point(2.5, 0.3)                  # (x, y) in axes → screen position
dot = Dot(point, color=RED)
```

`coords_to_point` is critical — it bridges *data coordinates* (whatever `x_range`/`y_range` you set) and *screen coordinates* (where to actually draw).

---

## 6. Animation types

| Animation                           | What it does |
|-------------------------------------|--------------|
| `Create(mob)`                       | Draw the object as if a pen is sketching it. |
| `Write(text_mob)`                   | Like `Create` but tuned for text. |
| `FadeIn(mob)` / `FadeOut(mob)`      | Opacity 0→1 / 1→0. |
| `Transform(a, b)`                   | Morph `a` into `b`. |
| `MoveAlongPath(mob, path)`          | Slide `mob` along a `Line` / `Arc` / curve. |
| `UpdateFromFunc(mob, fn)`           | Each frame, call `fn(mob)` to mutate it. |
| `mob.animate.method(...)`           | Auto-animate any `mob` method. `mob.animate.shift(UP)` interpolates the shift over the play time. |

### `ValueTracker(initial)` — animating a number

A `ValueTracker` is a Mobject that holds a single number. You animate the number; other Mobjects watch it via `add_updater` and respond.

```python
t_tracker = ValueTracker(0)

dot = Dot(color=YELLOW)
dot.add_updater(lambda m: m.move_to(axes.coords_to_point(
    t_tracker.get_value(),
    np.sin(2 * t_tracker.get_value()),
)))
self.add(dot)
self.play(t_tracker.animate.set_value(5), run_time=5)
```

While `t_tracker` ramps 0 → 5 over 5 seconds, the dot's updater repositions it each frame — tracing the curve.

### `UpdateFromFunc` — driving from pre-computed data

When you have a trajectory array (`states.shape == (N, 4)`) and want to animate frame-by-frame, this is the pattern:

```python
n_frames = len(t_array)
t_tracker = ValueTracker(0)

def update_bob(mob):
    i = int(t_tracker.get_value())
    i = min(i, n_frames - 1)
    x = states[i, 0]
    theta = states[i, 2]
    mob.move_to(axes.coords_to_point(x + L*np.sin(theta), -L*np.cos(theta)))

bob = Dot(color=ORANGE, radius=0.15)
bob.add_updater(update_bob)
self.add(bob)
self.play(t_tracker.animate.set_value(n_frames - 1),
          run_time=n_frames / 60, rate_func=linear)
```

---

## 7. Colours

Manim ships with named colour constants — all uppercase:

```python
RED, ORANGE, YELLOW, GREEN, TEAL, BLUE, PURPLE,
WHITE, BLACK, GREY, DARK_GREY, LIGHT_GREY
```

Hex strings work too:

```python
Dot(color="#5DCAA5")     # the project mint
```

For our cart-pole presentations, define a palette at the top of each scene matching the pygame window:

```python
CART_COL  = "#5DCAA5"
POLE_COL  = "#AFA9EC"
BOB_COL   = "#F0997B"
PHASE_COL = "#534AB7"
```

---

## 8. Camera

The default camera renders the entire scene. You can change its background, move it, or zoom.

```python
self.camera.background_color = "#0F0F0F"   # near-black, matches pygame
self.play(self.camera.animate.move_to(2 * RIGHT))   # pan right
self.play(self.camera.animate.scale(0.5))           # zoom in
```

For pendulum animations a dark background `"#0F0F0F"` keeps the colours popping.

---

## 9. The key workflow — "compute in Python, animate in Manim"

Manim is bad at physics. Python is bad at smooth video. So you split the job:

1. **Simulate** in a NumPy / SciPy script. Save `t`, `states` to a `.npz` file.
2. **Animate** in a Manim scene that loads that `.npz` and uses `plot_line_graph` + `UpdateFromFunc`.

Skeleton scene:

```python
from manim import *
import numpy as np

CART_COL = "#5DCAA5"
POLE_COL = "#AFA9EC"
BOB_COL  = "#F0997B"
L = 0.8

class CartPole(Scene):
    def construct(self):
        # ── 1. load pre-computed simulation ──
        data   = np.load("../../Day_1/pendulum_data.npz")
        t      = data["t"]
        states = data["states"]              # shape (N, 4) — x, x_dot, theta, theta_dot
        n      = len(t)

        # ── 2. background ──
        self.camera.background_color = "#0F0F0F"

        # ── 3. axes for the physical scene (x in metres, y in metres) ──
        axes = Axes(
            x_range=[-2, 2, 1], y_range=[-1.2, 0.3, 0.5],
            x_length=8, y_length=4,
            axis_config={"color": GREY, "include_tip": False},
        )
        self.add(axes)

        # ── 4. dynamic Mobjects ──
        track = Line(axes.coords_to_point(-2, 0),
                     axes.coords_to_point( 2, 0), color=GREY)
        cart  = Rectangle(width=0.6, height=0.3, color=CART_COL, fill_opacity=1)
        pole  = Line(ORIGIN, UP, color=POLE_COL, stroke_width=6)
        bob   = Dot(color=BOB_COL, radius=0.12)
        self.add(track, cart, pole, bob)

        # ── 5. driver ──
        idx = ValueTracker(0)

        def update_all(_):
            i = min(int(idx.get_value()), n - 1)
            x, _, th, _ = states[i]
            hinge = axes.coords_to_point(x, 0)
            tip   = axes.coords_to_point(x + L*np.sin(th), -L*np.cos(th))
            cart.move_to(hinge)
            pole.put_start_and_end_on(hinge, tip)
            bob.move_to(tip)

        # one dummy mobject hosts the updater so it fires every frame
        host = Mobject()
        host.add_updater(update_all)
        self.add(host)

        # ── 6. play ──
        self.play(idx.animate.set_value(n - 1),
                  run_time=t[-1], rate_func=linear)
```

Render with:

```bash
manim -pql cart_pole.py CartPole
```

The four `examples/` files in this folder build up to this pattern step by step:

| File | Demonstrates |
|------|--------------|
| `01_basic_scene.py`            | minimal scene — text, dot, axes, sine curve |
| `02_axes_and_plots.py`         | `plot_line_graph` from a NumPy array |
| `03_trajectory_animation.py`   | side-by-side physical + phase portrait, hard-coded trajectory |
| `04_pendulum_representation.py`| polished cart-pole template — start your real scene from here |

---

## Quick reference

| Call | Purpose |
|------|---------|
| `class MyScene(Scene): def construct(self):` | Define a scene. |
| `self.add(mob)`                              | Instantly add a mobject. |
| `self.play(animation, run_time=…, rate_func=…)` | Run an animation. |
| `self.wait(seconds)`                         | Hold the current frame. |
| `Dot(point, color, radius)`                  | Filled circle. |
| `Line(start, end, color, stroke_width)`      | Straight line. |
| `Rectangle(width, height, color, fill_opacity=1)` | Filled rectangle. |
| `Circle(radius, color)`                      | Circle. |
| `Arrow(start, end, color, buff)`             | Vector with arrowhead. |
| `Text(string, font_size, color)`             | Plain text. |
| `MathTex(r"\latex")`                         | LaTeX-rendered math. |
| `VGroup(*mobs)`                              | Group multiple mobjects. |
| `Axes(x_range, y_range, x_length, y_length)` | 2-D coordinate frame. |
| `axes.plot(fn, color)`                       | Plot a Python function. |
| `axes.plot_line_graph(x_values, y_values, line_color)` | Plot pre-computed arrays. |
| `axes.coords_to_point(x, y)`                 | Data-space → screen-space. |
| `axes.get_graph_label(graph, label)`         | Text label on a graph. |
| `Create(mob)`, `FadeIn(mob)`, `FadeOut(mob)` | Standard animations. |
| `MoveAlongPath(mob, path)`                   | Slide along a path. |
| `UpdateFromFunc(mob, fn)`                    | Mutate per frame. |
| `ValueTracker(v)`                            | Animatable scalar. |
| `mob.add_updater(fn)`                        | Re-run `fn(mob)` every frame. |
| `mob.animate.method(...)`                    | Auto-animated method call. |
| `self.camera.background_color = "#…"`        | Set background. |

**Run command:**  `manim -pql file.py SceneName`  (preview, low quality)
