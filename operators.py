"""
Operator classes for the Physics Dropper addon.
"""

import bpy
import os
import time
from typing import Set, Optional
from . import constants
from . import utils
from .logger import logger, SafeOperation, log_errors, log_performance, safe_context_access, safe_object_access
from . import rigidbody as rb
from . import cloth as cloth_module
from . import earthquake as eq

###############################################################################
# Mode Selection Operators
###############################################################################

class PD_OT_SetRigid(bpy.types.Operator):
    """Set mode to Rigidbody Physics"""
    bl_idname = "pd.set_rigid"
    bl_label = "Rigidbody"
    bl_description = "Use Rigidbody Physics"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        with SafeOperation("set_rigid_mode"):
            scene = safe_context_access("scene")
            if scene:
                scene.is_rigid = True
                logger.info("Switched to rigidbody physics mode")
                return {"FINISHED"}
            else:
                self.report({'ERROR'}, constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                return {"CANCELLED"}


class PD_OT_SetCloth(bpy.types.Operator):
    """Set mode to Cloth Physics"""
    bl_idname = "pd.set_cloth"
    bl_label = "Cloth"
    bl_description = "Use Cloth Physics"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        with SafeOperation("set_cloth_mode"):
            scene = safe_context_access("scene")
            if scene:
                scene.is_rigid = False
                logger.info("Switched to cloth physics mode")
                return {"FINISHED"}
            else:
                self.report({'ERROR'}, constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                return {"CANCELLED"}


###############################################################################
# Main Physics Operators
###############################################################################

class PD_OT_Drop(bpy.types.Operator):
    """Drop objects with physics"""
    bl_idname = "pd.drop"
    bl_label = "Drop"
    bl_description = "Drop all selected objects with physics"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        selected_objects = safe_context_access("selected_objects", [])
        return len(selected_objects) > 0

    def execute(self, context):
        try:
            with SafeOperation("drop_physics") as op:
                scene = safe_context_access("scene")
                if not scene:
                    self.report({'ERROR'}, constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                    return {"CANCELLED"}

                # Check if already dropped
                if scene.dropped:
                    logger.warning("Physics simulation already active")
                    return {"FINISHED"}

                # Validate scene state
                if not utils.validate_scene_state():
                    self.report({'ERROR'}, "Scene is not in a valid state for physics")
                    return {"CANCELLED"}

                # Check if mesh objects are selected
                if not utils.check_mesh_selected():
                    self.report({'ERROR'}, constants.ERROR_MESSAGES['NO_MESH_SELECTED'])
                    return {"CANCELLED"}

                # Clean up any invalid references
                utils.cleanup_invalid_references()

                # Reset earthquake settings
                eq.reset_fmodifier_list()

                # Clear any existing bake safely
                try:
                    if not utils.safe_mode_set('OBJECT'):
                        logger.warning("Failed to set object mode")

                    rigidbody_world = safe_context_access("scene.rigidbody_world")
                    if rigidbody_world:
                        bpy.ops.ptcache.free_bake_all()
                        logger.debug("Cleared existing physics cache")
                except Exception as e:
                    logger.warning("Error clearing physics cache", e)
                    # Continue anyway

                # Start appropriate physics simulation
                is_rigid = safe_context_access("scene.is_rigid", True)
                if is_rigid:
                    if rb.drop_rigid():
                        logger.info("Started rigidbody physics simulation")
                    else:
                        self.report({'ERROR'}, "Failed to start rigidbody simulation")
                        return {"CANCELLED"}
                else:
                    if cloth_module.drop_cloth():
                        logger.info("Started cloth physics simulation")
                    else:
                        self.report({'ERROR'}, "Failed to start cloth simulation")
                        return {"CANCELLED"}

                # Update earthquake if enabled
                eq.update_earthquake()

                # Mark operation as successful
                op.success = True
                self.report({'INFO'}, "Physics simulation started successfully")
                return {"FINISHED"}

        except Exception as e:
            logger.error("Unexpected error in drop operation", e)
            self.report({'ERROR'}, f"Physics drop failed: {str(e)}")
            return {"CANCELLED"}


class PD_OT_Apply(bpy.types.Operator):
    """Apply physics simulation"""
    bl_idname = "pd.apply"
    bl_label = "Apply"
    bl_description = "Apply the current state of the dropped objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = safe_context_access("scene")
        return scene and getattr(scene, 'dropped', False)

    def execute(self, context):
        try:
            with SafeOperation("apply_physics") as op:
                scene = safe_context_access("scene")
                if not scene:
                    self.report({'ERROR'}, constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                    return {"CANCELLED"}

                is_rigid = safe_context_access("scene.is_rigid", True)

                if is_rigid:
                    if rb.apply_rigid():
                        logger.info("Applied rigidbody physics simulation")
                    else:
                        self.report({'ERROR'}, "Failed to apply rigidbody simulation")
                        return {"CANCELLED"}
                else:
                    if cloth_module.apply_cloth():
                        logger.info("Applied cloth physics simulation")
                    else:
                        self.report({'ERROR'}, "Failed to apply cloth simulation")
                        return {"CANCELLED"}

                # Stop animation if playing and reset frame
                screen = safe_context_access("screen")
                if screen and getattr(screen, 'is_animation_playing', False):
                    bpy.ops.screen.animation_play()
                    logger.debug("Stopped animation playback after apply")

                # Set frame to start
                scene = safe_context_access("scene")
                if scene:
                    scene.frame_current = constants.DEFAULT_FRAME_START
                    logger.debug("Reset frame to start position after apply")

                # Mark operation as successful
                op.success = True
                self.report({'INFO'}, constants.SUCCESS_MESSAGES['PHYSICS_APPLIED'])
                return {"FINISHED"}

        except Exception as e:
            logger.error("Unexpected error in apply operation", e)
            self.report({'ERROR'}, f"Physics application failed: {str(e)}")
            return {"CANCELLED"}


class PD_OT_Reset(bpy.types.Operator):
    """Reset physics simulation"""
    bl_idname = "pd.reset"
    bl_label = "Reset"
    bl_description = "Reset the physics simulation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = safe_context_access("scene")
        return scene and getattr(scene, 'dropped', False)

    def execute(self, context):
        try:
            with SafeOperation("reset_physics") as op:
                # Stop animation if playing
                screen = safe_context_access("screen")
                if screen and getattr(screen, 'is_animation_playing', False):
                    bpy.ops.screen.animation_play()
                    logger.debug("Stopped animation playback")

                # Set frame to start
                scene = safe_context_access("scene")
                if scene:
                    scene.frame_current = constants.DEFAULT_FRAME_START

                # Apply current physics to clear everything
                is_rigid = safe_context_access("scene.is_rigid", True)
                if is_rigid:
                    if not rb.apply_rigid():
                        logger.warning("Issues occurred while resetting rigidbody physics")
                else:
                    if not cloth_module.apply_cloth():
                        logger.warning("Issues occurred while resetting cloth physics")

                # Mark operation as successful
                op.success = True
                logger.info("Physics reset completed successfully")
                self.report({'INFO'}, constants.SUCCESS_MESSAGES['SIMULATION_RESET'])
                return {"FINISHED"}

        except Exception as e:
            logger.error("Unexpected error in reset operation", e)
            self.report({'ERROR'}, f"Physics reset failed: {str(e)}")
            return {"CANCELLED"}


###############################################################################
# Force Field Operators
###############################################################################

class PD_OT_SimpleForce(bpy.types.Operator):
    """Add a simple force field"""
    bl_idname = "pd.simple_force"
    bl_label = "Add Simple Force"
    bl_description = "Add a simple force field"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = safe_context_access("scene")
        return scene and getattr(scene, 'dropped', False)

    def execute(self, context):
        try:
            with SafeOperation("add_simple_force"):
                # Get location from active object or use default
                active_object = safe_context_access("active_object")
                if active_object:
                    location = safe_object_access(active_object, "location", (0, 0, 0))
                else:
                    location = (0, 0, 0)
                    logger.warning("No active object found, using default location for force field")

                # Add force field
                bpy.ops.object.effector_add(
                    type='FORCE',
                    radius=1.0,
                    enter_editmode=False,
                    align='WORLD',
                    location=location
                )

                # Get the newly created force object
                force_object = safe_context_access("active_object")
                if not force_object:
                    self.report({'ERROR'}, "Failed to create force field object")
                    return {"CANCELLED"}

                # Configure force field
                utils.state.set_physics_dropper("force_object", force_object)

                # Set display properties
                force_object.empty_display_type = 'SPHERE'

                scene = safe_context_access("scene")
                if scene:
                    force_object.empty_display_size = getattr(scene, 'forcedistance', constants.FORCE_DISTANCE_DEFAULT)

                    # Set force field properties safely
                    if hasattr(force_object, 'field'):
                        force_object.field.strength = getattr(scene, 'forcestrength', constants.FORCE_STRENGTH_DEFAULT)
                        force_object.field.use_max_distance = True
                        force_object.field.distance_max = getattr(scene, 'forcedistance', constants.FORCE_DISTANCE_DEFAULT)
                        force_object.field.flow = getattr(scene, 'forceflow', constants.FORCE_FLOW_DEFAULT)

                logger.info("Added force field successfully")
                self.report({'INFO'}, constants.SUCCESS_MESSAGES['FORCE_ADDED'])
                return {"FINISHED"}

        except Exception as e:
            logger.error("Error adding force field", e)
            self.report({'ERROR'}, f"Failed to add force field: {str(e)}")
            return {"CANCELLED"}


class PD_OT_SimpleForceRemove(bpy.types.Operator):
    """Remove the simple force field"""
    bl_idname = "pd.simple_force_remove"
    bl_label = "Remove Simple Force"
    bl_description = "Remove the simple force field"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        force_obj = utils.state.get_physics_dropper("force_object")
        return force_obj is not None and utils.is_object_valid(force_obj)

    def execute(self, context):
        if rb.remove_simple_force():
            self.report({'INFO'}, constants.SUCCESS_MESSAGES['FORCE_REMOVED'])
            return {"FINISHED"}
        else:
            self.report({'WARNING'}, "Force field was already removed or not found")
            return {"FINISHED"}  # Still consider it successful


###############################################################################
# Baking Operators
###############################################################################

class PD_OT_BakeSimCache(bpy.types.Operator):
    """Bake physics to cache"""
    bl_idname = "pd.bake_sim_cache"
    bl_label = "Bake to Cache"
    bl_description = "Bake current physics simulation state to cache (preserves earthquake effects)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = safe_context_access("scene")
        screen = safe_context_access("screen")

        # Only allow baking when simulation is dropped AND animation is paused
        simulation_active = scene and getattr(scene, 'dropped', False)
        animation_paused = not (screen and getattr(screen, 'is_animation_playing', False))

        return simulation_active and animation_paused

    def execute(self, context):
        try:
            with SafeOperation("bake_simulation_cache") as op:
                from . import bake_utils

                scene = safe_context_access("scene")
                if not scene:
                    self.report({'ERROR'}, constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                    return {"CANCELLED"}

                start_frame = getattr(scene, 'w_startframe', constants.DEFAULT_FRAME_START)
                end_frame = getattr(scene, 'w_endframe', constants.DEFAULT_FRAME_END)

                # Bake the rigid body world cache - no other interference
                success = bake_utils.bake_rigidbody_simulation(start_frame, end_frame)

                if success:
                    # Reset to start state like apply/reset does
                    # Stop animation if playing
                    screen = safe_context_access("screen")
                    if screen and getattr(screen, 'is_animation_playing', False):
                        bpy.ops.screen.animation_play()
                        logger.debug("Stopped animation playback after cache baking")

                    # Set frame to start
                    scene.frame_current = constants.DEFAULT_FRAME_START
                    logger.debug("Reset frame to start position after cache baking")

                    # Mark operation as successful
                    op.success = True
                    self.report({'INFO'}, constants.SUCCESS_MESSAGES['BAKING_COMPLETE'])
                    return {"FINISHED"}

                self.report({'ERROR'}, constants.ERROR_MESSAGES['BAKING_FAILED'])
                return {"CANCELLED"}

        except Exception as e:
            logger.error("Unexpected error during baking", e)
            self.report({'ERROR'}, f"Baking failed: {str(e)}")
            return {"CANCELLED"}

    def _cleanup_collider_object(self):
        """Clean up the COLLIDER object after baking."""
        try:
            utils.safe_deselect_all()

            # Find and delete the COLLIDER object
            scene = safe_context_access("scene")
            if scene:
                collider = scene.objects.get(constants.COLLIDER_OBJECT_NAME)
                if collider and utils.is_object_valid(collider):
                    if utils.safe_object_delete(collider):
                        logger.debug("COLLIDER object deleted successfully")
                    else:
                        logger.warning("Failed to delete COLLIDER object")
                else:
                    # Also check for passive rigidbody objects
                    passive_obj = utils.state.get_rigidbody("passive")
                    if passive_obj and utils.is_object_valid(passive_obj):
                        if utils.safe_object_delete(passive_obj):
                            utils.state.set_rigidbody("passive", None)
                            logger.debug("Passive rigidbody object deleted")
        except Exception as e:
            logger.warning("Error during collider cleanup", e)


class PD_OT_BakeSimKeyframes(bpy.types.Operator):
    """Bake physics to keyframes"""
    bl_idname = "pd.bake_sim_keyframes"
    bl_label = "Bake to Keyframes"
    bl_description = "Bake current simulation to keyframes (preserves earthquake effects and external influences)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = safe_context_access("scene")
        screen = safe_context_access("screen")

        # Only allow baking when simulation is dropped AND animation is paused AND rigidbody
        simulation_active = scene and getattr(scene, 'dropped', False) and getattr(scene, 'is_rigid', True)
        animation_paused = not (screen and getattr(screen, 'is_animation_playing', False))

        return simulation_active and animation_paused

    def execute(self, context):
        try:
            with SafeOperation("bake_simulation_keyframes") as op:
                from . import bake_utils

                scene = safe_context_access("scene")
                if not scene:
                    self.report({'ERROR'}, constants.ERROR_MESSAGES['INVALID_CONTEXT'])
                    return {"CANCELLED"}

                start_frame = getattr(scene, 'w_startframe', constants.DEFAULT_FRAME_START)
                end_frame = getattr(scene, 'w_endframe', constants.DEFAULT_FRAME_END)

                # Check if animation is currently playing
                screen = safe_context_access("screen")
                if screen and getattr(screen, 'is_animation_playing', False):
                    self.report({'ERROR'}, "Cannot bake while animation is playing. Please pause the timeline first.")
                    return {"CANCELLED"}

                logger.info(f"Baking simulation to keyframes from frame {start_frame} to {end_frame}")

                # Step 1: First bake to cache (this preserves the current simulation state)
                try:
                    bake_utils.rb_bake_from_current_cache()
                    logger.info("Successfully baked current simulation to cache")
                except Exception as e:
                    logger.error("Failed to bake to cache before keyframe baking", e)
                    self.report({'ERROR'}, "Failed to bake current simulation to cache")
                    return {"CANCELLED"}

                # Step 2: Select active objects for keyframe baking
                if not rb.select_active():
                    self.report({'ERROR'}, "No active rigidbody objects found")
                    return {"CANCELLED"}

                # Step 3: Bake to keyframes from the cached simulation
                try:
                    bpy.ops.rigidbody.bake_to_keyframes(
                        frame_start=start_frame,
                        frame_end=end_frame,
                        step=1
                    )
                    logger.info("Successfully baked cached simulation to keyframes")

                    # Step 4: Reset to start state like apply/reset does
                    # Stop animation if playing
                    screen = safe_context_access("screen")
                    if screen and getattr(screen, 'is_animation_playing', False):
                        bpy.ops.screen.animation_play()
                        logger.debug("Stopped animation playback after keyframe baking")

                    # Set frame to start
                    scene.frame_current = constants.DEFAULT_FRAME_START
                    logger.debug("Reset frame to start position after keyframe baking")

                    # Apply the simulation (this cleans up physics and finalizes transforms)
                    if rb.apply_rigid():
                        logger.info("Applied rigidbody simulation after keyframe baking")
                    else:
                        logger.warning("Issues occurred while applying rigidbody after keyframe baking")

                    # Mark operation as successful
                    op.success = True
                    self.report({'INFO'}, constants.SUCCESS_MESSAGES['BAKING_COMPLETE'])
                    return {"FINISHED"}

                except Exception as e:
                    logger.error("Error baking to keyframes", e)
                    self.report({'ERROR'}, f"Failed to bake to keyframes: {str(e)}")
                    return {"CANCELLED"}

        except Exception as e:
            logger.error("Unexpected error in keyframe baking operation", e)
            self.report({'ERROR'}, f"Keyframe baking failed: {str(e)}")
            return {"CANCELLED"}

    def _cleanup_after_keyframe_bake(self):
        """Clean up after keyframe baking."""
        try:
            # Clean up COLLIDER object
            utils.safe_deselect_all()

            scene = safe_context_access("scene")
            if scene:
                collider = scene.objects.get(constants.COLLIDER_OBJECT_NAME)
                if collider and utils.is_object_valid(collider):
                    utils.safe_object_delete(collider)
                    logger.debug("COLLIDER object deleted after keyframe bake")

                # Also clean up passive object
                passive_obj = utils.state.get_rigidbody("passive")
                if passive_obj and utils.is_object_valid(passive_obj):
                    utils.safe_object_delete(passive_obj)
                    utils.state.set_rigidbody("passive", None)
                    logger.debug("Passive object deleted after keyframe bake")

        except Exception as e:
            logger.warning("Error during keyframe bake cleanup", e)


###############################################################################
# Animation Control Operators
###############################################################################

class PD_OT_PauseSim(bpy.types.Operator):
    """Toggle animation playback"""
    bl_idname = "pd.pause_sim"
    bl_label = "Pause/Play Simulation"
    bl_description = "Pause or play the physics simulation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = safe_context_access("scene")
        return scene and getattr(scene, 'dropped', False)

    def execute(self, context):
        try:
            screen = safe_context_access("screen")
            if screen:
                was_playing = getattr(screen, 'is_animation_playing', False)
                bpy.ops.screen.animation_play()

                if was_playing:
                    logger.debug("Paused animation playback")
                else:
                    logger.debug("Started animation playback")

                return {"FINISHED"}
            else:
                self.report({'ERROR'}, "Cannot access screen context")
                return {"CANCELLED"}

        except Exception as e:
            logger.error("Error toggling animation playback", e)
            self.report({'ERROR'}, f"Failed to toggle playback: {str(e)}")
            return {"CANCELLED"}


###############################################################################
# Misc Operators
###############################################################################

class PD_OT_Donate(bpy.types.Operator):
    """Show donation dialog"""
    bl_idname = "pd.donate"
    bl_label = "Donate"
    bl_description = "Support the development of this addon"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        split = layout.split(align=True, factor=0.5)
        split.scale_y = 1.5

        # Get icons safely
        icons = safe_context_access("scene.physics_dropper_icons")

        # Buy me a coffee button
        op = split.operator("wm.url_open", text="Buy me a Tea")
        if icons and 'BMAC' in icons:
            op.icon_value = icons['BMAC'].icon_id
        op.url = "https://buymeacoffee.com/FunAddons"

        # PayPal button
        op = split.operator("wm.url_open", text="Paypal")
        if icons and 'PAYPAL' in icons:
            op.icon_value = icons['PAYPAL'].icon_id
        op.url = "https://www.paypal.com/donate/?hosted_button_id=JYSV3UW4TJR64"

    def execute(self, context):
        return {"FINISHED"}


###############################################################################
# Register/Unregister
###############################################################################

# All operator classes to register
operators = [
    PD_OT_SetRigid,
    PD_OT_SetCloth,
    PD_OT_Drop,
    PD_OT_Apply,
    PD_OT_Reset,
    PD_OT_SimpleForce,
    PD_OT_SimpleForceRemove,
    PD_OT_BakeSimCache,
    PD_OT_BakeSimKeyframes,
    PD_OT_PauseSim,
    PD_OT_Donate,
]

# Register keymaps
def register_keymaps() -> bool:
    """Register keyboard shortcuts with improved error handling."""
    try:
        wm = bpy.context.window_manager
        if not wm:
            logger.error("Cannot access window manager for keymap registration")
            return False

        kc = wm.keyconfigs.addon
        if not kc:
            logger.error("Cannot access addon keyconfigs")
            return False

        registered_count = 0

        # Apply shortcut (Shift+V)
        try:
            km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
            kmi = km.keymap_items.new(
                "pd.apply",
                type=constants.DEFAULT_KEYMAPS['apply']['type'],
                value="PRESS",
                shift=constants.DEFAULT_KEYMAPS['apply']['shift'],
                ctrl=constants.DEFAULT_KEYMAPS['apply']['ctrl'],
                alt=constants.DEFAULT_KEYMAPS['apply']['alt']
            )
            utils.addon_keymaps['apply'] = (km, kmi)
            registered_count += 1
        except Exception as e:
            logger.warning("Failed to register 'apply' keymap", e)

        # Drop shortcut (V)
        try:
            km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
            kmi = km.keymap_items.new(
                "pd.drop",
                type=constants.DEFAULT_KEYMAPS['drop']['type'],
                value="PRESS",
                shift=constants.DEFAULT_KEYMAPS['drop']['shift'],
                ctrl=constants.DEFAULT_KEYMAPS['drop']['ctrl'],
                alt=constants.DEFAULT_KEYMAPS['drop']['alt']
            )
            utils.addon_keymaps['drop'] = (km, kmi)
            registered_count += 1
        except Exception as e:
            logger.warning("Failed to register 'drop' keymap", e)

        # Toggle force (F)
        try:
            km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
            kmi = km.keymap_items.new(
                "pd.simple_force",
                type=constants.DEFAULT_KEYMAPS['force']['type'],
                value="PRESS",
                shift=constants.DEFAULT_KEYMAPS['force']['shift'],
                ctrl=constants.DEFAULT_KEYMAPS['force']['ctrl'],
                alt=constants.DEFAULT_KEYMAPS['force']['alt']
            )
            utils.addon_keymaps['force'] = (km, kmi)
            registered_count += 1
        except Exception as e:
            logger.warning("Failed to register 'force' keymap", e)

        # Remove force (F release)
        try:
            km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
            kmi = km.keymap_items.new(
                "pd.simple_force_remove",
                type=constants.DEFAULT_KEYMAPS['force_remove']['type'],
                value=constants.DEFAULT_KEYMAPS['force_remove'].get('value', 'RELEASE'),
                shift=constants.DEFAULT_KEYMAPS['force_remove']['shift'],
                ctrl=constants.DEFAULT_KEYMAPS['force_remove']['ctrl'],
                alt=constants.DEFAULT_KEYMAPS['force_remove']['alt']
            )
            utils.addon_keymaps['force_remove'] = (km, kmi)
            registered_count += 1
        except Exception as e:
            logger.warning("Failed to register 'force_remove' keymap", e)

        logger.info(f"Registered {registered_count}/4 keymaps successfully")
        return registered_count > 0

    except Exception as e:
        logger.error("Critical error during keymap registration", e)
        return False

def unregister_keymaps() -> bool:
    """Unregister keyboard shortcuts with safe cleanup."""
    try:
        unregistered_count = 0

        for km_name, (km, kmi) in list(utils.addon_keymaps.items()):
            try:
                km.keymap_items.remove(kmi)
                unregistered_count += 1
                logger.debug(f"Unregistered keymap: {km_name}")
            except Exception as e:
                logger.warning(f"Failed to unregister keymap {km_name}", e)

        utils.addon_keymaps.clear()
        logger.info(f"Unregistered {unregistered_count} keymaps")
        return True

    except Exception as e:
        logger.error("Error during keymap unregistration", e)
        return False

def register() -> bool:
    """Register operators and keymaps with improved error handling."""
    try:
        registered_operators = 0

        for cls in operators:
            try:
                bpy.utils.register_class(cls)
                registered_operators += 1
                logger.debug(f"Registered operator: {cls.__name__}")
            except Exception as e:
                logger.error(f"Failed to register operator {cls.__name__}", e)

        if not register_keymaps():
            logger.warning("Keymap registration had issues")

        logger.info(f"Registered {registered_operators}/{len(operators)} operators")
        return registered_operators > 0

    except Exception as e:
        logger.error("Critical error during operator registration", e)
        return False

def unregister() -> bool:
    """Unregister operators and keymaps with safe cleanup."""
    try:
        if not unregister_keymaps():
            logger.warning("Keymap unregistration had issues")

        unregistered_operators = 0

        for cls in reversed(operators):
            try:
                bpy.utils.unregister_class(cls)
                unregistered_operators += 1
                logger.debug(f"Unregistered operator: {cls.__name__}")
            except Exception as e:
                logger.warning(f"Failed to unregister operator {cls.__name__}", e)

        logger.info(f"Unregistered {unregistered_operators}/{len(operators)} operators")
        return True

    except Exception as e:
        logger.error("Error during operator unregistration", e)
        return False