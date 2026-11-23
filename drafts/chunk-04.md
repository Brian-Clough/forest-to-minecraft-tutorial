# Chunk 4 notes: from elevation to block heights

Notes for the tutorial text, not final prose. Script: `scripts/04_build_terrain.py`. Picture: `docs/04_terrain.png`. Numbers: `docs/04_summary.txt`. Output (not committed, rebuilt by the script): `out/surface_y.npy`.

## What this chunk does
Turn the elevation band into one whole number per column: the y of the top ground block. Everything later (trees, ground cover, region files) stands on this array.

## Points worth making
1. **Fix the conventions now.** One block is 1 m. Raster row r is world z = r and column c is world x = c. Row 0 is the north edge, so north is up the page as on a map. Minecraft's z grows southward, so a raster row index and a z coordinate agree without flipping anything. Say these once; later chunks refer back.
2. **Pick the lowest ground height.** The lowest column goes at y = 0, with 64 blocks of stone below it (the world bottom is y = -64). The highest ground is y = 123 and the tallest tree would reach y = 157, far below the build limit of 319. The script asserts this, so a steeper window fails loudly instead of being cut off.
3. **No extra smoothing.** I tried a Gaussian blur first. It changed heights by 0.02 m on average and the largest change was 0.5 m, because the export already smoothed the 10 m model to 1 m. The blur did nothing, so it is not in the script. The honest teaching point: check whether a processing step does anything before keeping it.
4. **Gentle slopes become wide steps.** Rounding to whole blocks turns a slope of about 0.1 m per m into flat terraces. The median terrace is 9 blocks wide (10th to 90th percentile 5 to 19). Every neighbouring pair differs by 0 or 1 block, so the whole world is walkable without jumping. The cross-section panel shows the staircase against the true line.
5. **A hillshade of whole-block heights looks like contour stripes.** My first picture used the rounded heights and looked like a topographic map gone wrong. The left panel shades the continuous elevation instead. Worth a sentence: show data the way the eye can read it, and say which version you are showing.

## Numbers for the text
- Window 1,024 x 1,024 columns, elevation from the 10 m model (no 1 m lidar here).
- Ground y = 0 to 123, 123 blocks of relief; tallest tree top y = 157.
- Neighbour steps: 79.5% flat, 20.5% one block, 0.0% two or more.
- Median terrace width 9 blocks east-west.

## Things to say honestly
- The terrain is the 10 m model resampled, so it cannot show features smaller than about 10 m. Logging roads, stream banks and cut banks are missing. A reader with 1 m lidar will get much more detail from the same script, because the script picks the lidar band when it covers the window.
- Vertical resolution is the block: 1 m. A 0.4 m rise disappears or doubles depending on rounding. For very flat sites, consider scaling heights up (for example 2 blocks per metre); this window does not need it.

## Open decisions
- Whether to offer a vertical scale option. I left it out to keep the script short.
- Whether the tutorial should say anything about the Minecraft sea level (y = 63 in default worlds). Our world has no water and sets ground from y = 0, so I skipped it.
