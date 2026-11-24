"""Chunk 8: put the world into a Minecraft save so you can open it in the game.

First create a Superflat world in Minecraft (Create New World, World tab: World Type = Superflat; More tab: Allow Commands
on), then quit to the title screen. Minecraft writes the world's level.dat itself, and this script copies our region files
into that save. Your original region folder is renamed region_original, not deleted.

Usage: python scripts/08_install_world.py "<path to the save folder>"
  Mac:     ~/Library/Application Support/minecraft/saves/<world name>
  Windows: %APPDATA%\\.minecraft\\saves\\<world name>
  Linux:   ~/.minecraft/saves/<world name>
"""
import shutil, sys, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SRC = OUT / "world" / "dimensions" / "minecraft" / "overworld" / "region"     # chunk 7 writes this layout


def region_folder(save):
    """Java 26.1 and later keep the overworld in dimensions/minecraft/overworld; older versions use region/ in the save root."""
    new = save / "dimensions" / "minecraft" / "overworld"
    if new.is_dir():
        return new / "region"
    if (save / "region").is_dir() or (save / "level.dat").exists():
        return save / "region"
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    save = pathlib.Path(sys.argv[1]).expanduser()
    files = sorted(SRC.glob("r.*.mca"))
    if not files:
        sys.exit(f"No region files in {SRC}. Run scripts/07_write_world.py first.")
    if not (save / "level.dat").exists():
        sys.exit(f"{save} does not look like a Minecraft save (no level.dat). Create the Superflat world in the game first, "
                 "then quit to the title screen.")
    dest = region_folder(save)
    if dest is None:
        sys.exit(f"Could not find the overworld region folder in {save}.")
    backup = dest.with_name("region_original")
    if backup.exists():
        sys.exit(f"{backup} already exists, so this save has been installed before. Create a fresh Superflat world and use that.")
    if dest.exists():
        dest.rename(backup)
    dest.mkdir(parents=True)
    for f in files:
        shutil.copy2(f, dest / f.name)
    surface = np.load(OUT / "surface_y.npy")
    cz, cx = surface.shape[0] // 2, surface.shape[1] // 2
    y = int(surface[cz, cx]) + 1
    print(f"Copied {len(files)} region files to {dest}")
    print(f"The old region folder is now {backup.name}.")
    print()
    print("Open the world in Minecraft. You will start underground, so type this in the chat to move to the centre of the forest:")
    print(f"  /tp @s {cx} {y} {cz}")


if __name__ == "__main__":
    main()
