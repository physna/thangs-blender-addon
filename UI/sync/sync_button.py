import bpy
from services import get_sync_service

class THANGS_BLENDER_ADDON_OT_sync_button(bpy.types.Operator):
    """Sync Model"""
    bl_idname = "thangs_blender_addon.sync_button"
    bl_label = "Sync Model"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        if not bpy.context.blend_data.is_saved:
            return bpy.ops.thangs_blender_addon.sync_unsaved_file_dialog('INVOKE_DEFAULT')

        if bpy.context.blend_data.is_dirty:
            return bpy.ops.thangs_blender_addon.sync_dirty_file_dialog('INVOKE_DEFAULT')

    def execute(self, _context):
        sync_service = get_sync_service()
        sync_service.start_sync_process()
        return {'FINISHED'}

