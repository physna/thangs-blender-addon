import bpy
from .skip_save_dirty_button import THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button
from .save_dirty_button import THANGS_BLENDER_ADDON_OT_sync_save_dirty_button


class THANGS_BLENDER_ADDON_OT_sync_dirty_file_dialog(bpy.types.Operator):
    """Dirty file dialog when syncing"""
    bl_idname = "thangs_blender_addon.sync_dirty_file_dialog"
    bl_label = "Unsaved Changes"
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
        label_row.label(text="Current file has changes that have not been saved.")
        label_row2 = layout.row()
        label_row2.label(text="Do you want to save before syncing?")
        save_button_row = layout.row()
        save_and_sync_column = save_button_row.column(align=True)
        save_and_sync_column.operator(THANGS_BLENDER_ADDON_OT_sync_save_dirty_button.bl_idname)
        skip_save_and_sync_column = save_button_row.column(align=True)
        skip_save_and_sync_column.operator(THANGS_BLENDER_ADDON_OT_sync_skip_save_dirty_button.bl_idname)
