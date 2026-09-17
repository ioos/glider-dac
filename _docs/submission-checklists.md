---
title: Submission Checklists
keywords:
  - IOOS
  - documentation
toc: false
summary: >-
  This page contains checklists to:
  (1) Organize deployment directories for automated checks and ingestion.
  (2) Verify the file is ready for NGDAC submission.
  (3) Confirm the NetCDF file passes NGDAC QARTOD QC.
---

### Deployment Folder Checklist

#### 1. **Place Only Deployment Folders in Your Provider Directory**

  Only include deployment folders (no loose files) directly inside your provider directory.

  **Example:**
  ```
  my_provider/
    |- glider_20230701T120000Z/
    |- glider_20230701T120000Z-delayed/
    |- glider_20230815T090000Z/
  ```


#### 2. **Avoid Hidden or Dot-Folders**

  Remove any hidden files or folders (names starting with a dot) before submitting.

  **Example:**
  Remove `.DS_Store`, `.git`, or similar files.



#### 3. **Each Deployment Folder Must Contain at Least One Data File**

  Every deployment folder you submit must include at least one NetCDF data file:
  - Real-time: `glider_yyyymmddTHHMMSSZ.nc`
  - Delayed-mode: `glider_yyyymmddTHHMMSSZ_delayed.nc`

  **Example:**
  ```
  glider_20230701T120000Z/
    |- glider_20230701T120000Z.nc

  glider_20230701T120000Z-delayed/
    |- glider_20230701T120000Z_delayed.nc
  ```



#### 4. **Understand System Files and Correction Files**

- **System files** (`completed.txt`, `dataset.xml`, `deployment.json`, `wmoid.txt`)
  These files are **added by the system after you submit your data**.
  **Do not remove or modify them** if you see them in your folders after submission.

- **Correction file** (`extra_atts.json`)
  Only include this file if you are submitting corrections for a deployment.

  **Example:**
  ```
  glider_20230701T120000Z-delayed/
    |- glider_20230701T120000Z_delayed.nc
    |- extra_atts.json   # Only if corrections are needed
  ```



#### 5. **Use Correct File Naming Conventions**

  - Real-time folders: only real-time `.nc` files (e.g., `glider_20230701T120000Z.nc`)
  - Delayed-mode folders (`-delayed`): only delayed-mode `_delayed.nc` files (e.g., `glider_20230701T120000Z_delayed.nc`)

  **Example:**
  ```
  glider_20230701T120000Z/
    |- glider_20230701T120000Z.nc

  glider_20230701T120000Z-delayed/
    |- glider_20230701T120000Z_delayed.nc
  ```



#### 6. **Pair Real-Time and Delayed-Mode Folders**

  For every real-time deployment folder, include a corresponding delayed-mode folder (with `-delayed` suffix), and vice versa.

  **Example:**
  ```
  my_provider/
    |- glider_20230701T120000Z/
    |- glider_20230701T120000Z-delayed/
  ```



#### 7. **Limit Extra Files**

  Only required data files and, if needed, `extra_atts.json` should be present. Remove unnecessary files.

  **Example:**
  Do **not** include files like `notes.txt`, `backup.zip`, or more than three files of the same non-`.nc` extension.



#### 8. **Use Valid Timestamps in Folder Names**

  Deployment folder names must include a valid timestamp in the format `yyyymmddTHHMMSSZ`.

  **Example:**
  `glider_20230701T120000Z/`
  `glider_20230701T120000Z-delayed/`



#### 9. **Use Years Between 1998 and the Current Year**

  Ensure the year in your folder names is between 1998 and the current year.

  **Example:**
  `glider_20051231T235959Z/` is valid.
  `glider_19970101T000000Z/` is **not** valid.



#### 10. **Review and Fix All Error Messages**

  Check the system periodic notification email for any errors or warnings and follow the guidelines to correct errors and fix your folder.


#### Directory Structure Example

```
my_provider/
  |- glider_20230701T120000Z/
  |     |- glider_20230701T120000Z.nc
  |- glider_20230701T120000Z-delayed/
        |- glider_20230701T120000Z_delayed.nc
        |- extra_atts.json   # Only if corrections are needed
```

_System files (`completed.txt`, `dataset.xml`, `deployment.json`, `wmoid.txt`) will be added by the system after submission. Do not remove them._



**Questions?**
Contact: [glider.dac.support@noaa.gov](mailto:glider.dac.support@noaa.gov)

---

### File Submission Checklist


#### 1. File Naming

- [  ] **File name follows convention:**
  - Real-time: `glider_yyyymmddTHHMMSSZ.nc`
  - Delayed-mode: `glider_yyyymmddTHHMMSSZ_delayed.nc`

| `glider` | `yyyymmddTHHMMSSZ` | `delayed` |
|----------|----------|----------|
| glider name/type | UTC deployment start time ([ISO 8601](https://iso8601.com)) | for delayed-mode files only |



#### 2. Required Global Attributes

- [  ] All required global attributes are present and **populated with meaningful values** (or `" "` if not applicable).
- [  ] **Timestamps** (`date_created`, `date_issued`, `date_modified`) use ISO 8601 format (`YYYY-MM-DDThh:mm:ssZ`).
- [  ] **Institution** and **project** names match NCEI or ROR spelling, if available.
- [  ] **platform_type**: `"Seaglider"`, `"Spray"`, `"Slocum"`, etc.
- [  ] **Conventions** = `"Latest "`[CF Convention](https://cfconventions.org)
- [  ] **Metadata_Conventions** = `"Latest:"` [CF Convention](https://cfconventions.org), [ACDD](http://wiki.esipfed.org/index.php?title=Attribute_Convention_for_Data_Discovery), [IOOS Convention](https://ioos.github.io/conventions-for-observing-asset-identifiers/ioos-assets-v1-0.html), [Glider DAC](https://ioos.github.io/glider-dac/)
- [  ] **format_version** = `"Latest:"` [IOOS_Glider_NetCDF_v2.0.cdl](https://github.com/ioos/glider-dac/tree/gh-pages/_nc/template)
- [  ] **standard_name_vocabulary** = `"Latest:"` [Current Version](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html)
- [  ] **wmo_id** is included and correct (use the [providers' page](https://gliders.ioos.us/providers/) to **Search by WMO ID**)
- [  ] **sea_name** uses [NODC sea names](https://www.nodc.noaa.gov/worlddatacenter/regions.html) table
- [  ] **platform_type**, **platform:id**, **platform:wmo_id** are included and correct



#### 3. Required Variables & Dimensions

- [  ] **Dimensions:**
  - `time`
  - `traj_strlen`
- [  ] **Trajectory variable:**
  - `trajectory(traj_strlen)` with required attributes
- [  ] **Time-series variables** (all with corresponding `_qc` variables):
  - `time`, `lat`, `lon`, `pressure`, `depth`, `temperature`, `conductivity`, `salinity`, `density`
- [  ] **Profile variables** (all with corresponding `_qc` variables):
  - `profile_id`, `profile_time`, `profile_lat`, `profile_lon`, `time_uv`, `lat_uv`, `lon_uv`, `u`, `v`
- [  ] **Container variables:**
  - `platform` (with required attributes)
  - `instrument_ctd` (with as many attributes as possible)



#### 4. Variable Attributes

- [  ] Each variable includes all **required attributes** (e.g., `long_name`, `standard_name`, `units`, `ancillary_variables`, `valid_min`, `valid_max`, `_FillValue`, etc.).
- [  ] All **_qc variables** have correct flag values and meanings.
- [  ] No **missing values** in dimension variables (`time`, `traj_strlen`).
- [  ] All **string attributes** are actually stored as strings.



#### 5. Data Quality
**Before submitting, please check that your netCDF file includes the correct CF standard names, units and the correct naming convention for your QC variables:**

##### 5.1 User Submitted QC Variables
- [  ] Data quality variables have names ending with _qc (_quality control).
- [  ] No data quality variable is named with a prefix 'qartod_'.
- [  ] Data quality variables use the correct flag scheme and values.
- [  ] Data quality variables use attributes to describe qc processing methodology.

##### 5.2 Automated QC For Required Geophysical Variables
- [  ] A valid `standard_name` attribute
    - Temperature: `sea_water_temperature`
    - Conductivity: `sea_water_electrical_conductivity`
    - Density: `sea_water_density`
    - Pressure: `sea_water_pressure`
    - Salinity: `sea_water_practical_salinity`

- [  ] A valid `units` attribute
    - Temperature: `deg_C`
    - Conductivity: `S m-1`
    - Density: `kg m-3`
    - Pressure: `dbar`
    - Salinity: `1`

- [  ] `valid_min` and `valid_max` attributes
    - `valid_min` < `valid_max`

- [  ] Variables intended for quality processing do not contain missing values or consist solely of NaN or fill values

- [  ] Location and time variables:
    - `profile_lat` and `profile_lon` have valid values
    - `time` has valid, No duplicate, ascending timestamps



#### 6. Metadata Consistency

- [  ] All metadata (institution, project, platform, etc.) is consistent with previous submissions and public records.
- [  ] URLs (e.g., `creator_url`, `publisher_url`, `metadata_link`) are valid and up to date.



#### 7. Final Checks

- [  ] File opens without errors in NetCDF tools (e.g., `ncdump`, `Panoply`).
- [  ] All required fields are present and populated.
- [  ] No placeholder values (e.g., `" "`) remain where real values are available.
- [  ] File matches the [template examples](https://github.com/ioos/glider-dac/tree/gh-pages/_nc/template).



#### 8. References & Resources

- [NGDAC NetCDF File Format Version 2 documentation](https://github.com/ioos/glider-dac/tree/gh-pages/_nc/template)
- [NCEI NetCDF Templates](https://www.ncei.noaa.gov/netcdf-templates)
- [NODC Sea Names Table](http://www.nodc.noaa.gov/General/NODC-Archive/seanamelist.txt)
- [NGDAC netCDF File-Format v2.0](https://ioos.github.io/glider-dac/ngdac-netcdf-file-format-version-2.html)
- [CF Conventions](https://cfconventions.org/)
- [IOOS Metadata Profile v1.2](https://ioos.github.io/ioos-metadata/ioos-metadata-profile-v1-2)
- [Ocean Gliders_Format v1.0](https://github.com/OceanGlidersCommunity/OG-format-user-manual/blob/main/OG_Format.adoc)


**Questions?**
Contact: [glider.dac.support@noaa.gov](mailto:glider.dac.support@noaa.gov)

---

## NGDAC QARTOD QC Checklist
How to avoid the common mistakes that prevent the QARTOD QC process to run.

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
Double-check your file against this checklist and examples before submitting to the NGDAC!
If you’re unsure about CF standard names or required metadata, consult the [CF Standard Names Table](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html).

**Questions?**
Contact: [glider.dac.support@noaa.gov](mailto:glider.dac.support@noaa.gov)

---

