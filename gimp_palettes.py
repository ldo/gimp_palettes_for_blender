#+
# This add-on script for Blender 2.6 loads a set of colours from
# a Gimp .gpl file and creates a set of simple materials that use
# them, assigned to swatch objects created in a separate scene
# in the current document. From there they may be browsed and reused
# in other objects as needed.
#
# Copyright 2012 Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#-

import sys # debug
import math
import bpy
import mathutils

bl_info = \
    {
        "name" : "Gimp Palettes",
        "author" : "Lawrence D'Oliveiro <ldo@geek-central.gen.nz>",
        "version" : (0, 3, 0),
        "blender" : (2, 6, 1),
        "location" : "View3D > Add > External Materials > Load Palette...",
        "description" :
            "loads colours from a Gimp .gpl file into a set of swatch objects",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Object",
    }

class Failure(Exception) :

    def __init__(self, Msg) :
        self.Msg = Msg
    #end __init__

#end Failure

# Empty string as identifier for an enum item results in item
# appearing as disabled, which is why I use a single space instead
NoObject = " "
NoMaterial = " "

def ImportPalette(parms) :
    try :
        PaletteFile = open(parms.filepath, "r")
    except IOError as Why :
        raise Failure(str(Why))
    #end try
    if PaletteFile.readline().strip() != "GIMP Palette" :
        raise Failure("doesn't look like a GIMP palette file")
    #end if
    Name = "Untitled"
    while True :
        line = PaletteFile.readline()
        if len(line) == 0 :
            raise Failure("palette file seems to be empty")
        #end if
        line = line.rstrip("\n")
        if line.startswith("Name: ") :
            Name = line[6:].strip()
        #end if
        if line.startswith("#") :
            break
    #end while
    Colors = []
    while True :
        line = PaletteFile.readline()
        if len(line) == 0 :
            break
        if not line.startswith("#") :
            line = line.rstrip("\n")
            components = line.split("\t", 1)
            if len(components) == 1 :
                components.append("") # empty name
            #end if
            try :
                color = tuple(int(i.strip()) / 255.0 for i in components[0].split(None, 2))
            except ValueError :
                raise Failure("bad colour on line %s" % repr(line))
            #end try
            Colors.append((color, components[1]))
        #end if
    #end while
  # all successfully loaded
    bpy.ops.object.select_all(action = "DESELECT")
    bpy.ops.scene.new(type = "NEW")
    TheScene = bpy.context.scene
    TheScene.name = parms.scene_name
    if parms.base_object != NoObject and parms.base_object in bpy.data.objects :
        SwatchObject = bpy.data.objects[parms.base_object]
    else :
        SwatchObject = None
    #end if
    if SwatchObject != None :
        SwatchMaterial = bpy.data.materials[parms.base_material]
        XOffset, YOffset = tuple(x * 1.1 for x in tuple(SwatchObject.dimensions.xy))
    else :
        SwatchMaterial = None
        XOffset, YOffset = 2.2, 2.2 # nice margins assuming default mesh size of 2x2 units
    #end if
    PerRow = math.ceil(math.sqrt(len(Colors)))
    Row = 0
    Col = 0
    Layers = (True,) + 19 * (False,)
    for Color in Colors :
        bpy.ops.object.select_all(action = "DESELECT") # ensure materials get added to right objects
        Location = mathutils.Vector((Row * XOffset, Col * YOffset, 0.0))
        if SwatchObject != None :
            Swatch = SwatchObject.copy()
            Swatch.data = Swatch.data.copy() # ensure material slots are not shared
            TheScene.objects.link(Swatch)
            Swatch.layers = Layers
            Swatch.location = Location
        else :
            bpy.ops.mesh.primitive_plane_add \
              (
                layers = Layers,
                location = Location
              )
            Swatch = bpy.context.selected_objects[0]
        #end if
        Col += 1
        if Col == PerRow :
            Col = 0
            Row += 1
        #end if
        MaterialName = "%s_%s" % (Name, Color[1])
        if SwatchMaterial != None :
            Material = SwatchMaterial.copy()
            for i in range(0, len(Swatch.data.materials)) :
                if Swatch.data.materials[i] == SwatchMaterial :
                    Swatch.data.materials[i] = Material
                    Swatch.active_material_index = i
                #end if
            #end for
            Material.name = MaterialName
        else :
            Material = bpy.data.materials.new(MaterialName)
            Swatch.data.materials.append(Material)
        #end if
        if parms.use_as_diffuse :
            Material.diffuse_intensity = parms.diffuse_intensity
            Material.diffuse_color = Color[0]
        #end if
        if parms.use_as_specular :
            Material.specular_intensity = parms.specular_intensity
            Material.specular_color = Color[0]
        #end if
        if parms.use_as_mirror :
            Material.raytrace_mirror.reflect_factor = parms.mirror_reflect
            Material.mirror_color = Color[0]
        #end if
        if parms.use_as_sss :
            Material.subsurface_scattering.color = Color[0]
        #end if
    #end for
#end ImportPalette

def ListObjects(self, context) :
    return \
        (
            (
                (NoObject, "<Default Simple Plane>", ""),
            )
        +
            tuple
              (
                (o.name, o.name, "")
                    for o in bpy.data.objects
                    if o.type == "MESH" and len(o.data.materials) != 0
              )
        )
#end ListObjects

def ListObjectMaterials(self, context) :
    TheObjectName = self.base_object
    if TheObjectName != NoObject and TheObjectName in bpy.data.objects :
        TheObject = bpy.data.objects[TheObjectName]
        Result = tuple \
          (
            (m.name, m.name, "") for m in TheObject.data.materials
          )
    else :
        Result = ((NoMaterial, "<Default Material>", ""),)
    #end if
    return \
        Result
#end ListObjectMaterials

def ObjectSelected(self, context) :
    context.area.tag_redraw()
#end ObjectSelected

class LoadPalette(bpy.types.Operator) :
    bl_idname = "material.load_gimp_palette"
    bl_label = "Load Gimp Palette"
    # bl_context = "object"
    # bl_options = set()

    # underscores not allowed in filename/filepath property attrib names!
    # filename = bpy.props.StringProperty(subtype = "FILENAME")
    filepath = bpy.props.StringProperty(subtype = "FILE_PATH")
    scene_name = bpy.props.StringProperty(name = "New Scene Name", default = "Swatches")
    base_object = bpy.props.EnumProperty \
      (
        items = ListObjects,
        name = "Swatch Object",
        description = "Object to duplicate to create swatches",
        update = ObjectSelected
      )
    base_material = bpy.props.EnumProperty \
      (
        items = ListObjectMaterials,
        name = "Swatch Material",
        description = "Material in swatch object to show colour",
      )
    use_as_diffuse = bpy.props.BoolProperty \
      (
        name = "Use as Diffuse",
        description = "Whether to apply as material diffuse colour",
        default = True
      )
    diffuse_intensity = bpy.props.FloatProperty \
      (
        name = "Diffuse Intensity",
        description = "material diffuse intensity, only if applying as diffuse colour",
        min = 0.0,
        max = 1.0,
        default = 0.8
      )
    use_as_specular = bpy.props.BoolProperty \
      (
        name = "Use as Specular",
        description = "Whether to apply as material specular colour",
        default = False
      )
    specular_intensity = bpy.props.FloatProperty \
      (
        name = "Specular Intensity",
        description = "material specular intensity, only if applying as specular colour",
        min = 0.0,
        max = 1.0,
        default = 0.5
      )
    use_as_mirror = bpy.props.BoolProperty \
      (
        name = "Use for Mirror",
        description = "Whether to apply as material raytrace mirror colour",
        default = False
      )
    mirror_reflect = bpy.props.FloatProperty \
      (
        name = "Mirror Reflection Factor",
        description = "Reflection factor, only if applying as raytrace mirror colour",
        min = 0.0,
        max = 1.0,
        default = 0.8
      )
    use_as_sss = bpy.props.BoolProperty \
      (
        name = "Use for Subsurface Scattering",
        description = "Whether to apply as material subsurface scattering colour",
        default = False
      )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    #end invoke

    def execute(self, context):
        try :
            ImportPalette(self)
            Status = {"FINISHED"}
        except Failure as Why :
            sys.stderr.write("Failure: %s\n" % Why.Msg) # debug
            self.report({"ERROR"}, Why.Msg)
            Status = {"CANCELLED"}
        #end try
        return Status
    #end execute

#end LoadPalette

class LoaderMenu(bpy.types.Menu) :
    bl_idname = "material.load_ext_materials"
    bl_label = "External Materials"

    def draw(self, context) :
        self.layout.operator(LoadPalette.bl_idname, text = "Load Palette...", icon = "COLOR")
    #end draw

#end LoaderMenu

def add_invoke_item(self, context) :
    self.layout.menu(LoaderMenu.bl_idname, icon = "MATERIAL")
      # note that trying to directly add item to self.layout instead of submenu
      # doesn't work: its execute method gets run instead of invoke.
#end add_invoke_item

def register() :
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_add.append(add_invoke_item)
#end register

def unregister() :
    bpy.types.INFO_MT_add.remove(add_invoke_item)
    bpy.utils.unregister_module(__name__)
#end unregister

if __name__ == "__main__" :
    register()
#end if
