# 04_pendulum_representation.py
# polished cart-pole template — cart, pole, bob, live telemetry
# this is the starting point for the actual presentation animation
# render:   manim -pql 04_pendulum_representation.py PendulumRepresentation

from manim import *                              # core manim
import numpy as np                               # for the hard-coded trajectory


# ── project palette (matches pygame window) ────────────────────
BG_COL    = "#0F0F0F"                            # background
TRACK_COL = "#3C3C3C"                            # the cart rail
CART_COL  = "#5DCAA5"                            # mint cart
POLE_COL  = "#AFA9EC"                            # lilac pole
BOB_COL   = "#F0997B"                            # peach bob
TEXT_COL  = "#C8C8C8"                            # off-white telemetry

# ── pendulum geometry ──────────────────────────────────────────
L = 0.8                                          # pole length (matches Day_1/cart_pole_dynamics.py)


class PendulumRepresentation(Scene):
    def construct(self):

        # ── 1. background ─────────────────────────────────────────
        self.camera.background_color = BG_COL                    # dark scene background

        # ── 2. hard-coded passive cart-pole trajectory ────────────
        # in the real project this comes from np.load("pendulum_data.npz")
        N        = 240                                           # number of frames
        t_arr    = np.linspace(0, 6, N)                          # 6 second clip
        x_arr    = 0.4 * np.sin(0.8 * t_arr)                     # cart drifts in a slow sine
        theta_arr = 0.4 * np.exp(-0.15 * t_arr) * np.cos(2.5 * t_arr)   # pole swings, decaying

        # ── 3. coordinate frame for the physical scene ────────────
        axes = Axes(
            x_range=[-1.5, 1.5, 0.5],                            # x in metres
            y_range=[-1.2, 0.6, 0.5],                            # y in metres
            x_length=10,                                         # screen width
            y_length=5,                                          # screen height
            axis_config={"color": BG_COL, "stroke_opacity": 0},  # invisible — we just need the transform
        )
        # we keep axes only as a coordinate transform; we don't render it.

        # ── 4. the static track (a horizontal line at y = 0) ───────
        track_left  = axes.coords_to_point(-1.4, 0)              # left end of the rail in screen coords
        track_right = axes.coords_to_point( 1.4, 0)              # right end
        track       = Line(track_left, track_right,              # the rail itself
                           color=TRACK_COL, stroke_width=4)
        self.add(track)

        # ── 5. the cart, pole and bob (placeholder positions) ──────
        # the cart is drawn as a rectangle centred on the hinge
        cart = Rectangle(width=0.7, height=0.35,                 # ~0.35 m tall, 0.7 m wide on screen
                         color=CART_COL, fill_opacity=1,
                         stroke_width=0)\
            .move_to(axes.coords_to_point(0, 0))                 # starts at cart position 0

        # the pole — a thick line from hinge up/down to the bob
        pole = Line(axes.coords_to_point(0, 0),                  # hinge
                    axes.coords_to_point(0, L),                  # bob position (theta=0)
                    color=POLE_COL, stroke_width=8)

        # the bob — a dot at the tip of the pole
        bob = Dot(point=axes.coords_to_point(0, L),
                  color=BOB_COL, radius=0.14)

        self.add(cart, pole, bob)                                # add all three

        # ── 6. title and live angle readout ───────────────────────
        title = Text("cart-pole — passive simulation",
                     font_size=28, color=TEXT_COL)\
            .to_edge(UP, buff=0.4)                               # top of the frame
        self.add(title)

        # the angle readout uses a Variable that updates each frame
        angle_label = Text("theta = 0.0 deg",                    # placeholder text
                           font_size=22, color=TEXT_COL,
                           font="monospace")\
            .to_corner(UL, buff=0.5)                             # top-left corner
        self.add(angle_label)

        time_label = Text("t = 0.00 s",
                          font_size=22, color=TEXT_COL,
                          font="monospace")\
            .next_to(angle_label, DOWN, aligned_edge=LEFT, buff=0.15)
        self.add(time_label)

        # ── 7. the driver — one ValueTracker for the frame index ──
        idx = ValueTracker(0)                                    # ramps 0 → N-1 over the play time

        def hinge_screen(i):                                     # helper: hinge position for frame i
            return axes.coords_to_point(x_arr[i], 0)

        def tip_screen(i):                                       # helper: bob position for frame i
            xi  = x_arr[i]
            thi = theta_arr[i]
            return axes.coords_to_point(xi + L * np.sin(thi),    # cart_x + L*sin(theta)
                                        -L * np.cos(thi))        # -L*cos(theta) — bob hangs below

        def update_cart(mob):                                    # cart updater
            i = min(int(idx.get_value()), N - 1)
            mob.move_to(hinge_screen(i))                         # cart centres on hinge

        def update_pole(mob):                                    # pole updater — full redraw of endpoints
            i = min(int(idx.get_value()), N - 1)
            mob.put_start_and_end_on(hinge_screen(i), tip_screen(i))

        def update_bob(mob):                                     # bob updater — sits at the tip
            i = min(int(idx.get_value()), N - 1)
            mob.move_to(tip_screen(i))

        def update_angle_text(mob):                              # live angle readout
            i = min(int(idx.get_value()), N - 1)
            deg = np.degrees(theta_arr[i])                       # rad → deg for the human
            new_text = Text(f"theta = {deg:+6.1f} deg",          # rebuild the text mobject
                            font_size=22, color=TEXT_COL,
                            font="monospace")
            new_text.move_to(mob)                                # keep same position
            mob.become(new_text)                                 # in-place swap

        def update_time_text(mob):                               # live time readout
            i = min(int(idx.get_value()), N - 1)
            new_text = Text(f"t     = {t_arr[i]:5.2f} s",
                            font_size=22, color=TEXT_COL,
                            font="monospace")
            new_text.move_to(mob)
            mob.become(new_text)

        # attach all updaters at once
        cart.add_updater(update_cart)
        pole.add_updater(update_pole)
        bob.add_updater(update_bob)
        angle_label.add_updater(update_angle_text)
        time_label.add_updater(update_time_text)

        # ── 8. play it — index ramps from 0 to N-1 over t_arr[-1] seconds ──
        self.play(
            idx.animate.set_value(N - 1),
            run_time=t_arr[-1],                                  # real-time playback
            rate_func=linear,                                    # uniform speed
        )

        # ── 9. cleanup ─────────────────────────────────────────────
        cart.remove_updater(update_cart)
        pole.remove_updater(update_pole)
        bob.remove_updater(update_bob)
        angle_label.remove_updater(update_angle_text)
        time_label.remove_updater(update_time_text)
        self.wait(1)                                             # hold the final frame
