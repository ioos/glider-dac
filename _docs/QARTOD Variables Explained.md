
---
title: "GDAC Data Quality Control Process"

Source: Content imported from this [file]( https://docs.google.com/document/d/1T8-bo1-aDNn_PazOdvIAfKmKxYXlM9DH/edit) here.

date: 2026-03-26

author: "Leila Baghdad Brahim"

tags: [gdac, qartod, qc, netcdf, ioos]

draft: True

---

<!-- Filename: 2026-03-26-gdac-data-quality-control-process.md -->
<!-- Assumption: No explicit author/date provided; title inferred from document content. -->

# GDAC Data Quality Control Process

## Table of Contents

- [The Process of Adding QARTOD Variables to the GDAC netCDF Files](#the-process-of-adding-qartod-variables-to-the-gdac-netcdf-files)
  - [Step 1: Inspecting Files](#step-1-inspecting-files)
  - [Step 2: Processing Files](#step-2-processing-files)
  - [Step 3: Creating QARTOD Variables](#step-3-creating-qartod-variables)
  - [Step 5: Set a File Attribute](#step-5-set-a-file-attribute)
- [QARTOD Implementation – An IOOS Example](#qartod-implementation--an-ioos-example)
- [Glider DAC QC Resources](#glider-dac-qc-resources)

The quality control (QC) process is applied to all profile files submitted to the GDAC. Below is an overview of this process and the creation of the quality control data variables, referred to as QARTOD variables.

## The Process of Adding QARTOD Variables to the GDAC netCDF Files

### Step 1: Inspecting Files

The process begins with inspecting the file attributes to determine whether the QC process, which adds the QARTOD variables, has been executed. If the file attribute is set to `TRUE`, no further action is taken. If it is set to `FALSE`, the QC process is initiated, and file processing commences.

### Step 2: Processing Files

The QC process begins by scanning the file for five variables with CF-compliant standard names (see Table 1). Variables with valid standard names are then selected for QC and their `ancillary_variables` attribute (see Note 1) is checked for the presence of variables starting with `qartod_*` (Table 2). If `qartod_*` variables are found under `ancillary_variables`, the QC process moves on to the next variable. If no `qartod_*` variables are found, the QC process continues with further steps.

#### Table 1. Standard Names of Variables to be Checked in the QC Process

| Variables | CF Compliant standard names |
|---|---|
| `temperature` | `sea_water_temperature` |
| `conductivity` | `sea_water_electrical_conductivity` |
| `density` | `sea_water_density` |
| `pressure` | `sea_water_pressure` |
| `salinity` | `sea_water_practical_salinity` |

**Note 1.** The `ancillary_variables` attribute stores individual test variables as a space-separated list of names (see Image 1).

#### Table 2. Representation of two cases of the conductivity variable from different netCDF files, showing the `ancillary_variables` attribute listing QC variables

<table>
  <tr>
    <th>Non-GDAC QC variables<br>(See variable ending with <code>_qc</code>)</th>
    <th>GDAC QC variables<br>(See variables starting with <code>qartod_</code>)</th>
  </tr>
  <tr>
    <td valign="top">

> double conductivity(time=41);  
> :_FillValue = -999.0; // double  
> :accuracy = " ";  
> :ancillary_variables = "conductivity_qc ";  
> :instrument = "instrument_ctd";  
> :long_name = "Conductivity";  
> :observation_type = "measured";  
> :platform = "platform";  
> :precision = " ";  
> :resolution = " ";  
> :standard_name = "sea_water_electrical_conductivity";  
> :units = "S m-1";  
> :valid_max = 10.0f; // float  
> :valid_min = 0.0f; // float

   </td>
    <td valign="top">

> double conductivity(time=41);  
> :_FillValue = -999.0; // double  
> :accuracy = " ";  
> :ancillary_variables = "conductivity_qc qartod_conductivity_gross_range_flag qartod_conductivity_spike_flag qartod_conductivity_rate_of_change_flag qartod_conductivity_primary_flag qartod_conductivity_flat_line_flag";  
> :instrument = "instrument_ctd";  
> :long_name = "Conductivity";  
> :observation_type = "measured";  
> :platform = "platform";  
> :precision = " ";  
> :resolution = " ";  
> :standard_name = "sea_water_electrical_conductivity";  
> :units = "S m-1";  
> :valid_max = 10.0f; // float  
> :valid_min = 0.0f; // float

   </td>
  </tr>
</table>

### Step 3: Creating QARTOD Variables

The QC process then proceeds to create `qartod_*` variables for selected valid variables with valid standard names. It utilizes QC functions from the `ioos_qc` library to generate these variables (see Table 3). For each selected variable, five `qartod_*` variables are added (see Table 3). Each `qartod_*` variable includes QC test results and a list of attributes (see Image 1), as specified by the GDAC QC process. Additionally, the file will have a global attribute, `dac_qc_comment`, which provides a summary of any issues encountered during the creation of the `qartod_*` variables. The types of issues addressed by the QC process are outlined in Table 4.

#### Table 3. QARTOD Variables for the Selected Variable (`%(name)`)

| Test Description | Test Recommendation | Variable Name Syntax |
|---|---|---|
| Location Test | Required | `qartod_location_test_flag` |
| Gross Range Test | Required | `qartod_%(name)s_gross_range_flag` |
| Spike Test | Strongly Recommended | `qartod_%(name)s_spike_flag` |
| Rate of Change Test | Strongly Recommended | `qartod_%(name)s_rate_of_change_flag` |
| Flat Line Test | Strongly Recommended | `qartod_%(name)s_flat_line_flag` |
| Aggregate Quality Flag | Required | `qartod_%(name)s_primary_flag` |

### Image 1. netCDF representation of the conductivity flat line `qartod_*` variable and its attributes

> byte qartod_conductivity_flat_line_flag(time=41);  
> :_FillValue = -999B; // byte  
> :units = "1";  
> :standard_name = "flat_line_test_quality_flag";  
> :long_name = "QARTOD Flat Line Test for sea_water_pressure";  
> :flag_values = 1B, 2B, 3B, 4B, 9B; // byte  
> :valid_min = 1B; // byte  
> :valid_max = 9B; // byte  
> :flag_meanings = "PASS NOT_EVALUATED SUSPECT FAIL MISSING";  
> :references = "https://ioos.noaa.gov/project/qartod/";  
> :qartod_package = "https://github.com/ioos/ioos_qc/blob/main/ioos_qc/qartod.py";  
> :dac_comment = "ioos_qartod";  
> :ioos_category = "Quality";  
> :qartod_test = "'flat_line_test'";  
> :qartod_config = "{'tolerance': 1, 'suspect_threshold': 3600, 'fail_threshold': 9000}";

#### Table 4. Reporting issues encountered during QC processing

| Error Type | Issues Documented under the Global Variable `dac_qc_comment` |
|---|---|
| Variable Error | `'Missing variable, '` |
| Value Error | `'All NaNs, '` |
| Value Error | `'All Fill Values, '` |
| Attribute Error | `'Valid_min and Valid_max are switched, '` |
| Attribute Error | `'Invalid standard name, '` |
| Attribute Error | `'Multiple variables use the same standard name, '` |
| Attribute Error | `'Unable to map standard name to the variable’s unit, '` |
| Attribute Error | `'Unable to convert the variable’s unit, '` |
| Attribute Error | `'Unable to normalize data: unit conversion failed, '` |
| Value Error | `'Unable to calculate the spike_test threshold: the spike_test: fewer valid points, '` |
| Value Error | `'Unable to calculate the rate_of_change_test threshold: fewer valid points, '` |
| Exception Error | `'Unable to read qc test results, '` |
| Exception Error | `'Unable to calculate QC flags, '` |
| Exception Error | `'Unable to check location, '` |
| Value Error | `'Out of range profile_lat and profile_lon, '` |
| Value Error | `'Missing profile_lat and profile_lon, '` |
| Exception Error | `'Unable to check time, '` |
| Value Error | `'Masked timestamps, '` |
| Value Error | `'Start time precedes deployment time, '` |
| Format Error | `'Deployment time not in %Y%m%dT%H%M%S format, '` |
| Value Error | `'Missing deployment start time, '` |
| Value Error | `'Timestamps assigned a value of 0, NaN, or Fill Value, '` |
| Value Error | `'Duplicate timestamps, '` |
| Value Error | `'Out of order timestamps, '` |

### Step 5: Set a File Attribute

The final step in file processing involves returning to the system and updating the file attribute of the already QCed file to `True`. This ensures that the QC process is not triggered again for that file.

## QARTOD Implementation – An IOOS Example

Use the link below to access a reproducible example that demonstrates the application of `ioos_qc` functions to your data file. This example illustrates how QARTOD variable flags are applied and provides step-by-step instructions for plotting these flags on your raw data. By following these instructions, you will be able to visually inspect the QC process and assess the results.

**Link:** [QARTOD Test Example for netCDF](https://ioos.noaa.gov/project/qartod/)

## Glider DAC QC Resources

- **QC Manual**  
  [Manual for QC of Glider Data](https://ioos.noaa.gov/project/qartod/)

- **QC GitHub Repository**  
  [ioos_qc Repository](https://github.com/ioos/ioos_qc)

- **QC QARTOD Tests**  
  [qartod.py](https://github.com/ioos/ioos_qc/blob/main/ioos_qc/qartod.py)

- **QARTOD CF Compliance**  
  [IOOS Metadata Profile v1.2 - Quality Control/QARTOD](https://ioos.github.io/ioos-metadata/ioos-metadata-profile-v1-2.html#quality-controlqartod)

- **QARTOD Examples**  
  [IOOS QARTOD Examples](https://ioos.github.io/ioos_qc/examples.html)
