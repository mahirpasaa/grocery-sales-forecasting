"""Shared matplotlib styling so every figure in the repo looks like one system."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"     # primary series / sequential hue
ORANGE = "#eb6834"   # second series / highlight
MUTED = "#b9b8b2"    # de-emphasised marks
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

FIG_DIR = Path(__file__).resolve().parents[1] / "figures"


def apply() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "text.color": TEXT,
        "axes.labelcolor": TEXT_2,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 24,
        "axes.edgecolor": GRID,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": TEXT_2,
        "ytick.color": TEXT_2,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "axes.prop_cycle": mpl.cycler(color=[BLUE, ORANGE, "#1baf7a", "#eda100"]),
    })


def subtitle(ax, text: str) -> None:
    """Grey one-line subtitle under the title, stating the takeaway."""
    ax.text(0, 1.02, text, transform=ax.transAxes, color=TEXT_2, fontsize=9.5, va="bottom")


def save(fig, name: str) -> Path:
    FIG_DIR.mkdir(exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    return path
