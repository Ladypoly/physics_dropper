"""
Rigidbody physics functions for the Physics Dropper addon.
"""

import bpy
import random
from typing import List, Optional, Tuple, Any
from . import constants
from . import utils
from .logger import logger, SafeOperation, log_errors, log_performance, safe_object_access, safe_context_access


@log_performance("duplicate_collision_objects")
def duplicate(name: str, display_as: str) -> bool:
    """Create a duplicate of selected objects for collision with improved safety."""
    try:
        with SafeOperation("duplicate_collision_objects") as op:
            # Reset the join list safely
            utils.state.set_rigidbody("to_join", [])

            # Get selected objects safely
            selected_objects = safe_context_access("selected_objects", [])
            if not selected_objects:
                logger.warning("No objects selected for duplication")
                return False

            # Validate we can access scene
            scene = safe_context_access("scene")
            view_layer = safe_context_access("view_layer")
            if not scene or not view_layer:
                logger.error("Cannot access scene or view layer for duplication")
                return False

            duplicated_objects = []

            # Duplicate each selected object
            for obj in selected_objects:
                if not utils.is_object_valid(obj):
                    logger.warning(f"Skipping invalid object during duplication")
                    continue

                try:
                    # Create duplicate
                    new_obj = obj.copy()
                    if hasattr(obj, 'data') and obj.data:
                        new_obj.data = obj.data.copy()

                    # Link to scene
                    scene.collection.objects.link(new_obj)
                    duplicated_objects.append(new_obj)
                    view_layer.objects.active = new_obj

                    logger.debug(f"Duplicated object: {obj.name} -> {new_obj.name}")

                except Exception as e:
                    logger.warning(f"Failed to duplicate object {safe_object_access(obj, 'name', 'Unknown')}", e)

            if not duplicated_objects:
                logger.error("No objects were successfully duplicated")
                return False

            # Store duplicated objects
            utils.state.set_rigidbody("to_join", duplicated_objects)

            # Deselect all objects safely
            if not utils.safe_deselect_all():
                logger.warning("Failed to deselect all objects")

            # Select and prepare duplicated objects
            valid_objects = 0
            for obj in duplicated_objects:
                if utils.is_object_valid(obj):
                    if utils.safe_select_object(obj):
                        valid_objects += 1

                        # Make single user
                        try:
                            bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True)
                            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                        except Exception as e:
                            logger.warning(f"Failed to make object single user: {obj.name}", e)

            if valid_objects == 0:
                logger.error("No valid objects to join")
                return False

            # Join selected objects
            try:
                bpy.ops.object.join()
                logger.debug(f"Joined {valid_objects} objects")
            except Exception as e:
                logger.error("Failed to join objects", e)
                return False

            # Get the joined object
            active_object = safe_context_access("active_object")
            if not active_object:
                logger.error("No active object after joining")
                return False

            # Apply transformations safely
            try:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            except Exception as e:
                logger.warning("Failed to apply transformations", e)

            # Customize the joined object
            try:
                active_object.display_type = display_as
                active_object.name = name
                if hasattr(active_object, 'parent_bone'):
                    active_object.parent_bone = ""
            except Exception as e:
                logger.warning("Failed to customize joined object", e)

            # Apply optimization if enabled
            optimize_high_poly = safe_context_access("scene.p_optimizehighpoly", False)
            if optimize_high_poly:
                if not _apply_optimization_modifiers(active_object):
                    logger.warning("Optimization modifiers failed but continuing")

            logger.info(f"Successfully created collision object: {name}")
            op.success = True
            return True

    except Exception as e:
        logger.error("Critical error in duplicate function", e)
        return False


def _apply_optimization_modifiers(obj: Any) -> bool:
    """Apply optimization modifiers to an object."""
    try:
        scene = safe_context_access("scene")
        if not scene:
            return False

        # Add remesh modifier if voxel size is set
        voxel_size = getattr(scene, 'p_voxelsize', 0.0)
        if voxel_size > 0.0:
            try:
                remesh = obj.modifiers.new(name="Remesh", type='REMESH')
                remesh.voxel_size = min(voxel_size, constants.VOXEL_SIZE_MAX)
                logger.debug(f"Added remesh modifier with voxel size: {remesh.voxel_size}")
            except Exception as e:
                logger.warning("Failed to add remesh modifier", e)
                return False

        # Add decimate modifier
        decimate_rate = getattr(scene, 'p_decimaterate', constants.DECIMATE_RATIO_DEFAULT)
        try:
            decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.ratio = max(constants.DECIMATE_RATIO_MIN,
                               min(constants.DECIMATE_RATIO_MAX, decimate_rate))
            logger.debug(f"Added decimate modifier with ratio: {decimate.ratio}")
        except Exception as e:
            logger.warning("Failed to add decimate modifier", e)
            return False

        # Convert to mesh
        try:
            bpy.ops.object.convert(target='MESH')
            logger.debug("Converted object to mesh")
        except Exception as e:
            logger.warning("Failed to convert to mesh", e)
            return False

        return True

    except Exception as e:
        logger.error("Error applying optimization modifiers", e)
        return False


@log_errors
def set_world_settings() -> bool:
    """Set up physics world settings for the simulation with improved safety."""
    try:
        with SafeOperation("set_world_settings"):
            scene = safe_context_access("scene")
            if not scene:
                logger.error(constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                return False

            # Ensure rigidbody world exists
            rb_world = safe_context_access("scene.rigidbody_world")
            if not rb_world:
                logger.info("Creating rigidbody world")
                try:
                    bpy.ops.rigidbody.world_add()
                    rb_world = safe_context_access("scene.rigidbody_world")
                except Exception as e:
                    logger.error("Failed to create rigidbody world", e)
                    return False

            if not rb_world:
                logger.error(constants.ERROR_MESSAGES['NO_RIGIDBODY_WORLD'])
                return False

            # Store original settings safely
            try:
                # Access nested properties safely
                point_cache = safe_object_access(rb_world, "point_cache")
                effector_weights = safe_object_access(rb_world, "effector_weights")

                original_settings = [
                    safe_object_access(point_cache, "frame_start", constants.DEFAULT_FRAME_START) if point_cache else constants.DEFAULT_FRAME_START,
                    safe_object_access(point_cache, "frame_end", constants.DEFAULT_FRAME_END) if point_cache else constants.DEFAULT_FRAME_END,
                    safe_object_access(rb_world, "substeps_per_frame", constants.DEFAULT_SUBSTEPS),
                    safe_object_access(rb_world, "solver_iterations", constants.DEFAULT_SOLVER_ITERATIONS),
                    safe_object_access(rb_world, "enabled", True),
                    safe_object_access(rb_world, "use_split_impulse", True),
                    getattr(scene, 'frame_end', constants.DEFAULT_FRAME_END),
                    safe_object_access(effector_weights, "gravity", 1.0) if effector_weights else 1.0
                ]
                utils.state.set_rigidbody("world_settings", original_settings)
                logger.debug("Stored original world settings")

            except Exception as e:
                logger.warning("Failed to store some original settings", e)
                utils.state.set_rigidbody("world_settings", [])

            # Apply new settings with validation
            try:
                # Substeps and solver settings
                substeps = getattr(scene, 'w_subframes', constants.DEFAULT_SUBSTEPS)
                rb_world.substeps_per_frame = max(1, min(100, substeps))

                solver_iterations = getattr(scene, 'w_solver_iterations', constants.DEFAULT_SOLVER_ITERATIONS)
                rb_world.solver_iterations = max(1, min(100, solver_iterations))

                # Frame settings
                start_frame = getattr(scene, 'w_startframe', constants.DEFAULT_FRAME_START)
                end_frame = getattr(scene, 'w_endframe', constants.DEFAULT_FRAME_END)

                # Validate frame range
                if start_frame >= end_frame:
                    logger.warning(f"Invalid frame range: {start_frame}-{end_frame}, using defaults")
                    start_frame = constants.DEFAULT_FRAME_START
                    end_frame = constants.DEFAULT_FRAME_END

                # Apply frame settings
                if hasattr(rb_world, 'point_cache'):
                    rb_world.point_cache.frame_start = start_frame
                    rb_world.point_cache.frame_end = end_frame
                    rb_world.point_cache.frame_step = 1
                    rb_world.point_cache.index = 0

                # World settings
                rb_world.enabled = True
                rb_world.use_split_impulse = getattr(scene, 'w_split_impulse', True)

                # Scene frame settings
                scene.frame_current = constants.DEFAULT_FRAME_START
                scene.frame_start = constants.DEFAULT_FRAME_START
                scene.frame_end = end_frame
                scene.frame_step = 1

                # Gravity
                if hasattr(rb_world, 'effector_weights'):
                    rb_world.effector_weights.gravity = 1.0

                logger.info(f"Applied world settings: frames {start_frame}-{end_frame}, substeps {substeps}")
                return True

            except Exception as e:
                logger.error("Failed to apply world settings", e)
                return False

    except Exception as e:
        logger.error("Critical error in set_world_settings", e)
        return False


@log_errors
def revert_world_settings() -> bool:
    """Revert physics world settings to their original values."""
    try:
        with SafeOperation("revert_world_settings"):
            original_settings = utils.state.get_rigidbody("world_settings")
            if not original_settings:
                logger.info("No original settings to revert")
                return True

            rb_world = safe_context_access("scene.rigidbody_world")
            scene = safe_context_access("scene")

            if not rb_world or not scene:
                logger.warning("Cannot access rigidbody world or scene for settings revert")
                return False

            try:
                # Revert world settings
                if len(original_settings) >= 8:
                    if hasattr(rb_world, 'substeps_per_frame'):
                        rb_world.substeps_per_frame = int(original_settings[2])
                    if hasattr(rb_world, 'solver_iterations'):
                        rb_world.solver_iterations = int(original_settings[3])

                    # Revert frame settings
                    if hasattr(rb_world, 'point_cache'):
                        rb_world.point_cache.frame_start = int(original_settings[0])
                        rb_world.point_cache.frame_end = int(original_settings[1])
                        rb_world.point_cache.frame_step = 1
                        rb_world.point_cache.index = 0

                    rb_world.enabled = bool(original_settings[4])
                    rb_world.use_split_impulse = bool(original_settings[5])

                    # Revert scene settings
                    scene.frame_current = constants.DEFAULT_FRAME_START
                    scene.frame_start = constants.DEFAULT_FRAME_START
                    scene.frame_end = int(original_settings[6])
                    scene.frame_step = 1

                    # Revert gravity
                    if hasattr(rb_world, 'effector_weights'):
                        rb_world.effector_weights.gravity = float(original_settings[7])

                # Clear the stored settings
                utils.state.set_rigidbody("world_settings", [])
                logger.info("Successfully reverted world settings")
                return True

            except Exception as e:
                logger.error("Error reverting specific settings", e)
                return False

    except Exception as e:
        logger.error("Critical error in revert_world_settings", e)
        return False


@log_errors
def set_rigid_passive() -> bool:
    """Set up passive rigidbody object with improved error handling."""
    try:
        with SafeOperation("set_rigid_passive"):
            # Set world settings first
            if not set_world_settings():
                logger.error("Failed to set world settings")
                return False

            # Get the passive object
            passive_obj = utils.state.get_rigidbody("passive")
            if not passive_obj or not utils.is_object_valid(passive_obj):
                logger.error("No valid passive object to configure")
                return False

            # Make sure it's selected and active
            utils.safe_deselect_all()
            if not utils.safe_select_object(passive_obj):
                logger.error("Failed to select passive object")
                return False

            # Add rigidbody
            try:
                bpy.ops.rigidbody.objects_add(type='PASSIVE')
                logger.debug("Added passive rigidbody")
            except Exception as e:
                logger.error("Failed to add passive rigidbody", e)
                return False

            # Configure rigidbody settings
            if not _configure_passive_rigidbody(passive_obj):
                logger.warning("Some passive rigidbody settings failed")

            # Add earthquake effects to passive object (collider)
            try:
                from . import earthquake as eq

                # Apply earthquake effects (keyframes are handled within earthquake_function)
                success_count = 0
                if eq.earthquake_function(passive_obj, 0, 0):  # X-axis
                    success_count += 1
                if eq.earthquake_function(passive_obj, 1, 1):  # Y-axis
                    success_count += 1
                if eq.earthquake_function(passive_obj, 2, 2):  # Z-axis
                    success_count += 1

                if success_count > 0:
                    logger.info(f"Applied earthquake effects to collision object on {success_count}/3 axes")
                else:
                    logger.warning("Failed to apply earthquake effects to collision object")

            except Exception as e:
                logger.warning("Failed to apply earthquake effects to collision object", e)

            logger.info("Successfully configured passive rigidbody object")
            return True

    except Exception as e:
        logger.error("Critical error in set_rigid_passive", e)
        return False


def _configure_passive_rigidbody(obj: Any) -> bool:
    """Configure settings for a passive rigidbody object."""
    try:
        scene = safe_context_access("scene")
        if not scene or not hasattr(obj, 'rigid_body'):
            return False

        rigid_body = obj.rigid_body
        if not rigid_body:
            logger.warning("Object has no rigid_body property")
            return False

        # Set collision shape
        shape = getattr(scene, 'p_shape', 'MESH')
        if shape in [item[0] for item in constants.COLLISION_SHAPES]:
            rigid_body.collision_shape = shape
        else:
            rigid_body.collision_shape = 'MESH'
            logger.warning(f"Invalid collision shape {shape}, using MESH")

        # Set physical properties with validation
        friction = getattr(scene, 'p_friction', constants.FRICTION_DEFAULT)
        rigid_body.friction = max(constants.FRICTION_MIN, min(constants.FRICTION_MAX, friction))

        bounciness = getattr(scene, 'p_bounciness', constants.BOUNCINESS_DEFAULT)
        rigid_body.restitution = max(constants.BOUNCINESS_MIN, min(constants.BOUNCINESS_MAX, bounciness))

        margin = getattr(scene, 'p_margin', constants.PHYSICS_MARGIN_DEFAULT)
        rigid_body.collision_margin = max(constants.PHYSICS_MARGIN_MIN, min(constants.PHYSICS_MARGIN_MAX, margin))

        # Set other properties
        rigid_body.use_margin = True
        rigid_body.kinematic = True
        rigid_body.mesh_source = 'FINAL'

        mass = getattr(scene, 'a_mass', constants.MASS_DEFAULT)
        rigid_body.mass = max(constants.MASS_MIN, min(constants.MASS_MAX, mass))

        logger.debug(f"Configured passive rigidbody: shape={shape}, friction={friction}, bounciness={bounciness}")
        return True

    except Exception as e:
        logger.error("Error configuring passive rigidbody", e)
        return False


@log_performance("setup_active_rigidbodies")
def set_rigid_active() -> bool:
    """Set up active rigidbody objects with improved safety."""
    try:
        with SafeOperation("set_rigid_active"):
            # Get active objects
            active_objects = utils.state.get_rigidbody("active")
            if not active_objects:
                logger.warning("No active objects to configure")
                return False

            # Check optimization settings
            scene = safe_context_access("scene")
            use_optimization = scene and getattr(scene, 'optimizehighpoly', False)

            # Select appropriate objects (low-poly proxies if optimization is enabled)
            if use_optimization:
                objects_to_configure = utils.state.get_rigidbody("low_poly_list")
                if not objects_to_configure:
                    logger.warning("Optimization enabled but no low-poly objects found")
                    objects_to_configure = active_objects
            else:
                objects_to_configure = active_objects

            if not objects_to_configure:
                logger.error("No objects to configure for active rigidbody")
                return False

            # Deselect all and select target objects
            utils.safe_deselect_all()

            valid_objects = []
            for obj in objects_to_configure:
                if utils.is_object_valid(obj):
                    if utils.safe_select_object(obj):
                        valid_objects.append(obj)

            if not valid_objects:
                logger.error("No valid objects selected for active rigidbody setup")
                return False

            logger.info(f"Configuring {len(valid_objects)} active rigidbody objects")

            # Set origin to center of mass
            try:
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
                logger.debug("Set origins to center of volume")
            except Exception as e:
                logger.warning("Failed to set origins", e)

            # Add rigidbody
            try:
                bpy.ops.rigidbody.objects_add(type='ACTIVE')
                logger.debug("Added active rigidbodies")
            except Exception as e:
                logger.error("Failed to add active rigidbodies", e)
                return False

            # Configure each object's rigidbody settings
            configured_count = 0
            for obj in valid_objects:
                if _configure_active_rigidbody(obj):
                    configured_count += 1

            logger.info(f"Successfully configured {configured_count}/{len(valid_objects)} active rigidbodies")

            # Earthquake effects are applied to the collision object (passive rigidbody)
            logger.debug("Active rigidbody objects configured (no keyframes added to preserve physics)")

            # Start animation
            try:
                bpy.ops.screen.animation_play()
                logger.info("Started physics animation")
            except Exception as e:
                logger.warning("Failed to start animation", e)

            return configured_count > 0

    except Exception as e:
        logger.error("Critical error in set_rigid_active", e)
        return False


def _configure_active_rigidbody(obj: Any) -> bool:
    """Configure settings for an active rigidbody object."""
    try:
        scene = safe_context_access("scene")
        if not scene or not hasattr(obj, 'rigid_body'):
            return False

        rigid_body = obj.rigid_body
        if not rigid_body:
            logger.warning(f"Object {safe_object_access(obj, 'name', 'Unknown')} has no rigid_body property")
            return False

        # Set collision shape
        shape = getattr(scene, 'a_shape', 'CONVEX_HULL')
        if shape in [item[0] for item in constants.COLLISION_SHAPES]:
            rigid_body.collision_shape = shape
        else:
            rigid_body.collision_shape = 'CONVEX_HULL'
            logger.warning(f"Invalid active collision shape {shape}, using CONVEX_HULL")

        # Set physical properties with validation
        friction = getattr(scene, 'a_friction', constants.FRICTION_DEFAULT)
        rigid_body.friction = max(constants.FRICTION_MIN, min(constants.FRICTION_MAX, friction))

        bounciness = getattr(scene, 'a_bounciness', constants.BOUNCINESS_DEFAULT)
        rigid_body.restitution = max(constants.BOUNCINESS_MIN, min(constants.BOUNCINESS_MAX, bounciness))

        margin = getattr(scene, 'a_margin', constants.PHYSICS_MARGIN_DEFAULT)
        rigid_body.collision_margin = max(constants.PHYSICS_MARGIN_MIN, min(constants.PHYSICS_MARGIN_MAX, margin))

        # Set damping
        trans_damping = getattr(scene, 'a_tra_damp', constants.DAMPING_DEFAULT)
        rigid_body.linear_damping = max(constants.DAMPING_MIN, min(constants.DAMPING_MAX, trans_damping))

        rot_damping = getattr(scene, 'a_rot_damp', 0.1)
        rigid_body.angular_damping = max(0.0, min(1.0, rot_damping))

        # Set other properties
        rigid_body.use_margin = True
        rigid_body.mesh_source = 'FINAL'

        logger.debug(f"Configured active rigidbody for {safe_object_access(obj, 'name', 'Unknown')}")
        return True

    except Exception as e:
        logger.error(f"Error configuring active rigidbody for object", e)
        return False


@log_errors
def duplicate_link() -> bool:
    """Create linked duplicates for optimization with improved safety."""
    try:
        with SafeOperation("duplicate_link"):
            active_objects = utils.state.get_rigidbody("active")
            if not active_objects:
                logger.warning("No active objects for optimization")
                return False

            high_poly_list = []
            low_poly_list = []

            for active_obj in active_objects:
                if not utils.is_object_valid(active_obj):
                    logger.warning(f"Skipping invalid active object")
                    continue

                # Store reference to high-poly object
                high_poly_list.append(active_obj)

                # Create duplicate
                try:
                    scene = safe_context_access("scene")
                    if not scene:
                        logger.error("Cannot access scene for duplication")
                        return False

                    new_obj = active_obj.copy()
                    if hasattr(active_obj, 'data') and active_obj.data:
                        new_obj.data = active_obj.data.copy()

                    scene.collection.objects.link(new_obj)
                    low_poly_list.append(new_obj)

                    # Name and prepare the duplicate
                    new_obj.name = f"{active_obj.name}{constants.PHYSICS_PROXY_SUFFIX}"
                    if hasattr(new_obj, 'parent_bone'):
                        new_obj.parent_bone = ""

                    # Select both objects
                    utils.safe_deselect_all()
                    utils.safe_select_object(active_obj)
                    utils.safe_select_object(new_obj)

                    view_layer = safe_context_access("view_layer")
                    if view_layer:
                        view_layer.objects.active = new_obj

                    # Make single user
                    try:
                        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True)
                    except Exception as e:
                        logger.warning(f"Failed to make single user for {new_obj.name}", e)

                    # Parent the high-poly to the low-poly
                    try:
                        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                    except Exception as e:
                        logger.warning(f"Failed to parent objects", e)

                    # Hide the high-poly object
                    active_obj.hide_viewport = True

                    # Select and optimize the low-poly object
                    utils.safe_deselect_all()
                    utils.safe_select_object(new_obj)

                    if not _apply_active_optimization_modifiers(new_obj):
                        logger.warning(f"Failed to optimize {new_obj.name}")

                    logger.debug(f"Created optimized proxy: {active_obj.name} -> {new_obj.name}")

                except Exception as e:
                    logger.error(f"Failed to create proxy for {safe_object_access(active_obj, 'name', 'Unknown')}", e)
                    continue

            # Store the lists
            utils.state.set_rigidbody("high_poly_list", high_poly_list)
            utils.state.set_rigidbody("low_poly_list", low_poly_list)

            if low_poly_list:
                # Select all low-poly objects and convert to mesh
                utils.safe_deselect_all()
                for obj in low_poly_list:
                    utils.safe_select_object(obj)

                try:
                    bpy.ops.object.convert(target='MESH')
                    logger.info(f"Created {len(low_poly_list)} optimization proxies")
                except Exception as e:
                    logger.warning("Failed to convert proxies to mesh", e)

            return len(low_poly_list) > 0

    except Exception as e:
        logger.error("Critical error in duplicate_link", e)
        return False


def _apply_active_optimization_modifiers(obj: Any) -> bool:
    """Apply optimization modifiers to active object."""
    try:
        scene = safe_context_access("scene")
        if not scene:
            return False

        # Add remesh modifier if voxel size is set
        voxel_size = getattr(scene, 'a_voxelsize', 0.0)
        if voxel_size > 0.0:
            try:
                remesh = obj.modifiers.new(name="Remesh", type='REMESH')
                remesh.voxel_size = min(voxel_size, constants.VOXEL_SIZE_MAX)
            except Exception as e:
                logger.warning("Failed to add remesh modifier to active object", e)
                return False

        # Add decimate modifier
        decimate_rate = getattr(scene, 'a_decimaterate', constants.DECIMATE_RATIO_DEFAULT)
        try:
            decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.ratio = max(constants.DECIMATE_RATIO_MIN,
                               min(constants.DECIMATE_RATIO_MAX, decimate_rate))
        except Exception as e:
            logger.warning("Failed to add decimate modifier to active object", e)
            return False

        return True

    except Exception as e:
        logger.error("Error applying active object optimization", e)
        return False


@log_errors
def apply_duplicate_link() -> bool:
    """Apply and clean up linked duplicates with improved safety."""
    try:
        with SafeOperation("apply_duplicate_link"):
            high_poly_objects = utils.state.get_rigidbody("high_poly_list")
            low_poly_objects = utils.state.get_rigidbody("low_poly_list")

            if not high_poly_objects and not low_poly_objects:
                logger.info("No optimization proxies to clean up")
                return True

            # Unhide and clear parents from high-poly objects
            restored_count = 0
            if high_poly_objects:
                for obj in high_poly_objects:
                    if utils.is_object_valid(obj):
                        try:
                            obj.hide_viewport = False
                            utils.safe_deselect_all()
                            utils.safe_select_object(obj)

                            view_layer = safe_context_access("view_layer")
                            if view_layer:
                                view_layer.objects.active = obj

                            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                            restored_count += 1

                        except Exception as e:
                            logger.warning(f"Failed to restore high-poly object {safe_object_access(obj, 'name', 'Unknown')}", e)

            logger.info(f"Restored {restored_count} high-poly objects")

            # Delete low-poly proxy objects
            deleted_count = 0
            if low_poly_objects:
                for obj in low_poly_objects:
                    if utils.is_object_valid(obj):
                        if utils.safe_object_delete(obj):
                            deleted_count += 1

            logger.info(f"Deleted {deleted_count} low-poly proxy objects")

            # Clear the lists
            utils.state.set_rigidbody("high_poly_list", [])
            utils.state.set_rigidbody("low_poly_list", [])

            return True

    except Exception as e:
        logger.error("Critical error in apply_duplicate_link", e)
        return False


@log_performance("drop_rigid_physics")
def drop_rigid() -> bool:
    """Initialize rigidbody physics simulation with comprehensive error handling."""
    try:
        with SafeOperation("drop_rigid_physics") as op:
            logger.info("Starting rigidbody physics simulation")

            # Reset state
            utils.state.set_rigidbody("active", [])
            utils.state.set_rigidbody("passive", None)
            utils.state.set_rigidbody("to_join", [])
            utils.state.set_rigidbody("high_poly", None)
            utils.state.set_rigidbody("low_poly", None)
            utils.state.set_rigidbody("high_poly_list", [])
            utils.state.set_rigidbody("low_poly_list", [])

            # Set dropped flag
            scene = safe_context_access("scene")
            if scene:
                scene.dropped = True

            # Collect active mesh objects
            selected_objects = safe_context_access("selected_objects", [])
            active_objects = []

            for obj in selected_objects:
                if utils.is_object_valid(obj) and safe_object_access(obj, "type") == "MESH":
                    active_objects.append(obj)

                    view_layer = safe_context_access("view_layer")
                    if view_layer:
                        view_layer.objects.active = obj

            if not active_objects:
                logger.error("No valid mesh objects selected for rigidbody physics")
                return False

            utils.state.set_rigidbody("active", active_objects)
            logger.info(f"Selected {len(active_objects)} objects for rigidbody physics")

            # Invert selection to find collision objects
            try:
                bpy.ops.object.select_all(action='INVERT')
            except Exception as e:
                logger.warning("Failed to invert selection", e)

            # Deselect non-mesh objects from the inverted selection
            current_selection = safe_context_access("selected_objects", [])
            for obj in current_selection:
                if utils.is_object_valid(obj) and safe_object_access(obj, "type") != "MESH":
                    try:
                        obj.select_set(False)
                    except Exception as e:
                        logger.warning(f"Failed to deselect non-mesh object", e)

            # Create passive collision object
            if not duplicate(constants.COLLIDER_OBJECT_NAME, 'WIRE'):
                logger.error("Failed to create collision object")
                return False

            passive_obj = safe_context_access("active_object")
            if not passive_obj:
                logger.error("No passive object created")
                return False

            utils.state.set_rigidbody("passive", passive_obj)

            if not set_rigid_passive():
                logger.error("Failed to configure passive rigidbody")
                return False

            # Handle optimization if enabled
            use_optimization = scene and getattr(scene, 'optimizehighpoly', False)
            if use_optimization:
                logger.info("Using high-poly optimization")
                if not duplicate_link():
                    logger.warning("Optimization setup failed, using original objects")
                    use_optimization = False

            if not set_rigid_active():
                logger.error("Failed to configure active rigidbodies")
                return False

            # Mark as successful
            op.success = True
            logger.info("Successfully initialized rigidbody physics simulation")
            return True

    except Exception as e:
        logger.error("Critical error in drop_rigid", e)
        return False


@log_performance("apply_rigid_physics")
def apply_rigid() -> bool:
    """Apply rigidbody physics results and clean up with comprehensive error handling."""
    try:
        with SafeOperation("apply_rigid_physics") as op:
            logger.info("Applying rigidbody physics simulation")

            # Clear dropped flag
            scene = safe_context_access("scene")
            if scene:
                scene.dropped = False

            # Handle optimization cleanup if enabled
            use_optimization = scene and getattr(scene, 'optimizehighpoly', False)
            if use_optimization:
                if not apply_duplicate_link():
                    logger.warning("Optimization cleanup failed")

            # Get active objects
            active_objects = utils.state.get_rigidbody("active")
            if not active_objects:
                logger.warning("No active objects to apply physics to")
                return True

            # Deselect all objects
            utils.safe_deselect_all()

            # Select and apply visual transformation to active objects
            valid_objects = []
            for obj in active_objects:
                if utils.is_object_valid(obj):
                    if utils.safe_select_object(obj):
                        valid_objects.append(obj)

            if valid_objects:
                try:
                    bpy.ops.object.visual_transform_apply()
                    logger.info(f"Applied visual transforms to {len(valid_objects)} objects")
                except Exception as e:
                    logger.warning("Failed to apply visual transforms", e)

                # Remove rigidbody if not using optimization
                if not use_optimization:
                    try:
                        # Ensure we're in object mode and have valid context
                        if utils.safe_mode_set('OBJECT'):
                            # Make sure objects are selected
                            view_layer = safe_context_access("view_layer")
                            if view_layer and view_layer.objects.active:
                                bpy.ops.rigidbody.objects_remove()
                                logger.debug("Removed rigidbody properties from active objects")
                            else:
                                logger.warning("No active object for rigidbody removal")
                        else:
                            logger.warning("Could not set object mode for rigidbody removal")
                    except Exception as e:
                        logger.warning("Failed to remove rigidbody properties", e)

            # Remove force object if any
            if not remove_simple_force():
                logger.warning("Failed to remove force field")

            # Delete passive object
            passive_obj = utils.state.get_rigidbody("passive")
            if passive_obj:
                if utils.safe_object_delete(passive_obj):
                    logger.info("Deleted passive collision object")
                else:
                    logger.warning("Failed to delete passive collision object")
                utils.state.set_rigidbody("passive", None)

            # Select active objects for user
            utils.safe_deselect_all()
            selected_count = 0
            for obj in valid_objects:
                if utils.is_object_valid(obj):
                    if utils.safe_select_object(obj):
                        selected_count += 1

            logger.info(f"Selected {selected_count} objects after applying physics")

            # Clear active objects list
            utils.state.set_rigidbody("active", [])

            # Reset frame and settings
            if scene:
                scene.frame_current = constants.DEFAULT_FRAME_START

            if not revert_world_settings():
                logger.warning("Failed to fully revert world settings")

            # Mark as successful
            op.success = True
            logger.info("Successfully applied rigidbody physics simulation")
            return True

    except Exception as e:
        logger.error("Critical error in apply_rigid", e)
        return False


@log_errors
def select_active() -> bool:
    """Select all active rigidbody objects."""
    try:
        active_objects = utils.state.get_rigidbody("active")
        if not active_objects:
            logger.info("No active objects to select")
            return False

        utils.safe_deselect_all()
        selected_count = 0

        for obj in active_objects:
            if utils.is_object_valid(obj):
                if utils.safe_select_object(obj):
                    selected_count += 1

        logger.info(f"Selected {selected_count}/{len(active_objects)} active objects")
        return selected_count > 0

    except Exception as e:
        logger.error("Error selecting active objects", e)
        return False


@log_errors
def remove_simple_force() -> bool:
    """Remove force field object if it exists."""
    try:
        force_obj = utils.state.get_physics_dropper("force_object")
        if not force_obj:
            logger.debug("No force object to remove")
            return True

        if not utils.is_object_valid(force_obj):
            logger.debug("Force object already invalid")
            utils.state.set_physics_dropper("force_object", None)
            return True

        if utils.safe_object_delete(force_obj):
            utils.state.set_physics_dropper("force_object", None)
            logger.info("Successfully removed force field")
            return True
        else:
            logger.warning("Failed to delete force field object")
            return False

    except Exception as e:
        logger.error("Error removing force field", e)
        return False