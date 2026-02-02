from __future__ import annotations

import svgwrite

from .strokes import (
    StrokeStyle,
    stroke_line,
    stroke_polyline,
    arrow_head_open,
    ticks_on_axis,
)


def demo_axes_svg(path: str, W: int = 960, H: int = 540, seed: int = 1) -> None:
    dwg = svgwrite.Drawing(path, size=(W, H))

    # Styles: axes are calmer than data (very important in your samples)
    axis_style = StrokeStyle(width=2.2, amp=0.25, waves=1.0, taper=0.0)
    data_style = StrokeStyle(width=2.2, amp=0.55, waves=0.75, taper=0.10)

    origin = (130, 420)
    x_end = (880, 420)
    y_end = (130, 90)

    # axes
    stroke_line(dwg, origin, x_end, axis_style, seed=seed + 10, n=90)
    stroke_line(dwg, origin, y_end, axis_style, seed=seed + 20, n=90)

    # arrowheads (open/simple)
    arrow_head_open(dwg, x_end, (1, 0), axis_style, seed=seed + 30, size=14)
    arrow_head_open(dwg, y_end, (0, -1), axis_style, seed=seed + 40, size=14)

    # ticks on X (example)
    ticks_on_axis(
        dwg,
        origin,
        x_end,
        tick_positions_t=[0.15, 0.30, 0.45, 0.60, 0.75, 0.90],
        tick_len=20,
        style=axis_style,
        seed=seed + 50,
    )

    # sample polyline data (sharp corners preserved)
    pts = [
        (130, 340),
        (240, 300),
        (330, 315),
        (430, 260),
        (540, 285),
        (640, 210),
        (760, 240),
        (880, 160),
    ]
    stroke_polyline(dwg, pts, style=data_style, seed=seed + 100, n_per_seg=34)

    dwg.save()
