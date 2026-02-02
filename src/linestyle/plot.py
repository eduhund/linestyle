from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple
import math

import svgwrite

from .strokes import StrokeStyle, stroke_polyline, stroke_line, stroke_line_dashed, arrow_head_gesture, ticks_on_axis

Point = Tuple[float, float]


@dataclass(frozen=True)
class PlotBox:
    """
    Data coords (x,y) -> SVG coords inside a square (or any) box.
    """
    x0: float
    y0: float
    w: float
    h: float
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def xy(self, x: float, y: float) -> Point:
        # map x in [xmin,xmax] to [x0, x0+w]
        u = (x - self.xmin) / (self.xmax - self.xmin)
        v = (y - self.ymin) / (self.ymax - self.ymin)
        sx = self.x0 + u * self.w
        # SVG y grows downward, so invert
        sy = self.y0 + (1.0 - v) * self.h
        return (sx, sy)

def project_point_to_axes(
    dwg: svgwrite.Drawing,
    box: PlotBox,
    x: float,
    y: float,
    dashed_style: StrokeStyle,
    seed: int,
) -> None:
    """
    Draw dashed projections from point (x,y) to bottom X-axis and left Y-axis.
    Axes are assumed to be on borders: y=ymin and x=xmin.
    """
    p = box.xy(x, y)
    px = box.xy(x, box.ymin)      # down to X-axis (bottom)
    py = box.xy(box.xmin, y)      # left to Y-axis

    stroke_line_dashed(dwg, p, px, dashed_style, seed=seed + 1, n=50, dash_base=9, gap_base=11)
    stroke_line_dashed(dwg, p, py, dashed_style, seed=seed + 2, n=50, dash_base=9, gap_base=11)

    # Optional tiny tick/cross at the point (liner-only, subtle)
    r = 5.0
    stroke_line(dwg, (p[0]-r, p[1]), (p[0]+r, p[1]), dashed_style, seed=seed + 3, n=16)
    stroke_line(dwg, (p[0], p[1]-r), (p[0], p[1]+r), dashed_style, seed=seed + 4, n=16)


def sample_func(
    box: PlotBox,
    f: Callable[[float], float],
    n: int = 70,
) -> List[Point]:
    pts: List[Point] = []
    for i in range(n):
        t = i / (n - 1)
        x = box.xmin + (box.xmax - box.xmin) * t
        y = f(x)
        pts.append(box.xy(x, y))
    return pts


def sample_parametric(
    box: PlotBox,
    g: Callable[[float], Tuple[float, float]],
    n: int = 200,
) -> List[Point]:
    pts: List[Point] = []
    for i in range(n):
        t = i / (n - 1)
        x, y = g(t)
        pts.append(box.xy(x, y))
    return pts


def draw_axes(
    dwg: svgwrite.Drawing,
    box: PlotBox,
    axis_style: StrokeStyle,
    seed: int,
    ticks: int = 6,
    arrows: bool = True,
) -> None:
    # Axes on the borders: X at bottom, Y at left
    x_axis_y = box.ymin
    y_axis_x = box.xmin

    origin = box.xy(y_axis_x, x_axis_y)
    x_end  = box.xy(box.xmax, x_axis_y)
    y_end  = box.xy(y_axis_x, box.ymax)

    stroke_line(dwg, origin, x_end, axis_style, seed=seed + 1, n=90)
    stroke_line(dwg, origin, y_end, axis_style, seed=seed + 2, n=90)

    if arrows:
        arrow_head_gesture(dwg, x_end, (1, 0), axis_style, seed=seed + 3, size=14)
        arrow_head_gesture(dwg, y_end, (0, -1), axis_style, seed=seed + 4, size=14)

    if ticks > 0:
        ts = [i / ticks for i in range(1, ticks)]
        ticks_on_axis(dwg, origin, x_end, ts, tick_len=20, style=axis_style, seed=seed + 10)
        ticks_on_axis(dwg, origin, y_end, ts, tick_len=20, style=axis_style, seed=seed + 20)

def draw_curve(
    dwg: svgwrite.Drawing,
    pts: List[Point],
    style: StrokeStyle,
    seed: int,
    n_per_seg: int = 18,
) -> None:
    # Many points -> many short segments. Keep corners “honest”.
    stroke_polyline(dwg, pts, style=style, seed=seed, n_per_seg=n_per_seg)
