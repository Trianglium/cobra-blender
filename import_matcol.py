import os
import io
import sys
import bpy
import mathutils
import math

from .pyffi_ext.formats.materialcollection import MaterialcollectionFormat
from .pyffi_ext.formats.fgm import FgmFormat
from .utils.node_arrange import nodes_iterate

def load(operator, context, filepath = ""):
	create_material(filepath)
	return []

def load_tex(tree, tex_path):
	#todo: only load if img can't be found in existing images
	name = os.path.basename(tex_path)
	if name not in bpy.data.images:
		try:
			img = bpy.data.images.load(tex_path)
		except:
			print("Could not find image "+tex_path+", generating blank image!")
			img = bpy.data.images.new(tex_path,1,1)
	else:
		img = bpy.data.images[name]
	tex = tree.nodes.new('ShaderNodeTexImage')
	# tex.name = "Texture"+str(i)
	tex.image = img
	# #eg. African violets, but only in rendered view; but: glacier
	# tex.extension = "CLIP" if (cull_mode == "2" and not (material.AlphaTestEnable is False and material.AlphaBlendEnable is False) ) else "REPEAT"
	tex.interpolation = "Smart"

	return tex

def create_flip():
	name = "FlipX"
	#only create the material if we haven't already created it, then just grab it
	if name not in bpy.data.node_groups:
		# create a group
		test_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')

	else:
		test_group = bpy.data.node_groups[name]
		for node in test_group.nodes:
			test_group.nodes.remove(node)
		for node in test_group.inputs:
			test_group.inputs.remove(node)
		for node in test_group.outputs:
			test_group.outputs.remove(node)

	# create group inputs
	group_inputs = test_group.nodes.new('NodeGroupInput')
	group_inputs.location = (-350,0)
	test_group.inputs.new('NodeSocketVectorXYZ','in')

	# create group outputs
	group_outputs = test_group.nodes.new('NodeGroupOutput')
	group_outputs.location = (300,0)
	test_group.outputs.new('NodeSocketVectorXYZ','out')


	split = test_group.nodes.new('ShaderNodeSeparateXYZ')
	split.label = "Split"
	test_group.links.new(group_inputs.outputs["in"], split.inputs[0])
	
	flip = test_group.nodes.new('ShaderNodeMath')
	flip.operation = 'MULTIPLY'
	test_group.links.new(split.outputs[0], flip.inputs[0])
	flip.inputs[1].default_value = -1.0
	
	join = test_group.nodes.new('ShaderNodeCombineXYZ')
	join.label = "Join"
	test_group.links.new(flip.outputs[0], join.inputs[0])
	test_group.links.new(split.outputs[1], join.inputs[1])
	test_group.links.new(split.outputs[2], join.inputs[2])
	
	# #link output
	test_group.links.new(join.outputs[0], group_outputs.inputs['out'])
	
	nodes_iterate(test_group, group_outputs)
	return test_group

def create_group():
	flipgr = create_flip()
	name = "MatcolSlot"
	#only create the material if we haven't already created it, then just grab it
	if name not in bpy.data.node_groups:
		# create a group
		test_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')

	else:
		test_group = bpy.data.node_groups[name]
		for node in test_group.nodes:
			test_group.nodes.remove(node)
		for node in test_group.inputs:
			test_group.inputs.remove(node)
		for node in test_group.outputs:
			test_group.outputs.remove(node)

	# create group inputs
	group_inputs = test_group.nodes.new('NodeGroupInput')
	test_group.inputs.new('NodeSocketVectorTranslation','UVOffset')
	test_group.inputs.new('NodeSocketFloatAngle','uvRotationAngle')
	test_group.inputs.new('NodeSocketVectorTranslation','uvRotationPosition')
	test_group.inputs.new('NodeSocketVectorXYZ','uvTile')

	# create group outputs
	group_outputs = test_group.nodes.new('NodeGroupOutput')
	group_outputs.location = (300,0)
	test_group.outputs.new('NodeSocketVectorXYZ','out')


	offset_flipx = test_group.nodes.new("ShaderNodeGroup")
	offset_flipx.node_tree = flipgr
	test_group.links.new(group_inputs.outputs["UVOffset"], offset_flipx.inputs[0])
	
	rotpos_flipx = test_group.nodes.new("ShaderNodeGroup")
	rotpos_flipx.node_tree = flipgr
	test_group.links.new(group_inputs.outputs["uvRotationPosition"], rotpos_flipx.inputs[0])

	uv = test_group.nodes.new('ShaderNodeUVMap')
	uv.label = "UV Input"
	uv.uv_map = "UV0"
	
	scale_pivot = test_group.nodes.new('ShaderNodeMapping')
	scale_pivot.inputs[1].default_value[1] = -1.0
	scale_pivot.label = "Scale Pivot"
	test_group.links.new(uv.outputs[0], scale_pivot.inputs[0])



	uv_offset = test_group.nodes.new('ShaderNodeMapping')
	uv_offset.label = "UVOffset"
	test_group.links.new(scale_pivot.outputs[0], uv_offset.inputs[0])
	test_group.links.new(offset_flipx.outputs[0], uv_offset.inputs[1])
	
	uv_tile = test_group.nodes.new('ShaderNodeMapping')
	uv_tile.label = "uvTile"
	test_group.links.new(uv_offset.outputs[0], uv_tile.inputs[0])
	test_group.links.new(group_inputs.outputs["uvTile"], uv_tile.inputs[3])
	
	rot_pivot = test_group.nodes.new('ShaderNodeMapping')
	rot_pivot.inputs[1].default_value[1] = -1.0
	rot_pivot.label = "Rot Pivot"
	test_group.links.new(uv_tile.outputs[0], rot_pivot.inputs[0])
	
	uv_rot_pos_a = test_group.nodes.new('ShaderNodeMapping')
	uv_rot_pos_a.label = "uvRotationPosition"
	test_group.links.new(rot_pivot.outputs[0], uv_rot_pos_a.inputs[0])
	test_group.links.new(rotpos_flipx.outputs[0], uv_rot_pos_a.inputs[1])
	
	# extra step to create vector from float
	uv_rot_combine = test_group.nodes.new('ShaderNodeCombineXYZ')
	uv_rot_combine.label = "build uvRotation Vector"
	test_group.links.new(group_inputs.outputs["uvRotationAngle"], uv_rot_combine.inputs[2])
	
	
	uv_rot = test_group.nodes.new('ShaderNodeMapping')
	uv_rot.label = "uvRotationAngle"
	test_group.links.new(uv_rot_pos_a.outputs[0], uv_rot.inputs[0])
	test_group.links.new(uv_rot_combine.outputs[0], uv_rot.inputs[2])

	# extra step to negate input
	uv_rot_pos_flip = test_group.nodes.new('ShaderNodeVectorMath')
	uv_rot_pos_flip.operation = "SCALE"
	uv_rot_pos_flip.label = "flip uvRotationPosition"
	# counter intuitive index for non-vector argument!
	uv_rot_pos_flip.inputs[2].default_value = -1.0
	test_group.links.new(rotpos_flipx.outputs[0], uv_rot_pos_flip.inputs[0])
	
	uv_rot_pos_b = test_group.nodes.new('ShaderNodeMapping')
	uv_rot_pos_b.label = "undo uvRotationPosition"
	test_group.links.new(uv_rot_pos_flip.outputs[0], uv_rot_pos_b.inputs[1])
	test_group.links.new(uv_rot.outputs[0], uv_rot_pos_b.inputs[0])
	
	# #link output
	test_group.links.new(uv_rot_pos_b.outputs[0], group_outputs.inputs['out'])
	
	
	nodes_iterate(test_group, group_outputs)
	return test_group

def create_material(matcol_path):
	slots = load_matcol(matcol_path)

	matdir, mat_ext = os.path.split(matcol_path)
	matname = os.path.splitext(mat_ext)[0]
	print("MATERIAL:",matname)
	#only create the material if we haven't already created it, then just grab it
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
	#only create the material if we haven't already created it, then just grab it
	else:
		mat = bpy.data.materials[matname]

	
	mat.use_nodes = True
	
	group = create_group()
	tree = mat.node_tree
	# clear default nodes
	for node in tree.nodes:
		tree.nodes.remove(node)
	output = tree.nodes.new('ShaderNodeOutputMaterial')
	# principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
	shader_diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')
	
	last_mixer = None
	textures = []
	for i, (infos, texture) in enumerate( slots):
		# skip default materials that have no fgm assigned
		if not texture:
			continue
		print("Slot",i)
		tex = load_tex(tree, texture)
		textures.append(tex)

		# height offset attribute
		heightoffset = infos[2].info.value[0]
		offset = tree.nodes.new('ShaderNodeMath')
		offset.operation = "ADD"
		offset.inputs[1].default_value = heightoffset
		tree.links.new(tex.outputs[0], offset.inputs[0])

		# height scale attribute
		heightscale = infos[3].info.value[0]
		scale = tree.nodes.new('ShaderNodeMath')
		scale.operation = "MULTIPLY"
		scale.inputs[1].default_value = heightscale * 100
		tree.links.new(offset.outputs[0], scale.inputs[0])
		

		mask_path = os.path.join(matdir, matname+".playered_blendweights_{:02}.png".format(i))
		mask = load_tex(tree, mask_path)


		transform = tree.nodes.new("ShaderNodeGroup")
		transform.node_tree = group

		# m_uvRotationPosition
		uvrotpos = list(i for i in infos[6].info.value)[:3]
		transform.inputs["uvRotationPosition"].default_value = uvrotpos

		# m_UVOffset
		uvoffset = list(i for i in infos[4].info.value)[:3]
		transform.inputs["UVOffset"].default_value = uvoffset

		# m_uvTile
		uvscale = list(i for i in infos[7].info.value)[:3]
		transform.inputs["uvTile"].default_value = uvscale

		# m_uvRotationAngle
		# matcol stores it as fraction of 180°
		# in radians for blender internally even though it displays as degree
		rot = math.radians( infos[5].info.value[0]*180 )
		# flip since blender flips V coord
		transform.inputs["uvRotationAngle"].default_value = -rot
		tree.links.new(transform.outputs[0], tex.inputs[0])
		
		tex.update()
		mask.update()

		mixRGB = tree.nodes.new('ShaderNodeMixRGB')
		mixRGB.blend_type = "MIX"
		tree.links.new(mask.outputs[0], mixRGB.inputs[0])
		if last_mixer:
			tree.links.new(last_mixer.outputs[0], mixRGB.inputs[1])
		else:
			mixRGB.inputs[1].default_value = (0,0,0,1)
		tree.links.new(scale.outputs[0], mixRGB.inputs[2])
		last_mixer = mixRGB

	normal_path = os.path.join(matdir, matname+".pnormaltexture.png".format(i))
	normal = load_tex(tree, normal_path)
	normal.image.colorspace_settings.name = "Non-Color"
	normal_map = tree.nodes.new('ShaderNodeNormalMap')
	tree.links.new(normal.outputs[0],		normal_map.inputs[1])

	bump = tree.nodes.new('ShaderNodeBump')
	
	# does not create link in 2.81 ???
	tree.links.new(normal_map.outputs[0], bump.inputs[3])

	tree.links.new(mixRGB.outputs[0], bump.inputs[2])
	tree.links.new(bump.outputs[0],			shader_diffuse.inputs[2])
	tree.links.new(shader_diffuse.outputs[0],		output.inputs[0])
		
	nodes_iterate(tree, output)
	return mat
	# #now finally set all the textures we have in the mesh
	# me = ob.data
	# me.materials.append(mat)
	
def get_data(p, d):
	dat = d()
	with open(p, "rb") as stream:
		dat.read(stream)
	return dat
	
def load_matcol(matcol_path):
	lib_dir = os.path.normpath(os.path.dirname(matcol_path))
	materialcollection_data = get_data(matcol_path, MaterialcollectionFormat.Data)
	slots = []
	rootname = "anky_ankylo_backplates"
	basecol = ".pbasecolourtexture"
	baseheight = ".pheighttexture"
	all_textures = [file for file in os.listdir(lib_dir) if file.lower().endswith(".png")]
	base_textures = [os.path.join(lib_dir, file) for file in all_textures if rootname in file and basecol in file]
	height_textures = [os.path.join(lib_dir, file) for file in all_textures if rootname in file and baseheight in file]
	# print(base_textures)
	# for layer in materialcollection_data.header.layered_wrapper:
		# print(layer)
	for layer in materialcollection_data.header.layered_wrapper.layers:
		print(layer.name)
		if layer.name == "Default":
			print("Skipping Default layer")
			htex = None
		else:
			fgm_path = os.path.join(lib_dir, layer.name+".fgm")
			# print(fgm_path)
			fgm_data = get_data(fgm_path, FgmFormat.Data)
			base_index = fgm_data.fgm_header.textures[0].layers[1]
			height_index = fgm_data.fgm_header.textures[1].layers[1]
			print("base_array_index",base_index)
			print("height_array_index",height_index)
			print("base",base_textures[base_index])
			print("height",height_textures[height_index])
			htex = height_textures[height_index]
		slots.append( (layer.infos, htex) )
	return slots
	
if __name__ == '__main__':
	matcol_path = "C:/Users/arnfi/Desktop/pp/herrerasaurus.materialcollection"
	load_matcol(matcol_path)
	# python tmc.py