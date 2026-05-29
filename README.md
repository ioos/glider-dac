# **Glider Data Template Repository**

> This repository provides modular JSON templates for glider NetCDF data products. Global metadata are stored separately from variable definitions to support clarity, reuse, and maintainability.

This repository contains a structured set of JSON template files for assembling glider data products into a NetCDF-compatible format. The templates are organized by metadata function so that global attributes, platform information, deployment details, trajectory identifiers, profile summaries, time-series observations, QC variables, and derived products can be maintained independently while still supporting a consistent final dataset.

The repository is intended to support a workflow in which JSON definitions are read, validated, and combined into a NetCDF file suitable for operational use, data exchange, and archive-ready submission. The included Python builder script reads all `.json` files, applies the metadata definitions, and generates the final output.

---

## **Table of Contents**
1. **Overview**
2. **Repository Structure**
3. **Global Attributes**
4. **Variable Template Files**
5. **NetCDF Builder Script**
6. **Quality Control Convention**
7. **Repository Standards**
8. **Extending the Repository**
9. **Suggested Repository Opening Statement**

---

## **1. Overview**

This repository provides modular, standards-aligned JSON templates for glider data products. The templates are grouped by function to improve readability, maintainability, and reuse.

The design supports:
- separation of global metadata from variable definitions,
- clear organization of deployment and platform metadata,
- consistent handling of quality control fields,
- and simplified generation of NetCDF files from JSON inputs.

---

## **2. Repository Structure**

The repository contains three major content types:

1. **Global attribute definitions**
   - `global_attributes.json`

2. **Variable template definitions**
   - files named `*_var.json`

3. **NetCDF generation script**
   - `make_netcdf_from_json.py`

Each file group serves a specific role in the creation of a complete glider dataset.

---

## **3. Global Attributes**

### **File**
- `global_attributes.json`

### **Purpose**
This file defines the global metadata used to describe the dataset as a whole. These attributes support discovery, provenance, cataloging, and archive readiness.

### **Common metadata categories**
- dataset identification
- platform and instrument references
- geospatial and temporal coverage
- project, program, and institution metadata
- processing and QC information
- publication, licensing, and contact details

### **Representative fields**
| Field | Meaning |
|---|---|
| `title` | Human-readable dataset title |
| `id` | Unique dataset identifier |
| `institution` | Organization responsible for the data |
| `platform` | Platform identifier |
| `platform_type` | Glider type |
| `wmo_id` | WMO identifier for the platform |
| `project` | Project under which the data were collected |
| `summary` | Dataset abstract |
| `Conventions` | Metadata conventions followed |
| `format_version` | NetCDF/IOOS format designation |
| `standard_name_vocabulary` | CF standard name table version |

### **Formatting expectations**
- Global attributes should be used consistently across related files.
- Timestamp values should follow ISO 8601 extended format where required.
- String values should be meaningful and stable across deployments.
- Where the standard permits, a blank string may be used if no meaningful value exists.

---

## **4. Variable Template Files**

The repository includes modular `*_var.json` files, each representing a logical variable group.

### **4.1 `001_coordinates_var.json`**
Defines the core time-series coordinates and associated QC fields.

**Variables**
- `time`
- `TIME_QC`
- `LONGITUDE`
- `LONGITUDE_QC`
- `LATITUDE`
- `LATITUDE_QC`
- `DEPTH`
- `DEPTH_QC`

**Use**
This file is used for the main time-series coordinate axis and corresponding quality flags.

---

### **4.2 `002_gps_var.json`**
Defines GPS-derived timing and position fields.

**Variables**
- `TIME_GPS`
- `TIME_GPS_QC`
- `LONGITUDE_GPS`
- `LONGITUDE_GPS_QC`
- `LATITUDE_GPS`
- `LATITUDE_GPS_QC`

**Use**
Use this module for GPS fixes and their quality-control companions.

---

### **4.3 `003_trajectory_var.json`**
Defines the trajectory identifier.

**Variable**
- `TRAJECTORY`

**Use**
This variable identifies the deployment or mission trajectory.

---

### **4.4 `004_platform_var.json`**
Defines platform metadata.

**Variables**
- `WMO_IDENTIFIER`
- `PLATFORM_MODEL`
- `PLATFORM_SERIAL_NUMBER`
- `PLATFORM_NAME`
- `PLATFORM_DEPTH_RATING`
- `ICES_CODE`
- `PLATFORM_MAKER`
- `PLATFORM`

**Use**
Use this file to document the glider platform, manufacturer, model, serial number, and mission-specific platform metadata.

---

### **4.5 `005_deployment_var.json`**
Defines deployment metadata.

**Variables**
- `DEPLOYMENT_TIME`
- `DEPLOYMENT_LATITUDE`
- `DEPLOYMENT_LONGITUDE`
- `DEPLOYMENT_DEPTH`

**Use**
Use this file to capture the time and location of deployment.

---

### **4.6 `006_field_comparison_var.json`**
Defines references for field comparison or supplementary validation data.

**Variable**
- `FIELD_COMPARISON_REFERENCE`

**Use**
Use this file for external references, links, or supporting comparison datasets.

---

### **4.7 `007_hardware_var.json`**
Defines hardware and mission equipment metadata.

**Variables**
- `GLIDER_FIRMWARE_VERSION`
- `LANDSTATION_VERSION`
- `BATTERY_TYPE`
- `BATTERY_PACK`

**Use**
Use this file to document hardware configuration, firmware, and battery information.

---

### **4.8 `008_telecom_var.json`**
Defines telecommunications and tracking metadata.

**Variables**
- `TELECOM_TYPE`
- `TRACKING_SYSTEM`

**Use**
Use this file to describe telemetry and tracking systems used by the glider.

---

### **4.9 `009_phase_var.json`**
Defines glider phase and mission segment metadata.

**Variables**
- `PHASE`
- `PHASE_QC`
- `SEGMENT_NUMBER`
- `PROFILE_NUMBER`
- `PROFILE_DIRECTION`

**Use**
Use this file to represent operating phase, segment structure, profile numbering, and direction.

---

### **4.10 `010_sensors_var.json`**
Defines sensor metadata.

**Variable**
- `SENSOR_CTD_206523`

**Use**
Use this file to describe an onboard sensor and its associated calibration/provenance details.

---

### **4.11 `011_geophysical_var.json`**
Defines the primary geophysical observation variables.

**Variables**
- `PRESSURE`
- `PRESSURE_QC`
- `TEMPERATURE`
- `TEMPERATURE_QC`
- `CNDC`
- `CNDC_QC`
- `DENSITY`
- `DENSITY_QC`

**Use**
Use this file for the main science measurements and their QC flags.

---

### **4.12 `012_avg_segment_current_var.json`**
Defines depth-averaged current variables.

**Variables**
- `U`
- `V`
- `TIME_UV`
- `LAT_UV`
- `LON_UV`

**Use**
Use this file for calculated current estimates and associated summary metadata.

---

### **4.13 `013_profile_var.json`**
Defines profile-level summary variables.

**Variables**
- `PROFILE_ID`
- `PROFILE_TIME`
- `PROFILE_TIME_QC`
- `PROFILE_LATITUDE`
- `PROFILE_LATITUDE_QC`
- `PROFILE_LONGITUDE`
- `PROFILE_LONGITUDE_QC`

**Use**
Use this file to store one record per profile, including profile midpoint time and location.

---

## **5. NetCDF Builder Script**

### **File**
- `make_netcdf_from_json.py`

### **Purpose**
This Python script reads all `.json` files in the specified variable directory, parses the variable definitions, merges global attributes, and writes the result to a NetCDF file.

### **Main behavior**
The script is designed to:
- read all JSON variable template files in a directory,
- normalize dimension specifications,
- validate variable data shapes when explicit data are present,
- merge global attributes from the global-attribute JSON directory,
- create NetCDF dimensions,
- and write variables and metadata to the output file.

### **Usage**
```bash
python make_netcdf_from_json.py /path/to/variables_dir /path/to/global_attributes_dir output.nc
```

### **Implementation note**
Because the script reads all `.json` files in the target directory, file organization is important. The directory should contain only the JSON inputs intended for NetCDF assembly.

---

## **6. Quality Control Convention**

QC variables indicate the quality status of their associated data variables.

### **Standard QC meanings**
| Flag | Meaning |
|---|---|
| 0 | no_qc_performed |
| 1 | good_data |
| 2 | probably_good_data |
| 3 | bad_data_that_are_potentially_correctable |
| 4 | bad_data |
| 5 | value_changed |
| 6 | not_used |
| 7 | not_used |
| 8 | interpolated_value |
| 9 | missing_value |

### **Guidance**
- QC variables should match the dimensions of the parent variable.
- QC variables should follow a consistent naming pattern, typically `<VARIABLE>_QC`.
- `ancillary_variables` should be used where applicable.
- QC metadata should clearly describe the flag relationship to the parent variable.

---

## **7. Repository Standards**

To keep the repository reusable and consistent:

### **Naming**
- Use uppercase variable names.
- Use clear, descriptive file names.
- Keep one logical metadata group per JSON file.

### **Metadata consistency**
- Use CF-style metadata where appropriate.
- Preserve data types, units, and fill values exactly as defined.
- Use consistent `long_name`, `standard_name`, and `comment` fields.

### **Documentation**
Each file should be documented in this README with:
- purpose,
- included variables,
- intended use,
- and any special notes on dimensions, values, or QC behavior.

---

## **8. Extending the Repository**

When adding a new template or metadata module:

1. Create a new JSON file for the logical variable group.
2. Define dimensions and data types explicitly.
3. Include attributes for each variable.
4. Add QC fields when the data require quality assessment.
5. Update this README with a description of the new file.
6. Confirm compatibility with the NetCDF builder script.

### **Suggested naming pattern**
- `014_bio_var.json`
- `015_chemistry_var.json`
- `016_navigation_var.json`
