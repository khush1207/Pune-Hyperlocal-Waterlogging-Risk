import ee
import geemap
import pandas as pd

# ======================================================
# CONFIG
# ======================================================

PROJECT_ID = "hyperloal-flood-risk"

INPUT_CSV = r"F:/Khushboo/Hyperlocal-Flood-Risk/data/ward_sampling_points.csv"

OUTPUT_CSV = r"F:/Khushboo/Hyperlocal-Flood-Risk/data/URBAN-1.csv"

BUFFER_RADIUS = 500  # meters

START_DATE = "2023-01-01"
END_DATE = "2024-12-31"

# ======================================================
# Initialize Earth Engine
# ======================================================

ee.Initialize(project=PROJECT_ID)

print("✅ Connected to Earth Engine")

# ======================================================
# Load sampling points
# ======================================================

points = pd.read_csv(INPUT_CSV)

print(f"Loaded {len(points)} sampling points")

# ======================================================
# Dynamic World collection
# ======================================================

dw = (
    ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filterDate(START_DATE, END_DATE)
)

# Most frequent landcover during 2023-2024
landcover = dw.select("label.py").mode()

# ======================================================
# Process every point
# ======================================================

results = []

for i, row in points.iterrows():

    point = ee.Geometry.Point(
        [row["Longitude"], row["Latitude"]]
    )

    buffer = point.buffer(BUFFER_RADIUS)

    # Total pixels
    total_pixels = ee.Image.constant(1).reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=buffer,
        scale=10,
        maxPixels=1e9
    ).get("constant")

    # Built-up (class 6)
    built_pixels = landcover.eq(6).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=buffer,
        scale=10,
        maxPixels=1e9
    ).get("label.py")

    # Vegetation
    vegetation = (
        landcover.eq(1)   # Trees
        .Or(landcover.eq(2))  # Grass
        .Or(landcover.eq(4))  # Crops
        .Or(landcover.eq(5))  # Shrub & Scrub
    )

    vegetation_pixels = vegetation.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=buffer,
        scale=10,
        maxPixels=1e9
    ).get("label.py")

    total_pixels = ee.Number(total_pixels)
    built_pixels = ee.Number(built_pixels)
    vegetation_pixels = ee.Number(vegetation_pixels)

    built_percent = (
        built_pixels.divide(total_pixels)
        .multiply(100)
    )

    vegetation_percent = (
        vegetation_pixels.divide(total_pixels)
        .multiply(100)
    )

    results.append({
        "Ward_ID": row["Ward_ID"],
        "Ward_Name": row["Ward_Name"],
        "Point_ID": row["Point_ID"],
        "Latitude": row["Latitude"],
        "Longitude": row["Longitude"],
        "Builtup_Percent": built_percent.getInfo(),
        "Vegetation_Percent": vegetation_percent.getInfo()
    })

    if (i + 1) % 25 == 0:
        print(f"{i+1}/{len(points)} completed")

# ======================================================
# Save CSV
# ======================================================

output = pd.DataFrame(results)

output.to_csv(OUTPUT_CSV, index=False)

print("\n===================================")
print("Finished!")
print(output.head())
print(f"\nSaved to:\n{OUTPUT_CSV}")