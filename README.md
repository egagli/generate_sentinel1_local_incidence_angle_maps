# Easily generate Sentinel-1 local incidence angle maps given an AOI
**Eric Gagliano (egagli@uw.edu)** 

**Updated August 30, 2023**

Sentinel-1 local incidence angle (LIA) maps are very useful but often confusing and timely to fetch. This utility temporarily downloads [GRD files](https://planetarycomputer.microsoft.com/dataset/sentinel-1-grd) and a [Copernicus 30 meter DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30) from Microsoft Planetary Computer, and uses [sarsen](https://github.com/bopen/sarsen) under the hood to quickly(ish) create LIA rasters. Please please (please) check out the caveats section below before use. Using this utility is as easy as 1,2,3!



![steps](https://github.com/egagli/generate_sentinel1_local_incidence_angle_maps/assets/67975937/64018c09-0a5e-40cc-876d-45dbcc1a7f2c)

Caveats:
* Best to run this on the [Microsoft Planetary Computer hub](https://planetarycomputer.microsoft.com/docs/overview/environment/) if you want to avoid authentication with a subscription key, as I used the [MPC Sentinel-1 RTC repo](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc) for a granule search step. Check out [this page](https://planetarycomputer.microsoft.com/docs/concepts/sas/#when-an-account-is-needed) for running this repo off the MPC hub.  
* Creation of LIA rasters is DEM dependent. If you are interested in the exact LIA used in a specific RTC correction for example, this might get you close, but is likely different depending on which DEM was used for the RTC correction.
* For each relative orbit, I assume LIA maps do not change from one acqusition to the next. My guess is that this is fine for most purposes, though I'm sure in reality there are minor variations between subsequent passes of the same relative orbit due to variation in spacecraft attitude/viewing geometry. Would appreciate a fact check on this one.
* This tool will probably work best for areas within predefined Sentinel-1 footprints. I have not tested this tool with regions that overlap two separate scenes, and I am pretty confident it will fail. If you need this tool to perform this function, let me know and I'll see what I can do.
* I want to do some validation with the [LIAs available on AWS](https://registry.opendata.aws/sentinel-1-rtc-indigo/). I have not done this yet.

I took heavy inspiration from the following repos: 
* https://github.com/bopen/sarsen/blob/main/notebooks/gamma_wrt_incidence_angle-S1-GRD-IW-RTC-South-of-Redmond.ipynb
* https://github.com/microsoft/PlanetaryComputerExamples/blob/main/tutorials/rtc-qualitative-assessment.ipynb
* https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30#Example-Notebook

Lots of cool uses for LIA maps, check out https://github.com/egagli/sar_snowmelt_timing/blob/main/examples/binary_wet_snow_map_timeseries.ipynb to see an example for how we can use these maps to build binary wet snow maps.

Feel free to contact me at egagli@uw.edu if you need anything!
