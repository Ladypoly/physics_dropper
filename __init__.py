"""
Physics Dropper Addon for Blender
Allows for easy setup of rigid body and cloth physics simulations.
"""

bl_info = {
    "name": "Physics Dropper",
    "description": "Easy rigidbody and cloth physics simulation setup with enhanced stability",
    "author": "Elin",
    "version": (1, 3, 0),
    "blender": (4, 5, 0),
    "location": "Tool",
    "category": "3D View",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
}

import bpy
from bpy.app.handlers import persistent
import os
from typing import List, Optional

# Import local modules
from . import constants
from . import logger
from . import properties
from . import operators
from . import panels
from . import utils
from . import bake_utils

# Modules to register
modules = (
    properties,
    operators,
    panels,
)

@persistent
def undo_pre_handler(dummy):
    """Handle undo events - clean up invalid references."""
    try:
        # Clean up any invalid object references after undo
        utils.cleanup_invalid_references()
        # logger.logger.debug("Cleaned up invalid references after undo")
    except Exception as e:
        logger.logger.error("Error in undo handler", e)

def register():
    """Register the addon with improved error handling."""
    try:
        # logger.logger.info(f"Registering {constants.ADDON_NAME} v{constants.ADDON_VERSION}")

        # Initialize logging level from preferences if available
        try:
            # Set log level based on Blender's debug mode
            if bpy.app.debug:
                logger.logger.set_level(constants.LOG_LEVELS['DEBUG'])
            else:
                logger.logger.set_level(constants.LOG_LEVELS['INFO'])
        except Exception:
            pass  # Use default level

        # Register properties first
        if not properties.register():
            logger.logger.error("Failed to register properties")
            return

        # Register icons
        if not utils.register_icons():
            logger.logger.warning("Icon registration failed, continuing without icons")

        # Register classes from modules
        for module in modules:
            try:
                module.register()
                # logger.logger.debug(f"Registered module: {module.__name__}")
            except Exception as e:
                logger.logger.error(f"Failed to register module {module.__name__}", e)
                # Continue with other modules

        # Register handlers safely
        if undo_pre_handler not in bpy.app.handlers.undo_pre:
            bpy.app.handlers.undo_pre.append(undo_pre_handler)
            # logger.logger.debug("Registered undo handler")


        # Validate scene state
        if not utils.validate_scene_state():
            logger.logger.warning("Scene state validation failed")

        # logger.logger.info(f"Successfully registered {constants.ADDON_NAME}")

    except Exception as e:
        logger.logger.critical(f"Critical error during addon registration", e)
        # Try to clean up partial registration
        try:
            unregister()
        except Exception:
            pass
        raise

def unregister():
    """Unregister the addon with safe cleanup."""
    try:
        # logger.logger.info(f"Unregistering {constants.ADDON_NAME}")


        # Unregister handlers safely
        if undo_pre_handler in bpy.app.handlers.undo_pre:
            try:
                bpy.app.handlers.undo_pre.remove(undo_pre_handler)
                # logger.logger.debug("Unregistered undo handler")
            except ValueError:
                logger.logger.warning("Undo handler was not in the handlers list")

        # Clean up any remaining physics state
        try:
            utils.state.reset_all()
            utils.cleanup_invalid_references()
            # logger.logger.debug("Cleaned up physics state")
        except Exception as e:
            logger.logger.warning("Error cleaning up physics state", e)

        # Unregister classes from modules (reverse order)
        for module in reversed(modules):
            try:
                module.unregister()
                # logger.logger.debug(f"Unregistered module: {module.__name__}")
            except Exception as e:
                logger.logger.warning(f"Error unregistering module {module.__name__}", e)
                # Continue with other modules

        # Unregister icons
        if not utils.unregister_icons():
            logger.logger.warning("Icon unregistration had issues")

        # Unregister properties
        if not properties.unregister():
            logger.logger.warning("Property unregistration had issues")

        # logger.logger.info(f"Successfully unregistered {constants.ADDON_NAME}")

    except Exception as e:
        logger.logger.critical(f"Critical error during addon unregistration", e)
        # Don't re-raise during unregistration to avoid Blender crashes

if __name__ == "__main__":
    register()