"""Chunk 6: give each stand its own treatment, by age, and choose the ground block under every column.

Reads data/forest_aoi.tif and out/surface_y.npy (run 04_build_terrain.py first). Replaces chunk 5's single rule
(one tree per 6 m square) with a density and a height rule for each stand, and writes:
  out/trees.csv     one row per tree (same columns as chunk 5; blocks come in chunk 7)
  out/ground.npy    one code per ground column: 0 mature forest, 1 regrowth, 2 recent cut (see GROUND_BLOCK)
  docs/06_summary.txt, docs/06_stands.png

Usage: python scripts/06_stands_and_ground.py [path/to/forest_aoi.tif]
"""
import sys, pathlib
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Polygon, Rectangle

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIF = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "forest_aoi.tif"
OUT, DOCS = ROOT / "out", ROOT / "docs"

BANDS = ["dem3dep1m", "dem3dep10m", "canopy_h", "loss_year", "treecover2000"]
NODATA = -9998
IMAGERY_YEAR = 2019
MIN_TREE_H = 3.0
SEED = 20260101
SITE = 3                 # candidate tree sites: one per 3 m square (1,111 per ha), thinned to each stand's density

# ASSUMPTIONS, not measurements. Check them against a local source before you rely on them.
DENSITY_MATURE = 280     # stems per ha in uncut forest (chunk 5's grid gave about 265)
DENSITY_BY_AGE = [(5, 1100), (10, 900), (20, 600), (40, 400)]   # (age in years, stems per ha) for regrowth, interpolated
# Height of regrowth by age: passes through one data point (the 2003 stand, age 16 in 2019, median canopy 10 m) with an
# exponent chosen so that age 6 comes out under 3 m, because the canopy map shows almost nothing in the 2013 stand.
H_ANCHOR_AGE, H_ANCHOR_M, H_EXPONENT = 16, 10.0, 1.3

GROUND_BLOCK = {0: "podzol", 1: "grass_block", 2: "coarse_dirt"}   # mature floor, regrowth, recent cut


def load_layers(path):
    with rasterio.open(path) as src:
        data = src.read().astype("float64")
    layers = {}
    for name, a in zip(BANDS, data):
        a = a.copy(); a[~np.isfinite(a) | (a <= NODATA)] = np.nan; layers[name] = a
    return layers


def regrowth_height(age):
    return H_ANCHOR_M * (np.asarray(age, dtype=float) / H_ANCHOR_AGE) ** H_EXPONENT


def density_for_age(age):
    ages, dens = zip(*DENSITY_BY_AGE)
    return np.interp(age, ages, dens)


def classify(loss):
    """0 mature (never cut in the loss record), 1 regrowth (cut up to the imagery year), 2 recent cut (after it)."""
    loss = np.nan_to_num(loss, nan=0)
    cls = np.zeros(loss.shape, dtype=np.uint8)
    cls[(loss > 0) & (loss <= IMAGERY_YEAR)] = 1
    cls[loss > IMAGERY_YEAR] = 2
    return cls


def place_trees(canopy, ground_y, loss, cls, rng):
    h, w = canopy.shape
    rows = np.arange(0, h - SITE + 1, SITE); cols = np.arange(0, w - SITE + 1, SITE)
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    z = rr + rng.integers(0, SITE, rr.shape); x = cc + rng.integers(0, SITE, cc.shape)
    lv = np.nan_to_num(loss[z, x], nan=0).astype(int); c = cls[z, x]
    age = np.where(c == 1, IMAGERY_YEAR - lv, 0)
    site_density = 1e4 / SITE ** 2
    p = np.where(c == 0, DENSITY_MATURE, np.where(c == 1, density_for_age(age), 0)) / site_density
    keep = (rng.random(p.shape) < p) & (c < 2)
    seen = np.nan_to_num(canopy[z, x], nan=0.0)                      # height the canopy map shows at this point
    height_m = np.where(seen >= MIN_TREE_H, seen, np.where(c == 1, regrowth_height(age), 0.0))
    keep &= height_m >= 2.0
    z, x, height_m, lv = z[keep], x[keep], height_m[keep], lv[keep]
    hb = np.maximum(np.round(height_m).astype(int), 2)
    r = np.clip(np.round(hb / 8), 1, 4).astype(int)                  # crown half-width: about an eighth of the height
    return dict(x=x, z=z, y=ground_y[z, x], h=hb, r=r, loss=lv)


def main():
    L = load_layers(TIF)
    ground_y = np.load(OUT / "surface_y.npy").astype(int)
    canopy, loss = L["canopy_h"], L["loss_year"]
    cls = classify(loss)
    rng = np.random.default_rng(SEED)
    T = place_trees(canopy, ground_y, loss, cls, rng)
    n = len(T["x"]); area_ha = cls.size / 1e4
    lossv = np.nan_to_num(loss, nan=0)

    lines = []
    say = lambda s="": (print(s), lines.append(s))
    say(f"Stand classes (share of the window): mature {100 * (cls == 0).mean():.1f}%, regrowth {100 * (cls == 1).mean():.1f}%, "
        f"recent cut {100 * (cls == 2).mean():.1f}%.")
    say(f"Trees placed: {n:,} ({n / area_ha:.0f} per hectare over the whole window).")
    say()
    say(f"{'stand':<14}{'area %':>8}{'trees/ha':>10}{'median h':>10}{'ground block':>16}")
    for name, m, code in (("mature", cls == 0, 0),
                          *[(f"cut {yv}", lossv == yv, 1 if yv <= IMAGERY_YEAR else 2)
                            for yv in sorted(int(v) for v in np.unique(lossv) if v > 0) if (lossv == yv).mean() >= 0.005]):
        t = np.isin(T["loss"], [0] if name == "mature" else [int(name[4:])]) & (cls[T["z"], T["x"]] == code)
        med = f"{np.median(T['h'][t]):.0f}" if t.any() else "-"
        say(f"{name:<14}{100 * m.mean():>8.1f}{t.sum() / (m.sum() / 1e4):>10.0f}{med:>10}{GROUND_BLOCK[code]:>16}")
    say()
    say(f"Regrowth height rule: {H_ANCHOR_M:.0f} m at age {H_ANCHOR_AGE}, scaled by (age/{H_ANCHOR_AGE})^{H_EXPONENT}; "
        f"age 6 gives {float(regrowth_height(6)):.1f} m.")
    say("Densities and the height curve are assumptions (see the constants at the top of the script).")
    OUT.mkdir(exist_ok=True)
    np.savetxt(OUT / "trees.csv", np.column_stack([T[k] for k in ("x", "z", "y", "h", "r", "loss")]),
               fmt="%d", delimiter=",", header="x,z,y_ground,height,crown_r,loss_year", comments="")
    np.save(OUT / "ground.npy", cls)
    (DOCS / "06_summary.txt").write_text("\n".join(lines) + "\n")

    # ---- picture
    fig = plt.figure(figsize=(11, 8.6), dpi=130)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.7])
    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(cls, cmap=ListedColormap(["#2e5e3a", "#9bc46a", "#c9a27a"]), vmin=0, vmax=2, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title("Stand class, which sets the trees and the ground block", fontsize=9)
    for col, lab in (("#2e5e3a", "mature (podzol)"), ("#9bc46a", "regrowth (grass)"), ("#c9a27a", "recent cut (coarse dirt)")):
        ax.add_patch(Rectangle((0, 0), 0, 0, color=col, label=lab))
    ax.legend(fontsize=7, loc="lower left")
    ax = fig.add_subplot(gs[0, 1])
    a = np.linspace(2, 40, 100); ax.plot(a, regrowth_height(a), color="#2e7d32")
    for yv, col in ((2003, "#3b0f70"), (2013, "#cc4778")):
        m = (lossv == yv) & np.isfinite(canopy)
        ax.scatter([IMAGERY_YEAR - yv], [np.median(canopy[m])], color=col, zorder=3, label=f"canopy map, median of the {yv} cut")
    ax.axhline(MIN_TREE_H, color="grey", ls=":", lw=1); ax.text(30, MIN_TREE_H + 0.4, "canopy map shows nothing below about 3 m", fontsize=6, ha="right")
    ax.set_xlabel("stand age in 2019 (years)", fontsize=8); ax.set_ylabel("height (m)", fontsize=8); ax.tick_params(labelsize=7)
    ax.set_title("Regrowth height rule (line) and what the canopy map shows", fontsize=9); ax.legend(fontsize=7, loc="upper left")
    # two side views along row 640, chosen by scanning the loss map: 2013 regrowth -> mature -> 2022 cut, then 2022 cut -> 2003 regrowth
    row, band = 640, 3
    for k, (x0, x1) in enumerate(((100, 290), (505, 695))):
        axs = fig.add_subplot(gs[1, k]); xs = np.arange(x0, x1)
        axs.fill_between(xs, 0, ground_y[row - band:row + band + 1, x0:x1].max(axis=0), color="#8b7355")
        sel = (np.abs(T["z"] - row) <= band) & (T["x"] >= x0) & (T["x"] < x1)
        for i in np.flatnonzero(sel)[np.argsort(-np.abs(T["z"][sel] - row))]:
            x, y, hh, r = T["x"][i], T["y"][i], T["h"][i], T["r"][i]
            axs.add_patch(Rectangle((x - 0.3, y), 0.6, hh, color="#5b3a1e", lw=0))
            axs.add_patch(Polygon([(x - r, y + 0.35 * hh), (x + r, y + 0.35 * hh), (x, y + hh)], closed=True, color="#2e7d32", alpha=0.75, lw=0))
        gmin, gmax = ground_y[row, x0:x1].min(), ground_y[row, x0:x1].max()
        for yv, col in ((0, "#2e5e3a"), (2003, "#3b0f70"), (2013, "#cc4778"), (2022, "#fdc328")):
            m = lossv[row, x0:x1] == yv
            if m.any():
                axs.scatter(xs[m], np.full(m.sum(), gmin - 5), s=3, color=col, label="uncut" if yv == 0 else f"cut in {yv}")
        axs.set_xlim(x0, x1); axs.set_ylim(gmin - 9, gmax + 38); axs.set_aspect("equal")
        axs.legend(fontsize=7, loc="upper left", ncol=3)
        axs.set_title(f"Side view, row {row} (6 m slice), x = {x0} to {x1}", fontsize=9)
        axs.set_xlabel("x (blocks east)", fontsize=8); axs.set_ylabel("y (blocks)", fontsize=8); axs.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(DOCS / "06_stands.png"); plt.close(fig)
    print("Wrote out/trees.csv, out/ground.npy, docs/06_summary.txt, docs/06_stands.png")


if __name__ == "__main__":
    main()
