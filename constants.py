"""
Constants and configuration for the Physics Dropper addon.
"""

from typing import Dict, Tuple, Any

# Version and metadata
ADDON_VERSION = (1, 3, 0)
BLENDER_MIN_VERSION = (2, 93, 5)
ADDON_NAME = "Physics Dropper"

# Default values
DEFAULT_FRAME_START = 1
DEFAULT_FRAME_END = 250
DEFAULT_SUBSTEPS = 10
DEFAULT_SOLVER_ITERATIONS = 10

# Physics constants
PHYSICS_MARGIN_MIN = 0.001
PHYSICS_MARGIN_MAX = 1.0
PHYSICS_MARGIN_DEFAULT = 0.04

FRICTION_MIN = 0.0
FRICTION_MAX = 100.0
FRICTION_DEFAULT = 0.5

BOUNCINESS_MIN = 0.0
BOUNCINESS_MAX = 1.0
BOUNCINESS_DEFAULT = 0.0

MASS_MIN = 0.001
MASS_MAX = 1000.0
MASS_DEFAULT = 1.0

DAMPING_MIN = 0.0
DAMPING_MAX = 10.0
DAMPING_DEFAULT = 0.04

# Force field constants
FORCE_STRENGTH_MIN = -1000.0
FORCE_STRENGTH_MAX = 1000.0
FORCE_STRENGTH_DEFAULT = -1000.0

FORCE_DISTANCE_MIN = 0.0
FORCE_DISTANCE_MAX = 100.0
FORCE_DISTANCE_DEFAULT = 1.0

FORCE_FLOW_MIN = 0.0
FORCE_FLOW_MAX = 10.0
FORCE_FLOW_DEFAULT = 0.0

# Optimization constants
VOXEL_SIZE_MIN = 0.001
VOXEL_SIZE_MAX = 1.0
VOXEL_SIZE_DEFAULT = 0.1

DECIMATE_RATIO_MIN = 0.01
DECIMATE_RATIO_MAX = 1.0
DECIMATE_RATIO_DEFAULT = 0.5

# Timer intervals
POST_BAKE_TIMER_INTERVAL = 0.5
CLEANUP_TIMER_INTERVAL = 0.1

# Object names
COLLIDER_OBJECT_NAME = "COLLIDER"
PHYSICS_PROXY_SUFFIX = "_PhysProxy"

# Collision shapes
COLLISION_SHAPES = [
    ('CONVEX_HULL', 'Convex Hull', 'Collision shape is the convex hull of the mesh'),
    ('MESH', 'Mesh', 'Collision shape is the exact mesh'),
    ('BOX', 'Box', 'Collision shape is a box'),
    ('SPHERE', 'Sphere', 'Collision shape is a sphere'),
    ('CAPSULE', 'Capsule', 'Collision shape is a capsule'),
    ('CYLINDER', 'Cylinder', 'Collision shape is a cylinder'),
    ('CONE', 'Cone', 'Collision shape is a cone'),
    ('COMPOUND', 'Compound', 'Collision shape is a compound of shapes')
]

# Display types
DISPLAY_TYPES = [
    ('BOUNDS', 'Bounds', 'Display as bounding box'),
    ('WIRE', 'Wire', 'Display as wireframe'),
    ('SOLID', 'Solid', 'Display as solid'),
    ('TEXTURED', 'Textured', 'Display with textures')
]

# Cloth material presets
CLOTH_PRESETS: Dict[str, Tuple[float, ...]] = {
    "Cotton": (5, 0.30, 1.0, 15.0, 15.0, 15.0, 0.5, 5.0, 5.0, 5.0, 0.5,
               False, 0.0, 45.0, 15.0, 15.0, 15.0, 15.0,
               False, 0.0, 1.0, 0.0, 2, 0.015, 0.0, True, 5.0, 0.015, 0.0),
    "Denim": (12, 1.0, 1.0, 40.0, 40.0, 40.0, 10.0, 25.0, 25.0, 25.0, 0.5,
              False, 0.0, 45.0, 15.0, 15.0, 15.0, 15.0,
              False, 0.0, 1.0, 0.0, 2, 0.015, 0.0, True, 5.0, 0.015, 0.0),
    "Leather": (15, 0.40, 1.0, 80.0, 80.0, 80.0, 150.0, 25.0, 25.0, 25.0, 0.5,
                False, 0.0, 45.0, 15.0, 15.0, 15.0, 15.0,
                False, 0.0, 1.0, 0.0, 2, 0.015, 0.0, True, 5.0, 0.015, 0.0),
    "Rubber": (7, 3.0, 1.0, 15.0, 15.0, 15.0, 25.0, 25.0, 25.0, 25.0, 0.5,
               False, 0.0, 45.0, 15.0, 15.0, 15.0, 15.0,
               False, 0.0, 1.0, 0.0, 2, 0.015, 0.0, True, 5.0, 0.015, 0.0),
    "Silk": (5, 0.15, 1.0, 5.0, 5.0, 5.0, 0.05, 0.0, 0.0, 0.0, 0.5,
             False, 0.0, 45.0, 15.0, 15.0, 15.0, 15.0,
             False, 0.0, 1.0, 0.0, 2, 0.015, 0.0, True, 5.0, 0.015, 0.0)
}

# Cloth parameter names (for documentation)
CLOTH_PARAMETER_NAMES = [
    'quality_steps', 'mass', 'air_viscosity',
    'stiff_tension', 'stiff_compression', 'stiff_shear', 'stiff_bending',
    'damp_tension', 'damp_compression', 'damp_shear', 'damp_bending',
    'internal_springs', 'internal_spring_max_length', 'internal_spring_max_division',
    'internal_spring_tension', 'internal_spring_compression',
    'internal_spring_max_tension', 'internal_spring_max_compression',
    'use_pressure', 'pressure', 'pressure_scale', 'pressure_fluid_density',
    'quality', 'minimum_distance', 'impulse_clamping',
    'self_collision', 'self_collision_friction', 'self_collision_distance',
    'self_collision_impulse_clamping'
]

# Icon names
ICON_NAMES = ["DROPBOX", "X", "Y", "Z", "DROPCLOTH", "BMAC", "PAYPAL"]

# URL validation (for donation links)
ALLOWED_DOMAINS = ["buymeacoffee.com", "paypal.com"]

# Error messages
ERROR_MESSAGES = {
    'NO_MESH_SELECTED': "No mesh objects selected. Please select at least one mesh object.",
    'NO_RIGIDBODY_WORLD': "Failed to create rigidbody world. Check Blender version compatibility.",
    'FORCE_OBJECT_NOT_FOUND': "Force object not found or already deleted.",
    'OBJECT_DELETED': "Object was deleted during operation.",
    'INVALID_CONTEXT': "Invalid context for this operation.",
    'PROPERTY_UPDATE_FAILED': "Failed to update property. Object may have been deleted.",
}

# Success messages
SUCCESS_MESSAGES = {
    'PHYSICS_APPLIED': "Physics simulation applied successfully.",
    'BAKING_COMPLETE': "Physics baking completed successfully.",
    'FORCE_ADDED': "Force field added successfully.",
    'FORCE_REMOVED': "Force field removed successfully.",
    'SIMULATION_RESET': "Physics simulation reset successfully.",
}

# Log levels
LOG_LEVELS = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4
}

# Default log level
DEFAULT_LOG_LEVEL = LOG_LEVELS['INFO']

# Performance settings
MAX_OBJECTS_BATCH_OPERATION = 100  # Maximum objects to process in a single batch
LARGE_SCENE_THRESHOLD = 1000  # Object count threshold for performance warnings

# File paths
ICONS_DIR_NAME = "icons"
ASSETS_DIR_NAME = "assets"

# Keymap defaults
DEFAULT_KEYMAPS = {
    'drop': {'type': 'V', 'shift': False, 'ctrl': False, 'alt': False},
    'apply': {'type': 'V', 'shift': True, 'ctrl': False, 'alt': False},
    'force': {'type': 'F', 'shift': False, 'ctrl': False, 'alt': False}
}