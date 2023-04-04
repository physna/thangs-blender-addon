from .sync_panel import THANGS_BLENDER_ADDON_PT_sync_panel
from .sync_button import THANGS_BLENDER_ADDON_OT_sync_button
from .unsaved_file_dialog import THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog
from .save_new_file_and_sync_button import THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button
from .dirty_file_dialog import THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog
from .save_dirty_button import THANGS_BLENDER_ADDON_OT_sync_save_dirty_button
from .skip_save_dirty_button import THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button

def register():
    import bpy
    bpy.utils.register_class(THANGS_BLENDER_ADDON_PT_sync_panel)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_save_dirty_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button)
    bpy.types.Scene.thangs_blender_addon_sync_panel_status_message = bpy.props.StringProperty(
        name='ThangsSyncAddonSyncPanelStatusMessage', default='')

def unregister():
    import bpy
    if hasattr(bpy.types.Scene, 'thangs_blender_addon_sync_panel_status_message'):
        del bpy.types.Scene.thangs_blender_addon_sync_panel_status_message

    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_save_dirty_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_PT_sync_panel)
