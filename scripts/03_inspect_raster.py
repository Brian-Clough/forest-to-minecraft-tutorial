"""Chunk 3: look at the exported raster before building anything from it.

Reads data/forest_aoi.tif (five 1 m bands in UTM), masks missing values, picks the elevation layer that has real data,
prints a summary and checks, and writes images to docs/.

Usage: python scripts/03_inspect_raster.py [path/to/forest_aoi.tif]
"""
import sys, pathlib
import numpy as np
import rasterio
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIF = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "forest_aoi.tif"
OUT = ROOT / "docs"
OUT.mkdir(exist_ok=True)

BANDS = ["dem3dep1m", "dem3dep10m", "canopy_h", "loss_year", "treecover2000"]
NODATA = -9998          # the export marks missing as -9999; anything at or below this is "no data"
BLOCK_HEIGHT = 384      # Minecraft Java builds from y = -64 to 320


def load(path):
    with rasterio.open(path) as src:
        assert src.count == len(BANDS), f"expected {len(BANDS)} bands, found {src.count}"
        assert src.crs.is_projected and src.res == (1.0, 1.0), "expected a metric CRS at 1 m"
        data = src.read().astype("float64")
        info = dict(crs=src.crs, bounds=src.bounds, shape=src.shape, transform=src.transform)
    layers = {}
    for name, a in zip(BANDS, data):
        a = a.copy()
        a[~np.isfinite(a) | (a <= NODATA)] = np.nan     # one missing-value convention from here on: NaN
        layers[name] = a
    return layers, info


def choose_dem(layers, min_valid=0.95):
    """Use the 1 m lidar model if it covers the window, otherwise the 10 m model smoothed to 1 m."""
    for name in ("dem3dep1m", "dem3dep10m"):
        if np.isfinite(layers[name]).mean() >= min_valid:
            return name, layers[name]
    raise SystemExit("Neither elevation band covers the window. Pick another window or add another elevation source.")


def hillshade(dem, azimuth=315.0, altitude=45.0, cell=1.0, z=3.0):
    """Standard shaded relief: how much each cell faces the sun. Returns 0 (dark) to 1 (bright).
    z exaggerates heights so gentle terrain is visible in the picture; it does not change the data."""
    gy, gx = np.gradient(dem * z, cell)                       # gy is north-south with row 0 at the top (north)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(gy, -gx)
    az, alt = np.radians(360.0 - azimuth + 90.0), np.radians(altitude)
    shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    return np.clip(shade, 0, 1)


def main():
    layers, info = load(TIF)
    b = info["bounds"]
    lon, lat = Transformer.from_crs(info["crs"], 4326, always_xy=True).transform((b.left + b.right) / 2, (b.bottom + b.top) / 2)
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    say(f"File: {TIF.name}")
    say(f"Grid: {info['shape'][1]} x {info['shape'][0]} cells of 1 m, CRS {info['crs']}")
    say(f"South-west corner (E, N): {b.left:.0f}, {b.bottom:.0f}   centre: {lat:.4f} N, {abs(lon):.4f} W")
    say()
    say(f"{'band':<15}{'valid %':>8}{'min':>9}{'max':>9}{'mean':>9}")
    for n in BANDS:
        a = layers[n]; v = a[np.isfinite(a)]
        say(f"{n:<15}{100 * v.size / a.size:>8.1f}" + (f"{v.min():>9.1f}{v.max():>9.1f}{v.mean():>9.1f}" if v.size else f"{'-':>9}{'-':>9}{'-':>9}"))

    dem_name, dem = choose_dem(layers)
    relief = np.nanmax(dem) - np.nanmin(dem)
    say()
    say(f"Elevation used: {dem_name}. Range {np.nanmin(dem):.1f} to {np.nanmax(dem):.1f} m, relief {relief:.1f} m.")
    say(f"Fits the {BLOCK_HEIGHT}-block build height with {BLOCK_HEIGHT - relief:.0f} blocks to spare for trees: {'yes' if relief + np.nanmax(layers['canopy_h']) < BLOCK_HEIGHT else 'NO, scale the terrain down'}")

    loss = layers["loss_year"]; canopy = layers["canopy_h"]
    say()
    say("Canopy height (m) by year of forest loss:")
    say(f"{'loss year':<11}{'share %':>8}{'mean':>7}{'p10':>6}{'p50':>6}{'p90':>6}")
    for y in [0] + sorted(int(v) for v in np.unique(loss[np.isfinite(loss)]) if v > 0):
        m = loss == y
        if m.sum() < 0.005 * loss.size:
            continue
        v = canopy[m & np.isfinite(canopy)]
        say(f"{'none' if y == 0 else y:<11}{100 * m.mean():>8.1f}{v.mean():>7.1f}{np.percentile(v, 10):>6.0f}{np.percentile(v, 50):>6.0f}{np.percentile(v, 90):>6.0f}")
    say()
    say("Read the table against the dates: the canopy map comes from imagery around 2018 to 2020, so areas cut after that")
    say("still show standing trees. Chunk 6 uses the loss year to correct this.")
    (OUT / "03_summary.txt").write_text("\n".join(lines) + "\n")

    # ---- images
    hs = hillshade(dem)
    ext = (b.left, b.right, b.bottom, b.top)
    fig, ax = plt.subplots(figsize=(6.4, 6.0), dpi=150)
    ax.imshow(hs, cmap="gray", extent=ext, vmin=0, vmax=1)
    ax.set_title(f"Shaded relief from {dem_name}, relief {relief:.0f} m (heights exaggerated 3x)", fontsize=9)
    ax.set_xlabel("Easting (m, UTM)"); ax.set_ylabel("Northing (m, UTM)")
    ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(OUT / "03_hillshade.png"); plt.close(fig)

    fig, axs = plt.subplots(2, 2, figsize=(10, 9.2), dpi=130)
    panels = [
        (axs[0, 0], dem, dict(cmap="terrain"), "Elevation (m)"),
        (axs[0, 1], canopy, dict(cmap="YlGn", vmin=0, vmax=35), "Canopy height (m), imagery ~2018 to 2020"),
        (axs[1, 0], np.where(loss > 0, loss, np.nan), dict(cmap="plasma", vmin=2001, vmax=2025), "Year of forest loss (grey = none)"),
        (axs[1, 1], layers["treecover2000"], dict(cmap="Greens", vmin=0, vmax=100), "Tree cover in 2000 (%)"),
    ]
    for a, arr, kw, title in panels:
        im = a.imshow(arr, extent=ext, **kw); a.set_title(title, fontsize=10)
        a.set_facecolor("#cccccc"); a.set_xticks([]); a.set_yticks([])
        plt.colorbar(im, ax=a, fraction=0.046, pad=0.02)
    fig.suptitle(f"The window: 1,024 m square at {lat:.3f} N, {abs(lon):.3f} W", fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / "03_four_layers.png"); plt.close(fig)
    say(); print("Wrote docs/03_summary.txt, docs/03_hillshade.png, docs/03_four_layers.png")


if __name__ == "__main__":
    main()
