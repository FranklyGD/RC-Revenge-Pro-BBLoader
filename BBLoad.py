import sys, os, zlib, traceback, struct, math, base64, json
from RCRPDataTypes import *
from ModelExporter import export

def main():
	targetPath = sys.argv[1]

	if os.path.isdir(targetPath):
		level = int(sys.argv[2])
		flags = sys.argv[3:]
		levelFilePath = f"{targetPath}\\{level // 10}\\{level % 10}.BBK"
		decompressed_levelFolderPath = f"{targetPath}\\..\\Decompressed\\{level // 10}\\{level % 10}\\"
	else:
		flags = sys.argv[2:]
		level = 98 if "FRONT_END" in flags else -1
		levelFilePath = targetPath
		decompressed_levelFolderPath = f"{os.path.split(targetPath)[0]}\\Decompressed\\"

	with open(levelFilePath, "rb") as file:
		if not os.path.exists(decompressed_levelFolderPath):
			os.makedirs(decompressed_levelFolderPath)

		bbHeader = sBBHeader(file)

		if not flags or "NO_SRAM" not in flags and ("SFX_AMBIENT" in flags or "SFX_GENERIC" in flags):
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			sRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "sRAM.BBK", "wb") as dfile:
				dfile.write(sRAM)

		if not flags or "NO_VRAM" not in flags:
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			vRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "vRAM.BBK", "wb") as dfile:
				dfile.write(vRAM)

		if not flags or "NO_DRAM" not in flags:
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			dRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "dRAM.BBK", "wb") as dfile:
				dfile.write(dRAM)

	with open(decompressed_levelFolderPath + "dRAM.BBK", "rb") as file:
		if level == 98:
			FELevelData = sFELevelData(file)
			file.seek(FELevelData.pLvl - bbHeader.dRAMHeader.pCurr, os.SEEK_SET)
		else:
			file.seek(- 0x70, os.SEEK_END)

		Lvl = sLevelData(file)

		if Lvl.pGeneralText != 0:
			generalText = []
			# pointer jump
			rpGeneralText = Lvl.pGeneralText - bbHeader.dRAMHeader.pCurr + 4
			try: # Get all available strings before failing on null or non utf-8 character
				while True:
					file.seek(rpGeneralText, os.SEEK_SET)

					# pointer jump
					pTextTranslations = struct.unpack("<I", file.read(4))[0]
					if pTextTranslations == 0:
						break
					else:
						rpTextTranslations = pTextTranslations - bbHeader.dRAMHeader.pCurr
						file.seek(rpTextTranslations, os.SEEK_SET)
						generalText.append(TextGroup(file))

					rpGeneralText += 4
			except Exception:
				traceback.print_exc()

			with open(decompressed_levelFolderPath + f"generalText.json", "w") as text_file:
				text_file.write(json.dumps([textTranslations.json() for textTranslations in generalText], ensure_ascii=True, indent="\t"))

		# Collision

		rpAColGrid = Lvl.pAColGrid - bbHeader.dRAMHeader.pCurr
		file.seek(rpAColGrid, os.SEEK_SET)
		ColGrid = sColGridPXS(file)

		collisionPolys: list[ColPoly] = []

		rpPoly = ColGrid.pPoly - bbHeader.dRAMHeader.pCurr
		file.seek(rpPoly, os.SEEK_SET)
		for p in range(ColGrid.numPolys):
			collisionPolys.append(ColPoly(file))

		# AI

		aiNodes = []
		if Lvl.pAINode != 0:
			rpAINodeClass = Lvl.pAINode - bbHeader.dRAMHeader.pCurr
			file.seek(rpAINodeClass, os.SEEK_SET)

			# Apparently most of the data within the class seems not used properly in the BBK file
			# The whole structure is used more in live RAM than stored. Only 3 pieces of data is stored here:
			# Node Count, Node Links, Array of Nodes

			# AINodeClass = sAINodeClass(file) # <- That ain't it chief

			# This is how we actually read...

			noNodesSingle = struct.unpack("<H", file.read(2))[0]
			noNodesLink = struct.unpack("<H", file.read(2))[0] # Currently unused

			rpfirstNode = file.tell()
			aiNodes = [sAINode(file) for i in range(noNodesSingle)]

			# Convert AINode pointers to indices
			for aiNode in aiNodes:
				next = aiNode.next
				prev = aiNode.prev
				aiNode.next = [-1,-1]
				aiNode.prev = [-1,-1]
				for i in range(2):
					pNextNode = next[i]
					if pNextNode != 0:
						aiNode.next[i] = (pNextNode - rpfirstNode - bbHeader.dRAMHeader.pCurr) // 0x6c

					pPrevNode = prev[i]
					if pPrevNode != 0:
						aiNode.prev[i] = (pPrevNode - rpfirstNode - bbHeader.dRAMHeader.pCurr) // 0x6c

			with open(decompressed_levelFolderPath + f"ai.json", "w") as text_file:
				text_file.write(json.dumps([aiNode.json() for aiNode in aiNodes], ensure_ascii=True, indent="\t"))

		# Export to a model!
		export(decompressed_levelFolderPath, collisionPolys, aiNodes)

if __name__ == "__main__":
	main()