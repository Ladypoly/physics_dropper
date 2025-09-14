# Physics Dropper

A Blender addon for easy setup of rigid body and cloth physics simulations with advanced baking capabilities.

## Overview

Physics Dropper is a Blender addon that simplifies the process of setting up physics simulations in your 3D scenes. Whether you're working with rigid body dynamics or cloth simulations, this addon provides an intuitive interface and streamlined workflow for creating realistic physics interactions.

## 🚨 CRITICAL BAKING ISSUE (UNRESOLVED)

**Current Problem**: Cache baking (`bpy.ops.ptcache.bake_from_cache()`) is failing with several issues:
1. **Object at world zero**: First selected object gets stuck at (0,0,0) world origin
2. **Cache corruption**: Objects reset to start position on playback and fall without collision
3. **Context requirements**: The operator needs proper UI context (Properties/Timeline/3D View visible)

**Working Solution**: Direct call to `bpy.ops.ptcache.bake_from_cache()` with proper UI context works fine when called manually, but fails when integrated into the addon workflow.

**Files Involved**:
- `bake_utils.py:12-81` - Main baking function (currently broken)
- `operators.py:344-450` - Cache baking operator
- `utils.py:206-251` - Post-bake cleanup (disabled for cache baking)

## Features

### 🎯 Rigid Body Physics
- **Easy Drop System**: Apply rigid body physics to selected objects with a single click
- **Collision Detection**: Automatic collision mesh generation for complex objects
- **Force Fields**: Interactive force field system with customizable strength and distance
- **Earthquake Effects**: Built-in earthquake simulation for dynamic environments
- **Customizable Properties**: Fine-tune mass, friction, bounciness, and other physical properties

### 🧵 Cloth Simulation
- **Material Presets**: Pre-configured settings for common materials:
  - Cotton
  - Denim
  - Leather
  - Silk
  - Rubber
  - Custom settings
- **Advanced Parameters**: Control stiffness, damping, air viscosity, and internal springs
- **Self-Collision**: Configurable self-collision detection and handling
- **Pressure Effects**: Optional pressure simulation for inflatable objects

### ⚡ Workflow Tools
- **Cache Baking**: Preserve current physics simulation state with external influences (earthquake effects, forces)
  - ⚠️ **BROKEN**: Current implementation has object positioning and cache corruption issues
  - ✅ **Manual Workaround**: Use standalone `bpy.ops.ptcache.bake_from_cache()` function
- **Keyframe Baking**: Bake physics simulations to keyframes for performance
- **Armature Integration**: Bake armature animations alongside physics
- **Keyboard Shortcuts**: Customizable hotkeys for quick access to common operations
- **Visual Feedback**: Clear UI panels with intuitive controls

## Installation

1. **Download**: Download the Physics Dropper addon files
2. **Install in Blender**:
   - Open Blender
   - Go to `Edit > Preferences > Add-ons`
   - Click `Install...` and select the addon folder
   - Enable the "Physics Dropper" addon in the list
3. **Access**: Find the Physics Dropper panel in the 3D Viewport's Tool panel

## Requirements

- **Blender Version**: 2.93.5 or higher
- **Blender 4.5+**: Fully compatible with latest Blender versions

## Technology Stack

- **Language**: Python 3.x
- **Framework**: Blender Python API (bpy)
- **UI System**: Blender's built-in panel and operator system
- **Physics Engine**: Blender's native Bullet physics integration

## Usage

### Basic Rigid Body Setup
1. Select objects in your scene
2. Open the Physics Dropper panel
3. Choose "Rigidbody" mode
4. Click "Drop" to apply physics
5. Use "Apply" to finalize the simulation

### Cloth Simulation Setup
1. Select mesh objects suitable for cloth
2. Switch to "Cloth" mode in the panel
3. Choose a material preset or configure custom settings
4. Apply cloth physics and adjust parameters as needed

### Keyboard Shortcuts
The addon includes customizable keyboard shortcuts for:
- **Drop**: Apply physics to selected objects
- **Apply**: Finalize/bake the current simulation
- **Toggle Force**: Enable/disable force fields

Configure shortcuts in `Edit > Preferences > Add-ons > Physics Dropper`

## Architecture & File Structure

### Core System Files
```
physics_dropper/
├── __init__.py          # Main addon registration and entry point
├── operators.py         # Physics operation classes and UI operators
├── panels.py           # UI panel definitions and layout
├── properties.py       # Addon properties and settings
├── constants.py        # Configuration constants and defaults
├── logger.py           # Logging system with SafeOperation context manager
└── utils.py            # Core utility functions and PhysicsState management
```

### Physics Modules
```
├── rigidbody.py        # Rigid body physics functions and world setup
├── cloth.py            # Cloth simulation functions and material presets
├── earthquake.py       # Earthquake effect system using F-curve noise modifiers
├── bake_utils.py       # Physics cache baking utilities (⚠️ BROKEN)
└── armature_bake.py    # Armature-specific baking functions
```

### Assets
```
├── icons/              # UI icons and visual assets
│   ├── DROPBOX.png
│   ├── DROPCLOTH.png
│   └── ...
└── assets/             # Additional addon assets
```

### Key Classes and Systems

#### PhysicsState (utils.py:15-124)
Thread-safe state management for physics objects:
- `physics_dropper`: Main simulation state (active/passive objects, dropped status)
- `rigidbody`: Rigid body specific state (world settings, high/low poly objects)
- `cloth`: Cloth simulation state
- `earthquake`: F-curve modifier tracking for earthquake effects

#### SafeOperation (logger.py)
Context manager for safe Blender operations with error handling and performance tracking.

#### Baking System (bake_utils.py) ⚠️ BROKEN
- `bake_rigidbody_simulation()`: Main cache baking function
- `clear_rigidbody_bake()`: Cache clearing functionality
- `delete_collider()`: Cleanup collider objects after baking

## Contributing

This addon was created by Elin. For bug reports, feature requests, or contributions, please refer to the addon's support channels.

## License

Physics Dropper addon for Blender - Version 1.2.0

## Recent Changes & Development Notes

### Cache Baking Investigation (2024)
**Problem**: Cache baking workflow is fundamentally broken with multiple issues:

1. **Transform Corruption**: Objects getting reset to world origin (0,0,0)
2. **Cache State Issues**: Baked objects reset to start position and lose collision
3. **Context Problems**: `bpy.ops.ptcache.bake_from_cache()` requires specific UI context

**Root Causes Identified**:
- Post-bake cleanup (`utils.py:post_bake()`) was destroying physics setup needed for cache playback
- Object selection/manipulation during baking was corrupting transforms
- Timeline/frame manipulation was interfering with natural cache extent

**Working Manual Solution**:
```python
import bpy

def rb_bake_from_current_cache(scene=None):
    scene = scene or bpy.context.scene
    if not scene.rigidbody_world:
        raise RuntimeError("No Rigid Body World on the scene")

    pc = scene.rigidbody_world.point_cache

    def find_ui_override():
        wm = bpy.context.window_manager
        for win in wm.windows:
            scr = win.screen
            for area in scr.areas:
                if area.type in {'PROPERTIES', 'TIMELINE', 'VIEW_3D'}:
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return {
                                'window': win, 'screen': scr, 'area': area,
                                'region': region, 'scene': scene, 'point_cache': pc
                            }
        return None

    ctx = find_ui_override()
    if not ctx:
        raise RuntimeError("No suitable UI context found")

    with bpy.context.temp_override(**ctx):
        bpy.ops.ptcache.bake_from_cache()

rb_bake_from_current_cache()
```

**Key Principle**: Cache baking should preserve everything exactly as simulated - positions, physics setup, world settings, and natural simulation extent.

### Failed Approaches Tried
1. Complex context override with object selection
2. Transform preservation/restoration after baking
3. Direct API calls (`point_cache.bake()` - doesn't exist)
4. Frame range manipulation (interferes with natural extent)

**Next Developer**: The issue persists despite implementing the exact working function. Something in the addon workflow is still interfering with the baking process.

## Version History

- **v1.2.0**: Current version with enhanced cloth simulation and UI improvements
- Compatible with Blender 2.93.5+
- **Cache Baking**: Currently broken, needs investigation