
## User QC Submission Checklist: What Not To Do

> To ensure your netCDF file is properly checked by the GDAC QARTOD QC system, avoid these common mistakes:

| **What Not To Do**                                                      | **Why It Causes Problems**                    | **Example**                                                                                  |
|-------------------------------------------------------------------------|-----------------------------------------------|----------------------------------------------------------------------------------------------|
| Omit required geophysical variables                                     | QC tests cannot run on missing variables      | *You submit only `sea_water_temperature` but omit `salinity: sea_water_practical_salinity`.*    |
| Use non-standard or incorrect CF standard names                         | QC cannot identify/process the variable       | *You use `water_density` instead of the CF standard `sea_water_density`.*                     |
| Leave out or use incorrect units                                        | QC thresholds/tests may be invalid or skipped | *You use `bdar` instead of `dbar` for `sea_water_pressure` units.*                        |
| Omit `valid_min`/`valid_max`, or set `valid_min` ≥ `valid_max`          | QC cannot determine valid data ranges         | *You forget to set `valid_min` and `valid_max` for `sea_water_temperature`, or set both to 0.*|
| Submit all-NaN or all-fill-value variables                              | QC is skipped for variables with no data      | *Your `sea_water_electrical_conductivity` variable contains only NaN or fill values.*|
| Omit `profile_lat` and `profile_lon`                                    | Location QC cannot be performed               | *Your file has no `profile_lat` or `profile_lon` variables.*                                         |
| Submit files with missing/non-ascending time stamps                     | Time-based QC tests will fail                 | *Timestamps in `time` variable are not in order or some are missing.*                                |
| Use duplicate variable/standard names                                   | QC cannot uniquely identify variables         | *You have two variables both named `temperature` or both with the same `standard_name`.* |

---

**Tip:**  
Double-check your file against this checklist and examples before submitting to GDAC!  
If you’re unsure about CF standard names or required metadata, consult the [CF Standard Names Table](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html) or the GDAC user guide.

---
