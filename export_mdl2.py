import os
import time
import struct

import bpy
import mathutils

from .utils import matrix_util
from .pyffi_ext.formats.ms2 import Ms2Format

MAX_USHORT = 65535


def bone_name_for_blender(n):
	if "def_r_" in n:
		n = n.replace("def_r_", "def_")+".R"
	if "def_l_" in n:
		n = n.replace("def_l_", "def_")+".L"
	return n


def bone_name_for_ovl(n):
	if n.endswith(".R"):
		n = n[:-2].replace("def_", "def_r_")
	if n.endswith(".L"):
		n = n[:-2].replace("def_", "def_l_")
	return n


def get_armature():
	src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
	# do we have armatures?
	if src_armatures:
		# see if one of these is selected
		if len(src_armatures) > 1:
			sel_armatures = [ob for ob in src_armatures if ob.select]
			if sel_armatures:
				return sel_armatures[0]
		return src_armatures[0]


def ensure_tri_modifier(ob):
	"""Makes sure that ob has a triangulation modifier in its stack."""
	for mod in ob.modifiers:
		if mod.type in ('TRIANGULATE',):
			break
	else:
		ob.modifiers.new('Triangulate', 'TRIANGULATE')


def save(operator, context, filepath=''):
	errors = []
	start_time = time.time()
	# todo - get and set this per model, possibly according to model.flag
	num_uvs = 4
	print(f"\nExporting {filepath} into export subfolder...")
	if not os.path.isfile(filepath):
		errors.append(f"{filepath} does not exist. You must open an existing MDL2 file for exporting.")
		return errors
	data = Ms2Format.Data()
	# open file for binary reading
	with open(filepath, "rb") as stream:
		data.read(stream, data, file=filepath, quick=True)

		b_armature_ob = get_armature()
		# clear pose
		for pbone in b_armature_ob.pose.bones:
			pbone.matrix_basis = mathutils.Matrix()
		# bpy.context.scene.update()
		bone_names = data.bone_names
		# used to get index from bone name for faster weights
		bones_table = dict( (bone_name_for_blender(bone_name), bone_i) for bone_i, bone_name in enumerate(bone_names) )

		# ensure that these are initialized
		for model in data.mdl2_header.models:
			model.tri_indices = []
			model.verts = []

		for ob in bpy.data.objects:
			if type(ob.data) == bpy.types.Mesh:
				print("\nNext mesh...")

				# make sure the model has a triangulation modifier
				ensure_tri_modifier(ob)

				# make a copy with all modifiers applied
				dg = bpy.context.evaluated_depsgraph_get()
				eval_obj = ob.evaluated_get(dg)
				me = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dg)

				# get the index of this model in the mdl2 model buffer
				try:
					ind = int(ob.name.rsplit("_model", 1)[1])
				except:
					print("Bad name, skipping",ob.name)
					continue
				print("Model slot",ind)

				# we get the corresponding mdl2 model
				model = data.mdl2_header.models[ind]

				if not len(me.vertices):
					errors.append(f"Model {ob.name} has no vertices!")
					return errors

				if not len(me.polygons):
					errors.append(f"Model {ob.name} has no polygons!")
					return errors

				if len(me.uv_layers) != num_uvs:
					errors.append(f"Model {ob.name} has {len(me.uv_layers)} UV layers, but {num_uvs} were expected!")
					return errors

				uv_layer_lengths = [len(uv_layer.data) for uv_layer in me.uv_layers[:num_uvs]]
				if uv_layer_lengths.count(uv_layer_lengths[0]) != num_uvs:
					print(uv_layer_lengths, uv_layer_lengths.count(uv_layer_lengths[0]), num_uvs)
					errors.append(f"UV layers for {ob.name} do not have the same length - blender bug?")
					return errors

				unweighted_vertices = []
				tris = []
				# tangents have to be pre-calculated
				# this will also calculate loop normal
				me.calc_tangents()
				verts = []
				# use a dict mapping dummy vertices to their index for fast lookup
				dummy_vertices = {}

				count_unique = 0
				count_reused = 0

				# loop faces
				for face in me.polygons:
					tri = []
					if len(face.loop_indices) != 3:
						errors.append(f"Model {ob.name} is not triangulated!")
						return errors
					# loop over face loop
					for loop_index in face.loop_indices:
						b_loop = me.loops[loop_index]
						b_vert = me.vertices[b_loop.vertex_index]

						# get the vectors
						position = b_vert.co
						tangent = b_loop.tangent
						normal = b_loop.normal
						uvs = [(uv_layer.data[loop_index].uv.x, 1-uv_layer.data[loop_index].uv.y) for uv_layer in me.uv_layers[:num_uvs]]

						# create a dummy bytes str for indexing
						dummy = struct.pack('<10f', *position, *uvs[0], *uvs[1], *tangent )
						try:
							v_index = dummy_vertices[dummy]
							count_reused += 1
						except:
							v_index = count_unique
							dummy_vertices[dummy] = v_index
							count_unique += 1

							# create ms2 vertex
							ms2_vert = Ms2Format.PackedVert()
							# set pack base
							ms2_vert.base = data.mdl2_header.model_info.pack_offset
							verts.append(ms2_vert)

							# store the actual vert data
							ms2_vert.position = position
							ms2_vert.tangent = tangent
							ms2_vert.normal = normal
							ms2_vert.uvs = uvs

							# get the weights only if it's a new vert
							w = []
							for vertex_group in b_vert.groups:
								vgroup_name = ob.vertex_groups[vertex_group.group].name
								# get the unk0
								if vgroup_name == "unk0":
									ms2_vert.unk_0 = min(int(round(vertex_group.weight*255.0)), 255)
								elif vgroup_name == "fur_length":
									# only store this hack for shells, never for fins
									if model.flag == 885:
										ms2_vert.fur_length = vertex_group.weight
								else:
									# avoid check for dummy vertex groups without corresponding bones
									try: w.append( [bones_table[vgroup_name], vertex_group.weight] )
									except: w.append( [int(vgroup_name), vertex_group.weight] )
							# get the 4 strongest influences on this vert
							w_s = sorted(w, key = lambda x:x[1], reverse = True)[0:4]
							# pad the weight list to 4 bones, ie. add empty bones if missing
							for i in range(0, 4-len(w_s)): w_s.append( [0,0] )
							# summed weights
							sw = sum(w[1] for w in w_s)
							# print(sw)
							if sw > 0.0:
								# normalize
								for x in range(4):
									w_s[x][1] /= sw
								ms2_vert.weights = w_s
								# skin partition
								ms2_vert.bone_index = w_s[0][0]
							elif b_loop.vertex_index not in unweighted_vertices:
								# print("Sum of weights",sw)
								unweighted_vertices.append(b_loop.vertex_index)
							if v_index > MAX_USHORT:
								errors.append("f{ob.name} has too many MDL2 verts. The limit is {MAX_USHORT}. \nBlender vertices have to be duplicated on every UV seam, hence the increase.")
								return errors
						tri.append(v_index)
					tris.append( tri )

				print("count_unique",count_unique)
				print("count_reused",count_reused)

				out_tris = list(tris)
				# set shell count if not present
				if "add_shells" in ob:
					shell_count = ob["add_shells"]
				else:
					shell_count = 0
					ob["add_shells"] = 0
				print("Got to add shells",shell_count)
				for shell in range(shell_count):
					print("Shell",shell)
					out_tris.extend(tris)

				# update vert & tri array
				model.verts = verts
				model.tris = out_tris
				if unweighted_vertices:
					print("unweighted_vertices",unweighted_vertices)
					errors.append(f"#{ob.name} has {len(unweighted_vertices)} unweighted vertices!")
					return errors

		# check if any is empty
		for i, model in enumerate(data.mdl2_header.models):
			if not model.tri_indices or not model.verts:
				errors.append(f"MDL2 Modeldata #{i} has not been populated. \nEnsure that the name of the blender model for that number follows the naming convention.")
				return errors

		# write modified data
		data.write(stream, data, file=filepath)
	print(f"\nFinished Mdl2 Export in {time.time()-start_time:.2f} seconds")
	return errors
