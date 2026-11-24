# Tutorial: Bringing geospatial data into Minecraft

This tutorial demonstrates how to create Minecraft worlds that utilize real world geospatial data. 

The motivating example is a 1 km block of timberland in the Pacific Northwest, USA. It includes mature and young forest, as well as recent clearcuts, to demonstrate how different types of continuous and categorical spatial data can be rendered in the game. Each block will represent 1 meter of real world space. 

This tutorial uses Earth Engine for data access and python for processing the data layers and converting to formats Minecraft can recognize. You do not need Minecraft itself to run the tutorial, just to view and explore the world when it's done. 

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

Minecraft generates new worlds by default, using its own internal logic. We are going to generate a map that is built with real world geospatial data instead. To do this, we'll use three layers:

- **Elevation data** to set the ground height.
- **A canopy height map** to locate trees and determine their height above ground.
- **A year of forest loss map** to categorize different forest conditions, so structural changes will be easy to see in the rendered world.

**Why one block per metre.** Minecraft's blocks are one cubic metre by design, and the canopy height map we will use is itself at 1 m, so we won't need to do any resampling to align with the resolution of the data. But, you can scale imported datasets differently for other applications. 

**A limit to know about early.** The game builds from -64 to 320, 384 blocks tall. A kilometre of mountainous ground can span more than that, so we use heights relative to the lowest point in the window and check the range before we write anything.

**What this is not.** The goal of this tutorial is to show how geospatial layers can be brought into Minecraft and rendered in a way that makes them explorable. The focus is on making sure the data "looks right" and represents real world structure. It is a visual tool, not an accurate measurement.

## 2. The data

We use three public layers, all free to use with credit (full table and citations in [`data/SOURCES.md`](data/SOURCES.md)):

| Layer | What it gives | Resolution |
|---|---|---|
| USGS 3DEP | Bare-earth elevation from lidar | 1 m where lidar exists, otherwise 10 m |
| Meta/WRI canopy height | Height of the tallest vegetation, estimated from satellite photographs | 1 m |
| Hansen Global Forest Change | Year each area lost its forest, 2001 to 2025 | about 28 m |

The canopy height map is a model's estimate and not a lidar measurement, and most of its imagery dates from 2018 to 2020. Hansen's loss year is coarse, so small cuts are missed. Bear in mind that the Minecraft map will carry these limitations forward. 

### Getting the window out of Earth Engine

I have included all necessary datasets for our example patch in [`data/`](data/), so if you want to get right to world building you can skip this step. However, if you'd like to replace it with your own site you can follow these steps to render a different 1 km window anywhere in the continental US:

1. Open [`ee/export_aoi.js`](ee/export_aoi.js) in the Earth Engine Code Editor and press Run once. It adds the Hansen loss layer to the map (yellow for old loss, purple for recent).
2. Pan and zoom to a patchwork of clearcuts of different ages, then leave the map centred where you want the window. The script takes the map centre as the middle of a 1,024 m square.
3. Press Run again, then start the export in the Tasks tab. It writes one GeoTIFF with five bands: `dem3dep1m`, `dem3dep10m`, `canopy_h`, `loss_year`, `treecover2000`. Note we will use the 1m DEM, but we're also getting the 10m product as a fallback; Earth Engine cannot tell you in advance whether your site will have 1m coverage. 

The script exports in UTM, the metric map projection for the area, at a scale of exactly 1 m. This is what makes one pixel equal one block. Missing values are -9999 (for elevation and height) so that "no data" is never mistaken for "zero metres".

Next: [3. Looking at the raster](#3-looking-at-the-raster-next).

### Looking at the rasters
Before we start processing the data, let's have a look at our rasters so we know what to expect. The Minecraft world will be downstream of this step, so it's worth making sure the data are free of errors and that the grid is as expected. This repo includes a short diagnostic script which you can run as:

```
python scripts/03_inspect_raster.py
```

It prints a short report and writes two pictures. We will go through what each one tells us.

#### Is the grid as expected?
The report provides checks that the grid is in a metric coordinate system (UTM zone 10N) and that each cell is 1m. Our grid is 1,024 by, 1,024 cells, so our rendered world will represent an area a little over one square kilometer. 

The report also includes a matrix to show which layers in the combined .tif file contain real data:

band            valid %      min      max     mean
dem3dep1m           0.0        -        -        -
dem3dep10m        100.0    209.2    332.5    267.2
canopy_h          100.0      0.0     34.0     12.6
loss_year         100.0      0.0   2023.0   1344.7
treecover2000     100.0      0.0    100.0     81.2

This is mainly useful for checking which DEM to build the world off of. You can see that for our chosen block there is no 1m DEM coverage, so we will use the 10m layer instead. 

Here's an overview of the data layers:

![The four layers of the raster](docs/03_four_layers.png)

*Figure 1. The four layers over the same 1,024 m square.*

- **Elevation**: The block includes a ridge in the upper right, and drops down to a stream valley in the lower left. Minecraft's vertical axis is confined from -64 to 320, or a total of 384 blocks. With 123m of relief plus up to 34m of trees we will have room to spare. But this is a limitation to be aware of: blocks with very steep elevational gradients will get clipped. 

- **Canopy height**: Dark green shows taller forest, while pale green is short grading to no trees. The canopy height map I used stops at 34m, so some of the very tall Douglas fir trees that grow in this part of the world will be clipped as well. 

- **Year of forest loss**: This is the layer that tells us where the forest was cut and when. The colours are years: dark purple for the early 2000s, pink for the 2010s, yellow for about 2022, grey for no cut. Compare it with the canopy panel above. The pink block in the upper left lines up with the bare triangle, which is how the canopy map shows a cut from the 2010s: the replanted trees are still too small for the model to see.

- **Tree cover in 2000**: A baseline from the start of the record. The pale patch in the upper middle was not forested in 2000 and sits in a region that shows no cut afterwards, which suggests it was cleared before the record began and has regrown since. That is my reading from the maps, not something the files state, so treat it as a guess.

If you examine the data closely, you'll notice that there are some spots with predicted harvest yet standing trees per the canopy map. These are simply cases where harvests happened after the aerial imagery underpinning the canopy heights was taken after the harvests occur. We will follow the forest loss map. 


## 4. Turn elevation into blocks

Now that we know the data are usable, it's time to turn it into the thing Minecraft actually needs to build the world: for every column of the grid, the height of the top ground block, as a whole number. This will be the basis for the trees or any other details that we'll add later. 

To convert the DEM into Minecraft's ground layer run:

```
python scripts/04_build_terrain.py
```

### Orient the elevation data in space

We need to tell Minecraft how we want to position the actual elevation measurements within the world's grid. Here's the conventions we'll use:

**One block is one metre.** Each 1 m cell of the raster becomes one column of blocks, so our world will have 1,024 blocks on each side. 

**Rows and columns are already world coordinates.** Raster row `r` becomes world `z = r`, and column `c` becomes world `x = c`. Row 0 is the north edge of the map. Minecraft's z axis also grows toward the south, so a map with north at the top needs no flipping. Writing this down now keeps use from accidentally producing a mirrored world later.

**The lowest ground sits at y = 0.** The world extends down to y = -64, so that leaves 64 blocks of stone below the lowest spot. In code the conversion is one line:

```python
y = np.round(dem - dem.min()).astype(int) + Y_BASE   # Y_BASE = 0
```

### Does it fit?

The ```build_terrain.py``` script includes some checks to make sure the data block will fit within the limits of the game. In our data, ground runs from y = 0 to y = 123. The tallest tree on the canopy layer is 34 m, so even if it stood on the highest ground, its top would be at y = 157, well under the limit of 319.

```
Ground height in blocks: y = 0 to 123 (123 blocks of relief)
Tallest tree top if stood on the highest ground: y = 157 (limit 319)
```

If you choose a landscape that is too steep to fit into the game's constraints, the script will fail with an error. In this workflow, you will have to choose a different area with lower relief instead. 

### Do we need to smooth it?

The DEM export chunk above will use 1m LiDAR data with no smoothing if it's available, and defaults to the 10m product with a simple elevational ramp if not. This is purely to improve the visuals of the world, and therefore assumes that no subsequent analysis will be run on it. On this landscape no additional smoothing was necessary, though you may come to a different conclusion if you test it in other geographies. 

### What whole blocks do to gentle slopes

Minecraft worlds typically have slopes that progress one block at a time, so that you can traverse them without having to jump. It's worth verifying that our world will do the same:

![Shaded relief of the elevation and a cross-section through the middle of the window](docs/04_terrain.png)

*Figure 3. The elevational cross-section over 120 m. The grey line is the elevation in the file and the blue steps are the blocks we will build.*

A slope of about one metre in ten becomes a staircase of flat treads roughly ten blocks wide. Across the whole window the median tread is 9 blocks wide (the middle 80% of treads run from 5 to 19). The script also measures how steep the world feels to walk in:

```
flat (0 blocks)               79.5% of columns
one block (walkable)          20.5% of columns
two or more (needs a jump)     0.0% of columns
```

No column differs from its neighbours by more than one block, so a player can walk the whole world without jumping. 

### What this terrain cannot show

The elevation here comes from the 10 m model, so features smaller than about ten metres are missing: stream banks, cut banks beside roads, etc. If your window has 1 m lidar, the same script picks it up automatically and the terrain will show those details. If your ground is very flat, the whole-block step may erase real relief, and you could scale heights up, for example two blocks per metre. This window does not need it.

The script saves the grid to `out/surface_y.npy`. 
