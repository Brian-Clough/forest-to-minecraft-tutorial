# Draft: Chunk 8, set up the server

*First-pass tutorial prose for you to revise. Script: `scripts/08_make_server_folder.py`. Run chunk 7 first. This chunk is a different kind of step from the earlier ones, because the script assembles a folder and then you run a server.*

---

## 8. Open the world in a server

We have region files, but Minecraft also needs a few files around them, and a server to run them. This chunk uses a Paper server on your own computer, which is a free server that runs Minecraft Java worlds. You then join it from the normal game.

```
python scripts/08_make_server_folder.py
```

### What the script does

It copies the world from `out/world` to `out/server/world` and writes a small `server.properties` file next to it. It refuses to run if `out/server/world` already exists, so that it cannot overwrite a world you have played in.

The settings it writes are these:

| Setting | Value | Why |
|---|---|---|
| `level-type` | flat | the world outside our window is plain flat ground, not random terrain |
| `generate-structures` | false | no villages or dungeons appear in the forest |
| `spawn-monsters` | false | the forest stays quiet |
| `spawn-animals` | false | no random cows or sheep |
| `gamemode` | creative | you can fly and build |
| `spawn-protection` | 0 | you can edit blocks next to the spawn point |

Everything else takes the server's default.

### Two files the script leaves alone

The script does not write `level.dat`. That file holds the world's seed, spawn point, game rules and weather, and Java 26.1 changed it a good deal: some of its contents, such as game rules and world generation settings, moved to separate files. The server writes a correct one the first time it starts, so we let it.

The script also does not write `eula.txt`. That file is your agreement to Mojang's end-user licence, and you should read it and accept it yourself.

### Start the server

1. Download the Paper server for Minecraft 26.3 from papermc.io and put the `.jar` file in `out/server`.
2. From that folder, run `java -jar paper-*.jar`. It stops with a message about the EULA.
3. Open `eula.txt` and change `eula=false` to `eula=true`.
4. Run the same command again. Wait for a line saying the server is done starting.

On the first start, the server finds our region files, creates `level.dat`, and upgrades each chunk as it loads, because the chunks were written with an older data version (chunk 7). Expect a slow start and some log lines about this. The game also works out the lighting for every chunk at that point.

### Set the spawn and join

The script prints two commands with the coordinates of the window's centre. Type them into the server console:

```
setworldspawn 512 59 512
tp <your name> 512 59 512
```

Then start Minecraft Java 26.3, choose Multiplayer, add a server called `localhost`, and join. You should be standing in the middle of the forest window, and the ground should end at the edges of the 1,024-block square.

---

## Notes for you (not for publication)

- **Never run in Minecraft by me.** Everything in this chunk is untested. The two risks, in order, are (1) the server does not use our region files because there is no `level.dat` yet, and (2) the server rejects or mis-reads chunks written with the older data version. If the world comes up as plain flat land, risk 1 happened. If it reports chunk errors, risk 2 did.
- **Folder layout.** Java 26.1 and later keep the overworld in `world/dimensions/minecraft/overworld/region/`, and Paper follows the same layout (Paper's 26.1 announcement shows the tree). Chunk 7 originally wrote to `world/region/`, which was the pre-26.1 layout, so this patch moves that path. Fix chunk 7's README text if you copied the old path.
- **Spawn height.** The printed `y` is one block above the surface at the window's centre, which is a mature or regrowth stand, so you may land inside a tree crown. If so, fly up. A better spawn is an easy follow-up.
- **The edges.** Outside the window the server generates default flat land at about y = -60, while our ground sits at y = 0 to about 100, so you will see a cliff at the edge. A void world would hide it, but I did not confirm the flat-world settings format in 26.3, so I left it out.
- **The EULA and the jar** are yours to handle. The script says so.
- **Plugin worlds.** For WolfRabbit, the same `server.properties` settings apply, except `spawn-animals` should stay false as in its own README.
