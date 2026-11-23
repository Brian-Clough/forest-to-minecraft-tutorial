# Draft: Chunk 3, look at the raster before you build anything

*A first-pass tutorial draft to show where each figure would sit. It is meant to be rewritten in your voice; paths are relative to the repo root. Companion files: `drafts/chunk-03.md` (the bullet notes), `scripts/03_inspect_raster.py`, `docs/03_summary.txt`.*

---

## 3. Look before you build

The export from chunk 2 gave us one file with five layers stacked on a 1 m grid. Before turning any of it into blocks, spend ten minutes looking at it. Every later step trusts what is in this file, and a mistake here (the wrong pixel size, an empty layer, a map that is years out of date) will not announce itself. It will just produce a world that looks plausible and is wrong.

Run the inspection script:

```
python scripts/03_inspect_raster.py
```

It prints a short report and writes two pictures. We will go through what each one tells us.

### Is the grid what we think it is?

The script first checks two things and stops if either is wrong: the file is in a metric coordinate system (UTM zone 10N), and each cell is exactly 1 m. Ours is 1,024 by 1,024 cells, so the window is just over a kilometre on a side. That matters because one cell will become one block, so this window becomes a 1,024-block-square world.

### Which layers hold real data?

The export marks missing values as -9999, and Earth Engine can also leave blanks. The script turns both into one "no data" marker so that later code can never mistake a missing value for a height of zero.

```
band            valid %      min      max     mean
dem3dep1m           0.0        -        -        -
dem3dep10m        100.0    209.2    332.5    267.2
canopy_h          100.0      0.0     34.0     12.6
loss_year         100.0      0.0   2023.0   1344.7
treecover2000     100.0      0.0    100.0     81.2
```

Read the first two rows. The 1 m lidar elevation is empty here, because no 1 m lidar has been flown over this part of the Cascades. The 10 m elevation covers everything. Exporting both layers in chunk 2 is what lets the script carry on: it uses the lidar if it covers the window and falls back to the 10 m model if not. The price is detail. The 10 m model was smoothed up to 1 m during export, so the terrain it gives us is gentle and cannot show anything smaller than about ten metres.

### The picture of the four layers

![The four layers of the raster](docs/03_four_layers.png)

*Figure 1. The four layers over the same 1,024 m square. Top left: elevation. Top right: canopy height. Bottom left: the year each patch of forest was cut. Bottom right: tree cover in 2000.*

Look at the panels in this order.

**Top left, elevation.** A ridge in the upper right drops to a stream valley in the lower left, 123 m from top to bottom. Minecraft builds from y = -64 up to y = 320, which is 384 blocks. With 123 m of relief and trees at most 34 m tall, we have 261 blocks to spare. The script prints a plain yes or no for this, so a steeper window would tell you to scale the terrain down.

**Top right, canopy height.** Dark green is tall forest, pale is short or empty. Two things stand out. The pale triangle in the upper left has no trees at all. And thin pale lines cross the right half: these are roads, a good sign that the map is detailed enough to be interesting.

**Bottom left, year of forest loss.** This is the layer that tells us where the forest was cut and when. The colours are years: dark purple for the early 2000s, pink for the 2010s, yellow for about 2022, grey for no cut. Compare it with the canopy panel above. The pink block in the upper left lines up with the bare triangle, which is how the canopy map shows a cut from the 2010s: the replanted trees are still too small for the model to see.

**Bottom right, tree cover in 2000.** A baseline from the start of the record. The pale patch in the upper middle was not forested in 2000 and sits in a region that shows no cut afterwards, which suggests it was cleared before the record began and has regrown since. That is my reading from the maps, not something the files state, so treat it as a guess.

### The maps disagree, and the dates explain why

The canopy map and the loss map are not from the same date. The script puts the numbers side by side:

```
loss year   share %   mean   p10   p50   p90
none           33.2   14.3     9    14    21
2003           17.7   10.1     6    10    14
2013           20.3    0.1     0     0     0
2021            1.5   22.5    20    23    26
2022           26.7   21.2    17    22    26
```

The 2013 cut shows no trees, which is right. The 2003 cut shows trees about 10 m tall, which is plausible for a 20-year-old plantation. But the areas cut in 2021 and 2022 still show trees over 20 m tall. They were cut after the imagery behind the canopy map was taken (around 2018 to 2020), so the canopy layer still shows the forest that has since been removed. If we built the world from canopy height alone, we would plant tall trees in a clearcut.

This is the main lesson of the chunk, so it is worth stating plainly: **two layers that look like they describe the same ground can describe it on different dates.** Chunk 6 uses the loss year to correct the canopy layer.

### Things to keep in mind

- The canopy map stops at 34 m. Mature Douglas-fir in this region is taller. The world will show what the map says, not the real stand.
- The loss map is blocky, about 28 m per cell, so stand boundaries in the world will be blocky too.
- The shaded-relief picture below exaggerates heights threefold so that gentle terrain is visible. The data are unchanged.

![Shaded relief of the elevation](docs/03_hillshade.png)

*Figure 2. Shaded relief of the elevation layer, heights exaggerated 3x for the picture only. Axes are UTM coordinates in metres.*

Next, chunk 4 turns this elevation layer into a grid of block heights.

---

## Notes on the figures (not for publication)

- **Lettering.** The panels in Figure 1 have no letters, so the prose says "top left" and so on. If you would rather refer to A to D, I can add them to the script in a few lines.
- **Order.** Figure 1 comes before the loss-year table so that readers see the disagreement as a picture before they read it as numbers. Figure 2 is optional; it mostly duplicates the elevation panel and could be dropped or moved into the terrain chunk.
- **A figure not made yet.** A plot of canopy height against loss year (one box per cohort) would show the stale-canopy problem faster than the table does. I held back because the table already carries it. It would be a 15-line addition.
- **Claims I have not checked.** The "cleared before 2000 and regrown" reading of the pale patch, and the "plantation" wording for the 2003 cut, are inferences from the maps. Rewrite or cut them unless you can confirm them against the site.
