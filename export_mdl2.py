import os
import time
import struct

import bpy
import mathutils

from pyffi.formats.ms2 import Ms2Format

from .utils import io, matrix_util

# from .common_tmd import errors, log_error, correction_local, correction_global, name_to_blender, name_to_tmd

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
	
def ovl_bones(b_armature_data):
	# todo fix this on goliath frog, messes up due to srb bone
	
	# first just get the roots, then extend it
	roots = [bone for bone in b_armature_data.bones if not bone.parent]
	# this_level = []
	out_bones = roots
	# next_level = []
	for bone in roots:
		out_bones += [child for child in bone.children]
	
	return [b.name for b in out_bones]
	
def get_armature():
	src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
	#do we have armatures?
	if src_armatures:
		#see if one of these is selected
		if len(src_armatures) > 1:
			sel_armatures = [ob for ob in src_armatures if ob.select]
			if sel_armatures:
				return sel_armatures[0]
		return src_armatures[0]
		
def ensure_tri_modifier(ob):
	for mod in ob.modifiers:
		if mod.type in ('TRIANGULATE',):
			break
	else:
		ob.modifiers.new('Triangulate', 'TRIANGULATE')
	
def save(operator, context, filepath = '', export_anims = False, pad_anims = False):
	errors = []
	
	data = Ms2Format.Data()
	# open file for binary reading
	with open(filepath, "rb") as stream:
		data.inspect_quick(stream)
		data.read(stream, data, file=filepath, quick=True)
		
			
		b_armature_ob = get_armature()
		# clear pose
		for pbone in b_armature_ob.pose.bones:
			pbone.matrix_basis = mathutils.Matrix()
		bpy.context.scene.update()
		# bone_names = ovl_bones(b_armature_ob.data)
		bone_names = data.bone_names
		# used to get index from bone name for faster weights
		bones_table = dict( (bone_name_for_blender(bone_name), bone_i) for bone_i, bone_name in enumerate(bone_names) )
		
		for ob in bpy.data.objects:
			if type(ob.data) == bpy.types.Mesh:
				print("\nNext mesh...")
				
				# make sure the model has a triangulation modifier
				ensure_tri_modifier(ob)
				
				#make a copy with all modifiers applied - I think there was another way to do it too
				me = ob.to_mesh(bpy.context.scene, True, "PREVIEW", calc_tessface=False)
				
				#get the index of this model in the mdl2 model buffer
				try:
					ind = int(ob.name.rsplit("_model", 1)[1])
				except:
					print("Bad name, skipping",ob.name)
					continue
				print(ind)
				# we get the corresponding mdl2 model
				model = data.mdl2_header.models[ind]
				unweighted_vertices = []
				tris = []
				# tangents have to be pre-calculated
				# this will also calculate loop normal
				me.calc_tangents()
				verts = [ ]
				# dummy_vertices = []
				dummy_vertices = {}
				
				count_unique = 0
				count_reused = 0
				
				# side note: to update an array, use model.verts.update_size()
				
				# loop faces
				for face in me.polygons:
					tri = []
					# loop over face loop
					for loop_index in face.loop_indices:
						b_loop = me.loops[loop_index]
						b_vert = me.vertices[b_loop.vertex_index]
						
						# get the vectors
						position = b_vert.co
						tangent = b_loop.tangent
						normal = b_loop.normal
						uvs = [(uv_layer.data[loop_index].uv.x, 1-uv_layer.data[loop_index].uv.y) for uv_layer in me.uv_layers[0:4] ]
						
						# by default create a new packed vert for this blender vert
						must_pack = True
						
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
							w_s = sorted(w, key = lambda x:x[1], reverse = True)[0:4]
							#pad the weight list to 4 bones, ie. add empty bones if missing
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
						# todo: do the usual split verts stuff once properly implemented
						tri.append(v_index)
					tris.append( tri )
							
						
				print("count_unique",count_unique)
				print("count_reused",count_reused)
				
				out_tris = list(tris)
				shell_count = ob["add_shells"]
				print("Got to add shells",shell_count)
				for shell in range(shell_count):
					print("Shell",shell)
					out_tris.extend(tris)
					
				# update vert & tri array
				model.verts = verts
				model.tris = out_tris
				if unweighted_vertices:
					print("unweighted_vertices",unweighted_vertices)
				# print(len(model.verts), len(me.vertices))
				# for mdl2_vert, b_vert in zip(model.verts, me.vertices):
					# mdl2_vert.position = b_vert.co
		# write modified data
		data.write(stream, data, file=filepath)
	# success = '\nFinished Mdl2 Export in %.2f seconds\n' %(time.clock()-starttime)
	# print(success)
	return errors