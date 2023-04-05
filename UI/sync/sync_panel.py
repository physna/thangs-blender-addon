import bpy
from UI.common import View3DPanel
from services import ThangsSyncService, SyncInfo, get_thumbnail_service
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
        else:
            sync_data: SyncInfo = self.thangs_sync_service.get_sync_info_text_block()
            if sync_data:
                model_id = sync_data['model_id']
                sha = sync_data['version_sha']
                open_in_thangs_row = layout.row()
                open_in_thangs_row.operator(THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs.bl_idname).model_id = model_id

                thumbnail_service = get_thumbnail_service()
                if not thumbnail_service.is_thumbnail_loaded(model_id, sha):
                    thumbnail_service.load_thumbnail(model_id, sha, sync_data['thumbnail_url'])

                thumbnail_row = layout.row()
                thumbnail_row.box().template_icon(icon_value=thumbnail_service.get_thumbnail_icon_id(model_id, sha), scale=7)

                last_sync_time_label_row = layout.row()
                last_sync_time_label_row.label(text='Last Sync Time:')
                last_sync_time_row = layout.row()
                last_sync_time_column = last_sync_time_row.column(align=True)
                last_sync_time_column.alignment = 'RIGHT'
                last_sync_time_column.label(text=sync_data['last_sync_time'].strftime('%x %X'))

        sync_button_row = layout.row()
        sync_button_row.operator(THANGS_BLENDER_ADDON_OT_sync_button.bl_idname, text="Sync Model", icon='NONE')
