
# Glider DAC NetCDF File Submission Checklist

**Use this checklist to verify your file is ready for submission to the NGDAC.**

---

## Table of Contents

1. [File Naming](#file-naming)
2. [Required Global Attributes](#required-global-attributes)
3. [Required Variables & Dimensions](#required-variables--dimensions)
4. [Variable Attributes](#variable-attributes)
5. [Data Quality](#data-quality)
6. [Metadata Consistency](#metadata-consistency)
7. [Final Checks](#final-checks)
8. [References & Resources](#references--resources)

---

## 1. File Naming

- [ ] **File name follows convention:**  
  - Real-time: `glider_yyyymmddTHHMMSSZ.nc`
  - Delayed-mode: `glider_yyyymmddTHHMMSSZ_delayed.nc`
- [ ] `glider` = glider name/type;  
  `yyyymmddTHHMMSSZ` = UTC start time (ISO 8601);  
  `delayed` = for delayed-mode files only

---

## 2. Required Global Attributes

- [ ] All required global attributes are present and **populated with meaningful values** (or `" "` if not applicable).
- [ ] **Timestamps** (`date_created`, `date_issued`, `date_modified`) use ISO 8601 format (`YYYY-MM-DDThh:mm:ssZ`).
- [ ] **Institution** and **project** names match NCEI or ROR spelling, if available.
- [ ] **platform_type**: `"Seaglider"`, `"Spray"`, `"Slocum"`, etc.
- [ ] **Conventions** = `"Latest: CF-1.10"`
- [ ] **Metadata_Conventions** = `"Latest: CF-1.10, , ACDD v1.3, IOOS v1.2, Glider DAC v3.0"`
- [ ] **format_version** = `"IOOS_Glider_NetCDF_v2.0.nc"`
- [ ] **standard_name_vocabulary** is specified (e.g., `"Latest: Version 93, 17 March 2026)"`)
- [ ] **wmo_id** is included and correct (as assigned by NGDAC)
- [ ] **sea_name** uses NODC sea names table
- [ ] **platform_type**, **platform:id**, **platform:wmo_id** are included and correct

---

## 3. Required Variables & Dimensions

- [ ] **Dimensions:**  
  - `time`  
  - `traj_strlen`
- [ ] **Trajectory variable:**  
  - `trajectory(traj_strlen)` with required attributes
- [ ] **Time-series variables** (all with corresponding `_qc` variables):  
  - `time`, `lat`, `lon`, `pressure`, `depth`, `temperature`, `conductivity`, `salinity`, `density`
- [ ] **Profile variables** (all with corresponding `_qc` variables):  
  - `profile_id`, `profile_time`, `profile_lat`, `profile_lon`, `time_uv`, `lat_uv`, `lon_uv`, `u`, `v`
- [ ] **Container variables:**  
  - `platform` (with required attributes)  
  - `instrument_ctd` (with as many attributes as possible)

---

## 4. Variable Attributes

- [ ] Each variable includes all **required attributes** (e.g., `long_name`, `standard_name`, `units`, `ancillary_variables`, `valid_min`, `valid_max`, `_FillValue`, etc.).
- [ ] All **_qc variables** have correct flag values and meanings.
- [ ] No **missing values** in dimension variables (`time`, `traj_strlen`).
- [ ] All **string attributes** are actually stored as strings.

---

## 5. Data Quality
**Before submitting, please check that your netCDF file includes the correct CF standard names, units and the correct naming convention for your QC variables:**

### 5.1 User Submitted QC Variables
- [ ] Data quality variables have names ending with _qc (_quality control).
- [ ] No data quality variable is named with a prefix 'qartod_'.
- [ ] Data quality variables use the correct flag scheme and values.
- [ ] Data quality variables use attributes to describe qc processing methodology.


### 5.2 Automated QC For Required Geophysical Variables
- [ ] A valid `standard_name` attribute
    - Temperature: `sea_water_temperature`
    - Conductivity: `sea_water_electrical_conductivity`
    - Density: `sea_water_density`
    - Pressure: `sea_water_pressure`
    - Salinity: `sea_water_practical_salinity`
    
- [ ] A valid `units` attribute
    - Temperature: `deg_C`
    - Conductivity: `S m-1`
    - Density: `kg m-3`
    - Pressure: `dbar`
    - Salinity: `1`

- [ ] `valid_min` and `valid_max` attributes
    - `valid_min` < `valid_max`
    
- [ ] Variables intended for quality processing do not contain missing values or consist solely of NaN or fill values
 
- [ ] Location and time variables:
    - `profile_lat` and `profile_lon` have valid values
    - `time` has valid, No duplicate, ascending timestamps

---

## 6. Metadata Consistency

- [ ] All metadata (institution, project, platform, etc.) is consistent with previous submissions and public records.
- [ ] URLs (e.g., `creator_url`, `publisher_url`, `metadata_link`) are valid and up to date.

---

## 7. Final Checks

- [ ] File opens without errors in NetCDF tools (e.g., `ncdump`, `Panoply`).
- [ ] All required fields are present and populated.
- [ ] No placeholder values (e.g., `" "`) remain where real values are available.
- [ ] File matches the [template examples](https://github.com/ioos/glider-dac/tree/gh-pages/_nc/template).

---

## 8. References & Resources

- [NGDAC NetCDF File Format Version 2 documentation](https://github.com/ioos/glider-dac/tree/gh-pages/_nc/template)
- [NCEI NetCDF Templates](https://www.ncei.noaa.gov/netcdf-templates)
- [NODC Sea Names Table](http://www.nodc.noaa.gov/General/NODC-Archive/seanamelist.txt)
- [NGDAC netCDF File-Format v2.0](https://ioos.github.io/glider-dac/ngdac-netcdf-file-format-version-2.html)
- [CF Conventions](https://cfconventions.org/)
- [IOOS Metadata Profile v1.2](https://ioos.github.io/ioos-metadata/ioos-metadata-profile-v1-2)
- [Ocean Gliders_Format v1.0](https://github.com/OceanGlidersCommunity/OG-format-user-manual/blob/main/OG_Format.adoc)
---

**Ready to submit?**  
If all boxes are checked, your file should be compliant and ready for NGDAC submission!
