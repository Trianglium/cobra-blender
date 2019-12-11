bl_info = {	"name": "Frontier's Cobra Engine Formats (JWE, Planet Zoo)",
			"author": "Harlequinz Ego & HENDRIX",
			"blender": (2, 79, 0),
			"location": "File > Import-Export",
			"description": "Import-Export models, skeletons and animations.",
			"warning": "",
			"wiki_url": "https://github.com/HENDRIX-ZT2/cobra-blender",
			"support": 'COMMUNITY',
			"tracker_url": "https://github.com/HENDRIX-ZT2/cobra-blender/issues/new",
			"category": "Import-Export"}
import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import bpy.utils.previews
preview_collection = bpy.utils.previews.new()
		
class ImportBani(bpy.types.Operator, ImportHelper):
	"""Import from Cobra baked animations file format (.bani)"""
	bl_idname = "import_scene.cobra_bani"
	bl_label = 'Import Bani'
	bl_options = {'UNDO'}
	filename_ext = ".bani"
	filter_glob = StringProperty(default="*.bani", options={'HIDDEN'})
	files = CollectionProperty(type=bpy.types.PropertyGroup)
	# set_fps = BoolProperty(name="Adjust FPS", description="Set the scene to 30 frames per second to conform with the BFs.", default=True)
	def execute(self, context):
		from . import import_bani
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		return import_bani.load(self, context, **keywords)

class ImportMDL2(bpy.types.Operator, ImportHelper):
	"""Import from MDL2 file format (.MDL2)"""
	bl_idname = "import_scene.cobra_mdl2"
	bl_label = 'Import MDL2'
	bl_options = {'UNDO'}
	filename_ext = ".MDL2"
	filter_glob = StringProperty(default="*.MDL2", options={'HIDDEN'})
	use_custom_normals = BoolProperty(name="Use MDL2 Normals", description="Preserves the original shading of a MDL2.", default=False)
	mirror_mesh = BoolProperty(name="Mirror Meshes", description="Mirrors models. Careful, sometimes bones don't match!", default=False)
	
	def execute(self, context):
		from . import import_mdl2
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		errors = import_mdl2.load(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}

class ExportMDL2(bpy.types.Operator, ExportHelper):
	"""Export to MDL2 file format (.MDL2)"""
	bl_idname = "export_scene.cobra_mdl2"
	bl_label = 'Export MDL2'
	filename_ext = ".MDL2"
	filter_glob = StringProperty(default="*.MDL2", options={'HIDDEN'})
	
	def execute(self, context):
		from . import export_mdl2
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "check_existing"))
		errors = export_mdl2.save(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}
		
class StripShells(bpy.types.Operator):
	"""Remove duplicate faces for a faster export and to avoid blender hiccups"""
	bl_idname = "object.strip_shells"
	bl_label = "Strip Shells"
	bl_options = {'REGISTER', 'UNDO'}

	num_shells = IntProperty(
			name="Shell Count",
			description="Assumed number of shells",
			min=1, max=10,
			default=6, )
			
	def execute(self, context):
		from .utils import shell
		shell.strip_shells_wrapper(self.num_shells)
		return {'FINISHED'}

#Add to a menu
def menu_func_export(self, context):
	self.layout.operator(ExportMDL2.bl_idname, text="Cobra Model (.MDL2)", icon_value=preview_collection["frontier.png"].icon_id)

def menu_func_import(self, context):
	self.layout.operator(ImportMDL2.bl_idname, text="Cobra Model (.MDL2)", icon_value=preview_collection["frontier.png"].icon_id)
	self.layout.operator(ImportBani.bl_idname, text="Cobra Baked Anim (.bani)", icon_value=preview_collection["frontier.png"].icon_id)

def menu_func_object(self, context):
	self.layout.operator(StripShells.bl_idname, text="Strip Shells", icon_value=preview_collection["frontier.png"].icon_id)

def register():
	import os
	icons_dir = os.path.join(os.path.dirname(__file__), "icons")
	for icon_name_ext in os.listdir(icons_dir):
		icon_name = os.path.basename(icon_name_ext)
		preview_collection.load(icon_name, os.path.join(os.path.join(os.path.dirname(__file__), "icons"), icon_name_ext), 'IMAGE')
	bpy.utils.register_module(__name__)
	
	bpy.types.INFO_MT_file_import.append(menu_func_import)
	bpy.types.INFO_MT_file_export.append(menu_func_export)
	bpy.types.VIEW3D_PT_tools_object.append(menu_func_object)
	
def unregister():
	bpy.utils.previews.remove(preview_collection)
	
	bpy.utils.unregister_module(__name__)

	bpy.types.INFO_MT_file_import.remove(menu_func_import)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)
	bpy.types.VIEW3D_PT_tools_object.remove(menu_func_object)

if __name__ == "__main__":
	register()
