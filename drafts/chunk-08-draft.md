# Draft: Chunk 8, open the world in Minecraft

*First-pass tutorial prose for you to revise. Scripts: `scripts/08_install_world.py` (the main route) and `scripts/08b_make_server_folder.py` (optional). Run chunk 7 first. This is the one step where you work in the game itself.*

---

## 8. Open the world in Minecraft

We now have region files, but a Minecraft save needs more than those. It also needs a `level.dat` file holding the seed, the spawn point and the game rules. We could write that file by hand, but its contents change between Minecraft versions, and a wrong file means a world that will not open. So we let the game write it, and copy our region files into the save it creates.

### Create an empty world

1. Start Minecraft Java Edition 26.3 and choose **Create New World**.
2. On the **World** tab, set **World Type** to **Superflat**.
3. On the **More** tab, turn on **Allow Commands** (cheats). You will need one command later.
4. Create the world, let it load, then save and quit to the title screen. The world must be closed before the next step.

### Copy our world into it

```
python scripts/08_install_world.py "<path to the save folder>"
```

The save folder is the world's folder inside Minecraft's `saves` directory:

| System | Location |
|---|---|
| Mac | `~/Library/Application Support/minecraft/saves/<world name>` |
| Windows | `%APPDATA%\.minecraft\saves\<world name>` |
| Linux | `~/.minecraft/saves/<world name>` |

The script finds the right folder inside the save and renames the old region folder to `region_original`, so nothing is deleted. Since Java 26.1 the overworld's regions live in `dimensions/minecraft/overworld/region/`, and before that in `region/`. The script checks which layout the save uses.

It refuses to run in a save that is missing `level.dat`, and in one it has already installed into, so a second run cannot overwrite the first.

### Open it and move to the forest

Open the world from the single-player list. You will start underground, because the new world's spawn point sits at flat ground level, about y = -60, and our terrain now fills that space. The script printed a command with the coordinates of the window's centre. Type it in the chat:

```
/tp @s 512 59 512
```

You should now be standing in the forest, with ground that ends at the edge of the 1,024-block square. The first load can be slow, because the game computes lighting for every chunk it has not seen before. It also upgrades each chunk to the current format, because chunk 7 wrote them with an older data version. You may also want to set the world spawn with `/setworldspawn 512 59 512`.

### Optional: run it on a Paper server

If you want a server, for example to run the WolfRabbit plugin from the Minecraft ecology project, `scripts/08b_make_server_folder.py` builds a ready server folder from the same world, including a `server.properties` with flat world settings and no mobs. Download Paper for 26.3, run it once, accept the EULA in `eula.txt` yourself, and run it again. The script prints the commands for setting the spawn.

---

## Notes for you (not for publication)

- **Never run in Minecraft by me.** The two risks are (1) whether the game keeps our region files when it opens the save, and (2) whether it reads chunks written with the older data version (3953, set in `scripts/07_write_world.py`). If the world is flat land, risk 1 happened. If it reports chunk errors or the blocks look wrong, try risk 2 first.
- **I tested the script, not the result.** I ran `08_install_world.py` against fake saves in both layouts (26.1 and later, and older), plus a missing-`level.dat` case and a second-run case. It copies the files and renames the old folder correctly each time.
- **The "Allow Commands" label** is from memory of the world creation screen and may differ in 26.3. Any way of enabling cheats works.
- **Leftover files.** The new world can have `entities` and `poi` folders generated for its starting chunks. The script leaves them alone, since the flat world holds no entities or points of interest worth keeping. If you see odd villagers or similar, delete them.
- **The edges.** Outside the window the game generates ordinary flat land at about y = -60, while our ground reaches up to about y = 100, so there is a cliff at the boundary.
- **Player position.** The player's saved position is the old spawn point, buried in the new terrain, so the `/tp` is required, not optional. Writing a better spawn would mean editing `level.dat`, which the whole route is designed to avoid.
- **Codespace.** The scripts run in a Codespace, which has no Minecraft. Readers working there need to download `out/world` and run `08_install_world.py` on their own computer. The README should say so, and could suggest zipping `out/world` for download.
- **Server route:** the earlier version of this chunk is now the optional section. Its files and layout are unchanged apart from the rename to `08b`.
