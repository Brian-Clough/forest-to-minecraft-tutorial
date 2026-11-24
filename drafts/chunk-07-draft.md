# Draft: Chunk 7, write the world

*First-pass tutorial prose for you to revise. Script: `scripts/07_write_world.py`. It reads `out/surface_y.npy` (chunk 4), `out/ground.npy` and `out/trees.csv` (both chunk 6), so run chunks 4 to 6 first. It takes about 15 seconds and writes `out/world/dimensions/minecraft/overworld/region/`, about 17 MB.*

---

## 7. Write the world

Everything so far has been a table or a raster. This chunk turns them into blocks and saves them in the file format Minecraft reads. The world will not open yet, because it still lacks its `level.dat` file. Chunk 8 adds that.

```
python scripts/07_write_world.py
```

### How Minecraft stores a world

Minecraft stores terrain in **region files**, one per 512 × 512 block square. Our window is 1,024 × 1,024 blocks, so it needs four: `r.0.0.mca`, `r.1.0.mca`, `r.0.1.mca` and `r.1.1.mca`.

Since Java 26.1 the overworld's region files live inside the world folder at `dimensions/minecraft/overworld/region/`. Before 26.1 they sat directly in `world/region/`, and most older tutorials still show that layout. The script writes the new one.

A region file holds 32 × 32 **chunks**, and each chunk is a 16 × 16 column of blocks that is 384 blocks tall (y from -64 to 319). A chunk is split into 24 **sections**, each 16 blocks tall.

Each section lists the kinds of block it contains, its **palette**, and then gives one palette number for every block. A section that is all air needs only a one-entry palette and no block list at all. The block numbers are packed into 64-bit integers, using as few bits per block as the palette allows (never fewer than 4), and one number never straddles two integers.

The `nbtlib` package writes the chunk data (the format is called NBT), and the script adds the region-file wrapper itself: a header of chunk locations, then the chunks, each compressed with zlib and padded to 4,096 bytes.

### Build one chunk

For each chunk, the script fills the ground column by column from the surface height we computed in chunk 4:

| Depth | Block |
|---|---|
| y = -64 | bedrock |
| down to 4 blocks below the surface | stone |
| the 3 blocks under the surface | dirt |
| the surface block | podzol, grass block or coarse dirt, by the stand class from chunk 6 |

Then it adds the trees. Each tree is a spruce trunk with a cone of spruce leaves, using the tree's height and crown radius from `out/trees.csv`. A tree is just a template, a list of block offsets from its base, and there are fewer than a hundred distinct templates, so the script builds each one once and stamps it out.

Two details matter. Leaves are written with `persistent: true`, because leaves that nothing attached them to would otherwise decay and vanish within minutes. And a tree never overwrites ground: a crown that leans over a slope stops where the hillside starts, and a trunk always wins over a neighbour's leaves.

### Use an older data version on purpose

Every chunk carries a `DataVersion` number. Java 26.3 is 5023. The script stamps chunks with 3953 (Minecraft 1.21) instead, and the game upgrades them when it loads each chunk. The reason is that the chunk layout has kept the same shape since version 1.18, but the newest versions have renamed some fields, and an old version number is the safe way to avoid guessing the new names. If you would rather write the newest version directly, `CHUNK_DATA_VERSION` is a constant at the top of the script.

### Check what was written

The script's own output only says that chunks were written. To check the content, we read some back with a separate piece of code that decodes the files straight from the format description:

```
columns checked: 6400, wrong: 0
tallest tree: 31 trunk blocks (expected 31), a leaf at the tip
```

That is 25 random chunks, with every column's surface block, soil layers, bedrock and above-ground blocks matching the inputs. This is a check of the file, not of the game. Whether Minecraft accepts the files is something only opening the world can tell us, which chunk 10 does.

---

## Notes for you (not for publication)

- **Not tested in Minecraft.** I cannot run the game here. I verified the files with an independent decoder that I wrote from the format description (25 random chunks, all 6,400 columns correct), but a real server or client may still object. Expect one round of fixes after you first open it.
- **The DataVersion choice is a bet.** I could not confirm 26.3's exact chunk field names. The snapshot notes mention a Block State rename (`Name` to `id`, `Properties` to `properties`) but say only that it is a data pack change. An older stamp makes the game's upgrade code do the translation. If the game logs "upgrading" warnings or the blocks look wrong, that is the first thing to revisit.
- **Chunk 8 should use DataVersion 5023** in `level.dat`, since that file describes the game version, while the chunks carry their own.
- **No light or heightmap data is written.** The game computes both when it loads a chunk (`isLightOn` is 0). Expect a slow first load.
- **Tree total is 1,466,770 blocks** (313,709 logs, 1,153,061 leaves, before overlaps). Chunk 6's earlier estimate of 1.1 million was rough, so I changed that line in its draft to "about 1.5 million".
- **Outside the window the world is empty.** The game generates new terrain beyond the 1,024-block edge, according to the world type in `server.properties`. Chunk 8 and chunk 10 deal with that.
- **Biome** is `minecraft:taiga` for the whole window. It sets the grass and leaf colours. A reader in a different forest type should change `BIOME`.
