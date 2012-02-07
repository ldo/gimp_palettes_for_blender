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
        "version" : (0, 1, 0),
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

def ImportPalette(PaletteFileName, SceneName, DiffuseIntensity, SpecularIntensity) :
    try :
        PaletteFile = open(PaletteFileName, "r")
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
    TheScene.name = SceneName
    XOffset, YOffset = 2.2, 2.2 # nice margins assuming default mesh size of 2x2 units
    PerRow = math.ceil(math.sqrt(len(Colors)))
    Row = 0
    Col = 0
    for Color in Colors :
        bpy.ops.object.select_all(action = "DESELECT") # ensure materials get added to right objects
        bpy.ops.mesh.primitive_plane_add \
          (
            layers = (True,) + 19 * (False,),
            location = mathutils.Vector((Row * XOffset, Col * YOffset, 0.0))
          )
        Col += 1
        if Col == PerRow :
            Col = 0
            Row += 1
        #end if
        Swatch = bpy.context.selected_objects[0]
        Material = bpy.data.materials.new("%s_%s" % (Name, Color[1]))
        Swatch.data.materials.append(Material)
        Material.diffuse_intensity = DiffuseIntensity
        Material.specular_intensity = SpecularIntensity
        Material.diffuse_color = Color[0]
        Material.specular_color = Material.diffuse_color
    #end for
#end ImportPalette

class LoadPalette(bpy.types.Operator) :
    bl_idname = "material.load_gimp_palette"
    bl_label = "Load Gimp Palette"
    # bl_context = "object"
    # bl_options = set()

    # underscores not allowed in filename/filepath property attrib names!
    # filename = bpy.props.StringProperty(subtype = "FILENAME")
    filepath = bpy.props.StringProperty(subtype = "FILE_PATH")
    scene_name = bpy.props.StringProperty(name = "New Scene Name", default = "Swatches")
    diffuse_intensity = bpy.props.FloatProperty(name = "Diffuse Intensity", min = 0.0, max = 1.0, default = 1.0)
    specular_intensity = bpy.props.FloatProperty(name = "Specular Intensity", min = 0.0, max = 1.0, default = 0.0)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    #end invoke

    def execute(self, context):
        try :
            ImportPalette(self.filepath, self.scene_name, self.diffuse_intensity, self.specular_intensity)
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
