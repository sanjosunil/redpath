#!/usr/bin/env python3
"""Build data/<site>.json for RedPath (Mars survival map) from NASA rasters.

SI DISCLOSURE: this script was generated with Super Intelligence assistance
(Claude, Anthropic) and reviewed by the RedPath team.

Install:  pip install rasterio numpy
Example:
  python build_data.py jezero --lat 18.4 --lon 77.5 \
      --dem Mars_MGS_MOLA_MEX_HRSC_Blended_DEM_Global_200m.tif \
      --weh odyssey_grs_weh.tif --temp tes_mean_temp.tif --temp-kelvin \
      --tau mars_dust_opacity.tif

Only --dem is required. Any layer you do not supply is filled from a simple
model and the output "source" string says so, so the page never passes a model
off as measured data. Rasters must be in geographic (lon/lat) coordinates.
Use --lon360 if your raster stores longitude as 0 to 360.
"""
import argparse, json, math, os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

KM = 2 * math.pi * 3389.5 / 360  # km per degree on Mars


def read(path, bbox, nx, ny, lon360):
    w, s, e, n = bbox
    if lon360:
        w, e = w % 360, e % 360
    with rasterio.open(path) as src:
        win = from_bounds(w, s, e, n, transform=src.transform)
        a = src.read(1, window=win, out_shape=(ny, nx), resampling=Resampling.bilinear,
                     boundless=True, fill_value=np.nan, out_dtype="float64")
        if src.nodata is not None:
            a[a == src.nodata] = np.nan
    return a


def fill(a):
    """Replace gaps with the layer mean so scoring never sees NaN."""
    m = np.nanmean(a) if np.isfinite(a).any() else 0.0
    return np.where(np.isfinite(a), a, m)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("site")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--size-deg", type=float, default=4.0, help="north-south extent in degrees")
    p.add_argument("--n", type=int, default=96, help="grid cells per side")
    p.add_argument("--dem", required=True, help="elevation GeoTIFF in metres (e.g. MOLA-HRSC blended DEM)")
    p.add_argument("--weh", help="water-equivalent hydrogen, wt% (e.g. Odyssey GRS)")
    p.add_argument("--temp", help="mean annual surface temperature raster")
    p.add_argument("--temp-kelvin", action="store_true")
    p.add_argument("--tau", help="dust column opacity raster")
    p.add_argument("--lon360", action="store_true")
    a = p.parse_args()

    nx = ny = a.n
    half = a.size_deg / 2
    lon_span = a.size_deg / math.cos(math.radians(a.lat))  # keeps cells roughly square, matches index.html
    s_, n_ = a.lat - half, a.lat + half
    w_, e_ = a.lon - lon_span / 2, a.lon + lon_span / 2
    bbox = (w_, s_, e_, n_)
    kmy = (n_ - s_) / ny * KM
    kmx = (e_ - w_) / nx * KM * math.cos(math.radians(a.lat))

    lats = n_ - (np.arange(ny) + 0.5) * (n_ - s_) / ny
    lat_grid = np.repeat(lats[:, None], nx, axis=1)
    src = []

    elev = fill(read(a.dem, bbox, nx, ny, a.lon360)); src.append("elevation: " + os.path.basename(a.dem))
    dzdy, dzdx = np.gradient(elev, kmy * 1000, kmx * 1000)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))

    if a.weh:
        ice = fill(read(a.weh, bbox, nx, ny, a.lon360)); src.append("ice: " + os.path.basename(a.weh))
    else:
        ice = np.clip(2 + 12 * np.clip((np.abs(lat_grid) - 25) / 45, 0, 1), 0, 30); src.append("ice: MODEL (latitude only)")

    if a.temp:
        t = fill(read(a.temp, bbox, nx, ny, a.lon360)); t = t - 273.15 if a.temp_kelvin else t
        src.append("temperature: " + os.path.basename(a.temp))
    else:
        t = -20 - 90 * (1 - np.cos(np.radians(lat_grid))) - 0.0015 * elev; src.append("temperature: MODEL (latitude and elevation)")

    if a.tau:
        dust = fill(read(a.tau, bbox, nx, ny, a.lon360)); src.append("dust: " + os.path.basename(a.tau))
    else:
        dust = np.full((ny, nx), 0.45); src.append("dust: MODEL (constant 0.45)")

    # Radiation: elevation-based model scaled to the surface dose measured by the MSL RAD instrument
    # at Gale Crater (about 0.64 mSv/day, near -4.5 km). Replace with a MAVEN/RAD-driven model if you have one.
    dose = np.clip(0.64 + 0.025 * ((elev + 4500) / 1000), 0.4, 1.0)
    src.append("radiation: MODEL scaled to MSL RAD at Gale")

    flat = lambda x: np.round(x, 3).ravel().tolist()
    out = {"nx": nx, "ny": ny, "bbox": {"s": s_, "n": n_, "w": w_, "e": e_},
           "source": "; ".join(src),
           "layers": {"elev": flat(elev), "slope": flat(slope), "ice": flat(ice),
                      "dose": flat(dose), "temp": flat(t), "dust": flat(dust)}}
    os.makedirs("data", exist_ok=True)
    with open(f"data/{a.site}.json", "w") as f:
        json.dump(out, f)
    print(f"Wrote data/{a.site}.json ({nx}x{ny} cells, ~{kmx:.1f} x {kmy:.1f} km each)")
    print("Sources:", out["source"])


if __name__ == "__main__":
    main()
