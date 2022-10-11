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
import urllib.parse
import os
import json
import threading
from .thangs_login import ThangsLogin, stop_access_grant
from .thangs_fetcher import ThangsFetcher
from .thangs_events import ThangsEvents
from . import addon_updater_ops
from .config import ThangsConfig, initialize
import socket
import platform
import logging
from .thangs_importer import ThangsApi, initialize_thangsAPI, get_thangs_api

log = logging.getLogger(__name__)

bl_info = {
    "name": "Thangs Model Search",
    "author": "Thangs",
    "version": (0, 1, 9),
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
        default=True
    )

    updater_interval_months: IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0)

    updater_interval_days: IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=0,
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
        default=10,
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


initialize(bl_info["version"])
initialize_thangsAPI(callback=on_complete_search)
fetcher = ThangsFetcher(callback=on_complete_search)
amplitude = ThangsEvents()
thangs_config = ThangsConfig()
thangs_login = ThangsLogin()
thangs_api = get_thangs_api()

ButtonSearch = "Search"
# Added
PageNumber = fetcher.PageNumber
#Results = fetcher.Results

pcoll = fetcher.pcoll

PageTotal = fetcher.PageTotal
fetcher.thangs_ui_mode = 'SEARCH'

modelDropdownIndex = 0
enumHolder0 = []
enumHolder1 = []
enumHolder2 = []
enumHolder3 = []
enumHolder4 = []
enumHolder5 = []
enumHolder6 = []
enumHolder7 = []


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

class SearchBySelect(bpy.types.Operator):
    """Search by Object Selection"""
    bl_idname = "search.selection"
    bl_label = "Search By Selection"

    def execute(self, context):
        fetcher.selectionSearch(context)
        return {'FINISHED'}

def Model_Event(position):

    scope = fetcher.modelInfo[position][6]
    event_name = 'Thangs Model Link' if scope == 'thangs' else 'External Model Link'

    amplitude.send_amplitude_event(event_name, event_properties={
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

class ImportModelOperator(Operator):
    """Import Model into Blender"""
    bl_idname = "wm.import_model"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model to import",
    )
    modelIndex: IntProperty(
        name="Index",
        description="The index of the model to import"
    )
    # modelID: StringProperty(
    #     name="ModelID",
    #     description="The current model ID",
    #     default="ec0dcfff-6165-4146-96ac-6a01426c9659"
    # )

    def import_model(self):
        global thangs_api
        global fetcher
        print("Starting Download")
        thangs_api.handle_download(self.modelIndex)

    def execute(self, _context):
        print("Starting Import")
        import webbrowser
        print("Starting Login")

        # __location__ = os.path.realpath(
        #     os.path.join(os.getcwd(), os.path.dirname(__file__)))
        
        #bearer_DIR = os.path.join(__location__, 'bearer.json')
        if not os.path.exists('bearer.json'):
            print("Creating Bearer.json")
            f = open("bearer.json", "x")
        
        # check if size of file is 0
        if os.stat('bearer.json').st_size == 0:
            print("Json was empty")
            thangs_login.startLoginFromBrowser()
            print("Waiting on Login")
            thangs_login.token_available.wait()
            bearer = {
                'Bearer': str(thangs_login.token["TOKEN"]),
            }
            with open('bearer.json', 'w') as json_file:
                json.dump(bearer, json_file)
        
        f = open('bearer.json')
        data = json.load(f)
        fetcher.bearer = data["Bearer"]
        thangs_api.bearer = data["Bearer"]
        print(fetcher.bearer)
        print(thangs_api.bearer)

        import_thread = threading.Thread(
            target=self.import_model).start()
        print("Import Thread Returned")
        #webbrowser.open(self.url)
        Model_Event(self.modelIndex)
        return {'FINISHED'}


class BrowseToLicenseOperator(Operator):
    """Open model license in browser"""
    bl_idname = "wm.browse_to_license"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="License to open",
    )
    modelIndex: IntProperty(
        name="Index",
        description="The index of the model license to open"
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(self.modelIndex)
        return {'FINISHED'}


class BrowseToCreatorOperator(Operator):
    """Open creator's profile in browser"""
    bl_idname = "wm.browse_to_creator"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Creator profile to open",
    )
    modelIndex: IntProperty(
        name="Index",
        description="The index of the model creator to open"
    )

    def execute(self, _context):
        import webbrowser
        webbrowser.open(self.url)
        Model_Event(self.modelIndex)
        return {'FINISHED'}


class DropdownProperties(bpy.types.PropertyGroup):

    # def item_callback0(self, context=None):
    #     global modelDropdownIndex
    #     global enumHolder0
    #     if modelDropdownIndex == 0:
    #         enumHolder0 = fetcher.enumModelTotal[0]
    #         print(enumHolder0)
    #         return enumHolder0
    #     if modelDropdownIndex == 1:
    #         enumHolder0 = fetcher.enumModelTotal[1]
    #         print(enumHolder0)
    #         return enumHolder0

    def item_callback0(self, context=None):
        global modelDropdownIndex
        global enumHolder0
        enumHolder0 = fetcher.enumModelTotal[0]
        return enumHolder0

    def item_callback1(self, context=None):
        global modelDropdownIndex
        global enumHolder1
        enumHolder1 = fetcher.enumModelTotal[1]
        return enumHolder1

    def item_callback2(self, context=None):
        global modelDropdownIndex
        global enumHolder2
        enumHolder2 = fetcher.enumModelTotal[2]
        return enumHolder2

    def item_callback3(self, context=None):
        global modelDropdownIndex
        global enumHolder3
        enumHolder3 = fetcher.enumModelTotal[3]
        return enumHolder3

    def item_callback4(self, context=None):
        global modelDropdownIndex
        global enumHolder4
        enumHolder4 = fetcher.enumModelTotal[4]
        return enumHolder4

    def item_callback5(self, context=None):
        global modelDropdownIndex
        global enumHolder5
        enumHolder5 = fetcher.enumModelTotal[5]
        return enumHolder5

    def item_callback6(self, context=None):
        global modelDropdownIndex
        global enumHolder6
        enumHolder6 = fetcher.enumModelTotal[6]
        return enumHolder6

    def item_callback7(self, context=None):
        global modelDropdownIndex
        global enumHolder7
        enumHolder7 = fetcher.enumModelTotal[7]
        return enumHolder7

    def item_set0(self, context):
        global fetcher
        for item in fetcher.enumModels1:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts0:
                fetcher.result1 = item[3]
                thangs_api.model0 = bpy.context.scene.my_tool.dropdown_Parts0
                thangs_api.modelTitle0 = item[1]
                break

    def item_set1(self, context):
        global fetcher
        for item in fetcher.enumModels2:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts1:
                fetcher.result2 = item[3]
                thangs_api.model1 = bpy.context.scene.my_tool.dropdown_Parts1
                thangs_api.modelTitle1 = item[1]
                break

    def item_set2(self, context):
        global fetcher
        for item in fetcher.enumModels3:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts2:
                fetcher.result3 = item[3]
                thangs_api.model2 = bpy.context.scene.my_tool.dropdown_Parts2
                thangs_api.modelTitle2 = item[1]
                break

    def item_set3(self, context):
        global fetcher
        for item in fetcher.enumModels4:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts3:
                fetcher.result4 = item[3]
                thangs_api.model3 = bpy.context.scene.my_tool.dropdown_Parts3
                thangs_api.modelTitle3 = item[1]
                break
    
    def item_set4(self, context):
        global fetcher
        for item in fetcher.enumModels5:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts4:
                fetcher.result5 = item[3]
                thangs_api.model4 = bpy.context.scene.my_tool.dropdown_Parts4
                thangs_api.modelTitle4 = item[1]
                break

    def item_set5(self, context):
        global fetcher
        for item in fetcher.enumModels6:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts5:
                fetcher.result6 = item[3]
                thangs_api.model5 = bpy.context.scene.my_tool.dropdown_Parts5
                thangs_api.modelTitle5 = item[1]
                break

    def item_set6(self, context):
        global fetcher
        for item in fetcher.enumModels7:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts6:
                fetcher.result7 = item[3]
                thangs_api.model6 = bpy.context.scene.my_tool.dropdown_Parts6
                thangs_api.modelTitle6 = item[1]
                break

    def item_set7(self, context):
        global fetcher
        for item in fetcher.enumModels8:
            if item[0] == bpy.context.scene.my_tool.dropdown_Parts7:
                fetcher.result8 = item[3]
                thangs_api.model7 = bpy.context.scene.my_tool.dropdown_Parts7
                thangs_api.modelTitle7 = item[1]
                break

    dropdown_Parts0: bpy.props.EnumProperty(
        items=item_callback0,
        name="Parts",
        description="Model Parts",
        update=item_set0,
    )

    dropdown_Parts1: bpy.props.EnumProperty(
        items=item_callback1,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set1,
        get=None,
        set=None
    )

    dropdown_Parts2: bpy.props.EnumProperty(
        items=item_callback2,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set2,
        get=None,
        set=None
    )

    dropdown_Parts3: bpy.props.EnumProperty(
        items=item_callback3,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set3,
        get=None,
        set=None
    )

    dropdown_Parts4: bpy.props.EnumProperty(
        items=item_callback4,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set4,
        get=None,
        set=None
    )

    dropdown_Parts5: bpy.props.EnumProperty(
        items=item_callback5,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set5,
        get=None,
        set=None
    )

    dropdown_Parts6: bpy.props.EnumProperty(
        items=item_callback6,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set6,
        get=None,
        set=None
    )

    dropdown_Parts7: bpy.props.EnumProperty(
        items=item_callback7,
        name="Parts",
        description="Model Parts",
        default=None,
        options={'ANIMATABLE'},
        update=item_set7,
        get=None,
        set=None
    )


class ThangsLink(bpy.types.Operator):
    """Click to continue on Thangs"""
    bl_idname = "link.thangs"
    #bl_label = "Search"
    bl_label = "Redirect to Thangs"

    def execute(self, context):
        amplitude.send_amplitude_event("nav to thangs", event_properties={})
        webbrowser.open("https://thangs.com/search/"+fetcher.query +
                        "?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender&fileTypes=stl%2Cgltf%2Cobj%2Cfbx%2Cglb%2Csldprt%2Cstep%2Cmtl%2Cdxf%2Cstp&scope=thangs", new=0, autoraise=True)
        return {'FINISHED'}


icon_collections = {}
icons_dict = bpy.utils.previews.new()
icon_collections["main"] = icons_dict
icons_dict = icon_collections["main"]
icons_dir = os.path.join(os.path.dirname(__file__), "icons")
icons_dict.load("ThangsT", os.path.join(icons_dir, "T.png"), 'IMAGE')
icons_dict.load("CreativeC", os.path.join(icons_dir, "CC-Thin.png"), 'IMAGE')


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
        global modelDropdownIndex

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
                modelDropdownIndex = 0
                for model in fetcher.pcoll.Model:
                    modelURL = fetcher.modelInfo[z][1]
                    cell = grid.column().box()

                    if z == 0:
                        icon = fetcher.result1
                    elif z == 1:
                        icon = fetcher.result2
                    elif z == 2:
                        icon = fetcher.result3
                    elif z == 3:
                        icon = fetcher.result4
                    elif z == 4:
                        icon = fetcher.result5
                    elif z == 5:
                        icon = fetcher.result6
                    elif z == 6:
                        icon = fetcher.result7
                    elif z == 7:
                        icon = fetcher.result8

                    cell.template_icon(
                        icon_value=icon, scale=7)

                    col = cell.box().column(align=True)
                    row = col.row()
                    row.label(text="", icon='USER')
                    props = row.operator(
                        'wm.browse_to_creator', text="%s" % model[2])
                    props.url = thangs_config.thangs_config['url'] + "designer/" + urllib.parse.quote(str(
                        model[2])) + "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    props.modelIndex = z

                    row = col.row()
                    row.label(
                        text="", icon_value=icons_dict["CreativeC"].icon_id)
                    if model[3] == "":
                        props = row.operator(
                            'wm.browse_to_license', text="{}".format("No License"))
                        props.url = ""
                        props.enabled = False
                    else:
                        props = row.operator(
                            'wm.browse_to_license', text="{}".format("See License"))
                        props.url = model[3]
                        props.modelIndex = z

                    row = col.row()
                    row.label(text="{}".format(""), icon='FILEBROWSER')

                    scene = context.scene
                    mytool = scene.my_tool
                    dropdown = row.prop(mytool, "dropdown_Parts{}".format(z))

                    # if fetcher.length[z] == 1:
                    #     dropdown.enabled = False

                    props = cell.operator(
                        'wm.import_model', text="%s" % model[0])
                    props.url = modelURL + \
                        "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                    props.modelIndex = z
                        
                    z = z + 1
                    modelDropdownIndex = modelDropdownIndex + 1

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

        #row = col.row()
        #row.operator(SearchBySelect.bl_idname, text="Search By Selection", icon='NONE')

    def draw(self, context):
        addon_updater_ops.check_for_update_background()
        if fetcher.thangs_ui_mode == "VIEW":
            self.drawView(context)
        else:
            self.drawSearch(context)
        addon_updater_ops.update_notice_box_ui(self, context)


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
    log.info('sending thangs heartbeat')
    amplitude.send_amplitude_event(
        "Thangs Blender Addon - Heartbeat", event_properties={})
    return 300


def open_timer():
    log.info('sending thangs open')
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # True: n-panel is open
                    # False: n-panel is closed
                    n_panel_is_open = space.show_region_ui

                    amplitude.send_amplitude_event(
                        "Thangs Blender Addon - Opened", event_properties={'panel_open': n_panel_is_open})
                    return 60


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
    bpy.utils.register_class(ImportModelOperator)
    bpy.utils.register_class(BrowseToLicenseOperator)
    bpy.utils.register_class(BrowseToCreatorOperator)
    bpy.utils.register_class(DropdownProperties)
    bpy.utils.register_class(SearchBySelect)
    

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(
        type=DropdownProperties)

    bpy.types.Scene.thangs_model_search = bpy.props.StringProperty(
        name="",
        description="Search by text or 'Exact Phrase'",
        default="Search",
        update=startSearch
    )

    amplitude.deviceId = socket.gethostname().split(".")[0]
    amplitude.addon_version = bl_info["version"]
    amplitude.deviceOs = platform.system()
    amplitude.deviceVer = platform.release()

    addon_updater_ops.register(bl_info)

    bpy.app.timers.register(heartbeat_timer)
    bpy.app.timers.register(open_timer)

    log.info("Finished Register")


def unregister():
    from bpy.types import WindowManager
    global thangs_login

    del WindowManager.Model
    bpy.app.timers.unregister(heartbeat_timer)
    bpy.app.timers.unregister(open_timer)

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
    bpy.utils.unregister_class(ImportModelOperator)
    bpy.utils.unregister_class(BrowseToLicenseOperator)
    bpy.utils.unregister_class(BrowseToCreatorOperator)
    bpy.utils.unregister_class(DropdownProperties)
    bpy.utils.unregister_class(SearchBySelect)

    del bpy.types.Scene.my_tool
    addon_updater_ops.unregister()

    stop_access_grant()


if __name__ == "__main__":
    register()
