// Exports a 1,024 m square around the map centre as one 1 m GeoTIFF for the forest-to-blocks tutorial:
//   band 1  dem3dep1m     USGS 3DEP 1 m elevation (m), -9999 where 3DEP has no 1 m lidar there
//   band 2  dem3dep10m    USGS 3DEP 10 m elevation (m), the fallback, smoothed (bicubic) to 1 m
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
// To reproduce an earlier window exactly, set FIXED_SW to its UTM CRS and south-west corner. Use null to take the map centre instead.
var FIXED_SW = {crs: 'EPSG:32610', x0: 465521, y0: 5173342};   // the SW Washington window used in the tutorial

var crs, x0, y0, lonLat;
if (FIXED_SW) {
  crs = FIXED_SW.crs; x0 = FIXED_SW.x0; y0 = FIXED_SW.y0;
  var cx = x0 + SIZE_M / 2, cy = y0 + SIZE_M / 2;
  var centreGeom = ee.Geometry.Point([cx, cy], crs);
  lonLat = ee.List(centreGeom.transform('EPSG:4326', 1).coordinates()).getInfo();
  Map.setCenter(lonLat[0], lonLat[1], 15);
} else {
  var centre = Map.getCenter();
  lonLat = ee.List(centre.coordinates()).getInfo();           // ordinary numbers, so we can build a plain CRS string
  var zone = Math.floor((lonLat[0] + 180) / 6) + 1;
  crs = 'EPSG:326' + (zone < 10 ? '0' + zone : '' + zone);    // WGS84 / UTM, northern hemisphere (all of the US)
  var xy = ee.List(centre.transform(crs, 1).coordinates()).getInfo();
  x0 = Math.floor(xy[0]) - SIZE_M / 2;
  y0 = Math.floor(xy[1]) - SIZE_M / 2;
}
var region = ee.Geometry.Rectangle([x0, y0, x0 + SIZE_M, y0 + SIZE_M], crs, false);
Map.addLayer(region, {color: 'white'}, 'Export window', true, 0.4);

var dem1raw = ee.ImageCollection('USGS/3DEP/1m').filterBounds(region).select('elevation');
var dem1 = dem1raw.mosaic().rename('dem3dep1m').unmask(-9999);
// 10 m: the older single-image asset USGS/3DEP/10m is deprecated and exported empty; use the tile collection.
var dem10col = ee.ImageCollection('USGS/3DEP/10m_collection').filterBounds(region).select('elevation');
var dem10raw = dem10col.mosaic().setDefaultProjection(dem10col.first().projection()).resample('bicubic');  // smooth 10 m up to 1 m
var dem10 = dem10raw.rename('dem3dep10m').unmask(-9999);
var meta = ee.ImageCollection('projects/sat-io/open-datasets/facebook/meta-canopy-height').mosaic().select(0).rename('canopy_h').unmask(-9999);
var loss = HANSEN.select('lossyear').rename('loss_year').toFloat();
var lossYear = loss.where(loss.gt(0), loss.add(2000)).unmask(0);
var tc = HANSEN.select('treecover2000').rename('treecover2000').toFloat().unmask(0);

var out = ee.Image.cat([dem1.toFloat(), dem10.toFloat(), meta.toFloat(), lossYear, tc]).clip(region);
// diagnostics: how many 10 m / 1 m pixels have real elevation inside the window (0 means no coverage)
print('3DEP 1 m tiles overlapping', dem1raw.size());
print('3DEP 10 m tiles overlapping', dem10col.size());
print('Centre lon/lat', lonLat);
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