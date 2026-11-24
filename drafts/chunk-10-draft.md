# Draft: Chunk 10, know what you built

*First-pass tutorial prose for you to revise. This chunk has no script. Run times and sizes below were measured on the 1,024 × 1,024 example window in a cloud container (about 1 CPU); anything marked "estimate" was not measured.*

---

## 10. Know what you built

The world opens, the files check out, and the trees look like a forest. Before you use it for anything, you should know what it is and what it is not. It is a picture of four public datasets, drawn at one block per metre. It is not a forest inventory, and the gaps between the datasets and the world are the useful part to understand.

### What each piece is, and what it assumes

| Part of the world | Where it comes from | What to keep in mind |
|---|---|---|
| Ground shape | USGS 10 m elevation, because the 1 m lidar layer was empty over this window | Terraces about 9 blocks wide (median), because 10 m data is rounded to whole blocks. Lidar would give finer steps. |
| Tree heights | A canopy height model estimated from satellite photographs taken around 2018 to 2020 | An estimate, not a lidar measurement. Heights stop at about 34 m in this window. |
| Which ground was cut, and when | Hansen forest-loss map at about 28 m | Small cuts are missed, edges are blocky, and a few trees leak across the edge of the 2013 cut. |
| Tree positions | One random candidate per 3 m square, thinned to a density per stand | The positions are random, not surveyed. No real tree is at any of these spots. |
| Regrowth heights and stem counts | A growth curve through one measured point, and assumed densities | These are the weakest numbers in the world. See chunk 6. |
| Species | Every tree is a spruce | A placeholder. The data does not tell us the species. |
| Ground blocks | Three choices by stand class | Podzol, grass and coarse dirt are looks, not soil measurements. |
| What is missing | Understory, stumps, fallen logs, dead standing trees, streams, roads | None of these are in the datasets we used. |

The world is also frozen in time: the trees are as the imagery saw them around 2019, and the cuts run up to 2023.

### What it is good for

It is good for seeing the shape of the stands, the sizes of the cuts, and how the ground rises under them. It is a way to explain a map to someone who does not read maps, and a test bed for software that needs a believable forest, such as an ecology simulation.

It is not good for counting trees, estimating carbon, or checking a model against the ground. The tree positions are invented and the regrowth numbers are assumed. If you want to compare against a real plot, use the datasets themselves.

### How big can the window be

On the example window, each step is quick:

| Step | Time | Output |
|---|---|---|
| chunk 4, terrain | about 1 s | `surface_y.npy` |
| chunk 6, stands and trees | about 1 s | `trees.csv`, 45,848 trees |
| chunk 7, write the world | about 10 s | 17 MB of region files, 3 MB zipped |
| chunk 9, check | about 5 s | pass or fail |

Peak memory was about 300 MB. The input raster is 2.6 MB.

A window four times as wide, 4,096 blocks on a side, has 16 times the area. Treat these as estimates, not measurements: the scripts should take a few minutes and the world should be roughly 270 MB, but chunk 7 builds a list of every tree block in memory at once, so memory is likely to grow to a few gigabytes. Past that, you would change chunk 7 to build the trees one region at a time. Also check the limits on the other side. A tall hill plus a tall tree must still fit under y = 319, and chunk 4 stops with an error if it does not.

### Use your own site

The scripts are written for one window, and these are the things to change:

| What | Where |
|---|---|
| The area and the exported layers | the Earth Engine script from chunk 2 |
| The year of the canopy imagery | `IMAGERY_YEAR` in chunks 5 and 6 |
| The stem density and growth curve for your forest type | the constants at the top of `06_stands_and_ground.py` |
| The trees' look and the biome | `tree_template` and `BIOME` in `07_write_world.py` |
| The coordinate system | check the export is in a UTM zone that fits your site, because one cell must be one metre |

Re-run the checks after every change. Chunk 9 compares the finished world with your tables, so it tells you if a change broke the writer.

### Licences and credit

Three of the datasets are free to use with credit, and the loss and canopy layers require it. If you share the world files or a screenshot, say where the data came from. `data/SOURCES.md` lists each layer, its licence and the credit line to use.

### Where it goes wrong

These came up while building the example, so they are worth knowing before you hit them:

- **The world looks like the old version after you change a script.** Minecraft rewrites region files when it saves, so a file copied in while the game was running is overwritten. Quit the game completely before copying. If you move files between computers, compare `tail -c +8193 <file> | shasum` on both, and do it before the game has opened the world, because the game changes the files when it saves.
- **You start underground.** The new world's spawn is at flat ground level, so type the `/tp` command from chunk 8.
- **The commands are refused.** Turn on Allow Commands (cheats) when you create the world.
- **The world is plain flat land.** The region files are not in `dimensions/minecraft/overworld/region/`, or the game ignored them. Check the folder layout against your game version.
- **Chunk 9 says FAIL.** The message gives the block position of the first problems. Re-run chunk 7, and if it still fails, the cause is in your edit to the tables or to `07_write_world.py`.

### Ideas to try next

- Add stumps and slash to the recent cuts, so the coarse dirt does not look bare.
- Give each stand its own species mix, with different log and leaf blocks.
- Add an understory of ferns or shrubs under the older stands.
- Add standing dead trees, as bare logs with no leaves.
- Replace the assumed densities with plot data from your own site.
- Smooth the terraces, or use the 1 m lidar if your site has it.

---

## Notes for you (not for publication)

- **Measured vs. estimated.** The run times, the 300 MB peak memory, and the 17 MB and 3 MB file sizes are measured. The 4,096-block estimates (a few minutes, about 270 MB, a few gigabytes of memory) are my arithmetic and have not been run. Either run it once or keep the "estimate" wording.
- **Hansen licence line.** I wrote that the loss and canopy layers require credit, based on `data/SOURCES.md` (both CC BY 4.0). The USGS layers ask for attribution. Check the wording against that file before you publish.
- **Chunk 2's script name.** I called it "the Earth Engine script from chunk 2". Use the real filename once the final script is committed.
- **Troubleshooting list.** This is the list of real problems we hit. You may prefer to fold it into chunk 8 or keep it here as a quick reference.
- **Ideas list.** None of these is built or tested. I would not promise any of them as an exercise unless you try one first.
- **No claim about accuracy.** I deliberately did not say how close the world is to the real forest. We have no field data to test it against, so the draft says only that it cannot be used to test a model.
