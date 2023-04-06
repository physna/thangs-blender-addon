import bpy
from bpy.app.handlers import persistent


__supress_sync_on_save_handler__: bool = True


@persistent
def sync_on_save_handler(dummy):
    global __supress_sync_on_save_handler__

    if __supress_sync_on_save_handler__:
        return

    if not bpy.types.Scene.thangs_blender_addon_sync_panel_last_sync_time:
        return

    # TODO sync here
    print('do sync stuff')


def supress_sync_on_save():
    global __supress_sync_on_save_handler__

    __supress_sync_on_save_handler__ = True


def enable_sync_on_save():
    global __supress_sync_on_save_handler__

    __supress_sync_on_save_handler__ = False
