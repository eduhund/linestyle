import math
import svgwrite

from linestyle.strokes import StrokeStyle
from linestyle.plot import (
    PlotBox,
    draw_axes,
    sample_func,
    sample_parametric,
    draw_curve,
    project_point_to_axes,
)

W = 900
H = 900

# Square plotting area with margin
M = 120

# Asymmetric data ranges (to avoid center symmetry)
BOX = PlotBox(
    x0=M, y0=M, w=W - 2 * M, h=H - 2 * M,
    xmin=-1.2, xmax=4.8,
    ymin=-2.6, ymax=6.4,
)

axis_style = StrokeStyle(width=2.2, amp=0.25, waves=1.0, taper=0.0)
data_style = StrokeStyle(width=2.2, amp=0.55, waves=0.75, taper=0.10)
proj_style = StrokeStyle(width=2.0, amp=0.35, waves=0.65, taper=0.10)


def save_svg(name: str, draw_fn):
    path = f"out/{name}.svg"
    dwg = svgwrite.Drawing(path, size=(W, H))
    draw_fn(dwg)
    dwg.save()
    print("Wrote", path)


def parabola():
    def draw(dwg):
        draw_axes(dwg, BOX, axis_style, seed=1, ticks=6, arrows=True)

        # shifted parabola (asymmetric in this window)
        pts = sample_func(BOX, lambda x: 0.35 * (x - 1.6) * (x - 1.6) - 1.3, n=110)
        draw_curve(dwg, pts, data_style, seed=100, n_per_seg=12)

        # projection of a chosen point
        x0 = 3.2
        y0 = 0.35 * (x0 - 1.6) * (x0 - 1.6) - 1.3
        project_point_to_axes(dwg, BOX, x0, y0, proj_style, seed=900)

    return draw


def two_lines():
    def draw(dwg):
        draw_axes(dwg, BOX, axis_style, seed=2, ticks=6, arrows=True)

        # line 1: skewed sinusoid + slope + offset
        pts1 = sample_func(
            BOX,
            lambda x: 1.5 * math.sin(0.9 * x + 0.4) + 0.3 * x - 0.8,
            n=120,
        )
        draw_curve(dwg, pts1, data_style, seed=200, n_per_seg=12)

        # line 2: log curve (asymmetric, different character)
        data_style_2 = StrokeStyle(width=2.2, amp=0.45, waves=0.60, taper=0.10)
        pts2 = sample_func(BOX, lambda x: 0.9 * math.log(x + 1.5) - 1.2, n=90)
        draw_curve(dwg, pts2, data_style_2, seed=260, n_per_seg=14)

        # project a point on the first curve (just for demo)
        x0 = 4.1
        y0 = 1.5 * math.sin(0.9 * x0 + 0.4) + 0.3 * x0 - 0.8
        project_point_to_axes(dwg, BOX, x0, y0, proj_style, seed=910)

    return draw


def complex_lissajous():
    def draw(dwg):
        draw_axes(dwg, BOX, axis_style, seed=3, ticks=6, arrows=True)

        def g(t):
            # shifted + slightly noisy parametric curve, not centered
            x = 1.2 + 2.6 * math.sin(2 * math.pi * (2.0 * t) + 0.3) + 0.4 * math.sin(2 * math.pi * (7.0 * t))
            y = -0.8 + 2.9 * math.sin(2 * math.pi * (3.0 * t) - 0.2)
            return x, y

        pts = sample_parametric(BOX, g, n=260)
        draw_curve(dwg, pts, data_style, seed=300, n_per_seg=10)

    return draw


def tricky_piecewise():
    def draw(dwg):
        draw_axes(dwg, BOX, axis_style, seed=4, ticks=6, arrows=True)

        # piecewise, with corners + plateau (very "explain-y")
        def f(x):
            if x < 0.3:
                return -1.8 + 0.15 * (x - 0.3)           # almost flat
            if x < 2.0:
                return -1.8 + 2.4 * (x - 0.3)            # steep rise
            if x < 3.4:
                return 2.3                                # plateau
            return 2.3 - 1.7 * (x - 3.4)                  # descent

        pts = sample_func(BOX, f, n=70)
        draw_curve(dwg, pts, data_style, seed=400, n_per_seg=18)

        # projection on a corner point (nice for explanation)
        x0 = 2.0
        y0 = f(x0)
        project_point_to_axes(dwg, BOX, x0, y0, proj_style, seed=920)

    return draw


if __name__ == "__main__":
    save_svg("01_parabola", parabola())
    save_svg("02_two_lines", two_lines())
    save_svg("03_lissajous", complex_lissajous())
    save_svg("04_piecewise", tricky_piecewise())
