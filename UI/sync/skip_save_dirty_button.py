import bpy
from services import get_sync_service


class THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button(bpy.types.Operator):
    """Save a dirty file operator before syncing"""
    bl_idname = "thangs_blender_addon.sync_save_dirty_yes_button"
    bl_label = "Sync Anyway"
    bl_options = {'INTERNAL'}

    def execute(self, _context):
        sync_service = get_sync_service()
        sync_service.start_sync_process()
        return {'FINISHED'}
