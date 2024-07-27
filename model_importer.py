import bpy


class ImportResult:
    def __init__(self) -> None:
        self.failed = False
        self.importing = True
        pass


def import_model(file_extension, file_path):
    ReturnObject = ImportResult()
    try:
        if file_extension == '.fbx':
            print('FBX Import')
            bpy.ops.import_scene.fbx(filepath=file_path)
        elif file_extension == '.obj':
            print('OBJ Import')
            bpy.ops.import_scene.obj(filepath=file_path)
        elif file_extension == '.glb' or file_extension == '.gltf':
            print('GLTF/GLB Import')
            if bpy.app.version >= (3, 3, 0):
                bpy.ops.import_scene.gltf(filepath=file_path, import_pack_images=True, merge_vertices=False,
                                          import_shading='NORMALS', guess_original_bind_pose=True, bone_heuristic='TEMPERANCE')
            else:
                bpy.ops.import_scene.gltf(
                    filepath=file_path, import_pack_images=True, import_shading='NORMALS')
        elif file_extension == '.usdz':
            print('USDZ Import')
            if bpy.app.version >= (3, 2, 2):
                bpy.ops.wm.usd_import(filepath=file_path,
                                      import_cameras=True,
                                      import_curves=True,
                                      import_lights=True,
                                      import_materials=True,
                                      import_meshes=True,
                                      import_volumes=True,
                                      scale=1.0,
                                      read_mesh_uvs=True,
                                      read_mesh_colors=False,
                                      import_subdiv=False,
                                      import_instance_proxies=True,
                                      import_visible_only=True,
                                      import_guide=False,
                                      import_proxy=True,
                                      import_render=True,
                                      set_frame_range=True,
                                      relative_path=True,
                                      create_collection=False,
                                      light_intensity_scale=1.0,
                                      mtl_name_collision_mode='MAKE_UNIQUE',
                                      import_usd_preview=True,
                                      set_material_blend=True)
            else:
                bpy.ops.wm.usd_import(filepath=file_path,
                                      import_cameras=True,
                                      import_curves=True,
                                      import_lights=True,
                                      import_materials=True,
                                      import_meshes=True,
                                      import_volumes=True,
                                      scale=1.0,
                                      import_visible_only=True,
                                      set_frame_range=True,
                                      light_intensity_scale=1.0,
                                      mtl_name_collision_mode='MAKE_UNIQUE',
                                      set_material_blend=True)
        else:
            print('STL Import')
            bpy.ops.import_mesh.stl(filepath=file_path)

        ReturnObject.failed = False
        ReturnObject.importing = False
    except Exception as e:
        print(e) 
        ReturnObject.failed = True
        ReturnObject.importing = False
        pass

    return ReturnObject
