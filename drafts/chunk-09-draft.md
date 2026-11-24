# Draft: Chunk 9, check the world before you open it

*First-pass tutorial prose for you to revise. Script: `scripts/09_check_world.py`. Output: `docs/09_check.txt`. It reads `out/world/` and the three input files (`out/surface_y.npy`, `out/ground.npy`, `out/trees.csv`), takes about 6 seconds, and needs no Minecraft.*

---

## 9. Check the world

Opening the game tells you whether a world loads. It does not tell you whether the world is right. A tree can be missing its top, a hillside can have the wrong surface block, and none of that shows until someone walks past. This chunk gives a check you can run before you open anything, and again whenever you change a script.

```
python scripts/09_check_world.py
```

### What it checks

The script reads every chunk back out of the region files and compares it with the three tables that produced it. It does not reuse any code from chunk 7. That matters, because a check that shares the writer's code can share its mistakes. It decodes the files straight from the format described in chunk 7.

It checks four things:

| Check | What counts as passing |
|---|---|
| Chunks | all 4,096 are there, each in the right place, each marked complete |
| Every column | bedrock at the bottom, then stone, then 3 blocks of dirt, then the surface block for its stand class, with no air underground and only air, trunks and leaves above it |
| Every tree | the whole trunk is there, from the block above the ground up to the one below the tip |
| Logs | the world holds exactly as many log blocks as the trees table implies |

It does not check the leaves exactly. Neighbouring crowns overlap, and a crown stops where a hillside starts, so the number of leaf blocks cannot be predicted from the table alone. It reports the count and leaves it at that.

### Read the result

```
Chunks found: 4096 of 4096. DataVersion in the chunks: [3953].
Columns with the wrong blocks: 0 of 1,048,576.
Trees: 45,848 in the table, 0 with a missing trunk block.
Log blocks: 313,709 in the world, 313,709 expected from the trees table.
Leaf blocks: 811,027 in the world (not checked exactly, ...).

PASS
```

If anything fails, the script prints the first 20 problems, each with the block position, then ends with `FAIL`. It also exits with an error status, so you can use it in an automated check.

### Make sure the check can fail

A check that can only pass proves nothing. To see that this one has teeth, change an input and run it again. For example, make one tree in `out/trees.csv` five blocks taller, or change one value in `out/ground.npy`, without rewriting the world. The script should name the tree or the column that no longer matches. Put the input back and rerun chunk 7 when you are done.

### What this does not tell you

The check shows that the files hold what the tables say. It does not show that the tables look like a forest. Chunk 10 deals with that, and so does walking around in the game.

---

## Notes for you (not for publication)

- **Tested against altered inputs.** I changed one stand class patch (100 columns), raised one surface column by two blocks, and made one tree five blocks taller. The script reported 101 bad columns, one missing trunk and a log-count mismatch, and exited with status 1. So I know it can fail on those cases. It has not been tested against a damaged region file, such as a truncated chunk.
- **Exact leaf check left out.** An exact check would mean repeating chunk 7's placement rules, which would make it share the writer's logic, the thing the script is built to avoid.
- **Speed.** It takes about 6 seconds here. It decodes every block of every chunk with numpy, so a much larger window will take proportionally longer.
- **It checks the files, not the game.** The world already opened in Minecraft 26.3 when you tried it, so the two together cover "right content" and "loads".
- **DataVersion** shows 3953, the older version chunk 7 stamps. The line is there so a reader who changes `CHUNK_DATA_VERSION` can see the change took effect.
