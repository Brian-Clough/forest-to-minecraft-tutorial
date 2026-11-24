"""Chunk 5: decide where the trees go and how big each one is.

Reads data/forest_aoi.tif and out/surface_y.npy (run 04_build_terrain.py first). Corrects the canopy map for cuts made after
the imagery was taken, then places one tree per jittered grid cell where the canopy is tall enough. Writes out/trees.csv
(one row per tree, no blocks yet) plus a summary and a picture in docs/. Chunk 7 turns the rows into blocks.

Usage: python scripts/05_place_trees.py [path/to/forest_aoi.tif]
"""
import sys, pathlib
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIF = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "forest_aoi.tif"
OUT, DOCS = ROOT / "out", ROOT / "docs"

BANDS = ["dem3dep1m", "dem3dep10m", "canopy_h", "loss_year", "treecover2000"]
NODATA = -9998
IMAGERY_YEAR = 2019     # the canopy map comes from imagery around 2018 to 2020; cuts after this are not in it
CELL = 6                # metres between tree sites on average; one tree per CELL x CELL square (about 280 stems per ha)
MIN_TREE_H = 3.0        # canopy below this is shrubs or seedlings, not a tree we draw
SEED = 20260101


def load_layers(path):
    with rasterio.open(path) as src:
        data = src.read().astype("float64")
    layers = {}
    for name, a in zip(BANDS, data):
        a = a.copy(); a[~np.isfinite(a) | (a <= NODATA)] = np.nan; layers[name] = a
    return layers


def correct_canopy(canopy, loss):
    """Remove trees from ground cut after the imagery date. Cuts before it are already visible in the canopy map."""
    out = np.nan_to_num(canopy, nan=0.0).copy()
    out[np.nan_to_num(loss, nan=0) > IMAGERY_YEAR] = 0.0
    return out


def place_trees(canopy, ground_y, loss, rng):
    """One candidate per CELL x CELL square, jittered; keep it where the canopy at that point is tall enough."""
    h, w = canopy.shape
    rows = np.arange(0, h - CELL + 1, CELL); cols = np.arange(0, w - CELL + 1, CELL)
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    z = rr + rng.integers(0, CELL, rr.shape)
    x = cc + rng.integers(0, CELL, cc.shape)
    height = canopy[z, x]
    keep = height >= MIN_TREE_H
    z, x, height = z[keep], x[keep], height[keep]
    height_blocks = np.round(height).astype(int)
    crown_r = np.clip(np.round(height / 9), 1, 4).astype(int)       # crown half-width: about a ninth of the height
    return dict(x=x, z=z, y=ground_y[z, x], h=height_blocks, r=crown_r, loss=np.nan_to_num(loss[z, x], nan=0).astype(int))


def tree_profile(h, r):
    """Half-width of the crown at each block above the ground: a cone from 35% of the height up to the tip."""
    base = int(round(0.35 * h)); prof = {}
    for k in range(base, h + 1):
        prof[k] = r * (h - k) / max(h - base, 1)
    return prof


def block_count(trees):
    n = 0
    for h, r in zip(trees["h"], trees["r"]):
        n += h                                               # trunk
        for k, half in tree_profile(h, r).items():
            n += int(round(np.pi * round(half) ** 2 + 0.01)) if round(half) > 0 else 0
    return n


def main():
    layers = load_layers(TIF)
    ground_y = np.load(OUT / "surface_y.npy").astype(int)
    canopy_raw, loss = layers["canopy_h"], layers["loss_year"]
    canopy = correct_canopy(canopy_raw, loss)
    rng = np.random.default_rng(SEED)
    trees = place_trees(canopy, ground_y, loss, rng)
    n = len(trees["x"])
    area_ha = canopy.size / 1e4

    lines = []
    say = lambda s="": (print(s), lines.append(s))
    cut_late = np.nan_to_num(loss, nan=0) > IMAGERY_YEAR
    say(f"Canopy correction: {100 * cut_late.mean():.1f}% of the window was cut after {IMAGERY_YEAR}; its canopy is set to 0 m.")
    say(f"Mean canopy height: {np.nanmean(canopy_raw):.1f} m in the file, {canopy.mean():.1f} m after correction.")
    say(f"Trees placed: {n:,} ({n / area_ha:.0f} per hectare over the whole window), one candidate per {CELL} m square.")
    say(f"Height of placed trees: median {np.median(trees['h']):.0f} blocks, 90th percentile {np.percentile(trees['h'], 90):.0f}, tallest {trees['h'].max()}.")
    say()
    say(f"{'loss year':<11}{'area %':>8}{'trees/ha':>10}{'median h':>10}")
    for yv in [0] + sorted(int(v) for v in np.unique(loss[np.isfinite(loss)]) if v > 0):
        m = np.nan_to_num(loss, nan=0) == yv
        if m.mean() < 0.005:
            continue
        t = trees["loss"] == yv
        med = f"{np.median(trees['h'][t]):.0f}" if t.any() else "-"
        say(f"{'none' if yv == 0 else yv:<11}{100 * m.mean():>8.1f}{t.sum() / (m.sum() / 1e4):>10.0f}{med:>10}")
    nb = block_count(trees)
    say()
    say(f"About {nb / 1e6:.1f} million blocks of trunk and leaves in total (about {nb / canopy.size:.1f} per ground column).")
    say("These counts treat every stand the same way: one tree per 6 m square wherever the canopy is 3 m or more. Young stands")
    say("in real life are much denser than old ones, so the young stands here are too sparse. Chunk 6 refines the stands.")
    OUT.mkdir(exist_ok=True)
    np.savetxt(OUT / "trees.csv", np.column_stack([trees[k] for k in ("x", "z", "y", "h", "r", "loss")]),
               fmt="%d", delimiter=",", header="x,z,y_ground,height,crown_r,loss_year", comments="")
    (DOCS / "05_summary.txt").write_text("\n".join(lines) + "\n")

    # ---- picture: the correction, and a side view across a stand boundary
    fig = plt.figure(figsize=(11, 8.2), dpi=130)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.9])
    for i, (arr, title) in enumerate(((canopy_raw, "Canopy height in the file (m)"), (canopy, f"After removing cuts made after {IMAGERY_YEAR} (m)"))):
        ax = fig.add_subplot(gs[0, i]); im = ax.imshow(arr, cmap="YlGn", vmin=0, vmax=35)
        ax.set_title(title, fontsize=9); ax.set_xticks([]); ax.set_yticks([]); plt.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    row = 340; x0, x1, band = 325, 575, 3     # a slice chosen because it crosses from standing forest into the 2022 cut
    ax = fig.add_subplot(gs[1, :])
    sel = (np.abs(trees["z"] - row) <= band) & (trees["x"] >= x0) & (trees["x"] <= x1)
    xs = np.arange(x0, x1)
    ax.fill_between(xs, 0, ground_y[row - band:row + band + 1, x0:x1].max(axis=0), color="#8b7355")   # highest ground in the slice
    order = np.argsort(-np.abs(trees["z"][sel] - row))                      # draw the farthest trees first
    for i in np.flatnonzero(sel)[order]:
        x, y, h, r = trees["x"][i], trees["y"][i], trees["h"][i], trees["r"][i]
        base = y + 0.35 * h
        ax.add_patch(Rectangle((x - 0.3, y), 0.6, h, color="#5b3a1e", lw=0))
        ax.add_patch(Polygon([(x - r, base), (x + r, base), (x, y + h)], closed=True, color="#2e7d32", alpha=0.75, lw=0))
    cut = np.nan_to_num(loss[row, x0:x1], nan=0)
    for yv, col in ((2003, "#3b0f70"), (2013, "#cc4778"), (2021, "#f89441"), (2022, "#fdc328")):
        m = cut == yv
        if m.any():
            ax.scatter(xs[m], np.full(m.sum(), ground_y[row, x0:x1].min() - 6), s=3, color=col, label=f"cut in {yv}")
    ax.set_xlim(x0, x1); ax.set_ylim(ground_y[row, x0:x1].min() - 10, ground_y[row, x0:x1].max() + 40)
    ax.set_aspect("equal"); ax.legend(fontsize=7, loc="upper left", ncol=3)
    ax.set_title(f"Side view of the trees within {band} m of row {row} (a 6 m deep slice), x = {x0} to {x1}", fontsize=9)
    ax.set_xlabel("x (blocks east)", fontsize=8); ax.set_ylabel("y (blocks)", fontsize=8); ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(DOCS / "05_trees.png"); plt.close(fig)
    print("Wrote out/trees.csv, docs/05_summary.txt, docs/05_trees.png")


if __name__ == "__main__":
    main()
