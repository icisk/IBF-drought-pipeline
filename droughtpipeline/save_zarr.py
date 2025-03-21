import xarray as xr
import rioxarray  # Handles GeoTIFFs
import os
import re
import pandas as pd
import sys
import logging
import s3fs

# Path to the folder containing TIFF files
# tif_dir = "data"

# Function to extract month from filename
def extract_month_from_filename(filename, start_year=2025):
    match = re.search(r"_(\d+)-month", filename)  # Extracts the number before '-month'
    if match:
        month_offset = int(match.group(1))  # Extract numerical part
        month = (month_offset % 12) + 1
        year = start_year + (month_offset // 12)
        return pd.Timestamp(f"{year}-{month:02d}-01")
    return None

def save_zarr(tif_dir, output_zarr):
    logging.info(f"Saving Zarr file from {tif_dir} to {output_zarr}")
    logging.info(os.listdir(tif_dir))
    # List all TIFF files in the directory
    tif_files = sorted([f for f in os.listdir(tif_dir) if f.endswith(".tif")])

    # Load datasets with time dimension
    datasets = []
    time_coords = []

    for tif_file in tif_files:
        if tif_file.startswith("rlower_tercile_probability"):
            logging.info(tif_file)
            time_stamp = extract_month_from_filename(tif_file)
            if time_stamp:
                ds = rioxarray.open_rasterio(os.path.join(tif_dir, tif_file))
                ds = ds.squeeze()  # Remove singleton band dimension if present
                ds = ds.assign_coords(time=time_stamp)
                datasets.append(ds)
                time_coords.append(time_stamp)

    # Combine all datasets along the time dimension
    data_array = xr.concat(datasets, dim="time")

    # Convert to xarray Dataset with a meaningful variable name
    dataset = data_array.to_dataset(name="rlower_tercile_probability")
    s3 = s3fs.S3FileSystem()
    store = s3fs.S3Map(root=output_zarr, s3=s3, check=False)
    # Save as a Zarr file
    dataset.to_zarr(store=store, consolidated=True, mode='w')

    logging.info("Zarr file saved successfully!")
    return dataset