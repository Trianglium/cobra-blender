import os
import time
import math

import bpy
# import bmesh
import mathutils

from .utils import matrix_util
from .pyffi_ext.formats.ms2 import Ms2Format

def load_mdl2(file_path):
	"""Loads a mdl2 from the given file path"""
	print("Importing {0}".format(file_path))

	data = Ms2Format.Data()
	# open file for binary reading
	with open(file_path, "rb") as stream:
		data.inspect_quick(stream)
		data.read(stream, data, file=file_path)
	return data

def bone_name_for_blender(n):
	if "def_r_" in n:
		n = n.replace("def_r_", "def_")+".R"
	if "def_l_" in n:
		n = n.replace("def_l_", "def_")+".L"
	return n
	
def ovl_bones(b_armature_data):
	# first just get the roots, then extend it
	roots = [bone for bone in b_armature_data.bones if not bone.parent]
	# this_level = []
	out_bones = roots
	# next_level = []
	for bone in roots:
		out_bones += [child for child in bone.children]
	
	return [b.name for b in out_bones]

def import_armature(data):
	"""Scans an armature hierarchy, and returns a whole armature.
	This is done outside the normal node tree scan to allow for positioning
	of the bones before skins are attached."""
	bone_info = data.bone_info
	if bone_info:
		armature_name = "Test"
		b_armature_data = bpy.data.armatures.new(armature_name)
		b_armature_data.draw_type = 'STICK'
		# set axis orientation for export
		# b_armature_data.niftools.axis_forward = NifOp.props.axis_forward
		# b_armature_data.niftools.axis_up = NifOp.props.axis_up
		b_armature_obj = create_ob(armature_name, b_armature_data)
		b_armature_obj.show_x_ray = True
		b_armature_obj.layers = select_layer(10)
		bone_names = [bone_name_for_blender(n) for n in data.bone_names]
		# make armature editable and create bones
		bpy.ops.object.mode_set(mode='EDIT', toggle=False)
		print(bone_names)
		print("ovl order")
		for bone_name, o_mat, o_parent_ind in zip(bone_names, bone_info.bone_matrices, bone_info.bone_parents):
			print(bone_name)
			# create a new bone
			if not bone_name:
				bone_name = "Dummy"
			b_edit_bone = b_armature_data.edit_bones.new(bone_name)
			# get armature space matrix in blender's coordinate space
			# n_bind = matrix_util.import_matrix(o_mat).inverted()
			# it should not be needed once we are sure we read the right matrices
			raw_mat = matrix_util.import_matrix(o_mat)
			# print(bone_name, list(int(round(math.degrees(x))) for x in raw_mat.to_euler()))
			# print(bone_name, list(int(round(math.degrees(x))) for x in raw_mat.inverted().to_euler()), "inv")
			n_bind = raw_mat.inverted_safe()
			b_bind = matrix_util.nif_bind_to_blender_bind(n_bind)
			# the following is a workaround because blender can no longer set matrices to bones directly
			tail, roll = matrix_util.mat3_to_vec_roll(b_bind.to_3x3())
			b_edit_bone.head = b_bind.to_translation()
			b_edit_bone.tail = tail + b_edit_bone.head
			b_edit_bone.roll = roll
			# link to parent
			try:
				if o_parent_ind != 255:
					b_parent_bone = b_armature_data.edit_bones[bone_names[o_parent_ind]]
					b_edit_bone.parent = b_parent_bone
			except:
				pass
		
		fix_bone_lengths(b_armature_data)
		bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
		print("blender order")
		for bone in b_armature_data.bones:
			print(bone.name)
		print("restored order")
		bone_names_restored = ovl_bones(b_armature_data)
		for bone in bone_names_restored:
			print(bone)
		return b_armature_obj

def fix_bone_lengths(b_armature_data):
	"""Sets all edit_bones to a suitable length."""
	for b_edit_bone in b_armature_data.edit_bones:
		# don't change root bones
		if b_edit_bone.parent:
			# take the desired length from the mean of all children's heads
			if b_edit_bone.children:
				child_heads = mathutils.Vector()
				for b_child in b_edit_bone.children:
					child_heads += b_child.head
				bone_length = (b_edit_bone.head - child_heads / len(b_edit_bone.children)).length
				if bone_length < 0.0001:
					bone_length = 0.1
			# end of a chain
			else:
				bone_length = b_edit_bone.parent.length
			b_edit_bone.length = bone_length

def append_armature_modifier(b_obj, b_armature):
	"""Append an armature modifier for the object."""
	if b_obj and b_armature:
		b_obj.parent = b_armature
		armature_name = b_armature.name
		b_mod = b_obj.modifiers.new(armature_name, 'ARMATURE')
		b_mod.object = b_armature
		b_mod.use_bone_envelopes = False
		b_mod.use_vertex_groups = True



def create_material(ob, matname):
	# todo: get fgm file
	# material = bfmat(dirname, matname+".bfmat")
	
	print("MATERIAL:",matname)
	#only create the material if we haven't already created it, then just grab it
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
	else:
		mat = bpy.data.materials[matname]
	#now finally set all the textures we have in the mesh
	me = ob.data
	me.materials.append(mat)
	# #reversed so the last is shown
	# for mtex in reversed(mat.texture_slots):
		# if mtex:
			# try:
				# uv_i = int(mtex.uv_layer)
				# for texface in me.uv_textures[uv_i].data:
					# texface.image = mtex.texture.image
			# except:
				# print("No matching UV layer for Texture!")
	#and for rendering, make sure each poly is assigned to the material
	for f in me.polygons:
		f.material_index = 0
	
def create_ob(ob_name, ob_data):
	ob = bpy.data.objects.new(ob_name, ob_data)
	bpy.context.scene.objects.link(ob)
	bpy.context.scene.objects.active = ob
	return ob

def mesh_from_data(name, verts, faces, wireframe = True):
	me = bpy.data.meshes.new(name)
	me.from_pydata(verts, [], faces)
	me.update()
	ob = create_ob(name, me)
	if wireframe:
		ob.draw_type = 'WIRE'
	return ob, me
	
def select_layer(layer_nr): return tuple(i == layer_nr for i in range(0, 20))
	
def load(operator, context, filepath = "", use_custom_normals = False, mirror_mesh = False):
	mdl2_name = os.path.basename(filepath)
	data = load_mdl2(filepath)
	
	# else operators choke on objects in hidden layers
	bpy.context.scene.layers = [True] * 20

	errors = []
	# try:
	b_armature_obj = import_armature(data)
	# except:
		# print("Armature failed")
	print("data.models",data.mdl2_header.models)
	for model_i, model in enumerate(data.mdl2_header.models):
		lod_i = model.lod_index
		print("\nmodel_i",model_i)
		print("lod_i",lod_i)
		print("flag",model.flag)
		print("bits",bin(model.flag) )
		# create object and mesh from data
		ob, me = mesh_from_data(mdl2_name+"_LOD{}_model{}".format(lod_i, model_i), model.vertices, model.tris, wireframe = False)
		ob["add_shells"] = 0
		ob["flag"] = model.flag
		
		ob.layers = select_layer(lod_i)
		create_material(ob, model.material)
		
		# set uv data
		# todo: get UV count
		for uv_i in range(0, 4):
			uvs = model.uv_layers[uv_i]
			me.uv_textures.new("UV"+str(uv_i))
			me.uv_layers[-1].data.foreach_set("uv", [uv for pair in [uvs[l.vertex_index] for l in me.loops] for uv in (pair[0], 1-pair[1])])
		
		# # todo: get vcol count, if it is vcol
		# for col_i in range(2):
		# 	vcols = model.colors[col_i]
		# 	me.vertex_colors.new("RGB"+str(col_i))
		# 	me.vertex_colors[-1].data.foreach_set("color", [c for col in [vcols[l.vertex_index] for l in me.loops] for c in (col.r/255, col.g/255, col.b/255)])
		# 	me.vertex_colors.new("AAA"+str(col_i))
		# 	me.vertex_colors[-1].data.foreach_set("color", [c for col in [vcols[l.vertex_index] for l in me.loops] for c in (col.a/255, col.a/255, col.a/255)])
		
		# me.vertex_colors.new("tangents")
		# me.vertex_colors[-1].data.foreach_set("color", [c for col in [model.tangents[l.vertex_index] for l in me.loops] for c in col])
		
		# me.vertex_colors.new("normals")
		# me.vertex_colors[-1].data.foreach_set("color", [c for col in [model.normals[l.vertex_index] for l in me.loops] for c in col])
		
		# create vgroups and store weights
		for i, vert	in enumerate(model.weights):
			for bonename, weight in vert:
				bonename = bone_name_for_blender(bonename)
				if bonename not in ob.vertex_groups: ob.vertex_groups.new(bonename)
				ob.vertex_groups[bonename].add([i], weight, 'REPLACE')
		
		
		# map normals so we can set them to the edge corners (stored per loop)
		no_array = []
		for face in me.polygons:
			for vertex_index in face.vertices:
				no_array.append(model.normals[vertex_index])
				# no_array.append(model.tangents[vertex_index])
			face.use_smooth = True
			#and for rendering, make sure each poly is assigned to the material
			face.material_index = 0
		
		# set normals
		if use_custom_normals:
			me.use_auto_smooth = True
			me.normals_split_custom_set(no_array)
		# else:
		# # no operator, but bmesh
		# 	bm = bmesh.new()
		# 	bm.from_mesh(me)
		# 	bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
		# 	bm.to_mesh(me)
		# 	me.update()
		# 	bm.clear()
		# 	bm.free()
		
		bpy.ops.object.mode_set(mode='EDIT')
		if mirror_mesh:
			bpy.ops.mesh.bisect(plane_co=(0,0,0), plane_no=(1,0,0), clear_inner=True)
			bpy.ops.mesh.select_all(action='SELECT')
			mod = ob.modifiers.new('Mirror', 'MIRROR')
			mod.use_clip = True
			mod.use_mirror_merge = True
			mod.use_mirror_vertex_groups = True
			mod.use_x = True
			mod.merge_threshold = 0.001
		bpy.ops.mesh.tris_convert_to_quads()
		if not use_custom_normals:
			bpy.ops.mesh.remove_doubles(threshold = 0.0001, use_unselected = False)
		try:
			bpy.ops.uv.seams_from_islands()
		except:
			print(ob.name+" has no UV coordinates!")
		bpy.ops.object.mode_set(mode='OBJECT')

		# link to armature, only after mirror so the order is good and weights are mirrored
		if data.bone_info:
			append_armature_modifier(ob, b_armature_obj)

			
	success = '\nFinished MS2 Import'
	print(success)
	return errors