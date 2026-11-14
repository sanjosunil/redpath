# RedPath: Mars Survival Map

RedPath is an interactive planning tool for a Mars "Marswalk". It stacks NASA Mars data layers on one map, turns them into a 0-100 survival score, and finds the shortest and the safest walking route between two points.

Built for the NASA Space Apps Challenge: create a layered, integrated view of a location or route on the Martian surface that pulls together data from multiple NASA science missions.

## What it does
- **Layers:** elevation, slope, water-equivalent hydrogen (ice proxy), radiation dose, temperature, dust opacity.
- **Survival score:** each cell of a 96 x 96 grid (about 240 km across) gets a 0-100 score. Users change the weights of terrain, ice, radiation, temperature and dust.
- **Route planner:** A* search over the grid. It never crosses slopes above a user-set limit. It draws a shortest route (dashed) and a safest route (solid) and compares distance, EVA time, steepest slope, mean score and radiation dose.
- **Mission panel:** live cursor readouts, alerts and a site briefing for Jezero, Gale, Arcadia and Utopia.

## Run it
The page needs to be served over http so it can load `data/`:

```
python -m http.server
```

Then open http://localhost:8000. Without data files the page shows synthetic **DEMO** terrain and a banner says so.

## Use real NASA data
```
pip install rasterio numpy
python build_data.py jezero --lat 18.4 --lon 77.5 --dem <elevation.tif> --weh <weh.tif> --temp <temp.tif> --temp-kelvin --tau <tau.tif>
```
Only `--dem` is required. Any layer not supplied is filled from a simple model, and the `source` field in the output JSON records which layers are measured and which are modelled. The page shows this in the site briefing.

## NASA data and resources
- NASA Trek (Mars base map tiles): https://trek.nasa.gov/mars/
- NASA Planetary Data System (Mars Odyssey GRS, MGS MOLA): https://pds.nasa.gov/
- NASA PDS Geosciences Node (MSL RAD radiation data): https://pds-geosciences.wustl.edu/

Other tools: Leaflet (https://leafletjs.com/), cdnjs, rasterio, NumPy, USGS Astrogeology elevation model (https://astrogeology.usgs.gov/).

## Honest limits
- Radiation is an elevation-based model scaled to the surface dose measured by Curiosity's RAD instrument at Gale Crater (about 0.64 mSv/day). It is not a point-by-point measurement.
- Score thresholds, the 2.5 km/h walking pace and the 8 h EVA window are planning assumptions that mission experts should validate.
- The demo terrain is synthetic unless real data files are present in `data/`.

## Super Intelligence (SI) disclosure
The code in this repository (`index.html`, `build_data.py`) was generated with SI assistance (Claude, by Anthropic) and reviewed by the RedPath team. No NASA logos, flags or mission identifiers are used or modified.
