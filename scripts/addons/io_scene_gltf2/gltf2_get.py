# Copyright (c) 2017 The Khronos Group Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# Imports
#

import bpy
import os

from .gltf2_debug import *
from bgl import GL_MAP1_COLOR_4

#
# Globals
#

#
# Functions
#


def get_used_materials():
    materials = []

    for currentMaterial in bpy.data.materials:
        if currentMaterial.node_tree:
            for currentNode in currentMaterial.node_tree.nodes:
                if isinstance(currentNode, bpy.types.ShaderNodeGroup):
                    if currentNode.node_tree.name == 'glTF Metal Roughness':
                        materials.append(currentMaterial)
                    elif currentNode.node_tree.name == 'glTF Specular Glossiness':
                        materials.append(currentMaterial)
        else:
            materials.append(currentMaterial)

    return materials


def get_material_requires_texcoords(glTF, index):
    if glTF.get('materials') is None:
        return False
    
    materials = glTF['materials']
    
    if index < 0 or index >= len(materials):
        return False

    material = materials[index]
    
    # General
    
    if glTF.get('emissiveTexture') is not None:
        return True
    
    if glTF.get('normalTexture') is not None:
        return True
    
    if glTF.get('occlusionTexture') is not None:
        return True
    
    # Metal roughness
    
    if glTF.get('baseColorTexture') is not None:
        return True
    
    if glTF.get('metallicRoughnessTexture') is not None:
        return True
    
    # TODO: Specular Glossiness Material.
    
    # TODO: Common Material.

    return False


def get_material_requires_normals(glTF, index):
    if glTF.get('materials') is None:
        return False
    
    materials = glTF['materials']
    
    if index < 0 or index >= len(materials):
        return False

    material = materials[index]
    
    # General
    
    if glTF.get('normalTexture') is not None:
        return True
    
    # Metal roughness
    
    if glTF.get('baseColorTexture') is not None:
        return True
    
    if glTF.get('metallicRoughnessTexture') is not None:
        return True
    
    # TODO: Specular Glossiness Material.
    
    # TODO: Common Material.

    return False


def get_image_index(export_settings, uri):
    if export_settings['gltf_uri'] is None:
        return -1

    if uri in export_settings['gltf_uri']:
        return export_settings['gltf_uri'].index(uri)

    return -1


def get_texture_index(export_settings, glTF, name, shader_node_group):
    if shader_node_group is None:
        return -1
    
    if not isinstance(shader_node_group, bpy.types.ShaderNodeGroup):
        return -1

    if shader_node_group.inputs.get(name) is None:
        return -1
    
    if len(shader_node_group.inputs[name].links) == 0:
        return -1
    
    from_node = shader_node_group.inputs[name].links[0].from_node
    
    #

    if not isinstance(from_node, bpy.types.ShaderNodeTexImage):
        return -1

    if from_node.image is None or from_node.image.size[0] == 0 or from_node.image.size[1] == 0:
        return -1

    uri = get_uri(from_node.image.filepath)

    if export_settings['gltf_uri'] is None:
        return -1

    if glTF.get('textures') is None:
        return -1

    image_uri = export_settings['gltf_uri']        

    index = 0
    for texture in glTF['textures']:
        current_image_uri = image_uri[texture['source']]
        if current_image_uri == uri:
            return index
        
        index += 1

    return -1


def get_texcoord_index(glTF, name, shader_node_group):
    if shader_node_group is None:
        return 0
    
    if not isinstance(shader_node_group, bpy.types.ShaderNodeGroup):
        return 0

    if shader_node_group.inputs.get(name) is None:
        return 0
    
    if len(shader_node_group.inputs[name].links) == 0:
        return 0
    
    from_node = shader_node_group.inputs[name].links[0].from_node
    
    #

    if not isinstance(from_node, bpy.types.ShaderNodeTexImage):
        return 0
    
    #
    
    if len(from_node.inputs['Vector'].links) == 0:
        return 0

    input_node = from_node.inputs['Vector'].links[0].from_node

    if not isinstance(input_node, bpy.types.ShaderNodeUVMap):
        return 0
    
    if input_node.uv_map == '':
        return 0
    
    #

    # Try to gather map index.   
    for blender_mesh in bpy.data.meshes:
        texCoordIndex = blender_mesh.uv_textures.find(input_node.uv_map)
        if texCoordIndex >= 0:
            return texCoordIndex

    return 0


def get_material_index(glTF, name):
    if name is None:
        return -1

    if glTF.get('materials') is None:
        return -1

    index = 0
    for material in glTF['materials']:
        if material['name'] == name:
            return index
        
        index += 1

    return -1


def get_mesh_index(glTF, name):
    if glTF.get('meshes') is None:
        return -1

    index = 0
    for mesh in glTF['meshes']:
        if mesh['name'] == name:
            return index
        
        index += 1

    return -1


def get_skin_index(glTF, name):
    if glTF.get('skins') is None:
        return -1
    
    skeleton = get_node_index(glTF, name)

    index = 0
    for skin in glTF['skins']:
        if skin['skeleton'] == skeleton:
            return index
        
        index += 1

    return -1


def get_camera_index(glTF, name):
    if glTF.get('cameras') is None:
        return -1

    index = 0
    for camera in glTF['cameras']:
        if camera['name'] == name:
            return index
        
        index += 1

    return -1


def get_light_index(glTF, name):
    if glTF.get('extensions') is None:
        return -1
    
    extensions = glTF['extensions']
        
    if extensions.get('KHR_lights') is None:
        return -1
    
    khr_lights = extensions['KHR_lights']

    if khr_lights.get('lights') is None:
        return -1

    lights = khr_lights['lights']

    index = 0
    for light in lights:
        if light['name'] == name:
            return index
        
        index += 1

    return -1


def get_node_index(glTF, name):
    if glTF.get('nodes') is None:
        return -1

    index = 0
    for node in glTF['nodes']:
        if node['name'] == name:
            return index
        
        index += 1

    return -1


def get_scene_index(glTF, name):
    if glTF.get('scenes') is None:
        return -1

    index = 0
    for scene in glTF['scenes']:
        if scene['name'] == name:
            return index
        
        index += 1

    return -1


def get_uri(filepath):
    return os.path.splitext(bpy.path.basename(filepath))[0] + '.png'


def get_node(data_path):
    if data_path is None:
        return None

    index = data_path.find("[\"")
    if (index == -1):
        return None

    node_name = data_path[(index + 2):]

    index = node_name.find("\"")
    if (index == -1):
        return None

    return node_name[:(index)]


def get_data_path(data_path):
    index = data_path.rfind('.')
    
    if index == -1:
        return data_path
    
    return data_path[(index + 1):]


def get_scalar(default_value, init_value = 0.0):
    return_value = init_value

    if default_value is None:
        return return_value

    return_value = default_value 

    return return_value


def get_vec2(default_value, init_value = [0.0, 0.0]):
    return_value = init_value

    if default_value is None or len(default_value) < 2:
        return return_value

    index = 0
    for number in default_value:
        return_value[index] = number 

        index += 1
        if index == 2:
            return return_value

    return return_value


def get_vec3(default_value, init_value = [0.0, 0.0, 0.0]):
    return_value = init_value

    if default_value is None or len(default_value) < 3:
        return return_value

    index = 0
    for number in default_value:
        return_value[index] = number 

        index += 1
        if index == 3:
            return return_value

    return return_value


def get_vec4(default_value, init_value = [0.0, 0.0, 0.0, 1.0]):
    return_value = init_value

    if default_value is None or len(default_value) < 4:
        return return_value

    index = 0
    for number in default_value:
        return_value[index] = number 

        index += 1
        if index == 4:
            return return_value

    return return_value


def get_index(list, name):
    if list is None or name is None:
        return -1
    
    index = 0
    for element in list:
        if element.get('name') is None:
            return -1
    
        if element['name'] == name:
            return index
        
        index += 1
    
    return -1

