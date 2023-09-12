# Easily generate Sentinel-1 local incidence angle maps given an AOI
**Eric Gagliano (egagli@uw.edu)** 

**Updated September 11, 2023**

Sentinel-1 local incidence angle (LIA) maps are very useful but often confusing and timely to fetch. This utility uses [sarsen](https://github.com/bopen/sarsen) under the hood to quickly(ish) create LIA rasters from [GRD files](https://planetarycomputer.microsoft.com/dataset/sentinel-1-grd) and a [Copernicus 30 meter DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30) both temporarily downloaded from Microsoft Planetary Computer. Please please (please) check out the caveats section below before use. Using this utility is as easy as 1,2,3!



![steps](https://github.com/egagli/generate_sentinel1_local_incidence_angle_maps/assets/67975937/64018c09-0a5e-40cc-876d-45dbcc1a7f2c)

Caveats:
* Best to run this on the [Microsoft Planetary Computer hub](https://planetarycomputer.microsoft.com/docs/overview/environment/) if you want to avoid authentication with a subscription key, as I used the [Microsoft Planetary Computer Sentinel-1 RTC repo](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc) for a granule search step. Check out [this page](https://planetarycomputer.microsoft.com/docs/concepts/sas/#when-an-account-is-needed) for running this repo off the MPC hub.  
* Creation of LIA rasters is DEM dependent. If you are interested in the exact LIA used in a specific RTC correction for example, this might get you close, but is likely different depending on which DEM was used for the RTC correction. Though other DEMs might work well in specific locations, I use the Copernicus 30m DEM because it is global and is similar to what is used for RTC correction in the RTC product hosted on MPC (they use the PlanetDEM 30m for RTC correction). In this utility, the Copernicus 30m DEM is resampled with bilinear resampling to 10m and projected to UTM.
* For each relative orbit, I assume LIA maps do not change from one acqusition to the next. My guess is that this is fine for most purposes, though I'm sure in reality there are minor variations between subsequent passes of the same relative orbit due to variation in spacecraft position and attitude (which alters the viewing geometry). _Would appreciate a fact check on this one._
* ~~This tool will probably work best for areas within predefined Sentinel-1 footprints. I have not tested this tool with regions that overlap two separate scenes, and I am pretty confident it will fail. If you need this tool to perform this function, let me know and I'll see what I can do.~~ Ok, I think I have this working now (Sept 11, 2023).
* I want to do some validation and comparisons for these maps. Some options that come to mind are the [LIA maps available on AWS](https://registry.opendata.aws/sentinel-1-rtc-indigo/), though these LIA maps are only available over CONUS for January 2017 - April 2021. Also, ASF's HyP3 on-demand RTC processing has an [option to include the LIA raster in the final output](https://storymaps.arcgis.com/stories/2ead3222d2294d1fae1d11d3f98d7c35#ref-n-IVlZJ1). I have not done rigorous comparison with either of these yet.

I took heavy inspiration from the following notebooks: 
* https://github.com/bopen/sarsen/blob/main/notebooks/gamma_wrt_incidence_angle-S1-GRD-IW-RTC-South-of-Redmond.ipynb
* https://github.com/microsoft/PlanetaryComputerExamples/blob/main/tutorials/rtc-qualitative-assessment.ipynb
* https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30#Example-Notebook

Lots of cool uses for LIA maps, check out https://github.com/egagli/sar_snowmelt_timing/blob/main/examples/binary_wet_snow_map_timeseries.ipynb to see an example for how we can use these LIA maps to build a time series of binary wet snow maps.


Please feel free to contact me at egagli@uw.edu if you need anything!
