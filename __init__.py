# <pep8 compliant>
import bpy
from bpy.types import (PropertyGroup,
                       Operator,
                       )
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty
                       )
import bpy.utils.previews

import webbrowser
import urllib.parse
import os
import json
import socket
import platform
import logging
import threading
import addon_utils

from . import addon_updater_ops
from urllib.request import urlopen
from .thangs_login import ThangsLogin, stop_access_grant
from .thangs_fetcher import ThangsFetcher
from .thangs_events import ThangsEvents
from .config import ThangsConfig, initialize
from .thangs_importer import initialize_thangs_api, get_thangs_api#, ThangsApi

log = logging.getLogger(__name__)

bl_info = {
    "name": "Thangs Model Search",
    "author": "Thangs",
    "version": (0, 2, 0),
    "blender": (3, 2, 0),
    "location": "VIEW 3D > Tools > Thangs Search",
    "description": "Browse and download free 3D models",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/physna/thangs-blender-addon",
    "tracker_url": "https://github.com/physna/thangs-blender-addon/issues/new/choose",
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

    fp_val: StringProperty(
        name='fp_val',
        description="Api Protection Identifier",
        default="")        

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

def import_model():
    thangs_api.import_model()
    tag_redraw_areas()
    return

initialize(bl_info["version"])
initialize_thangs_api(callback=import_model)
fetcher = ThangsFetcher(callback=on_complete_search)
amplitude = ThangsEvents()
thangs_config = ThangsConfig()
thangs_login = ThangsLogin()
thangs_api = get_thangs_api()
execution_queue = thangs_api.execution_queue

ButtonSearch = "Search"
PageNumber = fetcher.PageNumber
pcoll = fetcher.pcoll
PageTotal = fetcher.PageTotal
fetcher.thangs_ui_mode = 'SEARCH'

resultsToShow = 8
enumHolders = []
for x in range(resultsToShow):
    enumHolders.append([])

def setSearch():
    global ButtonSearch
    ButtonSearch = bpy.context.scene.thangs_model_search
    return None

def LastPage():
    if fetcher.PageNumber == fetcher.PageTotal or fetcher.searching:
        return None
    else:
        fetcher.PageNumber = fetcher.PageTotal
        fetcher.search(fetcher.query)
        return None

def IncPage():
    if fetcher.searching:
        return None
    if fetcher.PageNumber < fetcher.PageTotal:
        fetcher.PageNumber = fetcher.PageNumber + 1
        fetcher.search(fetcher.query)
    return None

def DecPage():
    if fetcher.PageNumber == 1 or fetcher.searching:
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
        bearer_location = os.path.join(os.path.dirname(__file__), 'bearer.json')
        if not os.path.exists(bearer_location):
            print("Creating Bearer.json")
            f = open(bearer_location, "x")
        
        # check if size of file is 0
        if os.stat(bearer_location).st_size == 0:
            print("Json was empty")
            thangs_login.startLoginFromBrowser()
            print("Waiting on Login")
            thangs_login.token_available.wait()
            bearer = {
                'bearer': str(thangs_login.token["TOKEN"]),
            }
            with open(bearer_location, 'w') as json_file:
                json.dump(bearer, json_file)

        f = open(bearer_location)
        data = json.load(f)
        fetcher.bearer = data["bearer"]
        thangs_api.bearer = data["bearer"]

        fetcher.selectionSearch(context)
        return {'FINISHED'}

def Model_Event(position):
    model = fetcher.models[position]
    scope = model.scope
    event_name = 'Thangs Model Link' if scope == 'thangs' else 'External Model Link'
    amplitude.send_amplitude_event(event_name, event_properties={
        'path': model.attribution_url,
        'type': "text",
        'domain': model.domain,
        'scope': model.scope,
        'searchIndex': model.search_index,
        'phyndexerID': model.model_id,
        'searchMetadata': fetcher.searchMetaData,
    })
    data = {
        "modelId": model.model_id,
        "searchId": fetcher.uuid,
        "searchResultIndex": model.search_index,
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
    partIndex: IntProperty(
        name="Part Index",
        description="The index of the part to import"
    )
    license_url: StringProperty(
        name="License URL",
        description="Model License",
    )

    def login_user(self, _context, LicenseUrl, modelIndex, partIndex):
        global thangs_api
        global fetcher
        
        print("Starting Login")
        thangs_login_import = ThangsLogin()
        bearer_location = os.path.join(os.path.dirname(__file__), 'bearer.json')
        if not os.path.exists(bearer_location):
            print("Creating Bearer.json")
            f = open(bearer_location, "x")
        
        # check if size of file is 0
        try:
            print("Top of Try")
            if os.stat(bearer_location).st_size == 0:
                print("Json was empty")
                thangs_login_import.startLoginFromBrowser()
                print("Waiting on Login")
                thangs_login_import.token_available.wait()
                print("Setting Bearer")
                bearer = {
                    'bearer': str(thangs_login_import.token["TOKEN"]),
                }
                print("Dumping")
                with open(bearer_location, 'w') as json_file:
                    json.dump(bearer, json_file)
               
            print("After Dump")
            f = open(bearer_location)
            data = json.load(f)
            fetcher.bearer = data["bearer"]
            thangs_api.bearer = data["bearer"]
            f.close()
            print("Before Import")
            thangs_api.handle_download(fetcher.modelList[modelIndex].parts[partIndex], LicenseUrl,)
            Model_Event(modelIndex)
        except Exception as e:
            print("Error with Logging In:", e)
            thangs_api.importing = False
            thangs_api.searching = False
            thangs_api.failed = True
            tag_redraw_areas()
            try:
                f.close()
                os.remove(bearer_location)
            except:
                print("File couldn't be removed.")
        return

    def execute(self, _context):
        print("Starting Login and Import")
        login_thread = threading.Thread(target=self.login_user, args=(_context, self.license_url, self.modelIndex, self.partIndex)).start()
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

class BrowseToModelOperator(Operator):
    """Open model in browser"""
    bl_idname = "wm.browse_to_model"
    bl_label = ""
    bl_options = {'INTERNAL'}

    url: StringProperty(
        name="URL",
        description="Model page to open",
    )
    modelIndex: IntProperty(
        name="Index",
        description="The index of the model page to open"
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

class ThangsLink(bpy.types.Operator):
    """Click to continue on Thangs"""
    bl_idname = "link.thangs"
    bl_label = "Redirect to Thangs"

    def execute(self, context):
        amplitude.send_amplitude_event("nav to thangs", event_properties={})
        webbrowser.open(thangs_config.thangs_config["url"] + "search/" + fetcher.query +
                        "?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender", new=0, autoraise=True)
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
        # modes: SEARCH, VIEW
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
        global modelDropdownIndex
        global thangs_api

        wm = context.window_manager

        layout = self.layout

        if fetcher.searching == True:
            layout.active = False
            SearchingLayout = self.layout
            SearchingRow = SearchingLayout.row(align=True)
            SearchingRow.label(
                text="Searching...")
        
        if thangs_api.importing == True:
            layout.active = False
            ImportingLayout = self.layout
            ImportingRow = ImportingLayout.row(align=True)
            ImportingRow.label(
                text="Importing your Model...")

        if fetcher.totalModels != 0:
            if fetcher.searching == False and thangs_api.importing == False:
                row = layout.row()
                if thangs_api.import_limit == True:
                    row.label(text="The Daily Import Limit was Reached")
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
                    modelURL = model.attribution_url
                    cell = grid.column().box()

                    modelTitleRow = cell.row().label(text=str(fetcher.modelList[z].modelTitle))

                    icon = fetcher.modelList[z].parts[fetcher.modelList[z].partSelected].iconId

                    cell.template_icon(
                        icon_value=icon, scale=7)

                    col = cell.box().column(align=True)
                    row = col.row()
                    row.label(text="", icon='USER')

                    if model.owner_username == "" or model.owner_username is None:
                        row.enabled = False
                        props = row.operator(
                            'wm.browse_to_creator', text="{}".format(model.domain))
                    else:
                        props = row.operator(
                            'wm.browse_to_creator', text="%s" % model.owner_username)
                        props.url = thangs_config.thangs_config['url'] + "designer/" + urllib.parse.quote(str(
                            model.owner_username)) + "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                        props.modelIndex = z

                    row = col.row()
                    row.label(
                        text="", icon_value=icons_dict["CreativeC"].icon_id)

                    if model.license_url == None:
                        row.enabled = False
                        props = row.operator(
                            'wm.browse_to_license', text="{}".format("No License"))

                    else:
                        props = row.operator(
                            'wm.browse_to_license', text="{}".format("See License"))
                        props.url = model.license_url
                        props.modelIndex = z

                    if model.file_type == ".blend":
                        row = col.row()
                        row.label(text="{}".format(""), icon='APPEND_BLEND')
                        
                        if thangs_api.import_limit == True:
                            props = cell.operator(
                            'wm.browse_to_model', text="%s" % model.title, icon='URL')
                            props.url = modelURL + \
                                "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                            props.modelIndex = z
                        else:
                            props = cell.operator(
                                'wm.import_model', text="Import Model", icon='IMPORT')
                            props.url = modelURL + \
                                "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                            props.modelIndex = z
                            props.partIndex = fetcher.modelList[z].partSelected
                            if model.license_url is not None:
                                props.license_url = str(model.license_url)
                            else:
                                props.license_url = ""

                    else:
                        row = col.row()
                        row.label(text="{}".format(""), icon='FILEBROWSER')

                        scene = context.scene
                        mytool = scene.my_tool
                        dropdown = row.prop(mytool, "dropdown_Parts{}".format(z))

                        if thangs_api.import_limit == True:
                            props = cell.operator(
                            'wm.browse_to_model', text="%s" % model.title, icon='URL')
                            props.url = modelURL + \
                                "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                            props.modelIndex = z
                            props.partIndex = fetcher.modelList[z].partSelected
                        else:
                            props = cell.operator(
                                'wm.import_model', text="Import Model", icon='IMPORT')
                            props.url = modelURL + \
                                "/?utm_source=blender&utm_medium=referral&utm_campaign=blender_extender"
                            props.modelIndex = z
                            props.partIndex = fetcher.modelList[z].partSelected
                            if model.license_url is not None:
                                props.license_url = str(model.license_url)
                            else:
                                props.license_url = ""       
                    z = z + 1

                row = layout.row()
                row.ui_units_y = .9
                row.scale_y = .8
                row.ui_units_x = 1
                row.scale_x = 1

                column = row.column(align=True)
                column.scale_x = 1
                column.ui_units_y = .5
                column.ui_units_x = 5
                column.scale_y = 1.2

                if fetcher.PageNumber == 1:
                    column.active = False
                column.operator("firstpage.thangs", icon='REW')

                column = row.column(align=True)
                if fetcher.PageNumber == 1:
                    column.active = False
                column.operator("decpage.thangs", icon='PLAY_REVERSE')

                column = row.column(align=True)
                column.label(text=""+str(fetcher.PageNumber) +
                              "/"+str(fetcher.PageTotal)+"")

                column = row.column(align=True)
                if fetcher.PageNumber == fetcher.PageTotal:
                    column.active = False
                column.operator("incpage.thangs", icon='PLAY')

                column = row.column(align=True)
                if fetcher.PageNumber == fetcher.PageTotal:
                    column.active = False
                column.operator("lastpage.thangs", icon='FF')

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
            elif fetcher.SelectionFailed == True:
                SearchingRow.label(
                    text="Unable to search for")
                SearchingRow = layout.row()
                SearchingRow.label(
                    text="your selection on Thangs")
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


        # TODO ENABLE SEARCH BY SELECTION
        # row = col.row()
        # row.operator(SearchBySelect.bl_idname, text="Search By Selection", icon='NONE')

    def draw(self, context):
        addon_updater_ops.check_for_update_background()
        if fetcher.thangs_ui_mode == "VIEW":
            self.drawView(context)
        else:
            self.drawSearch(context)
        addon_updater_ops.update_notice_box_ui(self, context)

preview_collections = fetcher.preview_collections

def startSearch(self, value):
    queryText = bpy.context.scene.thangs_model_search
    fetcher.search(query=queryText)


def uninstall_old_version_timer():
    def is_old_addon(mod):
        name = mod.bl_info['name']
        if name == 'Thangs Model Search':
            print(mod.bl_info)
            if mod.__name__ == 'thangs-breeze' and 'RandyHucker' in json.dumps(mod.bl_info):
                return True
        return False
    existing_breeze_installation = next((mod for mod in addon_utils.modules() if is_old_addon(mod)), None)
    if existing_breeze_installation:
        print('Removing old Thangs Breeze installation')
        print(existing_breeze_installation.__name__)
        bpy.ops.preferences.addon_remove(module=existing_breeze_installation.__name__)
    return None

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

def execute_queued_functions():
    while not execution_queue.empty():
        function = execution_queue.get()
        function()
    return 1.0

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
        items=fetcher.models,
    )

    fetcher.pcoll = bpy.utils.previews.new()
    fetcher.icons_dict = bpy.utils.previews.new()
    fetcher.pcoll.Model_dir = ""
    fetcher.pcoll.Model = []
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
    bpy.utils.register_class(SearchBySelect)
    bpy.utils.register_class(BrowseToModelOperator)

    def dropdown_properties_item_set(index):
        def handler(self, context):
            global fetcher
            enum_models = getattr(fetcher.modelList[index], "parts")
            for i, item in enumerate(enum_models):
                if item.partId == getattr(bpy.context.scene.my_tool, "dropdown_Parts" + str(index)):
                    setattr(fetcher.modelList[index], "partSelected", item.index)
                    break
        return handler

    def dropdown_properties_item_callback(index):
        def handler(self, context):
            global enumHolders
            enumHolders[index].clear()
            for part in fetcher.modelList[index].parts:
                enumHolders[index].append((part.partId, part.partFileName, "", part.iconId, part.index))
            return enumHolders[index]
        return handler

    dropdown_properties_attributes = {}
    for i in range(8):
        dropdown_properties_attributes["dropdown_Parts" + str(i)] = bpy.props.EnumProperty(
            items=dropdown_properties_item_callback(i),
            name="Parts",
            description="Model Parts",
            update=dropdown_properties_item_set(i),
        )
    DropdownProperties = type(
        "DropdownProperties",
        (PropertyGroup,),
        {'__annotations__': dropdown_properties_attributes})

    bpy.utils.register_class(DropdownProperties)
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
    bpy.app.timers.register(execute_queued_functions)
    bpy.app.timers.register(uninstall_old_version_timer)

    log.info("Finished Register")


def unregister():
    from bpy.types import WindowManager
    global thangs_login

    if hasattr(WindowManager, 'Model'):
        del WindowManager.Model
    bpy.app.timers.unregister(heartbeat_timer)
    bpy.app.timers.unregister(open_timer)
    bpy.app.timers.unregister(execute_queued_functions)
    if bpy.app.timers.is_registered(uninstall_old_version_timer):
        bpy.app.timers.unregister(uninstall_old_version_timer)

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
    bpy.utils.unregister_class(SearchBySelect)
    bpy.utils.unregister_class(BrowseToModelOperator)

    if hasattr(bpy.types.Scene, 'my_tool'):
        del bpy.types.Scene.my_tool
    addon_updater_ops.unregister()

    stop_access_grant()
    urllib.request.urlcleanup()


if __name__ == "__main__":
    register()
