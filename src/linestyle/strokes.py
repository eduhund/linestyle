from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple, Optional

import numpy as np
import svgwrite

Point = Tuple[float, float]


@dataclass(frozen=True)
class StrokeStyle:
    """
    Liner style (first pass).
    The key idea: low-frequency drift (gesture), not jitter.
    """
    width: float = 2.2
    amp: float = 0.8           # max normal offset in px
    waves: float = 1.2         # how many slow waves along stroke
    taper: float = 0.08        # 0..0.2: reduce deviation near ends
    color: str = "#111"
    linecap: str = "round"
    linejoin: str = "round"


def _unit(vx: float, vy: float) -> Tuple[float, float]:
    n = math.hypot(vx, vy)
    if n == 0:
        return 0.0, 0.0
    return vx / n, vy / n


def _normal(p0: Point, p1: Point) -> Tuple[float, float]:
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    ux, uy = _unit(dx, dy)
    # rotate +90deg
    return -uy, ux


def _taper_k(t: float, taper: float) -> float:
    if taper <= 0:
        return 1.0
    edge = min(t, 1.0 - t)  # 0 at ends, 0.5 at center
    # linear ramp to 1.0
    return min(1.0, edge / taper)


def _smooth_offset(t: float, rng: np.random.Generator, waves: float) -> float:
    """
    Low-frequency correlated offset (gesture drift), tuned to be less 'wavy'.
    - main sine: 1 slow wave
    - very small second harmonic (kept tiny to avoid visible oscillation)
    """
    phase = rng.uniform(0.0, 2.0 * math.pi)
    # smaller 2nd harmonic than before
    a2 = rng.uniform(-0.10, 0.10)
    return (
        math.sin(2.0 * math.pi * waves * t + phase)
        + a2 * math.sin(2.0 * math.pi * (2.0 * waves) * t + 0.7 * phase)
    )

def stroke_line(
    dwg: svgwrite.Drawing,
    p0: Point,
    p1: Point,
    style: StrokeStyle,
    seed: int,
    n: int = 70,
) -> svgwrite.path.Path:
    """
    Draw a 'liner' line from p0 to p1 as a polyline path with low-frequency drift.
    """
    rng = np.random.default_rng(seed)
    nx, ny = _normal(p0, p1)

    pts: List[Point] = []
    for i in range(n):
        t = i / (n - 1)
        bx = p0[0] + (p1[0] - p0[0]) * t
        by = p0[1] + (p1[1] - p0[1]) * t

        k = _taper_k(t, style.taper)
        off = style.amp * k * _smooth_offset(t, rng, style.waves)

        x = bx + nx * off
        y = by + ny * off
        pts.append((x, y))

    path = dwg.path(
        fill="none",
        stroke=style.color,
        stroke_width=style.width,
        stroke_linecap=style.linecap,
        stroke_linejoin=style.linejoin,
    )

    path.push(f"M {pts[0][0]:.2f},{pts[0][1]:.2f}")
    for (x, y) in pts[1:]:
        path.push(f"L {x:.2f},{y:.2f}")

    dwg.add(path)
    return path

def stroke_line_dashed(
    dwg: svgwrite.Drawing,
    p0: Point,
    p1: Point,
    style: StrokeStyle,
    seed: int,
    n: int = 70,
    dash_base: float = 10.0,
    gap_base: float = 12.0,
) -> svgwrite.path.Path:
    """
    Same as stroke_line, but dashed. Dash pattern is slightly varied per call
    (still deterministic via seed) to keep it from looking CAD-perfect.
    """
    rng = np.random.default_rng(seed)

    # tiny variation per line, but not jittery
    dash = dash_base * float(rng.uniform(0.85, 1.15))
    gap  = gap_base  * float(rng.uniform(0.85, 1.20))
    dasharray = f"{dash:.1f} {gap:.1f}"

    nx, ny = _normal(p0, p1)
    pts: List[Point] = []
    for i in range(n):
        t = i / (n - 1)
        bx = p0[0] + (p1[0] - p0[0]) * t
        by = p0[1] + (p1[1] - p0[1]) * t

        k = _taper_k(t, style.taper)
        off = style.amp * k * _smooth_offset(t, rng, style.waves)

        pts.append((bx + nx * off, by + ny * off))

    path = dwg.path(
        fill="none",
        stroke=style.color,
        stroke_width=style.width,
        stroke_linecap=style.linecap,
        stroke_linejoin=style.linejoin,
        stroke_dasharray=dasharray,
    )

    path.push(f"M {pts[0][0]:.2f},{pts[0][1]:.2f}")
    for (x, y) in pts[1:]:
        path.push(f"L {x:.2f},{y:.2f}")

    # small random dash offset so different projection lines don't “phase lock”
    path.update({"stroke-dashoffset": f"{rng.uniform(0, dash + gap):.1f}"})

    dwg.add(path)
    return path


def stroke_polyline(
    dwg: svgwrite.Drawing,
    points: Sequence[Point],
    style: StrokeStyle,
    seed: int,
    n_per_seg: int = 30,
) -> None:
    """
    Draw a polyline (piecewise segments) preserving sharp corners.
    Important for your style: corners are intentional, not rounded.
    """
    if len(points) < 2:
        return
    for i in range(len(points) - 1):
        stroke_line(
            dwg,
            points[i],
            points[i + 1],
            style=style,
            seed=seed + i * 97,
            n=n_per_seg,
        )


def arrow_head_open(
    dwg: svgwrite.Drawing,
    tip: Point,
    direction: Point,
    style: StrokeStyle,
    seed: int,
    size: float = 14.0,
    open_angle_deg: float = 28.0,
) -> None:
    """
    Open, simple arrowhead (liner gesture), slightly asymmetric.
    """
    rng = np.random.default_rng(seed)
    dx, dy = _unit(direction[0], direction[1])

    # Left wing angle
    a1 = math.radians(open_angle_deg + rng.uniform(-4.0, 4.0))
    ca1, sa1 = math.cos(a1), math.sin(a1)
    lx = dx * ca1 - dy * sa1
    ly = dx * sa1 + dy * ca1

    # Right wing angle (different random)
    a2 = math.radians(open_angle_deg + rng.uniform(-6.0, 6.0))
    ca2, sa2 = math.cos(a2), math.sin(a2)
    rx = dx * ca2 + dy * sa2
    ry = -dx * sa2 + dy * ca2

    pL = (tip[0] - lx * size, tip[1] - ly * size)
    pR = (tip[0] - rx * size, tip[1] - ry * size)

    stroke_line(dwg, pL, tip, style, seed=seed + 101, n=18)
    stroke_line(dwg, pR, tip, style, seed=seed + 202, n=18)


def arrow_head_gesture(
    dwg: svgwrite.Drawing,
    tip: Point,
    direction: Point,
    style: StrokeStyle,
    seed: int,
    size: float = 14.0,
    open_angle_deg: float = 30.0,
) -> None:
    """
    More 'hand gesture' arrowhead:
    - stronger asymmetry
    - each wing is 2-segment stroke with a tiny kink near the tip
    """
    rng = np.random.default_rng(seed)
    dx, dy = _unit(direction[0], direction[1])

    def rot(vx, vy, ang):
        ca, sa = math.cos(ang), math.sin(ang)
        return (vx * ca - vy * sa, vx * sa + vy * ca)

    # strong asymmetry: different angles and sizes per wing
    angL = math.radians(open_angle_deg + rng.uniform(-9.0, 9.0))
    angR = math.radians(open_angle_deg + rng.uniform(-12.0, 12.0))
    sizeL = size * rng.uniform(0.85, 1.15)
    sizeR = size * rng.uniform(0.75, 1.20)

    lx, ly = rot(dx, dy, +angL)
    rx, ry = rot(dx, dy, -angR)

    # base points (start of wings)
    pL0 = (tip[0] - lx * sizeL, tip[1] - ly * sizeL)
    pR0 = (tip[0] - rx * sizeR, tip[1] - ry * sizeR)

    # add a small kink near the tip (not along the whole line)
    def kink_point(p0: Point, tip: Point, k: float) -> Point:
        vx, vy = (tip[0] - p0[0], tip[1] - p0[1])
        ux, uy = _unit(vx, vy)
        nx, ny = (-uy, ux)
        kk = rng.uniform(-k, k)
        t = rng.uniform(0.70, 0.85)
        bx = p0[0] + (tip[0] - p0[0]) * t
        by = p0[1] + (tip[1] - p0[1]) * t
        return (bx + nx * kk, by + ny * kk)

    pL1 = kink_point(pL0, tip, k=2.0)
    pR1 = kink_point(pR0, tip, k=2.5)

    # Wings: 2 segments each
    stroke_line(dwg, pL0, pL1, style, seed=seed + 111, n=14)
    stroke_line(dwg, pL1, tip, style, seed=seed + 112, n=10)

    stroke_line(dwg, pR0, pR1, style, seed=seed + 211, n=14)
    stroke_line(dwg, pR1, tip, style, seed=seed + 212, n=10)


def ticks_on_axis(
    dwg: svgwrite.Drawing,
    axis_p0: Point,
    axis_p1: Point,
    tick_positions_t: Sequence[float],
    tick_len: float,
    style: StrokeStyle,
    seed: int,
) -> None:
    """
    ticks by param t in [0..1] along axis line.
    tick direction is perpendicular to axis.
    """
    nx, ny = _normal(axis_p0, axis_p1)

    for i, t in enumerate(tick_positions_t):
        x = axis_p0[0] + (axis_p1[0] - axis_p0[0]) * t
        y = axis_p0[1] + (axis_p1[1] - axis_p0[1]) * t

        a = (x - nx * tick_len / 2.0, y - ny * tick_len / 2.0)
        b = (x + nx * tick_len / 2.0, y + ny * tick_len / 2.0)

        stroke_line(dwg, a, b, style, seed=seed + i * 31, n=12)
