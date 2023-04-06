import bpy
from services import get_sync_service
from .sync_on_save_handler import supress_sync_on_save, enable_sync_on_save


class THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button(bpy.types.Operator):
    """Save new file when syncing"""
    bl_idname = "thangs_blender_addon.sync_save_new_file_and_sync_button"
    bl_label = "Save & Sync"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        supress_sync_on_save()
        bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        enable_sync_on_save()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if bpy.context.blend_data.is_saved:
            sync_service = get_sync_service()
            sync_service.start_sync_process()
            return {'FINISHED'}

        return {'PASS_THROUGH'}
