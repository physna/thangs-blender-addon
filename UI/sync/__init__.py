from .sync_panel import THANGS_BLENDER_ADDON_PT_sync_panel, update_sync_on_save
from .sync_button import THANGS_BLENDER_ADDON_OT_sync_button
from .unsaved_file_dialog import THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog
from .save_new_file_and_sync_button import THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button
from .dirty_file_dialog import THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog
from .save_dirty_button import THANGS_BLENDER_ADDON_OT_sync_save_dirty_button
from .skip_save_dirty_button import THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button
from .open_synced_model_in_thangs import THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs
from services import sync_on_save_handler


def register():
    import bpy
    bpy.utils.register_class(THANGS_BLENDER_ADDON_PT_sync_panel)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_save_dirty_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button)
    bpy.utils.register_class(THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs)

    # TODO reset these on load
    bpy.types.Scene.thangs_blender_addon_sync_panel_status_message = bpy.props.StringProperty(
        name='ThangsSyncAddonSyncPanelStatusMessage', default='')
    bpy.types.Scene.thangs_blender_addon_sync_panel_sync_on_save = bpy.props.BoolProperty(
        name='Sync on Save', default=False, update=update_sync_on_save)
    bpy.types.Scene.thangs_blender_addon_sync_panel_sync_as_public_model = bpy.props.BoolProperty(
        name='Public Sharing', default=False)

    bpy.app.handlers.save_post.append(sync_on_save_handler)


def unregister():
    import bpy

    bpy.app.handlers.save_post.remove(sync_on_save_handler)

    if hasattr(bpy.types.Scene, 'thangs_blender_addon_sync_panel_sync_as_public_model'):
        del bpy.types.Scene.thangs_blender_addon_sync_panel_sync_as_public_model

    if hasattr(bpy.types.Scene, 'thangs_blender_addon_sync_panel_status_message'):
        del bpy.types.Scene.thangs_blender_addon_sync_panel_status_message

    if hasattr(bpy.types.Scene, 'thangs_blender_addon_sync_panel_sync_on_save'):
        del bpy.types.Scene.thangs_blender_addon_sync_panel_sync_on_save

    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_save_dirty_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_OT_sync_button)
    bpy.utils.unregister_class(THANGS_BLENDER_ADDON_PT_sync_panel)
