import bpy
from UI.common import View3DPanel
from .sync_button import THANGS_BLENDER_ADDON_OT_sync_button


class THANGS_BLENDER_ADDON_PT_sync_panel(bpy.types.Panel, View3DPanel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_idname = "thangs_blender_addon.sync_panel"
    bl_label = "Thangs Sync"

    def draw(self, context):
        layout = self.layout

        label_column = layout.column(align=True)
        label_column.label(text=context.scene.thangs_blender_addon_sync_panel_status_message)

        col = layout.column(align=True)
        row = col.row()
        row.operator(THANGS_BLENDER_ADDON_OT_sync_button.bl_idname,
                     text="Sync Model", icon='NONE')
