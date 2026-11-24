# Draft: Chunk 5, decide where the trees go

*First-pass tutorial prose for you to revise. Paths are relative to the repo root. Script: `scripts/05_place_trees.py`. Numbers: `docs/05_summary.txt`. Run chunk 4 first, because this script reads `out/surface_y.npy`.*

---

## 5. Decide where the trees go

We now have ground. The next question is what stands on it. A tree in Minecraft is just blocks, but before we make any blocks we need a list: for each tree, where it is, how tall, and how wide its crown is. Keeping this as a plain table has a practical benefit. You can check it, count it and plot it before a single block is written, and chunk 7 can turn the table into blocks in one pass.

```
python scripts/05_place_trees.py
```

### First, fix the canopy map

In chunk 3 we saw that the canopy layer and the forest-loss layer are from different dates. The canopy map comes from imagery taken around 2018 to 2020, so any ground cut afterwards still shows tall trees. If we placed trees straight from this map, we would plant a forest in a clearcut.

The script removes them with one rule: wherever the loss year is later than 2019, the canopy is set to zero.

```python
out[loss > IMAGERY_YEAR] = 0.0
```

Cuts made before 2019 need no correction, because the imagery already shows them: the cut from 2013 is bare in the canopy map, and the cut from 2003 shows young trees.

![The canopy map before and after correction, and a side view across a stand boundary](docs/05_trees.png)

*Figure 4. Top: canopy height in the file (left) and after removing the cuts made after 2019 (right). Bottom: a side view of the trees within 3 m of one row of the window, crossing from standing forest into the 2022 cut. The yellow dots mark the cut.*

In the top row, the bright triangle that appears on the right is the 2022 cut, with the blocky edge of the loss map. Overall, 28.2% of the window was cut after 2019, and the mean canopy height drops from 12.6 m to 6.6 m.

### Place one tree per square

The placement rule is deliberately simple. Divide the window into 6 m squares. In each square pick one random point. If the canopy at that point is 3 m or taller, put a tree there with that height. Below 3 m we treat the vegetation as shrubs or seedlings and draw nothing. Fix the random seed, so that anyone who reruns the script gets the same forest.

Each tree has a crown whose half-width is about a ninth of its height, between 1 and 4 blocks. The crown is a cone that starts a third of the way up the trunk and narrows to a point at the top. The script writes one row per tree to `out/trees.csv`: position, ground height, tree height, crown radius and loss year.

The result for this window:

```
Trees placed: 14,252 (136 per hectare over the whole window), one candidate per 6 m square.
Height of placed trees: median 13 blocks, 90th percentile 20, tallest 33.
```

### Check it against the stands

The most useful check is by cohort, because it tests the correction directly.

```
loss year    area %  trees/ha  median h
none           33.2       264        15
2003           17.7       264        10
2013           20.3         2        10
2021            1.5         0         -
2022           26.7         0         -
```

The 2021 and 2022 cuts have no trees, which is what we wanted. The uncut forest and the 2003 stand both come out at about 264 trees per hectare, which is the density the grid gives wherever the canopy is tall enough. The 2013 cut has two trees per hectare. The loss map is blocky, so a few trees from neighbouring stands leak across its edges.

### Be honest about what this is

This is a picture of the map, not a forest inventory. Every stand gets the same one-tree-per-square treatment, so the numbers above tell us about the grid, not the forest. Real young stands are typically much denser than old ones, so the 2003 stand is too sparse here. The 2013 stand, bare because its trees are too small for the canopy model to see, should really be a thicket of saplings, and the script draws nothing there. Chunk 6 gives each stand its own treatment, using its age.

In total the table describes about 0.7 million blocks of trunk and leaves, under one block per ground column on average. That is a light load for Minecraft.

---

## Notes for you (not for publication)

- **Reordering.** My original outline had trees in chunk 5 and the stand-age correction in chunk 6. The correction has to come first or the trees are wrong, so the minimal version (cuts after 2019 become bare) now sits here. Chunk 6 then handles ground cover and young stands, using age. If you prefer the original order, move the "fix the canopy map" section to chunk 6 and let chunk 5 place trees from the raw canopy.
- **The 2019 cutoff** is my reading of "imagery around 2018 to 2020". It is a constant at the top of the script. A cut in 2020 is treated as already visible, which may be wrong for a few cells.
- **Crown shape** is a plain cone. Real Douglas-fir crowns are narrower and layered. A reader who wants more realism could vary shape by height or add randomness.
- **Not yet tested:** nothing here has been placed into Minecraft. The block count comes from a rough count of the cone and trunk, not from a built world, and may differ slightly once chunk 7 rounds the crown to a grid.
- **The side-view figure** is a 6 m deep slice across one row, chosen by search because it crosses from forest into the cut. It is an illustration, not a typical row.
