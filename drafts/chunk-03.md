# Chunk 3 notes: looking at the raster

Notes for the tutorial text, not final prose. Script: `scripts/03_inspect_raster.py`. Images: `docs/03_four_layers.png`, `docs/03_hillshade.png`. Numbers: `docs/03_summary.txt`.

## What this chunk does
Open the GeoTIFF and look before building anything. Four things to check: the grid is what we think it is, which bands hold real values, the elevation fits in the game, and the maps agree with each other.

## Points worth making
1. **Check the grid first.** 1,024 x 1,024 cells, 1 m, metric CRS (UTM 10N). If the pixel size or CRS is wrong, every later step is wrong in a way that looks plausible. The script asserts both.
2. **One missing-value convention.** The export writes -9999 for missing, and Earth Engine can also leave NaN. The script converts both to NaN once, so later code never mistakes "no data" for "0 m".
3. **Band by band validity.** Here the 1 m lidar elevation band is 0% valid (no 1 m lidar exists in this window) and the 10 m band is 100% valid. The script picks whichever covers the window. This is the "export both" step from chunk 2 paying off. The 10 m data was smoothed to 1 m (bicubic) in the export, so the terrain is smooth and cannot show features smaller than about 10 m.
4. **Does it fit?** Minecraft Java builds from y = -64 to 320, 384 blocks. Relief here is 123 m, tallest canopy 34 m, so 261 blocks to spare. A steeper window may not fit and would need scaling.
5. **The maps disagree, on purpose of the dates.** The loss-year table shows the canopy map lagging: areas cut in 2021 and 2022 still have 21 to 22 m trees (imagery from about 2018 to 2020), the 2013 cut shows 0 m (seedlings are too small for the model to see), and the 2003 cut shows 10 m. Chunk 6 uses the loss year to remove trees cut after the imagery date.

## Numbers for the text
- Window: 46.7174 N, 123.4444 W, SW corner 465521 E, 5173342 N (UTM 10N).
- Loss cohorts: none 33%, 2003 18%, 2013 20%, 2021 1.5%, 2022 27%.
- Canopy height, median: no loss 14 m, 2003 cut 10 m, 2013 cut 0 m, 2022 cut 22 m (stale).
- Terrain gradient: median 0.10 m per m (about 6 degrees), 99th percentile 0.29 (about 16 degrees).

## Things to say honestly
- Canopy heights top out at 34 m, which looks low for mature Douglas-fir stands in this region. The model tends to cap tall trees. Say the world shows what the map says, not the true stand.
- The hillshade is exaggerated 3x only for the picture.
- Hansen's loss map is blocky (about 28 m cells): the world's stand boundaries will be blocky too.

## Open decision
Whether to commit the 2.6 MB GeoTIFF into the repo, or ask readers to download it. I assumed commit (small enough, and it makes the tutorial runnable).
