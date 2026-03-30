'''
allsky_brightnessmap.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module creates brightness maps from camera images by extracting the brightness
component and applying a color scale. It can optionally average multiple frames
before generating the brightness map.
'''
import allsky_shared as s
import os
import cv2
import numpy as np
from collections import deque
from datetime import datetime

metaData = {
    "name": "Brightness Map",
    "description": "Creates brightness maps from camera images with optional frame averaging",
    "module": "allsky_brightnessmap",
    "version": "v1.0.0",    
    "events": [
        "night"
    ],
    "experimental": "false",    
    "arguments":{
        "average_frames": "10",
        "colormap": "jet",
        "save_to_folder": "brightnessmap",
        "enabled": ""
    },
    "argumentdetails": {
        "average_frames": {
            "required": "false",
            "description": "Number of frames to average",
            "help": "Number of frames to average before creating a brightness map. Set to 1 to disable averaging.",
            "tab": "Settings",
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 100,
                "step": 1
            }          
        },
        "colormap": {
            "required": "false",
            "description": "Color Scale",
            "help": "The color scale to apply to the brightness map",
            "tab": "Settings",
            "type": {
                "fieldtype": "select",
                "values": "jet,rainbow,hot,cool,viridis,plasma,inferno,magma,cividis,turbo"
            }                
        },
        "save_to_folder": {
            "required": "false",
            "description": "Output Folder Name",
            "help": "The name of the folder where brightness maps will be saved. Maps are stored in ALLSKY_IMAGES/YYYYMMDD/[folder_name]/ similar to keograms and startrails",
            "tab": "Settings"
        },
        "enabled": {
            "required": "false",
            "description": "Enable Brightness Map",
            "help": "Enable or disable brightness map generation",
            "tab": "Settings",
            "type": {
                "fieldtype": "checkbox"
            }          
        }
    },
    "enabled": "false",
    "changelog": {
        "v1.0.0": [
            {
                "author": "Roman Dvorak",
                "authorurl": "https://github.com/roman-dvorak",
                "changes": "Initial Release"
            }
        ]                              
    }           
}

# Global frame buffer for averaging
frame_buffer = deque(maxlen=100)  # Maximum buffer size

def get_colormap(colormap_name):
    """Convert colormap name to OpenCV colormap constant"""
    colormaps = {
        'jet': cv2.COLORMAP_JET,
        'rainbow': cv2.COLORMAP_RAINBOW,
        'hot': cv2.COLORMAP_HOT,
        'cool': cv2.COLORMAP_COOL,
        'viridis': cv2.COLORMAP_VIRIDIS,
        'plasma': cv2.COLORMAP_PLASMA,
        'inferno': cv2.COLORMAP_INFERNO,
        'magma': cv2.COLORMAP_MAGMA,
        'cividis': cv2.COLORMAP_CIVIDIS,
        'turbo': cv2.COLORMAP_TURBO
    }
    return colormaps.get(colormap_name.lower(), cv2.COLORMAP_JET)

def extract_brightness(image):
    """Extract brightness (luminance) from image"""
    # Convert to grayscale if it's a color image
    if len(image.shape) == 3:
        # OpenCV uses weighted average: 0.299*R + 0.587*G + 0.114*B
        brightness = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        brightness = image
    
    return brightness

def create_brightness_map(brightness_image, colormap):
    """Create a colored brightness map from grayscale brightness"""
    # Apply the colormap
    colored_map = cv2.applyColorMap(brightness_image, colormap)
    return colored_map

def average_frames(frames):
    """Average multiple frames"""
    if len(frames) == 0:
        return None
    
    # Convert to float for averaging
    avg_frame = np.mean(frames, axis=0).astype(np.uint8)
    return avg_frame

def brightnessmap(params, event):
    '''
    Main entry point for the brightness map module.
    
    This module:
    1. Extracts the brightness component from each captured image
    2. Optionally averages multiple frames
    3. Applies a color scale to create a brightness map
    4. Saves the result to a dedicated folder
    '''
    
    result = ""
    
    # Check if enabled (checkbox returns empty string when unchecked)
    enabled = params.get("enabled", "")
    if not enabled:
        return "Brightness map generation is disabled"
    
    try:
        # Get parameters
        average_frames_count = int(params.get("average_frames", 10))
        colormap_name = params.get("colormap", "jet")
        folder_name = params.get("save_to_folder", "brightnessmap")
        
        # Get the colormap
        colormap = get_colormap(colormap_name)
        
        # Get the current image from the shared module
        if s.image is None:
            return "No image available"
        
        current_image = s.image.copy()
        
        # Extract brightness from current image
        brightness = extract_brightness(current_image)
        
        # Add to frame buffer
        global frame_buffer
        frame_buffer.append(brightness)
        
        # Check if we have enough frames to average
        if len(frame_buffer) < average_frames_count:
            result = f"Collecting frames: {len(frame_buffer)}/{average_frames_count}"
            s.log(1, f"INFO: {result}")
            return result
        
        # Get the last N frames for averaging
        frames_to_average = list(frame_buffer)[-average_frames_count:]
        
        # Average the frames
        averaged_brightness = average_frames(frames_to_average)
        
        # Create brightness map
        brightness_map = create_brightness_map(averaged_brightness, colormap)
        
        # Determine output path
        # Follow AllSky convention: save to images/YYYYMMDD/brightnessmap/
        # Similar to how keograms and startrails are saved
        allsky_images = s.getEnvironmentVariable("ALLSKY_IMAGES", fatal=False)
        if not allsky_images:
            # Fallback to ALLSKY_HOME/images
            allsky_home = s.getEnvironmentVariable("ALLSKY_HOME", fatal=False)
            if allsky_home:
                allsky_images = os.path.join(allsky_home, "images")
            else:
                allsky_images = os.path.expanduser("~/allsky/images")
        
        # Create date-based directory structure (YYYYMMDD)
        current_date = datetime.now().strftime("%Y%m%d")
        date_dir = os.path.join(allsky_images, current_date)
        
        # Create brightness map subdirectory
        output_dir = os.path.join(date_dir, folder_name)
        s.checkAndCreateDirectory(output_dir)
        
        # Generate filename with timestamp
        # Use AllSky convention: brightnessmap-YYYYMMDD_HHMMSS.jpg
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"brightnessmap-{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the brightness map
        cv2.imwrite(output_path, brightness_map)
        
        # Also save a "latest" version for easy access
        latest_path = os.path.join(output_dir, "latest.jpg")
        cv2.imwrite(latest_path, brightness_map)
        
        result = f"Brightness map saved to {output_path}"
        s.log(1, f"INFO: {result}")
        
        # Save metadata
        extraData = {
            "AS_BRIGHTNESSMAP_FRAMES_AVERAGED": str(average_frames_count),
            "AS_BRIGHTNESSMAP_COLORMAP": colormap_name,
            "AS_BRIGHTNESSMAP_TIMESTAMP": timestamp,
            "AS_BRIGHTNESSMAP_PATH": output_path
        }
        s.saveExtraData("brightnessmap.json", extraData)
        
    except Exception as e:
        result = f"ERROR: {str(e)}"
        s.log(0, result)
    
    return result

def brightnessmap_cleanup():
    '''Cleanup function for the module'''
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "brightnessmap.json"
            },
            "env": {
                "AS_BRIGHTNESSMAP_FRAMES_AVERAGED",
                "AS_BRIGHTNESSMAP_COLORMAP",
                "AS_BRIGHTNESSMAP_TIMESTAMP",
                "AS_BRIGHTNESSMAP_PATH"
            }
        }
    }
    s.cleanupModule(moduleData)
