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
