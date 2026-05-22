# 02_axes_and_plots.py
# axes with labels, a plotted function, and — most importantly —
# a plot from a pre-computed NumPy array (this is the cart-pole pattern)
# render:   manim -pql 02_axes_and_plots.py AxesAndPlots

from manim import *                              # core manim
import numpy as np                               # for building the trajectory array


class AxesAndPlots(Scene):
    def construct(self):

        # ── 1. axes with axis labels ────────────────────────────
        axes = Axes(
            x_range=[0, 4, 1],                          # 0 to 4 seconds, ticks every 1
            y_range=[-1.5, 1.5, 0.5],                   # amplitude range
            x_length=10,                                # how wide on screen
            y_length=5,                                 # how tall on screen
            axis_config={"color": GREY,                 # subtle grey axes
                         "include_tip": False},         # no arrows on the axis ends
        )
        x_label = axes.get_x_axis_label("t \\,(s)")     # LaTeX label for x axis
        y_label = axes.get_y_axis_label("\\theta")      # LaTeX label for y axis
        self.add(axes, x_label, y_label)                # add instantly (no animation)

        # ── 2. plot an analytic function ────────────────────────
        analytic = axes.plot(                           # axes.plot takes a callable
            lambda x: np.sin(2 * x),                    # what to draw
            color=BLUE,                                 # colour
        )
        self.play(Create(analytic), run_time=2)         # trace it over 2 seconds
        self.wait(0.5)                                  # short pause

        # ── 3. plot a PRE-COMPUTED numpy array (the cart-pole pattern) ──
        t_arr     = np.linspace(0, 4, 200)              # 200 timepoints from 0 to 4 s
        theta_arr = np.exp(-0.4 * t_arr) * np.cos(3 * t_arr)   # decaying oscillation
        # in the real project, t_arr and theta_arr come from np.load("pendulum_data.npz")

        data_plot = axes.plot_line_graph(               # plot_line_graph takes arrays directly
            x_values=t_arr,                             # x coordinates
            y_values=theta_arr,                         # y coordinates
            line_color=ORANGE,                          # colour of the trace
            add_vertex_dots=False,                      # don't draw a dot at every point
        )
        self.play(Create(data_plot), run_time=2)        # draw the array-based curve
        self.wait(0.5)

        # ── 4. a moving dot that traces along the array ─────────
        tracker = ValueTracker(0)                       # animatable scalar — represents an index into t_arr

        moving_dot = Dot(color=YELLOW, radius=0.12)     # the marker that will move

        def update_dot(mob):                            # updater: re-runs every frame
            i = int(tracker.get_value())                # current index (truncated to int)
            i = min(i, len(t_arr) - 1)                  # don't run off the end of the array
            mob.move_to(axes.coords_to_point(           # coords_to_point: (t, theta) → screen pos
                t_arr[i], theta_arr[i]
            ))

        moving_dot.add_updater(update_dot)              # tell manim to call update_dot every frame
        self.add(moving_dot)                            # put the dot on screen

        # animate tracker from 0 to len-1; updater carries the dot along
        self.play(
            tracker.animate.set_value(len(t_arr) - 1),  # the index ramps from 0 to last
            run_time=4,                                 # 4 seconds total — matches t_arr[-1]
            rate_func=linear,                           # constant speed (no easing)
        )

        moving_dot.remove_updater(update_dot)           # detach the updater when done
        self.wait(1)                                    # hold the final frame
