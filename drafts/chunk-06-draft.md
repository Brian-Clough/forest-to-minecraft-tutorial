# Draft: Chunk 6, treat each stand by its age

*First-pass tutorial prose for you to revise. Paths are relative to the repo root. Script: `scripts/06_stands_and_ground.py`. Numbers: `docs/06_summary.txt`. Run chunks 4 and 5 first, because this script reads `out/surface_y.npy`. It rewrites `out/trees.csv`, so chunk 5's output is replaced.*

---

## 6. Treat each stand by its age

Chunk 5 treated every patch of forest the same way. A forest is not like that. Our window holds old uncut forest, two stands that grew back after earlier cuts, and ground that was cut after the canopy imagery was taken. Each looks different in Minecraft, and each needs its own trees and its own ground block.

```
python scripts/06_stands_and_ground.py
```

### Sort the window into three classes

The forest-loss layer gives the year each cell was cut. The canopy imagery is from about 2019. That gives three classes:

| Class | Rule | Ground block |
|---|---|---|
| Mature | never cut in the loss record | podzol |
| Regrowth | cut in 2019 or earlier | grass block |
| Recent cut | cut after 2019 | coarse dirt |

The ground blocks are a choice, not a measurement. Podzol is the dark forest floor under conifers in Minecraft, grass suits young regrowth, and coarse dirt reads as bare disturbed soil. The script saves the class of every column in `out/ground.npy`. Chunk 7 turns the classes into blocks.

![Stand classes, the regrowth height rule, and two side views](docs/06_stands.png)

*Figure 5. Top left: the three classes. Top right: how tall regrowth is, by age. Bottom: side views across stand boundaries along one row.*

### Give regrowth a height and a density

Regrowth needs two numbers, and the canopy map supplies only part of the answer. Where the map shows a tree 3 m or taller, we use that height. Where it shows nothing, we still know the stand's age, so we use a growth curve.

The two regrowth stands show why we need it. The stand cut in 2003 was 16 years old in 2019, and the canopy map gives a median height of 10 m. The stand cut in 2013 was 6 years old, and the canopy map shows almost nothing, since only 1% of its cells reach 3 m. The model cannot see trees that small, but they are there.

The growth curve in the top-right panel passes through the 2003 point and is shaped so that a 6-year-old stand comes out at 2.8 m, just under what the map can see.

```python
height = 10.0 * (age / 16) ** 1.3
```

Young stands are also crowded. We give each stand a number of stems per hectare that falls with age: 1,100 at age 5, 600 at age 20, 400 at age 40, and 280 in uncut forest. The script lays down a candidate tree in every 3 m square, then keeps a random share of them to match the stand's density.

### Check it

```
stand          area %  trees/ha  median h    ground block
mature           33.2       271        15          podzol
cut 2003         17.7       714        10     grass_block
cut 2013         20.3      1060         3     grass_block
cut 2021          1.5         0         -     coarse_dirt
cut 2022         26.7         0         -     coarse_dirt
```

The window now holds 45,848 trees, about 437 per hectare. Chunk 7 builds the blocks: about 1.6 million of trunk and leaves, mostly leaves.

In the side views, the 2013 stand is a thicket of 3-block saplings next to old trees 20 to 30 blocks tall. In the right-hand view, the 2022 clearcut meets the 2003 stand, whose trees are about 10 blocks tall.

### Be honest about what is guessed

The one measured thing here is the 2003 point on the growth curve. The exponent, the stem densities and the ground blocks are our assumptions. The densities are typical for conifer regrowth, but they are not taken from a survey of this site. If you know a local source, replace the numbers in the `DENSITY_BY_AGE` table at the top of the script and rerun.

---

## Notes for you (not for publication)

- **Densities are my assumptions, not sourced.** I did not look up a reference for the stem counts, so cite one or soften the sentence before publishing. They are one table at the top of the script.
- **The growth curve rests on one data point.** The exponent 1.3 was picked to put age 6 under 3 m. It is a plausible shape, not a fitted one.
- **Other loss years exist but are small** (2002, 2012, 2014, 2018 under regrowth; 2023 under recent cut, each under 0.5% of the window). They follow the same rules by age, and the table lists only cohorts above 0.5%.
- **No stumps, shrubs or slash on the recent cuts.** Coarse dirt alone looks bare. Adding scattered stumps is an easy extension and a possible exercise.
- **Not tested in Minecraft.** Chunk 7 builds the real blocks, so the block total comes from there.
- **The side views** are one row (640), chosen by scanning the loss map for stand boundaries. The 2003 and 2013 stands never meet along a row in this window, so they are in separate panels.
- **Chunk 5's numbers are superseded.** If you keep the chunk 5 section as a stepping stone, say that chunk 6 replaces its tree table.
