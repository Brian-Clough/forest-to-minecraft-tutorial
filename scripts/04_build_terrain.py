"""Chunk 4: turn the elevation raster into a grid of block heights.

Reads data/forest_aoi.tif, picks the elevation layer that has data, and converts metres to whole blocks.
Writes out/surface_y.npy (the y of the top ground block in every 1 m column), plus a summary and a picture in docs/.

Usage: python scripts/04_build_terrain.py [path/to/forest_aoi.tif]

Conventions used from here on (chunks 5 to 8 rely on them):
  * One block is 1 m. A column of the raster is a column of blocks. Raster row r is world z = r, raster column c is world x = c.
  * Row 0 is the NORTH edge, so Minecraft's north (negative z) points up the page, as in a normal map.
  * The lowest ground sits at y = Y_BASE. The build limit is y = 319 and the bottom is y = -64.
"""
import sys, pathlib
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIF = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "forest_aoi.tif"
OUT, DOCS = ROOT / "out", ROOT / "docs"
OUT.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True)

BANDS = ["dem3dep1m", "dem3dep10m", "canopy_h", "loss_year", "treecover2000"]
NODATA = -9998
Y_BASE = 0           # y of the lowest ground column; leaves 64 blocks of stone below it
Y_MAX = 319          # Minecraft Java build limit


def load_dem(path):
    with rasterio.open(path) as src:
        assert src.count == len(BANDS) and src.res == (1.0, 1.0), "expected the five-band, 1 m export"
        data = src.read().astype("float64")
    layers = {}
    for name, a in zip(BANDS, data):
        a = a.copy(); a[~np.isfinite(a) | (a <= NODATA)] = np.nan; layers[name] = a
    for name in ("dem3dep1m", "dem3dep10m"):
        if np.isfinite(layers[name]).mean() >= 0.95:
            return name, layers[name], layers["canopy_h"]
    raise SystemExit("No elevation band covers the window.")


def step_stats(y):
    """How steep is the world, in the units a player feels? Largest height difference to any of the four neighbours."""
    d = np.zeros_like(y)
    for axis in (0, 1):
        diff = np.abs(np.diff(y, axis=axis))
        a = [slice(None)] * 2; b = [slice(None)] * 2
        a[axis], b[axis] = slice(0, -1), slice(1, None)
        d[tuple(a)] = np.maximum(d[tuple(a)], diff); d[tuple(b)] = np.maximum(d[tuple(b)], diff)
    return d


def hillshade(z, azimuth=315.0, altitude=45.0, exag=3.0):
    gy, gx = np.gradient(z * exag)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(gy, -gx)
    az, alt = np.radians(360.0 - azimuth + 90.0), np.radians(altitude)
    return np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)


def main():
    name, dem, canopy = load_dem(TIF)
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    # Fill any stray missing cells with the mean. (None here; the check keeps a bad window from silently becoming holes.)
    if np.isnan(dem).any():
        dem = np.where(np.isnan(dem), np.nanmean(dem), dem)

    y = np.round(dem - dem.min()).astype(int) + Y_BASE        # 1 m = 1 block, lowest ground at Y_BASE
    top = y.max() + int(np.nanmax(canopy))
    assert top <= Y_MAX, f"terrain plus the tallest tree reaches y = {top}, over the build limit {Y_MAX}"

    say(f"Elevation source: {name}")
    say(f"Ground height in blocks: y = {y.min()} to {y.max()} ({y.max() - y.min()} blocks of relief)")
    say(f"Tallest tree top if stood on the highest ground: y = {top} (limit {Y_MAX})")
    say()
    s = step_stats(y)
    say("Largest height difference between a column and its four neighbours:")
    for label, test in (("flat (0 blocks)", lambda a: a == 0), ("one block (walkable)", lambda a: a == 1),
                        ("two or more (needs a jump)", lambda a: a >= 2)):
        say(f"  {label:<28}{100 * test(s).mean():>6.1f}% of columns")
    # How wide are the terraces? Count the run lengths of equal height along the east-west direction.
    runs = []
    for row in y[::8]:
        edges = np.flatnonzero(np.diff(row) != 0)
        runs.extend(np.diff(edges))
    say(f"Median terrace width along east-west lines: {np.median(runs):.0f} blocks (10th to 90th percentile {np.percentile(runs, 10):.0f} to {np.percentile(runs, 90):.0f})")
    say()
    say("The file's 10 m elevation was already smoothed to 1 m in the export, so no further smoothing is applied.")
    say("Whole-block heights turn gentle slopes into wide flat steps. That is a property of the block grid, not an error.")
    (DOCS / "04_summary.txt").write_text("\n".join(lines) + "\n")
    np.save(OUT / "surface_y.npy", y.astype(np.int16))
    say("Wrote out/surface_y.npy (int16, rows = z from the north edge, columns = x from the west edge)")

    # ---- picture: shaded relief of the block heights, and a cross-section through the middle of the window
    r = dem.shape[0] // 2
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), dpi=140, gridspec_kw=dict(width_ratios=[1, 1.25]))
    axs[0].imshow(hillshade(dem), cmap="gray", vmin=0, vmax=1)
    axs[0].axhline(r, color="#d62728", lw=1)
    axs[0].set_title("Shaded relief of the elevation (north up)", fontsize=9); axs[0].set_xticks([]); axs[0].set_yticks([])
    c0 = 400; w = slice(c0, c0 + 120)
    xs = np.arange(1024)[w]
    axs[1].plot(xs, dem[r, w] - dem.min() + Y_BASE, color="#999999", lw=1.2, label="elevation in the file")
    axs[1].step(xs, y[r, w], where="mid", color="#1f77b4", lw=1.6, label="whole blocks (what we build)")
    axs[1].set_title(f"Cross-section along the red line (row {r}), 120 m wide", fontsize=9)
    axs[1].set_xlabel("x (blocks east of the west edge)", fontsize=8); axs[1].set_ylabel("y (block height)", fontsize=8)
    axs[1].tick_params(labelsize=7); axs[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(DOCS / "04_terrain.png"); plt.close(fig)
    print("Wrote docs/04_summary.txt, docs/04_terrain.png")


if __name__ == "__main__":
    main()
