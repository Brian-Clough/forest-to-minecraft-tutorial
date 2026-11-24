"""Chunk 9: check the world files against the inputs, before you open them in Minecraft.

Reads every chunk back from out/world/.../region/*.mca with its own decoder (it shares no code with chunk 7) and checks:
  - all 4,096 chunks are present, with the right position and status
  - every column: bedrock at the bottom, stone, three blocks of dirt, then the surface block for its stand class,
    nothing but air, trunks and leaves above it, and no air below it
  - every tree: its whole trunk is there, from the block above the ground to one below the tip
  - the world holds exactly as many log blocks as the trees table says
Writes docs/09_check.txt and exits with status 1 if anything fails.

Usage: python scripts/09_check_world.py [path/to/region/folder]
"""
import io, struct, sys, zlib, pathlib
import numpy as np
import nbtlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT, DOCS = ROOT / "out", ROOT / "docs"
REGION = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "world" / "dimensions" / "minecraft" / "overworld" / "region"
Y_MIN, N_SECTIONS = -64, 24

NAMES = {"minecraft:air": 0, "minecraft:stone": 1, "minecraft:dirt": 2, "minecraft:podzol": 3, "minecraft:grass_block": 4,
         "minecraft:coarse_dirt": 5, "minecraft:bedrock": 6, "minecraft:spruce_log": 7, "minecraft:spruce_leaves": 8}
AIR, STONE, DIRT, BEDROCK, LOG, LEAVES, OTHER = 0, 1, 2, 6, 7, 8, 99
SURFACE_BY_CLASS = np.array([3, 4, 5])          # stand class 0 mature, 1 regrowth, 2 recent cut -> podzol, grass, coarse dirt


def read_chunk(data, lx, lz):
    """Return the parsed chunk NBT, or None if the region file has no chunk there."""
    i = 4 * (lx + 32 * lz)
    loc = struct.unpack(">I", data[i:i + 4])[0]
    offset, count = loc >> 8, loc & 255
    if offset < 2 or count == 0:
        return None
    length, compression = struct.unpack(">IB", data[offset * 4096:offset * 4096 + 5])
    assert compression == 2, f"unexpected compression type {compression}"
    raw = zlib.decompress(data[offset * 4096 + 5:offset * 4096 + 4 + length])
    return nbtlib.File.parse(io.BytesIO(raw))


def decode_blocks(chunk):
    """Block codes with shape (384, 16, 16), indexed [y - Y_MIN, z, x]."""
    out = np.full((N_SECTIONS * 16, 16, 16), AIR, dtype=np.uint8)
    for sec in chunk["sections"]:
        y0 = (int(sec["Y"]) - Y_MIN // 16) * 16
        bs = sec["block_states"]
        palette = np.array([NAMES.get(str(e["Name"]), OTHER) for e in bs["palette"]], dtype=np.uint8)
        if "data" not in bs:
            out[y0:y0 + 16] = palette[0]
            continue
        bits = max(4, (len(palette) - 1).bit_length())
        per_long = 64 // bits                                   # entries never cross from one long to the next
        longs = np.array(bs["data"], dtype=np.int64).view(np.uint64)
        idx = (longs[:, None] >> (np.arange(per_long, dtype=np.uint64) * np.uint64(bits))) & np.uint64((1 << bits) - 1)
        out[y0:y0 + 16] = palette[idx.reshape(-1)[:4096].astype(np.int64)].reshape(16, 16, 16)
    return out


def main():
    surface = np.load(OUT / "surface_y.npy").astype(int)
    cls = np.load(OUT / "ground.npy")
    trees = np.loadtxt(OUT / "trees.csv", delimiter=",", skiprows=1, dtype=int)
    h, w = surface.shape
    lines, failures = [], []
    say = lambda s="": (print(s), lines.append(s))
    def fail(msg):
        failures.append(msg)
        if len(failures) <= 20:
            say("FAIL " + msg)

    by_chunk = {}
    for t in trees:
        by_chunk.setdefault((t[0] // 16, t[1] // 16), []).append(t)

    expected_chunks = (h // 16) * (w // 16)
    seen = 0; logs_found = 0; leaves_found = 0; bad_columns = 0; bad_trees = 0; versions = set()
    yy = np.arange(N_SECTIONS * 16)[:, None, None]
    for rx in range(w // 512):
        for rz in range(h // 512):
            path = REGION / f"r.{rx}.{rz}.mca"
            if not path.exists():
                fail(f"missing region file {path.name}"); continue
            data = path.read_bytes()
            for lz in range(32):
                for lx in range(32):
                    cx, cz = rx * 32 + lx, rz * 32 + lz
                    ch = read_chunk(data, lx, lz)
                    if ch is None:
                        fail(f"chunk {cx},{cz} is missing"); continue
                    seen += 1; versions.add(int(ch["DataVersion"]))
                    if int(ch["xPos"]) != cx or int(ch["zPos"]) != cz:
                        fail(f"chunk at slot {cx},{cz} says it is {int(ch['xPos'])},{int(ch['zPos'])}")
                    if str(ch["Status"]) != "minecraft:full":
                        fail(f"chunk {cx},{cz} status is {ch['Status']}")
                    B = decode_blocks(ch)
                    sl = (slice(cz * 16, cz * 16 + 16), slice(cx * 16, cx * 16 + 16))
                    gy = (surface[sl] - Y_MIN)[None]
                    top = np.take_along_axis(B, gy, 0)[0]
                    ok = top == SURFACE_BY_CLASS[cls[sl]]
                    for d in (1, 2, 3):
                        ok &= np.take_along_axis(B, gy - d, 0)[0] == DIRT
                    ok &= np.take_along_axis(B, gy - 4, 0)[0] == STONE
                    ok &= B[0] == BEDROCK
                    ok &= ~((B == AIR) & (yy <= gy)).any(axis=0)                    # no air at or below the surface
                    ok &= ~((yy > gy) & ~np.isin(B, (AIR, LOG, LEAVES))).any(axis=0)  # only air, logs and leaves above it
                    bad_columns += int((~ok).sum())
                    if not ok.all():
                        z, x = np.argwhere(~ok)[0]
                        fail(f"column x={cx * 16 + x}, z={cz * 16 + z} in chunk {cx},{cz} has the wrong blocks")
                    logs_found += int((B == LOG).sum()); leaves_found += int((B == LEAVES).sum())
                    for x, z, y, th, r, _ in by_chunk.get((cx, cz), []):
                        trunk = B[y - Y_MIN + 1:y - Y_MIN + th, z % 16, x % 16]
                        if len(trunk) != th - 1 or not (trunk == LOG).all():
                            bad_trees += 1
                            fail(f"tree at x={x}, z={z} (height {th}) is missing part of its trunk")

    expected_logs = int((trees[:, 3] - 1).sum())
    say()
    say(f"Chunks found: {seen} of {expected_chunks}. DataVersion in the chunks: {sorted(versions)}.")
    say(f"Columns with the wrong blocks: {bad_columns} of {h * w:,}.")
    say(f"Trees: {len(trees):,} in the table, {bad_trees} with a missing trunk block.")
    say(f"Log blocks: {logs_found:,} in the world, {expected_logs:,} expected from the trees table.")
    say(f"Leaf blocks: {leaves_found:,} in the world (not checked exactly, because crowns overlap and stop at hillsides).")
    if logs_found != expected_logs:
        fail("the number of log blocks does not match the trees table")
    if seen != expected_chunks:
        fail("the number of chunks is wrong")
    say()
    say("PASS" if not failures else f"FAIL: {len(failures)} problem(s)")
    DOCS.mkdir(exist_ok=True)
    (DOCS / "09_check.txt").write_text("\n".join(lines) + "\n")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
