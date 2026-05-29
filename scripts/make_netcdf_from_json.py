#!/usr/bin/env python3
"""
Create a NetCDF file from variable JSON files and global attribute JSONs.

Usage:
  python make_netcdf_from_json.py /path/to/variables_dir /path/to/global_attributes_dir output.nc
"""

import datetime
import os
import sys
import json
from pathlib import Path
import numpy as np
from netCDF4 import Dataset, num2date
from datetime import datetime, timezone

from pendulum import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------- Utilities / parser -------
def _format_dt(dt):
    # Try strftime; if dt is a cftime object that doesn't support strftime,
    # fall back to constructing the string from fields.
    try:
        return dt.strftime('%Y%m%dT%H%M%S')
    except Exception:
        try:
            return f"{dt.year:04d}{dt.month:02d}{dt.day:02d}T{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"
        except Exception:
            return str(dt)

def _normalize_dimensions(dims):
    """
    Accepts various JSON dimension specs and returns list of (name, size)
    Accepted formats:
      - [["time", 10], ["lat", 180]]
      - {"time": 10, "lat": 180}
      - [{"name":"time","size":10}, {"name":"lat","size":180}]
    Size can be None, -1, or "unlimited" to indicate unlimited dimension.
    """
    out = []
    if isinstance(dims, dict):
        for k, v in dims.items():
            out.append((str(k), None if v in (None, -1, "unlimited") else int(v)))
    elif isinstance(dims, list):
        for item in dims:
            if isinstance(item, list) and len(item) >= 2:
                out.append((str(item[0]), None if item[1] in (None, -1, "unlimited") else int(item[1])))
            elif isinstance(item, dict):
                name = item.get("name") or item.get("dim") or list(item.keys())[0]
                size = item.get("size") if "size" in item else item.get("length") if "length" in item else None
                out.append((str(name), None if size in (None, -1, "unlimited") else int(size)))
            else:
                # just a name with unknown size -> error upstream (we set None)
                out.append((str(item), None))
    else:
        raise ValueError("Unsupported 'dimensions' JSON structure: must be list or dict")
    return out

def _parse_variable_json(path):
    """
    Parse a JSON file that may describe:
      - a single variable object (dict with "dimensions"/"dtype"/...)
      - a dict mapping varname -> varspec
      - a dict with key "variables": [varspec, ...]
      - a list of variable objects

    Returns: (variables_list, report_dict)
      - variables_list: list of var dicts (same schema as before)
      - report: dict with file, ok, msg, and count of variables parsed
    """
    report = {"file": str(path), "ok": False, "msg": "", "count": 0}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            j = json.load(f)
    except Exception as e:
        report['msg'] = f"Failed to load JSON: {e}"
        return [], report

    vars_out = []
    basename = Path(path).stem

    def parse_one(obj, default_name):
        # same logic as previous parser but returns a single var dict or raises
        if not isinstance(obj, dict):
            raise ValueError("variable entry is not an object/dict")
        name = obj.get("name") or default_name
        dims = _normalize_dimensions(obj.get("dimensions", []))
        dtype_spec = obj.get("dtype", "float32")
        attributes = obj.get("attributes", {}) or {}

        # Data (optional)
        data = None
        if "data" in obj:
            data_arr = np.array(obj["data"])
            if dtype_spec in ("str", "string", "S", "U"):
                data = data_arr.astype('S')
            else:
                data = data_arr.astype(dtype_spec)

            expected_shape = tuple(s for (_, s) in dims if s is not None)
            if expected_shape and data.shape != expected_shape:
                raise ValueError(f"Data shape {data.shape} does not match declared dimensions {expected_shape}")

        # Determine numpy dtype
        if dtype_spec in ("str", "string"):
            if data is not None:
                dtype = data.dtype
            else:
                dtype = np.dtype('S1')
        else:
            try:
                dtype = np.dtype(dtype_spec)
            except Exception as e:
                raise ValueError(f"Invalid dtype '{dtype_spec}': {e}")

        fill_value = attributes.get("_FillValue", None)
        return {
            "name": name,
            "dims": dims,
            "dtype": dtype,
            "attributes": attributes,
            "data": data,
            "fill_value": fill_value
        }

    try:
        # Case: top-level object with "variables" list
        if isinstance(j, dict) and "variables" in j and isinstance(j["variables"], list):
            for i, obj in enumerate(j["variables"]):
                default_name = f"{basename}_{i}"
                vars_out.append(parse_one(obj, default_name))

        # Case: top-level mapping varname -> spec
        elif isinstance(j, dict) and not any(k in j for k in ("dimensions", "dtype", "data", "attributes")):
            # assume mapping varname->varspec
            for k, obj in j.items():
                if not isinstance(obj, dict):
                    # skip non-dict entries (or raise)
                    continue
                obj_with_name = dict(obj)
                obj_with_name.setdefault("name", k)
                vars_out.append(parse_one(obj_with_name, k))

        # Case: single variable object (legacy)
        elif isinstance(j, dict) and any(k in j for k in ("dimensions", "dtype", "data", "attributes")):
            vars_out.append(parse_one(j, basename))

        # Case: top-level list of variable objects
        elif isinstance(j, list):
            for i, obj in enumerate(j):
                default_name = f"{basename}_{i}"
                vars_out.append(parse_one(obj, default_name))

        else:
            raise ValueError("Unrecognized JSON structure for variable definitions")

    except Exception as e:
        report['msg'] = f"Failed parsing variables in file: {e}"
        return [], report

    report['ok'] = True
    report['msg'] = "Parsed OK"
    report['count'] = len(vars_out)
    return vars_out, report


def _read_all_variable_files(vars_dir, parallel=True, max_workers=8):
    """
    Read and parse all JSON files in vars_dir.
    Returns (variables_list, reports_list)
    """
    p = Path(vars_dir)
    files = sorted([f for f in p.iterdir() if f.is_file() and f.suffix.lower() == '.json'])
    variables = []
    reports = []
    if parallel and files:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_parse_variable_json, f): f for f in files}
            for fut in as_completed(futures):
                vars_from_file, rep = fut.result()
                if vars_from_file:
                    variables.extend(vars_from_file)
                reports.append(rep)
    else:
        for f in files:
            vars_from_file, rep = _parse_variable_json(f)
            if vars_from_file:
                variables.extend(vars_from_file)
            reports.append(rep)
    return variables, reports

def _read_global_attributes(gattrs_dir):
    """
    Read JSON files from global attributes dir and merge them; last key wins.
    """
    p = Path(gattrs_dir)
    if not p.exists():
        return {}
    gattrs = {}
    for f in sorted([f for f in p.iterdir() if f.is_file() and f.suffix.lower() == '.json']):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                j = json.load(fh)
            if not isinstance(j, dict):
                continue
            gattrs.update(j)
        except Exception:
            continue
    return gattrs

# ------- Main builder -------
def build_netcdf(output_path, vars_dir, global_attrs_dir=None, parallel_parse=True, max_workers=8):
    """
    Main entrypoint.
    Returns a report dict with per-variable parse status and final write status.
    """
    variables, parse_reports = _read_all_variable_files(vars_dir, parallel=parallel_parse, max_workers=max_workers)
    gattrs = _read_global_attributes(global_attrs_dir) if global_attrs_dir else {}

    # Collect dimensions: ensure consistent sizes if repeated
    dim_registry = {}  # name -> size (None means unlimited)
    for v in variables:
        for (dname, dsize) in v['dims']:
            if dname in dim_registry:
                existing = dim_registry[dname]
                # If both specified and not equal -> error
                if existing is not None and dsize is not None and existing != dsize:
                    # Report error in parse_reports and abort write
                    msg = f"Dimension size mismatch for '{dname}': {existing} vs {dsize}"
                    parse_reports.append({"file": "dimension_check", "ok": False, "msg": msg})
                    return {
                        "ok": False,
                        "msg": msg,
                        "parse_reports": parse_reports
                    }
                # otherwise keep the non-None
                if existing is None and dsize is not None:
                    dim_registry[dname] = dsize
            else:
                dim_registry[dname] = dsize

    # Create netCDF and write
    try:
        ds = Dataset(output_path, "w", format="NETCDF4")
    except Exception as e:
        return {"ok": False, "msg": f"Failed to open output file for writing: {e}", "parse_reports": parse_reports}

    # Create dimensions
    for dname, dsize in dim_registry.items():
        try:
            if dsize is None:
                ds.createDimension(dname, None)  # unlimited
            else:
                ds.createDimension(dname, int(dsize))
        except Exception as e:
            ds.close()
            return {"ok": False, "msg": f"Failed to create dimension {dname}: {e}", "parse_reports": parse_reports}

    # Set global attributes
    for k, v in (gattrs.items() if isinstance(gattrs, dict) else []):
        try:
            setattr(ds, k, v)
        except Exception:
            # ignore attributes that cannot be set
            pass

    # Create variables
    var_reports = []
    for v in variables:
        vname = v["name"]
        dim_names = [dn for (dn, _) in v["dims"]]
        try:
            # Special handling for string typed numpy dtype: pass the dtype object
            ncvar = ds.createVariable(vname, v["dtype"], tuple(dim_names), fill_value=v.get("_FillValue", None))
        except Exception as e:
            var_reports.append({"name": vname, "ok": False, "msg": f"Failed to create variable: {e}"})
            continue

        # Write data if present
        if v["data"] is not None:
            try:
                ncvar[...] = v["data"]
            except Exception as e:
                var_reports.append({"name": vname, "ok": False, "msg": f"Failed to write data: {e}"})
                continue

        # Set variable attributes
        for ak, av in v["attributes"].items():
            try:
                ncvar.setncattr(ak, av)
            except Exception:
                # ignore attributes that fail (e.g., complex types)
                pass

        var_reports.append({"name": vname, "ok": True, "msg": "Created OK"})

    # 1) Set time coverage globals if numeric time exists
    # tvar is the netCDF variable object (e.g., ds.variables['time'])
    # find time variable name present
    name = None
    varnames=('time','TIME')
    for n in varnames:
        if n in ds.variables:
            name = n
            break
    if name is None:
        return False

    tvar = ds.variables[name]
    tdata = tvar[:]  # read data (may be masked array)

    # Convert masked values to nan and ensure numeric array
    if hasattr(tdata, 'mask'):
        numeric = np.ma.filled(tdata, np.nan).astype('float64')
    else:
        numeric = np.array(tdata, dtype='float64')

    # Ensure there are valid numeric times
    if numeric.size == 0 or np.all(np.isnan(numeric)):
        # no valid times — don't set globals (or set to empty / skip)
        pass
    else:
        tmin = float(np.nanmin(numeric))
        tmax = float(np.nanmax(numeric))

        units = getattr(tvar, 'units', None)
        calendar = getattr(tvar, 'calendar', 'gregorian')

        # Convert numeric CF times to datetime/cftime objects if units present,
        # otherwise assume epoch seconds (UTC)
        if units:
            dt_min = num2date(tmin, units, calendar=calendar)
            dt_max = num2date(tmax, units, calendar=calendar)
        else:
            dt_min = datetime.fromtimestamp(tmin, tz=timezone.utc)
            dt_max = datetime.fromtimestamp(tmax, tz=timezone.utc)

        # Format and assign globals
        ds.time_coverage_start = _format_dt(dt_min)
        ds.time_coverage_end   = _format_dt(dt_max)


    # 2) Set vertical geospatial globals if depth exists
    if 'depth' in ds.variables:
        z = ds.variables['depth'][:]
        if z.size > 0:
            ds.geospatial_vertical_min = float(np.nanmin(z))
            ds.geospatial_vertical_max = float(np.nanmax(z))


    ds.close()
    return {"ok": True, "msg": "NetCDF file created", "output": str(output_path),
            "parse_reports": parse_reports, "variable_reports": var_reports}

# ------- CLI -------
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python make_netcdf_from_json.py /path/to/variables_dir /path/to/global_attributes_dir output.nc")
        sys.exit(2)
    vars_dir = sys.argv[1]
    gattrs_dir = sys.argv[2]
    out = sys.argv[3]
    report = build_netcdf(out, vars_dir, gattrs_dir, parallel_parse=True, max_workers=8)
    print(json.dumps(report, indent=2))
