---

# What **To Do** When Organizing Folders and Files for Glider Data Submission

Follow this checklist to ensure your provider and deployment directories are organized correctly for automated checks and ingestion.

---

## ✔️ Checklist: How To Organize Your Submission

### 1. **Place Only Deployment Folders in Your Provider Directory**

- **Do:**  
  Only include deployment folders (no loose files) directly inside your provider directory.

  **Example:**
  ```
  my_provider/
    ├── glider_20230701T120000Z/
    ├── glider_20230701T120000Z-delayed/
    └── glider_20230815T090000Z/
  ```

---

### 2. **Avoid Hidden or Dot-Folders**

- **Do:**  
  Remove any hidden files or folders (names starting with a dot) before submitting.

  **Example:**  
  Remove `.DS_Store`, `.git`, or similar files.

---

### 3. **Each Deployment Folder Must Contain at Least One Data File**

- **Do:**  
  Every deployment folder you submit must include at least one NetCDF data file:
  - Real-time: `glider_yyyymmddTHHMMSSZ.nc`
  - Delayed-mode: `glider_yyyymmddTHHMMSSZ_delayed.nc`

  **Example:**
  ```
  glider_20230701T120000Z/
    └── glider_20230701T120000Z.nc

  glider_20230701T120000Z-delayed/
    └── glider_20230701T120000Z_delayed.nc
  ```

---

### 4. **Understand System Files and Correction Files**

- **System files** (`completed.txt`, `dataset.xml`, `deployment.json`, `wmoid.txt`)  
  These files are **added by the system after you submit your data**.  
  **Do not remove or modify them** if you see them in your folders after submission.

- **Correction file** (`extra_atts.json`)  
  Only include this file if you are submitting corrections for a deployment.

  **Example:**
  ```
  glider_20230701T120000Z-delayed/
    ├── glider_20230701T120000Z_delayed.nc
    └── extra_atts.json   # Only if corrections are needed
  ```

---

### 5. **Use Correct File Naming Conventions**

- **Do:**  
  - Real-time folders: only real-time `.nc` files (e.g., `glider_20230701T120000Z.nc`)
  - Delayed-mode folders (`-delayed`): only delayed-mode `.nc` files (e.g., `glider_20230701T120000Z_delayed.nc`)

  **Example:**
  ```
  glider_20230701T120000Z/
    └── glider_20230701T120000Z.nc

  glider_20230701T120000Z-delayed/
    └── glider_20230701T120000Z_delayed.nc
  ```

---

### 6. **Pair Real-Time and Delayed-Mode Folders**

- **Do:**  
  For every real-time deployment folder, include a corresponding delayed-mode folder (with `-delayed` suffix), and vice versa.

  **Example:**
  ```
  my_provider/
    ├── glider_20230701T120000Z/
    └── glider_20230701T120000Z-delayed/
  ```

---

### 7. **Limit Extra Files**

- **Do:**  
  Only required data files and, if needed, `extra_atts.json` should be present. Remove unnecessary files.

  **Example:**  
  Do **not** include files like `notes.txt`, `backup.zip`, or more than three files of the same non-`.nc` extension.

---

### 8. **Use Valid Timestamps in Folder Names**

- **Do:**  
  Deployment folder names must include a valid timestamp in the format `yyyymmddTHHMMSSZ`.

  **Example:**  
  `glider_20230701T120000Z/`  
  `glider_20230701T120000Z-delayed/`

---

### 9. **Use Years Between 1998 and the Current Year**

- **Do:**  
  Ensure the year in your folder names is between 1998 and the current year.

  **Example:**  
  `glider_20051231T235959Z/` is valid.  
  `glider_19970101T000000Z/` is **not** valid.

---

### 10. **Review and Fix All Error Messages**

- **Do:**  
  Check the system periodic notification email for any errors or warnings and follow the guidelines to correct errors and fix your folder.

---

## Directory Structure Example

```
my_provider/
  ├── glider_20230701T120000Z/
  │     └── glider_20230701T120000Z.nc
  └── glider_20230701T120000Z-delayed/
        ├── glider_20230701T120000Z_delayed.nc
        └── extra_atts.json   # Only if corrections are needed
```

_System files (`completed.txt`, `dataset.xml`, `deployment.json`, `wmoid.txt`) will be added by the system after submission. Do not remove them._

---

**Questions?**  
Contact: [glider.dac.support@noaa.gov](mailto:glider.dac.support@noaa.gov)

---
