"""Nature-style figure defaults shared by all result figures.

Widths follow the journal's column sizes (single 89 mm, double 183 mm). Text is sans-serif at
5 to 7 pt, panel letters are bold lowercase at 8 pt, lines are 0.5 to 1 pt, there are no titles
inside panels (the caption carries the explanation), images carry scale bars, and every figure is
saved as vector PDF and 450 dpi PNG.
Colours: two validated categorical slots (dataviz reference palette, CVD-checked), grey-scale for
intensity and amplitude, and a blue-red diverging map with a neutral grey midpoint for signed phase.
"""

from __future__ import annotations

MM = 1 / 25.4
SINGLE = 89 * MM
DOUBLE = 183 * MM

INK, INK2, GRID = "#000000", "#4d4d4d", "#d9d9d9"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"  # categorical slots 1-3 (validated)
ACCENT = "#e34948"
DIVERGING = ["#104281", "#256abf", "#6da7ec", "#cde2fb", "#f0efec", "#f6c9c4", "#ec8c87", "#e34948", "#a32a2a"]


def apply():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7, "xtick.labelsize": 6,
        "ytick.labelsize": 6, "legend.fontsize": 6, "legend.frameon": False,
        "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.direction": "out", "ytick.direction": "out",
        "lines.linewidth": 1.0, "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 450,
        "image.interpolation": "antialiased",
    })
    return plt


def phase_cmap():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("phase_div", DIVERGING)


def panel_label(ax, letter, x=-0.02, y=1.02):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom", ha="right")


def scale_bar(ax, length, label, x0_frac=0.03, y_frac=0.12, color="white", lw=1.5):
    """Horizontal scale bar in data units along x, drawn inside the axes."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    xs = x0 + x0_frac * (x1 - x0)
    ys = y0 + y_frac * (y1 - y0)
    ax.plot([xs, xs + length], [ys, ys], color=color, lw=lw, solid_capstyle="butt")
    ax.text(xs + length / 2, ys + 0.06 * (y1 - y0), label, color=color, ha="center", va="bottom", fontsize=6)


def save(fig, path_stem):
    fig.savefig(f"{path_stem}.pdf")
    fig.savefig(f"{path_stem}.png", dpi=450)
