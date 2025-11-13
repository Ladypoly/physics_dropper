"""
UI panel classes for the Physics Dropper addon.

This module provides safe UI panel implementations with proper error handling,
validation, and logging for all panel operations.
"""

import bpy
from typing import Optional, Any
from . import constants
from . import logger
from . import utils
from .logger import safe_context_access, safe_object_access

# Get logger instance
log = logger.logger

def safe_icon_access(scene: Any, icon_collection_name: str, icon_name: str) -> int:
    """Safely access icon from icon collection.

    Args:
        scene: The scene object
        icon_collection_name: Name of the icon collection property
        icon_name: Name of the specific icon

    Returns:
        int: Icon ID or 0 if not found
    """
    try:
        icon_collection = safe_object_access(scene, icon_collection_name)
        if icon_collection and icon_name in icon_collection:
            icon = safe_object_access(icon_collection[icon_name], "icon_id", 0)
            return icon if icon else 0
        return 0
    except Exception as e:
        log.warning(f"Failed to access icon {icon_name}: {e}")
        return 0

def safe_keymap_access(keymap_name: str) -> bool:
    """Safely check if a keymap exists in addon keymaps.

    Args:
        keymap_name: Name of the keymap to check

    Returns:
        bool: True if keymap exists, False otherwise
    """
    try:
        return keymap_name in utils.addon_keymaps
    except Exception as e:
        log.warning(f"Failed to access keymap {keymap_name}: {e}")
        return False

def get_keymap_item(keymap_name: str) -> tuple:
    """Safely get keymap item.

    Args:
        keymap_name: Name of the keymap

    Returns:
        tuple: Keymap and keymap item, or (None, None) if not found
    """
    try:
        if keymap_name in utils.addon_keymaps:
            return utils.addon_keymaps[keymap_name]
        return None, None
    except Exception as e:
        log.warning(f"Failed to get keymap item {keymap_name}: {e}")
        return None, None

def safe_poll_not_dropped_rigidbody(context) -> bool:
    """Safe poll method for panels shown when not dropped and in rigidbody mode."""
    try:
        scene = safe_context_access("scene")
        if not scene:
            return False
        dropped = safe_object_access(scene, "dropped", False)
        is_rigid = safe_object_access(scene, "is_rigid", True)
        return not (dropped or not is_rigid)
    except Exception as e:
        log.warning(f"Safe poll failed: {e}")
        return False

def safe_poll_not_dropped_cloth(context) -> bool:
    """Safe poll method for panels shown when not dropped and in cloth mode."""
    try:
        scene = safe_context_access("scene")
        if not scene:
            return False
        dropped = safe_object_access(scene, "dropped", False)
        is_rigid = safe_object_access(scene, "is_rigid", True)
        return not (dropped or is_rigid)
    except Exception as e:
        log.warning(f"Safe poll failed: {e}")
        return False

###############################################################################
# Addon Preferences
###############################################################################

def get_hotkey_entry_item(km, kmi_name):
    """Get keymap item by operator name"""
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
    return None

class PD_AddonPreferences(bpy.types.AddonPreferences):
    """Extension preferences for keybinding configuration."""
    bl_idname = __package__

    def draw(self, context):
        """Draw the preferences panel with HardOps-style keymap interface."""
        try:
            import rna_keymap_ui

            layout = self.layout
            col = layout.column()

            col.label(text="Keyboard Shortcuts:", icon='KEYINGSET')
            col.separator()

            # Get user keyconfig for persistent changes
            wm = bpy.context.window_manager
            kc = wm.keyconfigs.user

            # Define our keymaps to show
            keymap_items = [
                ("3D View", "pd.drop", "Drop Objects", 'RIGID_BODY'),
                ("3D View", "pd.apply", "Apply Physics", 'CHECKMARK'),
                ("3D View", "pd.force_mode", "Force Mode", 'FORCE_FORCE')
            ]

            for km_name, operator_name, label, icon in keymap_items:
                try:
                    # Create a box for each keymap item
                    box = col.box()
                    row = box.row()
                    row.label(text=label, icon=icon)

                    # Get the keymap
                    km = kc.keymaps.get(km_name)
                    if km:
                        kmi = get_hotkey_entry_item(km, operator_name)
                        if kmi:
                            # Use Blender's built-in keymap UI - this automatically saves changes!
                            box.context_pointer_set("keymap", km)
                            rna_keymap_ui.draw_kmi([], kc, km, kmi, box, 0)
                        else:
                            box.label(text="No hotkey entry found")
                            box.label(text="Enable addon to register keymaps")
                    else:
                        box.label(text=f"Keymap '{km_name}' not found")

                except Exception as e:
                    log.warning(f"Failed to draw keymap for {label}: {e}")
                    box = col.box()
                    box.label(text=f"Error loading {label}", icon="ERROR")

            col.separator()
            col.label(text="Changes are saved automatically with user preferences", icon='INFO')

        except Exception as e:
            log.error(f"Failed to draw addon preferences: {e}")
            # Fallback layout
            try:
                layout = self.layout
                layout.label(text="Error loading preferences panel", icon="ERROR")
            except:
                pass

###############################################################################
# Main Panel
###############################################################################

class PD_PT_PhysicsDropper(bpy.types.Panel):
    """Main Physics Dropper panel with safe UI handling."""
    bl_label = "Physics Dropper"
    bl_idname = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'PhyDrop'

    def draw_header(self, context):
        """Draw panel header with safe icon access."""
        try:
            layout = self.layout
            scene = safe_context_access("scene")
            if scene:
                icon_id = safe_icon_access(scene, "physics_dropper_icons", "DROPBOX")
                layout.label(text="", icon_value=icon_id)
            else:
                layout.label(text="", icon='PHYSICS')
        except Exception as e:
            log.warning(f"Failed to draw panel header: {e}")
            try:
                layout = self.layout
                layout.label(text="", icon='PHYSICS')
            except:
                pass

    def draw(self, context):
        """Draw main panel with comprehensive safety measures."""
        try:
            layout = self.layout
            scene = safe_context_access("scene")

            if not scene:
                layout.label(text="Scene not available", icon="ERROR")
                return

            # Get scene properties safely
            dropped = safe_object_access(scene, "dropped", False)
            is_rigid = safe_object_access(scene, "is_rigid", True)
            selected_objects = safe_context_access("selected_objects")

            # Reset button if simulation is running
            if dropped:
                row = layout.row()
                row.operator("pd.reset", text="RESET", icon='X')

            # Mode selection buttons if not running
            if not dropped:
                try:
                    row = layout.row(align=True)
                    row.scale_y = 1.5
                    row.operator(
                        "pd.set_rigid",
                        text="Rigidbody",
                        depress=is_rigid,
                        icon='RIGID_BODY'
                    )
                    row.operator(
                        "pd.set_cloth",
                        text="Cloth",
                        depress=not is_rigid,
                        icon='MOD_CLOTH'
                    )
                except Exception as e:
                    log.warning(f"Failed to draw mode selection: {e}")

            # Drop or apply buttons
            if dropped:
                self._draw_simulation_controls(layout, scene, is_rigid)
            else:
                self._draw_drop_controls(layout, scene, is_rigid, selected_objects)

            # Cloth presets for cloth mode when not running
            if not dropped and not is_rigid:
                self._draw_cloth_presets(layout, scene)

        except Exception as e:
            log.error(f"Failed to draw main panel: {e}")
            try:
                layout = self.layout
                layout.label(text="Error loading panel", icon="ERROR")
            except:
                pass

    def _draw_simulation_controls(self, layout, scene, is_rigid: bool):
        """Draw simulation control buttons when simulation is running."""
        try:
            # Apply button
            col = layout.column(align=True)
            col.scale_y = 2.0
            col.alert = True
            col.operator("pd.apply", text="Apply", icon='CHECKMARK')

            # Bake to keyframes (only for rigidbody)
            if is_rigid:
                col = layout.column(align=True)
                col.scale_y = 2.0
                col.operator("pd.bake_sim_keyframes", text="Bake to Keyframes", icon='KEYFRAME')

            # Exit drop mode button
            col = layout.column(align=True)
            col.scale_y = 1.0
            col.operator("pd.exit_physics_mode", text="Exit Drop Mode", icon='CANCEL')

            # Additional simulation controls
            col = layout.column()
            col.scale_y = 1.5

            # Pause/play button
            screen = safe_context_access("screen")
            is_playing = safe_object_access(screen, "is_animation_playing", False) if screen else False
            play_icon = 'PAUSE' if is_playing else 'PLAY'
            col.operator("pd.pause_sim", text="Pause/Play Simulation", icon=play_icon)

            col.separator()

            # Force field controls
            force_object = utils.state.get_physics_dropper("forceobject")
            if force_object:
                col.operator("pd.simple_force_remove", text="Remove Simple Force", icon='CANCEL')
            else:
                col.operator("pd.simple_force", text="Add Simple Force", icon='FORCE_FORCE')

                # Info about force mode controls
                info_box = col.box()
                info_box.scale_y = 0.8
                info_box.label(text="Force Mode Controls:", icon='INFO')
                info_box.label(text="• Press F to create interactive force")
                info_box.label(text="• Mouse wheel to scale force distance")
                info_box.label(text="• Hold Ctrl to snap to surface")

            # Force properties
            try:
                row = col.row(align=True)
                row.scale_y = 1.0
                row.prop(scene, "forcestrength", text="Strength")
                row.prop(scene, "forceflow", text="Flow")
                row.prop(scene, "forcedistance", text="Distance")
            except Exception as e:
                log.warning(f"Failed to draw force properties: {e}")

            col.separator()

            # Earthquake controls
            self._draw_earthquake_controls(col, scene)

        except Exception as e:
            log.warning(f"Failed to draw simulation controls: {e}")

    def _draw_drop_controls(self, layout, scene, is_rigid: bool, selected_objects):
        """Draw drop controls when simulation is not running."""
        try:
            # Drop button
            row = layout.row(align=True)
            row.enabled = bool(selected_objects)
            row.scale_y = 2.0

            # Get appropriate icon
            icon_name = 'DROPBOX' if is_rigid else 'DROPCLOTH'
            icon_id = safe_icon_access(scene, "physics_dropper_icons", icon_name)
            if icon_id:
                row.operator("pd.drop", text="Drop", icon_value=icon_id)
            else:
                # Fallback to built-in icons
                fallback_icon = 'RIGID_BODY' if is_rigid else 'MOD_CLOTH'
                row.operator("pd.drop", text="Drop", icon=fallback_icon)

            # Message if no objects selected
            if not selected_objects:
                layout.label(text="Please select a mesh object")

        except Exception as e:
            log.warning(f"Failed to draw drop controls: {e}")

    def _draw_earthquake_controls(self, col, scene):
        """Draw earthquake control properties."""
        try:
            row = col.row(align=True)
            row.scale_y = 1.0
            row.prop(scene, "earthquake", text="Earthquake")

            # Earthquake axis controls with icons
            x_icon = safe_icon_access(scene, "physics_dropper_icons", "X")
            y_icon = safe_icon_access(scene, "physics_dropper_icons", "Y")
            z_icon = safe_icon_access(scene, "physics_dropper_icons", "Z")

            if x_icon:
                row.prop(scene, "earthquakex", icon_value=x_icon, text="")
            else:
                row.prop(scene, "earthquakex", text="X")

            if y_icon:
                row.prop(scene, "earthquakey", icon_value=y_icon, text="")
            else:
                row.prop(scene, "earthquakey", text="Y")

            if z_icon:
                row.prop(scene, "earthquakez", icon_value=z_icon, text="")
            else:
                row.prop(scene, "earthquakez", text="Z")

        except Exception as e:
            log.warning(f"Failed to draw earthquake controls: {e}")

    def _draw_cloth_presets(self, layout, scene):
        """Draw cloth preset selection."""
        try:
            col = layout.column(align=True)
            col.label(text="Presets:")
            col.separator()
            row = col.row(align=True)
            row.prop(scene, "c_a_presets", text="Presets", expand=True)
        except Exception as e:
            log.warning(f"Failed to draw cloth presets: {e}")


###############################################################################
# Active Settings Panel
###############################################################################

class PD_PT_ActiveSettings(bpy.types.Panel):
    """Panel for active object physics settings with safe UI handling."""
    bl_label = "Active Settings"
    bl_idname = "PD_PT_ActiveSettings"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_rigidbody(context)

    def draw_header(self, context):
        """Draw header with safe access."""
        try:
            layout = self.layout
            layout.label(text="", icon='RIGID_BODY')
        except Exception as e:
            log.warning(f"Failed to draw active settings header: {e}")

    def draw(self, context):
        """Draw active settings panel with safe property access."""
        try:
            layout = self.layout
            scene = safe_context_access("scene")

            if not scene:
                layout.label(text="Scene not available", icon="ERROR")
                return

            col = layout.column(align=True)

            # Optimization settings
            try:
                box = col.box()
                box.prop(scene, 'optimizehighpoly', text="Use Proxy for Highpoly Objects")

                optimize_highpoly = safe_object_access(scene, 'optimizehighpoly', False)
                if optimize_highpoly:
                    row = box.row(align=True)
                    row.prop(scene, 'a_voxelsize', text="Voxel Size")
                    row.prop(scene, 'a_decimaterate', text="Decimate Rate")
            except Exception as e:
                log.warning(f"Failed to draw optimization settings: {e}")

            # Physics settings
            try:
                col.prop(scene, 'a_shape', text="Shape")
                col.prop(scene, 'a_mass', text="Mass")
                col.prop(scene, 'a_friction', text="Friction", slider=True)
                col.prop(scene, 'a_bounciness', text="Bounciness", slider=True)
                col.prop(scene, 'a_margin', text="Margin", slider=True)
                col.prop(scene, 'a_tra_damp', text="Damping Translation", slider=True)
                col.prop(scene, 'a_rot_damp', text="Damping Rotation", slider=True)
            except Exception as e:
                log.warning(f"Failed to draw physics settings: {e}")

        except Exception as e:
            log.error(f"Failed to draw active settings panel: {e}")
            try:
                layout = self.layout
                layout.label(text="Error loading panel", icon="ERROR")
            except:
                pass


###############################################################################
# World Settings Panel
###############################################################################

class PD_PT_WorldSettings(bpy.types.Panel):
    """Panel for world physics settings"""
    bl_label = "World Settings"
    bl_idname = "PD_PT_WorldSettings"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_rigidbody(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='WORLD')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        row = col.row(align=True)
        row.prop(context.scene, 'w_startframe', text="Start Frame")
        row.prop(context.scene, 'w_endframe', text="End Frame")
        
        col.prop(context.scene, 'w_subframes', text="Substeps Per Frame")
        col.prop(context.scene, 'w_solver_iterations', text="Solver Iterations")
        col.prop(context.scene, 'w_split_impulse', text="Split Impulse")


###############################################################################
# Passive Settings Panel
###############################################################################

class PD_PT_PassiveSettings(bpy.types.Panel):
    """Panel for passive object physics settings"""
    bl_label = "Passive Settings"
    bl_idname = "PD_PT_PassiveSettings"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_rigidbody(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='OUTLINER_OB_MESH')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        # Optimization settings
        box = col.box()
        box.prop(context.scene, 'p_optimizehighpoly', text="Use Proxy for Highpoly Objects")
        
        if context.scene.p_optimizehighpoly:
            row = box.row(align=True)
            row.prop(context.scene, 'p_voxelsize', text="Voxel Size")
            row.prop(context.scene, 'p_decimaterate', text="Decimate Rate")
        
        # Physics settings
        col.prop(context.scene, 'p_shape', text="Shape")
        col.prop(context.scene, 'p_friction', text="Friction", slider=True)
        col.prop(context.scene, 'p_bounciness', text="Bounciness", slider=True)
        col.prop(context.scene, 'p_margin', text="Margin", slider=True)


###############################################################################
# Cloth Settings Panels
###############################################################################

class PD_PT_Stiffness(bpy.types.Panel):
    """Panel for cloth stiffness settings"""
    bl_label = "Stiffness"
    bl_idname = "PD_PT_Stiffness"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='DRIVER_DISTANCE')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.prop(context.scene, 'ca_stiff_tension', text="Tension")
        col.prop(context.scene, 'ca_stiff_compression', text="Compression")
        col.prop(context.scene, 'ca_stiff_shear', text="Shear")
        col.prop(context.scene, 'ca_stiff_bending', text="Bending")


class PD_PT_Damping(bpy.types.Panel):
    """Panel for cloth damping settings"""
    bl_label = "Damping"
    bl_idname = "PD_PT_Damping"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='SMOOTHCURVE')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.prop(context.scene, 'ca_damp_tension', text="Tension")
        col.prop(context.scene, 'ca_damp_compression', text="Compression")
        col.prop(context.scene, 'ca_damp_shear', text="Shear")
        col.prop(context.scene, 'ca_damp_bending', text="Bending")


class PD_PT_InternalSpring(bpy.types.Panel):
    """Panel for internal spring settings"""
    bl_label = "Internal Spring"
    bl_idname = "PD_PT_InternalSpring"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene, 'ca_internalsprings', text="")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.prop(context.scene, 'ca_internalspringmaxlength', text="Max Spring Creation Length")
        col.prop(context.scene, 'ca_internalspringmaxdevision', text="Max Creation Diversion")
        col.prop(context.scene, 'ca_internalspringtension', text="Tension")
        col.prop(context.scene, 'ca_internalspringcompression', text="Compression")
        col.prop(context.scene, 'ca_internalspringmaxtension', text="Max Tension")
        col.prop(context.scene, 'ca_internalspringmaxcompression', text="Max Compression")


class PD_PT_Pressure(bpy.types.Panel):
    """Panel for cloth pressure settings"""
    bl_label = "Pressure"
    bl_idname = "PD_PT_Pressure"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene, 'ca_usepressure', text="")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.prop(context.scene, 'ca_pressure', text="Pressure")
        col.prop(context.scene, 'ca_pressurescale', text="Pressure Scale")
        col.prop(context.scene, 'ca_pressurefluiddensity', text="Fluid Density")


class PD_PT_SelfCollision(bpy.types.Panel):
    """Panel for cloth self-collision settings"""
    bl_label = "Self Collision"
    bl_idname = "PD_PT_SelfCollision"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene, 'ca_selfcollision', text="")

    def draw(self, context):
        layout = self.layout
        
        layout.prop(context.scene, 'ca_selfcollisionfriction', text="Friction")
        layout.prop(context.scene, 'ca_selfcollisiondistance', text="Distance")
        layout.prop(context.scene, 'ca_selfcollisionimpulseclamping', text="Impulse Clamping")


class PD_PT_AdvancedClothSettings(bpy.types.Panel):
    """Panel for advanced cloth settings"""
    bl_label = "Advanced Cloth Settings"
    bl_idname = "PD_PT_AdvancedClothSettings"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='SETTINGS')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.prop(context.scene, 'ca_qualitysteps', text="Quality Steps")
        col.prop(context.scene, 'ca_quality', text="Collision Quality")
        col.prop(context.scene, 'ca_minimumdistance', text="Collision Distance")
        col.prop(context.scene, 'ca_impulseclamping', text="Collision Impulse Clamping")
        col.prop(context.scene, 'ca_mass', text="Mass")
        col.prop(context.scene, 'ca_air_viscosity', text="Air Viscosity")


class PD_PT_WorldCollisionSettings(bpy.types.Panel):
    """Panel for world collision settings for cloth"""
    bl_label = "World Collision Settings"
    bl_idname = "PD_PT_WorldCollisionSettings"
    bl_parent_id = "PD_PT_PhysicsDropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Poll with safe context access."""
        return safe_poll_not_dropped_cloth(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='WORLD')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        # Optimization settings
        box = col.box()
        box.prop(context.scene, 'p_optimizehighpoly', text="Use Proxy for Highpoly Objects")
        
        if context.scene.p_optimizehighpoly:
            row = box.row(align=True)
            row.prop(context.scene, 'p_voxelsize', text="Voxel Size")
            row.prop(context.scene, 'p_decimaterate', text="Decimate Rate")
        
        # Collision settings
        col.prop(context.scene, 'w_endframe', text="Simulation Length")
        col.prop(context.scene, 'c_p_damping', text="Damping", slider=True)
        col.prop(context.scene, 'c_p_thick_outer', text="Outer Thickness", slider=True)
        col.prop(context.scene, 'c_p_thick_inner', text="Inner Thickness", slider=True)
        col.prop(context.scene, 'c_p_friction', text="Friction", slider=True)


###############################################################################
# Register/Unregister
###############################################################################

# All panel classes to register
panels = [
    PD_AddonPreferences,
    PD_PT_PhysicsDropper,
    PD_PT_ActiveSettings,
    PD_PT_WorldSettings,
    PD_PT_PassiveSettings,
    PD_PT_Stiffness,
    PD_PT_Damping,
    PD_PT_InternalSpring,
    PD_PT_Pressure,
    PD_PT_SelfCollision,
    PD_PT_AdvancedClothSettings,
    PD_PT_WorldCollisionSettings,
]

def register():
    """Register panel classes with error handling."""
    try:
        for cls in panels:
            try:
                bpy.utils.register_class(cls)
                log.debug(f"Registered panel class: {cls.__name__}")
            except Exception as e:
                log.error(f"Failed to register panel class {cls.__name__}: {e}")
        log.info("Panel registration completed")
    except Exception as e:
        log.error(f"Critical error during panel registration: {e}")

def unregister():
    """Unregister panel classes with error handling."""
    try:
        for cls in reversed(panels):
            try:
                bpy.utils.unregister_class(cls)
                log.debug(f"Unregistered panel class: {cls.__name__}")
            except Exception as e:
                log.warning(f"Failed to unregister panel class {cls.__name__}: {e}")
        log.info("Panel unregistration completed")
    except Exception as e:
        log.error(f"Critical error during panel unregistration: {e}")
