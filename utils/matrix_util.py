import mathutils
import math
from bpy_extras.io_utils import axis_conversion

# a tuple of prefix, clipped prefix, suffix
naming_convention = (
	("def_r_", "def_", ".R"),
	("def_l_", "def_", ".L"),
)


def bone_name_for_blender(n):
	"""Appends a suffix to the end if relevant prefix was found"""
	for prefix, clipped_prefix, suffix in naming_convention:
		if prefix in n:
			n = n.replace(prefix, clipped_prefix)+suffix
	return n


def bone_name_for_ovl(n):
	"""Restores the proper prefix if relevant suffix was found"""
	for prefix, clipped_prefix, suffix in naming_convention:
		if n.endswith(suffix):
			n = n.replace(suffix, "").replace(clipped_prefix, prefix)
	return n


def nif_bind_to_blender_bind(nif_armature_space_matrix):
	# post multiplication: local space
	# return correction_inv * correction * nif_armature_space_matrix * correction_inv
	return correction_glob @ nif_armature_space_matrix @ correction_inv
	# return nif_armature_space_matrix * correction_inv


def set_bone_orientation(from_forward, from_up):
	# if version in (0x14020007, ):
	#	skyrim
	#	from_forward = "Z"
	#	from_up = "Y"
	# else:
	#	ZT2 and other old ones
	#	from_forward = "X"
	#	from_up = "Y"
	global correction
	global correction_inv
	correction = axis_conversion(from_forward, from_up).to_4x4()
	correction_inv = correction.inverted()
#from_forward='Y', from_up='Z', to_forward='Y', to_up='Z'
correction_glob = axis_conversion("-Z", "Y").to_4x4()
# mirror about x axis too:
correction_glob[0][0] = -1
# set these from outside using set_bone_correction_from_version once we have a version number
correction = None
correction_inv = None

set_bone_orientation("-X", "Y")

def import_matrix(m):
	"""Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
	return mathutils.Matrix( m.as_list() )#.transposed()
	
def decompose_srt(matrix):
    """Decompose Blender transform matrix as a scale, rotation matrix, and
    translation vector."""

    # get matrix components
    trans_vec, rot_quat, scale_vec = matrix.decompose()

    #obtain a combined scale and rotation matrix to test determinate
    rotmat = rot_quat.to_matrix()
    scalemat = mathutils.Matrix(   ((scale_vec[0], 0.0, 0.0),
                                    (0.0, scale_vec[1], 0.0),
                                    (0.0, 0.0, scale_vec[2])) )
    scale_rot = scalemat * rotmat

    # and fix their sign
    if (scale_rot.determinant() < 0): scale_vec.negate()
    # only uniform scaling
    # allow rather large error to accomodate some nifs
    if abs(scale_vec[0]-scale_vec[1]) + abs(scale_vec[1]-scale_vec[2]) > 0.02:
        NifLog.warn("Non-uniform scaling not supported." +
            " Workaround: apply size and rotation (CTRL-A).")
    return [scale_vec[0], rotmat, trans_vec]

