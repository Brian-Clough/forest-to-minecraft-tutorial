# Data sources and licences

The example GeoTIFF combines three public layers, exported from Google Earth Engine at 1 m in UTM. Licences were read from each dataset's catalogue page on 23 Nov 2026. Check them again before you reuse the data elsewhere.

| Band | Layer | Resolution | Licence | Credit |
|---|---|---|---|---|
| `dem3dep1m` | USGS 3DEP 1 m elevation (`USGS/3DEP/1m`), NAVD88 metres | 1 m, lidar-based, partial US coverage | Public domain ("most USGS information resides in the public domain"); attribution requested | U.S. Geological Survey, 3D Elevation Program 1-Meter Resolution Digital Elevation Model |
| `dem3dep10m` | USGS 3DEP 10 m elevation (`USGS/3DEP/10m`), fallback where no 1 m lidar exists | 10 m, resampled to 1 m | Public domain, attribution requested | U.S. Geological Survey, 3D Elevation Program |
| `canopy_h` | High Resolution Canopy Height Maps by WRI and Meta (`projects/sat-io/open-datasets/facebook/meta-canopy-height`) | 1 m, model estimate from Maxar imagery, about 80% of it acquired 2018 to 2020 | CC BY 4.0 | Tolan et al. (2024), *Remote Sensing of Environment* 300, 113888. "High Resolution Canopy Height Maps by WRI and Meta was accessed on 23 November 2026 from Google Earth Engine." Source imagery © 2016 Maxar |
| `loss_year` | Hansen Global Forest Change v1.13, `lossyear` | 27.83 m, nearest-neighbour to 1 m | CC BY 4.0 | Hansen et al. (2013), *Science* 342, 850 to 853, doi:10.1126/science.1244693 |
| `treecover2000` | Hansen Global Forest Change v1.13, `treecover2000` | 27.83 m | CC BY 4.0 | as above |

Notes
- The canopy height layer is a model's estimate from satellite photographs, not a lidar measurement, and it is a snapshot from roughly 2018 to 2020.
- Hansen's loss year is a coarse (about 28 m) detection of stand-replacing loss. Cuts smaller than a pixel are missed, and the year is the year the loss was detected.
