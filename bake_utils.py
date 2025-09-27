"""
Physics baking utility using direct cache access for Blender 4.2+
"""

import bpy
import time
from typing import Optional
from . import constants
from .logger import logger, SafeOperation, log_errors, log_performance

def rb_bake_from_current_cache(scene=None):
    """
    Bake rigid body simulation from current cache state using clean approach.

    Args:
        scene: Optional scene to use, defaults to current scene

    Raises:
        RuntimeError: If no rigid body world exists or no suitable UI context found
    """
    scene = scene or bpy.context.scene
    if not scene.rigidbody_world:
        raise RuntimeError("No Rigid Body World on the scene")

    pc = scene.rigidbody_world.point_cache

    # Use PROPERTIES or TIMELINE only to avoid view3d selection side effects
    def find_ui_override():
        wm = bpy.context.window_manager
        for win in wm.windows:
            scr = win.screen
            for area in scr.areas:
                if area.type in {'PROPERTIES', 'TIMELINE'}:
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return {
                                'window': win,
                                'screen': scr,
                                'area': area,
                                'region': region,
                                'scene': scene,
                                'point_cache': pc,
                            }
        return None

    ctx = find_ui_override()
    if not ctx:
        raise RuntimeError("No suitable UI context available")

    # Preserve state
    prev_frame = scene.frame_current
    vl = bpy.context.view_layer
    prev_active = vl.objects.active

    try:
        with bpy.context.temp_override(**ctx):
            # This commits current temp cache to baked cache without resim
            bpy.ops.ptcache.bake_from_cache()

    finally:
        # Restore state - prevents snap to origin and unwanted active changes
        scene.frame_set(prev_frame)
        try:
            vl.objects.active = prev_active
        except Exception:
            pass



@log_errors
def clear_rigidbody_bake() -> bool:
    """Clear the rigidbody cache with improved error handling."""
    try:
        with SafeOperation("clear_rigidbody_bake"):
            from . import utils

            # Check if there's anything to clear
            rb_world = utils.safe_context_access("scene.rigidbody_world")
            if not rb_world:
                logger.info("No rigidbody world found, nothing to clear")
                return True

            point_cache = getattr(rb_world, 'point_cache', None)
            if not point_cache:
                logger.warning("No point cache found in rigidbody world")
                return True

            if not point_cache.is_baked:
                logger.info("No baked cache found, nothing to clear")
                return True

            # Clear the cache
            try:
                bpy.ops.ptcache.free_bake_all()
                logger.info("Successfully cleared all physics caches")

                # Verify clearing was successful
                if not point_cache.is_baked:
                    logger.debug("Cache clearing verified")
                else:
                    logger.warning("Cache still marked as baked after clearing")

                return True

            except RuntimeError as e:
                logger.error("Blender runtime error while clearing cache", e)
                return False

    except Exception as e:
        logger.error("Error clearing rigidbody bake", e)
        return False

@log_errors
def delete_collider() -> bool:
    """Delete the COLLIDER object after baking with improved safety."""
    try:
        with SafeOperation("delete_collider"):
            from . import utils

            # Find the COLLIDER object safely
            scene = utils.safe_context_access("scene")
            if not scene:
                logger.error("Cannot access scene to find COLLIDER object")
                return False

            collider = scene.objects.get(constants.COLLIDER_OBJECT_NAME)
            if not collider:
                # Also check for objects with COLLIDER in the name (case variations)
                colliders = [obj for obj in scene.objects
                           if constants.COLLIDER_OBJECT_NAME.lower() in obj.name.lower()]
                if colliders:
                    collider = colliders[0]
                    logger.info(f"Found collider with different name: {collider.name}")
                else:
                    logger.info("No COLLIDER object found to delete")
                    return True  # Not an error if it doesn't exist

            # Verify object is still valid
            if not utils.is_object_valid(collider):
                logger.info("COLLIDER object already invalid/deleted")
                return True

            # Delete the collider safely
            if utils.safe_object_delete(collider):
                logger.info(f"Successfully deleted COLLIDER object: {collider.name}")
                return True
            else:
                logger.warning("Failed to delete COLLIDER object")
                return False

    except Exception as e:
        logger.error("Error deleting COLLIDER object", e)
        return False


@log_errors
def validate_baking_prerequisites() -> bool:
    """Validate that all prerequisites for baking are met."""
    try:
        from . import utils

        # Check scene state
        if not utils.validate_scene_state():
            logger.error("Scene state validation failed")
            return False

        # Check if there are objects to bake
        scene = utils.safe_context_access("scene")
        if not scene:
            return False

        selected_objects = utils.safe_context_access("selected_objects", [])
        if not selected_objects:
            logger.warning("No objects selected for baking")

        # Check if simulation is active
        if not getattr(scene, 'dropped', False):
            logger.error("No active physics simulation to bake")
            return False

        # Performance check
        perf_info = utils.get_performance_info()
        if perf_info.get('performance_warning', False):
            logger.warning(f"Large scene with {perf_info['total_objects']} objects may affect baking performance")

        return True

    except Exception as e:
        logger.error("Error validating baking prerequisites", e)
        return False


