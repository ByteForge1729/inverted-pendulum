# 03_trajectory_animation.py
# the cart-pole presentation template:
# left panel = physical animation, right panel = phase portrait,
# both driven from the same pre-computed trajectory array
# render:   manim -pql 03_trajectory_animation.py TrajectoryAnimation

from manim import *                              # core manim
import numpy as np                               # for the hard-coded trajectory


# project palette — keep close to the pygame window
BG_COL    = "#0F0F0F"                            # dark background
POLE_COL  = "#AFA9EC"                            # lilac rod
BOB_COL   = "#F0997B"                            # peach bob
TRACE_COL = "#534AB7"                            # phase-portrait trail
DOT_COL   = "#5DCAA5"                            # mint dot on phase plot

L = 1.0                                          # rod length used in this demo


class TrajectoryAnimation(Scene):
    def construct(self):

        # ── 1. build a fake simple-pendulum trajectory (no file dependency) ──
        N         = 200                                          # frame count
        t_arr     = np.linspace(0, 4, N)                         # 4 seconds at 50 fps-ish
        theta_arr = 0.6 * np.exp(-0.25 * t_arr) * np.cos(2.0 * t_arr)   # decaying swing
        # finite-difference the angle to get angular velocity (radians / s)
        thetad_arr = np.gradient(theta_arr, t_arr)               # same length as theta_arr

        # ── 2. background ────────────────────────────────────────
        self.camera.background_color = BG_COL                    # set the global background

        # ── 3. layout: left half = physical, right half = phase ──
        phys_axes = Axes(
            x_range=[-1.5, 1.5, 0.5],                            # x in metres
            y_range=[-1.3, 0.3, 0.5],                            # y in metres
            x_length=5.5,                                        # screen size
            y_length=4.5,
            axis_config={"color": DARK_GREY, "include_tip": False},
        ).to_edge(LEFT, buff=0.6)                                # park on the left
        phys_label = Text("physical", font_size=20, color=GREY)\
            .next_to(phys_axes, UP)                              # title above the panel

        phase_axes = Axes(
            x_range=[-1.0, 1.0, 0.5],                            # theta (rad)
            y_range=[-2.0, 2.0, 1.0],                            # theta_dot (rad/s)
            x_length=5.5,
            y_length=4.5,
            axis_config={"color": DARK_GREY, "include_tip": False},
        ).to_edge(RIGHT, buff=0.6)                               # park on the right
        phase_label = Text("phase portrait", font_size=20, color=GREY)\
            .next_to(phase_axes, UP)                             # title above
        phase_x_lab = MathTex("\\theta", font_size=24)\
            .next_to(phase_axes.x_axis, DOWN, buff=0.1)          # x-axis name
        phase_y_lab = MathTex("\\dot{\\theta}", font_size=24)\
            .next_to(phase_axes.y_axis, LEFT, buff=0.1)          # y-axis name

        self.add(phys_axes, phys_label,                          # add the static frame
                 phase_axes, phase_label, phase_x_lab, phase_y_lab)

        # ── 4. dynamic objects on the LEFT panel ─────────────────
        hinge_pt = phys_axes.coords_to_point(0, 0)               # the pivot point in screen coords
        rod = Line(hinge_pt, hinge_pt + DOWN, color=POLE_COL, stroke_width=6)  # placeholder line
        bob = Dot(color=BOB_COL, radius=0.15).move_to(hinge_pt + DOWN)         # placeholder bob
        self.add(rod, bob)                                       # put them on screen

        # ── 5. dynamic objects on the RIGHT panel ────────────────
        phase_dot = Dot(color=DOT_COL, radius=0.10)\
            .move_to(phase_axes.coords_to_point(theta_arr[0], thetad_arr[0]))   # start position
        # the phase trail is built up over time; precompute the full poly-line and reveal gradually:
        phase_trail = phase_axes.plot_line_graph(
            x_values=theta_arr, y_values=thetad_arr,             # entire trajectory
            line_color=TRACE_COL,
            add_vertex_dots=False,
            stroke_width=2,
        )
        self.add(phase_trail, phase_dot)                         # trail under the dot

        # ── 6. driver: one ValueTracker advances the frame index ──
        idx = ValueTracker(0)                                    # animatable scalar = frame index

        def update_rod(mob):                                     # left-panel rod updater
            i = min(int(idx.get_value()), N - 1)                 # bounds-safe
            th = theta_arr[i]                                    # current angle
            tip = phys_axes.coords_to_point(                     # tip position in screen coords
                L * np.sin(th), -L * np.cos(th)                  # x = L sin th, y = -L cos th
            )
            mob.put_start_and_end_on(hinge_pt, tip)              # redraw the rod from hinge to tip

        def update_bob(mob):                                     # left-panel bob updater
            i = min(int(idx.get_value()), N - 1)
            th = theta_arr[i]
            mob.move_to(phys_axes.coords_to_point(
                L * np.sin(th), -L * np.cos(th)
            ))

        def update_phase_dot(mob):                               # right-panel phase dot updater
            i = min(int(idx.get_value()), N - 1)
            mob.move_to(phase_axes.coords_to_point(
                theta_arr[i], thetad_arr[i]                      # (theta, theta_dot)
            ))

        rod.add_updater(update_rod)                              # attach all three updaters
        bob.add_updater(update_bob)
        phase_dot.add_updater(update_phase_dot)

        # ── 7. play it ───────────────────────────────────────────
        self.play(
            idx.animate.set_value(N - 1),                        # ramp the index from 0 to last
            run_time=t_arr[-1],                                  # match real time (4 s)
            rate_func=linear,                                    # no easing — uniform playback
        )

        # ── 8. cleanup ───────────────────────────────────────────
        rod.remove_updater(update_rod)                           # detach updaters when done
        bob.remove_updater(update_bob)
        phase_dot.remove_updater(update_phase_dot)
        self.wait(1)                                             # hold the final frame
