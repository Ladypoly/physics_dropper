# Physics Dropper

> Easy rigidbody and cloth physics simulation setup with enhanced stability

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/yourusername/physics_dropper)
[![Blender](https://img.shields.io/badge/Blender-4.2--5.0-orange.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)

Physics Dropper is a comprehensive Blender extension that streamlines physics simulation setup for both rigid body and cloth simulations. With an intuitive interface, interactive force fields, and powerful baking tools, it makes complex physics accessible to everyone.

## Features

### Rigid Body Physics
- **Quick Setup**: Apply active or passive rigid body physics with one click
- **Multiple Collision Shapes**: Convex Hull, Mesh, Box, Sphere, Capsule, Cylinder, Cone, and Compound
- **Fine-Tuned Control**: Adjust mass, friction, bounciness, damping, and collision margins
- **High-Poly Optimization**: Automatic proxy creation using voxel remeshing or decimation for better performance

### Cloth Simulation
- **Material Presets**: Pre-configured settings for Cotton, Denim, Leather, Rubber, and Silk
- **Comprehensive Controls**: Full control over stiffness (tension, compression, shear, bending)
- **Advanced Features**:
  - Internal springs for soft body-like behavior
  - Pressure effects for inflatable objects
  - Self-collision detection with adjustable friction
  - Air viscosity and quality settings

### Interactive Force Fields
- **Simple Force**: Add static force fields at object locations
- **Modal Force Mode (F key)**: Real-time interactive force field placement
  - Move mouse to position force in 3D space
  - Scroll wheel to adjust force radius
  - **Ctrl+Click** for surface snapping via raycast
  - Visual sphere display showing force area
- **Customizable**: Adjust strength (-1000 to 1000), distance, and air flow

### Earthquake Effects
- **Dynamic World Shake**: Add procedural earthquake motion to all active physics objects
- **Axis Control**: Enable/disable X, Y, Z axes independently
- **Adjustable Intensity**: 0-100% strength for subtle to extreme effects
- **Non-Destructive**: Uses F-curve noise modifiers for easy editing

### Baking System
- **Smart Baking**: Convert physics simulation to keyframes efficiently
  - Only bakes up to current timeline position
  - Preserves earthquake effects and external forces
  - Automatic cleanup and state reset
- **Workflow**: Play simulation, pause at desired point, then bake

### World Settings
- **Frame Range**: Configurable start/end frames for simulation
- **Substeps**: 1-100 substeps per frame for accuracy
- **Solver Iterations**: 1-100 constraint solver iterations
- **Split Impulse**: Reduces extra velocity in collisions

## Installation

### Requirements
- **Blender 4.2.0 - 5.0** (tested up to 5.0, may work with 5.1)

### Steps
1. Download or clone this repository
2. In Blender, go to **Edit → Preferences → Extensions**
3. Click **Install from Disk** (or drag and drop the extension folder)
4. Navigate to the downloaded folder and select it
5. Enable **Physics Dropper** in the extensions list
6. Find the panel in the **3D Viewport** sidebar under the **PhyDrop** tab

## Usage

### Quick Start

1. **Select** one or more mesh objects in your scene
2. Open the **PhyDrop** tab in the 3D Viewport sidebar (press **N** if hidden)
3. Choose your physics mode:
   - **Rigidbody**: For solid objects that bounce, collide, and fall
   - **Cloth**: For fabric, soft materials, and inflatable objects
4. Adjust parameters in the sub-panels (optional)
5. Press **Drop** button or press **V** key to apply physics
6. Press **Spacebar** to play the animation
7. Use **Apply** button or **Shift+V** when satisfied to finalize

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| **V** | Drop | Apply physics to selected objects |
| **Shift+V** | Apply | Finalize simulation and bake |
| **F** | Force Mode | Enter interactive force field mode |

*All shortcuts are customizable in Edit → Preferences → Add-ons → Physics Dropper*

### Rigid Body Workflow

#### Active Objects (Moving Objects)
1. Select objects that should move and respond to forces
2. Choose **Rigidbody** mode
3. Expand **Active Settings** panel
4. Adjust properties:
   - **Mass**: Weight of the object (0.001-1000 kg)
   - **Friction**: Surface grip (0-100)
   - **Bounciness**: Elasticity (0-1)
   - **Collision Shape**: Choose based on object geometry
5. Press **Drop** (V key)

#### Passive Objects (Collision Surfaces)
1. Select objects that should act as static collision surfaces (floors, walls, etc.)
2. Choose **Rigidbody** mode
3. Expand **Passive Settings** panel
4. Adjust collision shape and friction
5. Press **Drop** (V key)

#### High-Poly Objects
For complex geometry with many polygons:
1. Enable **Use Proxy** in Active or Passive Settings
2. Choose optimization method:
   - **Voxel Remesh**: Creates a solid voxel-based proxy
   - **Decimate**: Reduces polygon count while preserving shape
3. Adjust **Proxy Factor** for optimization level

### Cloth Simulation Workflow

1. Select mesh objects to turn into cloth
2. Choose **Cloth** mode
3. Select a **Material Preset** (optional but recommended):
   - **Cotton**: General purpose fabric
   - **Denim**: Stiffer, heavier fabric
   - **Leather**: Thick, resistant material
   - **Rubber**: Stretchy, elastic material
   - **Silk**: Light, flowing fabric
4. Fine-tune in sub-panels:
   - **Stiffness**: How resistant the cloth is to deformation
   - **Damping**: How quickly movement dampens
   - **Internal Spring**: Adds volume preservation
   - **Pressure**: For inflatable objects (balloons, cushions)
   - **Self Collision**: Prevents cloth from passing through itself
5. Press **Drop** (V key)

### Interactive Force Fields

#### Simple Force
1. Press **Add Force** button in main panel
2. Adjust **Force Strength** and **Distance** sliders
3. Play animation to see effect

#### Modal Force Mode (Advanced)
1. Press **F** key to enter force mode
2. **Move mouse** to position force field in 3D space
3. **Scroll wheel** to adjust force radius (distance)
4. **Ctrl+Click** to snap force to surface under cursor
5. **Left Click** to confirm placement
6. **Right Click** or **Esc** to cancel

Force fields appear as visual spheres showing their area of influence.

### Earthquake Effects

1. Check **Enable Earthquake** in main panel
2. Toggle axes (**X**, **Y**, **Z**) for directional shake
3. Adjust **Intensity** (0-100%)
4. Play animation to see all active physics objects shake
5. Effects use F-curve modifiers and can be edited in Graph Editor

### Baking to Keyframes

When you're satisfied with your simulation:

1. Play the animation to the point you want to bake
2. **Pause** the timeline
3. Press **Bake to Keyframes** button
4. Simulation is now permanent keyframe animation
5. Safe to modify further or use in rendering

**Benefits:**
- Faster playback and rendering
- No need to recalculate physics
- Can edit keyframes manually
- Preserves earthquake and force effects

### Control Buttons

| Button | Function |
|--------|----------|
| **Drop** | Apply physics simulation to selected objects |
| **Apply** | Finalize simulation and clean up |
| **Reset** | Remove all physics from scene |
| **Exit Drop Mode** | Keep simulation running but exit edit mode |
| **Pause/Play** | Toggle simulation playback |

## Technical Details

### Architecture

Physics Dropper uses a robust, thread-safe architecture:

- **State Management**: Thread-safe `PhysicsState` class tracks all simulation data
- **Safe Operations**: `SafeOperation` context manager ensures error handling
- **Property Validation**: All property updates are validated to prevent errors
- **Custom Icons**: Professional UI with custom icon integration
- **Modular Design**: Separate modules for rigidbody, cloth, earthquake, and baking systems

### File Structure

```
physics_dropper/
├── __init__.py              # Main entry point and registration
├── operators.py             # 13 operator classes for user actions
├── panels.py                # 12 UI panel classes
├── properties.py            # 80+ scene properties
├── rigidbody.py            # Rigid body physics system
├── cloth.py                # Cloth simulation system
├── earthquake.py           # F-curve noise modifier system
├── bake_utils.py           # Keyframe baking utilities
├── utils.py                # State management and helpers
├── logger.py               # Error handling and logging
├── constants.py            # Configuration constants
├── icons/                  # Custom UI icons
└── blender_manifest.toml   # Extension metadata
```

## Tips & Best Practices

### Performance
- Use **proxy objects** for high-poly meshes
- Reduce **substeps** and **solver iterations** for faster preview
- Increase quality settings only for final renders
- Bake simulations to keyframes for faster playback

### Stability
- Start with low force values and increase gradually
- Use **Split Impulse** in World Settings to reduce jitter
- Increase **Solver Iterations** if objects pass through each other
- Add more **Substeps** for fast-moving objects

### Cloth
- Always have a collision object (passive rigidbody or cloth collision)
- Enable **Self Collision** for complex folds
- Use **Pin Group** (vertex group) to anchor parts of cloth
- Adjust **Collision Quality** if penetration occurs

### Force Fields
- Use **Ctrl+Click** in Force Mode to snap to surfaces precisely
- Adjust **Flow** parameter to convert force to air flow for cloth
- Multiple force fields can be combined for complex effects
- Animate force strength for dynamic effects

## Support

If you find Physics Dropper useful, consider supporting its development:


[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](paypal.me/ElinHoehler)

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

Physics Dropper is licensed under the **GPL-3.0-or-later** license.

Copyright © 2024 Elin Höhler

## Changelog

### Version 1.3.0 (Latest)
- Migrated to Blender 4.5+ extension format
- Maintained backward compatibility with older versions
- Enhanced force mode with Ctrl+Click raycast surface snapping
- Improved keyframe baking system
- Updated for Blender 4.5 compatibility
- Various bug fixes and performance improvements

---

**Made with ❤️ for the Blender community**
