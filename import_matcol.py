import os
import io
import sys
import bpy
import mathutils

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

def create_material(matcol_path):
	slots = load_matcol(matcol_path)

	matdir, mat_ext = os.path.split(matcol_path)
	matname = os.path.splitext(mat_ext)[0]
	print("MATERIAL:",matname)
	#only create the material if we haven't already created it, then just grab it
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
		mat.use_nodes = True
		
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
			print("Slot",i)
			tex = load_tex(tree, texture)
			textures.append(tex)

			# height offset attribute
			heightoffset = infos[1].info.value[0]
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

			uv = tree.nodes.new('ShaderNodeUVMap')
			uv.name = "TexCoordIndex"+str(i)
			uv.uv_map = "UV0"
			
			transform = tree.nodes.new('ShaderNodeMapping')
			#todo: negate V coordinate
			matrix_4x4 = mathutils.Matrix()
			uvscale = list(i for i in infos[7].info.value)[:3]
			transform.scale = uvscale

			# in radians for both blender & game matcol
			rot = infos[5].info.value[0]
			# flip since blender flips V coord
			transform.rotation[2] = -rot
			transform.translation = matrix_4x4.to_translation()
			transform.name = "TextureTransform"+str(i)
			tree.links.new(uv.outputs[0], transform.inputs[0])
			tree.links.new(transform.outputs[0], tex.inputs[0])
			
			tex.update()
			mask.update()

			mixRGB = tree.nodes.new('ShaderNodeMixRGB')
			mixRGB.blend_type = "ADD"
			tree.links.new(mask.outputs[0], mixRGB.inputs[0])
			if last_mixer:
				tree.links.new(last_mixer.outputs[0], mixRGB.inputs[1])
			else:
				mixRGB.inputs[1].default_value = (0,0,0,1)
			tree.links.new(scale.outputs[0], mixRGB.inputs[2])
			last_mixer = mixRGB

		normal_path = os.path.join(matdir, matname+".pnormaltexture.png".format(i))
		normal = load_tex(tree, normal_path)
		normal.color_space = "NONE"
		normal_map = tree.nodes.new('ShaderNodeNormalMap')
		tree.links.new(normal.outputs[0],		normal_map.inputs[1])

		bump = tree.nodes.new('ShaderNodeBump')
		tree.links.new(mixRGB.outputs[0],		bump.inputs[2])
		tree.links.new(normal_map.outputs[0],		bump.inputs[3])
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
			continue
		fgm_path = os.path.join(lib_dir, layer.name+".fgm")
		# print(fgm_path)
		fgm_data = get_data(fgm_path, FgmFormat.Data)
		base_index = fgm_data.fgm_header.textures[0].layers[1]
		height_index = fgm_data.fgm_header.textures[1].layers[1]
		print("base_array_index",base_index)
		print("height_array_index",height_index)
		print("base",base_textures[base_index])
		print("height",height_textures[height_index])
		slots.append( (layer.infos, height_textures[height_index]) )
	return slots
	
if __name__ == '__main__':
	matcol_path = "C:/Users/arnfi/Desktop/pp/herrerasaurus.materialcollection"
	load_matcol(matcol_path)
	# python tmc.py