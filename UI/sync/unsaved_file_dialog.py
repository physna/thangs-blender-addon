import bpy
from .save_new_file_and_sync_button import THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button


class THANGS_BLENDER_ADDON_OT_sync_unsaved_file_dialog(bpy.types.Operator):
    """Unsaved file dialog when syncing"""
    bl_idname = "thangs_blender_addon.sync_unsaved_file_dialog"
    bl_label = "Unsaved File"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        label_row = layout.row()
        label_row.label(text="Current file has not been saved.")
        label_row2 = layout.row()
        label_row2.label(text="Please save before syncing to Thangs.")
        save_button_row = layout.row()
        save_button_row.operator(THANGS_BLENDER_ADDON_OT_sync_save_new_file_and_sync_button.bl_idname)
