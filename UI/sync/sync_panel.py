import bpy
from UI.common import View3DPanel
from services import ThangsSyncService, SyncInfo
from .sync_button import THANGS_BLENDER_ADDON_OT_sync_button
from .open_synced_model_in_thangs import THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs


class THANGS_BLENDER_ADDON_PT_sync_panel(bpy.types.Panel, View3DPanel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_idname = "thangs_blender_addon.sync_panel"
    bl_label = "Thangs Sync"

    def __init__(self):
        self.thangs_sync_service = ThangsSyncService()

    def draw(self, context):
        layout = self.layout

        if context.scene.thangs_blender_addon_sync_panel_status_message:
            status_label_row = layout.row()
            status_label_row.label(text=context.scene.thangs_blender_addon_sync_panel_status_message)

        sync_data: SyncInfo = self.thangs_sync_service.get_sync_info_text_block()
        if sync_data:
            last_sync_time_label_row = layout.row()
            last_sync_time_label_row.label(text='Last Sync Time:')
            last_sync_time_row = layout.row()
            last_sync_time_column = last_sync_time_row.column(align=True)
            last_sync_time_column.alignment = 'RIGHT'
            last_sync_time_column.label(text=sync_data['last_sync_time'].strftime('%x %X'))

            open_in_thangs_row = layout.row()
            open_in_thangs_row.operator(THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs.bl_idname).model_id = sync_data['model_id']


        row = layout.row()
        row.operator(THANGS_BLENDER_ADDON_OT_sync_button.bl_idname,
                     text="Sync Model", icon='NONE')
