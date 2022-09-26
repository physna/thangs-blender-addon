# <pep8 compliant>
import webbrowser
import bpy
from bpy.types import (Panel,
                       PropertyGroup,
                       Operator,
                       WindowManager,
                       )
from bpy.props import (StringProperty,
                       PointerProperty,
                       FloatVectorProperty,
                       BoolProperty,
                       IntProperty
                       )
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from bpy.app.handlers import persistent
import bpy.utils.previews
from urllib.request import urlopen
import os
from .thangs_fetcher import ThangsFetcher
from .thangs_events import ThangsEvents
from . import addon_updater_ops
import socket
import platform
import requests
import logging

log = logging.getLogger(__name__)


bl_info = {
    "name": "Thangs Model Search",
    "author": "Thangs",
    "version": (0, 1, 6),
    "blender": (3, 2, 0),
    "location": "VIEW 3D > Tools > Thangs Search",
    "description": "Browse and download free 3D models",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/RandyHucker/thangs-blender-addon",
    "tracker_url": "https://github.com/RandyHucker/thangs-blender-addon/issues/new/choose",
    "category": "Import/Export"
}


@addon_updater_ops.make_annotations
class DemoPreferences(bpy.types.AddonPreferences):
    """Demo bare-bones preferences"""
    bl_idname = __package__

    # Addon updater preferences.

    auto_check_update: BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False
    )

    updater_interval_months: IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0)

    updater_interval_days: IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31)

    updater_interval_hours: IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23)

    updater_interval_minutes: IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59)

    def draw(self, context):
        layout = self.layout

        # Works best if a column, or even just self.layout.
        mainrow = layout.row()
        col = mainrow.column()

        # Updater draw function, could also pass in col as third arg.
        addon_updater_ops.update_settings_ui(self, context)


def confirm_list(object):
    """ if single item passed, convert to list """
    if type(object) not in (list, tuple):
        object = [object]
    return object


def tag_redraw_areas(area_types: iter = ["ALL"]):
    """ run tag_redraw for given area types """
    if fetcher.searching == False:
        if fetcher.thangs_ui_mode == 'SEARCH':
            fetcher.thangs_ui_mode = 'VIEW'
    area_types = confirm_list(area_types)
    screens = [bpy.context.screen] if bpy.context.screen else bpy.data.screens
    for screen in screens:
        for area in screen.areas:
            for area_type in area_types:
                if area_type == "ALL" or area.type == area_type:
                    area.tag_redraw()


def on_complete_search():
    tag_redraw_areas()
    return


fetcher = ThangsFetcher(callback=on_complete_search)
amplitude = ThangsEvents()

#URLlist = []
ButtonSearch = "Search"
# Added
PageNumber = fetcher.PageNumber
#Results = fetcher.Results

pcoll = fetcher.pcoll

PageTotal = fetcher.PageTotal
fetcher.thangs_ui_mode = 'SEARCH'


def setSearch():
    global ButtonSearch
    ButtonSearch = bpy.context.scene.thangs_model_search
    return None


def LastPage():
    if fetcher.searching:
        return None

    if fetcher.PageNumber == fetcher.PageTotal:
        return None
    else:
        fetcher.PageNumber = fetcher.PageTotal
        fetcher.search(fetcher.query)
        return None


def IncPage():
    if fetcher.searching:
        return None
    # Pages = Results/7
    if fetcher.PageNumber < fetcher.PageTotal:
        fetcher.PageNumber = fetcher.PageNumber + 1
        fetcher.search(fetcher.query)
    return None


def DecPage():
    if fetcher.searching:
        return None
    if fetcher.PageNumber == 1:
        return None
    fetcher.PageNumber = fetcher.PageNumber - 1
    fetcher.search(fetcher.query)
    return None


def FirstPage():
    if fetcher.searching:
        return None
    fetcher.PageNumber = 1
    fetcher.search(fetcher.query)
    return None


class SearchButton(bpy.types.Operator):
    """Searches Thangs for Meshes"""
    bl_idname = "search.thangs"
    bl_label = " "

    def execute(self, context):
        setSearch()
        return {'FINISHED'}


class LastPageChange(bpy.types.Operator):
    """Go to Last Page"""
    bl_idname = "lastpage.thangs"
    bl_label = " Last Page"

    def execute(self, context):
        LastPage()
        return {'FINISHED'}


class IncPageChange(bpy.types.Operator):
    """Go to Next Page"""
    bl_idname = "incpage.thangs"
    bl_label = " Next Page"

    def execute(self, context):
        IncPage()
        return {'FINISHED'}


class DecPageChange(bpy.types.Operator):
    """Go to Previous Page"""
    bl_idname = "decpage.thangs"
    bl_label = " Previous Page"

    def execute(self, context):
        DecPage()
        return {'FINISHED'}


class FirstPageChange(bpy.types.Operator):
    """Go to First Page"""
    bl_idname = "firstpage.thangs"
    bl_label = "First Page"

    def execute(self, context):
        FirstPage()
        return {'FINISHED'}


def Model_Event(position):
    amplitude.send_amplitude_event("Thangs Model Link", event_properties={
        'path': fetcher.modelInfo[position][1],
        'type': "text",
                'domain': fetcher.modelInfo[position][5],
                'scope': fetcher.modelInfo[position][6],
                'searchIndex': fetcher.modelInfo[position][3],
                'phyndexerID': fetcher.modelInfo[position][2],
                'searchMetadata': fetcher.searchMetaData,
    })
    data = {
        "modelId": fetcher.modelInfo[position][2],
        "searchId": fetcher.uuid,
        "searchResultIndex": fetcher.modelInfo[position][3],
    }
    amplitude.send_thangs_event("Results", data)
    return


class WM_OT_url_pop1(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop1"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(0)
        return {'FINISHED'}


class WM_OT_url_pop2(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop2"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(1)
        return {'FINISHED'}


class WM_OT_url_pop3(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop3"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(2)
        return {'FINISHED'}


class WM_OT_url_pop4(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop4"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(3)
        return {'FINISHED'}


class WM_OT_url_pop5(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop5"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(4)
        return {'FINISHED'}


class WM_OT_url_pop6(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop6"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(5)
        return {'FINISHED'}


class WM_OT_url_pop7(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop7"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(6)
        return {'FINISHED'}


class WM_OT_url_pop8(Operator):
    """Open model in browser"""
    bl_idname = "wm.url_pop8"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to open",
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(7)
        return {'FINISHED'}


class ThangsLink(bpy.types.Operator):
    """Click to continue on Thangs"""
    bl_idname = "link.thangs"
    #bl_label = "Search"
    bl_label = "Redirect to Thangs"

    def execute(self, context):
        amplitude.send_amplitude_event("nav to thangs", event_properties={
                                       'device_os': str(fetcher.devideOS), 'device_ver': str(fetcher.deviceVer), 'source': "blender"})
        webbrowser.open("https://thangs.com/search/"+fetcher.query +
                        "?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender&fileTypes=stl%2Cgltf%2Cobj%2Cfbx%2Cglb%2Csldprt%2Cstep%2Cmtl%2Cdxf%2Cstp&scope=thangs", new=0, autoraise=True)
        return {'FINISHED'}


icon_collections = {}
icons_dict = bpy.utils.previews.new()
icon_collections["main"] = icons_dict
icons_dict = icon_collections["main"]
icons_dir = os.path.join(os.path.dirname(__file__), "icons")
icons_dict.load("ThangsT", os.path.join(icons_dir, "T.png"), 'IMAGE')


class THANGS_OT_search_invoke(Operator):
    """Search for Query"""

    bl_idname = "thangs.search_invoke"
    bl_label = "Clear Search   "
    bl_description = "Clear the Search"
    bl_options = {'REGISTER', 'INTERNAL'}

    next_mode: StringProperty()

    def execute(self, context):
        if fetcher.searching:
            return {'FINISHED'}
        print("Changed Mode to " + str(fetcher.thangs_ui_mode))
        # If adding a new plant, start off with the defaults
        if fetcher.thangs_ui_mode == 'SEARCH':
            self.next_mode == 'VIEW'
        else:
            self.next_mode == 'SEARCH'
        fetcher.thangs_ui_mode = self.next_mode

        context.area.tag_redraw()
        return {'FINISHED'}


class THANGS_PT_model_display(bpy.types.Panel):
    bl_label = "Thangs Model Search"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Thangs Search"

    def next_mode(self, op):
        # modes: ADD, EDIT, SELECT, SELECT_ADD, VIEW
        ops = ['SEARCH', 'VIEW']
        m = fetcher.thangs_ui_mode
        nm = m

        if op not in ops:
            return nm

        if m == 'SEARCH':
            nm = 'VIEW'
        elif m == 'VIEW':
            nm = 'SEARCH'
            if op == 'CANCEL':
                nm = 'VIEW'
        return nm

    def drawView(self, context):
        global pcollModel

        wm = context.window_manager

        layout = self.layout

        if fetcher.searching == True:
            layout.active = False
            SearchingLayout = self.layout
            SearchingRow = SearchingLayout.row(align=True)
            SearchingRow.label(
                text="Searching...")

        if fetcher.totalModels != 0:
            if fetcher.searching == False:
                row = layout.row()
                if fetcher.totalModels < 100:
                    row.label(text="Found " +
                              str(fetcher.totalModels)+" results for")
                elif fetcher.totalModels > 100 and fetcher.totalModels < 1000:
                    row.label(text="Found 100+ results for")
                else:
                    row.label(text="Found 1000+ results for")
                row.scale_x = .2
                row.ui_units_x = .1
                row.separator(factor=4)
                row.operator(
                    "link.thangs", icon_value=icons_dict["ThangsT"].icon_id)

                row = layout.row()
                row.label(
                    text="“"+bpy.context.scene.thangs_model_search+"” on Thangs")

                row = layout.row()
                p = row.operator("thangs.search_invoke", icon='CANCEL')
                p.next_mode = self.next_mode('SEARCH')

                grid = layout.grid_flow(
                    columns=1, even_columns=True, even_rows=True)
                z = 0
                for model in fetcher.pcoll.Model:

                    cell = grid.column().box()

                    if fetcher.length[z] > 1:
                        cell.template_icon_view(
                            wm, "ModelView{}".format((z+1)), scale=7, scale_popup=7, show_labels=True)
                    else:
                        cell.template_icon(
                            icon_value=fetcher.thumbnailNumbers[z], scale=7)

                    col = cell.box().column(align=True)
                    row = col.row()
                    row.label(text="{}".format(model[2]), icon='USER')
                    # row = col.row()
                    # row.label(text="{}".format(model[3]), icon='TEXT')
                    row = col.row()
                    row.label(text="{}".format(model[4]), icon='FILEBROWSER')

                    modelURL = fetcher.modelInfo[z][1]

                    if z == 0:
                        cell.operator('wm.url_pop1', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 1:
                        cell.operator('wm.url_pop2', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 2:
                        cell.operator('wm.url_pop3', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 3:
                        cell.operator('wm.url_pop4', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 4:
                        cell.operator('wm.url_pop5', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 5:
                        cell.operator('wm.url_pop6', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 6:
                        cell.operator('wm.url_pop7', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    elif z == 7:
                        cell.operator('wm.url_pop8', text="%s" % model[0]).url = modelURL + \
                            "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"

                    z = z + 1

                row = layout.row()
                row.ui_units_y = .9
                row.scale_y = .8
                row.ui_units_x = 1
                row.scale_x = 1

                column1 = row.column(align=True)
                if fetcher.PageNumber == 1:
                    column1.active = False

                column1.scale_x = 1
                column1.ui_units_y = .5
                column1.ui_units_x = 5
                column1.scale_y = 1.2

                column2 = row.column(align=True)
                if fetcher.PageNumber == 1:
                    column2.active = False
                column2.scale_x = 1
                column2.ui_units_y = .1
                column2.ui_units_x = 5
                column2.scale_y = 1.2

                column3 = row.column(align=True)
                column3.scale_x = 1
                column3.ui_units_y = .1
                column3.ui_units_x = 5
                column3.scale_y = 1.2

                column4 = row.column(align=True)
                if fetcher.PageNumber == fetcher.PageTotal:
                    column4.active = False

                column4.scale_x = 1
                column4.ui_units_y = .1
                column4.ui_units_x = 5
                column4.scale_y = 1.2

                column5 = row.column(align=True)
                if fetcher.PageNumber == fetcher.PageTotal:
                    column5.active = False

                column5.scale_x = 1
                column5.ui_units_y = .1
                column5.ui_units_x = 5
                column5.scale_y = 1.2

                column1.operator("firstpage.thangs", icon='REW')
                column2.operator("decpage.thangs", icon='PLAY_REVERSE')
                column3.label(text=""+str(fetcher.PageNumber) +
                              "/"+str(fetcher.PageTotal)+"")
                column4.operator("incpage.thangs", icon='PLAY')
                column5.operator("lastpage.thangs", icon='FF')

                row = layout.row()
                o = row.operator("thangs.search_invoke", icon='CANCEL')
                o.next_mode = self.next_mode('SEARCH')
        else:
            SearchingLayout = self.layout
            SearchingRow = SearchingLayout.row(align=True)
            if fetcher.failed == True:
                SearchingRow.label(
                    text="Unable to search for:")
                SearchingRow = layout.row()
                SearchingRow.label(
                    text="“"+bpy.context.scene.thangs_model_search+"” on Thangs")
                SearchingRow = layout.row()
                SearchingRow.label(
                    text="Please try again!")
            else:
                SearchingRow.label(
                    text="Found 0 Models for:")
                SearchingRow = layout.row()
                SearchingRow.label(
                    text="“"+bpy.context.scene.thangs_model_search+"” on Thangs")
                SearchingRow = layout.row()
                SearchingRow.label(
                    text="Please search for something else!")
            row = layout.row()
            o = row.operator("thangs.search_invoke", icon='CANCEL')
            o.next_mode = self.next_mode('SEARCH')

    def drawSearch(self, context):
        layout = self.layout

        wm = context.window_manager

        col = layout.column(align=True)

        if fetcher.searching:
            col.enabled = False
            SearchingRow = layout.row(align=True)
            SearchingRow.label(
                text="Fetching results for:")
            SearchingRow = layout.row(align=True)
            SearchingRow.label(
                text="'"+bpy.context.scene.thangs_model_search+"'")

        row = col.row()

        row.prop(context.scene, "thangs_model_search")

        row.scale_x = .18

    def draw(self, context):
        if fetcher.thangs_ui_mode == "VIEW":
            self.drawView(context)
        else:
            self.drawSearch(context)


def enum_previews_from_thangs_api1(self, context):
    global fetcher
    return fetcher.pcoll.ModelView1


def enum_previews_from_thangs_api2(self, context):
    global fetcher
    return fetcher.pcoll.ModelView2


def enum_previews_from_thangs_api3(self, context):
    global fetcher
    return fetcher.pcoll.ModelView3


def enum_previews_from_thangs_api4(self, context):
    global fetcher
    return fetcher.pcoll.ModelView4


def enum_previews_from_thangs_api5(self, context):
    global fetcher
    return fetcher.pcoll.ModelView5


def enum_previews_from_thangs_api6(self, context):
    global fetcher
    return fetcher.pcoll.ModelView6


def enum_previews_from_thangs_api7(self, context):
    global fetcher
    return fetcher.pcoll.ModelView7


def enum_previews_from_thangs_api8(self, context):
    global fetcher
    return fetcher.pcoll.ModelView8


preview_collections = fetcher.preview_collections


def startSearch(self, value):
    queryText = bpy.context.scene.thangs_model_search
    fetcher.search(query=queryText)


def heartbeat_timer():
    log.warning('sending thangs heartbeat')
    amplitude.send_amplitude_event("heartbeat", event_properties={'device_os': str(
        fetcher.devideOS), 'device_ver': str(fetcher.deviceVer), 'source': "blender"})
    return 30


def register():
    global fetcher
    from bpy.types import WindowManager
    from bpy.props import (
        StringProperty,
        EnumProperty,
        IntProperty,
        PointerProperty,
    )
    import bpy.utils.previews

    # Added
    WindowManager.Model_page = IntProperty(
        name="Current Page",
        default=0
    )

    WindowManager.Model_dir = StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default=""
    )

    WindowManager.Model = EnumProperty(
        name="",
        description="Click to view all results",
        items=fetcher.enumItems,
    )

    WindowManager.ModelView1 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api1,
    )

    WindowManager.ModelView2 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api2,
    )

    WindowManager.ModelView3 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api3,
    )

    WindowManager.ModelView4 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api4,
    )

    WindowManager.ModelView5 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api5,
    )

    WindowManager.ModelView6 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api6,
    )

    WindowManager.ModelView7 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api7,
    )

    WindowManager.ModelView8 = EnumProperty(
        name="",
        description="Click to view all results",
        items=enum_previews_from_thangs_api8,
    )

    fetcher.pcoll = bpy.utils.previews.new()
    fetcher.icons_dict = bpy.utils.previews.new()
    fetcher.pcoll.Model_dir = ""
    fetcher.pcoll.Model = ()
    # Added
    fetcher.pcoll.Model_page = 1

    fetcher.preview_collections["main"] = fetcher.pcoll
    icon_collections["main"] = icons_dict

    bpy.utils.register_class(THANGS_PT_model_display)
    bpy.utils.register_class(THANGS_OT_search_invoke)
    bpy.utils.register_class(SearchButton)
    bpy.utils.register_class(IncPageChange)
    bpy.utils.register_class(DecPageChange)
    bpy.utils.register_class(ThangsLink)
    bpy.utils.register_class(LastPageChange)
    bpy.utils.register_class(FirstPageChange)
    bpy.utils.register_class(DemoPreferences)
    bpy.utils.register_class(WM_OT_url_pop1)
    bpy.utils.register_class(WM_OT_url_pop2)
    bpy.utils.register_class(WM_OT_url_pop3)
    bpy.utils.register_class(WM_OT_url_pop4)
    bpy.utils.register_class(WM_OT_url_pop5)
    bpy.utils.register_class(WM_OT_url_pop6)
    bpy.utils.register_class(WM_OT_url_pop7)
    bpy.utils.register_class(WM_OT_url_pop8)

    bpy.types.Scene.thangs_model_search = bpy.props.StringProperty(
        name="",
        description="Search by text or 'Exact Phrase'",
        default="Search",
        update=startSearch
    )

    amplitude.deviceId = socket.gethostname().split(".")[0]
    fetcher.devideOS = platform.system()
    fetcher.deviceVer = platform.release()


    addon_updater_ops.register(bl_info)

    bpy.app.timers.register(heartbeat_timer)

    print("Finished Register")


def unregister():
    from bpy.types import WindowManager

    del WindowManager.Model
    bpy.app.timers.unregister(heartbeat_timer)

    for pcoll in fetcher.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    fetcher.preview_collections.clear()
    icon_collections.clear()

    bpy.utils.unregister_class(THANGS_PT_model_display)
    bpy.utils.unregister_class(THANGS_OT_search_invoke)
    bpy.utils.unregister_class(SearchButton)
    bpy.utils.unregister_class(IncPageChange)
    bpy.utils.unregister_class(DecPageChange)
    bpy.utils.unregister_class(ThangsLink)
    bpy.utils.unregister_class(LastPageChange)
    bpy.utils.unregister_class(FirstPageChange)
    bpy.utils.unregister_class(DemoPreferences)
    bpy.utils.unregister_class(WM_OT_url_pop1)
    bpy.utils.unregister_class(WM_OT_url_pop2)
    bpy.utils.unregister_class(WM_OT_url_pop3)
    bpy.utils.unregister_class(WM_OT_url_pop4)
    bpy.utils.unregister_class(WM_OT_url_pop5)
    bpy.utils.unregister_class(WM_OT_url_pop6)
    bpy.utils.unregister_class(WM_OT_url_pop7)
    bpy.utils.unregister_class(WM_OT_url_pop8)


if __name__ == "__main__":
    register()
