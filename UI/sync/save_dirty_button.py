import bpy
from services import get_sync_service, supress_sync_on_save, enable_sync_on_save


class THANGS_BLENDER_ADDON_OT_sync_save_dirty_button(bpy.types.Operator):
    """Save a dirty file operator before syncing"""
    bl_idname = "thangs_blender_addon.sync_save_dirty_button"
    bl_label = "Save & Sync"
    bl_options = {'INTERNAL'}

    def execute(self, _context):
        supress_sync_on_save()
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        enable_sync_on_save()

        sync_service = get_sync_service()
        sync_service.start_sync_process()
        return {'FINISHED'}
