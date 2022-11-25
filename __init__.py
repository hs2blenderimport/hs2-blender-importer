bl_info = {
    "name": "HS2 Import",
    "author": "name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Imports HS2",
    "warning": "",
    "doc_url": "",
    "category": "Material",
}


import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector
import os
import math


class ImportHelpers(bpy.types.Panel):
    bl_idname = "UI_PT_main_panel"
    bl_label = "Import Helpers"
    bl_category = "HS2 Importer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
        
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align = True)

        col.label(text = "Choose textures folder first!")
        col.prop(scene.properties, "textures_path", text = "")
        col.separator()
        self.addArmatureOperation(context, col, "op.assign_materials", "Assign Basic Materials")
        col.separator()
        col.operator("op.test")
        col.separator()
        col.label(text = "Hair texture name")
        col.prop(scene.properties, "hair_material_name")
        col.operator("op.create_hair_material")
        col.separator()
        col.label(text = "Clothes texture name")
        col.prop(scene.properties, "clothes_material_name")
        col.operator("op.create_clothes_material")
        col.separator()
        col.separator()
        col.label(text = "Configure Bones")
        self.addArmatureOperation(context, col, "op.configure_bones", "Configure Bones")
        col.separator()
        col.separator()
        col.label(text = "Bone name")
        col.prop(scene.properties, "bone_name", text = "")
        self.addArmatureOperation(context, col, "op.find_bones", "Find Bones")
    
    def addArmatureOperation(self, context, col, op, op_name):
        if isArmatureSelected(context):
            col.operator(op)
        else:
            assign_mat_row = col.row()
            assign_mat_row.enabled = False
            assign_mat_row.operator("op.disabled_operator", text = op_name)

        
class Adjustments(bpy.types.Panel):
    bl_idname = "UI_PT_adjustments_panel"
    bl_label = "Adjustments"
    bl_category = "HS2 Importer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align = True)

        if not isArmatureSelected(context):
            col.label(text = "Select the armature for your model to enable")
            return
        
        properties = getArmature(context).armature_properties
        
        col.label(text = "Hair Color 1")
        col.prop(properties, "hair_color1")
        col.separator()
        col.separator()
        col.label(text = "Hair Color 2")
        col.prop(properties, "hair_color2")
        col.separator()
        col.separator()
        col.label(text = "Hair Shine")
        col.prop(properties, "hair_shine", slider=True)
        col.separator()
        col.separator()
        col.label(text = "Body Strength")
        col.prop(properties, "body_strength", slider=True)
        col.separator()
        col.separator()
        col.label(text = "Body Shine")
        col.prop(properties, "body_shine", slider=True)
        col.separator()
        col.separator()
        col.label(text = "Eyes")
        col.prop(properties, "eye_shape")
        col.label(text = "Eyes Open")
        col.prop(properties, "eye_open", slider=True)
        col.label(text = "Eyes Color")
        col.prop(properties, "eye_color")
        col.label(text = "Eyes Color Type")
        col.prop(properties, "eye_color_type")
        col.separator()
        col.separator()
        col.label(text = "Mouth")
        col.prop(properties, "mouth_shape")
        col.label(text = "Mouth Open")
        col.prop(properties, "mouth_open", slider=True)
        col.separator()
        col.separator()
        col.label(text = "Eyebrows")
        col.prop(properties, "eyebrow_shape")
        col.label(text = "Eyebrows Amount")
        col.prop(properties, "eyebrows_amount", slider=True)

class DisabledOperator(bpy.types.Operator):
    bl_idname = "op.disabled_operator"
    bl_label = "Disabled"
    bl_description = "This action is disabled. Select your armature with your model to enable"
        
    def execute(self, context):         
        return {"FINISHED"}
    
class ArmatureProperties(bpy.types.PropertyGroup):    
    def update_hair_color(self, context):
        armature = getArmature(context)
        for object in getChildObjectsOfArmature(context):
            for material in object.material_slots:
                if "hair" not in material.name:
                    continue
                
                nodes = material.material.node_tree.nodes
                key = [node_key for node_key in nodes.keys() if "ColorRamp" in node_key][0]
                color_ramp = material.material.node_tree.nodes[key]
                    
                hair_color1 = armature.armature_properties.hair_color1
                color_ramp.color_ramp.elements[0].color = (
                    hair_color1[0], 
                    hair_color1[1], 
                    hair_color1[2], 
                    1
                )
                hair_color2 = armature.armature_properties.hair_color2
                color_ramp.color_ramp.elements[1].color = (
                    hair_color2[0],
                    hair_color2[1],
                    hair_color2[2],
                    1
                )
        
    
    hair_color1 : bpy.props.FloatVectorProperty(
        name = "",
        subtype = "COLOR",
        default = (1.0,1.0,1.0),
        size = 3,
        min = 0,
        max = 1,
        update = update_hair_color
    )
    
    hair_color2 : bpy.props.FloatVectorProperty(
        name = "",
        subtype = "COLOR",
        default = (1.0,1.0,1.0),
        size = 3,
        min = 0,
        max = 1,
        update = update_hair_color
    )
    
    def update_hair_shine(self, context):
        armature = getArmature(context)
        for object in getChildObjectsOfArmature(context):
            for material in object.material_slots:
                if "hair" not in material.name:
                    continue
                
                try:
                    nodes = material.material.node_tree.nodes
                    key = [node_key for node_key in nodes.keys() if "Principled BSDF" in node_key][0]
                    shader = material.material.node_tree.nodes[key]
                    shader.inputs[7].default_value = armature.armature_properties.hair_shine / 100
                    
                except:
                    raise Exception(material.material.node_tree.nodes.keys())
    
    hair_shine : bpy.props.FloatProperty(
        name = "",
        min = 0,
        max = 100,
        default = 5,
        update = update_hair_shine
    )
    
    def update_body_strength(self, context):
        armature = getArmature(context)
        material = getObjectWithPrefix(context, "o_body_cf").active_material
        bump_map = getNodeFromImageTexture(material, "BumpMap2", "Normal Map")
        bump_map.inputs[0].default_value = armature.armature_properties.body_strength / 300
    
    body_strength : bpy.props.FloatProperty(
        name = "",
        min = 0,
        max = 300,
        default = 100,
        update = update_body_strength
    )
    
    def update_body_shine(self, context):
        armature = getArmature(context)      
        for object_name in ["o_body_cf", "o_head"]:
            material = getObjectWithPrefix(context, object_name).active_material
            invert = getNodeFromImageTexture(material, "OcclusionMap", "Invert")
            invert.inputs[0].default_value = 0.5 + armature.armature_properties.body_shine / 200
    
    body_shine : bpy.props.FloatProperty(
        name = "",
        min = 0,
        max = 100,
        default = 100,
        update = update_body_shine
    )
    
    def eye_mapping(self):
        return {
            "normal": {
                "name": "Normal",
                "close_shape": "close"
            },
            "warai": {
                "name": "Smile",
                "close_shape": "warai_cl",
            },
            "damage": {
                "name": "Wince closed",
                "close_shape": None
            },
            "damage_R": {
                "name": "Wince R",
                "close_shape": "damage",
            },
            "damage_L": {
                "name": "Wince L",
                "close_shape": "damage",
            },
            "odoroki": {
                "name": "Surprise",
                "close_shape": "close",
            },
            "wink_R": {
                "name": "Wink R",
                "close_shape": "wink_cl",
            },
            "wink_L": {
                "name": "Wink L",
                "close_shape": "wink_cl",
            },
            "wink_half": {
                "name": "Wink half",
                "close_shape": "wink_cl",
            },
            "ikari": {
                "name": "Mad",
                "close_shape": "ikari_cl",
            },
        }
    
    def eye_item_callback(self, context):
        try:
            return [(key, self.eye_mapping()[key]["name"], "") for key in self.eye_mapping().keys()]
        except Exception as e:
            return [("error", "error", "")]
    
    def update_eyes(self, context):
        armature = getArmature(context)     
        head = getObjectWithPrefix(context, "o_head")
        lashes = getObjectWithPrefix(context, "o_eyelashes")
        shape_keys = head.data.shape_keys.key_blocks
        eye_shape_keys = [key for key in shape_keys if "head.e" in key.name]
        lash_shape_keys = lashes.data.shape_keys.key_blocks.values()
        
        eye_shape = armature.armature_properties.eye_shape
        close_shape = self.eye_mapping()[eye_shape]["close_shape"]
        
        for shape_key in eye_shape_keys + lash_shape_keys:
            if shape_key.name.endswith(eye_shape):
                if close_shape == None:
                    shape_key.value = 1
                else:
                    shape_key.value = armature.armature_properties.eye_open / 100
            
            elif close_shape != None and shape_key.name.endswith(close_shape):
                shape_key.value = 1 - (armature.armature_properties.eye_open / 100)
            
            else:
                shape_key.value = 0
        
    
    eye_shape : bpy.props.EnumProperty(
        name = "",
        items = eye_item_callback,
        update = update_eyes
    )
    
    eye_open : bpy.props.FloatProperty(
        name = "",
        min = 0,
        max = 100,
        default = 100,
        update = update_eyes,
    )
    
    def update_eye_color(self, context):
        armature = getArmature(context)
        
        for side in ["L", "R"]:
            material = getObjectWithPrefix(context, "o_eyebase_L").active_material
            eye_color = getNodeFromImageTexture(material, "Texture2", "Eye Color")
            input_eye_color = armature.armature_properties.eye_color
            eye_color.inputs[2].default_value = (
                input_eye_color[0],
                input_eye_color[1],
                input_eye_color[2],
                1
            )
    
    eye_color : bpy.props.FloatVectorProperty(
        name = "",
        subtype = "COLOR",
        default = (0.665388, 0.913099, 1.0),
        size = 3,
        min = 0,
        max = 1,
        update = update_eye_color
    )
    
    def update_eye_color_type(self, context):
        armature = getArmature(context)
        
        material = getObjectWithPrefix(context, "o_eyebase_L").active_material
        separate_rgb = getNodeFromImageTexture(material, "Texture2", "Separate RGB")
        eye_color_mix = getNodeFromImageTexture(material, "Texture2", "Eye Color")
        eye_color_type = armature.armature_properties.eye_color_type
        removeNodeLink(material, eye_color_mix.inputs[1], separate_rgb)
        material.node_tree.links.new(
            separate_rgb.outputs[0] if eye_color_type == "type_1" else separate_rgb.outputs[1],
            eye_color_mix.inputs[1]
        )
    
    eye_color_type : bpy.props.EnumProperty(
        name = "",
        items = [("type_1", "Type 1", ""), ("type_2", "Type 2", "")],
        description = "Switches which values to use for the eye color shading",
        update = update_eye_color_type
    )   
    
    def mouth_mapping(self):
        return {
            "normal": {
                "name": "Normal",
                "open_shape": "open1",
                "tongue_default_shape": None,
                "tongue_open_shape": "open1",
                "teeth_default_shape": None,
                "teeth_open_shape": "open1"
            },
            "warai1": {
                "name": "Smile",
                "open_shape": "warai1_op",
                "tongue_open_shape": "open0",
                "tongue_default_shape": None,
                "teeth_default_shape": None,
                "teeth_open_shape": "open0"
            },
            "warai2": {
                "name": "Smile Teeth",
                "open_shape": "warai2_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open1",
                "teeth_default_shape": None,
                "teeth_open_shape": "open1"
            },
            "kanasimi": {
                "name": "Sad",
                "open_shape": "kanasimi_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open0",
                "teeth_default_shape": None,
                "teeth_open_shape": "open1"
            },
            "ikari": {
                "name": "Mad",
                "open_shape": "ikari_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open0",
                "teeth_default_shape": None,
                "teeth_open_shape": "open0"
            },
            "fukure": {
                "name": "Puff",
                "open_shape": "fukure_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open1",
                "teeth_default_shape": None,
                "teeth_open_shape": "open1"
            },
            "damage": {
                "name": "Wince",
                "open_shape": "damage_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open1",
                "teeth_default_shape": None,
                "teeth_open_shape": "open1"
            },
            "rightup": {
                "name": "Smirk R",
                "open_shape": "rightup_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open0",
                "teeth_default_shape": None,
                "teeth_open_shape": "open0"
            },
            "leftup": {
                "name": "Smirk L",
                "open_shape": "leftup_op",
                "tongue_default_shape": None,
                "tongue_open_shape": "open0",
                "teeth_default_shape": None,
                "teeth_open_shape": "open0"
            },
            "tehepero": {
                "name": "Blep",
                "open_shape": None,
                "tongue_default_shape": "tehepero",
                "tongue_open_shape": None,
                "teeth_default_shape": "open0",
                "teeth_open_shape": None
            },
            "open1": {
                "name": "Open",
                "open_shape": None,
                "tongue_default_shape": "open1",
                "tongue_open_shape": None,
                "teeth_default_shape": "open1",
                "teeth_open_shape": None
            },
            "open2": {
                "name": "Wide open",
                "open_shape": None,
                "tongue_default_shape": "open2",
                "tongue_open_shape": None,
                "teeth_default_shape": "open2",
                "teeth_open_shape": None
            },
            "kiss": {
                "name": "Kiss",
                "open_shape": "kiss_op",
                "tongue_default_shape": "open0",
                "tongue_open_shape": "open1",
                "teeth_default_shape": "open0",
                "teeth_open_shape": "open1"
            },
            "fera": {
                "name": "Blow open",
                "open_shape": None,
                "tongue_default_shape": "fera",
                "tongue_open_shape": None,
                "teeth_default_shape": "fera",
                "teeth_open_shape": None
            },
            "sitadasi1": {
                "name": "Tongue",
                "open_shape": None,
                "tongue_default_shape": "sitadasi1",
                "tongue_open_shape": None,
                "teeth_default_shape": "sitadasi1",
                "teeth_open_shape": None
            },
            "sitadasi2": {
                "name": "Tongue small",
                "open_shape": None,
                "tongue_default_shape": "sitadasi2",
                "tongue_open_shape": None,
                "teeth_default_shape": "sitadasi2",
                "teeth_open_shape": None
            },
            "sitadasi3": {
                "name": "Tongue bite",
                "open_shape": None,
                "tongue_default_shape": "sitadasi3",
                "tongue_open_shape": None,
                "teeth_default_shape": "sitadasi3",
                "teeth_open_shape": None
            },
            "ahe1": {
                "name": "Ahegao",
                "open_shape": None,
                "tongue_default_shape": "ahe1",
                "tongue_open_shape": None,
                "teeth_default_shape": "ahe1",
                "teeth_open_shape": None
            },
            "ahe2": {
                "name": "Ahegao Wide",
                "open_shape": None,
                "tongue_default_shape": "ahe2",
                "tongue_open_shape": None,
                "teeth_default_shape": "ahe1",
                "teeth_open_shape": None
            },
            "_a": {
                "name": "Open small",
                "open_shape": None,
                "tongue_default_shape": "open0",
                "tongue_open_shape": None,
                "teeth_default_shape": "open0",
                "teeth_open_shape": None
            },
            "_i": {
                "name": "Bite",
                "open_shape": None,
                "tongue_default_shape": "open0",
                "tongue_open_shape": None,
                "teeth_default_shape": "open0",
                "teeth_open_shape": None
            },
            "_u": {
                "name": "Lip purse",
                "open_shape": None,
                "tongue_default_shape": "open0",
                "tongue_open_shape": None,
                "teeth_default_shape": "open0",
                "teeth_open_shape": None
            },
            "_e": {
                "name": "Open with teeth",
                "open_shape": None,
                "tongue_default_shape": "open0",
                "tongue_open_shape": None,
                "teeth_default_shape": "open0",
                "teeth_open_shape": None
            },
            "_o": {
                "name": "Kiss 2",
                "open_shape": None,
                "tongue_default_shape": "open0",
                "tongue_open_shape": None,
                "teeth_default_shape": "open0",
                "teeth_open_shape": None
            },
        }
    
    def mouth_item_callback(self, context):
        try:
            return [(key, self.mouth_mapping()[key]["name"], "") for key in self.mouth_mapping().keys()]
        except Exception as e:
            return [("error", "error", "")]
    
    def update_mouth(self, context):
        armature = getArmature(context)  
        head = getObjectWithPrefix(context, "o_head")
        tongue = getObjectWithPrefix(context, "o_tang")
        teeth = getObjectWithPrefix(context, "o_tooth")
        shape_keys = head.data.shape_keys.key_blocks
        mouth_shape_keys = [key for key in shape_keys if "head.k" in key.name]
        tongue_shape_keys = tongue.data.shape_keys.key_blocks.values()
        teeth_shape_keys = teeth.data.shape_keys.key_blocks.values()
        
        mouth_shape = armature.armature_properties.mouth_shape
        mouth_mapping = self.mouth_mapping()[mouth_shape]
        mouth_open_shape = mouth_mapping["open_shape"]
        
        tongue_shape = mouth_mapping["tongue_default_shape"]
        tongue_open_shape = mouth_mapping["tongue_open_shape"]
        
        teeth_shape = mouth_mapping["teeth_default_shape"]
        teeth_open_shape = mouth_mapping["teeth_open_shape"]
        
        def setShapeKeys(shape_keys, default_shape, open_shape):
            for shape_key in shape_keys:
                if default_shape != None and shape_key.name.endswith(default_shape):
                    if open_shape == None:
                        shape_key.value = 1
                    else:
                        shape_key.value = 1 - (armature.armature_properties.mouth_open / 100)
                
                elif open_shape != None and shape_key.name.endswith(open_shape):
                    shape_key.value = armature.armature_properties.mouth_open / 100
                
                else:
                    shape_key.value = 0
        
        setShapeKeys(mouth_shape_keys, mouth_shape, mouth_open_shape)
        setShapeKeys(tongue_shape_keys, tongue_shape, tongue_open_shape)
        setShapeKeys(teeth_shape_keys, teeth_shape, teeth_open_shape)
    
    mouth_shape : bpy.props.EnumProperty(
        name = "",
        items = mouth_item_callback,
        update = update_mouth
    )
    
    mouth_open : bpy.props.FloatProperty(
        name = "",
        min = 0,
        max = 100,
        default = 0,
        update = update_mouth,
    )
    
    def eyebrow_mapping(self):
        return {
            "normal": {
                "name": "Normal",
            },
            "warai1": {
                "name": "Happy"
            },
            "warai2": {
                "name": "Happy 2"
            },
            "ikari1": {
                "name": "Mad 1"
            },
            "ikari2": {
                "name": "Mad 2"
            },
            "kanasimi1": {
                "name": "Sad 1"
            },
            "kanasimi2": {
                "name": "Sad 2"
            },
            "damage": {
                "name": "Wince"
            },
            "up": {
                "name": "Raised"
            },
            "up_R": {
                "name": "Raised R"
            },
            "up_L": {
                "name": "Raised L"
            }
        }
    
    def eyebrow_item_callback(self, context):
        try:
            return [(key, self.eyebrow_mapping()[key]["name"], "") for key in self.eyebrow_mapping().keys()]
        except Exception as e:
            return [("error", "error", "")]
        
    def update_eyebrows(self, context):
        armature = getArmature(context)  
        head = getObjectWithPrefix(context, "o_head")
        shape_keys = head.data.shape_keys.key_blocks
        eyebrows_shape_keys = [key for key in shape_keys if "head.g" in key.name]
        
        eyebrow_shape = armature.armature_properties.eyebrow_shape

        for shape_key in eyebrows_shape_keys:
            if shape_key.name.endswith(eyebrow_shape):
                shape_key.value = armature.armature_properties.eyebrows_amount / 100      
            else:
                shape_key.value = 0
    
    eyebrow_shape : bpy.props.EnumProperty(
        name = "",
        items = eyebrow_item_callback,
        update = update_eyebrows
    )
    
    eyebrows_amount : bpy.props.FloatProperty(
        name = "",
        min = 0,
        max = 100,
        default = 100,
        update = update_eyebrows,
    )

class GlobalProperties(bpy.types.PropertyGroup):
    textures_path : bpy.props.StringProperty(default = "", maxlen = 4096, subtype = "DIR_PATH")
    bone_name : bpy.props.StringProperty(default = "", maxlen = 4096)
    name : bpy.props.StringProperty(default = "", maxlen = 4096)
    
    def item_callback(self, context):
        filenames = os.listdir(bpy.path.abspath(context.scene.properties.textures_path))
        
        def main_text_filter(filename):
            return "_MainTex.png" in filename
        main_text_filenames = filter(main_text_filter, filenames)
        main_text_filenames_stripped = [name.replace("_MainTex.png", "") for name in main_text_filenames]
        return [("", "", "")] + [(name, name, "") for name in main_text_filenames_stripped]
    
    hair_material_name : bpy.props.EnumProperty(
        name = "",
        items = item_callback
    )
    
    clothes_material_name : bpy.props.EnumProperty(
        name = "",
        items = item_callback
    )
    
class Test(bpy.types.Operator):
    bl_idname = "op.test"
    bl_label = "Test"
    
    def execute(self, context):
        armature = getArmature(context)
        
        material = getObjectWithPrefix(context, "o_eyebase_L").active_material
        separate_rgb = getNodeFromImageTexture(material, "Texture2", "Separate RGB")
        eye_color_mix = getNodeFromImageTexture(material, "Texture2", "Eye Color")
        eye_color_type = armature.armature_properties.eye_color_type
        removeNodeLink(material, eye_color_mix.inputs[1], separate_rgb)
        material.node_tree.links.new(
            separate_rgb.outputs[2] if eye_color_type == "type_1" else separate_rgb.outputs[1],
            eye_color_mix.inputs[1]
        )
        
        return {"FINISHED"}
    
class AssignMaterials(bpy.types.Operator):
    bl_idname = "op.assign_materials"
    bl_label = "Assign Basic Materials"
        
    def execute(self, context):
        # Body
        material = bpy.data.materials.new(name = "body")
        BodyMaterialBuilder(context, material).CreateMaterial()
        getObjectWithPrefix(context, "o_body_cf").active_material = material
        
        # Head
        material = bpy.data.materials.new(name = "head")
        HeadMaterialBuilder(context, material).CreateMaterial()
        getObjectWithPrefix(context, "o_head").active_material = material
#        
#        # Eyes
#        material = bpy.data.materials.new(name = "eyes")
#        EyeMaterialBuilder(context, material).CreateMaterial()
#        getObjectWithPrefix(context, "o_eyebase_L").active_material = material
#        getObjectWithPrefix(context, "o_eyebase_R").active_material = material
#        
#        # Eyelashes
#        material = bpy.data.materials.new(name = "eyelashes")
#        EyelashesMaterialBuilder(context, material).CreateMaterial()
#        getObjectWithPrefix(context, "o_eyelashes").active_material = material
#        
#        # Tongue
#        material = bpy.data.materials.new(name = "tongue")
#        TongueMaterialBuilder(context, material).CreateMaterial()
#        getObjectWithPrefix(context, "o_tang").active_material = material
#        
#        # Teeth
#        material = bpy.data.materials.new(name = "teeth")
#        TeethMaterialBuilder(context, material).CreateMaterial()
#        getObjectWithPrefix(context, "o_tooth").active_material = material

            
        return {"FINISHED"}
    
    
class MaterialBuilder():
    def __init__(self, context, material):
        self.context = context
        self.material = material
        self.material.use_nodes = True
        self.shader = self.material.node_tree.nodes.get("Principled BSDF")
        self.LoadTextures()

    def TextureNames(self):
        pass
    
    def LoadTextures(self):
        texture = {}
        self.node = {}

        for texture_metadata in self.TextureMetadata():
            try:
                filenames = os.listdir(bpy.path.abspath(self.context.scene.properties.textures_path))
                texture_name = texture_metadata["name"]
                texture_file_name = [
                    filename for filename in filenames if self.TextureNamePrefix() in filename and "_" + texture_name in filename
                ][0]
                texture[texture_name] = bpy.data.images.load(
                    self.context.scene.properties.textures_path + 
                    texture_file_name
                )
                texture[texture_name].colorspace_settings.name = "Raw"
                
                self.node[texture_name] = self.material.node_tree.nodes.new("ShaderNodeTexImage")
                self.node[texture_name].image = texture[texture_name]
                self.node[texture_name].location = texture_metadata["location"]
                
            except:
                continue
    
    def CreateMaterial(self):
        self.MainTexture()
        self.BumpMap()
        self.OcclussionMap()
        
    def MainTexture(self):
        pass
    
    def BumpMap(self):
        pass
    
    def OcclussionMap(self):
        pass
    
    def TextureNamePrefix(self):
        pass

class BodyMaterialBuilder(MaterialBuilder):
    def __init__(self, context, material):
        super(BodyMaterialBuilder, self).__init__(context, material)
    
    def TextureNamePrefix(self):
        return "cf_m_skin_body"
        
    def TextureMetadata(self):
        return [
            { "name": "MainTex", "location": (-2000, 1400) },
            { "name": "SubsurfaceAlbedo", "location": (-2000, 1000) },
            { "name": "OcclusionMap", "location": (-1500, 200) },
            { "name": "BumpMap", "location": (-1000, -600) },
            { "name": "BumpMap2_converted", "location": (-1000, -1000) },
            { "name": "Texture2", "location": (-2000, 600) },
        ]
        
    def MainTexture(self):
        # Main color
        try:  
            mix_main = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
            mix_main.blend_type = "MULTIPLY"
            mix_main.inputs[0].default_value = 0.5
            mix_main.location = (-1500, 1200)
              
            self.material.node_tree.links.new(self.node["MainTex"].outputs[0], mix_main.inputs[1])
            self.material.node_tree.links.new(self.node["SubsurfaceAlbedo"].outputs[0], mix_main.inputs[2])
        except:
            mix_main = self.node["MainTex"]
        
        # Nip color
        self.node["Texture2"].extension = "CLIP"
        self.node["Texture2"].image.colorspace_settings.name = "sRGB"
        
        uv_map = self.material.node_tree.nodes.new("ShaderNodeUVMap")
        uv_map.uv_map = "uv2"
        uv_map.location = (-2500, 500)
        
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-1500, 700)
        
        mix_nip = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        mix_nip.blend_type = "MULTIPLY"
        mix_nip.inputs[0].default_value = 0.5
        mix_nip.inputs[1].default_value = (.503, .202, .227, 1)
        mix_nip.location = (-1200, 850)
        
        color_ramp = self.material.node_tree.nodes.new("ShaderNodeValToRGB")
        color_ramp.color_ramp.elements.values()[0].position = .15
        color_ramp.location = (-1200, 600)
        
        mix_nip_with_main = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        mix_nip_with_main.location = (-750, 1000)
        
        self.material.node_tree.links.new(uv_map.outputs[0], self.node["Texture2"].inputs[0])
        self.material.node_tree.links.new(self.node["Texture2"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], mix_nip.inputs[2])
        self.material.node_tree.links.new(seperate_rgb.outputs[2], color_ramp.inputs[0])
        self.material.node_tree.links.new(color_ramp.outputs[0], mix_nip_with_main.inputs[0])
        self.material.node_tree.links.new(mix_main.outputs[0], mix_nip_with_main.inputs[1])
        self.material.node_tree.links.new(mix_nip.outputs[0], mix_nip_with_main.inputs[2])
        
        self.material.node_tree.links.new(mix_nip_with_main.outputs[0], self.shader.inputs[0])
        
        
    
    def BumpMap(self):
        normal_map1 = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map1.location = (-500, -600)
        normal_map2 = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map2.location = (-500, -1000)
        
        vector_math = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
        vector_math.operation = "MAXIMUM"
        vector_math.location = (-200, -800)
        
        self.material.node_tree.links.new(self.node["BumpMap"].outputs[0], normal_map1.inputs[1])
        
        try:
            self.material.node_tree.links.new(self.node["BumpMap2_converted"].outputs[0], normal_map2.inputs[1])
        
            self.material.node_tree.links.new(normal_map1.outputs[0], vector_math.inputs[0])
            self.material.node_tree.links.new(normal_map2.outputs[0], vector_math.inputs[1])
        
            self.material.node_tree.links.new(vector_math.outputs[0], self.shader.inputs[22])
        except:
            self.material.node_tree.links.new(normal_map1.outputs[0], self.shader.inputs[22])
        
    def OcclussionMap(self):
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-800, 200)
        
        invert = self.material.node_tree.nodes.new("ShaderNodeInvert")
        invert.location = (-500, 200)
        
        self.material.node_tree.links.new(self.node["OcclusionMap"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], invert.inputs[1])
        self.material.node_tree.links.new(invert.outputs[0], self.shader.inputs[9])
        
        
class HeadMaterialBuilder(MaterialBuilder):
    def TextureNamePrefix(self):
        return "cf_m_skin_head"
    
    def TextureMetadata(self):
        return [
            { "name": "MainTex", "location": (-2000, 1400) },
            { "name": "SubsurfaceAlbedo", "location": (-2000, 1000) },
            { "name": "OcclusionMap", "location": (-1500, 200) },
            { "name": "BumpMap_converted", "location": (-1000, -600) },
            { "name": "BumpMap2_converted", "location": (-1000, -1000) },
            { "name": "Texture3", "location": (-2000, 600) },
        ]
    
    def MainTexture(self):
        # Main color
        try:  
            mix_main = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
            mix_main.blend_type = "MULTIPLY"
            mix_main.inputs[0].default_value = 0.5
            mix_main.location = (-1500, 1200)
              
            self.material.node_tree.links.new(self.node["MainTex"].outputs[0], mix_main.inputs[1])
            self.material.node_tree.links.new(self.node["SubsurfaceAlbedo"].outputs[0], mix_main.inputs[2])
        except:
            mix_main = self.node["MainTex"]
        
        # Eye brow color
        self.node["Texture3"].extension = "CLIP"
        
        uv_map = self.material.node_tree.nodes.new("ShaderNodeUVMap")
        uv_map.uv_map = "uv3"
        uv_map.location = (-3000, 500)
        
        mapping = self.material.node_tree.nodes.new("ShaderNodeMapping")
        mapping.inputs[1].default_value = (0.02, -0.11, -0.25)
        mapping.inputs[2].default_value = (0, 0, -0.070511301781)
        mapping.inputs[3].default_value = (1.07, 1.72, 1)
        mapping.location = (-2500, 500)
        
        mix_with_main = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        mix_with_main.blend_type = "OVERLAY"
        mix_with_main.inputs[2].default_value = (0.020445, 0.009932, 0.006392, 1)
        mix_with_main.location = (-750, 1000)

        self.material.node_tree.links.new(uv_map.outputs[0], mapping.inputs[0]) 
        self.material.node_tree.links.new(mapping.outputs[0], self.node["Texture3"].inputs[0])
        self.material.node_tree.links.new(self.node["Texture3"].outputs[0], mix_with_main.inputs[0])
        self.material.node_tree.links.new(mix_main.outputs[0], mix_with_main.inputs[1])

        self.material.node_tree.links.new(mix_with_main.outputs[0], self.shader.inputs[0])

    def BumpMap(self):
        normal_map1 = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map1.location = (-500, -600)
        normal_map2 = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map2.location = (-500, -1000)
        
        vector_math = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
        vector_math.operation = "MAXIMUM"
        vector_math.location = (-200, -800)
        
        self.material.node_tree.links.new(self.node["BumpMap_converted"].outputs[0], normal_map1.inputs[1])
        
        try:
            self.material.node_tree.links.new(self.node["BumpMap2_converted"].outputs[0], normal_map2.inputs[1])
            
            self.material.node_tree.links.new(normal_map1.outputs[0], vector_math.inputs[0])
            self.material.node_tree.links.new(normal_map2.outputs[0], vector_math.inputs[1])
            
            self.material.node_tree.links.new(vector_math.outputs[0], self.shader.inputs[22])
        except:
            self.material.node_tree.links.new(normal_map1.outputs[0], self.shader.inputs[22])
        
    def OcclussionMap(self):
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-800, 200)
        
        invert = self.material.node_tree.nodes.new("ShaderNodeInvert")
        invert.location = (-500, 200)
        
        self.material.node_tree.links.new(self.node["OcclusionMap"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], invert.inputs[1])
        self.material.node_tree.links.new(invert.outputs[0], self.shader.inputs[9])    

class EyeMaterialBuilder(MaterialBuilder):
    def TextureNamePrefix(self):
        return "cf_m_eye"
    
    def TextureMetadata(self):
        return [
            { "name": "MainTex", "location": (-1200, 1000) },
            { "name": "Texture2", "location": (-1800, 600) },
            { "name": "Texture4", "location": (-800, 100) },
        ]
        
    def MainTexture(self):
        self.node["MainTex"].image.colorspace_settings.name = "sRGB"
        self.node["Texture2"].image.colorspace_settings.name = "sRGB"
        self.shader.inputs[9].default_value = 0
        
        overlay_with_main = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        overlay_with_main.blend_type = "OVERLAY"
        overlay_with_main.location = (-700, 800)
        overlay_with_main.name = "Eye Color Mix"
        
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-1400, 600)
        
        overlay_with_eye_color = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        overlay_with_eye_color.blend_type = "OVERLAY"
        overlay_with_eye_color.inputs[0].default_value = 1
        overlay_with_eye_color.inputs[2].default_value = (0.665388, 0.913099, 1.0, 1.0)
        overlay_with_eye_color.location = (-1000, 600)
        overlay_with_eye_color.name = "Eye Color"
        
        screen = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        screen.blend_type = "SCREEN"
        screen.inputs[0].default_value = 1
        screen.location = (-300, 300)
        
        self.material.node_tree.links.new(self.node["Texture2"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], overlay_with_eye_color.inputs[1])
        self.material.node_tree.links.new(seperate_rgb.outputs[2], overlay_with_main.inputs[0])
        self.material.node_tree.links.new(self.node["MainTex"].outputs[0], overlay_with_main.inputs[1])
        self.material.node_tree.links.new(overlay_with_eye_color.outputs[0], overlay_with_main.inputs[2])
        self.material.node_tree.links.new(overlay_with_main.outputs[0], screen.inputs[1])
        self.material.node_tree.links.new(self.node["Texture4"].outputs[0], screen.inputs[2])
        self.material.node_tree.links.new(screen.outputs[0], self.shader.inputs[0])
        
class EyelashesMaterialBuilder(MaterialBuilder):
    def TextureNamePrefix(self):
        return "c_m_eyelashes"
    
    def TextureMetadata(self):
        return [
            { "name": "MainTex", "location": (-800, 0) },
        ]
        
    def MainTexture(self):
        self.shader.inputs[0].default_value = (0.008694, 0.00407, 0.001584, 1)
        
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-400, 0)
        
        self.material.node_tree.links.new(self.node["MainTex"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], self.shader.inputs[21])
        
        self.material.shadow_method = "HASHED"
        self.material.blend_method = "HASHED"

class TongueMaterialBuilder(MaterialBuilder):
    def TextureNamePrefix(self):
        return "c_m_tang"
    
    def TextureMetadata(self):
        return [
            { "name": "MainTex", "location": (-800, 800) },
            { "name": "BumpMap_converted", "location": (-1000, -600) },
            { "name": "OcclusionMap", "location": (-1200, 200) },
        ]
        
    def MainTexture(self):
        self.material.node_tree.links.new(self.node["MainTex"].outputs[0], self.shader.inputs[0])
        
    def BumpMap(self):
        normal_map1 = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map1.location = (-500, -600)
        
        self.material.node_tree.links.new(self.node["BumpMap_converted"].outputs[0], normal_map1.inputs[1])
        self.material.node_tree.links.new(normal_map1.outputs[0], self.shader.inputs[22])
        
    def OcclussionMap(self):
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-800, 200)
        
        invert = self.material.node_tree.nodes.new("ShaderNodeInvert")
        invert.location = (-500, 200)
        
        self.material.node_tree.links.new(self.node["OcclusionMap"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], invert.inputs[1])
        self.material.node_tree.links.new(invert.outputs[0], self.shader.inputs[9])    
        
class TeethMaterialBuilder(MaterialBuilder):
    def TextureNamePrefix(self):
        return "c_m_tooth"
    
    def TextureMetadata(self):
        return [
            { "name": "MainTex", "location": (-800, 800) },
            { "name": "BumpMap_converted", "location": (-1000, -600) },
            { "name": "OcclusionMap", "location": (-1200, 200) },
        ]
        
    def MainTexture(self):
        self.material.node_tree.links.new(self.node["MainTex"].outputs[0], self.shader.inputs[0])
        
    def BumpMap(self):
        normal_map1 = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map1.location = (-500, -600)
        
        self.material.node_tree.links.new(self.node["BumpMap_converted"].outputs[0], normal_map1.inputs[1])
        self.material.node_tree.links.new(normal_map1.outputs[0], self.shader.inputs[22])
        
    def OcclussionMap(self):
        seperate_rgb = self.material.node_tree.nodes.new("ShaderNodeSeparateRGB")
        seperate_rgb.location = (-800, 200)
        
        invert = self.material.node_tree.nodes.new("ShaderNodeInvert")
        invert.location = (-500, 200)
        
        self.material.node_tree.links.new(self.node["OcclusionMap"].outputs[0], seperate_rgb.inputs[0])
        self.material.node_tree.links.new(seperate_rgb.outputs[0], invert.inputs[1])
        self.material.node_tree.links.new(invert.outputs[0], self.shader.inputs[9])    
        
class CreateHairMaterialTemplate(bpy.types.Operator):
    bl_idname = "op.create_hair_material"
    bl_label = "Create Hair Material"
        
    def execute(self, context):
        material = bpy.data.materials.new(name = context.scene.properties.hair_material_name)
        material.use_nodes = True
        material.shadow_method = "HASHED"
        material.blend_method = "HASHED"               
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs[7].default_value = 0.05
        
        self.MainTexture(material, shader, context)
        self.BumpMap(material, shader, context)
        self.OcclussionMap(material, shader, context)
        
        context.selected_objects[0].active_material = material
            
        return {"FINISHED"}
    
    def MainTexture(self, material, shader, context):
        main_texture = bpy.data.images.load(context.scene.properties.textures_path + context.scene.properties.hair_material_name + "_MainTex.png")
        main_texture.colorspace_settings.name = "Raw"
        main_image = material.node_tree.nodes.new("ShaderNodeTexImage")
        main_image.image = main_texture
        main_image.location = (-800, 500)
        
        color_ramp = material.node_tree.nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-400, 500)
        
        material.node_tree.links.new(main_image.outputs[0], color_ramp.inputs[0])
        material.node_tree.links.new(color_ramp.outputs[0], shader.inputs[0])
        material.node_tree.links.new(main_image.outputs[1], shader.inputs[21])
    
    def BumpMap(self, material, shader, context):
        bump_texture = bpy.data.images.load(context.scene.properties.textures_path + context.scene.properties.hair_material_name + "_BumpMap_converted.png")
        bump_texture.colorspace_settings.name = "Raw"
        bump_image = material.node_tree.nodes.new("ShaderNodeTexImage")
        bump_image.image = bump_texture
        bump_image.location = (-800, -400)
        
        normal_map1 = material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map1.location = (-400, -400)
        
        material.node_tree.links.new(bump_image.outputs[0], normal_map1.inputs[0])
        material.node_tree.links.new(normal_map1.outputs[0], shader.inputs[22])
        
    def OcclussionMap(self, material, shader, context):
        try:
            occlussion_texture = bpy.data.images.load(context.scene.properties.textures_path + context.scene.properties.hair_material_name + "_Occlusion.png")
            occlussion_texture.colorspace_settings.name = "Raw"
            occlussion_image = material.node_tree.nodes.new("ShaderNodeTexImage")
            occlussion_image.image = occlussion_texture
            occlussion_image.location = (-1200, 200)
             
            seperate_rgb = material.node_tree.nodes.new("ShaderNodeSeparateRGB")
            seperate_rgb.location = (-800, 200)
            
            invert = material.node_tree.nodes.new("ShaderNodeInvert")
            invert.location = (-400, 200)
            
            material.node_tree.links.new(occlussion_image.outputs[0], seperate_rgb.inputs[0])
            material.node_tree.links.new(seperate_rgb.outputs[0], invert.inputs[1])
            material.node_tree.links.new(invert.outputs[0], shader.inputs[9])    
        except:
            print("Skipping Occlusion for hair")
            

class CreateClothesMaterialTemplate(bpy.types.Operator):
    bl_idname = "op.create_clothes_material"
    bl_label = "Create Clothes Material"
        
    def execute(self, context):
        material = bpy.data.materials.new(name = context.scene.properties.clothes_material_name)
        material.use_nodes = True
        material.shadow_method = "HASHED"
        material.blend_method = "HASHED"               
        shader = material.node_tree.nodes.get("Principled BSDF")
        
        self.MainTexture(material, shader, context)
        self.BumpMap(material, shader, context)
        self.OcclussionMap(material, shader, context)
        
        context.selected_objects[0].active_material = material
            
        return {"FINISHED"}
    
    def MainTexture(self, material, shader, context):
        main_image = addImageTexture(
            context, 
            material, 
            context.scene.properties.clothes_material_name + "_MainTex.png", 
            (-1600, 500)
        )
    
        try:
            detail_mask_image = addImageTexture(
                context, 
                material, 
                context.scene.properties.clothes_material_name + "_DetailMask.png", 
                (-1600, -0),
                "sRGB"
            )
            
            detail_gloss_1_image = addImageTexture(
                context, 
                material, 
                context.scene.properties.clothes_material_name + "_DetailGlossMap.png", 
                (-1000, -300),
                "sRGB"
            )
            
            seperate_rgb = material.node_tree.nodes.new("ShaderNodeSeparateRGB")
            seperate_rgb.location = (-1300, 0)
            
            text_coord = material.node_tree.nodes.new("ShaderNodeTexCoord")
            text_coord.location = (-2000, -300)
            
            mapping1 = material.node_tree.nodes.new("ShaderNodeMapping")
            mapping1.inputs[3].default_value = (50, 50, 50)
            mapping1.location = (-1800, -300)
            
            mix1 = material.node_tree.nodes.new("ShaderNodeMixRGB")
            mix1.blend_type = "OVERLAY"
            mix1.location = (-400, 250)   
            
            material.node_tree.links.new(text_coord.outputs[2], mapping1.inputs[0])
            material.node_tree.links.new(mapping1.outputs[0], detail_gloss_1_image.inputs[0])
            material.node_tree.links.new(detail_mask_image.outputs[0], seperate_rgb.inputs[0])
            material.node_tree.links.new(seperate_rgb.outputs[0], mix1.inputs[0])
            material.node_tree.links.new(main_image.outputs[0], mix1.inputs[1])
            material.node_tree.links.new(detail_gloss_1_image.outputs[0], mix1.inputs[2])
            
            try:
                detail_gloss_2_image = addImageTexture(
                    context, 
                    material, 
                    context.scene.properties.clothes_material_name + "_DetailGlossMap2.png", 
                    (-1000, -700),
                    "sRGB"
                )
                
                mapping2 = material.node_tree.nodes.new("ShaderNodeMapping")
                mapping2.inputs[3].default_value = (50, 50, 50)
                mapping2.location = (-1800, -700)
                
                mix2 = material.node_tree.nodes.new("ShaderNodeMixRGB")
                mix2.blend_type = "OVERLAY"
                mix2.location = (-200, 550)
                
                material.node_tree.links.new(text_coord.outputs[2], mapping2.inputs[0])
                material.node_tree.links.new(mapping2.outputs[0], detail_gloss_2_image.inputs[0])
                material.node_tree.links.new(seperate_rgb.outputs[1], mix2.inputs[0])
                material.node_tree.links.new(mix1.outputs[0], mix2.inputs[1])
                material.node_tree.links.new(detail_gloss_2_image.outputs[0], mix2.inputs[2])
                material.node_tree.links.new(mix2.outputs[0], shader.inputs[0])
            except Exception as e:
                material.node_tree.links.new(mix1.outputs[0], shader.inputs[0])
                
        except Exception as e:
            material.node_tree.links.new(main_image.outputs[0], shader.inputs[0])
        
        material.node_tree.links.new(main_image.outputs[1], shader.inputs[21])
    
    def BumpMap(self, material, shader, context):
        try:
            bump_image = addImageTexture(
                context, 
                material, 
                context.scene.properties.clothes_material_name + "_BumpMap_converted.png", 
                (-800, -1000)
            )
            
            normal_map1 = material.node_tree.nodes.new("ShaderNodeNormalMap")
            normal_map1.location = (-400, -1000)
            
            material.node_tree.links.new(bump_image.outputs[0], normal_map1.inputs[1])
            material.node_tree.links.new(normal_map1.outputs[0], shader.inputs[22])
        except:
            print("Skipping Bump for clothes")
        
    def OcclussionMap(self, material, shader, context):
        pass
        
        
class ConfigureBones(bpy.types.Operator):
    bl_idname = "op.configure_bones"
    bl_label = "Configure Bones"
        
    def execute(self, context):
        assertArmatureSelected(context)
        
        current_mode = bpy.context.object.mode
        self.addAllConstraints(context)
        self.fixFingerRotation(context)
        self.addLookAtBone(context)
        bpy.ops.object.mode_set(mode=current_mode)
        
        return {"FINISHED"}
    
    def addAllConstraints(self, context):
        bpy.ops.object.mode_set(mode='POSE')
        self.addLegConstraints(context)
    
    def addConstraints(self, context, constraints):
        armature = getArmature(context)
        for constraint in constraints:
            bone = armature.pose.bones[constraint["original_bone"]]
            constraint_obj = bone.constraints.new(constraint["constraint_type"])
            constraint_obj.target = armature
            constraint_obj.subtarget = constraint["target_bone"]
            constraint_obj.influence = constraint["influence"]
            
            if constraint["constraint_type"] == "COPY_ROTATION" or constraint["constraint_type"] == "COPY_LOCATION":
                constraint_obj.owner_space = "LOCAL"
                constraint_obj.target_space = "LOCAL_OWNER_ORIENT"
                constraint_obj.use_x = constraint["use_x"]
                constraint_obj.use_y = constraint["use_y"]
                constraint_obj.use_z = constraint["use_z"]
                if constraint["use_offset"] != None:
                    constraint_obj.use_offset = constraint["use_offset"]
            
            if constraint["constraint_type"] == "TRACK_TO":
                constraint_obj.track_axis = constraint["track_axis"]
                constraint_obj.up_axis = constraint["up_axis"]
                constraint_obj.owner_space = "POSE"
                constraint_obj.target_space = "POSE"
                
    
    def addLegConstraints(self, context):
        for side in ["R", "L"]:
            leg_constraints = [{
                "original_bone": "cf_J_LegKnee_back_" + side,
                "target_bone": "leg." + side.lower(),
                "constraint_type": "COPY_ROTATION",
                "use_x": True,
                "use_y": False,
                "use_z": False,
                "influence": 1,
                "use_offset": None
            }, {
                "original_bone": "cf_J_LegKnee_dam_" + side,
                "target_bone": "leg." + side.lower(),
                "constraint_type": "COPY_ROTATION",
                "use_x": True,
                "use_y": False,
                "use_z": False,
                "influence": 0.5,
                "use_offset": None
            }, {
                "original_bone": "cf_J_SiriDam_" + side,
                "target_bone": "thigh." + side.lower(),
                "constraint_type": "COPY_ROTATION",
                "use_x": True,
                "use_y": False,
                "use_z": False,
                "influence": 0.5,
                "use_offset": None
            }, {
                "original_bone": "cf_J_LegUpDam_" + side,
                "target_bone": "thigh." + side.lower(),
                "constraint_type": "COPY_ROTATION",
                "use_x": True,
                "use_y": False,
                "use_z": True,
                "influence": 0.8,
                "use_offset": None
            }]
            self.addConstraints(context, leg_constraints)
    
    def fixFingerRotation(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bone_names = [
            "index",
            "middle",
            "ring",
            "pinky",
        ]
        armature = getArmature(context)
        bones = armature.data.edit_bones
        roll_value = math.radians(180)
        for side in ["l", "r"]:
            for bone_name in bone_names:
                bones[bone_name + "_bend_all." + side].roll = roll_value
                bones["c_" + bone_name + "2_rot." + side].roll = roll_value
                bones["c_" + bone_name + "3_rot." + side].roll = roll_value
                for num in ["1", "2", "3"]:
                    bones["c_" + bone_name + num + "." + side].roll = roll_value
            
            multiplier = 1 if side == "l" else -1
            thumb_roll_value = math.radians(270) * multiplier
            bones["thumb_bend_all." + side].roll = thumb_roll_value
            bones["c_thumb2_rot." + side].roll = thumb_roll_value
            bones["c_thumb3_rot." + side].roll = thumb_roll_value
            for num in ["1", "2", "3"]:
                bones["c_thumb" + num + "." + side].roll = thumb_roll_value
                
    def addLookAtBone(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bones = getArmature(context).data.edit_bones
        look_at_bone = bones.new("look_at")
        nose_bone = bones["cf_J_NoseBridge_s"]
        spine_bone = bones["cf_J_Spine02_s"]
        z_diff = nose_bone.head[2] - spine_bone.head[2]
        look_at_bone.head = (nose_bone.head[0], nose_bone.head[1] - z_diff, nose_bone.head[2])
        look_at_bone.tail = (nose_bone.tail[0], nose_bone.tail[1] - z_diff, nose_bone.tail[2])
        look_at_bone.layers[0] = True
        look_at_bone.roll = math.radians(90)
        
        for side in ["L", "R"]:
            look_at_eye_bone = bones.new("look_at_eye." + side.lower())
            look_bone = bones["cf_J_look_" + side]
            head_x_diff = look_bone.head[0] - nose_bone.head[0]
            tail_x_diff = look_bone.tail[0] - nose_bone.tail[0]
            look_at_eye_bone.head = (look_at_bone.head[0] + (head_x_diff * .75), look_at_bone.head[1], look_at_bone.head[2])
            look_at_eye_bone.tail = (look_at_bone.tail[0] + (tail_x_diff * .75), look_at_bone.tail[1], look_at_bone.tail[2])
            look_at_eye_bone.layers[0] = True
            look_at_eye_bone.roll = math.radians(90)
            
        bpy.ops.object.mode_set(mode='POSE')
        bones = getArmature(context).pose.bones
        
        look_at_bone = bones["look_at"]
        for side in ["L", "R"]:
            constraints = [{
                "original_bone": "look_at_eye." + side.lower(),
                "target_bone": "look_at",
                "constraint_type": "COPY_LOCATION",
                "use_x": True,
                "use_y": True,
                "use_z": True,
                "influence": 1,
                "use_offset": True
            }, {
                "original_bone": "cf_J_look_" + side,
                "target_bone": "look_at_eye." + side.lower(),
                "constraint_type": "TRACK_TO",
                "track_axis": "TRACK_Z",
                "up_axis": "UP_Y",
                "influence": 1,
            }]
            self.addConstraints(context, constraints)
        
        eye_custom_object = bpy.data.objects["cs_eye_aim"]
        look_at_custom_object = bpy.data.objects["cs_eye_aim_global"]
        
        bones["look_at"].custom_shape = look_at_custom_object
        bones["look_at"].custom_shape_scale_xyz[0] = 3
        bones["look_at"].custom_shape_scale_xyz[1] = 3
        bones["look_at"].custom_shape_scale_xyz[2] = 3
        bones["look_at_eye.l"].custom_shape = eye_custom_object
        bones["look_at_eye.r"].custom_shape = eye_custom_object
        
        bone_groups = getArmature(context).pose.bone_groups
        bones["look_at"].bone_group = bone_groups["body.x"]
        bones["look_at_eye.l"].bone_group = bone_groups["body.l"]
        bones["look_at_eye.r"].bone_group = bone_groups["body.r"]
        
class FindBones(bpy.types.Operator):
    bl_idname = "op.find_bones"
    bl_label = "Find Bones"
        
    def execute(self, context):
        context.scene.properties.bone_name     
            
        armature = getArmature(context).data
        for bone in armature.bones.items():
            names = context.scene.properties.bone_name.lower().split()
            bone[1].hide = not any([name in bone[0].lower() for name in names])

            
        return {"FINISHED"}
        
def addImageTexture(context, material, imageFilename, location, colorspace="Raw"):
    texture = bpy.data.images.load(context.scene.properties.textures_path + imageFilename)
    texture.colorspace_settings.name = colorspace
    image = material.node_tree.nodes.new("ShaderNodeTexImage")
    image.image = texture
    image.location = location
    return image
    

def getObjectWithPrefix(context, prefix):
    assertArmatureSelected(context)
    armature = context.selected_objects[0]
    
    for obj in context.editable_objects:
        if obj.parent == armature and obj.name.startswith(prefix):
            return obj
    
    raise Exception("Object not found with prefix", prefix)

def getChildObjectsOfArmature(context):
    assertArmatureSelected(context)
    armature = context.selected_objects[0]
    objects = []
    
    for obj in context.editable_objects:
        if obj.parent == armature:
            objects.append(obj)    
    
    return objects

def assertArmatureSelected(context):
    if (not isArmatureSelected(context)):
        raise Exception("No armature selected. Must select armature with your model")

def isArmatureSelected(context):
    if (len(context.selected_objects) == 0):
        return False
    if (context.selected_objects[0].type != "ARMATURE"):
        return False
    
    return True

def getArmature(context):
    assertArmatureSelected(context)
    return context.selected_objects[0]

def getNodeFromImageTexture(material, image_name, node_type):
    nodes = material.node_tree.nodes
    keys = [node_key for node_key in nodes.keys() if "Image Texture" in node_key]
    names = []
    for key in keys:
        image_texture = nodes[key]
        names.append(image_texture.image.name)
        if image_name in image_texture.image.name:
            found_node = getNodeInNodeTree(image_texture, node_type)
            if found_node == None:
                raise Exception("Did not find node with name node_type", node_type)
                
            return found_node
    
    raise Exception("Did not find image texture with image name", image_name, names)

def getNodeInNodeTree(node, node_type, depth = 0):
    if depth == 50:
        raise Exception("Potential infiinte recursion")
    
    for output in node.outputs:
        for link in output.links:
            if node_type in link.to_node.name:
                return link.to_node
            
            maybe_node = getNodeInNodeTree(link.to_node, node_type, depth + 1)
            
            if maybe_node != None:
                return maybe_node
    
    return None

def removeNodeLink(material, socket, node):
    for link in socket.links:
        if link.to_node == node or link.from_node == node:
            material.node_tree.links.remove(link)
            return
    
    raise Exception("Did not find link to remove", socket, node)
    
            
classes = [
    ImportHelpers,
    Adjustments,
    ArmatureProperties,
    GlobalProperties,
    DisabledOperator,
    AssignMaterials,
    Test,
    CreateHairMaterialTemplate,
    CreateClothesMaterialTemplate,
    ConfigureBones,
    FindBones
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Object.armature_properties = bpy.props.PointerProperty(type = ArmatureProperties)
    bpy.types.Scene.properties = bpy.props.PointerProperty(type = GlobalProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.properties

if __name__ == "__main__":
    register()
