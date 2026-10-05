"""House chart style: clean editorial charts in the tradition of newspaper data desks.

Every chart gets a headline that states the finding, a subtitle with the measure and units,
direct labels instead of legends, grey context behind one or two highlighted series, and a
source line. Figures are 1456 px wide, Substack's full-width image size.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"
CREDIT = ""  # e.g. "Chart: <publication name>"; printed bottom-right on every chart when set

INK = "#1A1A1A"
MUTED = "#6B6B6B"
GRID = "#E4E4E4"
CONTEXT = "#C7CBD1"
SHADE = "#F2F2EF"

RED = "#C0392B"
BLUE = "#1F5A85"
TEAL = "#21867A"
GOLD = "#D69E1E"
PURPLE = "#7B4F8E"
ORANGE = "#E0712C"
SLATE = "#5B6770"
SKY = "#4E9BD3"
PINK = "#C2507A"
OLIVE = "#8C8C2E"
GREEN = "#4C8C2B"
BROWN = "#8C6239"

COUNTRY_COLORS = {"KOR": RED, "JPN": PURPLE, "CHN": GOLD, "ITA": TEAL, "ESP": ORANGE, "DEU": SLATE, "FRA": SKY,
                  "GBR": PINK, "USA": BLUE, "BRA": OLIVE, "IND": GREEN, "NGA": BROWN, "WLD": INK}


def _first_font(candidates):
    available = {f.name for f in font_manager.fontManager.ttflist}
    return next((name for name in candidates if name in available), "DejaVu Sans")


FONT = _first_font(["Franklin Gothic Book", "Libre Franklin", "Helvetica Neue", "Helvetica", "Arial"])
FONT_BOLD = _first_font(["Franklin Gothic Demi", "Libre Franklin", "Helvetica Neue", "Helvetica", "Arial"])
BOLD = {"fontfamily": FONT_BOLD, "fontweight": "normal" if FONT_BOLD == "Franklin Gothic Demi" else "bold"}

mpl.rcParams.update({
    "font.family": FONT, "font.size": 9.5, "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "svg.fonttype": "none", "figure.dpi": 100, "savefig.dpi": 200, "lines.solid_capstyle": "round",
})

WIDTH = 7.28  # inches; 1456 px at 200 dpi
TEXT_LEFT = 0.035


def new_figure(title, subtitle, source, *, note=None, height=4.8, nrows=1, ncols=1, sharex=False, sharey=False,
               left=0.075, right=0.965, hspace=0.5, wspace=0.25, bottom_pad=0.42, top_pad=0.14, **subplot_kw):
    """A figure with headline, subtitle, source line and top rule; returns (fig, ax or axes array)."""
    fig, axes = plt.subplots(nrows, ncols, figsize=(WIDTH, height), sharex=sharex, sharey=sharey, **subplot_kw)
    inch = 1 / height
    y = 1 - 0.13 * inch
    fig.add_artist(Line2D([TEXT_LEFT, 1 - TEXT_LEFT], [y, y], transform=fig.transFigure, color=INK, lw=1.1))
    y -= 0.13 * inch
    for line in textwrap.wrap(title, 66):
        fig.text(TEXT_LEFT, y, line, fontsize=15, va="top", ha="left", color=INK, **BOLD)
        y -= 0.27 * inch
    y -= 0.07 * inch
    for line in textwrap.wrap(subtitle or "", 98):
        fig.text(TEXT_LEFT, y, line, fontsize=10.3, va="top", ha="left", color="#4D4D4D")
        y -= 0.2 * inch
    top = y - top_pad * inch
    foot = [f"Source: {source}"] + ([f"Note: {note}"] if note else [])
    lines = [line for text in foot for line in textwrap.wrap(text, 138)]
    yb = 0.1 * inch
    for line in reversed(lines):
        fig.text(TEXT_LEFT, yb, line, fontsize=7.8, va="bottom", ha="left", color=MUTED)
        yb += 0.155 * inch
    if CREDIT:
        fig.text(1 - TEXT_LEFT, 0.1 * inch, CREDIT, fontsize=7.8, va="bottom", ha="right", color=MUTED)
    fig.subplots_adjust(left=left, right=right, top=top, bottom=yb + bottom_pad * inch, hspace=hspace, wspace=wspace)
    return fig, axes


def polish(ax, grid="y", bottom=True):
    """Newspaper axes: no box, light gridlines, small ticks."""
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_visible(bottom)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(axis="y", length=0, pad=3)
    ax.tick_params(axis="x", length=3, width=0.8, color=INK, pad=3)
    if grid in ("y", "both"):
        ax.yaxis.grid(True, color=GRID, lw=0.8)
    if grid in ("x", "both"):
        ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def panel_title(ax, text, color=INK, size=10):
    ax.text(0, 1.03, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=size, color=color, **BOLD)


def label_ends(ax, items, x, *, gap=None, fontsize=9, dx=0):
    """Direct labels at the right end of lines, nudged apart so they don't overlap.

    items: dicts with y, text, color and optional bold. x is in data coordinates.
    """
    if not items:
        return
    lo, hi = ax.get_ylim()
    gap = gap if gap is not None else (hi - lo) * 0.048
    items = sorted(items, key=lambda d: d["y"])
    ys = [d["y"] for d in items]
    for _ in range(500):
        moved = False
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < gap - 1e-9:
                mid = (ys[i] + ys[i - 1]) / 2
                ys[i - 1], ys[i] = mid - gap / 2, mid + gap / 2
                moved = True
        if not moved:
            break
    for d, y in zip(items, ys):
        style = BOLD if d.get("bold") else {}
        ax.text(x + dx if dx else x, y, d["text"], color=d.get("color", INK), fontsize=fontsize, va="center",
                ha="left", clip_on=False, **style)


def shade_projection(ax, start, end=None, label="UN projection", y=None, fontsize=8.5):
    end = end if end is not None else ax.get_xlim()[1]
    ax.axvspan(start, end, color=SHADE, lw=0, zorder=0)
    lo, hi = ax.get_ylim()
    ax.text(start + (end - start) * 0.03, y if y is not None else hi - (hi - lo) * 0.03, label, fontsize=fontsize,
            color=MUTED, va="top", ha="left", style="italic")


def note(ax, text, xy, xytext, *, ha="left", va="center", color=MUTED, arrow=True, fontsize=8.8, bold=False):
    """A small annotation, optionally with a thin leader line."""
    style = BOLD if bold else {}
    props = dict(arrowstyle="-", color=color, lw=0.7, shrinkA=0, shrinkB=2) if arrow else None
    ax.annotate(text, xy=xy, xytext=xytext, textcoords="data", ha=ha, va=va, fontsize=fontsize, color=color,
                arrowprops=props, **style)


PLATE = {"boxstyle": "square,pad=0.15", "facecolor": "white", "edgecolor": "none"}  # white backing for labels on lines


def save(fig, name):
    """Write figures/<name>.png (1456 px wide) and .svg; close the figure unless shown inline."""
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=200)
    fig.savefig(FIGURES / f"{name}.svg")
    if "inline" not in mpl.get_backend():
        plt.close(fig)
    return FIGURES / f"{name}.png"
