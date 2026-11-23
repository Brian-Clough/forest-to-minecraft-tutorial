# forest-to-blocks

Tutorial project: turn open elevation and canopy height maps into a Minecraft Java Edition world, one block per metre. Site: a US landscape with clearcuts of different ages (Hansen loss year shows the age).

Status: Earth Engine export written (mock-run only), nothing downloaded yet.

1. `ee/export_aoi.js`: run in the Earth Engine Code Editor, centred on a clearcut patchwork. Exports a 1,024 m GeoTIFF, five bands, 1 m pixels in UTM.
2. (next) `scripts/build_world.py`: read the GeoTIFF, write an Anvil world.
3. (next) tutorial text.
