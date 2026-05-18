# 01_basic_scene.py
# the smallest useful Manim scene — text + dot + axes + sine curve
# render:   manim -pql 01_basic_scene.py BasicScene

from manim import *                              # bring in Scene, Dot, Axes, animations, colour constants...
import numpy as np                               # only used for np.sin / np.pi inside the lambda


class BasicScene(Scene):                         # every scene subclasses manim.Scene
    def construct(self):                         # construct() is where you describe the animation

        # ── 1. a title that fades in ────────────────────────────
        title = Text("manim basics", font_size=48)    # create a Text mobject; default position = ORIGIN
        title.to_edge(UP)                              # shift it to the top edge of the frame
        self.play(FadeIn(title))                       # animate: opacity 0 → 1 over the default 1 s
        self.wait(0.5)                                 # hold the frame for half a second

        # ── 2. a dot that moves along a straight path ───────────
        dot = Dot(color=YELLOW, radius=0.12)           # filled yellow circle, slightly bigger than default
        dot.move_to(LEFT * 3)                          # start position: 3 units left of centre
        self.play(Create(dot))                         # animate it appearing

        target = RIGHT * 3                             # destination = 3 units right
        path   = Line(LEFT * 3, target, color=GREY)    # a Line object — also a valid "path"
        self.play(MoveAlongPath(dot, path), run_time=2)  # slide the dot along the line over 2 s
        self.play(FadeOut(dot))                        # remove it nicely

        # ── 3. an axes with a sine curve plotted ────────────────
        axes = Axes(
            x_range=[0, 2 * np.pi, np.pi / 2],         # x goes 0 to 2π, ticks every π/2
            y_range=[-1.2, 1.2, 0.5],                  # y goes -1.2 to 1.2, ticks every 0.5
            x_length=8,                                # 8 manim units wide on screen
            y_length=3,                                # 3 manim units tall on screen
            axis_config={"color": GREY,                # grey axes
                         "include_tip": False},        # no arrowheads on axis ends
        )
        axes.to_edge(DOWN)                             # park the axes near the bottom of the frame

        curve = axes.plot(                             # axes.plot takes a Python callable
            lambda x: np.sin(x),                       # the function to plot
            color=BLUE,                                # line colour
        )

        self.play(Create(axes))                        # draw the axes
        self.play(Create(curve), run_time=2)           # then trace the sine curve
        self.wait(1)                                   # hold the finished frame
