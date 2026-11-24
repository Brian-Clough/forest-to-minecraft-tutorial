"""Chunk 8: put the world into a server folder Paper can start, with the settings it needs.

Copies out/world (chunk 7) to out/server/world and writes out/server/server.properties. It does NOT write level.dat or
eula.txt: the server creates level.dat itself on its first start, and you accept the EULA yourself. Prints the command that
sets the spawn point.

Usage: python scripts/08_make_server_folder.py
"""
import shutil, sys, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
WORLD_SRC = OUT / "world"
SERVER = OUT / "server"
REGION = pathlib.Path("dimensions") / "minecraft" / "overworld" / "region"      # Java 26.1 and later

PROPERTIES = """\
# Settings for the forest-to-minecraft tutorial world. The server fills in every other setting with its default.
level-name=world
level-type=minecraft\\:flat
generate-structures=false
spawn-monsters=false
spawn-animals=false
gamemode=creative
force-gamemode=true
allow-flight=true
spawn-protection=0
motd=Forest to Minecraft tutorial world
"""


def main():
    regions = sorted((WORLD_SRC / REGION).glob("r.*.mca"))
    if not regions:
        sys.exit(f"No region files in {WORLD_SRC / REGION}. Run scripts/07_write_world.py first.")
    dest = SERVER / "world"
    if dest.exists():
        sys.exit(f"{dest} already exists, and it may hold a world you have played in. Move or delete it, then run this again.")
    SERVER.mkdir(parents=True, exist_ok=True)
    shutil.copytree(WORLD_SRC, dest)
    props = SERVER / "server.properties"
    if not props.exists():
        props.write_text(PROPERTIES)
    surface = np.load(OUT / "surface_y.npy")
    cz, cx = surface.shape[0] // 2, surface.shape[1] // 2
    y = int(surface[cz, cx]) + 1
    print(f"Copied {len(regions)} region files to {dest}")
    print(f"Wrote {props}")
    print()
    print("Next: copy a Paper jar into out/server, run it once, accept the EULA in eula.txt, run it again, then in the server console:")
    print(f"  setworldspawn {cx} {y} {cz}")
    print(f"  tp <your name> {cx} {y} {cz}")


if __name__ == "__main__":
    main()
