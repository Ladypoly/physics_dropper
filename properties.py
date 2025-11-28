"""
Property definitions for the Physics Dropper addon.
"""

import bpy
from typing import Any, Callable, Optional
from . import constants
from .logger import logger, safe_object_access, safe_context_access
from . import earthquake as eq


def validate_property_update(func: Callable) -> Callable:
    """Decorator to safely handle property updates with validation."""
    def wrapper(self, context):
        try:
            # Validate context is available
            if not context:
                logger.warning(f"No context available for {func.__name__}")
                return

            # Clean up any invalid references before updating
            from . import utils
            utils.cleanup_invalid_references()

            # Call the original update function
            return func(self, context)

        except Exception as e:
            logger.error(f"Error in property update {func.__name__}", e)

    return wrapper


@validate_property_update
def update_earthquake(self, context):
    """Update earthquake settings safely."""
    try:
        eq.update_earthquake()
        # logger.debug("Updated earthquake settings")
    except Exception as e:
        logger.warning("Failed to update earthquake settings", e)


@validate_property_update
def update_earthquake_x(self, context):
    """Update X-axis earthquake settings safely."""
    try:
        eq.update_earthquake()
        # logger.debug("Updated X-axis earthquake settings")
    except Exception as e:
        logger.warning("Failed to update X-axis earthquake settings", e)


@validate_property_update
def update_earthquake_y(self, context):
    """Update Y-axis earthquake settings safely."""
    try:
        eq.update_earthquake()
        # logger.debug("Updated Y-axis earthquake settings")
    except Exception as e:
        logger.warning("Failed to update Y-axis earthquake settings", e)


@validate_property_update
def update_earthquake_z(self, context):
    """Update Z-axis earthquake settings safely."""
    try:
        eq.update_earthquake()
        # logger.debug("Updated Z-axis earthquake settings")
    except Exception as e:
        logger.warning("Failed to update Z-axis earthquake settings", e)


@validate_property_update
def update_force_strength(self, context):
    """Update force field strength safely."""
    try:
        from . import utils

        # Validate property value
        force_strength = getattr(self, 'forcestrength', constants.FORCE_STRENGTH_DEFAULT)
        if not (constants.FORCE_STRENGTH_MIN <= force_strength <= constants.FORCE_STRENGTH_MAX):
            logger.warning(f"Force strength {force_strength} out of valid range")
            force_strength = max(constants.FORCE_STRENGTH_MIN,
                               min(constants.FORCE_STRENGTH_MAX, force_strength))

        # Get force object safely
        force_obj = utils.state.get_physics_dropper("force_object")
        if force_obj and utils.is_object_valid(force_obj):
            field = safe_object_access(force_obj, "field")
            if field:
                field.strength = force_strength
                # logger.debug(f"Updated force strength to {force_strength}")
            else:
                logger.warning("Force object has no field property")
        else:
            # logger.debug("No valid force object to update")
            pass

    except Exception as e:
        logger.error("Failed to update force strength", e)


@validate_property_update
def update_force_distance(self, context):
    """Update force field distance safely."""
    try:
        from . import utils

        # Validate property value
        force_distance = getattr(self, 'forcedistance', constants.FORCE_DISTANCE_DEFAULT)
        if not (constants.FORCE_DISTANCE_MIN <= force_distance <= constants.FORCE_DISTANCE_MAX):
            logger.warning(f"Force distance {force_distance} out of valid range")
            force_distance = max(constants.FORCE_DISTANCE_MIN,
                               min(constants.FORCE_DISTANCE_MAX, force_distance))

        # Get force object safely
        force_obj = utils.state.get_physics_dropper("force_object")
        if force_obj and utils.is_object_valid(force_obj):
            field = safe_object_access(force_obj, "field")
            if field:
                field.distance_max = force_distance
                # Also update display size
                force_obj.empty_display_size = force_distance
                # logger.debug(f"Updated force distance to {force_distance}")
            else:
                logger.warning("Force object has no field property")
        else:
            # logger.debug("No valid force object to update")
            pass

    except Exception as e:
        logger.error("Failed to update force distance", e)


@validate_property_update
def update_force_flow(self, context):
    """Update force field flow safely."""
    try:
        from . import utils

        # Validate property value
        force_flow = getattr(self, 'forceflow', constants.FORCE_FLOW_DEFAULT)
        if not (constants.FORCE_FLOW_MIN <= force_flow <= constants.FORCE_FLOW_MAX):
            logger.warning(f"Force flow {force_flow} out of valid range")
            force_flow = max(constants.FORCE_FLOW_MIN,
                           min(constants.FORCE_FLOW_MAX, force_flow))

        # Get force object safely
        force_obj = utils.state.get_physics_dropper("force_object")
        if force_obj and utils.is_object_valid(force_obj):
            field = safe_object_access(force_obj, "field")
            if field:
                field.flow = force_flow
                # logger.debug(f"Updated force flow to {force_flow}")
            else:
                logger.warning("Force object has no field property")
        else:
            # logger.debug("No valid force object to update")
            pass

    except Exception as e:
        logger.error("Failed to update force flow", e)


@validate_property_update
def update_cloth_presets(self, context):
    """Update cloth presets safely."""
    try:
        from . import cloth as cloth_module
        from . import utils

        preset_name = getattr(self, 'c_a_presets', 'Cotton')

        if preset_name not in constants.CLOTH_PRESETS:
            logger.warning(f"Unknown cloth preset: {preset_name}")
            return

        # Apply the preset
        preset_values = constants.CLOTH_PRESETS[preset_name]
        cloth_module.set_cloth_parameter(*preset_values)
        # logger.info(f"Applied cloth preset: {preset_name}")

        # Update cloth settings if already dropped
        scene = safe_context_access("scene")
        if scene and getattr(scene, 'dropped', False):
            cloth_active = utils.state.get_cloth("active")
            updated_count = 0

            for obj in cloth_active:
                if utils.is_object_valid(obj):
                    active_modifier = safe_object_access(obj, "modifiers.active")
                    if active_modifier:
                        cloth_module.set_cloth_settings(active_modifier)
                        updated_count += 1

            if updated_count > 0:
                # logger.info(f"Updated {updated_count} active cloth objects with new preset")
                pass

    except Exception as e:
        logger.error("Failed to update cloth presets", e)


def register_properties() -> bool:
    """Register all properties for the addon with improved error handling."""
    try:
        # logger.info("Registering Physics Dropper properties")

        # Rigid body properties with proper validation
        bpy.types.Scene.a_shape = bpy.props.EnumProperty(
            name='Shape',
            description='Collision shape of the object',
            items=constants.COLLISION_SHAPES,
            default='CONVEX_HULL'
        )

        bpy.types.Scene.a_friction = bpy.props.FloatProperty(
            name='Friction',
            description='Resistance of object to movement',
            default=constants.FRICTION_DEFAULT,
            min=constants.FRICTION_MIN,
            max=constants.FRICTION_MAX,
            precision=3
        )

        bpy.types.Scene.a_bounciness = bpy.props.FloatProperty(  # Fixed typo
            name='Bounciness',
            description='Tendency of object to bounce after colliding',
            default=constants.BOUNCINESS_DEFAULT,
            min=constants.BOUNCINESS_MIN,
            max=constants.BOUNCINESS_MAX,
            precision=3
        )

        bpy.types.Scene.a_margin = bpy.props.FloatProperty(
            name='Margin',
            description='Collision margin for physics objects',
            default=constants.PHYSICS_MARGIN_DEFAULT,
            min=constants.PHYSICS_MARGIN_MIN,
            max=constants.PHYSICS_MARGIN_MAX,
            precision=4
        )

        bpy.types.Scene.a_tra_damp = bpy.props.FloatProperty(
            name='Translation Damping',
            description='Amount of linear velocity that is lost over time',
            default=constants.DAMPING_DEFAULT,
            min=constants.DAMPING_MIN,
            max=constants.DAMPING_MAX,
            precision=3
        )

        bpy.types.Scene.a_rot_damp = bpy.props.FloatProperty(
            name='Rotation Damping',
            description='Amount of angular velocity that is lost over time',
            default=0.1,
            min=0.001,
            max=1.0,
            precision=3
        )

        bpy.types.Scene.a_mass = bpy.props.FloatProperty(
            name='Mass',
            description='Mass of the rigidbody object',
            default=constants.MASS_DEFAULT,
            min=constants.MASS_MIN,
            max=constants.MASS_MAX,
            precision=3
        )

        # Passive object properties (collision objects)
        bpy.types.Scene.p_shape = bpy.props.EnumProperty(
            name='Passive Shape',
            description='Collision shape of the passive object',
            items=constants.COLLISION_SHAPES,
            default='MESH'
        )

        bpy.types.Scene.p_friction = bpy.props.FloatProperty(
            name='Passive Friction',
            description='Resistance of passive object to movement',
            default=constants.FRICTION_DEFAULT,
            min=constants.FRICTION_MIN,
            max=constants.FRICTION_MAX,
            precision=3
        )

        bpy.types.Scene.p_bounciness = bpy.props.FloatProperty(  # Fixed typo
            name='Passive Bounciness',
            description='Tendency of passive object to bounce after colliding',
            default=constants.BOUNCINESS_DEFAULT,
            min=constants.BOUNCINESS_MIN,
            max=constants.BOUNCINESS_MAX,
            precision=3
        )

        bpy.types.Scene.p_margin = bpy.props.FloatProperty(
            name='Passive Margin',
            description='Collision margin for passive objects',
            default=constants.PHYSICS_MARGIN_DEFAULT,
            min=constants.PHYSICS_MARGIN_MIN,
            max=constants.PHYSICS_MARGIN_MAX,
            precision=4
        )

        # World settings
        bpy.types.Scene.w_startframe = bpy.props.IntProperty(
            name='Start Frame',
            description='Starting frame for physics simulation',
            default=constants.DEFAULT_FRAME_START,
            min=1,
            max=1048574
        )

        bpy.types.Scene.w_endframe = bpy.props.IntProperty(
            name='End Frame',
            description='Ending frame for physics simulation',
            default=constants.DEFAULT_FRAME_END,
            min=1,
            max=1048574
        )

        bpy.types.Scene.w_split_impulse = bpy.props.BoolProperty(
            name='Split Impulse',
            description='Reduce extra velocity that can build up when objects collide',
            default=True
        )

        bpy.types.Scene.w_subframes = bpy.props.IntProperty(
            name='Substeps Per Frame',
            description='Number of simulation steps per frame',
            default=constants.DEFAULT_SUBSTEPS,
            min=1,
            max=100
        )

        bpy.types.Scene.w_solver_iterations = bpy.props.IntProperty(
            name='Solver Iterations',
            description='Amount of constraint solver iterations per simulation step',
            default=constants.DEFAULT_SOLVER_ITERATIONS,
            min=1,
            max=100
        )

        # Optimization properties
        bpy.types.Scene.optimizehighpoly = bpy.props.BoolProperty(
            name='Optimize High Poly Objects',
            description='Create low-poly proxies for high-poly objects',
            default=False
        )

        bpy.types.Scene.p_optimizehighpoly = bpy.props.BoolProperty(
            name='Optimize Passive High Poly',
            description='Create low-poly version for passive collision object',
            default=False
        )

        bpy.types.Scene.a_voxelsize = bpy.props.FloatProperty(
            name='Active Voxel Size',
            description='Voxel size for remeshing optimization (0 = disabled)',
            default=constants.VOXEL_SIZE_DEFAULT,
            min=0.0,
            max=constants.VOXEL_SIZE_MAX,
            precision=3
        )

        bpy.types.Scene.a_decimaterate = bpy.props.FloatProperty(
            name='Active Decimate Rate',
            description='Decimation ratio for active objects',
            default=constants.DECIMATE_RATIO_DEFAULT,
            min=constants.DECIMATE_RATIO_MIN,
            max=constants.DECIMATE_RATIO_MAX,
            precision=3
        )

        bpy.types.Scene.p_voxelsize = bpy.props.FloatProperty(
            name='Passive Voxel Size',
            description='Voxel size for passive object remeshing (0 = disabled)',
            default=0.0,
            min=0.0,
            max=constants.VOXEL_SIZE_MAX,
            precision=3
        )

        bpy.types.Scene.p_decimaterate = bpy.props.FloatProperty(
            name='Passive Decimate Rate',
            description='Decimation ratio for passive objects',
            default=constants.DECIMATE_RATIO_DEFAULT,
            min=constants.DECIMATE_RATIO_MIN,
            max=constants.DECIMATE_RATIO_MAX,
            precision=3
        )

        # Force field properties
        bpy.types.Scene.forcestrength = bpy.props.FloatProperty(
            name='Force Strength',
            description='Strength of the force field',
            default=constants.FORCE_STRENGTH_DEFAULT,
            min=constants.FORCE_STRENGTH_MIN,
            max=constants.FORCE_STRENGTH_MAX,
            update=update_force_strength,
            precision=1
        )

        bpy.types.Scene.forcedistance = bpy.props.FloatProperty(
            name='Force Distance',
            description='Maximum distance for force field effect',
            default=constants.FORCE_DISTANCE_DEFAULT,
            min=constants.FORCE_DISTANCE_MIN,
            max=constants.FORCE_DISTANCE_MAX,
            update=update_force_distance,
            precision=2
        )

        bpy.types.Scene.forceflow = bpy.props.FloatProperty(
            name='Force Flow',
            description='Convert force into air flow velocity',
            default=constants.FORCE_FLOW_DEFAULT,
            min=constants.FORCE_FLOW_MIN,
            max=constants.FORCE_FLOW_MAX,
            update=update_force_flow,
            precision=2
        )

        # Earthquake properties
        bpy.types.Scene.earthquake = bpy.props.FloatProperty(
            name='Earthquake Intensity',
            description='Amount of world shake',
            default=0.0,
            min=0.0,
            max=100.0,
            subtype='PERCENTAGE',
            update=update_earthquake,
            precision=1
        )

        bpy.types.Scene.earthquakex = bpy.props.BoolProperty(
            name='X-Axis',
            description='Shake the world along the X axis',
            default=True,
            update=update_earthquake_x
        )

        bpy.types.Scene.earthquakey = bpy.props.BoolProperty(
            name='Y-Axis',
            description='Shake the world along the Y axis',
            default=True,
            update=update_earthquake_y
        )

        bpy.types.Scene.earthquakez = bpy.props.BoolProperty(
            name='Z-Axis',
            description='Shake the world along the Z axis',
            default=True,
            update=update_earthquake_z
        )

        # Cloth preset property
        bpy.types.Scene.c_a_presets = bpy.props.EnumProperty(
            name='Cloth Material Presets',
            description='Predefined cloth material settings',
            items=[
                (name, name.capitalize(), f"Apply {name.lower()} material settings")
                for name in constants.CLOTH_PRESETS.keys()
            ],
            default='Cotton',
            update=update_cloth_presets
        )

        # Cloth collision properties
        bpy.types.Scene.c_p_damping = bpy.props.FloatProperty(
            name='Collision Damping',
            description='Damping during cloth collision',
            default=0.1,
            min=0.0,
            max=1.0,
            precision=3
        )

        bpy.types.Scene.c_p_thick_outer = bpy.props.FloatProperty(
            name='Outer Collision Thickness',
            description='Size of the outer collision zone',
            default=0.02,
            min=0.001,
            max=1.0,
            precision=3
        )

        bpy.types.Scene.c_p_thick_inner = bpy.props.FloatProperty(
            name='Inner Collision Thickness',
            description='Size of the inner collision zone',
            default=0.2,
            min=0.001,
            max=1.0,
            precision=3
        )

        bpy.types.Scene.c_p_friction = bpy.props.FloatProperty(
            name='Cloth Friction',
            description='Friction during movements along surfaces',
            default=80.0,
            min=0.0,
            max=100.0,
            precision=1
        )

        bpy.types.Scene.c_p_fatten = bpy.props.FloatProperty(
            name='Collider Fatten',
            description='Expand the collision mesh outward (Solidify thickness)',
            default=0.1,
            min=0.0,
            soft_max=1.0,
            precision=3
        )

        # Detailed cloth simulation properties
        bpy.types.Scene.ca_qualitysteps = bpy.props.IntProperty(
            name='Quality Steps',
            description='Number of simulation steps per frame',
            default=5,
            min=1,
            max=80
        )

        bpy.types.Scene.ca_mass = bpy.props.FloatProperty(
            name='Cloth Mass',
            description='Mass per unit area of the cloth material',
            default=0.3,
            min=0.001,
            max=10.0,
            precision=3
        )

        bpy.types.Scene.ca_air_viscosity = bpy.props.FloatProperty(
            name='Air Viscosity',
            description='Air thickness that slows falling objects',
            default=1.0,
            min=0.0,
            max=10.0,
            precision=2
        )

        # Cloth stiffness properties
        bpy.types.Scene.ca_stiff_tension = bpy.props.FloatProperty(
            name='Tension Stiffness',
            description='How much the material resists stretching',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        bpy.types.Scene.ca_stiff_compression = bpy.props.FloatProperty(
            name='Compression Stiffness',
            description='How much the material resists compression',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        bpy.types.Scene.ca_stiff_shear = bpy.props.FloatProperty(
            name='Shear Stiffness',
            description='How much the material resists shearing',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        bpy.types.Scene.ca_stiff_bending = bpy.props.FloatProperty(
            name='Bending Stiffness',
            description='Wrinkle resistance (higher = fewer, larger folds)',
            default=0.5,
            min=0.0,
            max=10000.0,
            precision=2
        )

        # Cloth damping properties
        bpy.types.Scene.ca_damp_tension = bpy.props.FloatProperty(
            name='Tension Damping',
            description='Damping in stretching behavior',
            default=5.0,
            min=0.0,
            max=50.0,
            precision=1
        )

        bpy.types.Scene.ca_damp_compression = bpy.props.FloatProperty(
            name='Compression Damping',
            description='Damping in compression behavior',
            default=5.0,
            min=0.0,
            max=50.0,
            precision=1
        )

        bpy.types.Scene.ca_damp_shear = bpy.props.FloatProperty(
            name='Shear Damping',
            description='Damping in shearing behavior',
            default=5.0,
            min=0.0,
            max=50.0,
            precision=1
        )

        bpy.types.Scene.ca_damp_bending = bpy.props.FloatProperty(
            name='Bending Damping',
            description='Damping in bending behavior',
            default=0.5,
            min=0.0,
            max=50.0,
            precision=2
        )

        # Internal springs properties
        bpy.types.Scene.ca_internalsprings = bpy.props.BoolProperty(
            name='Internal Springs',
            description='Enable internal springs for soft body behavior',
            default=False
        )

        bpy.types.Scene.ca_internalspringmaxlength = bpy.props.FloatProperty(
            name='Max Spring Length',
            description='Maximum length for internal spring creation',
            default=0.0,
            min=0.0,
            max=1000.0,
            precision=2
        )

        bpy.types.Scene.ca_internalspringmaxdevision = bpy.props.FloatProperty(
            name='Max Spring Angle',
            description='Maximum angle for internal spring points',
            default=45.0,
            min=0.0,
            max=180.0,
            precision=1,
            subtype='ANGLE'
        )

        bpy.types.Scene.ca_internalspringtension = bpy.props.FloatProperty(
            name='Internal Tension',
            description='Internal spring tension resistance',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        bpy.types.Scene.ca_internalspringcompression = bpy.props.FloatProperty(
            name='Internal Compression',
            description='Internal spring compression resistance',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        bpy.types.Scene.ca_internalspringmaxtension = bpy.props.FloatProperty(
            name='Max Internal Tension',
            description='Maximum internal tension stiffness',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        bpy.types.Scene.ca_internalspringmaxcompression = bpy.props.FloatProperty(
            name='Max Internal Compression',
            description='Maximum internal compression stiffness',
            default=15.0,
            min=0.0,
            max=10000.0,
            precision=1
        )

        # Pressure properties
        bpy.types.Scene.ca_usepressure = bpy.props.BoolProperty(
            name='Use Pressure',
            description='Enable cloth pressure for inflatable objects',
            default=False
        )

        bpy.types.Scene.ca_pressure = bpy.props.FloatProperty(
            name='Pressure Force',
            description='Uniform pressure applied to the mesh',
            default=0.0,
            min=-1000.0,
            max=1000.0,
            precision=1
        )

        bpy.types.Scene.ca_pressurescale = bpy.props.FloatProperty(
            name='Pressure Scale',
            description='Ambient pressure scaling factor',
            default=1.0,
            min=0.0,
            max=100.0,
            precision=2
        )

        bpy.types.Scene.ca_pressurefluiddensity = bpy.props.FloatProperty(
            name='Fluid Density',
            description='Density of fluid inside the object',
            default=0.0,
            min=0.0,
            max=10.0,
            precision=3
        )

        # Collision properties
        bpy.types.Scene.ca_quality = bpy.props.IntProperty(
            name='Collision Quality',
            description='Quality of collision detection (higher = better)',
            default=2,
            min=1,
            max=20
        )

        bpy.types.Scene.ca_minimumdistance = bpy.props.FloatProperty(
            name='Collision Distance',
            description='Minimum distance for collision repulsion',
            default=0.015,
            min=0.001,
            max=1.0,
            precision=4,
            subtype='DISTANCE'
        )

        bpy.types.Scene.ca_impulseclamping = bpy.props.FloatProperty(
            name='Impulse Clamping',
            description='Prevents explosions in collision situations',
            default=0.0,
            min=0.0,
            max=100.0,
            precision=2
        )

        # Self-collision properties
        bpy.types.Scene.ca_selfcollision = bpy.props.BoolProperty(
            name='Self Collision',
            description='Enable cloth self-collision detection',
            default=True
        )

        bpy.types.Scene.ca_selfcollisionfriction = bpy.props.FloatProperty(
            name='Self Collision Friction',
            description='Friction coefficient for self-collisions',
            default=5.0,
            min=0.0,
            max=100.0,
            precision=1
        )

        bpy.types.Scene.ca_selfcollisiondistance = bpy.props.FloatProperty(
            name='Self Collision Distance',
            description='Distance threshold for self-collision',
            default=0.015,
            min=0.001,
            max=1.0,
            precision=4,
            subtype='DISTANCE'
        )

        bpy.types.Scene.ca_selfcollisionimpulseclamping = bpy.props.FloatProperty(
            name='Self Impulse Clamping',
            description='Prevents self-collision explosions',
            default=0.0,
            min=0.0,
            max=100.0,
            precision=2
        )

        # Control and status properties
        bpy.types.Scene.dropped = bpy.props.BoolProperty(
            name='Physics Active',
            description='Whether physics simulation is currently active',
            default=False
        )

        bpy.types.Scene.is_rigid = bpy.props.BoolProperty(
            name='Rigid Body Mode',
            description='Use rigid body physics (vs cloth physics)',
            default=True
        )

        # logger.info("Successfully registered all Physics Dropper properties")
        return True

    except Exception as e:
        logger.error("Failed to register properties", e)
        return False


def unregister_properties() -> bool:
    """Unregister all properties with safe cleanup."""
    try:
        # logger.info("Unregistering Physics Dropper properties")

        # Complete list of all properties to unregister
        properties_to_remove = [
            # Active rigidbody properties
            'a_shape', 'a_friction', 'a_bounciness', 'a_margin',
            'a_tra_damp', 'a_rot_damp', 'a_mass',
            # Passive rigidbody properties
            'p_shape', 'p_friction', 'p_bounciness', 'p_margin',
            # World settings
            'w_startframe', 'w_endframe', 'w_split_impulse',
            'w_subframes', 'w_solver_iterations',
            # Optimization properties
            'optimizehighpoly', 'p_optimizehighpoly',
            'a_voxelsize', 'a_decimaterate', 'p_voxelsize', 'p_decimaterate',
            # Force field properties
            'forcestrength', 'forcedistance', 'forceflow',
            # Earthquake properties
            'earthquake', 'earthquakex', 'earthquakey', 'earthquakez',
            # Cloth properties
            'c_a_presets', 'c_p_damping', 'c_p_thick_outer', 'c_p_thick_inner', 'c_p_friction', 'c_p_fatten',
            # Detailed cloth properties
            'ca_qualitysteps', 'ca_mass', 'ca_air_viscosity',
            'ca_stiff_tension', 'ca_stiff_compression', 'ca_stiff_shear', 'ca_stiff_bending',
            'ca_damp_tension', 'ca_damp_compression', 'ca_damp_shear', 'ca_damp_bending',
            'ca_internalsprings', 'ca_internalspringmaxlength', 'ca_internalspringmaxdevision',
            'ca_internalspringtension', 'ca_internalspringcompression',
            'ca_internalspringmaxtension', 'ca_internalspringmaxcompression',
            'ca_usepressure', 'ca_pressure', 'ca_pressurescale', 'ca_pressurefluiddensity',
            'ca_quality', 'ca_minimumdistance', 'ca_impulseclamping',
            'ca_selfcollision', 'ca_selfcollisionfriction', 'ca_selfcollisiondistance',
            'ca_selfcollisionimpulseclamping',
            # Control properties
            'dropped', 'is_rigid'
        ]

        removed_count = 0
        for prop_name in properties_to_remove:
            try:
                if hasattr(bpy.types.Scene, prop_name):
                    delattr(bpy.types.Scene, prop_name)
                    removed_count += 1
                    # logger.debug(f"Unregistered property: {prop_name}")
            except Exception as e:
                logger.warning(f"Failed to unregister property {prop_name}", e)

        # logger.info(f"Unregistered {removed_count}/{len(properties_to_remove)} properties")
        return True

    except Exception as e:
        logger.error("Error during property unregistration", e)
        return False


def register() -> bool:
    """Register the properties module."""
    return register_properties()


def unregister() -> bool:
    """Unregister the properties module."""
    return unregister_properties()