---
title: "What Happens to Your netCDF File: QARTOD QC at GDAC"
date: 2026-04-17
author: "GDAC Data Team"
tags: [user-guide, netcdf, qartod, qc, submission]
---

# What Happens to Your netCDF File When You Submit to GDAC

Thank you for submitting your netCDF file to the Glider Data Assembly Center (GDAC)!  
This document explains what happens to your file during the automated Quality Control (QC) process, what new data you’ll see in your file, and what you need to check before submission.

---

## Table of Contents

- [What is QARTOD QC?](#what-is-qartod-qc)
- [What Happens to My File?](#what-happens-to-my-file)
- [What Will I See in My File After QC?](#what-will-i-see-in-my-file-after-qc)
- [What Do I Need in My File for QC to Work?](#what-do-i-need-in-my-file-for-qc-to-work)
- [What if There Are Issues?](#what-if-there-are-issues)
- [Resources](#resources)

---

## What is QARTOD QC?

QARTOD (Quality Assurance/Quality Control of Real-Time Oceanographic Data) is a set of standardized tests developed by IOOS to automatically check the quality of ocean data.  
At GDAC, these tests are run on all submitted netCDF profile files to help ensure your data is reliable and well-documented.

---

## What Happens to My File?

When you submit your netCDF file, the following happens automatically:

1. **File is checked for required variables and metadata.**
2. **QARTOD QC tests are run** on key geophysical variables (like temperature, salinity, pressure, etc.).
3. **New variables are added** to your file, showing the results of each QC test.
4. **A summary of any issues or errors** is recorded in a global attribute in your file.
5. **A file attribute is set** so the system knows QC has been completed.

---

## What Will I See in My File After QC?

After QC, your netCDF file will include:

- **New variables** for each geophysical variable tested.  
  For example, if you have a variable called `temperature`, you’ll see:
    - `qartod_temperature_gross_range_flag`
    - `qartod_temperature_spike_flag`
    - `qartod_temperature_rate_of_change_flag`
    - `qartod_temperature_flat_line_flag`
    - `qartod_temperature_primary_flag`
- **A location test variable**:  
    - `qartod_location_test_flag` (checks if your profile’s location is within a reasonable range)
- **Updated `ancillary_variables` attributes** on the original variables, listing the new QC variables.
- **A global attribute** called `dac_qc_comment` summarizing any issues found during QC.


> ### Important Note:
> The dac_qc_comment global attribute shown in ERDDAP for your deployment only reflects the most recent file processed. It does not show QC issues for every individual file submitted.

**Example:**

```text
double temperature(time=41);
  :ancillary_variables = "temperature_qc qartod_temperature_gross_range_flag qartod_temperature_spike_flag qartod_temperature_rate_of_change_flag qartod_temperature_primary_flag qartod_temperature_flat_line_flag";
  ...
byte qartod_temperature_gross_range_flag(time=41);
  :long_name = "QARTOD Gross Range Test for sea_water_temperature";
  :flag_meanings = "PASS NOT_EVALUATED SUSPECT FAIL MISSING";
  ...
```
---
## What Do I Need in My File for QC to Work?

**Before submitting, please check that your netCDF file includes:**

- **Required geophysical variables** with correct CF standard names and units:
    - `sea_water_temperature`
    - `sea_water_electrical_conductivity`
    - `sea_water_density`
    - `sea_water_pressure`
    - `sea_water_practical_salinity`
    
- **Each variable should have:**
    - A valid `standard_name` attribute (see above)
    - A valid `units` attribute (e.g., `deg_C`, `dbar`, `S m-1`, `1`, `kg m-3`)
    - `valid_min` and `valid_max` attributes (with `valid_min` < `valid_max`)
    - No missing or all-NaN/all-fill-value data
 
- **Location and time variables:**
    - `profile_lat` and `profile_lon` (with valid values)
    - `time` (with valid, ascending timestamps)
    
- **No duplicate or out-of-order timestamps**

**Tip:**  
If your file is missing any of these, QC may fail or skip those variables.

---

## What if There Are Issues?

- If QC finds problems, a summary will appear in the `dac_qc_comment` global attribute in your file.
- If a variable is missing required metadata or has invalid data, QC tests for that variable will be skipped and noted in the comment.
- If the entire file cannot be QCed, the file attribute `user.qc_run` will be set to `"error"`.

**If you have questions or see errors in your file after submission, contact the GDAC team for help!**

---

## Resources

- [Manual for QC of Glider Data (QARTOD)](https://ioos.noaa.gov/project/qartod/)
- [CF Standard Names Table](http://cfconventions.org/standard-names.html)
- [IOOS QARTOD Examples](https://ioos.github.io/ioos_qc/examples.html)
- [Contact GDAC Support](mailto:your-support-email@domain.org)

---
