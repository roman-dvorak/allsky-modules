'''
allsky_amasc01_thermalstatus.py

AllSky module to import thermal status data from AMASC01 thermal control system.
Reads /var/run/thermal-control-status.json and exposes values as AS_AMASC01_* variables
via the Allsky extra data mechanism.

Designed for AstroMeters AMASC01 AllSky Camera
https://astrometers.eu/products/AMASC01/

Author: Roman Dvořák <roman.dvorak@astrometers.eu>
'''

import json
import traceback

import allsky_shared as s


metaData = {
    "name": "AMASC01 Thermal Status",
    "description": "Reads AMASC01 thermal-control-status.json and exposes values as variables.",
    "module": "allsky_amasc01_thermalstatus",
    "version": "v1.0.0",
    "events": [
        "periodic"
    ],
    "experimental": "false",
    "arguments": {
        "jsonfile": "/var/run/thermal-control-status.json",
        "extradatafilename": "amasc01_thermalstatus.json",
        "period": 30
    },
    "argumentdetails": {
        "jsonfile": {
            "required": "true",
            "description": "Thermal status JSON file",
            "help": "Full path to thermal-control-status.json produced by amasc01-supervisor"
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "help": "File to create with AMASC01 thermal data for the overlay manager"
        },
        "period": {
            "required": "false",
            "description": "Read Every",
            "help": "Read data every X seconds. Zero disables throttling (runs every periodic event)",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 3600,
                "step": 5
            }
        }
    },
    "businfo": [],
    "changelog": {
        "v1.0.0": [
            {
                "author": "Roman Dvořák <roman.dvorak@astrometers.eu>",
                "authorurl": "https://astrometers.eu/",
                "changes": "Initial AMASC01 thermal status importer"
            }
        ]
    }
}


# Mapping from JSON keys in thermal-control-status.json to Allsky extra data keys
KEY_MAP = {
    "dome_temp": "AS_AMASC01_DOME_TEMP",
    "body_temp": "AS_AMASC01_BODY_TEMP",
    "envi_temp": "AS_AMASC01_ENVI_TEMP",
    "dome_humidity": "AS_AMASC01_DOME_HUMIDITY",
    "body_humidity": "AS_AMASC01_BODY_HUMIDITY",
    "envi_humidity": "AS_AMASC01_ENVI_HUMIDITY",
    "body_pressure": "AS_AMASC01_BODY_PRESSURE",
    "dome_dew_point": "AS_AMASC01_DOME_DEW_POINT",
    "body_dew_point": "AS_AMASC01_BODY_DEW_POINT",
    "envi_dew_point": "AS_AMASC01_ENVI_DEW_POINT",
    "heater_pwm": "AS_AMASC01_HEATER_PWM",
    "fan_pwm": "AS_AMASC01_FAN_PWM",
    "cpu_fan_state": "AS_AMASC01_CPU_FAN_STATE",
    "target_temp": "AS_AMASC01_TARGET_TEMP",
    "cooling_min": "AS_AMASC01_COOLING_MIN",
    "cooling_max": "AS_AMASC01_COOLING_MAX",
    "fan_override": "AS_AMASC01_FAN_OVERRIDE",
    "error_count": "AS_AMASC01_ERROR_COUNT"
}


def _get_param(params, name, default):
    """Helper to get a parameter with a default."""
    return params[name] if name in params and params[name] != "" else default


def amasc01_thermalstatus(params, event):
    """Entry point called by the Allsky module processor.

    Reads the JSON status file and writes selected values into the extra data file
    as AS_AMASC01_* variables.
    """

    result = ""
    extra_data = {}

    jsonfile = _get_param(params, "jsonfile", metaData["arguments"]["jsonfile"])
    extradatafilename = _get_param(
        params, "extradatafilename", metaData["arguments"]["extradatafilename"]
    )

    # period may be zero (run every periodic event)
    try:
        period = int(_get_param(params, "period", metaData["arguments"]["period"]))
    except (ValueError, TypeError):
        period = metaData["arguments"]["period"]

    if period > 0:
        should_run, diff = s.shouldRun(metaData["module"], period)
        if not should_run:
            result = f"Will run in {(period - diff):.2f} seconds"
            s.log(4, f"INFO: {result}")
            return result

    try:
        # Check readability via shared helper if available
        if hasattr(s, "isFileReadable") and not s.isFileReadable(jsonfile):
            result = f"JSON status file {jsonfile} is not readable"
            s.log(0, f"ERROR: {result}")
            # On error, delete existing extra data so overlays don't show stale data
            if hasattr(s, "deleteExtraData"):
                s.deleteExtraData(extradatafilename)
            return result

        with open(jsonfile, "r") as f:
            data = json.load(f)

        s.log(4, f"INFO: Retrieved thermal status from {jsonfile}: {data}")

        for src_key, dest_key in KEY_MAP.items():
            if src_key in data and data[src_key] is not None:
                # Store everything as string for consistent overlay rendering
                extra_data[dest_key] = str(data[src_key])

        # Always include a small status flag so overlays can easily detect module state
        extra_data["AS_AMASC01_STATUS"] = "OK"

        if hasattr(s, "saveExtraData"):
            s.saveExtraData(extradatafilename, extra_data)
        else:
            s.log(1, f"WARNING: saveExtraData not available, cannot persist {extradatafilename}")

        if hasattr(s, "setLastRun"):
            s.setLastRun(metaData["module"])

        result = "AMASC01 thermal status updated"
    except json.JSONDecodeError as e:
        result = f"Error decoding JSON in {jsonfile}: {e}"
        s.log(0, f"ERROR: {result}")
        if hasattr(s, "deleteExtraData"):
            s.deleteExtraData(extradatafilename)
    except Exception as e:  # pragma: no cover - generic safety net
        tb = traceback.format_exc()
        result = f"Unexpected error reading {jsonfile}: {e}"
        s.log(0, f"ERROR: {result} - traceback: {tb}")
        if hasattr(s, "deleteExtraData"):
            s.deleteExtraData(extradatafilename)

    return result


def amasc01_thermalstatus_cleanup():
    """Cleanup hook used by the Allsky module manager."""

    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                metaData["arguments"]["extradatafilename"],
            },
            "env": {},
        },
    }

    if hasattr(s, "cleanupModule"):
        s.cleanupModule(moduleData)
