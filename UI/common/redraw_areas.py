import bpy


def redraw_areas(area_types: iter = ["ALL"]):
    """ run tag_redraw for given area types """
    area_types = confirm_list(area_types)
    screens = [bpy.context.screen] if bpy.context.screen else bpy.data.screens
    for screen in screens:
        for area in screen.areas:
            for area_type in area_types:
                if area_type == "ALL" or area.type == area_type:
                    area.tag_redraw()


def confirm_list(arg):
    """ if single item passed, convert to list """
    if type(arg) not in (list, tuple):
        return [arg]
    return arg
