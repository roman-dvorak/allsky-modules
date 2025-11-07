# Brightness Map Module

## Overview

The Brightness Map module creates visual brightness maps from camera images by extracting the brightness (luminance) component and applying a color scale. This allows for better visualization of brightness distribution across the sky.

## Features

- **Brightness Extraction**: Extracts the luminance component from each captured image using ITU-R BT.601 luma coefficients
- **Frame Averaging**: Optionally averages multiple frames (configurable) to reduce noise and create smoother brightness maps
- **Color Scales**: Supports multiple color maps for visualization:
  - jet (default)
  - rainbow
  - hot
  - cool
  - viridis
  - plasma
  - inferno
  - magma
  - cividis
  - turbo
- **Dedicated Output Folder**: Saves brightness maps to a dedicated folder that can be displayed on the public page
- **Latest Image**: Always maintains a `latest.jpg` file for easy access to the most recent brightness map

## Configuration

### Parameters

| Parameter | Description | Default | Range/Options |
|-----------|-------------|---------|---------------|
| **Enable Brightness Map** | Enable or disable the module | Disabled | Checkbox |
| **Number of frames to average** | How many frames to average before creating a brightness map. Set to 1 to disable averaging. | 10 | 1-100 |
| **Color Scale** | The color scale to apply to the brightness map | jet | jet, rainbow, hot, cool, viridis, plasma, inferno, magma, cividis, turbo |
| **Output Folder Name** | The name of the folder where brightness maps will be saved | brightnessmap | Text |

## Usage

1. Enable the module in the AllSky module manager
2. Configure the number of frames to average (higher values produce smoother results but require more frames)
3. Select your preferred color scale
4. Optionally change the output folder name
5. The module will automatically create brightness maps during night captures

## Output

The module creates:
- Timestamped brightness map files in the format: `brightnessmap-YYYYMMDD_HHMMSS.jpg`
- A `latest.jpg` file that always contains the most recent brightness map
- A `brightnessmap.json` file containing metadata about the brightness map generation

## Output Location

Brightness maps are saved following AllSky conventions (similar to keograms and startrails):

`ALLSKY_IMAGES/YYYYMMDD/[folder_name]/`

For example, with the default settings: `~/allsky/images/20241107/brightnessmap/`

This structure ensures that brightness maps are:
- Organized by date alongside other daily outputs
- Accessible from the AllSky web interface
- Available for display on the public page

## Notes

- The module only runs during night captures (when actual sky images are being taken)
- Frame averaging improves quality but requires collecting enough frames first
- The module uses OpenCV's built-in colormaps for consistent and well-tested color scales
- Each brightness map is saved with a timestamp for historical tracking

## Troubleshooting

If brightness maps are not being generated:
1. Check that the module is enabled
2. Ensure the module is running during night captures
3. Check the AllSky logs for error messages
4. Verify that the output directory has write permissions

## Example Use Cases

1. **Sky Quality Analysis**: Monitor brightness distribution across the sky to identify light pollution patterns
2. **Cloud Detection**: Brightness variations can help identify cloud coverage
3. **Historical Comparison**: Compare brightness maps over time to track changes in sky conditions
4. **Public Display**: Show brightness maps on your public AllSky page for visitors

## Version History

### v1.0.0
- Initial release
- Frame averaging support
- Multiple color scale options
- Dedicated output folder
