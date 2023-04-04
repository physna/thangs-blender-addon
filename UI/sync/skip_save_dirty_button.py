import bpy
import threading
from services import ThangsSyncService


class THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button(bpy.types.Operator):
    """Save a dirty file operator before syncing"""
    bl_idname = "thangs_blender_addon.sync_save_dirty_yes_button"
    bl_label = "Sync Anyway"
    bl_options = {'INTERNAL'}

    def execute(self, _context):
        # TODO should probably move all the threading fun into the service
        sync_service = ThangsSyncService()
        threading.Thread(target=sync_service.sync_current_blender_file).start()
        return {'FINISHED'}
