# From forest maps to Minecraft blocks

This tutorial turns open elevation and canopy height maps into a Minecraft Java Edition world where one block is one metre. The example is a square kilometre of western US forest with clearcuts of different ages, so you can see structure (tall stands, young regrowth, bare ground) as terrain you can walk through.

Nothing here needs the game running: Python writes the world files directly. You only open Minecraft at the end to look at the result.

> Status: work in progress. Chunks 1 and 2 are written; the rest follow.

## Contents
1. [What we are building and why one block per metre](#1-what-we-are-building)
2. [The data](#2-the-data)
3. Looking at the raster *(next)*
4. Terrain *(next)*
5. Trees *(next)*
6. Ground by stand age *(next)*
7. Writing the world files *(next)*
8. `level.dat` and the version number *(next)*
9. Checking the result *(next)*
10. Opening it in the game, and what to be honest about *(next)*

## 1. What we are building

The goal is a world you can fly over, where the shapes of the land and the forest come from data and not from a generator. Three maps carry all the information:

- **Elevation** decides how high the ground is.
- **Canopy height** decides where trees stand and how tall they are.
- **Year of forest loss** decides what the ground looks like, so a recent clearcut and a regrown one are visibly different.

**Why one block per metre.** Minecraft's blocks are one cubic metre by design, and the canopy height map is itself at 1 m. At that scale a pixel is a block and no resampling is needed, so every choice you see in the world is traceable to a number in the data. A square of 1,024 m is also about as much as loads comfortably and is big enough to hold several stands.

**A limit to know about early.** The game builds from -64 to 320, 384 blocks tall. A kilometre of mountainous ground can span more than that, so we use heights relative to the lowest point in the window and check the range before we write anything.

**What this is not.** It is a picture drawn from public maps, not a measurement. Chunk 10 lists what the world can and cannot tell you.

## 2. The data

We use three public layers, all free to use with credit (full table and citations in [`data/SOURCES.md`](data/SOURCES.md)):

| Layer | What it gives | Resolution |
|---|---|---|
| USGS 3DEP | Bare-earth elevation from lidar | 1 m where lidar exists, otherwise 10 m |
| Meta/WRI canopy height | Height of the tallest vegetation, estimated from satellite photographs | 1 m |
| Hansen Global Forest Change | Year each area lost its forest, 2001 to 2025 | about 28 m |

The canopy height map is a model's estimate and not a lidar measurement, and most of its imagery dates from 2018 to 2020. Hansen's loss year is coarse, so small cuts are missed. These limits matter for how far you can trust the world, and we come back to them in chunk 10.

### Getting the window out of Earth Engine

The example data will live in [`data/`](data/) (it is not there yet), so readers can skip this step. To make your own window anywhere in the US:

1. Open [`ee/export_aoi.js`](ee/export_aoi.js) in the Earth Engine Code Editor and press Run once. It adds the Hansen loss layer to the map (yellow for old loss, purple for recent).
2. Pan and zoom to a patchwork of clearcuts of different ages, then leave the map centred where you want the window. The script takes the map centre as the middle of a 1,024 m square.
3. Press Run again, then start the export in the Tasks tab. It writes one GeoTIFF with five bands: `dem3dep1m`, `dem3dep10m`, `canopy_h`, `loss_year`, `treecover2000`.

The script exports in UTM, the metric map projection for the area, at a scale of exactly 1 m. This is what makes one pixel equal one block. Missing values are -9999 (for elevation and height) so that "no data" is never mistaken for "zero metres".

Why export the 10 m elevation as well as the 1 m one? The 1 m lidar model does not cover all of the US, and Earth Engine cannot tell you in advance whether your window falls in a gap. Exporting both lets chunk 3 check which one holds real values, so you can fall back when the 1 m layer is empty.

Next: [3. Looking at the raster](#3-looking-at-the-raster-next).
