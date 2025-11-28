"""
Earthquake simulation functions for the Physics Dropper addon.

This module provides safe earthquake effect functionality with proper error handling,
validation, and logging for all modifier operations.
"""

import bpy
import random
from typing import Optional, List, Any
from . import constants
from . import logger
from . import utils
from .logger import log_errors, log_performance, SafeOperation, safe_context_access, safe_object_access

# Get logger instance
log = logger.logger

@log_errors
def reset_fmodifier_list() -> bool:
    """Reset the list of F-curve modifiers safely.

    Returns:
        bool: True if reset was successful, False otherwise
    """
    with SafeOperation("reset_fmodifier_list") as op:
        try:
            utils.state.set_earthquake("fmodifier", [])
            log.debug("F-curve modifier list reset successfully")
            op.success = True
            return True
        except Exception as e:
            log.error(f"Failed to reset F-curve modifier list: {e}")
            return False

def get_fcurves_from_object(obj: Any) -> Any:
    """
    Get F-curves from an object, compatible with Blender 4.5 and 5.0+.

    Handles both legacy action.fcurves API (Blender 4.x) and new
    channelbag-based API (Blender 5.0+).

    Args:
        obj: The Blender object to get F-curves from

    Returns:
        F-curves collection or None if not found
    """
    # Get animation data
    animation_data = safe_object_access(obj, "animation_data")
    if not animation_data:
        log.debug("No animation_data found on object")
        return None

    action = safe_object_access(animation_data, "action")
    if not action:
        log.debug("No action found in animation_data")
        return None

    # Method 1: Try legacy Blender 4.x method first (simpler, faster if available)
    if hasattr(action, 'fcurves'):
        fcurves = safe_object_access(action, "fcurves")
        if fcurves:
            log.debug(f"Found F-curves via legacy action.fcurves (Blender 4.x)")
            return fcurves

    # Method 2: Try Blender 5.0+ channelbag method
    log.debug("Legacy method unavailable, trying channelbag method (Blender 5.0+)")

    # Check if action has the new slot-based system
    if not hasattr(action, 'slots') or len(action.slots) == 0:
        log.debug("Action has no slots (channelbag system unavailable)")
        return None

    # Try using bpy_extras helper (official method)
    try:
        from bpy_extras import anim_utils

        action_slot = safe_object_access(animation_data, "action_slot")
        if action_slot:
            channelbag = anim_utils.action_get_channelbag_for_slot(action, action_slot)
            if channelbag:
                fcurves = safe_object_access(channelbag, "fcurves")
                if fcurves:
                    log.debug(f"Found F-curves via channelbag (Blender 5.0+ official method)")
                    return fcurves
    except (ImportError, AttributeError, Exception) as e:
        log.debug(f"bpy_extras.anim_utils method failed: {e}")

    # Method 3: Manual channelbag iteration (fallback)
    try:
        if hasattr(action, 'layers') and len(action.layers) > 0:
            layer = action.layers[0]
            if hasattr(layer, 'strips') and len(layer.strips) > 0:
                strip = layer.strips[0]
                if hasattr(strip, 'channelbags'):
                    for channelbag in strip.channelbags:
                        fcurves = safe_object_access(channelbag, "fcurves")
                        if fcurves and len(fcurves) > 0:
                            log.debug(f"Found F-curves via manual channelbag iteration")
                            return fcurves
    except Exception as e:
        log.debug(f"Manual channelbag iteration failed: {e}")

    log.error("Could not find F-curves using any method (legacy or channelbag)")
    return None

@log_errors
def earthquake_function(obj: Any, keyindex: int, curveindex: int) -> bool:
    """Set up earthquake animation for an object with safe modifier management.

    Args:
        obj: The object to add earthquake effects to
        keyindex: Index for keyframe insertion
        curveindex: Index for F-curve lookup

    Returns:
        bool: True if earthquake setup was successful, False otherwise
    """
    with SafeOperation("setup_earthquake_animation") as op:
        try:
            # Validate inputs
            if not utils.is_object_valid(obj):
                log.error("Invalid object provided for earthquake setup")
                return False

            if keyindex < 0 or keyindex > 2 or curveindex < 0 or curveindex > 2:
                log.error(f"Invalid key/curve indices: {keyindex}, {curveindex}")
                return False

            log.debug(f"Setting up earthquake for object: {obj.name}, key={keyindex}, curve={curveindex}")

            # Insert keyframes to ensure F-curves exist
            try:
                # Insert multiple keyframes to ensure F-curve creation
                obj.keyframe_insert(data_path="location", index=keyindex, frame=1.0)
                obj.keyframe_insert(data_path="location", index=keyindex, frame=250.0)
                log.debug(f"Inserted keyframes for axis {keyindex} at frames 1 and 250")
            except Exception as e:
                log.error(f"Failed to insert keyframes: {e}")
                return False

            # Force scene update to ensure animation data is created
            try:
                import bpy
                bpy.context.view_layer.update()
            except Exception as e:
                log.warning(f"Failed to update view layer: {e}")

            # Get animation data safely with retry
            animation_data = None
            for attempt in range(3):
                animation_data = safe_object_access(obj, "animation_data")
                if animation_data:
                    break
                log.debug(f"Attempt {attempt + 1}: Waiting for animation data creation")
                import time
                time.sleep(0.01)

            if not animation_data:
                log.error(f"No animation data found for object {obj.name} after keyframe insertion")
                return False

            # Get F-curves using compatibility helper
            fcurves = get_fcurves_from_object(obj)

            if not fcurves:
                log.error(f"No F-curves found for object {obj.name}")
                return False

            log.debug(f"Found {len(fcurves)} F-curves for object {obj.name}")

            # Find the F-curve for the inserted keyframe
            fcurve = None
            try:
                fcurve = fcurves.find(data_path="location", index=curveindex)
                if not fcurve:
                    log.error(f"Could not find F-curve for location[{curveindex}] in {len(fcurves)} curves")
                    # Debug: List available F-curves
                    for i, curve in enumerate(fcurves):
                        log.debug(f"  F-curve {i}: {curve.data_path}[{curve.array_index}]")
                    return False
                else:
                    log.debug(f"Found F-curve for location[{curveindex}]: {fcurve.data_path}[{fcurve.array_index}]")
            except Exception as e:
                log.error(f"Failed to find F-curve: {e}")
                return False

            # Add noise modifier to the F-curve
            try:
                modifiers = safe_object_access(fcurve, "modifiers")
                if modifiers is None:
                    log.error(f"F-curve for location[{curveindex}] has no modifiers collection")
                    return False

                log.debug(f"F-curve modifiers collection found, creating noise modifier")

                modifier = modifiers.new(type='NOISE')
                if not modifier:
                    log.error("Failed to create noise modifier")
                    return False

                log.debug(f"Created noise modifier for F-curve {curveindex}")

                # Set initial modifier properties
                try:
                    modifier.strength = 0.0
                    modifier.scale = 0.2
                    modifier.phase = 0.0
                    modifier.offset = 0.0
                    log.debug(f"Configured noise modifier: strength=0.0, scale=0.2, phase=0.0")
                except Exception as e:
                    log.warning(f"Failed to set noise modifier properties: {e}")

                # Get current modifier list from state and add this modifier
                fmodifier_list = utils.state.get_earthquake("fmodifier") or []
                fmodifier_list.append(modifier)
                utils.state.set_earthquake("fmodifier", fmodifier_list)

                # Store which axis this modifier controls for debugging
                axis_names = ["X", "Y", "Z"]
                axis_name = axis_names[curveindex] if curveindex < 3 else f"Unknown({curveindex})"
                log.info(f"Successfully added noise modifier to {obj.name} {axis_name}-axis (location[{curveindex}]) at list index {len(fmodifier_list)-1}")

            except Exception as e:
                log.error(f"Failed to create or configure noise modifier: {e}")
                return False

            log.info(f"Successfully set up earthquake for {obj.name} axis {keyindex}")
            op.success = True
            return True

        except Exception as e:
            log.error(f"Unexpected error in earthquake setup: {e}")
            return False

@log_errors
@log_performance("update_earthquake_effects")
def update_earthquake() -> bool:
    """Update earthquake settings based on UI controls with safe modifier access.

    Returns:
        bool: True if update was successful, False otherwise
    """
    with SafeOperation("update_earthquake_effects") as op:
        try:
            # Get scene properties safely
            scene = safe_context_access("scene")
            if not scene:
                log.error("Cannot access scene for earthquake update")
                return False

            # Get F-curve modifiers from state
            fmodifier_list = utils.state.get_earthquake("fmodifier")
            if not fmodifier_list:
                log.debug("No F-curve modifiers available for earthquake update")
                return True  # Not an error, just nothing to update

            # Get earthquake settings safely
            earthquake_strength = safe_object_access(scene, "earthquake", 0.0)
            earthquakex = safe_object_access(scene, "earthquakex", False)
            earthquakey = safe_object_access(scene, "earthquakey", False)
            earthquakez = safe_object_access(scene, "earthquakez", False)

            log.debug(f"Earthquake settings: strength={earthquake_strength}, x={earthquakex}, y={earthquakey}, z={earthquakez}")

            # Validate earthquake strength
            if earthquake_strength < 0:
                log.warning(f"Invalid earthquake strength {earthquake_strength}, using 0")
                earthquake_strength = 0.0
            elif earthquake_strength > 100:
                log.warning(f"Earthquake strength {earthquake_strength} too high, clamping to 100")
                earthquake_strength = 100.0

            # Calculate normalized strength (doubled for more effect)
            normalized_strength = earthquake_strength / 200.0

            # Update each axis if modifiers exist
            axis_settings = [
                (earthquakex, "X"),
                (earthquakey, "Y"),
                (earthquakez, "Z")
            ]

            successful_updates = 0
            for i, (enabled, axis_name) in enumerate(axis_settings):
                if i < len(fmodifier_list):
                    modifier = fmodifier_list[i]
                    if modifier:  # Check if modifier still exists
                        try:
                            if enabled:
                                modifier.strength = normalized_strength
                                modifier.phase = random.uniform(1.0, 10.0)
                                log.info(f"ENABLED earthquake on {axis_name}-axis (modifier {i}): strength={normalized_strength}")
                            else:
                                modifier.strength = 0.0
                                log.info(f"DISABLED earthquake on {axis_name}-axis (modifier {i})")
                            successful_updates += 1
                        except ReferenceError:
                            log.warning(f"F-curve modifier for {axis_name}-axis was deleted")
                        except Exception as e:
                            log.warning(f"Failed to update {axis_name}-axis earthquake: {e}")
                    else:
                        log.warning(f"No modifier available for {axis_name}-axis")
                else:
                    log.warning(f"No modifier index {i} available for {axis_name}-axis")

            if successful_updates > 0:
                log.info(f"Successfully updated {successful_updates} earthquake modifiers")
                op.success = True
                return True
            else:
                log.warning("No earthquake modifiers were updated")
                return False

        except Exception as e:
            log.error(f"Unexpected error updating earthquake effects: {e}")
            return False

def cleanup_earthquake_modifiers() -> None:
    """Clean up invalid earthquake modifier references."""
    try:
        fmodifier_list = utils.state.get_earthquake("fmodifier")
        if not fmodifier_list:
            return

        valid_modifiers = []
        for modifier in fmodifier_list:
            try:
                # Try to access the modifier to check if it's still valid
                _ = modifier.strength
                valid_modifiers.append(modifier)
            except ReferenceError:
                log.debug("Removed invalid earthquake modifier reference")
            except Exception:
                log.debug("Removed inaccessible earthquake modifier")

        # Update state with cleaned list
        utils.state.set_earthquake("fmodifier", valid_modifiers)
        if len(valid_modifiers) != len(fmodifier_list):
            log.info(f"Cleaned up {len(fmodifier_list) - len(valid_modifiers)} invalid modifier references")

    except Exception as e:
        log.warning(f"Failed to cleanup earthquake modifiers: {e}")
