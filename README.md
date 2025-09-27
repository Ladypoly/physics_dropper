# Physics Dropper

A Blender addon for easy setup of rigid body and cloth physics simulations with streamlined baking capabilities.

## Overview

Physics Dropper is a Blender addon that simplifies the process of setting up physics simulations in your 3D scenes. Whether you're working with rigid body dynamics or cloth simulations, this addon provides an intuitive interface and streamlined workflow for creating realistic physics interactions.

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
- **Keyframe Baking**: Bake physics simulations to keyframes up to the current timeline position
  - Smart baking that only processes frames up to where you pause the simulation
  - Preserves earthquake effects and external forces in the baked animation
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
└── bake_utils.py       # Physics keyframe baking utilities
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

#### Baking System (bake_utils.py)
- `rb_bake_from_current_cache()`: Cache preparation for keyframe baking
- `clear_rigidbody_bake()`: Cache clearing functionality
- `delete_collider()`: Cleanup collider objects after baking

## Contributing

This addon was created by Elin. For bug reports, feature requests, or contributions, please refer to the addon's support channels.

## License

Physics Dropper addon for Blender - Version 1.3.0

## Recent Changes & Development Notes

### Latest Updates (2024)

#### Baking System Improvements
- **Removed Cache Baking**: Eliminated the problematic "Bake to Cache" functionality that was causing object positioning and cache corruption issues
- **Enhanced Keyframe Baking**: Improved the "Bake to Keyframes" feature to only bake up to the current timeline position
  - Now intelligently stops at the current frame instead of processing the entire timeline
  - More efficient workflow: pause simulation at desired frame, then bake
  - Preserves earthquake effects and external forces in baked keyframes

#### UI/UX Improvements
- **Better Button Sizing**: Improved visual hierarchy of simulation control buttons
  - Apply and Bake to Keyframes buttons are now prominently sized
  - Secondary controls (Pause/Play) are appropriately smaller
  - Force properties and earthquake controls are properly sized for readability

#### Code Quality
- **Cleaner Architecture**: Removed unused and problematic code paths
- **Better Error Handling**: Enhanced validation for frame ranges and simulation states
- **Improved Logging**: More descriptive messages for baking operations

## Version History

- **v1.3.0**: Current version with streamlined baking system and improved UI
- **v1.2.0**: Previous version with enhanced cloth simulation
- Compatible with Blender 2.93.5+ and fully tested with Blender 4.5+