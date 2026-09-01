# Changelog

## [1.0.0] - 2026-09-01

### 1. LiDAR Configuration (`config/lidar/lidar.yaml`)
Optimized and restricted the LiDAR's output for better performance and reliability:
- **Network Destination**: The `udp_dest` IP was changed from `192.168.1.111` to `192.168.1.20`.
- **Resolution**: `lidar_mode` was downgraded from `2048x10` to `1024x10` (halving the horizontal resolution).
- **Field of View**: The azimuth window was narrowed. The old package had a 120-degree window (`120000` to `240000`), whereas the new package restricts it to a tighter 90-degree window (`135000` to `225000`).
- **Range**: The `min_range` filter was increased from `0.25m` to `0.5m`.

### 2. URDF / Robot Description (`urdf/sensor_mounts.urdf.xacro`)
- **Simplified Mounting Structure**: The old `raptors_` package had a very complex hardware description for the sensor stack (including `robot_base_front_mount`, `module_base`, `pole_left_link`, `pole_cross_mount_link`, `cross_center_plate_link`, etc.). 
- The new `rover_autonomy` package strips all of this down to a much simpler, hardcoded `mount_link` offset, holding just `sensor_mount_00_link` and `sensor_mount_01_link`.

### 3. Core Architecture & Launch Modes (`mapping.launch.py`, `localization.launch.py`, `main_compute.yaml`)
- **Binary Mode Selection**: The new package uses the highly robust `[LiDAR][Cam0][Cam1]` binary mode logic (e.g., `111`, `110`, `001`) to seamlessly switch between hardware configurations across both mapping and localization.
- **Multi-Camera Workaround**: The new package natively includes the `rgbdx_sync` workaround to support multi-camera mapping (via the `RGBDImages` interface) when the RTAB-Map binary lacks native support. 
- **Formatting**: Minor readability/comment improvements were added to `camera.yaml`.
