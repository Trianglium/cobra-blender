from pyffi.formats.ms2 import Ms2Format
from pyffi.formats.bani import BaniFormat
		
class Mdl2File:

	@staticmethod
	def load(file_path):
		"""Loads a mdl2 from the given file path"""
		print("Importing {0}".format(file_path))

		data = Ms2Format.Data()
		# open file for binary reading
		with open(file_path, "rb") as stream:
			data.inspect_quick(stream)
			data.read(stream, data, file=file_path)
		return data
		
	@staticmethod
	def write(file_path):
		"""Loads a mdl2 from the given file path"""
		print("Importing {0}".format(file_path))

		data = Ms2Format.Data()
		# open file for binary reading
		with open(file_path, "rb") as stream:
			data.inspect_quick(stream)
			data.write(stream, data, file=file_path)
		return data
		
class BaniFile:
	@staticmethod
	def load(file_path):
		"""Loads a bani from the given file path"""
		print("Importing {0}".format(file_path))

		data = BaniFormat.Data()
		# open file for binary reading
		with open(file_path, "rb") as stream:
			data.inspect_quick(stream)
			data.read(stream, data, file=file_path)
		return data

# ms2 = Ms2File()
# data = ms2.load_ms2("C:/Users/arnfi/Desktop/ovl/models.ms2")