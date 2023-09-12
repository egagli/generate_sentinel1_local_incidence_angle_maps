"""
Functions to generate sentinel-1 lia maps

Author: Eric Gagliano (egagli@uw.edu)
Updated: 08/2023
"""

import os

os.system('pip install -q sarsen==0.9.2')

import numpy as np
import rioxarray  
import xarray as xr
import adlfs
import planetary_computer
import pystac_client
import pystac
import stackstac
import geopandas as gpd
import rioxarray as rxr
import sarsen

def create_cop30_dem(aoi_gdf,dem_folder_path,res=10):
    """
    Given a geodataframe and a path to a dem folder, create a 10m DEM in UTM derived from COP30 DEM. Adapted 
    from https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30#Example-Notebook. 

    Args:
    aoi_gdf: geodataframe of area of interest
    dem_folder_path: path to folder to store dem 
    
    Returns:
    No returns, but creates a 10m UTM projected DEM in the dem_folder_path 
    """
    
    dem_urlpath = f"{dem_folder_path}/dem.tif"
    dem_10m_UTM_urlpath = dem_urlpath.strip(".tif") + "_UTM.tif"
    
    catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1")

    search = catalog.search(collections="cop-dem-glo-30", bbox=aoi_gdf.total_bounds)
    items = list(search.get_items())
    dem_raster_all = stackstac.stack(items, bounds=aoi_gdf.total_bounds).squeeze()
    
    dem_raster = dem_raster_all.compute()
    if "time" in dem_raster.dims:
        dem_raster = dem_raster.max("time")
    dem_raster.rio.set_crs(dem_raster_all.rio.crs)
    dem_raster.rio.to_raster(dem_urlpath)
    
    t_srs = dem_raster.rio.estimate_utm_crs()
    t_srs = str(t_srs)
    
    os.system(f'gdalwarp -r bilinear -s_srs EPSG:4326+5773 -t_srs {t_srs} -tr {res} {res} -overwrite -ot Float32 -co COMPRESS=DEFLATE -dstnodata -3.4028234663852886e+38 {dem_urlpath} {dem_10m_UTM_urlpath}')
    os.system(f'rm {dem_urlpath}')
    dem_raster_10m_UTM = rxr.open_rasterio(dem_10m_UTM_urlpath,mask_and_scale=True)
    dem_raster_10m_UTM.rio.to_raster(dem_10m_UTM_urlpath)


def mirror_folder(fs, bucket, folder, exclude="vh"):
    # from https://github.com/bopen/sarsen/blob/main/notebooks/gamma_wrt_incidence_angle-S1-GRD-IW-RTC-South-of-Redmond.ipynb
    for path, folders, files in fs.walk(f"{bucket}/{folder}"):
        os.makedirs(path[len(bucket) + 1 :], exist_ok=True)
        for f in files:
            if exclude in f:
                continue
            file_path = os.path.join(path, f)
            lfile_path = file_path[len(bucket) + 1 :]
            if not os.path.isfile(lfile_path):
                fs.download(file_path, lfile_path + "~")
                os.rename(lfile_path + "~", lfile_path)
                
def get_lia(product_folder,dem_folder_path):
    """
    Given a product folder and dem folder path, download a GRD file from MPC and compute the lia map using sarsen. Adapted 
    from https://github.com/microsoft/PlanetaryComputerExamples/blob/main/tutorials/rtc-qualitative-assessment.ipynb. 

    Args:
    product_folder: folder name of granule of interest
    dem_folder_path: path to folder to store dem
    
    Returns:
    angle: lia map 
    """
    
    dem_urlpath = f"{dem_folder_path}/dem.tif"
    dem_10m_UTM_urlpath = dem_urlpath.strip(".tif") + "_UTM.tif"
    
    measurement_group = "IW/VV"
    grd_account_name = "sentinel1euwest"
    grd_bucket = "s1-grd"
    grd_token = planetary_computer.sas.get_token(grd_account_name, grd_bucket).token

    grd_product_folder = f"{grd_bucket}/{product_folder}"

    grd_fs = adlfs.AzureBlobFileSystem(grd_account_name, credential=grd_token)
    grd_fs.ls(grd_product_folder)
    
    mirror_folder(grd_fs, grd_bucket, product_folder)
    
    dem_raster_10m_UTM = sarsen.scene.open_dem_raster(dem_10m_UTM_urlpath)

    measurement_ds, kwargs = sarsen.apps.open_dataset_autodetect(product_folder,group=measurement_group)

    orbit_ecef = xr.open_dataset(product_folder, group=f"{measurement_group}/orbit", **kwargs)
    dem_ecef = sarsen.scene.convert_to_dem_ecef(dem_raster_10m_UTM,source_crs=str(dem_raster_10m_UTM.rio.estimate_utm_crs()))
    
    acquisition = sarsen.apps.simulate_acquisition(dem_ecef, orbit_ecef.position,coordinate_conversion=None, correct_radiometry=True)
    oriented_area = sarsen.scene.compute_dem_oriented_area(dem_ecef)
    dem_normal = -oriented_area / np.sqrt(xr.dot(oriented_area, oriented_area, dims="axis"))
    orbit_interpolator = sarsen.orbit.OrbitPolyfitIterpolator.from_position(orbit_ecef.position)
    position_ecef = orbit_interpolator.position()
    velocity_ecef = orbit_interpolator.velocity()
    acquisition = sarsen.geocoding.backward_geocode(dem_ecef, orbit_ecef.position, velocity_ecef)
    slant_range = np.sqrt((acquisition.dem_distance**2).sum(dim="axis"))
    dem_direction = acquisition.dem_distance / slant_range
    angle = np.arccos(xr.dot(dem_normal, dem_direction, dims="axis"))
    
    os.system('rm -rf GRD')

    return angle

def search_for_representative_scenes(aoi_gdf):
    """
    Given a geodataframe, return all relative orbits covered by the area of interest, as well as representative granules for each.

    Args:
    aoi_gdf: geodataframe of area of interest
    
    Returns:
    unique_relative_orbits: list of strings of relative orbits
    id_list: list of strings of representative granules
    """
    
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",modifier=planetary_computer.sign_inplace,)

    time_of_interest = "2016-01-01/2023-01-01"

    search = catalog.search(
        collections=["sentinel-1-rtc"],
        bbox=aoi_gdf.total_bounds,
        datetime=time_of_interest,)

    items = search.item_collection()
    print(f"Returned {len(items)} Items")
    ds = stackstac.stack(items,epsg=aoi_gdf.estimate_utm_crs().to_epsg())
    
    unique_relative_orbits = np.unique(ds['sat:relative_orbit'])
    id_list = []
    for relative_orbit in unique_relative_orbits:
        file_id = str(ds[ds['sat:relative_orbit']==relative_orbit][0].id.values)
        rtc_item = catalog.get_collection("sentinel-1-rtc").get_item(f"{file_id}")
        grd_item = pystac.read_file(rtc_item.get_single_link("derived_from").target)

        id_list.append(grd_item.assets['vv'].href[53:-23])
    
        print(f'For relative orbit {relative_orbit}, we will use {id_list[-1]} as the product folder.')
        
    return unique_relative_orbits,id_list
    
def create_lia_rasters(unique_relative_orbits,id_list,dem_folder_path,output_folder_path):
    """
    Given a list of relative orbits, list of representative granlues, and output folder path, 
    create rasters of lia maps.
    Args:
    unique_relative_orbits: list of strings of relative orbits
    id_list: list of strings of representative granules
    dem_folder_path: path to folder to store dem
    output_folder_path: path to output lia maps
    
    Returns:
    No returns, but creates lia tifs in the output folder
    """
    
    for relative_orbit,file_id in zip(unique_relative_orbits,id_list):
        angle = get_lia(file_id,dem_folder_path)
        save_path = f'{output_folder_path}/{relative_orbit}.tif'
        angle.rio.to_raster(save_path)
        print(f'LIA map for {file_id} is complete and saved at {save_path}.')
    
def create_lia_stack(unique_relative_orbits,output_folder_path):
    """
    Given a list of relative orbits and output folder path, stack lia raster tifs and save as netcdf. 
    Args:
    unique_relative_orbits: list of strings of relative orbits
    output_folder_path: path to output lia maps
    
    Returns:
    No returns, but creates lia netcdf in the output folder
    """
    rel_orbit_var = xr.Variable('sat:relative_orbit', unique_relative_orbits)
    lia_stack = xr.concat([rxr.open_rasterio(f"{output_folder_path}/{orbit}.tif") for orbit in unique_relative_orbits],dim=rel_orbit_var).squeeze().sortby('sat:relative_orbit')
    save_path = f'{output_folder_path}/lia_stack_orbits_{"_".join(unique_relative_orbits.astype(str))}.nc'
    lia_stack.to_netcdf(save_path)
    print(f'Raster stack is complete and saved at {save_path}')
    
def geojson_to_lia_rasters_and_lia_stack(aoi_geojson,res=10):
    """
    Given a geojson, create lia maps saved as tifs and a lia raster stack saved as a netcdf. 
    Args:
    aoi_geojson: string path to geojson
    
    Returns:
    No returns, but creates lia rasters and lia netcdf in the output folder
    """
    
    aoi_gdf = gpd.read_file(aoi_geojson)
    dem_folder_path = 'dems'
    output_folder_path = 'lia_maps'
    os.makedirs(dem_folder_path, exist_ok=True)
    os.makedirs(output_folder_path, exist_ok=True)
    
    create_cop30_dem(aoi_gdf,dem_folder_path,res=res)
    
    unique_relative_orbits,id_list = search_for_representative_scenes(aoi_gdf)
    
    create_lia_rasters(unique_relative_orbits,id_list,dem_folder_path,output_folder_path)
    create_lia_stack(unique_relative_orbits,output_folder_path)
    
    print(f'Complete! Check {output_folder_path} for LIA rasters and netcdf. For reference, 10m UTM projected DEM saved in {dem_folder_path}.')
