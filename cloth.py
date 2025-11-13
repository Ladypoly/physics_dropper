"""
Cloth physics functions for the Physics Dropper addon.

This module provides comprehensive cloth physics simulation functionality with
safe operations, validation, and error handling.
"""

import bpy
from typing import Optional, List, Any
from . import constants
from . import logger
from . import utils
from . import earthquake as eq
from .logger import log_errors, log_performance, SafeOperation, safe_context_access, safe_object_access

# Get logger instance
log = logger.logger

@log_errors
def set_cloth_parameter(
    ca_qualitysteps: int, ca_mass: float, ca_air_viscosity: float,
    ca_stiff_tension: float, ca_stiff_compression: float, ca_stiff_shear: float, ca_stiff_bending: float,
    ca_damp_tension: float, ca_damp_compression: float, ca_damp_shear: float, ca_damp_bending: float,
    ca_internalsprings: bool, ca_internalspringmaxlength: float, ca_internalspringmaxdevision: float,
    ca_internalspringtension: float, ca_internalspringcompression: float,
    ca_internalspringmaxtension: float, ca_internalspringmaxcompression: float,
    ca_usepressure: bool, ca_pressure: float, ca_pressurescale: float, ca_pressurefluiddensity: float,
    ca_quality: int, ca_minimumdistance: float, ca_impulseclamping: float,
    ca_selfcollision: bool, ca_selfcollisionfriction: float, ca_selfcollisiondistance: float,
    ca_selfcollisionimpulseclamping: float
) -> bool:
    """Set cloth parameters from given values.

    Args:
        ca_qualitysteps: Quality steps for cloth simulation
        ca_mass: Mass of the cloth
        ca_air_viscosity: Air viscosity affecting the cloth
        ca_stiff_tension: Tension stiffness
        ca_stiff_compression: Compression stiffness
        ca_stiff_shear: Shear stiffness
        ca_stiff_bending: Bending stiffness
        ca_damp_tension: Tension damping
        ca_damp_compression: Compression damping
        ca_damp_shear: Shear damping
        ca_damp_bending: Bending damping
        ca_internalsprings: Whether to use internal springs
        ca_internalspringmaxlength: Maximum internal spring length
        ca_internalspringmaxdevision: Maximum internal spring division
        ca_internalspringtension: Internal spring tension
        ca_internalspringcompression: Internal spring compression
        ca_internalspringmaxtension: Maximum internal spring tension
        ca_internalspringmaxcompression: Maximum internal spring compression
        ca_usepressure: Whether to use pressure
        ca_pressure: Pressure value
        ca_pressurescale: Pressure scale
        ca_pressurefluiddensity: Pressure fluid density
        ca_quality: Collision quality
        ca_minimumdistance: Minimum collision distance
        ca_impulseclamping: Impulse clamping
        ca_selfcollision: Whether to use self collision
        ca_selfcollisionfriction: Self collision friction
        ca_selfcollisiondistance: Self collision distance
        ca_selfcollisionimpulseclamping: Self collision impulse clamping

    Returns:
        bool: True if parameters were set successfully, False otherwise
    """
    with SafeOperation("set_cloth_parameters") as op:
        try:
            # Validate inputs
            if ca_qualitysteps < 1 or ca_qualitysteps > 100:
                log.warning(f"Quality steps {ca_qualitysteps} out of range [1-100], clamping")
                ca_qualitysteps = max(1, min(100, ca_qualitysteps))

            if ca_mass <= 0:
                log.warning(f"Invalid mass {ca_mass}, using default")
                ca_mass = constants.MASS_DEFAULT

            # Get scene safely
            scene = safe_context_access("scene")
            if not scene:
                log.error("Cannot access scene to set cloth parameters")
                return False

            log.debug(f"Setting cloth parameters with quality={ca_qualitysteps}, mass={ca_mass}")

            # Set basic properties
            scene.ca_qualitysteps = ca_qualitysteps
            scene.ca_mass = ca_mass
            scene.ca_air_viscosity = ca_air_viscosity

            # Set stiffness properties
            scene.ca_stiff_tension = ca_stiff_tension
            scene.ca_stiff_compression = ca_stiff_compression
            scene.ca_stiff_shear = ca_stiff_shear
            scene.ca_stiff_bending = ca_stiff_bending

            # Set damping properties
            scene.ca_damp_tension = ca_damp_tension
            scene.ca_damp_compression = ca_damp_compression
            scene.ca_damp_shear = ca_damp_shear
            scene.ca_damp_bending = ca_damp_bending

            # Set internal springs properties
            scene.ca_internalsprings = ca_internalsprings
            scene.ca_internalspringmaxlength = ca_internalspringmaxlength
            scene.ca_internalspringmaxdevision = ca_internalspringmaxdevision
            scene.ca_internalspringtension = ca_internalspringtension
            scene.ca_internalspringcompression = ca_internalspringcompression
            scene.ca_internalspringmaxtension = ca_internalspringmaxtension
            scene.ca_internalspringmaxcompression = ca_internalspringmaxcompression

            # Set pressure properties
            scene.ca_usepressure = ca_usepressure
            scene.ca_pressure = ca_pressure
            scene.ca_pressurescale = ca_pressurescale
            scene.ca_pressurefluiddensity = ca_pressurefluiddensity

            # Set collision properties
            scene.ca_quality = ca_quality
            scene.ca_minimumdistance = ca_minimumdistance
            scene.ca_impulseclamping = ca_impulseclamping

            # Set self collision properties
            scene.ca_selfcollision = ca_selfcollision
            scene.ca_selfcollisionfriction = ca_selfcollisionfriction
            scene.ca_selfcollisiondistance = ca_selfcollisiondistance
            scene.ca_selfcollisionimpulseclamping = ca_selfcollisionimpulseclamping

            log.info("Cloth parameters set successfully")
            op.success = True
            return True

        except AttributeError as e:
            log.error(f"Scene missing cloth properties: {e}")
            return False
        except (TypeError, ValueError) as e:
            log.error(f"Invalid parameter value: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error setting cloth parameters: {e}")
            return False

@log_errors
@log_performance("duplicate_cloth_objects")
def duplicate_cloth(name: str, display_as: str) -> bool:
    """Create a duplicate of selected objects for cloth collisions.

    Args:
        name: Name for the duplicated collision object
        display_as: Display type for the collision object

    Returns:
        bool: True if duplication was successful, False otherwise
    """
    with SafeOperation("duplicate_cloth_objects") as op:
        try:
            # Validate inputs
            if not name or not isinstance(name, str):
                log.error("Invalid name provided for cloth duplication")
                return False

            if display_as not in ['BOUNDS', 'WIRE', 'SOLID', 'TEXTURED']:
                log.warning(f"Invalid display type {display_as}, using WIRE")
                display_as = 'WIRE'

            # Get context safely
            context = bpy.context
            scene = safe_context_access("scene")
            view_layer = safe_context_access("view_layer")

            if not scene or not view_layer:
                log.error("Cannot access scene or view layer for cloth duplication")
                return False

            # Get selected objects
            selected_objects = list(context.selected_objects)
            if not selected_objects:
                log.warning("No objects selected for cloth duplication")
                return False

            log.debug(f"Duplicating {len(selected_objects)} objects for cloth collision")

            # Initialize cloth state
            utils.state.set_cloth("tojoin", [])
            tojoin_list = []

            # Duplicate selected objects
            for obj in selected_objects:
                if not utils.is_object_valid(obj):
                    log.warning(f"Skipping invalid object during duplication")
                    continue

                try:
                    new_obj = obj.copy()
                    if obj.data:
                        new_obj.data = obj.data.copy()

                    scene.collection.objects.link(new_obj)
                    tojoin_list.append(new_obj)
                    view_layer.objects.active = new_obj

                    log.debug(f"Duplicated object: {obj.name} -> {new_obj.name}")

                except Exception as e:
                    log.warning(f"Failed to duplicate object {obj.name}: {e}")
                    continue

            if not tojoin_list:
                log.error("Failed to duplicate any objects")
                return False

            # Update state
            utils.state.set_cloth("tojoin", tojoin_list)

            # Deselect all objects safely
            try:
                bpy.ops.object.select_all(action='DESELECT')
            except RuntimeError as e:
                log.warning(f"Failed to deselect objects: {e}")

            # Select duplicates and make single user
            active_count = 0
            for obj in tojoin_list:
                if utils.is_object_valid(obj):
                    try:
                        obj.select_set(True)
                        view_layer.objects.active = obj
                        active_count += 1
                    except ReferenceError:
                        log.warning(f"Object was deleted during selection")
                        continue

            if active_count == 0:
                log.error("No valid objects to join")
                return False

            # Make single user
            try:
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True)
                log.debug("Made objects single user")
            except RuntimeError as e:
                log.warning(f"Failed to make single user: {e}")

            # Join objects
            try:
                if active_count > 1:
                    bpy.ops.object.join()
                    log.debug("Joined duplicate objects")
            except RuntimeError as e:
                log.error(f"Failed to join objects: {e}")
                return False

            # Apply transformations
            try:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                log.debug("Applied transformations")
            except RuntimeError as e:
                log.warning(f"Failed to apply transformations: {e}")

            # Configure joined object
            active_object = safe_context_access("active_object")
            if active_object:
                try:
                    active_object.display_type = display_as
                    active_object.name = name
                    active_object.parent_bone = ""

                    # Add optimization modifiers
                    _add_cloth_optimization_modifiers(active_object)

                    log.info(f"Successfully created cloth collision object: {name}")
                    op.success = True
                    return True

                except Exception as e:
                    log.error(f"Failed to configure collision object: {e}")
                    return False
            else:
                log.error("No active object after joining")
                return False

        except Exception as e:
            log.error(f"Unexpected error in cloth duplication: {e}")
            return False

def _add_cloth_optimization_modifiers(obj: Any) -> None:
    """Add optimization modifiers to cloth collision object.

    Args:
        obj: The object to add modifiers to
    """
    try:
        scene = safe_context_access("scene")
        if not scene:
            return

        # Add remesh modifier if voxel size is set
        voxel_size = safe_object_access(scene, "p_voxelsize", 0.0)
        if voxel_size != 0.0:
            remesh = obj.modifiers.new(name="Remesh", type='REMESH')
            remesh.voxel_size = max(constants.VOXEL_SIZE_MIN, min(constants.VOXEL_SIZE_MAX, voxel_size))
            log.debug(f"Added remesh modifier with voxel size: {remesh.voxel_size}")

        # Add decimate modifier
        decimate_rate = safe_object_access(scene, "p_decimaterate", constants.DECIMATE_RATIO_DEFAULT)
        decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.ratio = max(constants.DECIMATE_RATIO_MIN, min(constants.DECIMATE_RATIO_MAX, decimate_rate))
        log.debug(f"Added decimate modifier with ratio: {decimate.ratio}")

        # Convert to mesh
        try:
            bpy.ops.object.convert(target='MESH')
            log.debug("Converted object to mesh")
        except RuntimeError as e:
            log.warning(f"Failed to convert to mesh: {e}")

    except Exception as e:
        log.warning(f"Failed to add optimization modifiers: {e}")

@log_errors
def add_collision_modifier(obj: Any) -> bool:
    """Add collision modifier to an object.

    Args:
        obj: The object to add collision modifier to

    Returns:
        bool: True if collision modifier was added successfully, False otherwise
    """
    with SafeOperation("add_collision_modifier") as op:
        try:
            if not utils.is_object_valid(obj):
                log.error("Invalid object provided for collision modifier")
                return False

            # Get scene properties safely
            scene = safe_context_access("scene")
            if not scene:
                log.error("Cannot access scene for collision properties")
                return False

            log.debug(f"Adding collision modifier to object: {obj.name}")

            # Add collision modifier
            try:
                bpy.ops.object.modifier_add(type='COLLISION')
            except RuntimeError as e:
                log.error(f"Failed to add collision modifier: {e}")
                return False

            # Configure collision properties safely
            collision = safe_object_access(obj, "collision")
            if collision:
                try:
                    collision.damping = safe_object_access(scene, "c_p_damping", constants.DAMPING_DEFAULT)
                    collision.thickness_outer = safe_object_access(scene, "c_p_thick_outer", 0.02)
                    collision.thickness_inner = safe_object_access(scene, "c_p_thick_inner", 0.02)
                    collision.cloth_friction = safe_object_access(scene, "c_p_friction", constants.FRICTION_DEFAULT)

                    log.debug("Collision modifier properties configured")
                except Exception as e:
                    log.warning(f"Failed to set some collision properties: {e}")
            else:
                log.warning("Collision modifier added but properties not accessible")

            log.info(f"Collision modifier added to {obj.name}")
            op.success = True
            return True

        except Exception as e:
            log.error(f"Unexpected error adding collision modifier: {e}")
            return False

@log_errors
def set_cloth_passive() -> bool:
    """Set up passive object for cloth simulation.

    Returns:
        bool: True if passive setup was successful, False otherwise
    """
    with SafeOperation("set_cloth_passive") as op:
        try:
            # Get passive object from state
            passive_obj = utils.state.get_cloth("passive")
            if not passive_obj or not utils.is_object_valid(passive_obj):
                log.error("No valid passive object found")
                return False

            log.debug(f"Setting up passive cloth object: {passive_obj.name}")

            # Set active object safely
            view_layer = safe_context_access("view_layer")
            if view_layer:
                view_layer.objects.active = passive_obj

            # Add collision modifier
            if not add_collision_modifier(passive_obj):
                log.error("Failed to add collision modifier to passive object")
                return False

            # Set up earthquake if available
            try:
                eq.earthquake_function(passive_obj, 0, 0)
                eq.earthquake_function(passive_obj, 1, 1)
                eq.earthquake_function(passive_obj, 2, 2)
                log.debug("Earthquake effects applied to passive object")
            except Exception as e:
                log.warning(f"Failed to apply earthquake effects: {e}")

            log.info("Passive cloth object setup completed")
            op.success = True
            return True

        except Exception as e:
            log.error(f"Unexpected error setting up passive cloth: {e}")
            return False

@log_errors
def set_cloth_settings(cloth_modifier: Any) -> bool:
    """Configure settings for a cloth modifier.

    Args:
        cloth_modifier: The cloth modifier to configure

    Returns:
        bool: True if settings were configured successfully, False otherwise
    """
    with SafeOperation("set_cloth_settings") as op:
        try:
            if not cloth_modifier:
                log.error("No cloth modifier provided")
                return False

            # Get scene properties safely
            scene = safe_context_access("scene")
            if not scene:
                log.error("Cannot access scene for cloth settings")
                return False

            log.debug("Configuring cloth modifier settings")

            # Get cloth settings and collision settings safely
            settings = safe_object_access(cloth_modifier, "settings")
            collision_settings = safe_object_access(cloth_modifier, "collision_settings")

            if not settings:
                log.error("Cannot access cloth modifier settings")
                return False

            # Set quality and general properties
            settings.quality = safe_object_access(scene, "ca_qualitysteps", 5)
            settings.mass = safe_object_access(scene, "ca_mass", constants.MASS_DEFAULT)
            settings.air_damping = safe_object_access(scene, "ca_air_viscosity", 1.0)

            # Set stiffness properties
            settings.tension_stiffness = safe_object_access(scene, "ca_stiff_tension", 15.0)
            settings.compression_stiffness = safe_object_access(scene, "ca_stiff_compression", 15.0)
            settings.shear_stiffness = safe_object_access(scene, "ca_stiff_shear", 15.0)
            settings.bending_stiffness = safe_object_access(scene, "ca_stiff_bending", 0.5)

            # Set damping properties
            settings.tension_damping = safe_object_access(scene, "ca_damp_tension", 5.0)
            settings.compression_damping = safe_object_access(scene, "ca_damp_compression", 5.0)
            settings.shear_damping = safe_object_access(scene, "ca_damp_shear", 5.0)
            settings.bending_damping = safe_object_access(scene, "ca_damp_bending", 0.5)

            # Set internal springs properties
            settings.use_internal_springs = safe_object_access(scene, "ca_internalsprings", False)
            settings.internal_spring_max_length = safe_object_access(scene, "ca_internalspringmaxlength", 0.0)
            settings.internal_spring_max_diversion = safe_object_access(scene, "ca_internalspringmaxdevision", 45.0)
            settings.internal_tension_stiffness = safe_object_access(scene, "ca_internalspringtension", 15.0)
            settings.internal_compression_stiffness = safe_object_access(scene, "ca_internalspringcompression", 15.0)
            settings.internal_tension_stiffness_max = safe_object_access(scene, "ca_internalspringmaxtension", 15.0)
            settings.internal_compression_stiffness_max = safe_object_access(scene, "ca_internalspringmaxcompression", 15.0)

            # Set pressure properties
            settings.use_pressure = safe_object_access(scene, "ca_usepressure", False)
            settings.uniform_pressure_force = safe_object_access(scene, "ca_pressure", 0.0)
            settings.pressure_factor = safe_object_access(scene, "ca_pressurescale", 1.0)
            settings.fluid_density = safe_object_access(scene, "ca_pressurefluiddensity", 0.0)

            # Set collision properties if collision settings exist
            if collision_settings:
                collision_settings.collision_quality = safe_object_access(scene, "ca_quality", 2)
                collision_settings.distance_min = safe_object_access(scene, "ca_minimumdistance", 0.015)
                collision_settings.impulse_clamp = safe_object_access(scene, "ca_impulseclamping", 0.0)

                # Set self collision properties
                collision_settings.use_self_collision = safe_object_access(scene, "ca_selfcollision", True)
                collision_settings.self_friction = safe_object_access(scene, "ca_selfcollisionfriction", 5.0)
                collision_settings.self_distance_min = safe_object_access(scene, "ca_selfcollisiondistance", 0.015)
                collision_settings.self_impulse_clamp = safe_object_access(scene, "ca_selfcollisionimpulseclamping", 0.0)
            else:
                log.warning("Collision settings not accessible on cloth modifier")

            log.info("Cloth modifier settings configured successfully")
            op.success = True
            return True

        except AttributeError as e:
            log.error(f"Missing cloth modifier attributes: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error configuring cloth settings: {e}")
            return False

@log_errors
@log_performance("set_cloth_active_objects")
def set_cloth_active() -> bool:
    """Set up active cloth objects.

    Returns:
        bool: True if active cloth setup was successful, False otherwise
    """
    with SafeOperation("set_cloth_active_objects") as op:
        try:
            # Get active objects from state
            active_objects = utils.state.get_cloth("active")
            if not active_objects:
                log.warning("No active cloth objects found")
                return True  # Not an error, just nothing to do

            # Get context objects safely
            scene = safe_context_access("scene")
            view_layer = safe_context_access("view_layer")

            if not scene or not view_layer:
                log.error("Cannot access scene or view layer for cloth setup")
                return False

            log.debug(f"Setting up {len(active_objects)} active cloth objects")

            # Deselect all objects safely
            try:
                bpy.ops.object.select_all(action='DESELECT')
            except RuntimeError as e:
                log.warning(f"Failed to deselect objects: {e}")

            successful_count = 0

            # Configure each active cloth object
            for obj in active_objects:
                if not utils.is_object_valid(obj):
                    log.warning(f"Skipping invalid object in active cloth list")
                    continue

                try:
                    log.debug(f"Processing cloth object: {obj.name}")

                    # Select and activate object
                    obj.select_set(True)
                    view_layer.objects.active = obj

                    # Add cloth modifier
                    try:
                        bpy.ops.object.modifier_add(type='CLOTH')
                    except RuntimeError as e:
                        log.error(f"Failed to add cloth modifier to {obj.name}: {e}")
                        continue

                    # Get the active modifier (should be the cloth modifier we just added)
                    active_modifier = safe_object_access(obj, "modifiers")
                    if active_modifier and len(active_modifier) > 0:
                        cloth_modifier = active_modifier[-1]  # Get the last added modifier

                        # Set end frame safely
                        point_cache = safe_object_access(cloth_modifier, "point_cache")
                        if point_cache:
                            end_frame = safe_object_access(scene, "w_endframe", constants.DEFAULT_FRAME_END)
                            point_cache.frame_end = end_frame
                            log.debug(f"Set cloth end frame to: {end_frame}")

                        # Configure cloth settings
                        if not set_cloth_settings(cloth_modifier):
                            log.warning(f"Failed to configure cloth settings for {obj.name}")
                    else:
                        log.error(f"No modifiers found on {obj.name} after adding cloth modifier")
                        continue

                    # Add collision modifier
                    if not add_collision_modifier(obj):
                        log.warning(f"Failed to add collision modifier to {obj.name}")
                        # Continue anyway, cloth can work without collision

                    successful_count += 1
                    log.debug(f"Successfully configured cloth object: {obj.name}")

                except ReferenceError:
                    log.warning(f"Object was deleted during cloth setup")
                    continue
                except Exception as e:
                    log.error(f"Unexpected error setting up cloth on {obj.name}: {e}")
                    continue

            if successful_count == 0:
                log.error("Failed to set up any active cloth objects")
                return False

            # Start animation safely
            try:
                bpy.ops.screen.animation_play()
                log.info(f"Started animation for {successful_count} cloth objects")
            except RuntimeError as e:
                log.warning(f"Failed to start animation: {e}")
                # This is not critical, cloth can be manually animated

            log.info(f"Active cloth setup completed for {successful_count} objects")
            op.success = True
            return True

        except Exception as e:
            log.error(f"Unexpected error setting up active cloth objects: {e}")
            return False

@log_errors
@log_performance("apply_cloth_simulation")
def apply_cloth() -> bool:
    """Apply cloth simulation results and clean up.

    Returns:
        bool: True if cloth application was successful, False otherwise
    """
    with SafeOperation("apply_cloth_simulation") as op:
        try:
            # Get context objects safely
            scene = safe_context_access("scene")
            view_layer = safe_context_access("view_layer")

            if not scene or not view_layer:
                log.error("Cannot access scene or view layer for cloth application")
                return False

            log.debug("Starting cloth simulation application")

            # Clear dropped flag
            if hasattr(scene, 'dropped'):
                scene.dropped = False

            # Get active and passive objects from state
            active_objects = utils.state.get_cloth("active")
            passive_obj = utils.state.get_cloth("passive")

            # Deselect all objects safely
            try:
                bpy.ops.object.select_all(action='DESELECT')
            except RuntimeError as e:
                log.warning(f"Failed to deselect objects: {e}")

            # Select and convert active objects to mesh
            converted_count = 0
            if active_objects:
                for obj in active_objects:
                    if utils.is_object_valid(obj):
                        try:
                            obj.select_set(True)
                            view_layer.objects.active = obj
                            converted_count += 1
                        except ReferenceError:
                            log.warning(f"Active cloth object was deleted during application")
                            continue

                if converted_count > 0:
                    try:
                        bpy.ops.object.convert(target='MESH')
                        log.debug(f"Converted {converted_count} cloth objects to mesh")

                        # Set origin to geometry
                        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                        log.debug("Set origin to geometry for cloth objects")
                    except RuntimeError as e:
                        log.warning(f"Failed to convert cloth objects to mesh: {e}")
                else:
                    log.warning("No valid active cloth objects to convert")

            # Delete passive object safely
            if passive_obj and utils.is_object_valid(passive_obj):
                try:
                    bpy.ops.object.select_all(action='DESELECT')
                    passive_obj.select_set(True)
                    view_layer.objects.active = passive_obj
                    utils.safe_object_delete(passive_obj)
                    log.debug("Deleted passive cloth object")
                except Exception as e:
                    log.warning(f"Failed to delete passive object: {e}")
            else:
                log.warning("No valid passive object to delete")

            # Final selection of active objects
            try:
                bpy.ops.object.select_all(action='DESELECT')
                final_count = 0
                if active_objects:
                    for obj in active_objects:
                        if utils.is_object_valid(obj):
                            obj.select_set(True)
                            view_layer.objects.active = obj
                            final_count += 1

                log.debug(f"Final selection: {final_count} cloth objects")
            except Exception as e:
                log.warning(f"Failed to make final selection: {e}")

            # Clear state
            utils.state.set_cloth("active", [])
            utils.state.set_cloth("passive", None)
            utils.state.set_cloth("tojoin", [])

            # Reset frame
            try:
                scene.frame_current = constants.DEFAULT_FRAME_START
                log.debug("Reset frame to start")
            except Exception as e:
                log.warning(f"Failed to reset frame: {e}")

            log.info("Cloth simulation application completed successfully")
            op.success = True
            return True

        except Exception as e:
            log.error(f"Unexpected error applying cloth simulation: {e}")
            return False

@log_errors
@log_performance("drop_cloth_simulation")
def drop_cloth() -> bool:
    """Initialize cloth physics simulation.

    Returns:
        bool: True if cloth simulation was initialized successfully, False otherwise
    """
    with SafeOperation("drop_cloth_simulation") as op:
        try:
            # Get context objects safely
            context = bpy.context
            scene = safe_context_access("scene")
            view_layer = safe_context_access("view_layer")

            if not scene or not view_layer:
                log.error("Cannot access scene or view layer for cloth initialization")
                return False

            log.debug("Starting cloth simulation initialization")

            # Reset state
            utils.state.set_cloth("active", [])
            utils.state.set_cloth("passive", None)
            utils.state.set_cloth("tojoin", [])

            # Set dropped flag
            if hasattr(scene, 'dropped'):
                scene.dropped = True

            # Collect active mesh objects from selection (including collection instances)
            selected_objects = list(context.selected_objects)

            if not selected_objects:
                log.error("No objects selected for cloth simulation")
                return False

            # Use utility function to get mesh objects (handles collection instances)
            active_objects = utils.get_mesh_objects_from_selection(selected_objects)

            if active_objects:
                # Set the last object as active
                if len(active_objects) > 0:
                    view_layer.objects.active = active_objects[-1]
                    log.debug(f"Added {len(active_objects)} active cloth object(s)")

            if not active_objects:
                log.error("No mesh objects or collection instances found in selection for cloth simulation")
                return False

            # Update state with active objects
            utils.state.set_cloth("active", active_objects)
            log.info(f"Found {len(active_objects)} active cloth objects")

            # Invert selection to find collision objects
            try:
                bpy.ops.object.select_all(action='INVERT')
            except RuntimeError as e:
                log.error(f"Failed to invert selection: {e}")
                return False

            # Filter out non-mesh objects and non-instances from inverted selection
            collision_objects = []
            for obj in context.selected_objects:
                if utils.is_object_valid(obj):
                    # Keep mesh objects and collection instances
                    if obj.type == "MESH" or utils.is_collection_instance(obj):
                        collision_objects.append(obj)
                    else:
                        try:
                            obj.select_set(False)
                        except ReferenceError:
                            continue

            log.info(f"Found {len(collision_objects)} potential collision objects")

            # Create passive collision object
            if not duplicate_cloth(constants.COLLIDER_OBJECT_NAME, 'WIRE'):
                log.error("Failed to create collision object")
                return False

            # Get the created passive object
            passive_obj = safe_context_access("active_object")
            if not passive_obj:
                log.error("No passive object created")
                return False

            # Update state with passive object
            utils.state.set_cloth("passive", passive_obj)
            log.debug(f"Created passive collision object: {passive_obj.name}")

            # Set up passive and active objects
            if not set_cloth_passive():
                log.error("Failed to set up passive cloth object")
                return False

            if not set_cloth_active():
                log.error("Failed to set up active cloth objects")
                return False

            log.info("Cloth simulation initialized successfully")
            op.success = True
            return True

        except Exception as e:
            log.error(f"Unexpected error initializing cloth simulation: {e}")
            return False
