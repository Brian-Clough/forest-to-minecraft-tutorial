// Exports a 1,024 m square around the map centre as one 1 m GeoTIFF for the forest-to-blocks tutorial:
//   band 1  dem3dep1m     USGS 3DEP 1 m elevation (m), -9999 where 3DEP has no 1 m lidar there
//   band 2  dem3dep10m    USGS 3DEP 10 m elevation (m), the fallback, resampled to 1 m
//   band 3  canopy_h      Meta/WRI 1 m canopy height (m), 0 where no trees, -9999 = no data
//   band 4  loss_year     Hansen v1.13 year of forest loss (2001 to 2025), 0 = none (30 m, nearest)
//   band 5  treecover2000 Hansen tree cover 2000 (%)
// How to use: (1) turn on the Hansen layer below, pan to a patchwork of clearcuts (US only: both 3DEP and
// the Meta layer must cover it), (2) leave the map centred on the spot you want, (3) press Run, then the Tasks tab.
// Output is in UTM (north zone from the centre longitude), so 1 pixel = 1 m = 1 Minecraft block.

var HANSEN = ee.Image('UMD/hansen/global_forest_change_2025_v1_13');
Map.setOptions('SATELLITE');
Map.addLayer(HANSEN.select('lossyear').selfMask(), {min: 1, max: 25, palette: ['yellow', 'orange', 'red', 'purple']}, 'Hansen loss year (yellow old, purple recent)');

var SIZE_M = 1024;
var centre = Map.getCenter();
var lon = ee.Number(centre.coordinates().get(0));
var lat = ee.Number(centre.coordinates().get(1));
var zone = lon.add(180).divide(6).floor().add(1);
var crs = ee.String('EPSG:326').cat(zone.format('%02d'));     // WGS84 / UTM north
var utmPoint = centre.transform(crs, 1);
var xy = ee.List(utmPoint.coordinates());
var x0 = ee.Number(xy.get(0)).floor().subtract(SIZE_M / 2);
var y0 = ee.Number(xy.get(1)).floor().subtract(SIZE_M / 2);
var region = ee.Geometry.Rectangle([x0, y0, x0.add(SIZE_M), y0.add(SIZE_M)], crs, false);
Map.addLayer(region, {color: 'white'}, 'Export window', true, 0.4);

var dem1 = ee.ImageCollection('USGS/3DEP/1m').select('elevation').mosaic().rename('dem3dep1m').unmask(-9999);
var dem10 = ee.Image('USGS/3DEP/10m').select('elevation').rename('dem3dep10m').unmask(-9999);
var meta = ee.ImageCollection('projects/sat-io/open-datasets/facebook/meta-canopy-height').mosaic().select(0).rename('canopy_h').unmask(-9999);
var loss = HANSEN.select('lossyear').rename('loss_year').toFloat();
var lossYear = loss.where(loss.gt(0), loss.add(2000)).unmask(0);
var tc = HANSEN.select('treecover2000').rename('treecover2000').toFloat().unmask(0);

var out = ee.Image.cat([dem1.toFloat(), dem10.toFloat(), meta.toFloat(), lossYear, tc]).clip(region);
print('Centre lon/lat', lon, lat);
print('UTM CRS', crs);
print('SW corner (E, N)', x0, y0);

Export.image.toDrive({
  image: out,
  description: 'forest_to_blocks_aoi',
  folder: 'forest_to_blocks',
  fileNamePrefix: 'forest_to_blocks_aoi',
  region: region,
  crs: crs,
  scale: 1,
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF'
});
