""" allsky_sqm.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module calculates Sky Quality Meter (SQM) value from the image

Modified by: Roman Dvorak (roman.dvorak@astrometers.eu)
https://github.com/astroMeters/
"""
import allsky_shared as s
import os
import cv2
import math

metaData = {
    "name": "SQM Calculator",
    "description": "Calculates Sky Quality Meter (SQM) value from the image",
    "module": "allsky_sqm",
    "version": "v1.1.0",    
    "events": [
        "day",
        "night",
        "endofnight",
        "daynight",
        "nightday",
        "periodic"
    ],
    "experimental": "false",    
    "arguments":{
        "roi": "",
        "fallback": "10",
        "calibrationConstant": "20.0",
        "formula": "",
        "maskFilename": "",
        "extradatafilename": "allskysqm.json"
    },
    "argumentdetails": {
        "roi" : {
            "required": "false",
            "description": "Region of Interest",
            "help": "Click on the image to select ROI area for SQM calculation. Leave empty to use fallback percentage.",
            "type": {
                "fieldtype": "roi"
            }
        },
        "fallback" : {
            "required": "false",
            "description": "Fallback Percentage",
            "help": "Percentage of image center to use if ROI is not specified (default: 10%)",
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 100,
                "step": 1
            }
        },
        "calibrationConstant" : {
            "required": "false",
            "description": "Calibration Constant (C)",
            "help": "Calibration constant for SQM calculation: SQM = C - 2.5 * log10(brightness). Typical values: 18-22",
            "type": {
                "fieldtype": "spinner",
                "min": 10,
                "max": 30,
                "step": 0.1
            }
        },
        "formula" : {
            "required": "false",
            "description": "Custom SQM Formula",
            "help": "Custom formula for SQM calculation. Available variables: sqmAvg, weightedSqmAvg, sqmMagArcsec. Leave empty for standard calculation."
        },
        "maskFilename": {
            "required": "false",
            "description": "Mask Filename",
            "help": "Optional mask image filename to apply before SQM calculation"
        },
        "extradatafilename": {
            "required": "false",
            "description": "Extra Data Filename",
            "help": "Name of the file to store extra data"
        }
    },
    "changelog": {
        "v1.1.0" : [
            {
                "author": "Roman Dvorak",
                "authorurl": "https://github.com/astroMeters/",
                "changes": "Added interactive ROI widget, proper SQM mag/arcsec² conversion with calibration constant, exposure/gain weighted brightness calculation, saveExtraData support, support for all time events (day/night/periodic), and custom formula evaluation"
            }
        ],
        "v1.0.0" : [
            {
                "author": "AllSky Team",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ]                              
    }             
}

def sqm(params, event):
    roi = params.get("roi", "")
    fallback = int(params.get("fallback", 10))
    calibrationConstant = float(params.get("calibrationConstant", 20.0))
    formula = params.get("formula", "")
    maskFilename = params.get("maskFilename", "")
    extradatafilename = params.get("extradatafilename", "allskysqm.json")

    result = ""
    image = s.image

    if image is None:
        s.log(0, "ERROR: No image available")
        return "No image available"

    # Convert to grayscale if needed
    if len(image.shape) == 2:
        grayImage = image
    else:
        grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply mask if specified
    if maskFilename != "":
        try:
            imageMask = s.load_mask(maskFilename, image)
            if imageMask is not None:
                if grayImage.shape[:2] == imageMask.shape[:2]:
                    # Ensure mask is in correct format
                    if imageMask.dtype != grayImage.dtype:
                        imageMask = (imageMask * 255).astype(grayImage.dtype)
                    grayImage = cv2.bitwise_and(src1=grayImage, src2=grayImage, mask=imageMask)
                    if s.LOGLEVEL >= 4:
                        s.writeDebugImage(metaData["module"], "masked-image.png", grayImage)
                else:
                    s.log(0, "ERROR: Source image and mask dimensions do not match")
        except Exception as e:
            s.log(0, f"ERROR: Failed to load mask: {e}")

    imageHeight, imageWidth = grayImage.shape[:2]
    
    # Parse ROI or use fallback
    try:
        if roi and len(roi) > 0:
            roiList = roi.split(",")
            x1 = int(roiList[0])
            y1 = int(roiList[1])
            x2 = int(roiList[2])
            y2 = int(roiList[3])
        else:
            raise ValueError("ROI not set")
    except:
        if roi and len(roi) > 0:
            s.log(0, f"ERROR: SQM ROI is invalid, falling back to {fallback}% of image")
        else:
            s.log(1, f"INFO: SQM ROI not set, falling back to {fallback}% of image")
        
        fallbackAdj = (100 / fallback)
        x1 = int((imageWidth / 2) - (imageWidth / fallbackAdj))
        y1 = int((imageHeight / 2) - (imageHeight / fallbackAdj))
        x2 = int((imageWidth / 2) + (imageWidth / fallbackAdj))
        y2 = int((imageHeight / 2) + (imageHeight / fallbackAdj))

    s.log(4, f"INFO: SQM ROI x1 {x1} y1 {y1} x2 {x2} y2 {y2}")

    croppedImage = grayImage[y1:y2, x1:x2]

    if s.LOGLEVEL >= 4:
        s.writeDebugImage(metaData["module"], "cropped-image.png", croppedImage)

    # Get camera settings
    maxExposure_s = s.asfloat(s.getSetting("nightmaxautoexposure")) / 1000
    exposure_s = s.asfloat(s.getEnvironmentVariable("AS_EXPOSURE_US")) / 1000 / 1000
    maxGain = s.asfloat(s.getSetting("nightmaxautogain"))
    gain = s.asfloat(s.getEnvironmentVariable("AS_GAIN"))

    # Calculate brightness values
    sqmAvg = cv2.mean(src=croppedImage)[0]
    weightedSqmAvg = (((maxExposure_s - exposure_s) / 10) + 1) * (sqmAvg * (((maxGain - gain) / 10) + 1))

    # Convert weighted brightness to SQM in mag/arcsec²
    # SQM = C - 2.5 * log10(brightness)
    # Add small value to avoid log(0)
    sqmMagArcsec = calibrationConstant - 2.5 * math.log10(max(weightedSqmAvg, 0.01))

    s.log(1, f"INFO: Brightness avg={sqmAvg:.2f}, weighted={weightedSqmAvg:.2f}, SQM={sqmMagArcsec:.2f} mag/arcsec²")
    
    # Apply custom formula if provided
    if formula and formula != '':
        try:
            # Create namespace for eval with available variables
            eval_namespace = {
                "sqmAvg": sqmAvg,
                "weightedSqmAvg": weightedSqmAvg,
                "sqmMagArcsec": sqmMagArcsec
            }
            sqm_value = float(eval(formula, {"__builtins__": {}}, eval_namespace))
            result = f"SQM calculated as {sqm_value:.2f} mag/arcsec² (custom formula)"
            s.log(1, f"INFO: Ran Formula: {formula}")
            s.log(1, f"INFO: {result}")
        except Exception as e:
            result = f"Error in formula: {str(e)}"
            sqm_value = sqmMagArcsec
            s.log(0, f"ERROR: {result}")
    else:
        sqm_value = sqmMagArcsec
        result = f"SQM calculated as {sqm_value:.2f} mag/arcsec²"

    # Save data using AllSky standard method
    extraData = {}
    extraData["AS_SQM"] = str(round(sqm_value, 2))
    extraData["AS_SQMAVG"] = str(round(sqmAvg, 2))
    extraData["AS_SQMWEIGHTED"] = str(round(weightedSqmAvg, 2))
    s.saveExtraData(extradatafilename, extraData)

    return result

def sqm_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskysqm.json": "s"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
