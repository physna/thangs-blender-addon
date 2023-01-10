import bpy


class Return:
    def __init__(self) -> None:
        self.failed = False
        self.importing = True
        pass


ReturnObject = Return()


def VerisonImport(file_extension, file_path):
    try:
        print(bpy.app.version)
        if bpy.app.version < (2, 80, 0):
            if file_extension == '.fbx':
                print('FBX Import')
                bpy.ops.import_scene.fbx(filepath=file_path)
            elif file_extension == '.obj':
                print('OBJ Import')
                bpy.ops.import_scene.obj(filepath=file_path)
            elif file_extension == '.glb' or file_extension == '.gltf':
                print('GLTF/GLB Import')
                bpy.ops.import_scene.gltf(filepath=file_path, import_pack_images=True, merge_vertices=False,
                                          import_shading='NORMALS', guess_original_bind_pose=True, bone_heuristic='TEMPERANCE')
            elif file_extension == '.usdz':
                print('USDZ Import')
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
                print('STL Import')
                bpy.ops.import_mesh.stl(filepath=file_path)

    except:
        ReturnObject.failed = True
        ReturnObject.importing = False
        return ReturnObject
    return ReturnObject
