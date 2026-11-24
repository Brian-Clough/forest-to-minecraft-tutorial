"""Chunk 7: write the terrain, ground blocks and trees into Minecraft region files.

Reads out/surface_y.npy (chunk 4), out/ground.npy (chunk 6) and out/trees.csv (chunk 6). Writes out/world/region/r.X.Z.mca.
The world has no level.dat yet; chunk 8 adds it. One raster cell is one block: column c is world x, row r is world z.

Usage: python scripts/07_write_world.py
"""
import io, struct, time, zlib, pathlib
import numpy as np
import nbtlib
from nbtlib import Compound, Int, Byte, Long, String, List, LongArray

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
REGION_DIR = OUT / "world" / "region"

# The chunk layout below is the one Minecraft has used since 1.18. We stamp the chunks with an older DataVersion
# (1.21, 3953) on purpose: the game upgrades older data when it loads it, so we do not have to match the newest
# field names. Java 26.3 itself is DataVersion 5023 (level.dat in chunk 8 uses that).
CHUNK_DATA_VERSION = 3953
Y_MIN, Y_MAX = -64, 319                     # build limits of the overworld
BIOME = "minecraft:taiga"

AIR, STONE, DIRT, PODZOL, GRASS, COARSE, BEDROCK, LOG, LEAVES = range(9)
BLOCK_STATE = {
    AIR: ("minecraft:air", None), STONE: ("minecraft:stone", None), DIRT: ("minecraft:dirt", None),
    PODZOL: ("minecraft:podzol", None), GRASS: ("minecraft:grass_block", None), COARSE: ("minecraft:coarse_dirt", None),
    BEDROCK: ("minecraft:bedrock", None), LOG: ("minecraft:spruce_log", None),
    LEAVES: ("minecraft:spruce_leaves", {"persistent": "true", "distance": "1"}),    # persistent: placed leaves must not decay
}
SURFACE_BY_CLASS = np.array([PODZOL, GRASS, COARSE], dtype=np.uint8)   # chunk 6: mature, regrowth, recent cut
TOPSOIL_DEPTH = 3                            # dirt blocks under the surface block


def tree_template(h, r):
    """Blocks of one tree relative to its ground column, as (dx, dy, dz, block). Trunk then a cone of leaves."""
    base = max(1, int(round(0.35 * h))); cells = []
    for k in range(base, h + 1):
        rad = int(round(r * (h - k) / max(h - base, 1)))
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if dx * dx + dz * dz <= rad * rad + 0.5:
                    cells.append((dx, k, dz, LEAVES))
    for k in range(1, h):
        cells.append((0, k, 0, LOG))
    return np.array(cells, dtype=np.int32)


def all_tree_blocks(trees):
    """One array of (x, y, z, block) for every block of every tree."""
    templates, parts = {}, []
    for x, z, y, h, r, _ in trees:
        key = (int(h), int(r))
        if key not in templates:
            templates[key] = tree_template(*key)
        t = templates[key]
        parts.append(np.column_stack([t[:, 0] + x, t[:, 1] + y, t[:, 2] + z, t[:, 3]]))
    return np.concatenate(parts)


def section_nbt(blocks16, section_y):
    """One 16x16x16 section; blocks16 has shape (y, z, x) of block codes."""
    codes, inverse = np.unique(blocks16, return_inverse=True)
    palette = List[Compound]()
    for c in codes:
        name, props = BLOCK_STATE[int(c)]
        entry = Compound({"Name": String(name)})
        if props:
            entry["Properties"] = Compound({k: String(v) for k, v in props.items()})
        palette.append(entry)
    block_states = Compound({"palette": palette})
    if len(codes) > 1:                          # a one-block section stores no data array
        bits = max(4, int(len(codes) - 1).bit_length())
        per_long = 64 // bits                   # entries never cross from one long to the next
        idx = inverse.reshape(-1).astype(np.uint64)
        pad = (-len(idx)) % per_long
        idx = np.concatenate([idx, np.zeros(pad, dtype=np.uint64)]).reshape(-1, per_long)
        shifts = (np.arange(per_long, dtype=np.uint64) * np.uint64(bits))
        packed = np.bitwise_or.reduce(idx << shifts, axis=1)
        block_states["data"] = LongArray(packed.view(np.int64))
    return Compound({"Y": Byte(section_y), "block_states": block_states,
                     "biomes": Compound({"palette": List[String]([String(BIOME)])})})


def chunk_nbt(cx, cz, blocks):
    """blocks has shape (384, 16, 16), index [y - Y_MIN, z, x]."""
    sections = List[Compound]()
    for s in range((Y_MAX - Y_MIN + 1) // 16):
        sections.append(section_nbt(blocks[s * 16:(s + 1) * 16], s + Y_MIN // 16))
    root = Compound({
        "DataVersion": Int(CHUNK_DATA_VERSION), "xPos": Int(cx), "yPos": Int(Y_MIN // 16), "zPos": Int(cz),
        "Status": String("minecraft:full"), "LastUpdate": Long(0), "InhabitedTime": Long(0), "isLightOn": Byte(0),
        "sections": sections, "block_entities": List[Compound](),
        "structures": Compound({"starts": Compound(), "References": Compound()}),
    })
    buf = io.BytesIO()
    nbtlib.File(root, gzipped=False, root_name="").write(buf)
    return buf.getvalue()


def write_region(path, chunks):
    """chunks maps (local x, local z) in 0..31 to raw chunk NBT. Region file: 8 KiB header, then 4 KiB sectors."""
    locations, timestamps, body = bytearray(4096), bytearray(4096), bytearray()
    sector, now = 2, int(time.time())
    for (lx, lz), raw in chunks.items():
        payload = zlib.compress(raw)
        record = struct.pack(">IB", len(payload) + 1, 2) + payload          # compression type 2 = zlib
        record += b"\0" * (-len(record) % 4096)
        n = len(record) // 4096
        i = 4 * (lx + 32 * lz)
        locations[i:i + 4] = struct.pack(">I", (sector << 8) | n)
        timestamps[i:i + 4] = struct.pack(">I", now)
        body += record; sector += n
    path.write_bytes(bytes(locations) + bytes(timestamps) + bytes(body))


def main():
    t0 = time.time()
    surface = np.load(OUT / "surface_y.npy").astype(np.int32)
    cls = np.load(OUT / "ground.npy")
    trees = np.loadtxt(OUT / "trees.csv", delimiter=",", skiprows=1, dtype=np.int64)
    h, w = surface.shape
    assert h % 16 == 0 and w % 16 == 0, "the window must be a whole number of chunks"
    assert surface.min() >= 0 and surface.max() + trees[:, 3].max() <= Y_MAX, "terrain and trees must fit the build limits"
    tb = all_tree_blocks(trees)
    tb = tb[(tb[:, 0] >= 0) & (tb[:, 0] < w) & (tb[:, 2] >= 0) & (tb[:, 2] < h) & (tb[:, 1] <= Y_MAX)]
    ckey = (tb[:, 0] >> 4) * 1000 + (tb[:, 2] >> 4)
    order = np.argsort(ckey, kind="stable"); tb, ckey = tb[order], ckey[order]
    starts = np.searchsorted(ckey, np.unique(ckey)); chunk_slice = dict(zip(np.unique(ckey), zip(starts, list(starts[1:]) + [len(tb)])))
    print(f"{len(trees):,} trees, {len(tb):,} tree blocks")

    yy = (np.arange(Y_MIN, Y_MAX + 1, dtype=np.int32))[:, None, None]
    REGION_DIR.mkdir(parents=True, exist_ok=True)
    counts = dict(chunks=0)
    for rz in range(0, h // 512 + (h % 512 > 0)):
        for rx in range(0, w // 512 + (w % 512 > 0)):
            chunks = {}
            for lz in range(32):
                for lx in range(32):
                    cx, cz = rx * 32 + lx, rz * 32 + lz
                    if cx * 16 >= w or cz * 16 >= h:
                        continue
                    sl = (slice(cz * 16, cz * 16 + 16), slice(cx * 16, cx * 16 + 16))
                    g = surface[sl][None]; top = SURFACE_BY_CLASS[cls[sl]][None]
                    B = np.where(yy < g - TOPSOIL_DEPTH, STONE, np.where(yy < g, DIRT, np.where(yy == g, top, AIR))).astype(np.uint8)
                    B[0] = BEDROCK
                    got = chunk_slice.get(cx * 1000 + cz)
                    if got:
                        rows = tb[got[0]:got[1]]
                        for code in (LEAVES, LOG):                                       # leaves first, so a trunk always wins
                            r = rows[rows[:, 3] == code]
                            xi, yi, zi = r[:, 0] & 15, r[:, 1] - Y_MIN, r[:, 2] & 15
                            free = (B[yi, zi, xi] == AIR) | (B[yi, zi, xi] == LEAVES)    # never overwrite the ground
                            B[yi[free], zi[free], xi[free]] = code
                    chunks[(lx, lz)] = chunk_nbt(cx, cz, B); counts["chunks"] += 1
            if chunks:
                write_region(REGION_DIR / f"r.{rx}.{rz}.mca", chunks)
                print(f"wrote r.{rx}.{rz}.mca ({len(chunks)} chunks), {time.time() - t0:.0f} s")
    print(f"Done: {counts['chunks']} chunks in {REGION_DIR}")


if __name__ == "__main__":
    main()
