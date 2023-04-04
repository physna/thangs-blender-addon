import bpy
import threading
from services import ThangsSyncService


class THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button(bpy.types.Operator):
    """Save new file when syncing"""
    bl_idname = "thangs_blender_addon.sync_save_new_file_and_sync_button"
    bl_label = "Save & Sync"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if bpy.context.blend_data.is_saved:
            # TODO should probably move all the threading fun into the service
            sync_service = ThangsSyncService()
            threading.Thread(target=sync_service.sync_current_blender_file).start()
            return {'FINISHED'}

        return {'PASS_THROUGH'}
