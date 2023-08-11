import math
import os
import io
import struct
import enum

bbHeader = None

class sBBHeader:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)
			global bbHeader
			bbHeader = self

	def read(self, file: io.BufferedReader):
		self.checksum = struct.unpack("<I", file.read(4))[0]
		self.magic = struct.unpack("<I", file.read(4))[0]
		self.sRAMOffset = struct.unpack("<I", file.read(4))[0]
		self.vRAMOffset = struct.unpack("<I", file.read(4))[0]
		self.dRAMOffset = struct.unpack("<I", file.read(4))[0]
		self.handlesOffset = struct.unpack("<I", file.read(4))[0]
		self.flag = struct.unpack("<I", file.read(4))[0]
		self.sRAMHeader = sBBSRAMHeader(file)
		self.vRAMHeader = sBBVRAMHeader(file)
		self.dRAMHeader = sBBDRAMHeader(file)
		self.handlesHeader = sBBHandlesHeader(file)

class sBBSRAMHeader:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.checksum = struct.unpack("<I", file.read(4))[0]
		self.magic = struct.unpack("<I", file.read(4))[0]
		self.dataSize = struct.unpack("<I", file.read(4))[0]
		self.startOfGenericAddr = struct.unpack("<i", file.read(4))[0]
		self.endOfGenericAddr = struct.unpack("<i", file.read(4))[0]
		self.endOfAmbientAddr = struct.unpack("<i", file.read(4))[0]
		self.firstAmbientIndex = struct.unpack("<H", file.read(2))[0]
		self.lastAmbientIndex = struct.unpack("<H", file.read(2))[0]
		self.effectList = [EffectStruct(file) for i in range(140)]

class EffectStruct:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.Addr = struct.unpack("<i", file.read(4))[0]
		self.Size = struct.unpack("<i", file.read(4))[0]
		self.ImgAddr = struct.unpack("<i", file.read(4))[0]
		self.ImgSize = struct.unpack("<i", file.read(4))[0]
		self.Multi = struct.unpack("<i", file.read(4))[0]
		self.Loop = struct.unpack("<i", file.read(4))[0]
		self.ResourceId = struct.unpack("<i", file.read(4))[0]
		self.LoopAddr = struct.unpack("<i", file.read(4))[0]

class sBBVRAMHeader:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.checksum = struct.unpack("<I", file.read(4))[0]
		self.magic = struct.unpack("<I", file.read(4))[0]
		self.dataSize = struct.unpack("<I", file.read(4))[0]
		self.texData = texData(file)

class texData:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.texMemoryHandle = struct.unpack("<I", file.read(4))[0]
		self.pInterTex = struct.unpack("<I", file.read(4))[0]
		self.currentInterTex = struct.unpack("<I", file.read(4))[0]
		self.textStartX = struct.unpack("<i", file.read(4))[0]
		self.textStartY = struct.unpack("<i", file.read(4))[0]
		self.clutStartX = struct.unpack("<i", file.read(4))[0]
		self.clutStartY = struct.unpack("<i", file.read(4))[0]
		self.tCX = struct.unpack("<i", file.read(4))[0]
		self.tCY = struct.unpack("<i", file.read(4))[0]
		self.cCX = struct.unpack("<i", file.read(4))[0]
		self.cCY = struct.unpack("<i", file.read(4))[0]
		self.clutArray = [v for v in struct.unpack("<256h", file.read(512))]
		self.clutLineArray = [v for v in struct.unpack("<64B", file.read(64))]
		self.nrVramTextures = struct.unpack("<I", file.read(4))[0]
		self.nrVramCluts = struct.unpack("<I", file.read(4))[0]
		self.pHoleArray = [pigeonHole(file) for i in range(9)]
		self.pTexTypeConv = struct.unpack("<I", file.read(4))[0]

class pigeonHole:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.xStart = struct.unpack("<h", file.read(2))[0]
		self.yStart = struct.unpack("<h", file.read(2))[0]
		self.xSize = struct.unpack("<h", file.read(2))[0]
		self.ySize = struct.unpack("<h", file.read(2))[0]
		self.xOffset = struct.unpack("<h", file.read(2))[0]
		self.yOffset = struct.unpack("<h", file.read(2))[0]
		self.status = struct.unpack("<h", file.read(2))[0]
		self.type = struct.unpack("<h", file.read(2))[0]

class sBBDRAMHeader:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.checksum = struct.unpack("<I", file.read(4))[0]
		self.magic = struct.unpack("<I", file.read(4))[0]
		self.dataSize = struct.unpack("<I", file.read(4))[0]
		self.pMax = struct.unpack("<I", file.read(4))[0]
		self.pCurr = struct.unpack("<I", file.read(4))[0]

class sBBHandlesHeader:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.checksum = struct.unpack("<I", file.read(4))[0]
		self.magic = struct.unpack("<I", file.read(4))[0]
		self.dataSize = struct.unpack("<I", file.read(4))[0]

class sFELevelData: # Front End Specific
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		file.seek(-0x140, os.SEEK_END)
		self.pLvl = struct.unpack("<I", file.read(4))[0]
		self.pBorderSet = struct.unpack("<I", file.read(4))[0]
		self.pColourSet = struct.unpack("<I", file.read(4))[0]

class sLevelData:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.pALFData = struct.unpack("<I", file.read(4))[0]
		self.pTSOData = struct.unpack("<I", file.read(4))[0]
		self.pAnimData = struct.unpack("<I", file.read(4))[0]
		self.pVISData = struct.unpack("<I", file.read(4))[0]
		self.pSVG = struct.unpack("<I", file.read(4))[0]
		self.pAColGrid = struct.unpack("<I", file.read(4))[0]
		self.pAColGridInt = struct.unpack("<I", file.read(4))[0]
		self.pCameras = struct.unpack("<I", file.read(4))[0]
		self.pPaths = struct.unpack("<I", file.read(4))[0]
		self.pSFXData = struct.unpack("<I", file.read(4))[0]
		self.pMVARList = struct.unpack("<I", file.read(4))[0]
		self.pGeneralText = struct.unpack("<I", file.read(4))[0]

class TextGroup:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.localizations = {}
		rpTextTranslation = file.tell()
		for i in range(4):
			file.seek(rpTextTranslation, os.SEEK_SET)
			pText = struct.unpack("<I", file.read(4))[0]
			global bbHeader
			rpText = pText - bbHeader.dRAMHeader.pCurr

			file.seek(rpText, os.SEEK_SET)
			text = readString(file)

			self.localizations[LocalizationLanguage(i).name] = text

			rpTextTranslation += 4

	def json(self):
		return self.localizations

class LocalizationLanguage(enum.Enum):
	EN = 0
	FR = 1
	DE = 2
	ES = 3

class sColGridPXS:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.min = Vector.read(file)
		self.max = Vector.read(file)
		self.extra = Vector.read(file)
		self.numCellsX = struct.unpack("<i", file.read(4))[0]
		self.numCellsZ = struct.unpack("<i", file.read(4))[0]
		self.totalCells = struct.unpack("<i", file.read(4))[0]
		self.numPolys = struct.unpack("<i", file.read(4))[0]
		self.numIds = struct.unpack("<i", file.read(4))[0]
		self.numVectors = struct.unpack("<i", file.read(4))[0]
		self.cellSize = Vector.read(file)
		self.pCell = struct.unpack("<I", file.read(4))[0]
		self.pPoly = struct.unpack("<I", file.read(4))[0]
		self.pIds = struct.unpack("<I", file.read(4))[0]
		self.pVec = struct.unpack("<I", file.read(4))[0]

class Vector:
	def __init__(self, data):
		self.data = [data[0], data[1], data[2]]

	@classmethod
	def read(cls, file: io.BufferedReader, pad: bool = False):
		data = struct.unpack("<3f", file.read(12))
		if pad:
			file.seek(4, os.SEEK_CUR)

		return cls(data)

	def __str__(self) -> str:
		return f"<{self.data[0]}, {self.data[1]}, {self.data[2]}>"

	@property
	def x(self) -> float:
		return self.data[0]

	@x.setter
	def x(self, value: float):
		self.data[0] = value

	@property
	def y(self) -> float:
		return self.data[1]

	@y.setter
	def y(self, value: float):
		self.data[1] = value

	@property
	def z(self) -> float:
		return self.data[2]

	@z.setter
	def z(self, value: float):
		self.data[2] = value

	def __add__(left: "Vector", right: "Vector"):
		return Vector([left.x + right.x, left.y + right.y, left.z + right.z])

	def __sub__(left: "Vector", right: "Vector"):
		return Vector([left.x - right.x, left.y - right.y, left.z - right.z])

	@staticmethod
	def dot(left: "Vector", right: "Vector"):
		return left.x * right.x + left.y * right.y + left.z * right.z

	@staticmethod
	def cross(left: "Vector", right: "Vector"):
		return Vector([
			left.y * right.z - left.z * right.y,
			left.z * right.x - left.x * right.z,
			left.x * right.y - left.y * right.x
		])

	def length(self):
		return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

class ColPoly:
	def __init__(self, file: io.BufferedReader):
		if file:
			self.read(file)

	def read(self, file: io.BufferedReader):
		self.normal = Vector.read(file, True)
		self.vertices = [Vector.read(file, True) for i in range(4)]
		self.vertexCount = struct.unpack("<B", file.read(1))[0]
		self.gid = struct.unpack("<B", file.read(1))[0]
		self.ma = struct.unpack("<B", file.read(1))[0]
		self.material = MaterialType(struct.unpack("<B", file.read(1))[0])
		self.d = struct.unpack("<f", file.read(4))[0]
		self.bbMaxZ = struct.unpack("<f", file.read(4))[0]
		self.sid = struct.unpack("<H", file.read(2))[0]
		self.pad = struct.unpack("<H", file.read(2))[0]

class MaterialType(enum.Enum):
	ASPHALT = 0
	CARPET = 1
	COBBLES = 2
	GRASS = 3
	GRAVEL = 4
	ICE = 5
	LEAVES = 6
	METAL = 7
	MUD = 8
	PEBBLES = 9
	PUDDLE = 10
	SAND = 11
	SLATE = 12
	SOIL = 13
	OIL = 14
	STONE = 15
	WOOD_NORMAL = 16
	WOOD_BUMPY = 17
	WATER = 18
	RIVER = 19
	LAVA = 20
	GLOOP = 21
	SOLID_GLOOP = 22
	SWAMP = 23
	CONVEYOR = 24
	COL_TRIGGER_1 = 25
	COL_TRIGGERABLE_MATERIAL_1 = 26
	SWITCHOVER_BOAT2CAR = 27
	SWITCHOVER_CAR2BOAT = 28
	DEFAULT = 29
	BOOST = 30
	RESPAWN = 31
	VERTICAL_WATER = 32
	GLASS = 33
	BLOOD = 34
	MILK = 35
	INVISIBLE_BOOST = 36
	ALIEN = 37
	ASPHALT_DUST = 38
	BARREL_HOLLOW = 39
	BARREL_SOLID = 40
	BOING = 41

def readString(file: io.BufferedReader) -> str:
	string = ""
	while True:
		b = file.read(1)
		if b[0] == 0:
			break
		string += b.decode(errors="backslashreplace")

	return string