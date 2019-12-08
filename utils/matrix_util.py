import mathutils
import math
from bpy_extras.io_utils import axis_conversion

def nif_bind_to_blender_bind(nif_armature_space_matrix):
	# post multiplication: local space
	# return correction_inv * correction * nif_armature_space_matrix * correction_inv
	return correction_glob * nif_armature_space_matrix * correction_inv
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
def vec_roll_to_mat3(vec, roll):
    #port of the updated C function from armature.c
    #https://developer.blender.org/T39470
    #note that C accesses columns first, so all matrix indices are swapped compared to the C version
    
    nor = vec.normalized()
    THETA_THRESHOLD_NEGY = 1.0e-9
    THETA_THRESHOLD_NEGY_CLOSE = 1.0e-5
    
    #create a 3x3 matrix
    bMatrix = mathutils.Matrix().to_3x3()

    theta = 1.0 + nor[1]

    if (theta > THETA_THRESHOLD_NEGY_CLOSE) or ((nor[0] or nor[2]) and theta > THETA_THRESHOLD_NEGY):

        bMatrix[1][0] = -nor[0]
        bMatrix[0][1] = nor[0]
        bMatrix[1][1] = nor[1]
        bMatrix[2][1] = nor[2]
        bMatrix[1][2] = -nor[2]
        if theta > THETA_THRESHOLD_NEGY_CLOSE:
            #If nor is far enough from -Y, apply the general case.
            bMatrix[0][0] = 1 - nor[0] * nor[0] / theta
            bMatrix[2][2] = 1 - nor[2] * nor[2] / theta
            bMatrix[0][2] = bMatrix[2][0] = -nor[0] * nor[2] / theta
        
        else:
            #If nor is too close to -Y, apply the special case.
            theta = nor[0] * nor[0] + nor[2] * nor[2]
            bMatrix[0][0] = (nor[0] + nor[2]) * (nor[0] - nor[2]) / -theta
            bMatrix[2][2] = -bMatrix[0][0]
            bMatrix[0][2] = bMatrix[2][0] = 2.0 * nor[0] * nor[2] / theta

    else:
        #If nor is -Y, simple symmetry by Z axis.
        bMatrix = mathutils.Matrix().to_3x3()
        bMatrix[0][0] = bMatrix[1][1] = -1.0

    #Make Roll matrix
    rMatrix = mathutils.Matrix.Rotation(roll, 3, nor)
    
    #Combine and output result
    mat = rMatrix * bMatrix
    return mat

def mat3_to_vec_roll(mat):
    #this hasn't changed
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv * mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll

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

