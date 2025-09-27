"""
Utility functions for the Physics Dropper addon.
"""

import bpy
import os
import threading
import time
from typing import List, Optional, Any, Dict
from bpy.utils import previews
from . import constants
from .logger import logger, SafeOperation, safe_object_access, safe_context_access


class PhysicsState:
    """Thread-safe state management for physics objects."""

    def __init__(self):
        self._lock = threading.Lock()
        self._physics_dropper = {
            "active": [],
            "passive": [],
            "dropped": False,
            "world_settings": [],
            "mesh_selected": True,
            "force_object": None,
        }
        self._rigidbody = {
            "world_settings": [],
            "active": [],
            "passive": None,
            "to_join": [],
            "high_poly": None,
            "low_poly": None,
            "high_poly_list": [],
            "low_poly_list": [],
        }
        self._cloth = {
            "active": [],
            "passive": None,
            "to_join": [],
        }
        self._earthquake = {
            "fmodifier": [],
        }

    def get_physics_dropper(self, key: str = None) -> Any:
        """Thread-safe access to physics_dropper state."""
        with self._lock:
            if key is None:
                return self._physics_dropper.copy()
            return self._physics_dropper.get(key)

    def set_physics_dropper(self, key: str, value: Any) -> None:
        """Thread-safe update to physics_dropper state."""
        with self._lock:
            self._physics_dropper[key] = value

    def get_rigidbody(self, key: str = None) -> Any:
        """Thread-safe access to rigidbody state."""
        with self._lock:
            if key is None:
                return self._rigidbody.copy()
            return self._rigidbody.get(key)

    def set_rigidbody(self, key: str, value: Any) -> None:
        """Thread-safe update to rigidbody state."""
        with self._lock:
            self._rigidbody[key] = value

    def get_cloth(self, key: str = None) -> Any:
        """Thread-safe access to cloth state."""
        with self._lock:
            if key is None:
                return self._cloth.copy()
            return self._cloth.get(key)

    def set_cloth(self, key: str, value: Any) -> None:
        """Thread-safe update to cloth state."""
        with self._lock:
            self._cloth[key] = value

    def get_earthquake(self, key: str = None) -> Any:
        """Thread-safe access to earthquake state."""
        with self._lock:
            if key is None:
                return self._earthquake.copy()
            return self._earthquake.get(key)

    def set_earthquake(self, key: str, value: Any) -> None:
        """Thread-safe update to earthquake state."""
        with self._lock:
            self._earthquake[key] = value

    def reset_all(self) -> None:
        """Reset all state to defaults."""
        with self._lock:
            self._physics_dropper = {
                "active": [],
                "passive": [],
                "dropped": False,
                "world_settings": [],
                "mesh_selected": True,
                "force_object": None,
            }
            self._rigidbody = {
                "world_settings": [],
                "active": [],
                "passive": None,
                "to_join": [],
                "high_poly": None,
                "low_poly": None,
                "high_poly_list": [],
                "low_poly_list": [],
            }
            self._cloth = {
                "active": [],
                "passive": None,
                "to_join": [],
            }
            self._earthquake = {
                "fmodifier": [],
            }


# Global state instance
state = PhysicsState()

# Legacy compatibility - these will be deprecated
physics_dropper = {}
rigidbody = {}
cloth = {}
earthquake = {}

# Icon handling
def register_icons() -> bool:
    """Register custom icons for the addon."""
    try:
        with SafeOperation("register_icons"):
            bpy.types.Scene.physics_dropper_icons = previews.new()
            icons_dir = os.path.join(os.path.dirname(__file__), constants.ICONS_DIR_NAME)

            if not os.path.exists(icons_dir):
                logger.warning(f"Icons directory not found: {icons_dir}")
                return False

            missing_icons = []
            for icon_name in constants.ICON_NAMES:
                icon_path = os.path.join(icons_dir, f"{icon_name}.png")
                if os.path.exists(icon_path):
                    bpy.types.Scene.physics_dropper_icons.load(
                        icon_name, icon_path, 'IMAGE'
                    )
                else:
                    missing_icons.append(icon_name)

            if missing_icons:
                logger.warning(f"Missing icon files: {missing_icons}")

            # logger.info(f"Registered {len(constants.ICON_NAMES) - len(missing_icons)} icons")
            return True
    except Exception as e:
        logger.error("Failed to register icons", e)
        return False

def unregister_icons() -> bool:
    """Unregister custom icons."""
    try:
        with SafeOperation("unregister_icons"):
            if hasattr(bpy.types.Scene, 'physics_dropper_icons'):
                previews.remove(bpy.types.Scene.physics_dropper_icons)
                delattr(bpy.types.Scene, 'physics_dropper_icons')
                # logger.info("Unregistered icons successfully")
            else:
                logger.warning("No icons to unregister")
            return True
    except Exception as e:
        logger.error("Failed to unregister icons", e)
        return False

def check_mesh_selected() -> bool:
    """Check if a mesh object is selected."""
    try:
        with SafeOperation("check_mesh_selected"):
            selected_objects = safe_context_access("selected_objects", [])

            mesh_selected = any(
                safe_object_access(obj, "type") == "MESH"
                for obj in selected_objects
            )

            state.set_physics_dropper("mesh_selected", mesh_selected)

            if not mesh_selected:
                logger.warning("No mesh objects selected")
            else:
                mesh_count = sum(1 for obj in selected_objects if safe_object_access(obj, "type") == "MESH")
                # logger.info(f"Found {mesh_count} mesh objects selected")

            return mesh_selected
    except Exception as e:
        logger.error("Error checking mesh selection", e)
        state.set_physics_dropper("mesh_selected", False)
        return False

def post_bake() -> bool:
    """Operations to perform after baking physics."""
    try:
        with SafeOperation("post_bake"):
            from . import rigidbody as rb_module

            # Remove force field
            if not rb_module.remove_simple_force():
                logger.warning("Failed to remove force field during post-bake cleanup")

            # Clean up passive object
            passive_obj = state.get_rigidbody("passive")
            if passive_obj and is_object_valid(passive_obj):
                if safe_object_delete(passive_obj):
                    state.set_rigidbody("passive", None)
                    # logger.info("Deleted passive rigidbody object")
                else:
                    logger.warning("Failed to delete passive rigidbody object")

            # Select active objects
            safe_deselect_all()
            active_objects = state.get_rigidbody("active")
            valid_count = 0

            for obj in active_objects:
                if is_object_valid(obj):
                    if safe_select_object(obj):
                        valid_count += 1

            state.set_rigidbody("active", [])
            # logger.info(f"Selected {valid_count} active objects for cleanup")

            # Reset frame and settings
            scene = safe_context_access("scene")
            if scene:
                scene.frame_current = constants.DEFAULT_FRAME_START

            if not rb_module.revert_world_settings():
                logger.warning("Failed to revert world settings")

            # logger.info("Post-bake cleanup completed successfully")
            return None  # Return None to run timer only once

    except Exception as e:
        logger.error("Error during post-bake cleanup", e)
        return None  # Return None to prevent timer loop

# Addon keymaps
addon_keymaps = {}


# Utility functions for safe Blender operations
def is_object_valid(obj: Any) -> bool:
    """Check if a Blender object is valid and still exists."""
    try:
        if obj is None:
            return False
        # Try to access name property - will raise ReferenceError if object is deleted
        _ = obj.name
        return True
    except ReferenceError:
        # logger.debug("Object reference is no longer valid")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking object validity: {e}")
        return False


def safe_object_delete(obj: Any) -> bool:
    """Safely delete a Blender object."""
    try:
        if not is_object_valid(obj):
            # logger.debug("Object already invalid, nothing to delete")
            return True

        # Check if object is in the current scene
        scene = safe_context_access("scene")
        if not scene or obj.name not in scene.objects:
            logger.warning(f"Object {obj.name} not found in current scene")
            return False

        # Store object name before deletion
        obj_name = safe_object_access(obj, "name", "Unknown")

        safe_deselect_all()
        if safe_select_object(obj):
            bpy.ops.object.delete()
            # logger.debug(f"Successfully deleted object: {obj_name}")
            return True
        else:
            logger.warning(f"Failed to select object for deletion: {obj_name}")
            return False

    except Exception as e:
        logger.error(f"Error deleting object", e)
        return False


def safe_select_object(obj: Any) -> bool:
    """Safely select a Blender object."""
    try:
        if not is_object_valid(obj):
            return False

        obj.select_set(True)
        view_layer = safe_context_access("view_layer")
        if view_layer:
            view_layer.objects.active = obj
        return True

    except Exception as e:
        logger.warning(f"Failed to select object", e)
        return False


def safe_deselect_all() -> bool:
    """Safely deselect all objects."""
    try:
        bpy.ops.object.select_all(action='DESELECT')
        return True
    except Exception as e:
        logger.warning(f"Failed to deselect all objects", e)
        return False


def safe_mode_set(mode: str) -> bool:
    """Safely set object mode."""
    try:
        current_mode = safe_context_access("mode")
        if current_mode == mode.upper():
            return True

        active_object = safe_context_access("active_object")
        if not active_object:
            logger.warning(f"No active object to set mode {mode}")
            return False

        bpy.ops.object.mode_set(mode=mode)
        return True

    except Exception as e:
        logger.warning(f"Failed to set mode to {mode}", e)
        return False


def validate_scene_state() -> bool:
    """Validate that the scene is in a good state for physics operations."""
    try:
        scene = safe_context_access("scene")
        if not scene:
            logger.error("No active scene found")
            return False

        # Check if we have objects
        objects = safe_context_access("scene.objects")
        if not objects:
            logger.warning("Scene has no objects")
            return False

        # Check object count for performance warnings
        object_count = len(objects)
        if object_count > constants.LARGE_SCENE_THRESHOLD:
            logger.warning(f"Large scene detected: {object_count} objects. Performance may be affected.")

        return True

    except Exception as e:
        logger.error("Error validating scene state", e)
        return False


def cleanup_invalid_references() -> None:
    """Clean up invalid object references from state."""
    try:
        with SafeOperation("cleanup_invalid_references"):
            # Clean physics_dropper state
            force_obj = state.get_physics_dropper("force_object")
            if force_obj and not is_object_valid(force_obj):
                state.set_physics_dropper("force_object", None)
                # logger.debug("Cleaned invalid force object reference")

            # Clean rigidbody state
            passive = state.get_rigidbody("passive")
            if passive and not is_object_valid(passive):
                state.set_rigidbody("passive", None)
                # logger.debug("Cleaned invalid passive object reference")

            # Clean active object lists
            active_objects = state.get_rigidbody("active")
            if active_objects:
                valid_active = [obj for obj in active_objects if is_object_valid(obj)]
                if len(valid_active) != len(active_objects):
                    state.set_rigidbody("active", valid_active)
                    # logger.debug(f"Cleaned {len(active_objects) - len(valid_active)} invalid active object references")

            # Clean cloth state
            cloth_passive = state.get_cloth("passive")
            if cloth_passive and not is_object_valid(cloth_passive):
                state.set_cloth("passive", None)
                # logger.debug("Cleaned invalid cloth passive object reference")

            cloth_active = state.get_cloth("active")
            if cloth_active:
                valid_cloth_active = [obj for obj in cloth_active if is_object_valid(obj)]
                if len(valid_cloth_active) != len(cloth_active):
                    state.set_cloth("active", valid_cloth_active)
                    # logger.debug(f"Cleaned {len(cloth_active) - len(valid_cloth_active)} invalid cloth active object references")

    except Exception as e:
        logger.error("Error during cleanup of invalid references", e)


def get_performance_info() -> Dict[str, Any]:
    """Get current performance-related information."""
    try:
        scene = safe_context_access("scene")
        if not scene:
            return {}

        object_count = len(scene.objects)
        selected_count = len(safe_context_access("selected_objects", []))

        return {
            "total_objects": object_count,
            "selected_objects": selected_count,
            "large_scene": object_count > constants.LARGE_SCENE_THRESHOLD,
            "performance_warning": object_count > constants.LARGE_SCENE_THRESHOLD,
        }

    except Exception as e:
        logger.error("Error getting performance info", e)
        return {}