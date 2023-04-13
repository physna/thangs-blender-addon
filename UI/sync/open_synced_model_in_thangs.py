import bpy
import webbrowser
from config import get_config


class THANGS_BLENDER_ADDON_OT_open_synced_model_in_thangs(bpy.types.Operator):
    """Opens a synced model in Thangs"""
    bl_idname = "thangs_blender_addon.open_synced_model_in_thangs"
    bl_label = "Open in Thangs"
    bl_options = {'INTERNAL'}

    model_id: bpy.props.IntProperty()

    def execute(self, _context):
        thangs_config = get_config()
        url = f'{thangs_config.thangs_config["url"]}m/{self.model_id}'
        webbrowser.open(url)
        return {'FINISHED'}

